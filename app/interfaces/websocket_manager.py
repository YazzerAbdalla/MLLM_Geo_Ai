from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import asyncio
import json
import logging
from app.infrastructure.job_store import _redis_store

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Maps job_id to a list of active websocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Maps job_id to the asyncio task listening to redis
        self.pubsub_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
            
        self.active_connections[job_id].append(websocket)
        
        # Start a redis pubsub listener for this job if not already running
        if job_id not in self.pubsub_tasks and _redis_store.is_available():
            task = asyncio.create_task(self._listen_to_redis(job_id))
            self.pubsub_tasks[job_id] = task

    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.active_connections:
            try:
                self.active_connections[job_id].remove(websocket)
            except ValueError:
                pass
            
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
                # Cancel the redis listener
                task = self.pubsub_tasks.pop(job_id, None)
                if task:
                    task.cancel()

    async def _listen_to_redis(self, job_id: str):
        try:
            pubsub = _redis_store.r.pubsub()
            channel_name = f"job_progress_{job_id}"
            pubsub.subscribe(channel_name)
            
            while True:
                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    try:
                        data = message["data"].decode("utf-8")
                        await self._broadcast(job_id, data)
                    except Exception as e:
                        logger.error(f"Error processing pubsub message: {e}")
                
                await asyncio.sleep(0.1)
                
                # Exit if no connections left
                if job_id not in self.active_connections:
                    break
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis pubsub listener error for job {job_id}: {e}")
        finally:
            try:
                pubsub.unsubscribe(channel_name)
            except:
                pass

    async def _broadcast(self, job_id: str, message: str):
        if job_id in self.active_connections:
            websockets = self.active_connections[job_id]
            for ws in websockets[:]:
                try:
                    await ws.send_text(message)
                except Exception:
                    self.disconnect(ws, job_id)

manager = ConnectionManager()
