"""Gemini optimization service for efficient extraction"""
from typing import List, Dict, Any, Optional, Tuple
import re


class GeminiOptimizationService:
    """Service for optimizing Gemini API calls through windowing and caching"""

    # Token estimates (rough)
    AVG_TOKENS_PER_WORD = 1.3
    TOKEN_BUFFER = 500  # For prompt overhead
    
    # Model limits
    GEMINI_INPUT_LIMIT = 30720  # tokens
    GEMINI_OUTPUT_LIMIT = 8192  # tokens

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough estimate of tokens in text"""
        words = len(text.split())
        return int(words * GeminiOptimizationService.AVG_TOKENS_PER_WORD)

    @staticmethod
    def create_semantic_windows(
        text: str,
        window_size: int = 2000,
        overlap: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        Create overlapping windows of text for processing.
        
        Args:
            text: Full text to window
            window_size: Target tokens per window
            overlap: Overlap tokens between windows
            
        Returns:
            List of windows with metadata
        """
        # Split into sentences for better boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        windows = []
        current_window = []
        current_tokens = 0
        start_sentence_idx = 0
        
        for sent_idx, sentence in enumerate(sentences):
            sent_tokens = GeminiOptimizationService.estimate_tokens(sentence)
            
            # If adding this sentence exceeds window, save current window
            if current_tokens + sent_tokens > window_size and current_window:
                window_text = " ".join(current_window)
                windows.append({
                    "text": window_text,
                    "start_sentence": start_sentence_idx,
                    "end_sentence": sent_idx,
                    "tokens": current_tokens,
                    "window_index": len(windows),
                })
                
                # Start new window with overlap
                # Keep last few sentences for context
                overlap_sentences = []
                overlap_tokens = 0
                for back_idx in range(len(current_window) - 1, -1, -1):
                    s = current_window[back_idx]
                    s_tokens = GeminiOptimizationService.estimate_tokens(s)
                    if overlap_tokens + s_tokens <= overlap:
                        overlap_sentences.insert(0, s)
                        overlap_tokens += s_tokens
                    else:
                        break
                
                current_window = overlap_sentences
                current_tokens = overlap_tokens
                start_sentence_idx = sent_idx - len(overlap_sentences)
            
            current_window.append(sentence)
            current_tokens += sent_tokens
        
        # Add final window
        if current_window:
            windows.append({
                "text": " ".join(current_window),
                "start_sentence": start_sentence_idx,
                "end_sentence": len(sentences),
                "tokens": current_tokens,
                "window_index": len(windows),
            })
        
        return windows

    @staticmethod
    def optimize_prompt(
        system_prompt: str,
        user_content: str,
        context_budget: int = 5000,
    ) -> Tuple[str, str, int]:
        """
        Optimize prompt to fit within token budget.
        
        Returns:
            (optimized_system_prompt, optimized_user_content, estimated_input_tokens)
        """
        system_tokens = GeminiOptimizationService.estimate_tokens(system_prompt)
        user_tokens = GeminiOptimizationService.estimate_tokens(user_content)
        overhead = GeminiOptimizationService.TOKEN_BUFFER
        
        total_tokens = system_tokens + user_tokens + overhead
        
        # If under budget, return as-is
        if total_tokens <= context_budget:
            return system_prompt, user_content, total_tokens
        
        # Need to trim user content
        available_for_user = context_budget - system_tokens - overhead
        
        if available_for_user < 500:
            # Can't optimize enough, return minimal
            return system_prompt[:context_budget // 2], user_content[:500], context_budget
        
        # Trim user content to fit
        words = user_content.split()
        max_words = int(available_for_user / GeminiOptimizationService.AVG_TOKENS_PER_WORD)
        trimmed_content = " ".join(words[:max_words])
        
        if len(words) > max_words:
            trimmed_content += f"\n... (truncated, {len(words) - max_words} words omitted)"
        
        return system_prompt, trimmed_content, context_budget

    @staticmethod
    def merge_extraction_results(
        windows: List[Dict[str, Any]],
        extractions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Merge extraction results from multiple windows, removing duplicates.
        
        Args:
            windows: List of text windows processed
            extractions: List of extraction results (one per window)
            
        Returns:
            Merged extraction with deduplicated entities
        """
        merged = {
            "decisions": [],
            "actions": [],
            "blockers": [],
            "topics": [],
            "meeting_summary": "",
        }
        
        seen_decisions = set()
        seen_actions = set()
        seen_blockers = set()
        seen_topics = set()
        
        for extraction in extractions:
            # Merge decisions (deduplicate by title)
            for decision in extraction.get("decisions", []):
                title_hash = decision.get("title", "").lower()
                if title_hash not in seen_decisions:
                    merged["decisions"].append(decision)
                    seen_decisions.add(title_hash)
                else:
                    # Update with higher confidence if available
                    for existing in merged["decisions"]:
                        if existing.get("title", "").lower() == title_hash:
                            if decision.get("confidence_score", 0) > existing.get("confidence_score", 0):
                                existing.update(decision)
                            break
            
            # Merge actions (deduplicate by title)
            for action in extraction.get("actions", []):
                title_hash = action.get("title", "").lower()
                if title_hash not in seen_actions:
                    merged["actions"].append(action)
                    seen_actions.add(title_hash)
            
            # Merge blockers
            for blocker in extraction.get("blockers", []):
                title_hash = blocker.get("title", "").lower()
                if title_hash not in seen_blockers:
                    merged["blockers"].append(blocker)
                    seen_blockers.add(title_hash)
            
            # Merge topics
            for topic in extraction.get("topics", []):
                title_hash = topic.get("title", "").lower()
                if title_hash not in seen_topics:
                    merged["topics"].append(topic)
                    seen_topics.add(title_hash)
            
            # Update summary (take longest non-empty)
            summary = extraction.get("meeting_summary", "")
            if summary and len(summary) > len(merged["meeting_summary"]):
                merged["meeting_summary"] = summary
        
        return merged

    @staticmethod
    def get_processing_plan(
        transcript_length: int,
        max_tokens_per_call: int = 4000,
    ) -> Dict[str, Any]:
        """
        Create a processing plan for efficient extraction.
        
        Returns plan with:
        - Number of windows needed
        - Recommended extraction strategy
        - Estimated API calls
        """
        est_tokens = GeminiOptimizationService.estimate_tokens("x" * transcript_length)
        
        window_count = max(1, (est_tokens + max_tokens_per_call - 1) // max_tokens_per_call)
        
        return {
            "total_tokens_estimated": est_tokens,
            "max_tokens_per_call": max_tokens_per_call,
            "window_count": window_count,
            "estimated_api_calls": window_count,
            "strategy": "multi-window" if window_count > 1 else "single-pass",
            "deduplication_needed": window_count > 1,
        }

    @staticmethod
    def should_extract_from_segment(
        segment_text: str,
        min_length: int = 100,
        min_tokens: int = 50,
    ) -> bool:
        """
        Determine if a segment has enough content to be worth extracting from.
        
        Returns:
            True if segment should be processed
        """
        if len(segment_text) < min_length:
            return False
        
        tokens = GeminiOptimizationService.estimate_tokens(segment_text)
        return tokens >= min_tokens

    @staticmethod
    def prioritize_windows(
        windows: List[Dict[str, Any]],
        budget_tokens: int,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Prioritize windows for processing within token budget.
        
        Returns:
            (primary_windows, secondary_windows)
        """
        windows_sorted = sorted(
            windows,
            key=lambda w: w.get("tokens", 0),
            reverse=True
        )
        
        primary = []
        secondary = []
        current_tokens = 0
        
        for window in windows_sorted:
            if current_tokens + window.get("tokens", 0) <= budget_tokens:
                primary.append(window)
                current_tokens += window.get("tokens", 0)
            else:
                secondary.append(window)
        
        return primary, secondary
