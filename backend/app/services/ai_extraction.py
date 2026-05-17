"""AI-powered extraction pipeline using Google Generative AI"""
import hashlib
import json
import asyncio
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import google.generativeai as genai
from app.core.config import get_settings
from app.services.gemini_optimization import GeminiOptimizationService


class ExtractionResult(BaseModel):
    """Result of AI extraction"""
    entity_type: str  # "decision", "action", "blocker", "topic"
    title: str
    description: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class ExtractionOutput(BaseModel):
    """Complete extraction output for a transcript"""
    decisions: List[ExtractionResult] = Field(default_factory=list)
    actions: List[ExtractionResult] = Field(default_factory=list)
    blockers: List[ExtractionResult] = Field(default_factory=list)
    topics: List[ExtractionResult] = Field(default_factory=list)
    meeting_summary: str = ""


class AIExtractionService:
    """Service for extracting intelligence from meeting transcripts using Gemini"""

    def __init__(self):
        """Initialize Gemini API"""
        settings = get_settings()
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.extraction_cache = {}  # Simple in-memory cache

    async def extract_from_transcript(
        self,
        transcript_text: str,
        meeting_title: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        use_cache: bool = True,
    ) -> ExtractionOutput:
        """
        Extract decisions, actions, blockers, and topics from transcript.
        
        Args:
            transcript_text: Full transcript text
            meeting_title: Title of the meeting
            attendees: List of attendee names
            use_cache: Whether to use cached results
            
        Returns:
            ExtractionOutput with extracted entities
        """
        # Check cache using a stable content hash
        cache_key = hashlib.sha256(
            "|".join([
                meeting_title or "",
                ",".join(attendees or []),
                transcript_text,
            ]).encode("utf-8")
        ).hexdigest()
        if use_cache and cache_key in self.extraction_cache:
            return self.extraction_cache[cache_key]

        clean_transcript = self._compress_transcript(transcript_text)
        context_header = f"Meeting: {meeting_title or 'Untitled Meeting'}\n"
        if attendees:
            context_header += f"Attendees: {', '.join(attendees)}\n"

        processing_plan = GeminiOptimizationService.get_processing_plan(len(clean_transcript))
        if processing_plan["window_count"] > 1:
            windows = GeminiOptimizationService.create_semantic_windows(
                clean_transcript,
                window_size=1800,
                overlap=200,
            )
            window_extractions: List[Dict[str, Any]] = []
            for window in windows:
                window_context = f"{context_header}\nTranscript window {window.get('window_index', 0) + 1}:\n{window['text']}"
                prompt = self._build_extraction_prompt(window_context)
                response = await self._call_gemini(prompt)
                extraction = self._parse_extraction_response(response)
                window_extractions.append(extraction.model_dump())

            merged = GeminiOptimizationService.merge_extraction_results(windows, window_extractions)
            extraction = self._parse_extraction_response(json.dumps(merged))
        else:
            # Build context
            context = f"{context_header}\nTranscript:\n{clean_transcript}"

            # Build extraction prompt with prompt trimming if needed
            prompt = self._build_extraction_prompt(context)
            _, optimized_prompt, _ = GeminiOptimizationService.optimize_prompt(
                "You are an intelligence extraction engine.",
                prompt,
                context_budget=GeminiOptimizationService.GEMINI_INPUT_LIMIT - GeminiOptimizationService.TOKEN_BUFFER,
            )

            # Call Gemini
            response = await self._call_gemini(optimized_prompt)

            # Parse response
            extraction = self._parse_extraction_response(response)

        extraction = self._normalize_extraction_output(extraction)

        # Cache result
        if use_cache:
            self.extraction_cache[cache_key] = extraction

        return extraction

    async def extract_from_segments(
        self,
        segments: List[Dict[str, str]],
        batch_size: int = 3,
    ) -> Dict[int, ExtractionOutput]:
        """
        Extract from multiple transcript segments in batches.
        
        Args:
            segments: List of segment dicts with keys: segment_id, text
            batch_size: Number of segments to process in parallel
            
        Returns:
            Dict mapping segment_id to ExtractionOutput
        """
        results = {}
        
        # Process in batches
        for i in range(0, len(segments), batch_size):
            batch = segments[i : i + batch_size]
            
            # Process batch in parallel
            tasks = [
                self.extract_from_transcript(
                    segment["text"],
                    meeting_title=segment.get("segment_title"),
                )
                for segment in batch
            ]
            
            batch_results = await asyncio.gather(*tasks)
            
            # Store results
            for segment, result in zip(batch, batch_results):
                results[segment["segment_id"]] = result
        
        return results

    async def enrich_extraction(
        self,
        extraction: ExtractionOutput,
        additional_context: Optional[str] = None,
    ) -> ExtractionOutput:
        """
        Enrich extraction with additional analysis or context.
        
        Args:
            extraction: Initial extraction output
            additional_context: Additional context to consider
            
        Returns:
            Enhanced extraction output
        """
        # Build enrichment prompt
        extraction_json = json.dumps(
            {
                "decisions": [d.model_dump() for d in extraction.decisions],
                "actions": [a.model_dump() for a in extraction.actions],
                "blockers": [b.model_dump() for b in extraction.blockers],
                "topics": [t.model_dump() for t in extraction.topics],
            },
            indent=2,
        )
        
        prompt = f"""Given the following extracted intelligence from a meeting:

{extraction_json}

{f'Additional context: {additional_context}' if additional_context else ''}

Please:
1. Verify the extraction is accurate and complete
2. Identify any missing decisions, actions, or blockers
3. Suggest relationships between the identified items
4. Rate the overall quality of the extraction

Return the enriched extraction in the same JSON format, with any additions or corrections."""

        response = await self._call_gemini(prompt)
        enriched = self._parse_extraction_response(response)
        
        return enriched

    def _build_extraction_prompt(self, context: str) -> str:
        """Build the extraction prompt for Gemini"""
        return f"""Analyze the following meeting transcript and extract:

1. **Decisions**: Conclusions or agreements reached
2. **Action Items**: Tasks assigned or committed to (include who and when if mentioned)
3. **Blockers**: Issues, risks, or problems discussed
4. **Topics**: Main topics discussed in the meeting

For each item, provide:
- Title: Brief name/title
- Description: 1-2 sentence explanation
- Confidence Score: 0.0-1.0 confidence in this extraction
- Tags: Relevant tags or categories
- Assigned To: (for actions only) Person responsible if mentioned
- Due Date: (for actions only) Target completion date if mentioned
- Priority: (for actions) "low", "medium", or "high" if determinable

Context:
{context}

Return ONLY a valid JSON object with this structure:
{{
  "decisions": [
    {{"title": "...", "description": "...", "confidence_score": 0.95, "tags": []}}
  ],
  "actions": [
    {{"title": "...", "description": "...", "confidence_score": 0.90, "assigned_to": "...", "due_date": "...", "priority": "...", "tags": []}}
  ],
  "blockers": [
    {{"title": "...", "description": "...", "confidence_score": 0.85, "tags": []}}
  ],
  "topics": [
    {{"title": "...", "description": "...", "confidence_score": 0.95, "tags": []}}
  ],
  "meeting_summary": "..."
}}

Ensure all confidence scores are between 0 and 1. Return ONLY the JSON, no other text."""

    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API and return response"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 4000,
                },
            )
            return response.text
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            return "{}"

    def _parse_extraction_response(self, response_text: str) -> ExtractionOutput:
        """Parse Gemini response into ExtractionOutput"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response_text
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            data = json.loads(json_str)
            
            # Parse each entity type
            decisions = [
                ExtractionResult(entity_type="decision", **item)
                for item in data.get("decisions", [])
            ]
            actions = [
                ExtractionResult(entity_type="action", **item)
                for item in data.get("actions", [])
            ]
            blockers = [
                ExtractionResult(entity_type="blocker", **item)
                for item in data.get("blockers", [])
            ]
            topics = [
                ExtractionResult(entity_type="topic", **item)
                for item in data.get("topics", [])
            ]
            
            return ExtractionOutput(
                decisions=decisions,
                actions=actions,
                blockers=blockers,
                topics=topics,
                meeting_summary=data.get("meeting_summary", ""),
            )
        except Exception as e:
            print(f"Error parsing extraction response: {e}")
            return ExtractionOutput()

    def _compress_transcript(self, transcript_text: str) -> str:
        """Compress duplicated transcript lines and trim empty segments."""
        lines = [line.strip() for line in transcript_text.splitlines() if line.strip()]
        compressed: List[str] = []
        seen = set()
        for line in lines:
            normalized = re.sub(r"\s+", " ", line).lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            compressed.append(line)
        return "\n".join(compressed)

    def _normalize_extraction_output(self, extraction: ExtractionOutput) -> ExtractionOutput:
        """Normalize titles and deduplicate obvious duplicates inside one extraction."""
        def normalize_item(item: ExtractionResult) -> ExtractionResult:
            item.title = re.sub(r"\s+", " ", item.title).strip()
            item.description = re.sub(r"\s+", " ", item.description).strip()
            item.tags = sorted({tag.strip().lower() for tag in item.tags if tag and tag.strip()})
            return item

        buckets = {
            "decisions": extraction.decisions,
            "actions": extraction.actions,
            "blockers": extraction.blockers,
            "topics": extraction.topics,
        }

        for bucket_name, items in buckets.items():
            deduped: Dict[str, ExtractionResult] = {}
            for item in items:
                item = normalize_item(item)
                key = item.title.lower()
                existing = deduped.get(key)
                if not existing or item.confidence_score >= existing.confidence_score:
                    deduped[key] = item
            setattr(extraction, bucket_name, list(deduped.values()))

        return extraction
