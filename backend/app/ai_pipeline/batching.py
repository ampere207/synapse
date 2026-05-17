"""Transcript batching and intelligent chunking"""
from typing import List, Dict, Any
from datetime import datetime, timedelta


class TranscriptBatcher:
    """Intelligently batch transcript chunks for AI processing"""
    
    def __init__(
        self,
        time_window_seconds: int = 120,
        token_limit: int = 1000,
    ):
        self.time_window_seconds = time_window_seconds
        self.token_limit = token_limit
        self.buffer: List[Dict[str, Any]] = []
        self.last_batch_time = datetime.utcnow()
    
    def add_chunk(self, chunk: Dict[str, Any]) -> bool:
        """Add chunk to buffer, return True if batch ready"""
        self.buffer.append(chunk)
        return self._should_trigger_batch()
    
    def _should_trigger_batch(self) -> bool:
        """Check if batch should be triggered"""
        if not self.buffer:
            return False
        
        # Time window exceeded
        time_elapsed = (datetime.utcnow() - self.last_batch_time).total_seconds()
        if time_elapsed >= self.time_window_seconds:
            return True
        
        # Token limit exceeded
        total_tokens = sum(chunk.get("token_count", len(chunk.get("text", "").split())) for chunk in self.buffer)
        if total_tokens >= self.token_limit:
            return True
        
        # Topic transition (simple heuristic: different speakers)
        if len(self.buffer) > 1:
            speakers = set(chunk.get("speaker") for chunk in self.buffer[-2:])
            if len(speakers) > 1 and None not in speakers:
                # Speaker transition detected
                return len(self.buffer) > 3  # Allow at least 3 chunks per batch
        
        return False
    
    def get_batch(self) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Get current batch and return remaining buffer"""
        batch = self.buffer.copy()
        self.buffer = []
        self.last_batch_time = datetime.utcnow()
        return batch, self.buffer
    
    def get_buffer_text(self, buffer: List[Dict[str, Any]] = None) -> str:
        """Get concatenated text from buffer"""
        if buffer is None:
            buffer = self.buffer
        
        texts = []
        for chunk in buffer:
            speaker = chunk.get("speaker", "Unknown")
            text = chunk.get("text", "")
            texts.append(f"{speaker}: {text}")
        
        return "\n".join(texts)
