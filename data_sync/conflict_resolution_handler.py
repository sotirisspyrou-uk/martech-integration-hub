#!/usr/bin/env python3
"""
Conflict Resolution Handler - Intelligent Data Synchronization

Advanced conflict detection and resolution for MarTech data synchronization.

⚖️ INTELLIGENT CONFLICT RESOLUTION ⚖️
Automatically resolve data conflicts with business-aware algorithms.

Author: Sotirios Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

🚀 THE RARE TECHNICAL MARKETING LEADER 🚀
Combining C-suite strategy with hands-on AI implementation.
Proven track record: From startup innovation to enterprise transformation.

DISCLAIMER: This is demonstration code showcasing technical capabilities.
For production use, additional security hardening and testing required.
"""

import hashlib
import json
import logging
import random
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of data conflicts"""
    VALUE_MISMATCH = auto()
    TEMPORAL_CONFLICT = auto()
    STRUCTURAL_CONFLICT = auto()
    SEMANTIC_CONFLICT = auto()
    BUSINESS_RULE_VIOLATION = auto()
    DUPLICATE_RECORD = auto()
    MISSING_DATA = auto()
    FORMAT_INCONSISTENCY = auto()


class ResolutionStrategy(Enum):
    """Conflict resolution strategies"""
    LAST_WRITE_WINS = auto()
    FIRST_WRITE_WINS = auto()
    MERGE_VALUES = auto()
    PRIORITY_SOURCE = auto()
    BUSINESS_RULES = auto()
    ML_PREDICTION = auto()
    MANUAL_REVIEW = auto()
    AUTOMATED_ENRICHMENT = auto()


class ConflictSeverity(Enum):
    """Severity levels for conflicts"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResolutionOutcome(Enum):
    """Resolution outcomes"""
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    POSTPONED = "postponed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"


@dataclass
class ConflictRecord:
    """Represents a data conflict"""
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conflict_type: ConflictType = ConflictType.VALUE_MISMATCH
    severity: ConflictSeverity = ConflictSeverity.MEDIUM
    entity_id: str = ""
    field_name: str = ""
    source_values: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolution_strategy: Optional[ResolutionStrategy] = None
    resolved_value: Any = None
    confidence_score: float = 0.0
    resolution_notes: str = ""
    requires_review: bool = False


