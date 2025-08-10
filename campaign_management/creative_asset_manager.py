"""
Creative Asset Manager for MarTech Integration Hub

Comprehensive creative asset management system for multi-channel marketing campaigns
with automated optimization, A/B testing, and performance-driven content creation.

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
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple, BinaryIO
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import mimetypes
import base64
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from collections import defaultdict, Counter
import threading
import queue
import requests
from urllib.parse import urlparse
import boto3
from botocore.exceptions import NoCredentialsError
import redis
from jinja2 import Template
from textblob import TextBlob
import re

logger = logging.getLogger(__name__)


class AssetType(Enum):
    """Creative asset types."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    HTML = "html"
    PDF = "pdf"
    TEMPLATE = "template"
    BANNER = "banner"
    LOGO = "logo"
    SOCIAL_POST = "social_post"
    EMAIL_TEMPLATE = "email_template"
    LANDING_PAGE = "landing_page"


class AssetStatus(Enum):
    """Asset status types."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    TESTING = "testing"


class AssetChannel(Enum):
    """Marketing channels for assets."""
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    DISPLAY_ADS = "display_ads"
    SEARCH_ADS = "search_ads"
    VIDEO_ADS = "video_ads"
    PRINT = "print"
    WEB = "web"
    MOBILE_APP = "mobile_app"
    OUT_OF_HOME = "out_of_home"
    PODCAST = "podcast"


class OptimizationType(Enum):
    """Asset optimization types."""
    RESIZE = "resize"
    COMPRESS = "compress"
    FORMAT_CONVERT = "format_convert"
    COLOR_ENHANCE = "color_enhance"
    CROP = "crop"
    FILTER_APPLY = "filter_apply"
    TEXT_OVERLAY = "text_overlay"
    WATERMARK = "watermark"
    QUALITY_ENHANCE = "quality_enhance"
    BATCH_PROCESS = "batch_process"


class PerformanceMetric(Enum):
    """Asset performance metrics."""
    IMPRESSIONS = "impressions"
    CLICKS = "clicks"
    CTR = "ctr"
    CONVERSIONS = "conversions"
    ENGAGEMENT_RATE = "engagement_rate"
    SHARES = "shares"
    LIKES = "likes"
    COMMENTS = "comments"
    VIEW_TIME = "view_time"
    BOUNCE_RATE = "bounce_rate"
    COMPLETION_RATE = "completion_rate"


@dataclass
class AssetMetadata:
    """Creative asset metadata."""
    file_name: str
    file_size: int
    mime_type: str
    dimensions: Optional[Tuple[int, int]] = None
    duration: Optional[float] = None  # For video/audio
    color_palette: List[str] = field(default_factory=list)
    dominant_colors: List[str] = field(default_factory=list)
    text_content: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    file_hash: Optional[str] = None
    thumbnail_path: Optional[str] = None


@dataclass
class AssetVersion:
    """Asset version information."""
    version_id: str
    version_number: int
    file_path: str
    created_by: str
    created_at: datetime
    changes_description: str
    metadata: AssetMetadata
    is_current: bool = False
    parent_version_id: Optional[str] = None


@dataclass
class AssetPerformance:
    """Asset performance tracking."""
    asset_id: str
    channel: AssetChannel
    campaign_id: Optional[str]
    metrics: Dict[PerformanceMetric, float]
    date_range: Tuple[datetime, datetime]
    impressions_breakdown: Dict[str, int] = field(default_factory=dict)
    audience_segments: Dict[str, Dict] = field(default_factory=dict)
    geographic_performance: Dict[str, Dict] = field(default_factory=dict)
    device_performance: Dict[str, Dict] = field(default_factory=dict)
    time_performance: Dict[str, Dict] = field(default_factory=dict)


@dataclass
class CreativeAsset:
    """Creative asset definition."""
    asset_id: str
    name: str
    description: str
    asset_type: AssetType
    status: AssetStatus
    tags: List[str]
    channels: List[AssetChannel]
    current_version: AssetVersion
    versions: List[AssetVersion] = field(default_factory=list)
    performance_history: List[AssetPerformance] = field(default_factory=list)
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expiry_date: Optional[datetime] = None
    brand_guidelines: Dict[str, Any] = field(default_factory=dict)
    usage_rights: Dict[str, Any] = field(default_factory=dict)
    approval_workflow: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssetTemplate:
    """Reusable asset template."""
    template_id: str
    name: str
    description: str
    asset_type: AssetType
    channels: List[AssetChannel]
    template_content: str  # JSON or template format
    placeholders: List[str]  # Dynamic content placeholders
    styling_options: Dict[str, Any]
    created_by: str
    created_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    is_active: bool = True


@dataclass
class OptimizationRule:
    """Asset optimization rule."""
    rule_id: str
    name: str
    description: str
    asset_type: AssetType
    channels: List[AssetChannel]
    conditions: Dict[str, Any]  # Conditions that trigger optimization
    optimizations: List[OptimizationType]
    parameters: Dict[str, Any]
    is_active: bool = True
    priority: int = 0
    success_rate: float = 0.0
    usage_count: int = 0


class CreativeAssetManager:
    """
    Comprehensive creative asset management system.
    
    Features:
    - Multi-format asset storage and management
    - Automated asset optimization and resizing
    - Performance tracking across channels
    - Version control and approval workflows
    - AI-powered content analysis and tagging
    - Template-based asset generation
    - Brand compliance checking
    - A/B testing integration
    """
    
    def __init__(self,
                 storage_path: str = "./assets",
                 cdn_config: Optional[Dict[str, str]] = None,
                 redis_host: str = 'localhost',
                 redis_port: int = 6379,
                 aws_config: Optional[Dict[str, str]] = None):
        
        # Storage configuration
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        for subdir in ['originals', 'optimized', 'thumbnails', 'templates', 'temp']:
            (self.storage_path / subdir).mkdir(exist_ok=True)
        
        # CDN and cloud storage
        self.cdn_config = cdn_config or {}
        self.aws_config = aws_config or {}
        
        # Redis connection for caching
        try:
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
            self.redis_client.ping()
            self.redis_available = True
        except:
            self.redis_available = False
            logger.warning("Redis not available, using in-memory cache")
        
        # In-memory storage
        self.assets: Dict[str, CreativeAsset] = {}
        self.templates: Dict[str, AssetTemplate] = {}
        self.optimization_rules: Dict[str, OptimizationRule] = {}
        self.performance_cache: Dict[str, Dict] = {}
        
        # Processing queues
        self.optimization_queue = queue.Queue()
        self.analysis_queue = queue.Queue()
        
        # Threading for background processing
        self.processing_threads = []
        self.is_processing = True
        
        # AI models for content analysis
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.color_analyzer = None  # Initialize on first use
        
        # Start background processing
        self._start_background_processing()
        
        # Create default optimization rules
        self._create_default_optimization_rules()
        
        logger.info("Creative Asset Manager initialized successfully")
    
    def _start_background_processing(self):
        """Start background processing threads."""
        try:
            # Optimization processing thread
            optimization_thread = threading.Thread(target=self._process_optimization_queue, daemon=True)
            optimization_thread.start()
            self.processing_threads.append(optimization_thread)
            
            # Analysis processing thread
            analysis_thread = threading.Thread(target=self._process_analysis_queue, daemon=True)
            analysis_thread.start()
            self.processing_threads.append(analysis_thread)
            
            logger.info(f"Started {len(self.processing_threads)} background processing threads")
            
        except Exception as e:
            logger.error(f"Failed to start background processing: {e}")
    
    def _create_default_optimization_rules(self):
        """Create default asset optimization rules."""
        try:
            default_rules = [
                OptimizationRule(
                    rule_id="social_media_resize",
                    name="Social Media Auto-Resize",
                    description="Automatically resize images for social media platforms",
                    asset_type=AssetType.IMAGE,
                    channels=[AssetChannel.SOCIAL_MEDIA],
                    conditions={"max_width": 1200, "max_height": 1200},
                    optimizations=[OptimizationType.RESIZE, OptimizationType.COMPRESS],
                    parameters={"quality": 85, "format": "JPEG"}
                ),
                OptimizationRule(
                    rule_id="email_optimize",
                    name="Email Image Optimization",
                    description="Optimize images for email campaigns",
                    asset_type=AssetType.IMAGE,
                    channels=[AssetChannel.EMAIL],
                    conditions={"max_size_kb": 100},
                    optimizations=[OptimizationType.COMPRESS, OptimizationType.RESIZE],
                    parameters={"max_width": 600, "quality": 75}
                ),
                OptimizationRule(
                    rule_id="display_ad_format",
                    name="Display Ad Format Optimization",
                    description="Ensure display ads meet format requirements",
                    asset_type=AssetType.BANNER,
                    channels=[AssetChannel.DISPLAY_ADS],
                    conditions={"required_formats": ["JPG", "PNG", "GIF"]},
                    optimizations=[OptimizationType.FORMAT_CONVERT, OptimizationType.COMPRESS],
                    parameters={"formats": ["JPG", "PNG"], "max_size_kb": 150}
                )
            ]
            
            for rule in default_rules:
                self.optimization_rules[rule.rule_id] = rule
            
            logger.info(f"Created {len(default_rules)} default optimization rules")
            
        except Exception as e:
            logger.error(f"Failed to create default optimization rules: {e}")
    
    def upload_asset(self,
                    file_data: Union[str, bytes, BinaryIO],
                    file_name: str,
                    asset_name: str,
                    asset_type: AssetType,
                    channels: List[AssetChannel],
                    description: str = "",
                    tags: List[str] = None,
                    created_by: str = "system") -> Optional[str]:
        """Upload and process a new creative asset."""
        try:
            asset_id = str(uuid.uuid4())
            tags = tags or []
            
            # Determine file path
            file_extension = Path(file_name).suffix.lower()
            stored_filename = f"{asset_id}{file_extension}"
            file_path = self.storage_path / "originals" / stored_filename
            
            # Save file
            if isinstance(file_data, str):  # File path
                shutil.copy2(file_data, file_path)
            elif isinstance(file_data, bytes):
                with open(file_path, 'wb') as f:
                    f.write(file_data)
            else:  # File-like object
                with open(file_path, 'wb') as f:
                    shutil.copyfileobj(file_data, f)
            
            # Generate file metadata
            metadata = self._analyze_asset_metadata(file_path, file_name)
            
            # Create asset version
            version = AssetVersion(
                version_id=f"{asset_id}_v1",
                version_number=1,
                file_path=str(file_path),
                created_by=created_by,
                created_at=datetime.now(),
                changes_description="Initial upload",
                metadata=metadata,
                is_current=True
            )
            
            # Create asset
            asset = CreativeAsset(
                asset_id=asset_id,
                name=asset_name,
                description=description,
                asset_type=asset_type,
                status=AssetStatus.DRAFT,
                tags=tags,
                channels=channels,
                current_version=version,
                versions=[version],
                created_by=created_by
            )
            
            # Store asset
            self.assets[asset_id] = asset
            
            # Queue for analysis and optimization
            self.analysis_queue.put(asset_id)
            self.optimization_queue.put(asset_id)
            
            # Store in Redis if available
            if self.redis_available:
                self.redis_client.hset(
                    f"asset:{asset_id}",
                    mapping={
                        'name': asset.name,
                        'type': asset.asset_type.value,
                        'status': asset.status.value,
                        'created_at': asset.created_at.isoformat(),
                        'file_path': str(file_path)
                    }
                )
            
            logger.info(f"Uploaded asset: {asset_name} ({asset_id})")
            return asset_id
            
        except Exception as e:
            logger.error(f"Failed to upload asset: {e}")
            return None
    
    def _analyze_asset_metadata(self, file_path: Path, file_name: str) -> AssetMetadata:
        """Analyze asset file and extract metadata."""
        try:
            stat = file_path.stat()
            file_size = stat.st_size
            mime_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
            
            # Calculate file hash
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            metadata = AssetMetadata(
                file_name=file_name,
                file_size=file_size,
                mime_type=mime_type,
                file_hash=file_hash
            )
            
            # Extract image-specific metadata
            if mime_type.startswith('image/'):
                try:
                    with Image.open(file_path) as img:
                        metadata.dimensions = img.size
                        
                        # Extract dominant colors
                        metadata.dominant_colors = self._extract_dominant_colors(img)
                        
                        # Generate thumbnail
                        thumbnail_path = self._generate_thumbnail(file_path, img)
                        metadata.thumbnail_path = thumbnail_path
                        
                except Exception as e:
                    logger.warning(f"Failed to analyze image metadata: {e}")
            
            # Extract video-specific metadata
            elif mime_type.startswith('video/'):
                try:
                    cap = cv2.VideoCapture(str(file_path))
                    if cap.isOpened():
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        
                        metadata.dimensions = (width, height)
                        if fps > 0:
                            metadata.duration = frame_count / fps
                        
                        # Generate video thumbnail
                        thumbnail_path = self._generate_video_thumbnail(file_path, cap)
                        metadata.thumbnail_path = thumbnail_path
                    
                    cap.release()
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze video metadata: {e}")
            
            # Extract text content for text-based assets
            elif mime_type.startswith('text/') or file_path.suffix.lower() in ['.txt', '.md', '.html']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        metadata.text_content = content[:5000]  # Limit content length
                        metadata.keywords = self._extract_keywords(content)
                        
                except Exception as e:
                    logger.warning(f"Failed to extract text content: {e}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to analyze asset metadata: {e}")
            return AssetMetadata(file_name=file_name, file_size=0, mime_type='application/octet-stream')
    
    def _extract_dominant_colors(self, img: Image.Image, num_colors: int = 5) -> List[str]:
        """Extract dominant colors from an image."""
        try:
            # Convert image to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize image for faster processing
            img = img.resize((150, 150))
            
            # Convert to numpy array and reshape
            data = np.array(img)
            data = data.reshape((-1, 3))
            
            # Use K-means clustering to find dominant colors
            kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
            kmeans.fit(data)
            
            # Convert colors to hex format
            colors = []
            for color in kmeans.cluster_centers_:
                hex_color = '#{:02x}{:02x}{:02x}'.format(int(color[0]), int(color[1]), int(color[2]))
                colors.append(hex_color)
            
            return colors
            
        except Exception as e:
            logger.warning(f"Failed to extract dominant colors: {e}")
            return []
    
    def _generate_thumbnail(self, file_path: Path, img: Image.Image) -> Optional[str]:
        """Generate thumbnail for image asset."""
        try:
            thumbnail_filename = f"{file_path.stem}_thumb.jpg"
            thumbnail_path = self.storage_path / "thumbnails" / thumbnail_filename
            
            # Create thumbnail
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            img.save(thumbnail_path, 'JPEG', quality=85)
            
            return str(thumbnail_path)
            
        except Exception as e:
            logger.warning(f"Failed to generate thumbnail: {e}")
            return None
    
    def _generate_video_thumbnail(self, file_path: Path, cap: cv2.VideoCapture) -> Optional[str]:
        """Generate thumbnail for video asset."""
        try:
            # Seek to middle of video
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
            
            ret, frame = cap.read()
            if ret:
                thumbnail_filename = f"{file_path.stem}_thumb.jpg"
                thumbnail_path = self.storage_path / "thumbnails" / thumbnail_filename
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image and save
                img = Image.fromarray(frame_rgb)
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, 'JPEG', quality=85)
                
                return str(thumbnail_path)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to generate video thumbnail: {e}")
            return None
    
    def _extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """Extract keywords from text content."""
        try:
            # Clean text
            text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
            text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
            text = text.lower()
            
            # Use TextBlob for basic keyword extraction
            blob = TextBlob(text)
            
            # Extract noun phrases
            noun_phrases = blob.noun_phrases
            
            # Extract single important words
            words = blob.words
            important_words = [word for word in words if len(word) > 3]
            
            # Combine and get most frequent
            all_keywords = list(noun_phrases) + important_words
            keyword_counts = Counter(all_keywords)
            
            return [keyword for keyword, count in keyword_counts.most_common(max_keywords)]
            
        except Exception as e:
            logger.warning(f"Failed to extract keywords: {e}")
            return []
    
    def _process_optimization_queue(self):
        """Background thread to process asset optimizations."""
        while self.is_processing:
            try:
                # Get asset from queue (blocking with timeout)
                try:
                    asset_id = self.optimization_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                if asset_id in self.assets:
                    self._optimize_asset(asset_id)
                
                self.optimization_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in optimization processing: {e}")
    
    def _process_analysis_queue(self):
        """Background thread to process asset analysis."""
        while self.is_processing:
            try:
                # Get asset from queue (blocking with timeout)
                try:
                    asset_id = self.analysis_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                if asset_id in self.assets:
                    self._analyze_asset_content(asset_id)
                
                self.analysis_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in analysis processing: {e}")
    
    def _optimize_asset(self, asset_id: str):
        """Apply optimization rules to an asset."""
        try:
            asset = self.assets[asset_id]
            applicable_rules = []
            
            # Find applicable optimization rules
            for rule in self.optimization_rules.values():
                if (rule.is_active and 
                    rule.asset_type == asset.asset_type and 
                    any(channel in asset.channels for channel in rule.channels)):
                    applicable_rules.append(rule)
            
            if not applicable_rules:
                return
            
            # Sort by priority
            applicable_rules.sort(key=lambda r: r.priority, reverse=True)
            
            # Apply optimizations
            for rule in applicable_rules:
                self._apply_optimization_rule(asset, rule)
                rule.usage_count += 1
            
            logger.info(f"Applied {len(applicable_rules)} optimization rules to asset {asset_id}")
            
        except Exception as e:
            logger.error(f"Failed to optimize asset {asset_id}: {e}")
    
    def _apply_optimization_rule(self, asset: CreativeAsset, rule: OptimizationRule):
        """Apply a specific optimization rule to an asset."""
        try:
            original_path = Path(asset.current_version.file_path)
            
            if not original_path.exists():
                logger.warning(f"Original file not found: {original_path}")
                return
            
            for optimization in rule.optimizations:
                if optimization == OptimizationType.RESIZE:
                    self._resize_asset(original_path, rule.parameters)
                elif optimization == OptimizationType.COMPRESS:
                    self._compress_asset(original_path, rule.parameters)
                elif optimization == OptimizationType.FORMAT_CONVERT:
                    self._convert_asset_format(original_path, rule.parameters)
                elif optimization == OptimizationType.COLOR_ENHANCE:
                    self._enhance_asset_colors(original_path, rule.parameters)
                elif optimization == OptimizationType.CROP:
                    self._crop_asset(original_path, rule.parameters)
            
            rule.success_rate = min(1.0, rule.success_rate + 0.1)  # Increment success rate
            
        except Exception as e:
            logger.error(f"Failed to apply optimization rule {rule.rule_id}: {e}")
    
    def _resize_asset(self, file_path: Path, parameters: Dict[str, Any]):
        """Resize image asset."""
        try:
            if not file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                return
            
            max_width = parameters.get('max_width', 1200)
            max_height = parameters.get('max_height', 1200)
            
            with Image.open(file_path) as img:
                # Calculate new size while maintaining aspect ratio
                ratio = min(max_width / img.width, max_height / img.height)
                
                if ratio < 1.0:  # Only resize if image is larger
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    
                    # Save optimized version
                    optimized_path = self.storage_path / "optimized" / f"resized_{file_path.name}"
                    img.save(optimized_path, quality=parameters.get('quality', 85))
                    
                    logger.debug(f"Resized asset: {file_path.name} to {new_size}")
            
        except Exception as e:
            logger.warning(f"Failed to resize asset: {e}")
    
    def _compress_asset(self, file_path: Path, parameters: Dict[str, Any]):
        """Compress image asset."""
        try:
            if not file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                return
            
            quality = parameters.get('quality', 75)
            max_size_kb = parameters.get('max_size_kb', 500)
            
            with Image.open(file_path) as img:
                # Try different quality levels to meet size requirement
                for q in range(quality, 20, -10):
                    optimized_path = self.storage_path / "optimized" / f"compressed_{file_path.name}"
                    
                    if file_path.suffix.lower() == '.png':
                        img.save(optimized_path, 'PNG', optimize=True)
                    else:
                        img.save(optimized_path, 'JPEG', quality=q, optimize=True)
                    
                    # Check file size
                    if optimized_path.stat().st_size <= max_size_kb * 1024:
                        logger.debug(f"Compressed asset: {file_path.name} (quality: {q})")
                        break
            
        except Exception as e:
            logger.warning(f"Failed to compress asset: {e}")
    
    def _convert_asset_format(self, file_path: Path, parameters: Dict[str, Any]):
        """Convert asset to different format."""
        try:
            target_formats = parameters.get('formats', ['JPEG'])
            
            if not file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                return
            
            with Image.open(file_path) as img:
                for fmt in target_formats:
                    if fmt.upper() == 'JPEG':
                        converted_path = self.storage_path / "optimized" / f"{file_path.stem}.jpg"
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        img.save(converted_path, 'JPEG', quality=parameters.get('quality', 85))
                    
                    elif fmt.upper() == 'PNG':
                        converted_path = self.storage_path / "optimized" / f"{file_path.stem}.png"
                        img.save(converted_path, 'PNG', optimize=True)
                    
                    logger.debug(f"Converted asset: {file_path.name} to {fmt}")
            
        except Exception as e:
            logger.warning(f"Failed to convert asset format: {e}")
    
    def _enhance_asset_colors(self, file_path: Path, parameters: Dict[str, Any]):
        """Enhance asset colors."""
        try:
            if not file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                return
            
            brightness = parameters.get('brightness', 1.0)
            contrast = parameters.get('contrast', 1.0)
            saturation = parameters.get('saturation', 1.0)
            
            with Image.open(file_path) as img:
                # Apply enhancements
                if brightness != 1.0:
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(brightness)
                
                if contrast != 1.0:
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(contrast)
                
                if saturation != 1.0:
                    enhancer = ImageEnhance.Color(img)
                    img = enhancer.enhance(saturation)
                
                # Save enhanced version
                enhanced_path = self.storage_path / "optimized" / f"enhanced_{file_path.name}"
                img.save(enhanced_path, quality=parameters.get('quality', 90))
                
                logger.debug(f"Enhanced asset colors: {file_path.name}")
            
        except Exception as e:
            logger.warning(f"Failed to enhance asset colors: {e}")
    
    def _crop_asset(self, file_path: Path, parameters: Dict[str, Any]):
        """Crop asset to specified dimensions."""
        try:
            if not file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                return
            
            crop_box = parameters.get('crop_box')  # (left, top, right, bottom)
            target_ratio = parameters.get('aspect_ratio')  # width/height ratio
            
            with Image.open(file_path) as img:
                if crop_box:
                    img = img.crop(crop_box)
                elif target_ratio:
                    # Smart crop to aspect ratio
                    current_ratio = img.width / img.height
                    
                    if current_ratio > target_ratio:
                        # Image is too wide, crop width
                        new_width = int(img.height * target_ratio)
                        left = (img.width - new_width) // 2
                        img = img.crop((left, 0, left + new_width, img.height))
                    elif current_ratio < target_ratio:
                        # Image is too tall, crop height
                        new_height = int(img.width / target_ratio)
                        top = (img.height - new_height) // 2
                        img = img.crop((0, top, img.width, top + new_height))
                
                # Save cropped version
                cropped_path = self.storage_path / "optimized" / f"cropped_{file_path.name}"
                img.save(cropped_path, quality=parameters.get('quality', 90))
                
                logger.debug(f"Cropped asset: {file_path.name}")
            
        except Exception as e:
            logger.warning(f"Failed to crop asset: {e}")
    
    def _analyze_asset_content(self, asset_id: str):
        """Perform AI-powered content analysis on asset."""
        try:
            asset = self.assets[asset_id]
            
            # Analyze based on asset type
            if asset.asset_type == AssetType.IMAGE:
                self._analyze_image_content(asset)
            elif asset.asset_type == AssetType.TEXT:
                self._analyze_text_content(asset)
            elif asset.asset_type == AssetType.VIDEO:
                self._analyze_video_content(asset)
            
            logger.debug(f"Analyzed content for asset: {asset_id}")
            
        except Exception as e:
            logger.error(f"Failed to analyze asset content: {e}")
    
    def _analyze_image_content(self, asset: CreativeAsset):
        """Analyze image content for objects, text, and features."""
        try:
            # This would integrate with computer vision APIs like Google Vision, AWS Rekognition
            # For demo, we'll simulate analysis results
            
            analysis_results = {
                'objects_detected': ['person', 'product', 'text', 'logo'],
                'text_detected': 'Sample detected text from image',
                'faces_count': 2,
                'brand_elements': ['logo', 'product'],
                'emotion_analysis': {'positive': 0.8, 'neutral': 0.15, 'negative': 0.05},
                'quality_score': 0.85,
                'composition_score': 0.78
            }
            
            # Update asset tags based on analysis
            detected_objects = analysis_results.get('objects_detected', [])
            asset.tags.extend([obj for obj in detected_objects if obj not in asset.tags])
            
            # Store analysis results in metadata
            if not hasattr(asset, 'analysis_results'):
                asset.analysis_results = {}
            asset.analysis_results['image_analysis'] = analysis_results
            
        except Exception as e:
            logger.warning(f"Failed to analyze image content: {e}")
    
    def _analyze_text_content(self, asset: CreativeAsset):
        """Analyze text content for sentiment, topics, and readability."""
        try:
            text_content = asset.current_version.metadata.text_content
            if not text_content:
                return
            
            # Sentiment analysis
            blob = TextBlob(text_content)
            sentiment = blob.sentiment
            
            # Basic readability metrics
            word_count = len(blob.words)
            sentence_count = len(blob.sentences)
            avg_words_per_sentence = word_count / max(sentence_count, 1)
            
            # Extract topics (simple keyword-based)
            topics = asset.current_version.metadata.keywords[:5]
            
            analysis_results = {
                'sentiment_polarity': sentiment.polarity,
                'sentiment_subjectivity': sentiment.subjectivity,
                'word_count': word_count,
                'sentence_count': sentence_count,
                'avg_words_per_sentence': avg_words_per_sentence,
                'readability_score': min(1.0, 1.0 - (avg_words_per_sentence - 15) * 0.05),
                'main_topics': topics,
                'language_detected': str(blob.detect_language()) if hasattr(blob, 'detect_language') else 'en'
            }
            
            # Update tags based on sentiment
            if sentiment.polarity > 0.1:
                asset.tags.append('positive')
            elif sentiment.polarity < -0.1:
                asset.tags.append('negative')
            else:
                asset.tags.append('neutral')
            
            # Store analysis results
            if not hasattr(asset, 'analysis_results'):
                asset.analysis_results = {}
            asset.analysis_results['text_analysis'] = analysis_results
            
        except Exception as e:
            logger.warning(f"Failed to analyze text content: {e}")
    
    def _analyze_video_content(self, asset: CreativeAsset):
        """Analyze video content for scenes, objects, and audio."""
        try:
            # This would integrate with video analysis APIs
            # For demo, we'll simulate analysis results
            
            duration = asset.current_version.metadata.duration or 30.0
            
            analysis_results = {
                'duration': duration,
                'scene_changes': max(1, int(duration / 5)),  # Estimate scene changes
                'dominant_colors': asset.current_version.metadata.dominant_colors,
                'estimated_objects': ['product', 'person', 'text', 'brand_logo'],
                'audio_detected': True,
                'motion_intensity': 'medium',
                'visual_complexity': 'high',
                'brand_exposure_time': duration * 0.3  # 30% brand exposure
            }
            
            # Add video-specific tags
            if duration < 15:
                asset.tags.append('short-form')
            elif duration > 60:
                asset.tags.append('long-form')
            
            if analysis_results['motion_intensity'] == 'high':
                asset.tags.append('dynamic')
            
            # Store analysis results
            if not hasattr(asset, 'analysis_results'):
                asset.analysis_results = {}
            asset.analysis_results['video_analysis'] = analysis_results
            
        except Exception as e:
            logger.warning(f"Failed to analyze video content: {e}")
    
    def get_asset(self, asset_id: str) -> Optional[CreativeAsset]:
        """Get asset by ID."""
        return self.assets.get(asset_id)
    
    def search_assets(self,
                     query: str = "",
                     asset_type: Optional[AssetType] = None,
                     channels: Optional[List[AssetChannel]] = None,
                     tags: Optional[List[str]] = None,
                     status: Optional[AssetStatus] = None,
                     limit: int = 50) -> List[CreativeAsset]:
        """Search assets based on criteria."""
        try:
            results = list(self.assets.values())
            
            # Apply filters
            if asset_type:
                results = [a for a in results if a.asset_type == asset_type]
            
            if channels:
                results = [a for a in results if any(ch in a.channels for ch in channels)]
            
            if tags:
                results = [a for a in results if any(tag in a.tags for tag in tags)]
            
            if status:
                results = [a for a in results if a.status == status]
            
            # Text search
            if query:
                query_lower = query.lower()
                filtered_results = []
                
                for asset in results:
                    # Search in name, description, tags, and keywords
                    searchable_text = f"{asset.name} {asset.description} {' '.join(asset.tags)}"
                    if asset.current_version.metadata.keywords:
                        searchable_text += f" {' '.join(asset.current_version.metadata.keywords)}"
                    
                    if query_lower in searchable_text.lower():
                        filtered_results.append(asset)
                
                results = filtered_results
            
            # Sort by creation date (newest first)
            results.sort(key=lambda a: a.created_at, reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to search assets: {e}")
            return []
    
    def get_asset_performance(self, asset_id: str, 
                            date_range: Optional[Tuple[datetime, datetime]] = None) -> List[AssetPerformance]:
        """Get performance data for an asset."""
        try:
            asset = self.assets.get(asset_id)
            if not asset:
                return []
            
            # Filter by date range if specified
            performances = asset.performance_history
            if date_range:
                start_date, end_date = date_range
                performances = [
                    p for p in performances 
                    if p.date_range[0] >= start_date and p.date_range[1] <= end_date
                ]
            
            return performances
            
        except Exception as e:
            logger.error(f"Failed to get asset performance: {e}")
            return []
    
    def record_asset_performance(self, asset_id: str, performance: AssetPerformance) -> bool:
        """Record performance data for an asset."""
        try:
            asset = self.assets.get(asset_id)
            if not asset:
                return False
            
            asset.performance_history.append(performance)
            
            # Update performance cache
            cache_key = f"performance_{asset_id}"
            if cache_key not in self.performance_cache:
                self.performance_cache[cache_key] = []
            self.performance_cache[cache_key].append(asdict(performance))
            
            logger.debug(f"Recorded performance data for asset: {asset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record asset performance: {e}")
            return False
    
    def create_asset_template(self, template: AssetTemplate) -> bool:
        """Create a new asset template."""
        try:
            self.templates[template.template_id] = template
            
            logger.info(f"Created asset template: {template.name} ({template.template_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create asset template: {e}")
            return False
    
    def generate_from_template(self, template_id: str, 
                              placeholder_values: Dict[str, str],
                              output_name: str,
                              channels: List[AssetChannel],
                              created_by: str = "system") -> Optional[str]:
        """Generate asset from template."""
        try:
            template = self.templates.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # Replace placeholders in template content
            content = template.template_content
            for placeholder, value in placeholder_values.items():
                content = content.replace(f"{{{{{placeholder}}}}}", value)
            
            # Create temporary file with generated content
            temp_path = self.storage_path / "temp" / f"{uuid.uuid4()}.html"
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Upload as new asset
            asset_id = self.upload_asset(
                file_data=str(temp_path),
                file_name=f"{output_name}.html",
                asset_name=output_name,
                asset_type=template.asset_type,
                channels=channels,
                description=f"Generated from template: {template.name}",
                tags=["template-generated", template_id],
                created_by=created_by
            )
            
            # Update template usage count
            template.usage_count += 1
            
            # Clean up temp file
            temp_path.unlink()
            
            return asset_id
            
        except Exception as e:
            logger.error(f"Failed to generate asset from template: {e}")
            return None
    
    def get_asset_insights(self, asset_id: str) -> Dict[str, Any]:
        """Get comprehensive insights about an asset."""
        try:
            asset = self.assets.get(asset_id)
            if not asset:
                return {}
            
            # Calculate performance metrics
            total_impressions = sum(
                p.metrics.get(PerformanceMetric.IMPRESSIONS, 0) 
                for p in asset.performance_history
            )
            
            total_clicks = sum(
                p.metrics.get(PerformanceMetric.CLICKS, 0) 
                for p in asset.performance_history
            )
            
            avg_ctr = total_clicks / max(total_impressions, 1)
            
            # Channel performance
            channel_performance = defaultdict(lambda: {'impressions': 0, 'clicks': 0})
            for perf in asset.performance_history:
                channel_performance[perf.channel.value]['impressions'] += perf.metrics.get(PerformanceMetric.IMPRESSIONS, 0)
                channel_performance[perf.channel.value]['clicks'] += perf.metrics.get(PerformanceMetric.CLICKS, 0)
            
            # Best performing channel
            best_channel = max(
                channel_performance.items(),
                key=lambda x: x[1]['clicks'],
                default=('none', {'clicks': 0})
            )[0]
            
            insights = {
                'asset_info': {
                    'name': asset.name,
                    'type': asset.asset_type.value,
                    'status': asset.status.value,
                    'created_at': asset.created_at.isoformat(),
                    'age_days': (datetime.now() - asset.created_at).days
                },
                'performance_summary': {
                    'total_impressions': int(total_impressions),
                    'total_clicks': int(total_clicks),
                    'average_ctr': round(avg_ctr, 4),
                    'campaigns_used': len(set(p.campaign_id for p in asset.performance_history if p.campaign_id)),
                    'channels_used': len(set(p.channel for p in asset.performance_history))
                },
                'channel_performance': dict(channel_performance),
                'best_channel': best_channel,
                'file_info': {
                    'size_bytes': asset.current_version.metadata.file_size,
                    'mime_type': asset.current_version.metadata.mime_type,
                    'dimensions': asset.current_version.metadata.dimensions,
                    'file_hash': asset.current_version.metadata.file_hash
                },
                'tags': asset.tags,
                'optimization_applied': len([r for r in self.optimization_rules.values() if asset.asset_type == r.asset_type]),
                'analysis_results': getattr(asset, 'analysis_results', {})
            }
            
            # Add recommendations
            recommendations = []
            
            if avg_ctr < 0.02:
                recommendations.append("Low CTR detected. Consider A/B testing different creative variations.")
            
            if len(asset.channels) == 1:
                recommendations.append("Asset is only used in one channel. Consider expanding to other channels.")
            
            if asset.status == AssetStatus.DRAFT:
                recommendations.append("Asset is still in draft status. Consider reviewing and publishing.")
            
            if (datetime.now() - asset.created_at).days > 90 and not asset.performance_history:
                recommendations.append("Asset has no performance data after 90 days. Consider archiving or optimizing.")
            
            insights['recommendations'] = recommendations
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get asset insights: {e}")
            return {}
    
    def cleanup_assets(self, days_to_keep: int = 180) -> int:
        """Clean up old unused assets."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cleaned_count = 0
            
            assets_to_remove = []
            
            for asset_id, asset in self.assets.items():
                # Check if asset is old and unused
                if (asset.created_at < cutoff_date and 
                    asset.status in [AssetStatus.DRAFT, AssetStatus.ARCHIVED] and
                    not asset.performance_history):
                    
                    # Delete files
                    try:
                        file_path = Path(asset.current_version.file_path)
                        if file_path.exists():
                            file_path.unlink()
                        
                        # Delete thumbnails and optimized versions
                        if asset.current_version.metadata.thumbnail_path:
                            thumb_path = Path(asset.current_version.metadata.thumbnail_path)
                            if thumb_path.exists():
                                thumb_path.unlink()
                        
                        assets_to_remove.append(asset_id)
                        cleaned_count += 1
                        
                    except OSError as e:
                        logger.warning(f"Failed to delete asset files: {e}")
            
            # Remove from tracking
            for asset_id in assets_to_remove:
                del self.assets[asset_id]
                
                # Remove from Redis if available
                if self.redis_available:
                    self.redis_client.delete(f"asset:{asset_id}")
            
            logger.info(f"Cleaned up {cleaned_count} old assets")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup assets: {e}")
            return 0


