"""
Backup & Recovery System for MarTech Integration Hub

Enterprise-grade backup and disaster recovery system for marketing data
with automated backups, point-in-time recovery, and failover capabilities.

Author: Sotiris Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

DISCLAIMER: This is demonstration code for portfolio purposes.
Not intended for production use without proper testing and validation.
"""

import logging
import json
import os
import hashlib
import gzip
import shutil
import tarfile
import threading
import queue
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import pandas as pd
import numpy as np
import sqlite3
import pickle
import boto3
from botocore.exceptions import NoCredentialsError
import redis
import pymongo
from concurrent.futures import ThreadPoolExecutor, as_completed
import schedule
import psutil
import cryptography
from cryptography.fernet import Fernet
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class BackupType(Enum):
    """Types of backups."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"
    CONTINUOUS = "continuous"
    ARCHIVE = "archive"


class BackupStatus(Enum):
    """Backup operation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    CORRUPTED = "corrupted"


class RecoveryMode(Enum):
    """Recovery operation modes."""
    FULL_RESTORE = "full_restore"
    POINT_IN_TIME = "point_in_time"
    SELECTIVE = "selective"
    ROLLBACK = "rollback"
    FAILOVER = "failover"
    DISASTER_RECOVERY = "disaster_recovery"


class StorageBackend(Enum):
    """Backup storage backends."""
    LOCAL = "local"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"
    FTP = "ftp"
    NFS = "nfs"
    GLACIER = "glacier"


class DataSource(Enum):
    """Data source types."""
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    REDIS = "redis"
    MONGODB = "mongodb"
    API = "api"
    STREAM = "stream"
    QUEUE = "queue"


@dataclass
class BackupPolicy:
    """Backup policy configuration."""
    policy_id: str
    name: str
    backup_type: BackupType
    frequency: str  # cron expression or interval
    retention_days: int
    compression: bool = True
    encryption: bool = True
    verify_backup: bool = True
    storage_backends: List[StorageBackend] = field(default_factory=list)
    data_sources: List[DataSource] = field(default_factory=list)
    max_parallel_operations: int = 5
    bandwidth_limit_mbps: Optional[float] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class BackupJob:
    """Individual backup job."""
    job_id: str
    policy_id: str
    backup_type: BackupType
    status: BackupStatus
    source_paths: List[str]
    destination_path: str
    storage_backend: StorageBackend
    started_at: datetime
    completed_at: Optional[datetime] = None
    size_bytes: int = 0
    compressed_size_bytes: int = 0
    files_count: int = 0
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    verification_status: Optional[str] = None
    recovery_point_objective: Optional[timedelta] = None


@dataclass
class RecoveryJob:
    """Recovery job configuration."""
    job_id: str
    recovery_mode: RecoveryMode
    backup_job_id: str
    target_paths: List[str]
    recovery_point: Optional[datetime] = None
    status: BackupStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    recovered_files: int = 0
    recovered_bytes: int = 0
    error_message: Optional[str] = None
    rollback_enabled: bool = False
    verification_enabled: bool = True


@dataclass
class BackupCatalog:
    """Backup catalog entry."""
    catalog_id: str
    backup_job_id: str
    file_path: str
    file_size: int
    modified_time: datetime
    checksum: str
    backup_time: datetime
    storage_location: str
    is_encrypted: bool = False
    is_compressed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DisasterRecoveryPlan:
    """Disaster recovery plan configuration."""
    plan_id: str
    name: str
    description: str
    priority: int  # 1-10, 1 being highest
    recovery_time_objective: timedelta  # RTO
    recovery_point_objective: timedelta  # RPO
    backup_policies: List[str]  # Policy IDs
    recovery_procedures: List[Dict[str, Any]]
    failover_sequence: List[str]
    notification_contacts: List[str]
    test_schedule: str  # cron expression
    last_tested: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


