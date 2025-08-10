import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from concurrent.futures import ThreadPoolExecutor
from config.settings import settings

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class SyncPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SyncTask:
    """Represents a data synchronization task."""
    id: str
    source_platform: str
    target_platform: str
    object_type: str  # leads, contacts, opportunities, etc.
    operation: str  # create, update, delete
    data: Dict[str, Any]
    priority: SyncPriority = SyncPriority.MEDIUM
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    updated_at: datetime = None
    status: SyncStatus = SyncStatus.PENDING
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


class RealTimeSyncManager:
    """
    Real-time data synchronization manager across marketing platforms.
    Handles conflict detection, resolution, and ensures data consistency.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.redis_url
        self.redis_client = None
        self.active_syncs: Dict[str, SyncTask] = {}
        self.sync_handlers: Dict[str, Callable] = {}
        self.conflict_resolvers: Dict[str, Callable] = {}
        self.running = False
        self.worker_threads = 4
        self.executor = ThreadPoolExecutor(max_workers=self.worker_threads)
        self.sync_statistics = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'conflicts_resolved': 0,
            'average_sync_time': 0.0
        }
        self._setup_redis()
    
    def _setup_redis(self):
        """Initialize Redis connection for real-time messaging."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established for real-time sync")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def register_sync_handler(self, platform: str, handler: Callable):
        """Register a synchronization handler for a specific platform."""
        self.sync_handlers[platform] = handler
        logger.info(f"Registered sync handler for platform: {platform}")
    
    def register_conflict_resolver(self, object_type: str, resolver: Callable):
        """Register a conflict resolution handler for specific object types."""
        self.conflict_resolvers[object_type] = resolver
        logger.info(f"Registered conflict resolver for object type: {object_type}")
    
    async def start(self):
        """Start the real-time sync manager."""
        if self.running:
            logger.warning("Sync manager is already running")
            return
        
        self.running = True
        logger.info("Starting real-time sync manager")
        
        # Start background tasks
        tasks = [
            self._process_sync_queue(),
            self._monitor_sync_health(),
            self._cleanup_completed_tasks(),
            self._listen_for_changes()
        ]
        
        await asyncio.gather(*tasks)
    
    async def stop(self):
        """Stop the sync manager gracefully."""
        logger.info("Stopping real-time sync manager")
        self.running = False
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Close Redis connection
        if self.redis_client:
            self.redis_client.close()
    
    def queue_sync(
        self, 
        source_platform: str,
        target_platform: str,
        object_type: str,
        operation: str,
        data: Dict[str, Any],
        priority: SyncPriority = SyncPriority.MEDIUM
    ) -> str:
        """Queue a synchronization task."""
        task_id = f"{source_platform}_{target_platform}_{object_type}_{int(time.time() * 1000)}"
        
        sync_task = SyncTask(
            id=task_id,
            source_platform=source_platform,
            target_platform=target_platform,
            object_type=object_type,
            operation=operation,
            data=data,
            priority=priority
        )
        
        # Store task in Redis queue
        queue_name = f"sync_queue:{priority.name.lower()}"
        task_data = json.dumps(asdict(sync_task), default=str)
        
        self.redis_client.lpush(queue_name, task_data)
        self.active_syncs[task_id] = sync_task
        
        logger.info(f"Queued sync task {task_id}: {operation} {object_type} from {source_platform} to {target_platform}")
        return task_id
    
    async def _process_sync_queue(self):
        """Process synchronization tasks from the queue."""
        queues = ['sync_queue:critical', 'sync_queue:high', 'sync_queue:medium', 'sync_queue:low']
        
        while self.running:
            try:
                # Process queues by priority
                for queue_name in queues:
                    task_data = self.redis_client.rpop(queue_name)
                    
                    if task_data:
                        task_dict = json.loads(task_data)
                        
                        # Convert datetime strings back to datetime objects
                        task_dict['created_at'] = datetime.fromisoformat(task_dict['created_at'])
                        task_dict['updated_at'] = datetime.fromisoformat(task_dict['updated_at'])
                        task_dict['priority'] = SyncPriority[task_dict['priority']]
                        task_dict['status'] = SyncStatus[task_dict['status']]
                        
                        task = SyncTask(**task_dict)
                        
                        # Submit task for processing
                        future = self.executor.submit(self._execute_sync_task, task)
                        
                        # Don't wait for completion to maintain real-time processing
                        continue
                
                # Brief pause if no tasks found
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing sync queue: {e}")
                await asyncio.sleep(1)
    
    def _execute_sync_task(self, task: SyncTask) -> bool:
        """Execute a single synchronization task."""
        start_time = time.time()
        
        try:
            logger.info(f"Executing sync task {task.id}")
            task.status = SyncStatus.IN_PROGRESS
            task.updated_at = datetime.now()
            
            # Update task status in Redis
            self._update_task_status(task)
            
            # Check for conflicts before syncing
            conflict_detected = self._check_for_conflicts(task)
            
            if conflict_detected:
                resolved = self._resolve_conflict(task, conflict_detected)
                if not resolved:
                    task.status = SyncStatus.FAILED
                    task.error_message = "Conflict resolution failed"
                    self._update_task_status(task)
                    return False
            
            # Execute the sync using registered handler
            target_handler = self.sync_handlers.get(task.target_platform)
            
            if not target_handler:
                raise Exception(f"No sync handler registered for platform: {task.target_platform}")
            
            # Perform the synchronization
            result = target_handler(task)
            
            if result:
                task.status = SyncStatus.COMPLETED
                self.sync_statistics['successful_syncs'] += 1
                logger.info(f"Successfully completed sync task {task.id}")
            else:
                raise Exception("Sync handler returned False")
            
        except Exception as e:
            logger.error(f"Sync task {task.id} failed: {e}")
            task.status = SyncStatus.FAILED
            task.error_message = str(e)
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = SyncStatus.RETRYING
                
                # Re-queue with exponential backoff
                retry_delay = 2 ** task.retry_count
                asyncio.get_event_loop().call_later(
                    retry_delay,
                    lambda: self._requeue_task(task)
                )
                logger.info(f"Retrying sync task {task.id} in {retry_delay} seconds (attempt {task.retry_count})")
            else:
                self.sync_statistics['failed_syncs'] += 1
        
        finally:
            # Update statistics
            sync_duration = time.time() - start_time
            self._update_sync_statistics(sync_duration)
            task.updated_at = datetime.now()
            self._update_task_status(task)
            self.sync_statistics['total_syncs'] += 1
        
        return task.status == SyncStatus.COMPLETED
    
    def _check_for_conflicts(self, task: SyncTask) -> Optional[Dict[str, Any]]:
        """Check for data conflicts before synchronization."""
        try:
            # Look for existing records with same identifier
            conflict_key = f"conflict:{task.target_platform}:{task.object_type}:{task.data.get('id', '')}"
            existing_data = self.redis_client.get(conflict_key)
            
            if existing_data:
                existing_record = json.loads(existing_data)
                
                # Check timestamps to detect conflicts
                task_timestamp = task.data.get('last_modified', task.updated_at.isoformat())
                existing_timestamp = existing_record.get('last_modified', '')
                
                if existing_timestamp and task_timestamp < existing_timestamp:
                    return {
                        'type': 'timestamp_conflict',
                        'existing_data': existing_record,
                        'task_data': task.data,
                        'conflict_key': conflict_key
                    }
            
            # Store current data for future conflict detection
            self.redis_client.setex(
                conflict_key,
                3600,  # 1 hour TTL
                json.dumps({
                    'data': task.data,
                    'last_modified': task.updated_at.isoformat(),
                    'source': task.source_platform
                })
            )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking for conflicts: {e}")
            return None
    
    def _resolve_conflict(self, task: SyncTask, conflict: Dict[str, Any]) -> bool:
        """Resolve data conflicts using registered resolvers."""
        try:
            resolver = self.conflict_resolvers.get(task.object_type)
            
            if resolver:
                resolved_data = resolver(task.data, conflict['existing_data'])
                task.data = resolved_data
                self.sync_statistics['conflicts_resolved'] += 1
                logger.info(f"Resolved conflict for task {task.id}")
                return True
            else:
                # Default resolution: use latest timestamp
                task_time = datetime.fromisoformat(task.data.get('last_modified', task.updated_at.isoformat()))
                existing_time = datetime.fromisoformat(conflict['existing_data'].get('last_modified', ''))
                
                if task_time >= existing_time:
                    logger.info(f"Using task data for conflict resolution (newer timestamp)")
                    return True
                else:
                    logger.info(f"Skipping sync due to older timestamp")
                    return False
                    
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            return False
    
    def _requeue_task(self, task: SyncTask):
        """Re-queue a failed task for retry."""
        queue_name = f"sync_queue:{task.priority.name.lower()}"
        task_data = json.dumps(asdict(task), default=str)
        self.redis_client.lpush(queue_name, task_data)
    
    def _update_task_status(self, task: SyncTask):
        """Update task status in Redis."""
        try:
            task_key = f"sync_task:{task.id}"
            task_data = json.dumps(asdict(task), default=str)
            self.redis_client.setex(task_key, 86400, task_data)  # 24 hour TTL
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
    
    def _update_sync_statistics(self, sync_duration: float):
        """Update synchronization statistics."""
        # Update average sync time
        current_avg = self.sync_statistics['average_sync_time']
        total_syncs = self.sync_statistics['total_syncs']
        
        if total_syncs > 0:
            new_avg = ((current_avg * total_syncs) + sync_duration) / (total_syncs + 1)
            self.sync_statistics['average_sync_time'] = new_avg
        else:
            self.sync_statistics['average_sync_time'] = sync_duration
    
    async def _listen_for_changes(self):
        """Listen for real-time data changes from platforms."""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe('platform_changes')
        
        while self.running:
            try:
                message = pubsub.get_message(timeout=1.0)
                
                if message and message['type'] == 'message':
                    change_data = json.loads(message['data'])
                    await self._handle_platform_change(change_data)
                    
            except Exception as e:
                logger.error(f"Error listening for platform changes: {e}")
                await asyncio.sleep(1)
    
    async def _handle_platform_change(self, change_data: Dict[str, Any]):
        """Handle real-time platform data changes."""
        try:
            # Extract change information
            platform = change_data.get('platform')
            object_type = change_data.get('object_type')
            operation = change_data.get('operation')
            data = change_data.get('data')
            
            # Determine target platforms for sync
            target_platforms = self._get_sync_targets(platform, object_type)
            
            # Queue sync tasks for each target
            for target_platform in target_platforms:
                self.queue_sync(
                    source_platform=platform,
                    target_platform=target_platform,
                    object_type=object_type,
                    operation=operation,
                    data=data,
                    priority=SyncPriority.HIGH  # Real-time changes get high priority
                )
                
        except Exception as e:
            logger.error(f"Error handling platform change: {e}")
    
    def _get_sync_targets(self, source_platform: str, object_type: str) -> List[str]:
        """Get target platforms for synchronization based on source and object type."""
        # This would be configurable based on business rules
        sync_targets = {
            'salesforce': {
                'leads': ['hubspot', 'mailchimp'],
                'contacts': ['hubspot', 'mailchimp'],
                'opportunities': ['hubspot']
            },
            'hubspot': {
                'contacts': ['salesforce', 'mailchimp'],
                'deals': ['salesforce'],
                'companies': ['salesforce']
            },
            'google_analytics': {
                'conversions': ['salesforce', 'hubspot'],
                'sessions': ['hubspot']
            }
        }
        
        return sync_targets.get(source_platform, {}).get(object_type, [])
    
    async def _monitor_sync_health(self):
        """Monitor sync health and performance metrics."""
        while self.running:
            try:
                # Check queue lengths
                queue_lengths = {}
                for priority in ['critical', 'high', 'medium', 'low']:
                    queue_name = f"sync_queue:{priority}"
                    length = self.redis_client.llen(queue_name)
                    queue_lengths[priority] = length
                
                # Log health metrics
                total_queued = sum(queue_lengths.values())
                success_rate = 0
                
                if self.sync_statistics['total_syncs'] > 0:
                    success_rate = (self.sync_statistics['successful_syncs'] / 
                                  self.sync_statistics['total_syncs']) * 100
                
                logger.info(f"Sync Health - Queued: {total_queued}, Success Rate: {success_rate:.1f}%, "
                          f"Avg Time: {self.sync_statistics['average_sync_time']:.2f}s")
                
                # Store metrics in Redis for monitoring dashboard
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'queue_lengths': queue_lengths,
                    'statistics': self.sync_statistics,
                    'success_rate': success_rate
                }
                
                self.redis_client.setex('sync_health_metrics', 300, json.dumps(metrics))
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Error monitoring sync health: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_completed_tasks(self):
        """Clean up completed sync tasks to prevent memory leaks."""
        while self.running:
            try:
                # Clean up tasks older than 24 hours
                cleanup_time = datetime.now() - timedelta(hours=24)
                
                tasks_to_remove = []
                for task_id, task in self.active_syncs.items():
                    if (task.status in [SyncStatus.COMPLETED, SyncStatus.FAILED] and 
                        task.updated_at < cleanup_time):
                        tasks_to_remove.append(task_id)
                
                for task_id in tasks_to_remove:
                    del self.active_syncs[task_id]
                    # Remove from Redis as well
                    self.redis_client.delete(f"sync_task:{task_id}")
                
                if tasks_to_remove:
                    logger.info(f"Cleaned up {len(tasks_to_remove)} completed sync tasks")
                
                await asyncio.sleep(3600)  # Run cleanup every hour
                
            except Exception as e:
                logger.error(f"Error during task cleanup: {e}")
                await asyncio.sleep(3600)
    
    def get_sync_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific sync task."""
        try:
            task_key = f"sync_task:{task_id}"
            task_data = self.redis_client.get(task_key)
            
            if task_data:
                return json.loads(task_data)
            
            # Check in-memory cache
            if task_id in self.active_syncs:
                return asdict(self.active_syncs[task_id])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return None
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """Get current synchronization statistics."""
        return self.sync_statistics.copy()
    
    def publish_platform_change(
        self, 
        platform: str, 
        object_type: str, 
        operation: str, 
        data: Dict[str, Any]
    ):
        """Publish a platform data change for real-time processing."""
        try:
            change_data = {
                'platform': platform,
                'object_type': object_type,
                'operation': operation,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            
            self.redis_client.publish('platform_changes', json.dumps(change_data))
            logger.debug(f"Published change event: {platform} {object_type} {operation}")
            
        except Exception as e:
            logger.error(f"Error publishing platform change: {e}")


# Example conflict resolution functions
def resolve_lead_conflict(task_data: Dict[str, Any], existing_data: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve conflicts for lead data by merging non-conflicting fields."""
    resolved = task_data.copy()
    
    # Use latest timestamp for most fields
    task_time = datetime.fromisoformat(task_data.get('last_modified', ''))
    existing_time = datetime.fromisoformat(existing_data.get('last_modified', ''))
    
    if existing_time > task_time:
        # Keep existing data for newer fields, but preserve specific task data
        for key, value in existing_data.items():
            if key not in ['id', 'created_date']:  # Don't overwrite ID or creation date
                resolved[key] = value
    
    return resolved


def resolve_contact_conflict(task_data: Dict[str, Any], existing_data: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve conflicts for contact data with field-level merging."""
    resolved = existing_data.copy()
    
    # Fields that should always use the latest value
    always_update_fields = ['email', 'phone', 'last_activity_date', 'lead_score']
    
    for field in always_update_fields:
        if field in task_data:
            resolved[field] = task_data[field]
    
    # For other fields, use the one with the latest timestamp
    task_time = datetime.fromisoformat(task_data.get('last_modified', ''))
    existing_time = datetime.fromisoformat(existing_data.get('last_modified', ''))
    
    if task_time > existing_time:
        resolved.update(task_data)
    
    return resolved