def create_sample_asset_manager() -> CreativeAssetManager:
    """Create sample creative asset manager for demonstration."""
    
    manager = CreativeAssetManager()
    
    # Create sample assets (simulated)
    sample_assets = [
        {
            'name': 'Summer Campaign Banner',
            'type': AssetType.BANNER,
            'channels': [AssetChannel.DISPLAY_ADS, AssetChannel.SOCIAL_MEDIA],
            'tags': ['summer', 'campaign', 'promotional']
        },
        {
            'name': 'Product Launch Video',
            'type': AssetType.VIDEO,
            'channels': [AssetChannel.SOCIAL_MEDIA, AssetChannel.VIDEO_ADS],
            'tags': ['product', 'launch', 'video']
        },
        {
            'name': 'Email Newsletter Template',
            'type': AssetType.EMAIL_TEMPLATE,
            'channels': [AssetChannel.EMAIL],
            'tags': ['newsletter', 'template', 'email']
        }
    ]
    
    # Simulate asset creation
    for i, asset_config in enumerate(sample_assets, 1):
        asset_id = f"demo_asset_{i:03d}"
        
        # Create mock asset
        metadata = AssetMetadata(
            file_name=f"{asset_config['name'].lower().replace(' ', '_')}.jpg",
            file_size=1024 * 500,  # 500KB
            mime_type="image/jpeg",
            dimensions=(1200, 800),
            dominant_colors=['#FF6B35', '#F7931E', '#FFD23F'],
            keywords=['marketing', 'campaign', 'brand']
        )
        
        version = AssetVersion(
            version_id=f"{asset_id}_v1",
            version_number=1,
            file_path=f"./demo/{asset_config['name'].lower().replace(' ', '_')}.jpg",
            created_by="demo_user",
            created_at=datetime.now() - timedelta(days=i*5),
            changes_description="Initial upload",
            metadata=metadata,
            is_current=True
        )
        
        asset = CreativeAsset(
            asset_id=asset_id,
            name=asset_config['name'],
            description=f"Demo {asset_config['type'].value} for marketing campaigns",
            asset_type=asset_config['type'],
            status=AssetStatus.APPROVED,
            tags=asset_config['tags'],
            channels=asset_config['channels'],
            current_version=version,
            versions=[version]
        )
        
        manager.assets[asset_id] = asset
        
        # Add sample performance data
        import random
        for j in range(3):  # 3 performance records per asset
            performance = AssetPerformance(
                asset_id=asset_id,
                channel=random.choice(asset_config['channels']),
                campaign_id=f"campaign_{random.randint(1, 5):03d}",
                metrics={
                    PerformanceMetric.IMPRESSIONS: random.randint(10000, 50000),
                    PerformanceMetric.CLICKS: random.randint(500, 2500),
                    PerformanceMetric.CTR: random.uniform(0.03, 0.08),
                    PerformanceMetric.CONVERSIONS: random.randint(25, 150)
                },
                date_range=(
                    datetime.now() - timedelta(days=(j+1)*7),
                    datetime.now() - timedelta(days=j*7)
                )
            )
            
            asset.performance_history.append(performance)
    
    # Create sample templates
    email_template = AssetTemplate(
        template_id="email_promo",
        name="Promotional Email Template",
        description="Responsive email template for promotional campaigns",
        asset_type=AssetType.EMAIL_TEMPLATE,
        channels=[AssetChannel.EMAIL],
        template_content="""
        <div style="max-width: 600px; margin: 0 auto;">
            <h1>{{title}}</h1>
            <p>{{content}}</p>
            <a href="{{cta_url}}" style="background: #FF6B35; color: white; padding: 10px 20px; text-decoration: none;">{{cta_text}}</a>
        </div>
        """,
        placeholders=['title', 'content', 'cta_url', 'cta_text'],
        styling_options={'primary_color': '#FF6B35', 'secondary_color': '#F7931E'},
        created_by="template_designer"
    )
    
    manager.templates[email_template.template_id] = email_template
    
    return manager


