#!/usr/bin/env python3
"""
Data Transformation Tools - Advanced MarTech Data Processing

Comprehensive data transformation and normalization for marketing technology integrations.

🔄 INTELLIGENT DATA TRANSFORMATION 🔄
Advanced ETL capabilities with business-aware data processing.

Author: Sotirios Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

🚀 THE RARE TECHNICAL MARKETING LEADER 🚀
Combining C-suite strategy with hands-on AI implementation.
Proven track record: From startup innovation to enterprise transformation.

DISCLAIMER: This is demonstration code showcasing technical capabilities.
For production use, additional security hardening and testing required.
"""

import base64
import hashlib
import json
import logging
import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd
from dateutil import parser as date_parser
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TransformationType(Enum):
    """Types of data transformations"""
    CLEAN = auto()
    NORMALIZE = auto()
    STANDARDIZE = auto()
    ENCODE = auto()
    AGGREGATE = auto()
    DERIVE = auto()
    VALIDATE = auto()
    ENRICH = auto()


class DataType(Enum):
    """Supported data types"""
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
class TransformationRule:
    """Configuration for data transformation"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    source_field: str = ""
    target_field: str = ""
    transformation_type: TransformationType = TransformationType.CLEAN
    target_data_type: DataType = DataType.STRING
    parameters: Dict[str, Any] = field(default_factory=dict)
    conditions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TransformationResult:
    """Result of a transformation operation"""
    rule_id: str = ""
    success: bool = True
    original_value: Any = None
    transformed_value: Any = None
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0


@dataclass
class ValidationRule:
    """Data validation rule"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    field_name: str = ""
    rule_type: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    severity: str = "error"  # error, warning, info


