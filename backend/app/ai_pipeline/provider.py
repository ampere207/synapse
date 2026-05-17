"""AI Provider abstraction - supports multiple providers (Gemini, OpenAI, etc.)"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.core.config import get_settings
import google.generativeai as genai


settings = get_settings()


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    async def summarize(self, text: str) -> str:
        """Summarize text"""
        pass
    
    @abstractmethod
    async def extract_decisions(self, text: str) -> list[Dict[str, Any]]:
        """Extract decisions from text"""
        pass
    
    @abstractmethod
    async def extract_actions(self, text: str) -> list[Dict[str, Any]]:
        """Extract action items from text"""
        pass
    
    @abstractmethod
    async def extract_topics(self, text: str) -> list[str]:
        """Extract topics from text"""
        pass


class GeminiProvider(AIProvider):
    """Gemini AI provider implementation"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    async def summarize(self, text: str) -> str:
        """Summarize text using Gemini"""
        if not self.api_key:
            return ""
        
        prompt = f"""Please provide a concise summary of the following meeting transcript:

{text}

Summary:"""
        
        response = self.model.generate_content(prompt)
        return response.text
    
    async def extract_decisions(self, text: str) -> list[Dict[str, Any]]:
        """Extract decisions from text"""
        if not self.api_key:
            return []
        
        prompt = f"""Extract all decisions made in this meeting transcript. 
Return as JSON array with objects containing 'title', 'description', and 'decided_by' fields.

Transcript:
{text}

Return only valid JSON array:"""
        
        response = self.model.generate_content(prompt)
        try:
            # Parse JSON response
            import json
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text)
        except:
            return []
    
    async def extract_actions(self, text: str) -> list[Dict[str, Any]]:
        """Extract action items from text"""
        if not self.api_key:
            return []
        
        prompt = f"""Extract all action items and next steps from this meeting transcript.
Return as JSON array with objects containing 'title', 'description', 'assigned_to', and 'due_date' fields.

Transcript:
{text}

Return only valid JSON array:"""
        
        response = self.model.generate_content(prompt)
        try:
            import json
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text)
        except:
            return []
    
    async def extract_topics(self, text: str) -> list[str]:
        """Extract topics from text"""
        if not self.api_key:
            return []
        
        prompt = f"""Extract the main topics discussed in this meeting transcript.
Return as JSON array of topic strings.

Transcript:
{text}

Return only valid JSON array of strings:"""
        
        response = self.model.generate_content(prompt)
        try:
            import json
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text)
        except:
            return []


def get_ai_provider() -> AIProvider:
    """Get configured AI provider"""
    return GeminiProvider()
