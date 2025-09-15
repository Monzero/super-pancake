# utils/validation_utils.py

import pandas as pd
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import numpy as np

class ValidationUtils:
    """Utility functions for data validation and quality checks"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, str(email).strip())) if email else False
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', str(phone))
        # Check if it's a valid length (7-15 digits)
        return 7 <= len(digits_only) <= 15
    
    @staticmethod
    def validate_date(date_str: str, date_formats: List[str] = None) -> Tuple[bool, Optional[datetime]]:
        """Validate date string against common formats"""
        if not date_str:
            return False, None
        
        if date_formats is None:
            date_formats = [
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%Y-%m-%d %H:%M:%S',
                '%m/%d/%Y %H:%M:%S',
                '%Y%m%d'
            ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(str(date_str).strip(), fmt)
                return True, parsed_date
            except ValueError:
                continue
        
        return False, None
    
    @staticmethod
    def validate_numeric_range(value: Any, min_val: float = None, max_val: float = None) -> bool:
        """Validate if numeric value is within specified range"""
        try:
            num_val = float(value)
            if min_val is not None and num_val < min_val:
                return False
            if max_val is not None and num_val > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_string_length(value: str, min_length: int = None, max_length: int = None) -> bool:
        """Validate string length constraints"""
        if value is None:
            return False
        
        str_val = str(value)
        length = len(str_val)
        
        if min_length is not None and length < min_length:
            return False
        if max_length is not None and length > max_length:
            return False
        
        return True
    
    @staticmethod
    def validate_pattern(value: str, pattern: str) -> bool:
        """Validate string against regex pattern"""
        if not value or not pattern:
            return False
        try:
            return bool(re.match(pattern, str(value)))
        except re.error:
            return False
    
    @staticmethod
    def detect_data_type(series: pd.Series) -> str:
        """Detect the most appropriate data type for a pandas Series"""
        # Remove nulls for analysis
        non_null_series = series.dropna()
        
        if len(non_null_series) == 0:
            return 'unknown'
        
        # Try to detect numeric types
        try:
            pd.to_numeric(non_null_series)
            # Check if it's integer
            if all(float(x).is_integer() for x in non_null_series):
                return 'integer'
            else:
                return 'float'
        except (ValueError, TypeError):
            pass
        
        # Try to detect dates
        date_count = 0
        for val in non_null_series.head(100):  # Sample first 100 values
            is_valid, _ = ValidationUtils.validate_date(str(val))
            if is_valid:
                date_count += 1
        
        if date_count > len(non_null_series) * 0.8:  # 80% are valid dates
            return 'date'
        
        # Try to detect boolean
        unique_vals = set(str(x).lower() for x in non_null_series.unique())
        bool_vals = {'true', 'false', 't', 'f', 'yes', 'no', 'y', 'n', '1', '0'}
        if unique_vals.issubset(bool_vals) and len(unique_vals) <= 2:
            return 'boolean'
        
        # Check for email patterns
        email_count = sum(1 for x in non_null_series.head(100) 
                         if ValidationUtils.validate_email(str(x)))
        if email_count > len(non_null_series.head(100)) * 0.8:
            return 'email'
        
        # Check for phone patterns
        phone_count = sum(1 for x in non_null_series.head(100) 
                         if ValidationUtils.validate_phone(str(x)))
        if phone_count > len(non_null_series.head(100)) * 0.8:
            return 'phone'
        
        # Default to string
        return 'string'
    
    @staticmethod
    def check_data_consistency(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Check for data consistency issues across the DataFrame"""
        issues = []
        
        for column in df.columns:
            series = df[column]
            
            # Check for mixed data types
            if series.dtype == 'object':
                types_found = set()
                for val in series.dropna().head(100):
                    if isinstance(val, str):
                        types_found.add('string')
                    elif isinstance(val, (int, float)):
                        types_found.add('numeric')
                    elif isinstance(val, bool):
                        types_found.add('boolean')
                
                if len(types_found) > 1:
                    issues.append({
                        'column': column,
                        'issue_type': 'mixed_data_types',
                        'severity': 'MEDIUM',
                        'description': f"Column contains mixed data types: {', '.join(types_found)}"
                    })
            
            # Check for suspicious patterns
            if series.dtype == 'object':
                # Check for leading/trailing spaces
                string_series = series.astype(str)
                spaces_count = (string_series != string_series.str.strip()).sum()
                if spaces_count > 0:
                    issues.append({
                        'column': column,
                        'issue_type': 'whitespace_issues',
                        'severity': 'LOW',
                        'description': f"Found {spaces_count} values with leading/trailing spaces"
                    })
                
                # Check for case inconsistency
                unique_values = series.dropna().unique()
                if len(unique_values) > 1:
                    lower_values = set(str(x).lower() for x in unique_values)
                    if len(lower_values) < len(unique_values):
                        issues.append({
                            'column': column,
                            'issue_type': 'case_inconsistency',
                            'severity': 'LOW',
                            'description': f"Found case inconsistencies in categorical data"
                        })
        
        return issues
    
    @staticmethod
    def validate_referential_integrity(
        child_df: pd.DataFrame, 
        parent_df: pd.DataFrame,
        child_key: str,
        parent_key: str
    ) -> List[Dict[str, Any]]:
        """Validate referential integrity between two DataFrames"""
        issues = []
        
        if child_key not in child_df.columns:
            issues.append({
                'issue_type': 'missing_column',
                'severity': 'HIGH',
                'description': f"Child key '{child_key}' not found in child table"
            })
            return issues
        
        if parent_key not in parent_df.columns:
            issues.append({
                'issue_type': 'missing_column',
                'severity': 'HIGH',
                'description': f"Parent key '{parent_key}' not found in parent table"
            })
            return issues
        
        # Check for orphaned records
        child_values = set(child_df[child_key].dropna())
        parent_values = set(parent_df[parent_key].dropna())
        
        orphaned_values = child_values - parent_values
        if orphaned_values:
            issues.append({
                'issue_type': 'referential_integrity_violation',
                'severity': 'HIGH',
                'description': f"Found {len(orphaned_values)} orphaned records in child table",
                'orphaned_count': len(orphaned_values),
                'sample_orphaned_values': list(orphaned_values)[:5]
            })
        
        return issues
    
    @staticmethod
    def validate_unique_constraints(df: pd.DataFrame, unique_columns: List[str]) -> List[Dict[str, Any]]:
        """Validate unique constraints on specified columns"""
        issues = []
        
        for column in unique_columns:
            if column not in df.columns:
                issues.append({
                    'column': column,
                    'issue_type': 'missing_column',
                    'severity': 'HIGH',
                    'description': f"Unique constraint column '{column}' not found"
                })
                continue
            
            duplicates = df[column].duplicated().sum()
            if duplicates > 0:
                issues.append({
                    'column': column,
                    'issue_type': 'unique_constraint_violation',
                    'severity': 'HIGH',
                    'description': f"Found {duplicates} duplicate values in unique column",
                    'duplicate_count': duplicates
                })
        
        return issues
    
    @staticmethod
    def calculate_data_quality_score(
        total_records: int,
        null_count: int,
        duplicate_count: int,
        validation_errors: int,
        constraint_violations: int
    ) -> float:
        """Calculate overall data quality score (0-100)"""
        if total_records == 0:
            return 0.0
        
        # Calculate individual quality metrics
        completeness = (total_records - null_count) / total_records
        uniqueness = (total_records - duplicate_count) / total_records if total_records > 0 else 1.0
        validity = (total_records - validation_errors) / total_records if total_records > 0 else 1.0
        consistency = (total_records - constraint_violations) / total_records if total_records > 0 else 1.0
        
        # Weighted average (you can adjust weights as needed)
        weights = {
            'completeness': 0.3,
            'uniqueness': 0.2, 
            'validity': 0.3,
            'consistency': 0.2
        }
        
        quality_score = (
            completeness * weights['completeness'] +
            uniqueness * weights['uniqueness'] +
            validity * weights['validity'] +
            consistency * weights['consistency']
        ) * 100
        
        return round(quality_score, 2)
    
    @staticmethod
    def suggest_data_improvements(validation_issues: List[Dict[str, Any]]) -> List[str]:
        """Suggest improvements based on validation issues"""
        suggestions = []
        
        issue_types = [issue['issue_type'] for issue in validation_issues]
        
        if 'whitespace_issues' in issue_types:
            suggestions.append("🔧 Trim leading/trailing spaces from text fields")
        
        if 'case_inconsistency' in issue_types:
            suggestions.append("🔧 Standardize text case (upper/lower) for categorical fields")
        
        if 'mixed_data_types' in issue_types:
            suggestions.append("🔧 Convert mixed data types to consistent format")
        
        if 'unique_constraint_violation' in issue_types:
            suggestions.append("🔧 Remove or resolve duplicate records")
        
        if 'referential_integrity_violation' in issue_types:
            suggestions.append("🔧 Fix orphaned records or add missing parent records")
        
        if any(issue['severity'] == 'HIGH' for issue in validation_issues):
            suggestions.append("⚠️ Priority: Address HIGH severity issues first")
        
        if not suggestions:
            suggestions.append("✅ Data quality looks good! No major issues detected.")
        
        return suggestions