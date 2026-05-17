"""AI processing worker - processes jobs from queue"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.ai_pipeline.queue import ai_queue
from app.ai_pipeline.provider import get_ai_provider
from app.models.ai_job import AIProcessingJob, JobStatusEnum
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIWorker:
    """Worker process for async AI job processing"""
    
    def __init__(self, worker_id: str = "worker-1"):
        self.worker_id = worker_id
        self.provider = get_ai_provider()
        self.running = False
    
    async def start(self):
        """Start worker process"""
        self.running = True
        logger.info(f"Starting AI worker {self.worker_id}")
        
        while self.running:
            try:
                # Get next job from queue
                job = await ai_queue.dequeue_job()
                
                if not job:
                    # No jobs, wait before retry
                    await asyncio.sleep(5)
                    continue
                
                await self._process_job(job)
            
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(10)
    
    async def _process_job(self, job: dict):
        """Process a single job"""
        job_id = job.get("id")
        job_type = job.get("type")
        input_data = job.get("input_data", {})
        
        logger.info(f"Processing job {job_id} of type {job_type}")
        
        db = AsyncSessionLocal()
        try:
            result = None
            
            if job_type == "summarize_chunk":
                result = await self.provider.summarize(input_data.get("text", ""))
            
            elif job_type == "extract_decisions":
                result = await self.provider.extract_decisions(input_data.get("text", ""))
            
            elif job_type == "extract_actions":
                result = await self.provider.extract_actions(input_data.get("text", ""))
            
            elif job_type == "build_graph":
                result = await self._build_graph(input_data, db)
            
            # Store result
            await ai_queue.set_job_result(job_id, result or {}, "completed")
            
            logger.info(f"Completed job {job_id}")
        
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            await ai_queue.set_job_result(job_id, {"error": str(e)}, "failed")
        
        finally:
            await db.close()
    
    async def _build_graph(self, input_data: dict, db: AsyncSession) -> dict:
        """Build graph from transcript"""
        text = input_data.get("text", "")
        
        # Extract all intelligence
        topics = await self.provider.extract_topics(text)
        decisions = await self.provider.extract_decisions(text)
        actions = await self.provider.extract_actions(text)
        
        return {
            "topics": topics,
            "decisions": decisions,
            "actions": actions,
        }
    
    async def stop(self):
        """Stop worker"""
        self.running = False
        logger.info(f"Stopping AI worker {self.worker_id}")


async def run_worker(worker_id: str = "worker-1"):
    """Run a worker as a background task"""
    await ai_queue.init()
    worker = AIWorker(worker_id)
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()
    finally:
        await ai_queue.close()


if __name__ == "__main__":
    asyncio.run(run_worker())
