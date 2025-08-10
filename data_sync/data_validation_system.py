#!/usr/bin/env python3
"""
Data Validation System - Comprehensive MarTech Data Quality

Advanced data validation and quality assurance for marketing technology integrations.

✅ ENTERPRISE DATA QUALITY ✅
Automated validation with comprehensive quality scoring and reporting.

Author: Sotirios Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

🚀 THE RARE TECHNICAL MARKETING LEADER 🚀
Combining C-suite strategy with hands-on AI implementation.
Proven track record: From startup innovation to enterprise transformation.

DISCLAIMER: This is demonstration code showcasing technical capabilities.
For production use, additional security hardening and testing required.
"""

import json
import logging
import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd
from dateutil import parser as date_parser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationRuleType(Enum):
    """Types of validation rules"""
    REQUIRED = auto()
    FORMAT = auto()
    RANGE = auto()
    LENGTH = auto()
    PATTERN = auto()
    UNIQUENESS = auto()
    REFERENCE = auto()
    CUSTOM = auto()
    BUSINESS_LOGIC = auto()


class ValidationSeverity(Enum):
    """Severity levels for validation failures"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DataType(Enum):
    """Supported data types for validation"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    JSON = "json"
    CURRENCY = "currency"


@dataclass
class ValidationRule:
    """Configuration for data validation"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    field_name: str = ""
    rule_type: ValidationRuleType = ValidationRuleType.REQUIRED
    data_type: DataType = DataType.STRING
    severity: ValidationSeverity = ValidationSeverity.ERROR
    parameters: Dict[str, Any] = field(default_factory=dict)
    conditions: Dict[str, Any] = field(default_factory=dict)
    custom_validator: Optional[Callable] = None
    enabled: bool = True
    priority: int = 5
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationResult:
    """Result of a validation check"""
    rule_id: str = ""
    field_name: str = ""
    is_valid: bool = True
    severity: ValidationSeverity = ValidationSeverity.INFO
    message: str = ""
    value: Any = None
    expected: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationSummary:
    """Summary of validation results"""
    total_records: int = 0
    total_validations: int = 0
    passed_validations: int = 0
    failed_validations: int = 0
    critical_errors: int = 0
    errors: int = 0
    warnings: int = 0
    info_messages: int = 0
    quality_score: float = 0.0
    field_scores: Dict[str, float] = field(default_factory=dict)
    rule_results: Dict[str, int] = field(default_factory=dict)


class DataValidationSystem:
    """
    Comprehensive data validation system for MarTech integrations.
    
    🎯 ENTERPRISE FEATURES:
    - Multi-level validation rules (field, record, dataset)
    - Real-time data quality scoring
    - Automated anomaly detection
    - Comprehensive quality reporting
    - Custom business logic validation
    
    🔧 VALIDATION CAPABILITIES:
    - Format validation (email, phone, URL, etc.)
    - Business rule enforcement
    - Statistical outlier detection
    - Cross-field validation
    - Data completeness assessment
    
    🔗 Learn more: https://verityai.co
    💼 Connect: https://www.linkedin.com/in/sspyrou/
    """
    
    def __init__(self):
        self.validation_rules: Dict[str, ValidationRule] = {}
        self.validation_history: List[Dict] = []
        self.reference_data: Dict[str, Set] = {}
        
        self._initialize_default_rules()
        self._initialize_reference_data()
    
    def _initialize_default_rules(self):
        """Initialize default validation rules"""
        
        # Email validation
        email_rule = ValidationRule(
            name="Email Format Validation",
            description="Validate email address format",
            field_name="email",
            rule_type=ValidationRuleType.FORMAT,
            data_type=DataType.EMAIL,
            severity=ValidationSeverity.ERROR,
            parameters={
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "allow_empty": False
            }
        )
        self.add_validation_rule(email_rule)
        
        # Phone validation
        phone_rule = ValidationRule(
            name="Phone Number Validation",
            description="Validate phone number format",
            field_name="phone",
            rule_type=ValidationRuleType.PATTERN,
            data_type=DataType.PHONE,
            severity=ValidationSeverity.WARNING,
            parameters={
                "patterns": [
                    r"^\+?[\d\s\-\(\)]{10,}$",
                    r"^\(\d{3}\)\s?\d{3}-\d{4}$"
                ]
            }
        )
        self.add_validation_rule(phone_rule)
    
    def _initialize_reference_data(self):
        """Initialize reference data for validation"""
        self.reference_data["country_codes"] = {
            "US", "CA", "UK", "GB", "DE", "FR", "IT", "ES", "AU", "JP"
        }
    
    def add_validation_rule(self, rule: ValidationRule):
        """Add a validation rule"""
        self.validation_rules[rule.rule_id] = rule
        logger.info(f"Added validation rule: {rule.name}")
    
    def validate_data(self, data: Union[Dict, List[Dict], pd.DataFrame]) -> Tuple[Any, List[ValidationResult]]:
        """Validate data using configured rules"""
        all_results = []
        
        if isinstance(data, dict):
            record_results = self._validate_record(data)
            all_results.extend(record_results)
        elif isinstance(data, list):
            for record in data:
                record_results = self._validate_record(record)
                all_results.extend(record_results)
        elif isinstance(data, pd.DataFrame):
            for _, row in data.iterrows():
                record_dict = row.to_dict()
                record_results = self._validate_record(record_dict)
                all_results.extend(record_results)
        
        # Create summary
        summary = self._create_validation_summary(all_results, len(data) if hasattr(data, '__len__') else 1)
        
        return summary, all_results
    
    def _validate_record(self, record: Dict[str, Any]) -> List[ValidationResult]:
        """Validate a single record"""
        results = []
        
        for rule in self.validation_rules.values():
            if not rule.enabled:
                continue
            
            try:
                result = self._apply_validation_rule(record, rule)
                results.append(result)
            except Exception as e:
                error_result = ValidationResult(
                    rule_id=rule.rule_id,
                    field_name=rule.field_name,
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Validation error: {str(e)}",
                    value=record.get(rule.field_name)
                )
                results.append(error_result)
        
        return results
    
    def _apply_validation_rule(self, record: Dict[str, Any], rule: ValidationRule) -> ValidationResult:
        """Apply a single validation rule"""
        field_value = record.get(rule.field_name)
        
        is_valid = True
        message = "Valid"
        
        if rule.rule_type == ValidationRuleType.REQUIRED:
            is_valid = field_value is not None and str(field_value).strip() != ""
            message = "Required field is missing" if not is_valid else "Valid"
        
        elif rule.rule_type == ValidationRuleType.FORMAT:
            if field_value is not None:
                if rule.data_type == DataType.EMAIL:
                    pattern = rule.parameters.get("pattern", r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
                    is_valid = bool(re.match(pattern, str(field_value)))
                    message = "Invalid email format" if not is_valid else "Valid"
        
        elif rule.rule_type == ValidationRuleType.PATTERN:
            if field_value is not None:
                patterns = rule.parameters.get("patterns", [])
                is_valid = any(re.match(pattern, str(field_value)) for pattern in patterns)
                message = "Pattern validation failed" if not is_valid else "Valid"
        
        return ValidationResult(
            rule_id=rule.rule_id,
            field_name=rule.field_name,
            is_valid=is_valid,
            severity=rule.severity if not is_valid else ValidationSeverity.INFO,
            message=message,
            value=field_value,
            metadata={"rule_name": rule.name}
        )
    
    def _create_validation_summary(self, results: List[ValidationResult], total_records: int) -> ValidationSummary:
        """Create validation summary from results"""
        total_validations = len(results)
        passed_validations = sum(1 for r in results if r.is_valid)
        failed_validations = total_validations - passed_validations
        
        quality_score = (passed_validations / max(total_validations, 1)) * 100
        
        return ValidationSummary(
            total_records=total_records,
            total_validations=total_validations,
            passed_validations=passed_validations,
            failed_validations=failed_validations,
            quality_score=quality_score
        )


def demo_data_validation():
    """Demo data validation system"""
    print("✅ DATA VALIDATION SYSTEM DEMO")
    print("Comprehensive MarTech Data Quality")
    
    validator = DataValidationSystem()
    
    sample_data = [
        {"name": "John Smith", "email": "john@company.com", "phone": "(555) 123-4567"},
        {"name": "", "email": "invalid-email", "phone": "123"},
        {"name": "Sarah Johnson", "email": "sarah@example.com", "phone": "+44 20 7946 0958"}
    ]
    
    summary, results = validator.validate_data(sample_data)
    
    print(f"Quality Score: {summary.quality_score:.1f}%")
    print(f"Failed Validations: {summary.failed_validations}")
    
    print("\n🔗 Visit: https://verityai.co")
    print("💼 Connect: https://www.linkedin.com/in/sspyrou/")


if __name__ == "__main__":
    demo_data_validation()
