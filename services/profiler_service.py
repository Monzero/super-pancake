import pandas as pd
import numpy as np
from typing import Dict, Any, List
from models.profiler import FieldProfile, TableProfile, ProfilerResults
from models.schema import TableSchema

class ProfilerService:
    """Service for data profiling and analysis"""
    
    @staticmethod
    def profile_data(schema: TableSchema, sample_df: pd.DataFrame) -> ProfilerResults:
        """Profile sample data and generate comprehensive statistics"""
        results = ProfilerResults()
        
        # Profile each field
        for field in schema.fields:
            if field.field_name in sample_df.columns:
                field_profile = ProfilerService._profile_field(field, sample_df[field.field_name])
                results.field_profiles[field.id] = field_profile
        
        # Profile table
        table_profile = ProfilerService._profile_table(schema, sample_df)
        results.table_profiles[schema.id] = table_profile
        
        # Identify quality issues
        results.quality_issues = ProfilerService._identify_quality_issues(schema, sample_df)
        
        # Generate schema summary
        results.schema_summary = ProfilerService._generate_schema_summary(results)
        
        return results
    
    @staticmethod
    def _profile_field(field, column_data: pd.Series) -> FieldProfile:
        """Profile individual field"""
        statistics = {}
        
        # Basic statistics
        statistics['RECORDS'] = len(column_data)
        statistics['NULL_COUNT'] = column_data.isnull().sum()
        statistics['POPULATION_PERCENTAGE'] = ((len(column_data) - statistics['NULL_COUNT']) / len(column_data) * 100) if len(column_data) > 0 else 0
        statistics['DISTINCT_COUNT'] = column_data.nunique()
        
        # Handle non-null data
        non_null_data = column_data.dropna()
        
        if len(non_null_data) > 0:
            # Data type detection
            if pd.api.types.is_numeric_dtype(non_null_data):
                statistics['DATA_TYPE'] = 'numeric'
                statistics['MIN_VALUE'] = float(non_null_data.min())
                statistics['MAX_VALUE'] = float(non_null_data.max())
                statistics['MEAN_VALUE'] = float(non_null_data.mean())
                statistics['MEDIAN_VALUE'] = float(non_null_data.median())
            else:
                statistics['DATA_TYPE'] = 'categorical'
                # String length analysis
                str_lengths = non_null_data.astype(str).str.len()
                statistics['MIN_LENGTH'] = int(str_lengths.min())
                statistics['MAX_LENGTH'] = int(str_lengths.max())
                statistics['AVG_LENGTH'] = float(str_lengths.mean())
                
                # Leading/trailing spaces count
                str_data = non_null_data.astype(str)
                statistics['LEADING_TRAILING_SPACES_COUNT'] = (
                    (str_data != str_data.str.strip()).sum()
                )
            
            # Most common values
            value_counts = non_null_data.value_counts().head(5)
            statistics['MOST_COMMON_VALUES'] = value_counts.to_dict()
        
        return FieldProfile(
            field_id=field.id,
            field_name=field.field_name,
            statistics=statistics
        )
    
    @staticmethod
    def _profile_table(schema: TableSchema, sample_df: pd.DataFrame) -> TableProfile:
        """Profile entire table"""
        statistics = {
            'TOTAL_RECORDS': len(sample_df),
            'TOTAL_FIELDS': len(sample_df.columns),
            'SCHEMA_FIELDS': len(schema.fields),
            'MEMORY_USAGE_KB': sample_df.memory_usage(deep=True).sum() / 1024,
            'DUPLICATE_ROWS': sample_df.duplicated().sum()
        }
        
        # Primary key analysis
        primary_key_fields = [f.field_name for f in schema.fields if f.primary_key]
        if primary_key_fields:
            pk_data = sample_df[primary_key_fields] if all(f in sample_df.columns for f in primary_key_fields) else None
            if pk_data is not None:
                statistics['PRIMARY_KEY_VIOLATIONS'] = pk_data.duplicated().sum()
        
        return TableProfile(
            table_id=schema.id,
            table_name=schema.name,
            statistics=statistics
        )
    
    @staticmethod
    def _identify_quality_issues(schema: TableSchema, sample_df: pd.DataFrame) -> List[Dict]:
        """Identify data quality issues"""
        issues = []
        
        for field in schema.fields:
            if field.field_name not in sample_df.columns:
                continue
            
            column_data = sample_df[field.field_name]
            
            # Check for high null percentage
            null_percentage = (column_data.isnull().sum() / len(column_data)) * 100
            if null_percentage > 50:
                issues.append({
                    'field': field.field_name,
                    'issue_type': 'HIGH_NULL_PERCENTAGE',
                    'severity': 'HIGH',
                    'description': f"Field has {null_percentage:.1f}% null values"
                })
            
            # Check for low cardinality in non-categorical fields
            if field.data_type.lower() not in ['categorical', 'enum'] and column_data.nunique() < 5:
                issues.append({
                    'field': field.field_name,
                    'issue_type': 'LOW_CARDINALITY',
                    'severity': 'MEDIUM',
                    'description': f"Field has only {column_data.nunique()} distinct values"
                })
            
            # Check for data type mismatches
            if field.data_type.lower() in ['int', 'integer', 'number']:
                non_null_data = column_data.dropna()
                if len(non_null_data) > 0 and not pd.api.types.is_numeric_dtype(non_null_data):
                    issues.append({
                        'field': field.field_name,
                        'issue_type': 'DATA_TYPE_MISMATCH',
                        'severity': 'HIGH',
                        'description': f"Expected numeric data but found non-numeric values"
                    })
        
        return issues
    
    @staticmethod
    def _generate_schema_summary(results: ProfilerResults) -> Dict[str, Any]:
        """Generate overall schema summary"""
        total_fields = len(results.field_profiles)
        total_issues = len(results.quality_issues)
        
        high_severity_issues = sum(1 for issue in results.quality_issues if issue.get('severity') == 'HIGH')
        
        return {
            'total_fields_profiled': total_fields,
            'total_quality_issues': total_issues,
            'high_severity_issues': high_severity_issues,
            'overall_quality_score': max(0, 100 - (high_severity_issues * 20) - ((total_issues - high_severity_issues) * 5))
        }