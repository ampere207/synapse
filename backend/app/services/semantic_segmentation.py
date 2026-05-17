"""Semantic segmentation service for transcript chunk analysis"""
import re
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import math


class SemanticSegmentationService:
    """Service for grouping transcript chunks into semantic topics"""

    # Common English stop words
    STOP_WORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "am", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "can", "that", "this", "as", "it",
        "which", "who", "whom", "whose", "what", "when", "where", "why", "how",
        "i", "you", "he", "she", "we", "they", "me", "him", "her", "us", "them",
        "my", "your", "his", "her", "its", "our", "their", "all", "each", "every",
        "both", "few", "more", "most", "other", "some", "any", "no", "nor", "not",
        "so", "such", "only", "own", "same", "then", "than", "just", "very",
    }

    @staticmethod
    def extract_keywords(text: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """Extract keywords from text with TF-like scoring"""
        # Clean and tokenize
        tokens = re.findall(r'\b[a-z]+\b', text.lower())
        
        # Remove stop words and very short tokens
        filtered = [t for t in tokens if t not in SemanticSegmentationService.STOP_WORDS and len(t) > 2]
        
        if not filtered:
            return []
        
        # Calculate frequency score
        freq = Counter(filtered)
        total = len(filtered)
        
        # Return top keywords with normalized scores
        keywords = [
            (word, count / total) for word, count in freq.most_common(top_n)
        ]
        return keywords

    @staticmethod
    def calculate_semantic_distance(
        text1: str,
        text2: str,
    ) -> float:
        """Calculate semantic distance between two text segments (0-1, lower = more similar)"""
        if not text1 or not text2:
            return 1.0
        
        keywords1 = set([word for word, _ in SemanticSegmentationService.extract_keywords(text1, top_n=10)])
        keywords2 = set([word for word, _ in SemanticSegmentationService.extract_keywords(text2, top_n=10)])
        
        if not keywords1 or not keywords2:
            return 1.0
        
        # Jaccard distance
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        
        if union == 0:
            return 1.0
        
        jaccard = intersection / union
        return 1.0 - jaccard  # Convert similarity to distance

    @staticmethod
    def detect_topic_transition(
        prev_chunk: Dict[str, Any],
        curr_chunk: Dict[str, Any],
        transition_threshold: float = 0.6,
    ) -> bool:
        """Detect if there's a topic transition between consecutive chunks"""
        prev_text = prev_chunk.get("text", "")
        curr_text = curr_chunk.get("text", "")
        
        distance = SemanticSegmentationService.calculate_semantic_distance(prev_text, curr_text)
        
        # Topic transition if distance exceeds threshold
        return distance > transition_threshold

    @staticmethod
    async def segment_transcript(
        chunks: List[Dict[str, Any]],
        speaker_change_weight: float = 0.3,
        semantic_weight: float = 0.7,
        transition_threshold: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """
        Segment transcript into topic clusters.
        
        Args:
            chunks: List of transcript chunks with keys: text, speaker, timestamp, index
            speaker_change_weight: Weight for speaker changes in transition detection
            semantic_weight: Weight for semantic similarity in transition detection
            transition_threshold: Threshold (0-1) for topic transitions
            
        Returns:
            List of topic segments with their metadata
        """
        if not chunks or len(chunks) == 0:
            return []
        
        segments = []
        current_segment = {
            "topic_id": 0,
            "start_index": 0,
            "end_index": 0,
            "chunks": [],
            "speakers": set(),
            "text": "",
            "keywords": [],
            "transitions": [],
        }
        
        for i, chunk in enumerate(chunks):
            # Check for topic transition
            is_transition = False
            if i > 0:
                # Calculate combined transition score
                speaker_changed = chunks[i - 1].get("speaker") != chunk.get("speaker")
                semantic_dist = SemanticSegmentationService.calculate_semantic_distance(
                    chunks[i - 1].get("text", ""),
                    chunk.get("text", ""),
                )
                
                # Combined score
                combined_score = (
                    (speaker_change_weight if speaker_changed else 0) +
                    (semantic_weight * semantic_dist)
                )
                
                is_transition = combined_score > transition_threshold
            
            if is_transition and current_segment["chunks"]:
                # Finalize current segment
                current_segment["end_index"] = i - 1
                current_segment["text"] = " ".join([c.get("text", "") for c in current_segment["chunks"]])
                current_segment["keywords"] = SemanticSegmentationService.extract_keywords(
                    current_segment["text"], top_n=5
                )
                current_segment["speakers"] = list(current_segment["speakers"])
                segments.append(current_segment)
                
                # Start new segment
                current_segment = {
                    "topic_id": len(segments),
                    "start_index": i,
                    "end_index": i,
                    "chunks": [],
                    "speakers": set(),
                    "text": "",
                    "keywords": [],
                    "transitions": [],
                }
            
            # Add chunk to current segment
            current_segment["chunks"].append(chunk)
            current_segment["speakers"].add(chunk.get("speaker", "Unknown"))
            if is_transition:
                current_segment["transitions"].append({
                    "chunk_index": i,
                    "reason": "topic_transition",
                })
        
        # Finalize last segment
        if current_segment["chunks"]:
            current_segment["end_index"] = len(chunks) - 1
            current_segment["text"] = " ".join([c.get("text", "") for c in current_segment["chunks"]])
            current_segment["keywords"] = SemanticSegmentationService.extract_keywords(
                current_segment["text"], top_n=5
            )
            current_segment["speakers"] = list(current_segment["speakers"])
            segments.append(current_segment)
        
        return segments

    @staticmethod
    def summarize_segment(segment: Dict[str, Any], max_length: int = 150) -> str:
        """Generate a brief summary of a topic segment"""
        text = segment.get("text", "")
        keywords = [kw[0] for kw in segment.get("keywords", [])]
        speakers = segment.get("speakers", [])
        
        # Build summary: speakers + keywords
        summary = ""
        if speakers:
            summary += f"Discussed by {', '.join(speakers[:2])}: "
        
        if keywords:
            summary += f"topics on {', '.join(keywords[:3])}"
        
        # If no summary formed, use first part of text
        if not summary:
            summary = text[:max_length].rstrip() + "..."
        
        return summary[:max_length]

    @staticmethod
    def group_similar_segments(
        segments: List[Dict[str, Any]],
        similarity_threshold: float = 0.4,
    ) -> List[Dict[str, Any]]:
        """
        Group semantically similar segments together.
        
        Returns:
            List of segment groups with cluster_id
        """
        if len(segments) <= 1:
            return [{"segment": s, "cluster_id": 0} for s in segments]
        
        # Build similarity matrix
        n = len(segments)
        clusters = list(range(n))  # Each segment starts in its own cluster
        
        for i in range(n):
            for j in range(i + 1, n):
                text_i = segments[i].get("text", "")
                text_j = segments[j].get("text", "")
                
                distance = SemanticSegmentationService.calculate_semantic_distance(text_i, text_j)
                
                # If similar enough, merge into same cluster
                if distance < (1.0 - similarity_threshold):
                    # Union-find style merge
                    root_i = clusters[i]
                    root_j = clusters[j]
                    if root_i != root_j:
                        # Merge j's cluster into i's
                        for k in range(n):
                            if clusters[k] == root_j:
                                clusters[k] = root_i
        
        # Renumber clusters
        unique_clusters = list(set(clusters))
        cluster_map = {old: new for new, old in enumerate(unique_clusters)}
        
        result = []
        for i, segment in enumerate(segments):
            result.append({
                "segment": segment,
                "cluster_id": cluster_map[clusters[i]],
            })
        
        return result
