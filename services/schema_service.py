import pandas as pd
from typing import List, Dict, Tuple, Any
from models.schema import TableSchema, FieldSchema

class SchemaService:
    """Service for schema management and validation"""
    
    @staticmethod
    def parse_schema_from_csv(df: pd.DataFrame) -> TableSchema:
        """Parse schema definition from CSV DataFrame"""
        schema = TableSchema()
        
        for _, row in df.iterrows():
            # Handle required fields
            field_name = str(row.get('field_name', '')).strip()
            data_type = str(row.get('data_type', '')).strip()
            
            # Handle optional fields with sensible defaults
            description = str(row.get('description', '')).strip()
            if not description:
                # Generate description from field name if not provided
                description = field_name.replace('_', ' ').title()
            
            field = FieldSchema(
                field_name=field_name,
                description=description,
                data_type=data_type,
                length=int(row['length']) if pd.notna(row.get('length')) else None,
                nullable=str(row.get('nullable', 'Y')).upper() == 'Y',
                primary_key=str(row.get('primary_key', 'N')).upper() == 'Y',
                foreign_key_ref=str(row.get('foreign_key_ref', '')).strip(),
                example_values=str(row.get('example_values', '')).strip(),
                tags=str(row.get('tags', '')).strip()
            )
            schema.fields.append(field)
        
        return schema
    
    @staticmethod
    def validate_sample_data(schema: TableSchema, sample_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Validate sample data against schema definition"""
        validation_issues = []
        
        # Check if all schema fields exist in sample data
        schema_fields = {field.field_name for field in schema.fields}
        sample_fields = set(sample_df.columns)
        
        missing_fields = schema_fields - sample_fields
        extra_fields = sample_fields - schema_fields
        
        if missing_fields:
            validation_issues.append({
                'type': 'missing_fields',
                'message': f"Missing fields in sample data: {', '.join(missing_fields)}"
            })
        
        if extra_fields:
            validation_issues.append({
                'type': 'extra_fields',
                'message': f"Extra fields in sample data: {', '.join(extra_fields)}"
            })
        
        # Validate data types and constraints for existing fields
        for field in schema.fields:
            if field.field_name not in sample_df.columns:
                continue
            
            column_data = sample_df[field.field_name]
            
            # Check nullable constraint
            if not field.nullable and column_data.isnull().any():
                validation_issues.append({
                    'type': 'nullable_violation',
                    'field': field.field_name,
                    'message': f"Field '{field.field_name}' cannot be null but contains null values"
                })
            
            # Check data type compatibility
            if field.data_type.lower() in ['int', 'integer', 'number']:
                non_null_data = column_data.dropna()
                if len(non_null_data) > 0 and not pd.api.types.is_numeric_dtype(non_null_data):
                    validation_issues.append({
                        'type': 'data_type_mismatch',
                        'field': field.field_name,
                        'message': f"Field '{field.field_name}' should be numeric but contains non-numeric values"
                    })
            
            # Check length constraints for string fields
            if field.length and field.data_type.lower() in ['string', 'varchar', 'text']:
                max_length = column_data.astype(str).str.len().max()
                if max_length > field.length:
                    validation_issues.append({
                        'type': 'length_violation',
                        'field': field.field_name,
                        'message': f"Field '{field.field_name}' has values longer than specified length {field.length}"
                    })
        
        return validation_issues
    
    @staticmethod
    def get_supported_data_types() -> List[str]:
        """Get list of supported data types"""
        return [
            'string', 'varchar', 'text', 'char',
            'int', 'integer', 'number', 'numeric',
            'float', 'decimal', 'double',
            'date', 'datetime', 'timestamp',
            'boolean', 'bool',
            'email', 'phone', 'url',
            'json', 'array'
        ]
    
    @staticmethod
    def validate_data_type(data_type: str) -> bool:
        """Validate if data type is supported"""
        supported_types = SchemaService.get_supported_data_types()
        return data_type.lower() in [t.lower() for t in supported_types]