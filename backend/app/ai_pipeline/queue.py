"""Async processing queue for AI jobs"""
import redis.asyncio as aioredis
from app.core.config import get_settings
import json
import uuid
from datetime import datetime

settings = get_settings()


class AIProcessingQueue:
    """Redis-based queue for async AI processing"""
    
    def __init__(self):
        self.redis = None
    
    async def init(self):
        """Initialize Redis connection"""
        self.redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
    
    async def enqueue_job(
        self,
        job_type: str,
        organization_id: str,
        meeting_id: str,
        input_data: dict,
        priority: str = "medium"
    ) -> str:
        """Enqueue a new processing job"""
        job_id = str(uuid.uuid4())
        
        job = {
            "id": job_id,
            "type": job_type,
            "organization_id": organization_id,
            "meeting_id": meeting_id,
            "input_data": input_data,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Use priority queue
        queue_name = f"ai_queue:{priority}"
        await self.redis.lpush(queue_name, json.dumps(job))
        
        return job_id
    
    async def dequeue_job(self) -> dict:
        """Dequeue next job from priority queues"""
        # Try high priority first, then medium, then low
        for priority in ["high", "medium", "low"]:
            queue_name = f"ai_queue:{priority}"
            job_data = await self.redis.rpop(queue_name)
            if job_data:
                return json.loads(job_data)
        
        return None
    
    async def set_job_result(self, job_id: str, result: dict, status: str = "completed"):
        """Store job result"""
        result_key = f"job_result:{job_id}"
        result_data = {
            "status": status,
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
        }
        await self.redis.set(result_key, json.dumps(result_data), ex=86400)  # 24h expiry
    
    async def get_job_result(self, job_id: str) -> dict:
        """Get job result"""
        result_key = f"job_result:{job_id}"
        data = await self.redis.get(result_key)
        if data:
            return json.loads(data)
        return None


# Global queue instance
ai_queue = AIProcessingQueue()