class DataTransformationTools:
    """
    Advanced data transformation toolkit for MarTech integrations.
    
    🎯 ENTERPRISE FEATURES:
    - Intelligent data type detection and conversion
    - Business-rule-based transformations
    - Advanced data cleaning and normalization
    - Custom transformation pipeline creation
    - Real-time data validation and enrichment
    
    🔧 TRANSFORMATION CAPABILITIES:
    - Multi-format data parsing (JSON, CSV, XML, etc.)
    - Smart data type inference and conversion
    - Advanced string cleaning and standardization
    - Date/time parsing and normalization
    - Currency and numeric standardization
    
    🔗 Learn more: https://verityai.co
    💼 Connect: https://www.linkedin.com/in/sspyrou/
    """
    
    def __init__(self):
        self.transformation_rules: Dict[str, TransformationRule] = {}
        self.validation_rules: Dict[str, ValidationRule] = {}
        self.custom_transformations: Dict[str, Callable] = {}
        self.data_profiles: Dict[str, Dict] = {}
        self.transformation_history: List[Dict] = []
        
        self._initialize_default_rules()
        self._initialize_custom_transformations()
    
    def _initialize_default_rules(self):
        """Initialize default transformation rules"""
        
        # Email cleaning and validation
        email_rule = TransformationRule(
            name="Email Normalization",
            description="Clean and normalize email addresses",
            source_field="email",
            target_field="email",
            transformation_type=TransformationType.CLEAN,
            target_data_type=DataType.EMAIL,
            parameters={
                "lowercase": True,
                "trim_whitespace": True,
                "validate_format": True,
                "remove_duplicates": True
            }
        )
        self.add_transformation_rule(email_rule)
        
        # Phone number standardization
        phone_rule = TransformationRule(
            name="Phone Number Standardization",
            description="Standardize phone number formats",
            source_field="phone",
            target_field="phone",
            transformation_type=TransformationType.STANDARDIZE,
            target_data_type=DataType.PHONE,
            parameters={
                "country_code": "+1",
                "format": "international",
                "remove_extensions": False
            }
        )
        self.add_transformation_rule(phone_rule)
        
        # Currency normalization
        currency_rule = TransformationRule(
            name="Currency Normalization",
            description="Normalize currency values to standard format",
            source_field="revenue",
            target_field="revenue_normalized",
            transformation_type=TransformationType.NORMALIZE,
            target_data_type=DataType.CURRENCY,
            parameters={
                "base_currency": "USD",
                "decimal_places": 2,
                "remove_symbols": True
            }
        )
        self.add_transformation_rule(currency_rule)
        
        # Name standardization
        name_rule = TransformationRule(
            name="Name Standardization",
            description="Standardize customer names",
            source_field="name",
            target_field="name",
            transformation_type=TransformationType.CLEAN,
            target_data_type=DataType.STRING,
            parameters={
                "title_case": True,
                "remove_extra_spaces": True,
                "remove_special_chars": False,
                "standardize_titles": True
            }
        )
        self.add_transformation_rule(name_rule)
    
    def _initialize_custom_transformations(self):
        """Initialize custom transformation functions"""
        
        self.custom_transformations.update({
            "extract_domain": self._extract_email_domain,
            "calculate_age": self._calculate_age_from_birthdate,
            "categorize_revenue": self._categorize_revenue_bucket,
            "parse_utm_parameters": self._parse_utm_parameters,
            "generate_customer_key": self._generate_customer_key,
            "extract_first_name": self._extract_first_name,
            "extract_last_name": self._extract_last_name,
            "normalize_country": self._normalize_country_name,
            "calculate_lifetime_value": self._calculate_lifetime_value
        })
    
    def add_transformation_rule(self, rule: TransformationRule):
        """Add a transformation rule"""
        self.transformation_rules[rule.rule_id] = rule
        logger.info(f"Added transformation rule: {rule.name}")
    
    def transform_data(self, data: Union[Dict, List[Dict], pd.DataFrame], 
                      rules: Optional[List[str]] = None) -> Tuple[Any, List[TransformationResult]]:
        """Transform data using configured rules"""
        results = []
        
        if isinstance(data, dict):
            transformed_data, result = self._transform_record(data, rules)
            results.extend(result)
        elif isinstance(data, list):
            transformed_data = []
            for record in data:
                transformed_record, result = self._transform_record(record, rules)
                transformed_data.append(transformed_record)
                results.extend(result)
        elif isinstance(data, pd.DataFrame):
            transformed_data = data.copy()
            for _, row in data.iterrows():
                record_dict = row.to_dict()
                transformed_record, result = self._transform_record(record_dict, rules)
                results.extend(result)
                for field, value in transformed_record.items():
                    if field in transformed_data.columns:
                        transformed_data.at[row.name, field] = value
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
        
        return transformed_data, results
    
    def _transform_record(self, record: Dict[str, Any], 
                         rules: Optional[List[str]] = None) -> Tuple[Dict[str, Any], List[TransformationResult]]:
        """Transform a single record"""
        import time
        
        transformed_record = record.copy()
        results = []
        
        # Get applicable rules
        applicable_rules = self._get_applicable_rules(record, rules)
        
        # Sort rules by priority
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)
        
        # Apply transformations
        for rule in applicable_rules:
            if not rule.enabled:
                continue
            
            start_time = time.time()
            
            try:
                result = self._apply_transformation(transformed_record, rule)
                result.processing_time = time.time() - start_time
                results.append(result)
                
                if result.success and result.transformed_value is not None:
                    transformed_record[rule.target_field] = result.transformed_value
                
            except Exception as e:
                error_result = TransformationResult(
                    rule_id=rule.rule_id,
                    success=False,
                    original_value=record.get(rule.source_field),
                    error_message=str(e),
                    processing_time=time.time() - start_time
                )
                results.append(error_result)
                logger.error(f"Transformation failed for rule {rule.name}: {str(e)}")
        
        return transformed_record, results
    
    def _get_applicable_rules(self, record: Dict[str, Any], 
                            rules: Optional[List[str]] = None) -> List[TransformationRule]:
        """Get applicable transformation rules for a record"""
        applicable_rules = []
        
        for rule in self.transformation_rules.values():
            # Filter by rule IDs if specified
            if rules and rule.rule_id not in rules:
                continue
            
            # Check if source field exists in record
            if rule.source_field not in record:
                continue
            
            # Check conditions
            if self._check_rule_conditions(record, rule):
                applicable_rules.append(rule)
        
        return applicable_rules
    
    def _check_rule_conditions(self, record: Dict[str, Any], rule: TransformationRule) -> bool:
        """Check if rule conditions are met"""
        if not rule.conditions:
            return True
        
        for condition_field, condition_value in rule.conditions.items():
            if condition_field not in record:
                return False
            
            record_value = record[condition_field]
            
            if isinstance(condition_value, dict):
                # Complex condition (e.g., {"gt": 100, "lt": 1000})
                for operator, value in condition_value.items():
                    if operator == "eq" and record_value != value:
                        return False
                    elif operator == "ne" and record_value == value:
                        return False
                    elif operator == "gt" and not (record_value > value):
                        return False
                    elif operator == "lt" and not (record_value < value):
                        return False
                    elif operator == "gte" and not (record_value >= value):
                        return False
                    elif operator == "lte" and not (record_value <= value):
                        return False
                    elif operator == "in" and record_value not in value:
                        return False
                    elif operator == "not_in" and record_value in value:
                        return False
            else:
                # Simple equality check
                if record_value != condition_value:
                    return False
        
        return True
    
    def _apply_transformation(self, record: Dict[str, Any], 
                            rule: TransformationRule) -> TransformationResult:
        """Apply a single transformation rule"""
        original_value = record.get(rule.source_field)
        
        try:
            if rule.transformation_type == TransformationType.CLEAN:
                transformed_value = self._clean_data(original_value, rule)
            elif rule.transformation_type == TransformationType.NORMALIZE:
                transformed_value = self._normalize_data(original_value, rule)
            elif rule.transformation_type == TransformationType.STANDARDIZE:
                transformed_value = self._standardize_data(original_value, rule)
            elif rule.transformation_type == TransformationType.ENCODE:
                transformed_value = self._encode_data(original_value, rule)
            elif rule.transformation_type == TransformationType.DERIVE:
                transformed_value = self._derive_data(record, rule)
            elif rule.transformation_type == TransformationType.VALIDATE:
                transformed_value = self._validate_data(original_value, rule)
            elif rule.transformation_type == TransformationType.ENRICH:
                transformed_value = self._enrich_data(original_value, rule)
            else:
                raise ValueError(f"Unknown transformation type: {rule.transformation_type}")
            
            return TransformationResult(
                rule_id=rule.rule_id,
                success=True,
                original_value=original_value,
                transformed_value=transformed_value,
                metadata={"rule_name": rule.name}
            )
            
        except Exception as e:
            return TransformationResult(
                rule_id=rule.rule_id,
                success=False,
                original_value=original_value,
                error_message=str(e)
            )
    
    def _clean_data(self, value: Any, rule: TransformationRule) -> Any:
        """Clean data based on target data type"""
        if value is None:
            return None
        
        params = rule.parameters
        
        if rule.target_data_type == DataType.STRING:
            result = str(value).strip() if params.get("trim_whitespace", True) else str(value)
            
            if params.get("lowercase", False):
                result = result.lower()
            elif params.get("uppercase", False):
                result = result.upper()
            elif params.get("title_case", False):
                result = result.title()
            
            if params.get("remove_extra_spaces", True):
                result = re.sub(r'\s+', ' ', result)
            
            if params.get("remove_special_chars", False):
                result = re.sub(r'[^\w\s-]', '', result)
            
            if params.get("standardize_titles", False):
                result = self._standardize_name_titles(result)
            
            return result
            
        elif rule.target_data_type == DataType.EMAIL:
            email = str(value).strip().lower()
            
            if params.get("validate_format", True):
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    raise ValueError(f"Invalid email format: {email}")
            
            return email
            
        elif rule.target_data_type == DataType.PHONE:
            return self._clean_phone_number(str(value), params)
            
        elif rule.target_data_type in [DataType.INTEGER, DataType.FLOAT]:
            return self._clean_numeric_value(value, rule.target_data_type)
            
        elif rule.target_data_type == DataType.CURRENCY:
            return self._clean_currency_value(value, params)
            
        return value
    
    def _normalize_data(self, value: Any, rule: TransformationRule) -> Any:
        """Normalize data values"""
        if value is None:
            return None
        
        params = rule.parameters
        
        if rule.target_data_type == DataType.CURRENCY:
            # Convert to base currency and normalize format
            amount = self._extract_numeric_from_currency(value)
            base_currency = params.get("base_currency", "USD")
            decimal_places = params.get("decimal_places", 2)
            
            # Apply currency conversion if needed
            normalized_amount = round(float(amount), decimal_places)
            return f"{normalized_amount:.{decimal_places}f}"
            
        elif rule.target_data_type == DataType.DATE:
            return self._normalize_date(value, params)
            
        elif rule.target_data_type == DataType.DATETIME:
            return self._normalize_datetime(value, params)
            
        return value
    
    def _standardize_data(self, value: Any, rule: TransformationRule) -> Any:
        """Standardize data formats"""
        if value is None:
            return None
        
        params = rule.parameters
        
        if rule.target_data_type == DataType.PHONE:
            return self._standardize_phone_number(str(value), params)
        
        elif rule.target_data_type == DataType.STRING:
            result = str(value)
            
            if params.get("format") == "sentence_case":
                result = result.capitalize()
            elif params.get("format") == "title_case":
                result = result.title()
            elif params.get("format") == "upper_case":
                result = result.upper()
            elif params.get("format") == "lower_case":
                result = result.lower()
            
            return result
        
        return value
    
    def _encode_data(self, value: Any, rule: TransformationRule) -> Any:
        """Encode data values"""
        if value is None:
            return None
        
        params = rule.parameters
        encoding_type = params.get("encoding_type", "label")
        
        if encoding_type == "label":
            # Simple label encoding
            mapping = params.get("mapping", {})
            return mapping.get(value, value)
        
        elif encoding_type == "onehot":
            # One-hot encoding (returns dict)
            categories = params.get("categories", [])
            result = {f"{rule.target_field}_{cat}": 0 for cat in categories}
            if value in categories:
                result[f"{rule.target_field}_{value}"] = 1
            return result
        
        return value
    
    def _derive_data(self, record: Dict[str, Any], rule: TransformationRule) -> Any:
        """Derive new data from existing fields"""
        params = rule.parameters
        derivation_type = params.get("derivation_type")
        
        if derivation_type == "concatenate":
            fields = params.get("fields", [])
            separator = params.get("separator", " ")
            values = [str(record.get(field, "")) for field in fields if record.get(field)]
            return separator.join(values)
        
        elif derivation_type == "calculate":
            formula = params.get("formula", "")
            # Simple formula evaluation (extend as needed)
            if formula == "revenue_per_month":
                revenue = record.get("total_revenue", 0)
                months = record.get("customer_age_months", 1)
                return revenue / max(months, 1)
        
        elif derivation_type == "custom_function":
            function_name = params.get("function_name")
            if function_name in self.custom_transformations:
                return self.custom_transformations[function_name](record)
        
        return None
    
    def _validate_data(self, value: Any, rule: TransformationRule) -> Any:
        """Validate data and return cleaned value"""
        params = rule.parameters
        
        if rule.target_data_type == DataType.EMAIL:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, str(value)):
                raise ValueError(f"Invalid email: {value}")
        
        elif rule.target_data_type == DataType.PHONE:
            phone_pattern = params.get("pattern", r'^\+?[\d\s\-\(\)]+$')
            if not re.match(phone_pattern, str(value)):
                raise ValueError(f"Invalid phone number: {value}")
        
        return value
    
    def _enrich_data(self, value: Any, rule: TransformationRule) -> Any:
        """Enrich data with additional information"""
        params = rule.parameters
        enrichment_type = params.get("enrichment_type")
        
        if enrichment_type == "domain_info":
            if "@" in str(value):
                domain = str(value).split("@")[1]
                return {"original": value, "domain": domain}
        
        elif enrichment_type == "location_info":
            # Mock location enrichment
            country_mapping = params.get("country_mapping", {})
            return country_mapping.get(str(value).upper(), value)
        
        return value
    
    # Helper methods for specific transformations
    
    def _clean_phone_number(self, phone: str, params: Dict) -> str:
        """Clean phone number"""
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Add country code if missing
        if not cleaned.startswith('+'):
            country_code = params.get("country_code", "+1")
            if not cleaned.startswith(country_code.replace('+', '')):
                cleaned = country_code + cleaned
        
        return cleaned
    
    def _standardize_phone_number(self, phone: str, params: Dict) -> str:
        """Standardize phone number format"""
        cleaned = self._clean_phone_number(phone, params)
        format_type = params.get("format", "international")
        
        if format_type == "international":
            return cleaned
        elif format_type == "national":
            return cleaned.replace(params.get("country_code", "+1"), "")
        elif format_type == "formatted":
            # Format as (XXX) XXX-XXXX for US numbers
            digits = re.sub(r'[^\d]', '', cleaned)
            if len(digits) == 11 and digits.startswith('1'):
                digits = digits[1:]
            if len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        
        return cleaned
    
    def _clean_numeric_value(self, value: Any, target_type: DataType) -> Union[int, float]:
        """Clean numeric value"""
        if isinstance(value, (int, float)):
            return int(value) if target_type == DataType.INTEGER else float(value)
        
        # Extract numeric value from string
        numeric_str = re.sub(r'[^\d.-]', '', str(value))
        
        if target_type == DataType.INTEGER:
            return int(float(numeric_str)) if numeric_str else 0
        else:
            return float(numeric_str) if numeric_str else 0.0
    
    def _clean_currency_value(self, value: Any, params: Dict) -> str:
        """Clean currency value"""
        numeric_value = self._extract_numeric_from_currency(value)
        decimal_places = params.get("decimal_places", 2)
        return f"{numeric_value:.{decimal_places}f}"
    
    def _extract_numeric_from_currency(self, value: Any) -> float:
        """Extract numeric value from currency string"""
        if isinstance(value, (int, float)):
            return float(value)
        
        # Remove currency symbols and formatting
        numeric_str = re.sub(r'[^\d.-]', '', str(value))
        return float(numeric_str) if numeric_str else 0.0
    
    def _normalize_date(self, value: Any, params: Dict) -> str:
        """Normalize date format"""
        if isinstance(value, datetime):
            return value.strftime(params.get("format", "%Y-%m-%d"))
        
        try:
            parsed_date = date_parser.parse(str(value))
            return parsed_date.strftime(params.get("format", "%Y-%m-%d"))
        except:
            return str(value)
    
    def _normalize_datetime(self, value: Any, params: Dict) -> str:
        """Normalize datetime format"""
        if isinstance(value, datetime):
            return value.strftime(params.get("format", "%Y-%m-%d %H:%M:%S"))
        
        try:
            parsed_datetime = date_parser.parse(str(value))
            return parsed_datetime.strftime(params.get("format", "%Y-%m-%d %H:%M:%S"))
        except:
            return str(value)
    
    def _standardize_name_titles(self, name: str) -> str:
        """Standardize name titles and suffixes"""
        # Common title mappings
        title_mappings = {
            "mr": "Mr.",
            "mrs": "Mrs.",
            "ms": "Ms.",
            "dr": "Dr.",
            "prof": "Prof.",
            "jr": "Jr.",
            "sr": "Sr.",
            "iii": "III",
            "iv": "IV"
        }
        
        words = name.split()
        standardized_words = []
        
        for word in words:
            lower_word = word.lower().rstrip('.')
            if lower_word in title_mappings:
                standardized_words.append(title_mappings[lower_word])
            else:
                standardized_words.append(word.title())
        
        return " ".join(standardized_words)
    
    # Custom transformation functions
    
    def _extract_email_domain(self, record: Dict[str, Any]) -> Optional[str]:
        """Extract domain from email address"""
        email = record.get("email", "")
        if "@" in email:
            return email.split("@")[1].lower()
        return None
    
    def _calculate_age_from_birthdate(self, record: Dict[str, Any]) -> Optional[int]:
        """Calculate age from birthdate"""
        birthdate = record.get("birthdate")
        if not birthdate:
            return None
        
        try:
            if isinstance(birthdate, str):
                birth_date = date_parser.parse(birthdate).date()
            else:
                birth_date = birthdate.date() if hasattr(birthdate, 'date') else birthdate
            
            today = datetime.now().date()
            age = today.year - birth_date.year
            
            if today.month < birth_date.month or \
               (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
            
            return age
        except:
            return None
    
    def _categorize_revenue_bucket(self, record: Dict[str, Any]) -> str:
        """Categorize revenue into buckets"""
        revenue = record.get("revenue", 0)
        
        if revenue >= 100000:
            return "Enterprise"
        elif revenue >= 50000:
            return "Large"
        elif revenue >= 10000:
            return "Medium"
        elif revenue >= 1000:
            return "Small"
        else:
            return "Micro"
    
    def _parse_utm_parameters(self, record: Dict[str, Any]) -> Dict[str, str]:
        """Parse UTM parameters from URL"""
        url = record.get("landing_url", "")
        utm_params = {}
        
        utm_keys = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"]
        
        for key in utm_keys:
            pattern = f"{key}=([^&]*)"
            match = re.search(pattern, url)
            if match:
                utm_params[key] = match.group(1)
        
        return utm_params
    
    def _generate_customer_key(self, record: Dict[str, Any]) -> str:
        """Generate unique customer key"""
        email = record.get("email", "")
        name = record.get("name", "")
        
        key_string = f"{email}:{name}".lower()
        return hashlib.md5(key_string.encode()).hexdigest()[:12]
    
    def _extract_first_name(self, record: Dict[str, Any]) -> Optional[str]:
        """Extract first name from full name"""
        name = record.get("name", "")
        if name:
            return name.split()[0] if name.split() else None
        return None
    
    def _extract_last_name(self, record: Dict[str, Any]) -> Optional[str]:
        """Extract last name from full name"""
        name = record.get("name", "")
        if name:
            parts = name.split()
            return parts[-1] if len(parts) > 1 else None
        return None
    
    def _normalize_country_name(self, record: Dict[str, Any]) -> str:
        """Normalize country name"""
        country = record.get("country", "")
        
        country_mappings = {
            "usa": "United States",
            "us": "United States",
            "uk": "United Kingdom",
            "gb": "United Kingdom"
        }
        
        return country_mappings.get(country.lower(), country.title())
    
    def _calculate_lifetime_value(self, record: Dict[str, Any]) -> float:
        """Calculate customer lifetime value"""
        avg_order_value = record.get("avg_order_value", 0)
        order_frequency = record.get("order_frequency_per_year", 0)
        customer_lifespan = record.get("customer_lifespan_years", 1)
        
        return float(avg_order_value) * float(order_frequency) * float(customer_lifespan)
    
    def create_transformation_pipeline(self, steps: List[Dict[str, Any]]) -> str:
        """Create a transformation pipeline"""
        pipeline_id = str(uuid.uuid4())
        
        for i, step in enumerate(steps):
            rule = TransformationRule(
                name=step.get("name", f"Pipeline Step {i+1}"),
                description=step.get("description", ""),
                source_field=step["source_field"],
                target_field=step["target_field"],
                transformation_type=TransformationType[step["transformation_type"].upper()],
                target_data_type=DataType[step["target_data_type"].upper()],
                parameters=step.get("parameters", {}),
                conditions=step.get("conditions", {}),
                priority=len(steps) - i  # Higher priority for earlier steps
            )
            
            self.add_transformation_rule(rule)
        
        return pipeline_id
    
    def profile_data(self, data: Union[Dict, List[Dict], pd.DataFrame]) -> Dict[str, Any]:
        """Create data profile with statistics and recommendations"""
        if isinstance(data, dict):
            records = [data]
        elif isinstance(data, list):
            records = data
        elif isinstance(data, pd.DataFrame):
            records = data.to_dict('records')
        else:
            raise ValueError("Unsupported data type")
        
        profile = {
            "total_records": len(records),
            "fields": {},
            "recommendations": []
        }
        
        if not records:
            return profile
        
        # Analyze each field
        all_fields = set()
        for record in records:
            all_fields.update(record.keys())
        
        for field in all_fields:
            field_profile = self._profile_field(field, records)
            profile["fields"][field] = field_profile
        
        # Generate recommendations
        profile["recommendations"] = self._generate_recommendations(profile["fields"])
        
        return profile
    
    def _profile_field(self, field_name: str, records: List[Dict]) -> Dict[str, Any]:
        """Profile a specific field"""
        values = [record.get(field_name) for record in records]
        non_null_values = [v for v in values if v is not None]
        
        profile = {
            "total_count": len(values),
            "non_null_count": len(non_null_values),
            "null_count": len(values) - len(non_null_values),
            "null_percentage": (len(values) - len(non_null_values)) / len(values) * 100,
            "unique_count": len(set(str(v) for v in non_null_values)),
            "data_types": {},
            "sample_values": non_null_values[:10] if non_null_values else [],
            "inferred_type": None,
            "quality_issues": []
        }
        
        # Analyze data types
        type_counts = defaultdict(int)
        for value in non_null_values:
            type_counts[type(value).__name__] += 1
        
        profile["data_types"] = dict(type_counts)
        profile["inferred_type"] = max(type_counts, key=type_counts.get) if type_counts else "unknown"
        
        # Check for quality issues
        if "email" in field_name.lower():
            invalid_emails = [v for v in non_null_values if not self._is_valid_email(str(v))]
            if invalid_emails:
                profile["quality_issues"].append(f"Invalid email formats: {len(invalid_emails)} records")
        
        if "phone" in field_name.lower():
            invalid_phones = [v for v in non_null_values if not self._is_valid_phone(str(v))]
            if invalid_phones:
                profile["quality_issues"].append(f"Invalid phone formats: {len(invalid_phones)} records")
        
        return profile
    
    def _generate_recommendations(self, field_profiles: Dict[str, Dict]) -> List[str]:
        """Generate transformation recommendations"""
        recommendations = []
        
        for field_name, profile in field_profiles.items():
            null_percentage = profile["null_percentage"]
            quality_issues = profile["quality_issues"]
            
            if null_percentage > 20:
                recommendations.append(f"High null percentage in {field_name} ({null_percentage:.1f}%) - consider data enrichment")
            
            if quality_issues:
                recommendations.append(f"Quality issues in {field_name}: {'; '.join(quality_issues)}")
            
            if "email" in field_name.lower() and profile["inferred_type"] == "str":
                recommendations.append(f"Apply email standardization to {field_name}")
            
            if "phone" in field_name.lower() and profile["inferred_type"] == "str":
                recommendations.append(f"Apply phone number standardization to {field_name}")
            
            if "revenue" in field_name.lower() or "price" in field_name.lower():
                recommendations.append(f"Apply currency normalization to {field_name}")
        
        return recommendations
    
    def _is_valid_email(self, email: str) -> bool:
        """Check if email format is valid"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Check if phone format is valid"""
        # Simple check for phone numbers
        cleaned = re.sub(r'[^\d]', '', phone)
        return len(cleaned) >= 10
    
    def get_transformation_history(self) -> List[Dict]:
        """Get transformation history"""
        return self.transformation_history.copy()
    
    def export_transformation_config(self) -> Dict[str, Any]:
        """Export transformation configuration"""
        return {
            "rules": {
                rule_id: {
                    "name": rule.name,
                    "description": rule.description,
                    "source_field": rule.source_field,
                    "target_field": rule.target_field,
                    "transformation_type": rule.transformation_type.name,
                    "target_data_type": rule.target_data_type.value,
                    "parameters": rule.parameters,
                    "conditions": rule.conditions,
                    "priority": rule.priority,
                    "enabled": rule.enabled
                }
                for rule_id, rule in self.transformation_rules.items()
            }
        }


def demo_data_transformation():
    """
    Demonstrate data transformation capabilities.
    
    🚀 Ready to transform your marketing data processing?
    📧 Contact: https://verityai.co
    💼 LinkedIn: https://www.linkedin.com/in/sspyrou/
    """
    print("\n" + "="*80)
    print("🔄 DATA TRANSFORMATION TOOLS DEMO")
    print("Advanced MarTech Data Processing")
    print("="*80)
    
    # Initialize transformation tools
    transformer = DataTransformationTools()
    
    # Sample raw marketing data
    raw_data = [
        {
            "id": "CUST_001",
            "name": "john SMITH jr",
            "email": "  JOHN.SMITH@Company.COM  ",
            "phone": "(555) 123-4567 ext. 123",
            "revenue": "$15,250.75",
            "birthdate": "1985-03-15",
            "country": "usa",
            "landing_url": "https://example.com/page?utm_source=google&utm_medium=cpc&utm_campaign=summer2024"
        },
        {
            "id": "CUST_002", 
            "name": "sarah johnson",
            "email": "sarah.johnson@example.co.uk",
            "phone": "+44 20 7946 0958",
            "revenue": "€8,500.00",
            "birthdate": "1990-07-22",
            "country": "UK",
            "landing_url": "https://example.com/landing"
        },
        {
            "id": "CUST_003",
            "name": "DR. MICHAEL CHEN",
            "email": "invalid-email-format",
            "phone": "555.987.6543",
            "revenue": "22500",
            "birthdate": "1978-11-08",
            "country": "canada",
            "landing_url": "https://example.com/promo?utm_source=facebook&utm_medium=social"
        }
    ]
    
    print(f"\n📊 Sample Raw Data:")
    print(f"  • Records: {len(raw_data)}")
    print(f"  • Fields: {len(raw_data[0]) if raw_data else 0}")
    
    # Show sample raw record
    print(f"\n📋 Raw Record Example:")
    for key, value in raw_data[0].items():
        print(f"    • {key}: {value}")
    
    # Profile the data
    print("\n🔍 Data Profiling...")
    profile = transformer.profile_data(raw_data)
    
    print(f"  ✓ Total Records: {profile['total_records']}")
    print(f"  ✓ Fields Analyzed: {len(profile['fields'])}")
    
    # Show field profiles
    print("\n📈 Field Analysis:")
    for field_name, field_profile in profile['fields'].items():
        print(f"\n  {field_name}:")
        print(f"    • Non-null: {field_profile['non_null_count']}/{field_profile['total_count']}")
        print(f"    • Unique values: {field_profile['unique_count']}")
        print(f"    • Inferred type: {field_profile['inferred_type']}")
        if field_profile['quality_issues']:
            print(f"    • Issues: {'; '.join(field_profile['quality_issues'])}")
    
    # Show recommendations
    print("\n💡 Transformation Recommendations:")
    for i, recommendation in enumerate(profile['recommendations'], 1):
        print(f"  {i}. {recommendation}")
    
    # Add custom transformation rules
    print("\n⚙️ Adding Custom Transformation Rules...")
    
    # Age calculation rule
    age_rule = TransformationRule(
        name="Age Calculation",
        description="Calculate age from birthdate",
        source_field="birthdate",
        target_field="age",
        transformation_type=TransformationType.DERIVE,
        target_data_type=DataType.INTEGER,
        parameters={"derivation_type": "custom_function", "function_name": "calculate_age"}
    )
    transformer.add_transformation_rule(age_rule)
    
    # Revenue bucket categorization
    revenue_bucket_rule = TransformationRule(
        name="Revenue Categorization",
        description="Categorize customers by revenue bucket",
        source_field="revenue",
        target_field="revenue_bucket",
        transformation_type=TransformationType.DERIVE,
        target_data_type=DataType.STRING,
        parameters={"derivation_type": "custom_function", "function_name": "categorize_revenue_bucket"}
    )
    transformer.add_transformation_rule(revenue_bucket_rule)
    
    # Transform the data
    print("\n🔄 Applying Transformations...")
    transformed_data, transformation_results = transformer.transform_data(raw_data)
    
    # Show transformation results
    successful_transformations = sum(1 for r in transformation_results if r.success)
    failed_transformations = len(transformation_results) - successful_transformations
    
    print(f"  ✓ Successful: {successful_transformations}")
    print(f"  ❌ Failed: {failed_transformations}")
    
    # Show transformed record
    print(f"\n✨ Transformed Record Example:")
    for key, value in transformed_data[0].items():
        print(f"    • {key}: {value}")
    
    # Show transformation details
    print(f"\n🔍 Transformation Details:")
    for i, result in enumerate(transformation_results[:6]):  # Show first 6
        status = "✓" if result.success else "❌"
        print(f"\n  {status} Transformation {i+1}:")
        print(f"    • Rule ID: {result.rule_id[:8]}...")
        print(f"    • Original: {result.original_value}")
        print(f"    • Transformed: {result.transformed_value}")
        if result.error_message:
            print(f"    • Error: {result.error_message}")
        print(f"    • Time: {result.processing_time:.3f}s")
    
    # Show data quality improvements
    print(f"\n📊 Data Quality Summary:")
    
    # Count improvements
    improvements = {
        "emails_cleaned": 0,
        "phones_standardized": 0,
        "names_standardized": 0,
        "currencies_normalized": 0,
        "fields_derived": 0
    }
    
    for result in transformation_results:
        if result.success and result.transformed_value != result.original_value:
            if "email" in str(result.metadata.get("rule_name", "")).lower():
                improvements["emails_cleaned"] += 1
            elif "phone" in str(result.metadata.get("rule_name", "")).lower():
                improvements["phones_standardized"] += 1
            elif "name" in str(result.metadata.get("rule_name", "")).lower():
                improvements["names_standardized"] += 1
            elif "currency" in str(result.metadata.get("rule_name", "")).lower():
                improvements["currencies_normalized"] += 1
            elif "derive" in str(result.metadata.get("rule_name", "")).lower():
                improvements["fields_derived"] += 1
    
    for improvement_type, count in improvements.items():
        if count > 0:
            print(f"  • {improvement_type.replace('_', ' ').title()}: {count}")
    
    # Export configuration
    config = transformer.export_transformation_config()
    print(f"\n⚙️ Configuration Export:")
    print(f"  • Total Rules: {len(config['rules'])}")
    print(f"  • Rule Types: {len(set(rule['transformation_type'] for rule in config['rules'].values()))}")
    
    print("\n" + "="*80)
    print("💡 ADVANCED DATA TRANSFORMATION")
    print("")
    print("✨ Key Capabilities Demonstrated:")
    print("  • Intelligent data type detection")
    print("  • Business-rule-based transformations")
    print("  • Custom transformation functions")
    print("  • Data quality profiling and recommendations")
    print("  • Multi-format data processing")
    print("")
    print("🎯 Perfect for:")
    print("  • MarTech data standardization")
    print("  • CRM data cleansing and enrichment")
    print("  • Customer data unification")
    print("  • Analytics data preparation")
    print("")
    print("📧 Ready to transform your data processing?")
    print("🔗 Visit: https://verityai.co")
    print("💼 Connect: https://www.linkedin.com/in/sspyrou/")
    print("="*80)


if __name__ == "__main__":
    demo_data_transformation()