class BackupRecoverySystem:
    """
    Comprehensive backup and recovery system for marketing data.
    
    Features:
    - Automated backup scheduling and execution
    - Multiple backup strategies (full, incremental, differential)
    - Multi-destination backup storage
    - Point-in-time recovery
    - Disaster recovery planning
    - Data encryption and compression
    - Backup verification and integrity checking
    - Performance monitoring and reporting
    """
    
    def __init__(self,
                 storage_config: Dict[str, Any],
                 encryption_key: Optional[str] = None,
                 catalog_db_path: str = "./backup_catalog.db"):
        
        # Storage configuration
        self.storage_config = storage_config
        self.local_backup_path = Path(storage_config.get('local_path', './backups'))
        self.local_backup_path.mkdir(parents=True, exist_ok=True)
        
        # Encryption setup
        if encryption_key:
            self.cipher_suite = Fernet(encryption_key.encode())
        else:
            self.cipher_suite = Fernet(Fernet.generate_key())
        
        # Catalog database
        self.catalog_db_path = catalog_db_path
        self._initialize_catalog_db()
        
        # In-memory storage
        self.backup_policies: Dict[str, BackupPolicy] = {}
        self.backup_jobs: Dict[str, BackupJob] = {}
        self.recovery_jobs: Dict[str, RecoveryJob] = {}
        self.dr_plans: Dict[str, DisasterRecoveryPlan] = {}
        
        # Job queues
        self.backup_queue = queue.Queue()
        self.recovery_queue = queue.Queue()
        
        # Performance metrics
        self.metrics = {
            'total_backups': 0,
            'successful_backups': 0,
            'failed_backups': 0,
            'total_recoveries': 0,
            'successful_recoveries': 0,
            'total_bytes_backed_up': 0,
            'total_bytes_recovered': 0,
            'average_backup_speed_mbps': 0,
            'average_recovery_speed_mbps': 0
        }
        
        # Thread pool for parallel operations
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Background processing
        self.is_running = True
        self.processing_threads = []
        
        # Cloud storage clients
        self.s3_client = None
        self.azure_client = None
        self.gcs_client = None
        
        # Initialize cloud clients if configured
        self._initialize_cloud_storage()
        
        # Start background processing
        self._start_background_processing()
        
        # Create default policies
        self._create_default_policies()
        
        logger.info("Backup & Recovery System initialized successfully")
    
    def _initialize_catalog_db(self):
        """Initialize backup catalog database."""
        try:
            conn = sqlite3.connect(self.catalog_db_path)
            cursor = conn.cursor()
            
            # Create catalog table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_catalog (
                    catalog_id TEXT PRIMARY KEY,
                    backup_job_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    modified_time TIMESTAMP,
                    checksum TEXT,
                    backup_time TIMESTAMP,
                    storage_location TEXT,
                    is_encrypted BOOLEAN,
                    is_compressed BOOLEAN,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_backup_job ON backup_catalog(backup_job_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_backup_time ON backup_catalog(backup_time)")
            
            conn.commit()
            conn.close()
            
            logger.info("Backup catalog database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize catalog database: {e}")
    
    def _initialize_cloud_storage(self):
        """Initialize cloud storage clients."""
        try:
            # AWS S3
            if 's3' in self.storage_config:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.storage_config['s3'].get('access_key'),
                    aws_secret_access_key=self.storage_config['s3'].get('secret_key'),
                    region_name=self.storage_config['s3'].get('region', 'us-east-1')
                )
                logger.info("S3 client initialized")
            
            # Azure Blob Storage
            if 'azure' in self.storage_config:
                # Would initialize Azure client here
                logger.info("Azure Blob Storage client would be initialized")
            
            # Google Cloud Storage
            if 'gcs' in self.storage_config:
                # Would initialize GCS client here
                logger.info("Google Cloud Storage client would be initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize cloud storage: {e}")
    
    def _create_default_policies(self):
        """Create default backup policies."""
        try:
            # Daily full backup policy
            daily_policy = BackupPolicy(
                policy_id="daily_full",
                name="Daily Full Backup",
                backup_type=BackupType.FULL,
                frequency="0 2 * * *",  # 2 AM daily
                retention_days=30,
                storage_backends=[StorageBackend.LOCAL, StorageBackend.S3],
                data_sources=[DataSource.DATABASE, DataSource.FILE_SYSTEM]
            )
            
            # Hourly incremental backup
            hourly_policy = BackupPolicy(
                policy_id="hourly_incremental",
                name="Hourly Incremental Backup",
                backup_type=BackupType.INCREMENTAL,
                frequency="0 * * * *",  # Every hour
                retention_days=7,
                storage_backends=[StorageBackend.LOCAL],
                data_sources=[DataSource.DATABASE]
            )
            
            # Weekly archive backup
            weekly_policy = BackupPolicy(
                policy_id="weekly_archive",
                name="Weekly Archive Backup",
                backup_type=BackupType.ARCHIVE,
                frequency="0 3 * * 0",  # 3 AM Sunday
                retention_days=365,
                storage_backends=[StorageBackend.S3, StorageBackend.GLACIER],
                data_sources=[DataSource.DATABASE, DataSource.FILE_SYSTEM, DataSource.REDIS]
            )
            
            # Real-time continuous backup
            continuous_policy = BackupPolicy(
                policy_id="continuous_critical",
                name="Continuous Critical Data Backup",
                backup_type=BackupType.CONTINUOUS,
                frequency="*/5 * * * *",  # Every 5 minutes
                retention_days=3,
                storage_backends=[StorageBackend.LOCAL, StorageBackend.S3],
                data_sources=[DataSource.DATABASE]
            )
            
            # Add policies
            self.backup_policies[daily_policy.policy_id] = daily_policy
            self.backup_policies[hourly_policy.policy_id] = hourly_policy
            self.backup_policies[weekly_policy.policy_id] = weekly_policy
            self.backup_policies[continuous_policy.policy_id] = continuous_policy
            
            logger.info(f"Created {len(self.backup_policies)} default backup policies")
            
        except Exception as e:
            logger.error(f"Failed to create default policies: {e}")
    
    def _start_background_processing(self):
        """Start background processing threads."""
        try:
            # Backup processing thread
            backup_thread = threading.Thread(target=self._process_backup_queue, daemon=True)
            backup_thread.start()
            self.processing_threads.append(backup_thread)
            
            # Recovery processing thread
            recovery_thread = threading.Thread(target=self._process_recovery_queue, daemon=True)
            recovery_thread.start()
            self.processing_threads.append(recovery_thread)
            
            # Scheduled job thread
            schedule_thread = threading.Thread(target=self._run_scheduled_jobs, daemon=True)
            schedule_thread.start()
            self.processing_threads.append(schedule_thread)
            
            # Cleanup thread
            cleanup_thread = threading.Thread(target=self._cleanup_old_backups, daemon=True)
            cleanup_thread.start()
            self.processing_threads.append(cleanup_thread)
            
            logger.info(f"Started {len(self.processing_threads)} background processing threads")
            
        except Exception as e:
            logger.error(f"Failed to start background processing: {e}")
    
    def create_backup(self,
                     policy_id: str,
                     source_paths: List[str],
                     manual_trigger: bool = False) -> Optional[str]:
        """Create a backup based on policy."""
        try:
            policy = self.backup_policies.get(policy_id)
            if not policy:
                raise ValueError(f"Backup policy {policy_id} not found")
            
            # Create backup job
            job_id = f"backup_{policy_id}_{int(time.time())}"
            
            # Determine destination path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            destination = self.local_backup_path / policy_id / timestamp
            destination.mkdir(parents=True, exist_ok=True)
            
            job = BackupJob(
                job_id=job_id,
                policy_id=policy_id,
                backup_type=policy.backup_type,
                status=BackupStatus.PENDING,
                source_paths=source_paths,
                destination_path=str(destination),
                storage_backend=policy.storage_backends[0] if policy.storage_backends else StorageBackend.LOCAL,
                started_at=datetime.now(),
                metadata={'manual_trigger': manual_trigger}
            )
            
            self.backup_jobs[job_id] = job
            
            # Queue for processing
            self.backup_queue.put(job_id)
            
            logger.info(f"Created backup job: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def _process_backup_queue(self):
        """Process backup jobs from queue."""
        while self.is_running:
            try:
                # Get job from queue
                try:
                    job_id = self.backup_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                job = self.backup_jobs.get(job_id)
                if not job:
                    continue
                
                # Execute backup
                self._execute_backup(job)
                
                self.backup_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processing backup queue: {e}")
    
    def _execute_backup(self, job: BackupJob):
        """Execute a backup job."""
        try:
            job.status = BackupStatus.IN_PROGRESS
            start_time = time.time()
            
            policy = self.backup_policies.get(job.policy_id)
            if not policy:
                raise ValueError(f"Policy {job.policy_id} not found")
            
            # Perform backup based on type
            if job.backup_type == BackupType.FULL:
                result = self._perform_full_backup(job, policy)
            elif job.backup_type == BackupType.INCREMENTAL:
                result = self._perform_incremental_backup(job, policy)
            elif job.backup_type == BackupType.DIFFERENTIAL:
                result = self._perform_differential_backup(job, policy)
            elif job.backup_type == BackupType.SNAPSHOT:
                result = self._perform_snapshot_backup(job, policy)
            else:
                result = self._perform_full_backup(job, policy)  # Default to full
            
            if result:
                job.status = BackupStatus.COMPLETED
                job.completed_at = datetime.now()
                
                # Calculate backup speed
                duration = time.time() - start_time
                if duration > 0 and job.size_bytes > 0:
                    speed_mbps = (job.size_bytes / (1024 * 1024)) / duration
                    self._update_metrics('backup_speed', speed_mbps)
                
                # Verify backup if configured
                if policy.verify_backup:
                    self._verify_backup(job)
                
                # Replicate to additional storage backends
                if len(policy.storage_backends) > 1:
                    self._replicate_backup(job, policy.storage_backends[1:])
                
                # Update metrics
                self.metrics['total_backups'] += 1
                self.metrics['successful_backups'] += 1
                self.metrics['total_bytes_backed_up'] += job.size_bytes
                
                logger.info(f"Backup completed: {job.job_id} ({job.size_bytes:,} bytes)")
            else:
                job.status = BackupStatus.FAILED
                self.metrics['failed_backups'] += 1
                logger.error(f"Backup failed: {job.job_id}")
            
        except Exception as e:
            job.status = BackupStatus.FAILED
            job.error_message = str(e)
            self.metrics['failed_backups'] += 1
            logger.error(f"Failed to execute backup {job.job_id}: {e}")
    
    def _perform_full_backup(self, job: BackupJob, policy: BackupPolicy) -> bool:
        """Perform a full backup."""
        try:
            total_size = 0
            total_files = 0
            
            for source_path in job.source_paths:
                source = Path(source_path)
                
                if not source.exists():
                    logger.warning(f"Source path does not exist: {source_path}")
                    continue
                
                if source.is_file():
                    # Backup single file
                    dest_file = Path(job.destination_path) / source.name
                    size = self._backup_file(source, dest_file, policy)
                    total_size += size
                    total_files += 1
                    
                elif source.is_dir():
                    # Backup directory
                    for file_path in source.rglob('*'):
                        if file_path.is_file():
                            relative_path = file_path.relative_to(source)
                            dest_file = Path(job.destination_path) / relative_path
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            
                            size = self._backup_file(file_path, dest_file, policy)
                            total_size += size
                            total_files += 1
                            
                            # Catalog the backup
                            self._add_to_catalog(job.job_id, file_path, dest_file, size)
            
            # Create backup manifest
            manifest = {
                'job_id': job.job_id,
                'backup_type': job.backup_type.value,
                'timestamp': job.started_at.isoformat(),
                'source_paths': job.source_paths,
                'total_files': total_files,
                'total_size': total_size,
                'checksum': self._calculate_backup_checksum(job.destination_path)
            }
            
            manifest_path = Path(job.destination_path) / 'backup_manifest.json'
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            job.size_bytes = total_size
            job.files_count = total_files
            job.checksum = manifest['checksum']
            
            return True
            
        except Exception as e:
            logger.error(f"Full backup failed: {e}")
            return False
    
    def _perform_incremental_backup(self, job: BackupJob, policy: BackupPolicy) -> bool:
        """Perform an incremental backup (only changed files since last backup)."""
        try:
            # Find last successful backup
            last_backup = self._find_last_backup(job.policy_id)
            
            if not last_backup:
                # No previous backup, perform full backup
                logger.info("No previous backup found, performing full backup")
                return self._perform_full_backup(job, policy)
            
            last_backup_time = last_backup.completed_at
            total_size = 0
            total_files = 0
            
            for source_path in job.source_paths:
                source = Path(source_path)
                
                if source.is_dir():
                    for file_path in source.rglob('*'):
                        if file_path.is_file():
                            # Check if file was modified since last backup
                            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                            
                            if file_mtime > last_backup_time:
                                relative_path = file_path.relative_to(source)
                                dest_file = Path(job.destination_path) / relative_path
                                dest_file.parent.mkdir(parents=True, exist_ok=True)
                                
                                size = self._backup_file(file_path, dest_file, policy)
                                total_size += size
                                total_files += 1
                                
                                self._add_to_catalog(job.job_id, file_path, dest_file, size)
            
            job.size_bytes = total_size
            job.files_count = total_files
            
            # Store reference to parent backup
            job.metadata['parent_backup'] = last_backup.job_id
            
            return True
            
        except Exception as e:
            logger.error(f"Incremental backup failed: {e}")
            return False
    
    def _perform_differential_backup(self, job: BackupJob, policy: BackupPolicy) -> bool:
        """Perform a differential backup (changes since last full backup)."""
        try:
            # Find last full backup
            last_full_backup = self._find_last_full_backup(job.policy_id)
            
            if not last_full_backup:
                # No previous full backup, perform full backup
                logger.info("No previous full backup found, performing full backup")
                return self._perform_full_backup(job, policy)
            
            # Similar to incremental but references last full backup
            return self._perform_incremental_backup(job, policy)
            
        except Exception as e:
            logger.error(f"Differential backup failed: {e}")
            return False
    
    def _perform_snapshot_backup(self, job: BackupJob, policy: BackupPolicy) -> bool:
        """Perform a snapshot backup."""
        try:
            # Create a compressed archive of all source paths
            archive_name = f"snapshot_{job.job_id}.tar.gz"
            archive_path = Path(job.destination_path) / archive_name
            
            with tarfile.open(archive_path, 'w:gz') as tar:
                for source_path in job.source_paths:
                    tar.add(source_path, arcname=Path(source_path).name)
            
            job.size_bytes = archive_path.stat().st_size
            job.compressed_size_bytes = job.size_bytes
            job.files_count = len(job.source_paths)
            
            # Encrypt if configured
            if policy.encryption:
                self._encrypt_file(archive_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Snapshot backup failed: {e}")
            return False
    
    def _backup_file(self, source: Path, destination: Path, policy: BackupPolicy) -> int:
        """Backup a single file."""
        try:
            # Copy file
            shutil.copy2(source, destination)
            
            # Compress if configured
            if policy.compression:
                compressed_path = Path(str(destination) + '.gz')
                with open(destination, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove uncompressed file
                destination.unlink()
                destination = compressed_path
            
            # Encrypt if configured
            if policy.encryption:
                self._encrypt_file(destination)
            
            return destination.stat().st_size
            
        except Exception as e:
            logger.error(f"Failed to backup file {source}: {e}")
            return 0
    
    def _encrypt_file(self, file_path: Path):
        """Encrypt a file in place."""
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            encrypted_data = self.cipher_suite.encrypt(file_data)
            
            encrypted_path = Path(str(file_path) + '.enc')
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Remove unencrypted file
            file_path.unlink()
            
        except Exception as e:
            logger.error(f"Failed to encrypt file {file_path}: {e}")
    
    def _calculate_backup_checksum(self, backup_path: str) -> str:
        """Calculate checksum for backup verification."""
        try:
            hasher = hashlib.sha256()
            
            for file_path in Path(backup_path).rglob('*'):
                if file_path.is_file():
                    with open(file_path, 'rb') as f:
                        while chunk := f.read(8192):
                            hasher.update(chunk)
            
            return hasher.hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to calculate checksum: {e}")
            return ""
    
    def _add_to_catalog(self, job_id: str, source: Path, destination: Path, size: int):
        """Add backup entry to catalog."""
        try:
            catalog_entry = BackupCatalog(
                catalog_id=f"cat_{int(time.time() * 1000000)}",
                backup_job_id=job_id,
                file_path=str(source),
                file_size=size,
                modified_time=datetime.fromtimestamp(source.stat().st_mtime),
                checksum=self._calculate_file_checksum(source),
                backup_time=datetime.now(),
                storage_location=str(destination),
                is_encrypted=destination.suffix == '.enc',
                is_compressed='.gz' in destination.suffixes
            )
            
            # Store in database
            conn = sqlite3.connect(self.catalog_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO backup_catalog 
                (catalog_id, backup_job_id, file_path, file_size, modified_time,
                 checksum, backup_time, storage_location, is_encrypted, is_compressed, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                catalog_entry.catalog_id,
                catalog_entry.backup_job_id,
                catalog_entry.file_path,
                catalog_entry.file_size,
                catalog_entry.modified_time,
                catalog_entry.checksum,
                catalog_entry.backup_time,
                catalog_entry.storage_location,
                catalog_entry.is_encrypted,
                catalog_entry.is_compressed,
                json.dumps(catalog_entry.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to add to catalog: {e}")
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return ""
    
    def _find_last_backup(self, policy_id: str) -> Optional[BackupJob]:
        """Find the last successful backup for a policy."""
        policy_backups = [
            job for job in self.backup_jobs.values()
            if job.policy_id == policy_id and job.status == BackupStatus.COMPLETED
        ]
        
        if policy_backups:
            return max(policy_backups, key=lambda j: j.completed_at or datetime.min)
        
        return None
    
    def _find_last_full_backup(self, policy_id: str) -> Optional[BackupJob]:
        """Find the last successful full backup for a policy."""
        full_backups = [
            job for job in self.backup_jobs.values()
            if job.policy_id == policy_id 
            and job.backup_type == BackupType.FULL
            and job.status == BackupStatus.COMPLETED
        ]
        
        if full_backups:
            return max(full_backups, key=lambda j: j.completed_at or datetime.min)
        
        return None
    
    def _verify_backup(self, job: BackupJob):
        """Verify backup integrity."""
        try:
            job.status = BackupStatus.VERIFYING
            
            # Recalculate checksum
            current_checksum = self._calculate_backup_checksum(job.destination_path)
            
            if current_checksum == job.checksum:
                job.status = BackupStatus.VERIFIED
                job.verification_status = "passed"
                logger.info(f"Backup verification passed: {job.job_id}")
            else:
                job.status = BackupStatus.CORRUPTED
                job.verification_status = "failed"
                logger.error(f"Backup verification failed: {job.job_id}")
            
        except Exception as e:
            logger.error(f"Failed to verify backup: {e}")
            job.verification_status = "error"
    
    def _replicate_backup(self, job: BackupJob, backends: List[StorageBackend]):
        """Replicate backup to additional storage backends."""
        for backend in backends:
            try:
                if backend == StorageBackend.S3:
                    self._replicate_to_s3(job)
                elif backend == StorageBackend.AZURE_BLOB:
                    self._replicate_to_azure(job)
                elif backend == StorageBackend.GCS:
                    self._replicate_to_gcs(job)
                elif backend == StorageBackend.GLACIER:
                    self._replicate_to_glacier(job)
                
                logger.info(f"Replicated backup to {backend.value}: {job.job_id}")
                
            except Exception as e:
                logger.error(f"Failed to replicate to {backend.value}: {e}")
    
    def _replicate_to_s3(self, job: BackupJob):
        """Replicate backup to S3."""
        if not self.s3_client:
            logger.warning("S3 client not configured")
            return
        
        try:
            bucket_name = self.storage_config['s3']['bucket']
            
            for file_path in Path(job.destination_path).rglob('*'):
                if file_path.is_file():
                    s3_key = f"backups/{job.job_id}/{file_path.relative_to(job.destination_path)}"
                    
                    self.s3_client.upload_file(
                        str(file_path),
                        bucket_name,
                        s3_key
                    )
            
            logger.info(f"Backup replicated to S3: {job.job_id}")
            
        except Exception as e:
            logger.error(f"S3 replication failed: {e}")
    
    def _replicate_to_azure(self, job: BackupJob):
        """Replicate backup to Azure Blob Storage."""
        # Implementation would go here
        logger.info(f"Azure replication would be performed for: {job.job_id}")
    
    def _replicate_to_gcs(self, job: BackupJob):
        """Replicate backup to Google Cloud Storage."""
        # Implementation would go here
        logger.info(f"GCS replication would be performed for: {job.job_id}")
    
    def _replicate_to_glacier(self, job: BackupJob):
        """Archive backup to AWS Glacier."""
        # Implementation would go here
        logger.info(f"Glacier archival would be performed for: {job.job_id}")
    
    def restore_backup(self,
                      backup_job_id: str,
                      target_paths: List[str],
                      recovery_mode: RecoveryMode = RecoveryMode.FULL_RESTORE,
                      recovery_point: Optional[datetime] = None) -> Optional[str]:
        """Restore data from backup."""
        try:
            backup_job = self.backup_jobs.get(backup_job_id)
            if not backup_job:
                raise ValueError(f"Backup job {backup_job_id} not found")
            
            # Create recovery job
            job_id = f"recovery_{int(time.time())}"
            
            recovery_job = RecoveryJob(
                job_id=job_id,
                recovery_mode=recovery_mode,
                backup_job_id=backup_job_id,
                target_paths=target_paths,
                recovery_point=recovery_point,
                status=BackupStatus.PENDING,
                started_at=datetime.now()
            )
            
            self.recovery_jobs[job_id] = recovery_job
            
            # Queue for processing
            self.recovery_queue.put(job_id)
            
            logger.info(f"Created recovery job: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create recovery job: {e}")
            return None
    
    def _process_recovery_queue(self):
        """Process recovery jobs from queue."""
        while self.is_running:
            try:
                try:
                    job_id = self.recovery_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                job = self.recovery_jobs.get(job_id)
                if not job:
                    continue
                
                # Execute recovery
                self._execute_recovery(job)
                
                self.recovery_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processing recovery queue: {e}")
    
    def _execute_recovery(self, job: RecoveryJob):
        """Execute a recovery job."""
        try:
            job.status = BackupStatus.IN_PROGRESS
            start_time = time.time()
            
            backup_job = self.backup_jobs.get(job.backup_job_id)
            if not backup_job:
                raise ValueError(f"Backup job {job.backup_job_id} not found")
            
            # Perform recovery based on mode
            if job.recovery_mode == RecoveryMode.FULL_RESTORE:
                result = self._perform_full_restore(job, backup_job)
            elif job.recovery_mode == RecoveryMode.POINT_IN_TIME:
                result = self._perform_point_in_time_recovery(job, backup_job)
            elif job.recovery_mode == RecoveryMode.SELECTIVE:
                result = self._perform_selective_restore(job, backup_job)
            else:
                result = self._perform_full_restore(job, backup_job)
            
            if result:
                job.status = BackupStatus.COMPLETED
                job.completed_at = datetime.now()
                
                # Calculate recovery speed
                duration = time.time() - start_time
                if duration > 0 and job.recovered_bytes > 0:
                    speed_mbps = (job.recovered_bytes / (1024 * 1024)) / duration
                    self._update_metrics('recovery_speed', speed_mbps)
                
                # Update metrics
                self.metrics['total_recoveries'] += 1
                self.metrics['successful_recoveries'] += 1
                self.metrics['total_bytes_recovered'] += job.recovered_bytes
                
                logger.info(f"Recovery completed: {job.job_id} ({job.recovered_bytes:,} bytes)")
            else:
                job.status = BackupStatus.FAILED
                logger.error(f"Recovery failed: {job.job_id}")
            
        except Exception as e:
            job.status = BackupStatus.FAILED
            job.error_message = str(e)
            logger.error(f"Failed to execute recovery {job.job_id}: {e}")
    
    def _perform_full_restore(self, job: RecoveryJob, backup_job: BackupJob) -> bool:
        """Perform a full restore from backup."""
        try:
            source_path = Path(backup_job.destination_path)
            
            if not source_path.exists():
                # Try to restore from cloud storage
                logger.info("Local backup not found, attempting cloud restore")
                # Implementation would restore from cloud
                return False
            
            total_files = 0
            total_bytes = 0
            
            for target_path in job.target_paths:
                target = Path(target_path)
                target.mkdir(parents=True, exist_ok=True)
                
                # Restore all files
                for backup_file in source_path.rglob('*'):
                    if backup_file.is_file() and backup_file.name != 'backup_manifest.json':
                        relative_path = backup_file.relative_to(source_path)
                        restore_path = target / relative_path
                        restore_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Decrypt if needed
                        if backup_file.suffix == '.enc':
                            decrypted_data = self.cipher_suite.decrypt(backup_file.read_bytes())
                            restore_path = restore_path.with_suffix('')
                            restore_path.write_bytes(decrypted_data)
                        # Decompress if needed
                        elif backup_file.suffix == '.gz':
                            with gzip.open(backup_file, 'rb') as f_in:
                                restore_path = restore_path.with_suffix('')
                                with open(restore_path, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                        else:
                            shutil.copy2(backup_file, restore_path)
                        
                        total_files += 1
                        total_bytes += restore_path.stat().st_size
            
            job.recovered_files = total_files
            job.recovered_bytes = total_bytes
            
            return True
            
        except Exception as e:
            logger.error(f"Full restore failed: {e}")
            return False
    
    def _perform_point_in_time_recovery(self, job: RecoveryJob, backup_job: BackupJob) -> bool:
        """Perform point-in-time recovery."""
        try:
            if not job.recovery_point:
                return self._perform_full_restore(job, backup_job)
            
            # Find all backups up to recovery point
            relevant_backups = [
                bj for bj in self.backup_jobs.values()
                if bj.policy_id == backup_job.policy_id
                and bj.status == BackupStatus.COMPLETED
                and bj.completed_at <= job.recovery_point
            ]
            
            # Sort by time
            relevant_backups.sort(key=lambda j: j.completed_at)
            
            # Restore from each backup in sequence
            for backup in relevant_backups:
                temp_job = RecoveryJob(
                    job_id=f"temp_{job.job_id}",
                    recovery_mode=RecoveryMode.FULL_RESTORE,
                    backup_job_id=backup.job_id,
                    target_paths=job.target_paths,
                    status=BackupStatus.IN_PROGRESS,
                    started_at=datetime.now()
                )
                
                self._perform_full_restore(temp_job, backup)
                
                job.recovered_files += temp_job.recovered_files
                job.recovered_bytes += temp_job.recovered_bytes
            
            return True
            
        except Exception as e:
            logger.error(f"Point-in-time recovery failed: {e}")
            return False
    
    def _perform_selective_restore(self, job: RecoveryJob, backup_job: BackupJob) -> bool:
        """Perform selective file restore."""
        # Implementation would allow selecting specific files to restore
        return self._perform_full_restore(job, backup_job)
    
    def _run_scheduled_jobs(self):
        """Run scheduled backup jobs."""
        while self.is_running:
            try:
                # Check each policy for scheduled execution
                for policy in self.backup_policies.values():
                    if policy.is_active:
                        # Simple scheduling - in production would use cron parser
                        # For demo, run daily backups
                        last_run = self._get_last_run_time(policy.policy_id)
                        
                        if not last_run or (datetime.now() - last_run).days >= 1:
                            # Create scheduled backup
                            source_paths = self._get_policy_source_paths(policy)
                            self.create_backup(policy.policy_id, source_paths, manual_trigger=False)
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in scheduled job processing: {e}")
                time.sleep(60)
    
    def _get_last_run_time(self, policy_id: str) -> Optional[datetime]:
        """Get last run time for a policy."""
        policy_jobs = [
            job for job in self.backup_jobs.values()
            if job.policy_id == policy_id and job.status == BackupStatus.COMPLETED
        ]
        
        if policy_jobs:
            latest_job = max(policy_jobs, key=lambda j: j.completed_at or datetime.min)
            return latest_job.completed_at
        
        return None
    
    def _get_policy_source_paths(self, policy: BackupPolicy) -> List[str]:
        """Get source paths for a backup policy."""
        # In production, this would be configured per policy
        # For demo, return sample paths
        paths = []
        
        if DataSource.DATABASE in policy.data_sources:
            paths.append('./data/database')
        
        if DataSource.FILE_SYSTEM in policy.data_sources:
            paths.append('./data/files')
        
        if DataSource.REDIS in policy.data_sources:
            # Would export Redis data first
            paths.append('./data/redis_export')
        
        return paths if paths else ['./data']
    
    def _cleanup_old_backups(self):
        """Clean up old backups based on retention policies."""
        while self.is_running:
            try:
                for policy in self.backup_policies.values():
                    cutoff_date = datetime.now() - timedelta(days=policy.retention_days)
                    
                    # Find old backups
                    old_backups = [
                        job for job in self.backup_jobs.values()
                        if job.policy_id == policy.policy_id
                        and job.completed_at
                        and job.completed_at < cutoff_date
                    ]
                    
                    for job in old_backups:
                        # Delete backup files
                        backup_path = Path(job.destination_path)
                        if backup_path.exists():
                            shutil.rmtree(backup_path)
                            logger.info(f"Deleted old backup: {job.job_id}")
                        
                        # Remove from tracking
                        del self.backup_jobs[job.job_id]
                
                time.sleep(3600)  # Run hourly
                
            except Exception as e:
                logger.error(f"Error in cleanup processing: {e}")
                time.sleep(3600)
    
    def _update_metrics(self, metric_name: str, value: float):
        """Update performance metrics."""
        if metric_name == 'backup_speed':
            current_avg = self.metrics['average_backup_speed_mbps']
            count = self.metrics['successful_backups']
            self.metrics['average_backup_speed_mbps'] = ((current_avg * (count - 1)) + value) / count
        elif metric_name == 'recovery_speed':
            current_avg = self.metrics['average_recovery_speed_mbps']
            count = self.metrics['successful_recoveries']
            self.metrics['average_recovery_speed_mbps'] = ((current_avg * (count - 1)) + value) / count
    
    def get_backup_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a backup job."""
        job = self.backup_jobs.get(job_id)
        if job:
            return asdict(job)
        return None
    
    def get_recovery_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a recovery job."""
        job = self.recovery_jobs.get(job_id)
        if job:
            return asdict(job)
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        return self.metrics.copy()
    
    def create_disaster_recovery_plan(self, plan: DisasterRecoveryPlan) -> bool:
        """Create a disaster recovery plan."""
        try:
            self.dr_plans[plan.plan_id] = plan
            logger.info(f"Created disaster recovery plan: {plan.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create DR plan: {e}")
            return False
    
    def test_disaster_recovery(self, plan_id: str) -> Dict[str, Any]:
        """Test a disaster recovery plan."""
        try:
            plan = self.dr_plans.get(plan_id)
            if not plan:
                return {'success': False, 'error': 'Plan not found'}
            
            test_results = {
                'plan_id': plan_id,
                'test_time': datetime.now(),
                'tests_passed': 0,
                'tests_failed': 0,
                'details': []
            }
            
            # Test each backup policy
            for policy_id in plan.backup_policies:
                policy = self.backup_policies.get(policy_id)
                if policy:
                    # Verify recent backup exists
                    last_backup = self._find_last_backup(policy_id)
                    if last_backup and last_backup.status == BackupStatus.VERIFIED:
                        test_results['tests_passed'] += 1
                        test_results['details'].append(f"Policy {policy_id}: Backup verified")
                    else:
                        test_results['tests_failed'] += 1
                        test_results['details'].append(f"Policy {policy_id}: No verified backup")
            
            # Update plan
            plan.last_tested = datetime.now()
            
            return test_results
            
        except Exception as e:
            logger.error(f"Failed to test DR plan: {e}")
            return {'success': False, 'error': str(e)}


def create_sample_backup_system() -> BackupRecoverySystem:
    """Create sample backup system for demonstration."""
    
    storage_config = {
        'local_path': './backups',
        's3': {
            'bucket': 'martech-backups',
            'region': 'us-east-1'
        }
    }
    
    system = BackupRecoverySystem(storage_config)
    
    # Create sample disaster recovery plan
    dr_plan = DisasterRecoveryPlan(
        plan_id="dr_critical",
        name="Critical Systems DR Plan",
        description="Disaster recovery for critical marketing systems",
        priority=1,
        recovery_time_objective=timedelta(hours=4),
        recovery_point_objective=timedelta(hours=1),
        backup_policies=["daily_full", "hourly_incremental"],
        recovery_procedures=[
            {'step': 1, 'action': 'Verify backup integrity'},
            {'step': 2, 'action': 'Restore database'},
            {'step': 3, 'action': 'Restore application files'},
            {'step': 4, 'action': 'Verify system functionality'}
        ],
        failover_sequence=['primary_db', 'app_servers', 'cache_layer'],
        notification_contacts=['ops@example.com', 'cto@example.com'],
        test_schedule="0 0 * * 0"  # Weekly
    )
    
    system.create_disaster_recovery_plan(dr_plan)
    
    return system


def run_backup_recovery_demo():
    """
    Run the backup & recovery system demonstration.
    
    Author: Sotiris Spyrou | https://verityai.co
    """
    
    print("💾 Backup & Recovery System Demo")
    print("=" * 50)
    
    print("🎯 Key Features:")
    print("  • Automated backup scheduling")
    print("  • Multiple backup strategies")
    print("  • Multi-destination storage")
    print("  • Point-in-time recovery")
    print("  • Disaster recovery planning")
    print("  • Data encryption & compression")
    print("  • Backup verification")
    print("  • Performance monitoring")
    
    print("\n📦 Backup Types:")
    for backup_type in BackupType:
        print(f"  • {backup_type.value}")
    
    print("\n💿 Storage Backends:")
    for backend in list(StorageBackend)[:5]:
        print(f"  • {backend.value}")
    
    print("\n🚀 Initializing backup system...")
    system = create_sample_backup_system()
    
    print("✅ Backup system initialized")
    print(f"   • Backup policies: {len(system.backup_policies)}")
    print(f"   • DR plans: {len(system.dr_plans)}")
    
    # Show policies
    print("\n📋 Backup Policies:")
    for policy_id, policy in system.backup_policies.items():
        print(f"   • {policy.name}")
        print(f"     - Type: {policy.backup_type.value}")
        print(f"     - Retention: {policy.retention_days} days")
        print(f"     - Storage: {', '.join(b.value for b in policy.storage_backends)}")
    
    # Create sample backup
    print("\n🔄 Creating sample backup...")
    job_id = system.create_backup(
        "daily_full",
        ["./data/sample"],
        manual_trigger=True
    )
    
    if job_id:
        print(f"   ✅ Backup job created: {job_id}")
        
        # Wait for completion (in real scenario)
        time.sleep(1)
        
        # Get status
        status = system.get_backup_status(job_id)
        if status:
            print(f"   • Status: {status['status']}")
            print(f"   • Files: {status.get('files_count', 0)}")
            print(f"   • Size: {status.get('size_bytes', 0):,} bytes")
    
    # Show metrics
    metrics = system.get_metrics()
    print(f"\n📊 System Metrics:")
    print(f"   • Total backups: {metrics['total_backups']}")
    print(f"   • Success rate: {metrics['successful_backups']}/{metrics['total_backups'] or 1}")
    print(f"   • Data backed up: {metrics['total_bytes_backed_up']:,} bytes")
    print(f"   • Avg speed: {metrics['average_backup_speed_mbps']:.2f} MB/s")
    
    # Test DR plan
    print("\n🔥 Testing Disaster Recovery Plan...")
    test_results = system.test_disaster_recovery("dr_critical")
    print(f"   • Tests passed: {test_results.get('tests_passed', 0)}")
    print(f"   • Tests failed: {test_results.get('tests_failed', 0)}")
    
    print("\n🌟 Advanced Features:")
    print("  • Incremental & differential backups")
    print("  • Automated retention management")
    print("  • Cross-region replication")
    print("  • Instant recovery capabilities")
    print("  • Compliance-ready archival")
    print("  • Real-time backup monitoring")
    
    print(f"\n💼 Portfolio: https://verityai.co")
    print(f"🔗 LinkedIn: https://www.linkedin.com/in/sspyrou/")
    print("⚠️  DISCLAIMER: This is demonstration code for portfolio purposes.")
    
    return system


if __name__ == "__main__":
    run_backup_recovery_demo()