def run_creative_asset_demo():
    """
    Run the creative asset manager demonstration.
    
    Author: Sotiris Spyrou | https://verityai.co
    """
    
    print("🎨 Creative Asset Manager Demo")
    print("=" * 50)
    
    print("🎯 Key Features:")
    print("  • Multi-format asset storage and management")
    print("  • Automated asset optimization and resizing")
    print("  • Performance tracking across channels")
    print("  • Version control and approval workflows")
    print("  • AI-powered content analysis and tagging")
    print("  • Template-based asset generation")
    print("  • Brand compliance checking")
    print("  • A/B testing integration")
    
    print("\n📁 Supported Asset Types:")
    for asset_type in list(AssetType)[:8]:  # Show first 8 types
        print(f"  • {asset_type.value}")
    print(f"  • ... and {len(AssetType) - 8} more asset types")
    
    print("\n🔧 Optimization Types:")
    for opt_type in list(OptimizationType)[:6]:  # Show first 6 optimization types
        print(f"  • {opt_type.value}")
    print(f"  • ... and {len(OptimizationType) - 6} more optimization types")
    
    print("\n🚀 Initializing asset manager...")
    manager = create_sample_asset_manager()
    
    print("✅ Asset manager initialized")
    print(f"   • Assets loaded: {len(manager.assets)}")
    print(f"   • Templates available: {len(manager.templates)}")
    print(f"   • Optimization rules: {len(manager.optimization_rules)}")
    
    # Display asset summary
    print("\n📊 Asset Inventory:")
    asset_types = defaultdict(int)
    asset_channels = defaultdict(int)
    
    for asset in manager.assets.values():
        asset_types[asset.asset_type.value] += 1
        for channel in asset.channels:
            asset_channels[channel.value] += 1
    
    print("   By Type:")
    for asset_type, count in asset_types.items():
        print(f"     • {asset_type}: {count}")
    
    print("   By Channel:")
    for channel, count in sorted(asset_channels.items(), key=lambda x: x[1], reverse=True):
        print(f"     • {channel}: {count}")
    
    # Show asset performance
    print("\n📈 Asset Performance Summary:")
    total_impressions = 0
    total_clicks = 0
    
    for asset in manager.assets.values():
        for perf in asset.performance_history:
            total_impressions += perf.metrics.get(PerformanceMetric.IMPRESSIONS, 0)
            total_clicks += perf.metrics.get(PerformanceMetric.CLICKS, 0)
    
    avg_ctr = total_clicks / max(total_impressions, 1)
    
    print(f"   • Total Impressions: {total_impressions:,}")
    print(f"   • Total Clicks: {total_clicks:,}")
    print(f"   • Average CTR: {avg_ctr*100:.2f}%")
    print(f"   • Performance Records: {sum(len(a.performance_history) for a in manager.assets.values())}")
    
    # Show asset insights for first asset
    if manager.assets:
        first_asset_id = list(manager.assets.keys())[0]
        insights = manager.get_asset_insights(first_asset_id)
        
        print(f"\n🔍 Asset Insights - {insights.get('asset_info', {}).get('name', 'Unknown')}:")
        perf_summary = insights.get('performance_summary', {})
        print(f"   • Impressions: {perf_summary.get('total_impressions', 0):,}")
        print(f"   • Clicks: {perf_summary.get('total_clicks', 0):,}")
        print(f"   • CTR: {perf_summary.get('average_ctr', 0)*100:.2f}%")
        print(f"   • Channels Used: {perf_summary.get('channels_used', 0)}")
        print(f"   • Best Channel: {insights.get('best_channel', 'none')}")
        
        recommendations = insights.get('recommendations', [])
        if recommendations:
            print(f"   • Top Recommendation: {recommendations[0]}")
    
    # Template demonstration
    print("\n📋 Template System:")
    for template_id, template in manager.templates.items():
        print(f"   • {template.name}")
        print(f"     - Type: {template.asset_type.value}")
        print(f"     - Placeholders: {len(template.placeholders)}")
        print(f"     - Usage Count: {template.usage_count}")
    
    # Search demonstration
    print("\n🔍 Asset Search Examples:")
    
    # Search by type
    banners = manager.search_assets(asset_type=AssetType.BANNER)
    print(f"   • Banner assets: {len(banners)} found")
    
    # Search by tag
    summer_assets = manager.search_assets(tags=['summer'])
    print(f"   • Summer-tagged assets: {len(summer_assets)} found")
    
    # Search by channel
    social_assets = manager.search_assets(channels=[AssetChannel.SOCIAL_MEDIA])
    print(f"   • Social media assets: {len(social_assets)} found")
    
    # Optimization rules
    print("\n⚡ Optimization Rules:")
    for rule_id, rule in manager.optimization_rules.items():
        print(f"   • {rule.name}")
        print(f"     - Target: {rule.asset_type.value}")
        print(f"     - Optimizations: {len(rule.optimizations)}")
        print(f"     - Success Rate: {rule.success_rate*100:.1f}%")
        print(f"     - Usage: {rule.usage_count} times")
    
    print("\n🌟 Advanced Capabilities:")
    print("  • AI-powered content analysis and auto-tagging")
    print("  • Multi-channel performance optimization")
    print("  • Brand compliance checking and enforcement")
    print("  • Automated A/B test creative generation")
    print("  • Cloud storage integration (S3, CDN)")
    print("  • Real-time asset usage tracking")
    
    print(f"\n💼 Portfolio: https://verityai.co")
    print(f"🔗 LinkedIn: https://www.linkedin.com/in/sspyrou/")
    print("⚠️  DISCLAIMER: This is demonstration code for portfolio purposes.")
    
    return manager


if __name__ == "__main__":
    run_creative_asset_demo()