@dataclass
class ResolutionRule:
    """Business rule for conflict resolution"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    field_patterns: List[str] = field(default_factory=list)
    conflict_types: Set[ConflictType] = field(default_factory=set)
    priority: int = 5
    strategy: ResolutionStrategy = ResolutionStrategy.BUSINESS_RULES
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ConflictMetrics:
    """Metrics for conflict resolution"""
    total_conflicts: int = 0
    resolved_conflicts: int = 0
    escalated_conflicts: int = 0
    failed_resolutions: int = 0
    average_resolution_time: float = 0.0
    conflict_types_count: Dict[str, int] = field(default_factory=dict)
    resolution_strategies_count: Dict[str, int] = field(default_factory=dict)
    confidence_scores: List[float] = field(default_factory=list)
    success_rate: float = 0.0


class ConflictResolutionHandler:
    """
    Advanced conflict resolution system for MarTech data synchronization.
    
    🎯 ENTERPRISE CAPABILITIES:
    - Intelligent conflict detection and categorization
    - Business-rule-based automatic resolution
    - ML-powered similarity matching and deduplication
    - Configurable resolution strategies per data type
    - Comprehensive audit trails and metrics
    
    🔧 RESOLUTION FEATURES:
    - Multi-source data reconciliation
    - Temporal conflict resolution
    - Semantic similarity matching
    - Priority-based source weighting
    - Automated data enrichment
    
    🔗 Learn more: https://verityai.co
    💼 Connect: https://www.linkedin.com/in/sspyrou/
    """
    
    def __init__(self):
        self.conflicts: Dict[str, ConflictRecord] = {}
        self.resolution_rules: Dict[str, ResolutionRule] = {}
        self.source_priorities: Dict[str, int] = {}
        self.metrics = ConflictMetrics()
        self.similarity_vectorizer = TfidfVectorizer()
        self.conflict_history: deque = deque(maxlen=10000)
        
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default resolution rules"""
        
        # Email address conflicts - prefer most recent
        email_rule = ResolutionRule(
            name="Email Address Resolution",
            description="Resolve email conflicts by choosing most recent valid email",
            field_patterns=["email", "*_email", "email_*"],
            conflict_types={ConflictType.VALUE_MISMATCH},
            priority=8,
            strategy=ResolutionStrategy.BUSINESS_RULES,
            conditions={"validate_email": True},
            actions=[
                {"type": "validate_format", "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
                {"type": "prefer_recent", "timestamp_field": "updated_at"}
            ]
        )
        self.add_resolution_rule(email_rule)
        
        # Revenue conflicts - sum or take highest
        revenue_rule = ResolutionRule(
            name="Revenue Field Resolution",
            description="Resolve revenue conflicts by taking highest value",
            field_patterns=["revenue", "total_revenue", "lifetime_value"],
            conflict_types={ConflictType.VALUE_MISMATCH},
            priority=9,
            strategy=ResolutionStrategy.BUSINESS_RULES,
            conditions={"field_type": "numeric"},
            actions=[
                {"type": "take_maximum", "validate_positive": True}
            ]
        )
        self.add_resolution_rule(revenue_rule)
        
        # Customer name conflicts - merge and clean
        name_rule = ResolutionRule(
            name="Customer Name Resolution",
            description="Resolve name conflicts using similarity matching",
            field_patterns=["name", "customer_name", "full_name", "display_name"],
            conflict_types={ConflictType.VALUE_MISMATCH, ConflictType.SEMANTIC_CONFLICT},
            priority=7,
            strategy=ResolutionStrategy.ML_PREDICTION,
            conditions={"field_type": "string"},
            actions=[
                {"type": "similarity_match", "threshold": 0.8},
                {"type": "merge_names", "prefer_complete": True}
            ]
        )
        self.add_resolution_rule(name_rule)
        
        # Timestamp conflicts - prefer most recent
        timestamp_rule = ResolutionRule(
            name="Timestamp Resolution",
            description="Resolve timestamp conflicts by preferring most recent",
            field_patterns=["*_at", "*_date", "timestamp", "date_*"],
            conflict_types={ConflictType.TEMPORAL_CONFLICT, ConflictType.VALUE_MISMATCH},
            priority=6,
            strategy=ResolutionStrategy.LAST_WRITE_WINS,
            conditions={"field_type": "datetime"},
            actions=[
                {"type": "take_latest", "validate_format": True}
            ]
        )
        self.add_resolution_rule(timestamp_rule)
        
        # Duplicate detection rule
        duplicate_rule = ResolutionRule(
            name="Duplicate Record Resolution",
            description="Resolve duplicate records by merging data",
            field_patterns=["*"],
            conflict_types={ConflictType.DUPLICATE_RECORD},
            priority=10,
            strategy=ResolutionStrategy.MERGE_VALUES,
            conditions={"similarity_threshold": 0.9},
            actions=[
                {"type": "merge_records", "keep_latest": True},
                {"type": "preserve_history", "archive": True}
            ]
        )
        self.add_resolution_rule(duplicate_rule)
    
    def detect_conflicts(self, records: List[Dict[str, Any]], 
                        entity_key: str = "id") -> List[ConflictRecord]:
        """Detect conflicts in a batch of records"""
        conflicts = []
        
        # Group records by entity
        entity_groups = defaultdict(list)
        for record in records:
            entity_id = record.get(entity_key)
            if entity_id:
                entity_groups[entity_id].append(record)
        
        # Detect conflicts within each entity group
        for entity_id, entity_records in entity_groups.items():
            if len(entity_records) > 1:
                entity_conflicts = self._detect_entity_conflicts(entity_id, entity_records)
                conflicts.extend(entity_conflicts)
        
        # Store detected conflicts
        for conflict in conflicts:
            self.conflicts[conflict.conflict_id] = conflict
        
        logger.info(f"Detected {len(conflicts)} conflicts across {len(entity_groups)} entities")
        return conflicts
    
    def _detect_entity_conflicts(self, entity_id: str, 
                               records: List[Dict[str, Any]]) -> List[ConflictRecord]:
        """Detect conflicts for a specific entity"""
        conflicts = []
        
        # Get all field names across records
        all_fields = set()
        for record in records:
            all_fields.update(record.keys())
        
        # Check each field for conflicts
        for field_name in all_fields:
            field_values = {}
            field_metadata = {}
            
            for i, record in enumerate(records):
                if field_name in record:
                    source_id = record.get('_source', f'source_{i}')
                    field_values[source_id] = record[field_name]
                    field_metadata[source_id] = {
                        'timestamp': record.get('_timestamp', datetime.now()),
                        'confidence': record.get('_confidence', 1.0),
                        'record_index': i
                    }
            
            # Check for value conflicts
            if len(field_values) > 1:
                unique_values = set(str(v) for v in field_values.values() if v is not None)
                if len(unique_values) > 1:
                    conflict = self._create_conflict_record(
                        entity_id, field_name, field_values, field_metadata
                    )
                    conflicts.append(conflict)
        
        # Check for duplicate records
        if len(records) > 1:
            duplicates = self._detect_duplicate_records(entity_id, records)
            conflicts.extend(duplicates)
        
        return conflicts
    
    def _create_conflict_record(self, entity_id: str, field_name: str,
                              values: Dict[str, Any], 
                              metadata: Dict[str, Dict]) -> ConflictRecord:
        """Create a conflict record"""
        conflict_type = self._classify_conflict_type(field_name, values)
        severity = self._assess_conflict_severity(conflict_type, field_name, values)
        
        return ConflictRecord(
            conflict_type=conflict_type,
            severity=severity,
            entity_id=entity_id,
            field_name=field_name,
            source_values=values.copy(),
            metadata=metadata.copy()
        )
    
    def _classify_conflict_type(self, field_name: str, 
                              values: Dict[str, Any]) -> ConflictType:
        """Classify the type of conflict"""
        # Check for temporal conflicts
        if any(pattern in field_name.lower() for pattern in ['date', 'time', '_at']):
            return ConflictType.TEMPORAL_CONFLICT
        
        # Check for semantic conflicts (similar but not identical strings)
        string_values = [str(v) for v in values.values() if v is not None]
        if len(string_values) > 1 and all(isinstance(v, str) for v in values.values()):
            similarities = []
            for i, val1 in enumerate(string_values):
                for val2 in string_values[i+1:]:
                    if val1 and val2:
                        similarity = self._calculate_string_similarity(val1, val2)
                        similarities.append(similarity)
            
            if similarities and max(similarities) > 0.7:
                return ConflictType.SEMANTIC_CONFLICT
        
        # Default to value mismatch
        return ConflictType.VALUE_MISMATCH
    
    def _assess_conflict_severity(self, conflict_type: ConflictType, 
                                field_name: str, values: Dict[str, Any]) -> ConflictSeverity:
        """Assess the severity of a conflict"""
        # Critical fields that require high severity
        critical_fields = ['id', 'customer_id', 'email', 'revenue', 'status']
        high_impact_fields = ['name', 'phone', 'address', 'segment']
        
        if any(critical in field_name.lower() for critical in critical_fields):
            return ConflictSeverity.CRITICAL
        elif any(high in field_name.lower() for high in high_impact_fields):
            return ConflictSeverity.HIGH
        elif conflict_type in [ConflictType.BUSINESS_RULE_VIOLATION, ConflictType.DUPLICATE_RECORD]:
            return ConflictSeverity.HIGH
        else:
            return ConflictSeverity.MEDIUM
    
    def _detect_duplicate_records(self, entity_id: str, 
                                records: List[Dict[str, Any]]) -> List[ConflictRecord]:
        """Detect duplicate records for an entity"""
        duplicates = []
        
        # Calculate similarity between all record pairs
        for i, record1 in enumerate(records):
            for j, record2 in enumerate(records[i+1:], i+1):
                similarity = self._calculate_record_similarity(record1, record2)
                
                if similarity > 0.9:  # High similarity threshold
                    source_values = {
                        f'record_{i}': record1,
                        f'record_{j}': record2
                    }
                    
                    metadata = {
                        f'record_{i}': {'similarity_score': similarity, 'index': i},
                        f'record_{j}': {'similarity_score': similarity, 'index': j}
                    }
                    
                    duplicate_conflict = ConflictRecord(
                        conflict_type=ConflictType.DUPLICATE_RECORD,
                        severity=ConflictSeverity.HIGH,
                        entity_id=entity_id,
                        field_name="*",
                        source_values=source_values,
                        metadata=metadata
                    )
                    duplicates.append(duplicate_conflict)
        
        return duplicates
    
    def resolve_conflicts(self, conflict_ids: Optional[List[str]] = None) -> Dict[str, ResolutionOutcome]:
        """Resolve conflicts using configured strategies"""
        if conflict_ids is None:
            conflict_ids = list(self.conflicts.keys())
        
        resolution_results = {}
        
        for conflict_id in conflict_ids:
            if conflict_id not in self.conflicts:
                continue
            
            conflict = self.conflicts[conflict_id]
            
            try:
                outcome = self._resolve_single_conflict(conflict)
                resolution_results[conflict_id] = outcome
                
                # Update metrics
                self._update_resolution_metrics(conflict, outcome)
                
                # Add to history
                self.conflict_history.append({
                    'conflict_id': conflict_id,
                    'resolved_at': datetime.now(),
                    'outcome': outcome,
                    'strategy': conflict.resolution_strategy
                })
                
            except Exception as e:
                logger.error(f"Failed to resolve conflict {conflict_id}: {str(e)}")
                resolution_results[conflict_id] = ResolutionOutcome.FAILED
        
        logger.info(f"Resolved {len(resolution_results)} conflicts")
        return resolution_results
    
    def _resolve_single_conflict(self, conflict: ConflictRecord) -> ResolutionOutcome:
        """Resolve a single conflict"""
        # Find applicable resolution rule
        applicable_rule = self._find_applicable_rule(conflict)
        
        if applicable_rule:
            return self._apply_resolution_rule(conflict, applicable_rule)
        else:
            return self._apply_default_resolution(conflict)
    
    def _find_applicable_rule(self, conflict: ConflictRecord) -> Optional[ResolutionRule]:
        """Find the best applicable resolution rule"""
        applicable_rules = []
        
        for rule in self.resolution_rules.values():
            if not rule.enabled:
                continue
            
            # Check conflict type match
            if conflict.conflict_type not in rule.conflict_types:
                continue
            
            # Check field pattern match
            field_match = False
            for pattern in rule.field_patterns:
                if pattern == "*" or pattern in conflict.field_name:
                    field_match = True
                    break
                if pattern.startswith("*") and conflict.field_name.endswith(pattern[1:]):
                    field_match = True
                    break
                if pattern.endswith("*") and conflict.field_name.startswith(pattern[:-1]):
                    field_match = True
                    break
            
            if field_match:
                applicable_rules.append(rule)
        
        # Return highest priority rule
        if applicable_rules:
            return max(applicable_rules, key=lambda r: r.priority)
        
        return None
    
    def _apply_resolution_rule(self, conflict: ConflictRecord, 
                             rule: ResolutionRule) -> ResolutionOutcome:
        """Apply a resolution rule to a conflict"""
        conflict.resolution_strategy = rule.strategy
        
        try:
            if rule.strategy == ResolutionStrategy.LAST_WRITE_WINS:
                resolved_value = self._resolve_last_write_wins(conflict)
            elif rule.strategy == ResolutionStrategy.FIRST_WRITE_WINS:
                resolved_value = self._resolve_first_write_wins(conflict)
            elif rule.strategy == ResolutionStrategy.MERGE_VALUES:
                resolved_value = self._resolve_merge_values(conflict)
            elif rule.strategy == ResolutionStrategy.PRIORITY_SOURCE:
                resolved_value = self._resolve_priority_source(conflict)
            elif rule.strategy == ResolutionStrategy.BUSINESS_RULES:
                resolved_value = self._resolve_business_rules(conflict, rule)
            elif rule.strategy == ResolutionStrategy.ML_PREDICTION:
                resolved_value = self._resolve_ml_prediction(conflict)
            else:
                return ResolutionOutcome.ESCALATED
            
            # Apply resolved value
            conflict.resolved_value = resolved_value
            conflict.resolved_at = datetime.now()
            conflict.confidence_score = self._calculate_confidence_score(conflict, rule)
            conflict.resolution_notes = f"Resolved using rule: {rule.name}"
            
            # Check if manual review is needed
            if conflict.confidence_score < 0.7 or conflict.severity == ConflictSeverity.CRITICAL:
                conflict.requires_review = True
                return ResolutionOutcome.REQUIRES_REVIEW
            
            return ResolutionOutcome.RESOLVED
            
        except Exception as e:
            logger.error(f"Failed to apply rule {rule.name}: {str(e)}")
            return ResolutionOutcome.FAILED
    
    def _resolve_last_write_wins(self, conflict: ConflictRecord) -> Any:
        """Resolve using last write wins strategy"""
        latest_timestamp = None
        latest_value = None
        
        for source, value in conflict.source_values.items():
            timestamp = conflict.metadata.get(source, {}).get('timestamp', datetime.min)
            if latest_timestamp is None or timestamp > latest_timestamp:
                latest_timestamp = timestamp
                latest_value = value
        
        return latest_value
    
    def _resolve_first_write_wins(self, conflict: ConflictRecord) -> Any:
        """Resolve using first write wins strategy"""
        earliest_timestamp = None
        earliest_value = None
        
        for source, value in conflict.source_values.items():
            timestamp = conflict.metadata.get(source, {}).get('timestamp', datetime.max)
            if earliest_timestamp is None or timestamp < earliest_timestamp:
                earliest_timestamp = timestamp
                earliest_value = value
        
        return earliest_value
    
    def _resolve_merge_values(self, conflict: ConflictRecord) -> Any:
        """Resolve by merging values"""
        values = list(conflict.source_values.values())
        
        # For strings, concatenate unique parts
        if all(isinstance(v, str) for v in values):
            unique_parts = []
            for value in values:
                if value and value not in unique_parts:
                    unique_parts.append(value.strip())
            return " | ".join(unique_parts)
        
        # For numbers, take average
        elif all(isinstance(v, (int, float)) for v in values):
            return sum(values) / len(values)
        
        # For lists, merge unique items
        elif all(isinstance(v, list) for v in values):
            merged = []
            for value_list in values:
                for item in value_list:
                    if item not in merged:
                        merged.append(item)
            return merged
        
        # Default: return most complete value
        return max(values, key=lambda v: len(str(v)) if v is not None else 0)
    
    def _resolve_priority_source(self, conflict: ConflictRecord) -> Any:
        """Resolve using source priority"""
        highest_priority = -1
        priority_value = None
        
        for source, value in conflict.source_values.items():
            priority = self.source_priorities.get(source, 0)
            if priority > highest_priority:
                highest_priority = priority
                priority_value = value
        
        return priority_value if priority_value is not None else list(conflict.source_values.values())[0]
    
    def _resolve_business_rules(self, conflict: ConflictRecord, rule: ResolutionRule) -> Any:
        """Resolve using business rules"""
        for action in rule.actions:
            if action["type"] == "validate_format":
                # Return first value matching pattern
                import re
                pattern = action["pattern"]
                for value in conflict.source_values.values():
                    if isinstance(value, str) and re.match(pattern, value):
                        return value
            
            elif action["type"] == "take_maximum":
                numeric_values = [v for v in conflict.source_values.values() 
                                if isinstance(v, (int, float)) and v > 0]
                if numeric_values:
                    return max(numeric_values)
            
            elif action["type"] == "take_latest":
                return self._resolve_last_write_wins(conflict)
        
        # Default to first value
        return list(conflict.source_values.values())[0]
    
    def _resolve_ml_prediction(self, conflict: ConflictRecord) -> Any:
        """Resolve using ML prediction"""
        values = list(conflict.source_values.values())
        
        # For string values, use similarity clustering
        if all(isinstance(v, str) for v in values):
            return self._resolve_string_similarity(values)
        
        # For numeric values, detect outliers
        elif all(isinstance(v, (int, float)) for v in values):
            return self._resolve_numeric_outliers(values)
        
        # Default to most frequent value
        from collections import Counter
        value_counts = Counter(values)
        return value_counts.most_common(1)[0][0]
    
    def _resolve_string_similarity(self, values: List[str]) -> str:
        """Resolve strings using similarity analysis"""
        if not values:
            return ""
        
        # Calculate pairwise similarities
        similarities = []
        for i, val1 in enumerate(values):
            for val2 in values[i+1:]:
                sim = self._calculate_string_similarity(val1, val2)
                similarities.append((val1, val2, sim))
        
        # Find the most similar pair and return the more complete one
        if similarities:
            best_pair = max(similarities, key=lambda x: x[2])
            val1, val2 = best_pair[0], best_pair[1]
            return val1 if len(val1) > len(val2) else val2
        
        return values[0]
    
    def _resolve_numeric_outliers(self, values: List[Union[int, float]]) -> Union[int, float]:
        """Resolve numeric values by removing outliers"""
        if len(values) <= 2:
            return values[0]
        
        mean = np.mean(values)
        std = np.std(values)
        
        # Remove outliers (values more than 2 std from mean)
        filtered_values = [v for v in values if abs(v - mean) <= 2 * std]
        
        if filtered_values:
            return np.mean(filtered_values)
        else:
            return mean
    
    def _apply_default_resolution(self, conflict: ConflictRecord) -> ResolutionOutcome:
        """Apply default resolution strategy"""
        # Default to last write wins
        conflict.resolution_strategy = ResolutionStrategy.LAST_WRITE_WINS
        conflict.resolved_value = self._resolve_last_write_wins(conflict)
        conflict.resolved_at = datetime.now()
        conflict.confidence_score = 0.5  # Low confidence for default resolution
        conflict.resolution_notes = "Resolved using default strategy (last write wins)"
        
        if conflict.severity == ConflictSeverity.CRITICAL:
            conflict.requires_review = True
            return ResolutionOutcome.REQUIRES_REVIEW
        
        return ResolutionOutcome.RESOLVED
    
    def _calculate_confidence_score(self, conflict: ConflictRecord, 
                                  rule: ResolutionRule) -> float:
        """Calculate confidence score for resolution"""
        base_confidence = 0.8
        
        # Adjust based on strategy
        if rule.strategy == ResolutionStrategy.BUSINESS_RULES:
            base_confidence = 0.9
        elif rule.strategy == ResolutionStrategy.ML_PREDICTION:
            base_confidence = 0.7
        elif rule.strategy == ResolutionStrategy.PRIORITY_SOURCE:
            base_confidence = 0.85
        
        # Adjust based on conflict type
        if conflict.conflict_type == ConflictType.DUPLICATE_RECORD:
            base_confidence *= 0.9
        elif conflict.conflict_type == ConflictType.SEMANTIC_CONFLICT:
            base_confidence *= 0.8
        
        # Adjust based on number of conflicting values
        num_conflicts = len(conflict.source_values)
        if num_conflicts > 3:
            base_confidence *= 0.9
        
        return min(base_confidence, 1.0)
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        if not str1 or not str2:
            return 0.0
        
        # Use TF-IDF vectorization for similarity
        try:
            vectors = self.similarity_vectorizer.fit_transform([str1, str2])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return similarity
        except:
            # Fallback to Levenshtein-like similarity
            return self._levenshtein_similarity(str1, str2)
    
    def _levenshtein_similarity(self, str1: str, str2: str) -> float:
        """Calculate Levenshtein similarity"""
        if len(str1) < len(str2):
            return self._levenshtein_similarity(str2, str1)
        
        if len(str2) == 0:
            return 0.0
        
        previous_row = list(range(len(str2) + 1))
        for i, c1 in enumerate(str1):
            current_row = [i + 1]
            for j, c2 in enumerate(str2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        max_len = max(len(str1), len(str2))
        distance = previous_row[-1]
        return 1.0 - (distance / max_len)
    
    def _calculate_record_similarity(self, record1: Dict[str, Any], 
                                   record2: Dict[str, Any]) -> float:
        """Calculate similarity between two records"""
        common_fields = set(record1.keys()) & set(record2.keys())
        if not common_fields:
            return 0.0
        
        field_similarities = []
        for field in common_fields:
            val1, val2 = record1[field], record2[field]
            
            if val1 == val2:
                similarity = 1.0
            elif isinstance(val1, str) and isinstance(val2, str):
                similarity = self._calculate_string_similarity(val1, val2)
            elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # Numeric similarity based on relative difference
                if val1 == 0 and val2 == 0:
                    similarity = 1.0
                else:
                    diff = abs(val1 - val2)
                    avg = (abs(val1) + abs(val2)) / 2
                    similarity = max(0, 1 - (diff / max(avg, 1)))
            else:
                similarity = 0.0
            
            field_similarities.append(similarity)
        
        return np.mean(field_similarities) if field_similarities else 0.0
    
    def add_resolution_rule(self, rule: ResolutionRule):
        """Add a custom resolution rule"""
        self.resolution_rules[rule.rule_id] = rule
        logger.info(f"Added resolution rule: {rule.name}")
    
    def set_source_priority(self, source: str, priority: int):
        """Set priority for a data source"""
        self.source_priorities[source] = priority
        logger.info(f"Set priority {priority} for source: {source}")
    
    def get_conflict_summary(self) -> Dict[str, Any]:
        """Get summary of all conflicts"""
        total_conflicts = len(self.conflicts)
        resolved_conflicts = sum(1 for c in self.conflicts.values() if c.resolved_at)
        pending_conflicts = total_conflicts - resolved_conflicts
        
        # Group by type and severity
        type_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for conflict in self.conflicts.values():
            type_counts[conflict.conflict_type.name] += 1
            severity_counts[conflict.severity.value] += 1
        
        return {
            "total_conflicts": total_conflicts,
            "resolved_conflicts": resolved_conflicts,
            "pending_conflicts": pending_conflicts,
            "resolution_rate": resolved_conflicts / max(total_conflicts, 1) * 100,
            "conflicts_by_type": dict(type_counts),
            "conflicts_by_severity": dict(severity_counts),
            "requires_review": sum(1 for c in self.conflicts.values() if c.requires_review)
        }
    
    def _update_resolution_metrics(self, conflict: ConflictRecord, outcome: ResolutionOutcome):
        """Update resolution metrics"""
        self.metrics.total_conflicts += 1
        
        if outcome == ResolutionOutcome.RESOLVED:
            self.metrics.resolved_conflicts += 1
            if conflict.resolved_at and conflict.detected_at:
                resolution_time = (conflict.resolved_at - conflict.detected_at).total_seconds()
                # Update average resolution time using exponential moving average
                alpha = 0.1
                self.metrics.average_resolution_time = (
                    alpha * resolution_time + 
                    (1 - alpha) * self.metrics.average_resolution_time
                )
            
            if conflict.confidence_score:
                self.metrics.confidence_scores.append(conflict.confidence_score)
        
        elif outcome == ResolutionOutcome.ESCALATED:
            self.metrics.escalated_conflicts += 1
        elif outcome == ResolutionOutcome.FAILED:
            self.metrics.failed_resolutions += 1
        
        # Update type and strategy counts
        self.metrics.conflict_types_count[conflict.conflict_type.name] = (
            self.metrics.conflict_types_count.get(conflict.conflict_type.name, 0) + 1
        )
        
        if conflict.resolution_strategy:
            self.metrics.resolution_strategies_count[conflict.resolution_strategy.name] = (
                self.metrics.resolution_strategies_count.get(conflict.resolution_strategy.name, 0) + 1
            )
        
        # Update success rate
        if self.metrics.total_conflicts > 0:
            self.metrics.success_rate = self.metrics.resolved_conflicts / self.metrics.total_conflicts * 100


def demo_conflict_resolution():
    """
    Demonstrate conflict resolution capabilities.
    
    🚀 Ready to eliminate data conflicts in your MarTech stack?
    📧 Contact: https://verityai.co
    💼 LinkedIn: https://www.linkedin.com/in/sspyrou/
    """
    print("\n" + "="*80)
    print("⚖️ CONFLICT RESOLUTION HANDLER DEMO")
    print("Intelligent Data Synchronization")
    print("="*80)
    
    # Initialize conflict handler
    handler = ConflictResolutionHandler()
    
    # Set source priorities
    handler.set_source_priority("salesforce", 10)
    handler.set_source_priority("hubspot", 8)
    handler.set_source_priority("mailchimp", 6)
    handler.set_source_priority("manual_entry", 4)
    
    # Create sample conflicting records
    sample_records = [
        {
            "id": "CUST_001",
            "name": "John Smith",
            "email": "john.smith@company.com",
            "revenue": 15000,
            "last_contact": "2024-01-15",
            "_source": "salesforce",
            "_timestamp": datetime(2024, 1, 15, 10, 0),
            "_confidence": 0.95
        },
        {
            "id": "CUST_001", 
            "name": "Jon Smith",
            "email": "j.smith@company.com",
            "revenue": 18000,
            "last_contact": "2024-01-20",
            "_source": "hubspot",
            "_timestamp": datetime(2024, 1, 20, 14, 30),
            "_confidence": 0.85
        },
        {
            "id": "CUST_001",
            "name": "John W. Smith",
            "email": "john.smith@company.com", 
            "revenue": 16500,
            "segment": "Enterprise",
            "_source": "manual_entry",
            "_timestamp": datetime(2024, 1, 18, 9, 15),
            "_confidence": 0.90
        },
        {
            "id": "CUST_002",
            "name": "Sarah Johnson",
            "email": "sarah@example.com",
            "revenue": 8500,
            "_source": "mailchimp",
            "_timestamp": datetime(2024, 1, 10, 16, 0),
            "_confidence": 0.80
        },
        {
            "id": "CUST_002",
            "name": "S. Johnson", 
            "email": "sarah.johnson@example.com",
            "revenue": 9200,
            "_source": "salesforce",
            "_timestamp": datetime(2024, 1, 12, 11, 30),
            "_confidence": 0.92
        }
    ]
    
    print("\n📊 Sample Data:")
    print(f"  • Records: {len(sample_records)}")
    print(f"  • Unique Entities: {len(set(r['id'] for r in sample_records))}")
    print(f"  • Data Sources: {len(set(r['_source'] for r in sample_records))}")
    
    # Detect conflicts
    print("\n🔍 Detecting Conflicts...")
    conflicts = handler.detect_conflicts(sample_records, entity_key="id")
    
    print(f"  ✓ Detected: {len(conflicts)} conflicts")
    
    # Show detected conflicts
    print("\n📋 Conflict Details:")
    for i, conflict in enumerate(conflicts[:5]):  # Show first 5
        print(f"\n  Conflict {i+1}:")
        print(f"    • Type: {conflict.conflict_type.name}")
        print(f"    • Severity: {conflict.severity.value}")
        print(f"    • Entity: {conflict.entity_id}")
        print(f"    • Field: {conflict.field_name}")
        print(f"    • Sources: {list(conflict.source_values.keys())}")
        print(f"    • Values: {list(conflict.source_values.values())}")
    
    # Resolve conflicts
    print("\n⚡ Resolving Conflicts...")
    resolution_results = handler.resolve_conflicts()
    
    # Show resolution results
    resolved_count = sum(1 for outcome in resolution_results.values() 
                        if outcome == ResolutionOutcome.RESOLVED)
    review_count = sum(1 for outcome in resolution_results.values() 
                      if outcome == ResolutionOutcome.REQUIRES_REVIEW)
    
    print(f"  ✓ Resolved: {resolved_count}")
    print(f"  ⚠️  Requires Review: {review_count}")
    print(f"  ❌ Failed: {len(resolution_results) - resolved_count - review_count}")
    
    # Show resolved conflicts
    print("\n🎯 Resolution Examples:")
    resolved_conflicts = [conflict for conflict in handler.conflicts.values() 
                         if conflict.resolved_at]
    
    for i, conflict in enumerate(resolved_conflicts[:3]):
        print(f"\n  Resolution {i+1}:")
        print(f"    • Field: {conflict.field_name}")
        print(f"    • Strategy: {conflict.resolution_strategy.name if conflict.resolution_strategy else 'N/A'}")
        print(f"    • Original Values: {list(conflict.source_values.values())}")
        print(f"    • Resolved Value: {conflict.resolved_value}")
        print(f"    • Confidence: {conflict.confidence_score:.2f}")
        print(f"    • Notes: {conflict.resolution_notes}")
    
    # Show summary statistics
    summary = handler.get_conflict_summary()
    print("\n📈 Conflict Resolution Summary:")
    print(f"  • Total Conflicts: {summary['total_conflicts']}")
    print(f"  • Resolution Rate: {summary['resolution_rate']:.1f}%")
    print(f"  • Pending Review: {summary['requires_review']}")
    
    print("\n📊 Conflicts by Type:")
    for conflict_type, count in summary['conflicts_by_type'].items():
        percentage = (count / summary['total_conflicts']) * 100
        print(f"    • {conflict_type}: {count} ({percentage:.1f}%)")
    
    print("\n⚠️ Conflicts by Severity:")
    for severity, count in summary['conflicts_by_severity'].items():
        percentage = (count / summary['total_conflicts']) * 100
        print(f"    • {severity.upper()}: {count} ({percentage:.1f}%)")
    
    # Show metrics
    metrics = handler.metrics
    print("\n🎯 Performance Metrics:")
    print(f"  • Average Resolution Time: {metrics.average_resolution_time:.2f}s")
    print(f"  • Success Rate: {metrics.success_rate:.1f}%")
    if metrics.confidence_scores:
        avg_confidence = sum(metrics.confidence_scores) / len(metrics.confidence_scores)
        print(f"  • Average Confidence: {avg_confidence:.2f}")
    
    print("\n" + "="*80)
    print("💡 INTELLIGENT CONFLICT RESOLUTION")
    print("")
    print("✨ Key Capabilities Demonstrated:")
    print("  • Automatic conflict detection across data sources")
    print("  • Business-rule-based resolution strategies")
    print("  • ML-powered similarity matching")
    print("  • Configurable source prioritization")
    print("  • Comprehensive audit trails")
    print("")
    print("🎯 Perfect for:")
    print("  • Multi-source customer data integration")
    print("  • CRM and marketing automation sync")
    print("  • Data warehouse consolidation")
    print("  • Master data management")
    print("")
    print("📧 Ready to eliminate data conflicts?")
    print("🔗 Visit: https://verityai.co")
    print("💼 Connect: https://www.linkedin.com/in/sspyrou/")
    print("="*80)


if __name__ == "__main__":
    demo_conflict_resolution()
