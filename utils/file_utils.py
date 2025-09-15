import pandas as pd
import streamlit as st
from typing import Optional, Tuple
import tempfile
import os

class FileUtils:
    """Utility functions for file handling"""
    
    @staticmethod
    def save_uploaded_file(uploaded_file) -> Optional[str]:
        """Save uploaded file to temporary location"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                return tmp_file.name
        except Exception as e:
            st.error(f"Error saving file: {e}")
            return None
    
    @staticmethod
    def read_csv_file(file_path: str, clean_data: bool = True) -> Optional[pd.DataFrame]:
        """Read CSV file and return DataFrame with optional data cleaning"""
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            if clean_data:
                df = FileUtils.clean_dataframe(df)
            
            return df
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")
            return None
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean DataFrame by removing empty/null rows and showing statistics"""
        original_rows = len(df)
        
        # Remove rows where ALL values are null
        df_cleaned = df.dropna(how='all')
        
        # Remove rows where all values are empty strings
        df_cleaned = df_cleaned[~(df_cleaned == '').all(axis=1)]
        
        # For schema files, remove rows where required fields are empty
        if 'field_name' in df_cleaned.columns:
            df_cleaned = df_cleaned[df_cleaned['field_name'].notna()]
            df_cleaned = df_cleaned[df_cleaned['field_name'].str.strip() != '']
        
        cleaned_rows = len(df_cleaned)
        removed_rows = original_rows - cleaned_rows
        
        if removed_rows > 0:
            st.info(f"Data cleaned: Removed {removed_rows} empty rows. Using {cleaned_rows} valid records out of {original_rows} total.")
        
        return df_cleaned
    
    @staticmethod
    def validate_schema_csv(df: pd.DataFrame) -> Tuple[bool, str]:
        """Validate if CSV has required schema columns"""
        # Check if DataFrame is empty after cleaning
        if len(df) == 0:
            return False, "No valid data found in CSV file"
        
        # Only require the absolute essentials
        required_columns = ['field_name', 'data_type']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
        
        # Check for empty required fields
        for col in required_columns:
            if df[col].isnull().any() or (df[col] == '').any():
                empty_count = df[col].isnull().sum() + (df[col] == '').sum()
                return False, f"Column '{col}' contains {empty_count} empty values"
        
        return True, f"Schema CSV is valid with {len(df)} field definitions"
    
    @staticmethod
    def get_data_quality_summary(df: pd.DataFrame) -> dict:
        """Get summary of data quality issues"""
        summary = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'empty_rows': 0,
            'completely_null_rows': 0,
            'rows_with_nulls': 0,
            'null_percentage': 0
        }
        
        if len(df) > 0:
            # Count completely empty rows (all nulls or empty strings)
            all_null_mask = df.isnull().all(axis=1)
            all_empty_mask = (df == '').all(axis=1)
            summary['completely_null_rows'] = (all_null_mask | all_empty_mask).sum()
            
            # Count rows with any nulls
            summary['rows_with_nulls'] = df.isnull().any(axis=1).sum()
            
            # Calculate null percentage
            total_cells = df.size
            null_cells = df.isnull().sum().sum()
            summary['null_percentage'] = (null_cells / total_cells * 100) if total_cells > 0 else 0
        
        return summary
    
    @staticmethod
    def preview_file_content(file_path: str, max_rows: int = 10) -> Optional[pd.DataFrame]:
        """Preview file content without full processing"""
        try:
            # Read just a few rows to preview
            df_preview = pd.read_csv(file_path, nrows=max_rows)
            return df_preview
        except Exception as e:
            st.error(f"Error previewing file: {e}")
            return None
    
    @staticmethod
    def get_schema_requirements() -> dict:
        """Get schema requirements information"""
        return {
            'required': {
                'field_name': 'Name of the field/column',
                'data_type': 'Data type (string, number, date, etc.)'
            },
            'optional': {
                'description': 'Human-readable description of the field',
                'length': 'Maximum length for string fields',
                'nullable': 'Whether field can be null (Y/N, defaults to Y)',
                'primary_key': 'Whether field is primary key (Y/N, defaults to N)',
                'foreign_key_ref': 'Reference to foreign key table.field',
                'example_values': 'Sample values separated by |',
                'tags': 'Metadata tags for categorization'
            }
        }
    
    @staticmethod
    def generate_sample_schema_csv() -> str:
        """Generate a sample schema CSV content"""
        return """field_name,data_type,description,nullable,primary_key,example_values
user_id,string,Unique user identifier,N,Y,USR001|USR002
first_name,string,User's first name,N,N,John|Jane
last_name,string,User's last name,N,N,Doe|Smith
email,string,User's email address,Y,N,john@email.com|jane@email.com
age,number,User's age in years,Y,N,25|30|35
registration_date,date,Date user registered,N,N,2024-01-15|2024-02-20"""