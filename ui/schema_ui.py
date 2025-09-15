import streamlit as st
import pandas as pd
import json
import numpy as np
from datetime import datetime
from services.schema_service import SchemaService
from services.profiler_service import ProfilerService
from services.project_service import ProjectService
from utils.file_utils import FileUtils
from ui.profiler_ui import ProfilerUI
from models.schema import TableSchema
from models.project import ProjectFile

class SchemaUI:
    """UI components for schema management"""
    
    def __init__(self):
        self.schema_service = SchemaService()
        self.profiler_service = ProfilerService()
        self.project_service = ProjectService()
        self.file_utils = FileUtils()
        self.profiler_ui = ProfilerUI()
    
    def render_schema_management(self, project_config):
        """Render schema management interface"""
        # No title here since main.py handles it
        
        # Initialize session state for schemas
        if 'schemas' not in st.session_state:
            st.session_state.schemas = {}
        if 'sample_data' not in st.session_state:
            st.session_state.sample_data = {}
        if 'profiler_results' not in st.session_state:
            st.session_state.profiler_results = {}
        if 'replacing_files' not in st.session_state:
            st.session_state.replacing_files = {}
        
        # Create main tabs: Source Schemas and Target Schema
        tab1, tab2 = st.tabs(["Source Schemas", "Target Schema"])
        
        with tab1:
            self._render_source_schemas_tab(project_config)
        
        with tab2:
            self._render_target_schema_tab(project_config)
    
    def _render_source_schemas_tab(self, project_config):
        """Render all source schemas in one tab, vertically stacked"""
        st.subheader("Source Schemas")
        
        if not project_config.input_schema_names:
            st.info("No input schemas configured for this project.")
            return
        
        # Render each source schema as a separate section
        for i, schema_name in enumerate(project_config.input_schema_names):
            # Add separator between schemas (except for the first one)
            if i > 0:
                st.markdown("---")
            
            # Schema section header
            st.markdown(f"### {schema_name}")
            
            # Render the schema content
            self._render_schema_content(schema_name, project_config, is_target=False)
    
    def _render_target_schema_tab(self, project_config):
        """Render target schema in its own tab"""
        st.subheader("Target Schema")
        
        if not project_config.target_schema_name:
            st.info("No target schema configured for this project.")
            return
        
        # Render the target schema content
        self._render_schema_content(project_config.target_schema_name, project_config, is_target=True)
    
    def _render_schema_content(self, schema_name: str, project_config, is_target: bool = False):
        """Render the content for a single schema (works for both source and target)"""
        # Check for existing files
        existing_schema_file = project_config.get_file(schema_name, 'schema')
        existing_sample_file = project_config.get_file(schema_name, 'sample')
        
        # Check if user is in "replacing" mode
        replacing_schema = st.session_state.replacing_files.get(f"schema_{schema_name}", False)
        replacing_sample = st.session_state.replacing_files.get(f"sample_{schema_name}", False)
        
        # Schema definition section
        st.markdown("#### Schema Definition")
        
        # Show existing schema file info if available and not replacing
        if existing_schema_file and not replacing_schema:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info(f"**Loaded:** {existing_schema_file.original_filename}")
            with col2:
                if st.button(f"Replace Schema", key=f"replace_schema_{schema_name}"):
                    # Set replacing mode
                    st.session_state.replacing_files[f"schema_{schema_name}"] = True
                    st.rerun()
            with col3:
                file_size_kb = existing_schema_file.file_size / 1024
                st.caption(f"Size: {file_size_kb:.1f} KB")
            
            # Auto-load existing schema into session state if not already loaded
            if f"schema_{schema_name}" not in st.session_state.schemas:
                df = self.project_service.load_project_file(project_config.name, existing_schema_file)
                if df is not None:
                    schema = self.schema_service.parse_schema_from_csv(df)
                    schema.name = schema_name
                    st.session_state.schemas[f"schema_{schema_name}"] = schema
        
        # Schema file uploader (show if no existing file OR user is replacing)
        if not existing_schema_file or replacing_schema:
            if replacing_schema:
                st.warning("Replace mode active. Upload a new schema file:")
                col1, col2 = st.columns([1, 1])
                with col2:
                    if st.button(f"Cancel Replace", key=f"cancel_schema_{schema_name}"):
                        st.session_state.replacing_files[f"schema_{schema_name}"] = False
                        st.rerun()
            
            schema_file = st.file_uploader(
                f"Upload Schema Definition for {schema_name}",
                type=['csv'],
                key=f"schema_upload_{schema_name}_{replacing_schema}",
                help="CSV file with columns: field_name, data_type, and optional metadata columns"
            )
            
            if schema_file:
                # Show file preview before processing
                with st.expander("File Preview", expanded=True):
                    temp_path = self.file_utils.save_uploaded_file(schema_file)
                    if temp_path:
                        preview_df = self.file_utils.preview_file_content(temp_path, max_rows=5)
                        if preview_df is not None:
                            st.write(f"**File preview (first 5 rows):**")
                            st.dataframe(preview_df, use_container_width=True)
                
                # Process file button
                if st.button(f"Process {schema_file.name}", key=f"process_schema_{schema_name}_{replacing_schema}"):
                    # If replacing, remove old file first
                    if replacing_schema and existing_schema_file:
                        project_config.remove_file(schema_name, 'schema')
                        if f"schema_{schema_name}" in st.session_state.schemas:
                            del st.session_state.schemas[f"schema_{schema_name}"]
                    
                    # Save the new uploaded file
                    project_file = self.project_service.save_uploaded_file(
                        project_config.name, schema_name, 'schema', schema_file, schema_file.name
                    )
                    
                    if project_file:
                        # Add to project config
                        project_config.add_file(project_file)
                        self.project_service.save_project(project_config)
                        
                        # Process the file with cleaning
                        df = self.file_utils.read_csv_file(
                            self.project_service.get_project_file_path(project_config.name, project_file),
                            clean_data=True
                        )
                        
                        if df is not None and len(df) > 0:
                            is_valid, message = self.file_utils.validate_schema_csv(df)
                            if is_valid:
                                schema = self.schema_service.parse_schema_from_csv(df)
                                schema.name = schema_name
                                st.session_state.schemas[f"schema_{schema_name}"] = schema
                                
                                # Clear replacing mode
                                st.session_state.replacing_files[f"schema_{schema_name}"] = False
                                
                                st.success(f"Schema definition loaded and saved successfully! {message}")
                                st.rerun()
                            else:
                                st.error(f"Validation failed: {message}")
                        else:
                            st.error("No valid data found in the file after cleaning")
                    else:
                        st.error("Failed to save schema file")
        
        # Display schema if loaded
        if f"schema_{schema_name}" in st.session_state.schemas:
            schema = st.session_state.schemas[f"schema_{schema_name}"]
            self._display_schema_details(schema)
        
        # Sample data section
        st.markdown("#### Sample Data (Optional)")
        
        # More flexible check for schema availability
        schema_available = (f"schema_{schema_name}" in st.session_state.schemas) or existing_schema_file
        
        # Show existing sample file info if available and not replacing
        if existing_sample_file and not replacing_sample:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info(f"**Loaded:** {existing_sample_file.original_filename}")
            with col2:
                if st.button(f"Replace Sample", key=f"replace_sample_{schema_name}"):
                    # Set replacing mode
                    st.session_state.replacing_files[f"sample_{schema_name}"] = True
                    st.rerun()
            with col3:
                file_size_kb = existing_sample_file.file_size / 1024
                st.caption(f"Size: {file_size_kb:.1f} KB")
            
            # Auto-load existing sample data into session state if not already loaded
            if f"sample_{schema_name}" not in st.session_state.sample_data:
                sample_df = self.project_service.load_project_file(project_config.name, existing_sample_file)
                if sample_df is not None:
                    st.session_state.sample_data[f"sample_{schema_name}"] = sample_df
        
        # Sample file uploader - show if schema is available and (no existing file OR replacing)
        if schema_available and (not existing_sample_file or replacing_sample):
            if replacing_sample:
                st.warning("Replace mode active. Upload a new sample data file:")
                col1, col2 = st.columns([1, 1])
                with col2:
                    if st.button(f"Cancel Replace", key=f"cancel_sample_{schema_name}"):
                        st.session_state.replacing_files[f"sample_{schema_name}"] = False
                        st.rerun()
            
            sample_file = st.file_uploader(
                f"Upload Sample Data for {schema_name}",
                type=['csv'],
                key=f"sample_upload_{schema_name}_{replacing_sample}",
                help="CSV file containing sample data that matches the schema definition"
            )
            
            if sample_file:
                # Show file preview and quality summary
                with st.expander("File Preview & Quality Check", expanded=True):
                    temp_path = self.file_utils.save_uploaded_file(sample_file)
                    if temp_path:
                        # Get quality summary before cleaning
                        raw_df = pd.read_csv(temp_path)
                        quality_summary = self.file_utils.get_data_quality_summary(raw_df)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**File Statistics:**")
                            st.write(f"- Total rows: {quality_summary['total_rows']}")
                            st.write(f"- Total columns: {quality_summary['total_columns']}")
                            st.write(f"- Completely empty rows: {quality_summary['completely_null_rows']}")
                            st.write(f"- Rows with nulls: {quality_summary['rows_with_nulls']}")
                            st.write(f"- Null percentage: {quality_summary['null_percentage']:.1f}%")
                        
                        with col2:
                            preview_df = self.file_utils.preview_file_content(temp_path, max_rows=5)
                            if preview_df is not None:
                                st.write("**Data Preview:**")
                                st.dataframe(preview_df, use_container_width=True)
                
                # Process file button
                if st.button(f"Process {sample_file.name}", key=f"process_sample_{schema_name}_{replacing_sample}"):
                    # Make sure schema is loaded into session state
                    if f"schema_{schema_name}" not in st.session_state.schemas and existing_schema_file:
                        df = self.project_service.load_project_file(project_config.name, existing_schema_file)
                        if df is not None:
                            schema = self.schema_service.parse_schema_from_csv(df)
                            schema.name = schema_name
                            st.session_state.schemas[f"schema_{schema_name}"] = schema
                    
                    # If replacing, remove old file first
                    if replacing_sample and existing_sample_file:
                        project_config.remove_file(schema_name, 'sample')
                        if f"sample_{schema_name}" in st.session_state.sample_data:
                            del st.session_state.sample_data[f"sample_{schema_name}"]
                    
                    # Save the new uploaded file
                    project_file = self.project_service.save_uploaded_file(
                        project_config.name, schema_name, 'sample', sample_file, sample_file.name
                    )
                    
                    if project_file:
                        # Add to project config
                        project_config.add_file(project_file)
                        self.project_service.save_project(project_config)
                        
                        # Process the file with cleaning
                        sample_df = self.file_utils.read_csv_file(
                            self.project_service.get_project_file_path(project_config.name, project_file),
                            clean_data=True
                        )
                        
                        if sample_df is not None and len(sample_df) > 0:
                            st.session_state.sample_data[f"sample_{schema_name}"] = sample_df
                            
                            # Clear replacing mode
                            st.session_state.replacing_files[f"sample_{schema_name}"] = False
                            
                            st.success(f"Sample data loaded and saved successfully! Using {len(sample_df)} valid records.")
                            st.rerun()
                        else:
                            st.error("No valid data found in the file after cleaning")
                    else:
                        st.error("Failed to save sample file")
        elif not schema_available:
            st.info("Upload a schema definition first before adding sample data.")
        
        # Process sample data if available
        if f"sample_{schema_name}" in st.session_state.sample_data and f"schema_{schema_name}" in st.session_state.schemas:
            sample_df = st.session_state.sample_data[f"sample_{schema_name}"]
            schema = st.session_state.schemas[f"schema_{schema_name}"]
            
            # Validate sample data against schema
            validation_issues = self.schema_service.validate_sample_data(schema, sample_df)
            
            if validation_issues:
                st.warning("Validation issues found:")
                for issue in validation_issues:
                    st.write(f"- {issue['message']}")
            else:
                st.success("Sample data validates successfully against schema!")
            
            # Display sample data preview
            self._display_sample_data(sample_df, schema_name)
            
            # Data profiling section
            st.markdown("#### Data Profiling")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                profile_button = st.button(
                    f"Profile Data for {schema_name}", 
                    key=f"profile_{schema_name}",
                    help="Analyze data quality and generate comprehensive statistics"
                )
            
            with col2:
                if f"profile_{schema_name}" in st.session_state.profiler_results:
                    # Single working export button
                    if st.button(f"Download Report", key=f"download_{schema_name}", help="Download complete profiling report as JSON"):
                        self._generate_simple_export(st.session_state.profiler_results[f"profile_{schema_name}"], schema_name)
            
            # Generate profiler results
            if profile_button:
                with st.spinner("Profiling data..."):
                    profiler_results = self.profiler_service.profile_data(schema, sample_df)
                    st.session_state.profiler_results[f"profile_{schema_name}"] = profiler_results
                    st.success("Data profiling completed!")
                    st.rerun()
            
            # Display profiler results using ProfilerUI
            if f"profile_{schema_name}" in st.session_state.profiler_results:
                profiler_results = st.session_state.profiler_results[f"profile_{schema_name}"]
                
                # Render profiler dashboard
                self.profiler_ui.render_profiler_dashboard(profiler_results, schema_name)
    
    def _generate_simple_export(self, profiler_results, schema_name: str):
        """Generate a simple, working export"""
        try:
            # Convert profiler results to simple dictionary
            export_data = {
                "schema_name": schema_name,
                "export_timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_fields": profiler_results.schema_summary.get('total_fields_profiled', 0),
                    "quality_issues": profiler_results.schema_summary.get('total_quality_issues', 0),
                    "quality_score": profiler_results.schema_summary.get('overall_quality_score', 0)
                },
                "field_statistics": [],
                "quality_issues": profiler_results.quality_issues
            }
            
            # Add field statistics
            for field_profile in profiler_results.field_profiles.values():
                stats = field_profile.statistics
                field_data = {
                    "field_name": field_profile.field_name,
                    "data_type": stats.get('DATA_TYPE', 'Unknown'),
                    "records": int(stats.get('RECORDS', 0)),
                    "null_count": int(stats.get('NULL_COUNT', 0)),
                    "population_percentage": float(stats.get('POPULATION_PERCENTAGE', 0)),
                    "distinct_count": int(stats.get('DISTINCT_COUNT', 0))
                }
                
                # Add type-specific stats
                if stats.get('DATA_TYPE') == 'numeric':
                    if stats.get('MIN_VALUE') is not None:
                        field_data["min_value"] = float(stats['MIN_VALUE'])
                    if stats.get('MAX_VALUE') is not None:
                        field_data["max_value"] = float(stats['MAX_VALUE'])
                    if stats.get('MEAN_VALUE') is not None:
                        field_data["mean_value"] = float(stats['MEAN_VALUE'])
                else:
                    if stats.get('MIN_LENGTH') is not None:
                        field_data["min_length"] = int(stats['MIN_LENGTH'])
                    if stats.get('MAX_LENGTH') is not None:
                        field_data["max_length"] = int(stats['MAX_LENGTH'])
                    if stats.get('AVG_LENGTH') is not None:
                        field_data["avg_length"] = float(stats['AVG_LENGTH'])
                
                # Add most common values (convert to simple format)
                if 'MOST_COMMON_VALUES' in stats and stats['MOST_COMMON_VALUES']:
                    field_data["top_values"] = []
                    for value, count in list(stats['MOST_COMMON_VALUES'].items())[:5]:
                        field_data["top_values"].append({
                            "value": str(value),
                            "count": int(count)
                        })
                
                export_data["field_statistics"].append(field_data)
            
            # Convert to JSON string
            json_str = json.dumps(export_data, indent=2)
            
            # Create download button
            st.download_button(
                label="Download JSON Report",
                data=json_str,
                file_name=f"{schema_name}_profiling_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            st.success("Report ready for download!")
            
        except Exception as e:
            st.error(f"Export failed: {str(e)}")
            st.write("Error details:", str(e))
    
    def _display_schema_details(self, schema: TableSchema):
        """Display schema definition details"""
        with st.expander("Schema Fields Details", expanded=True):
            # Create DataFrame for display
            schema_data = []
            for field in schema.fields:
                schema_data.append({
                    'Field Name': field.field_name,
                    'Data Type': field.data_type,
                    'Length': field.length if field.length else '',
                    'Nullable': 'Yes' if field.nullable else 'No',
                    'Primary Key': 'Yes' if field.primary_key else 'No',
                    'Foreign Key': field.foreign_key_ref if field.foreign_key_ref else '',
                    'Description': field.description,
                    'Example Values': field.example_values,
                    'Tags': field.tags
                })
            
            if schema_data:
                schema_df = pd.DataFrame(schema_data)
                st.dataframe(schema_df, use_container_width=True, height=min(400, len(schema_data) * 35 + 100))
                
                # Schema summary
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Fields", len(schema.fields))
                with col2:
                    primary_keys = sum(1 for field in schema.fields if field.primary_key)
                    st.metric("Primary Keys", primary_keys)
                with col3:
                    nullable_fields = sum(1 for field in schema.fields if field.nullable)
                    st.metric("Nullable Fields", nullable_fields)
                with col4:
                    foreign_keys = sum(1 for field in schema.fields if field.foreign_key_ref)
                    st.metric("Foreign Keys", foreign_keys)
    
    def _display_sample_data(self, sample_df: pd.DataFrame, schema_name: str):
        """Display sample data preview"""
        st.markdown("##### Sample Data Preview")
        
        # Data overview metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Valid Records", f"{len(sample_df):,}")
        with col2:
            st.metric("Columns", len(sample_df.columns))
        with col3:
            memory_usage = sample_df.memory_usage(deep=True).sum() / 1024  # KB
            st.metric("Memory", f"{memory_usage:.1f} KB")
        with col4:
            duplicates = sample_df.duplicated().sum()
            st.metric("Duplicates", duplicates)
        
        # Sample data table
        with st.expander("Data Sample (First 10 Rows)", expanded=True):
            st.dataframe(
                sample_df.head(10), 
                use_container_width=True,
                height=min(400, 10 * 35 + 100)
            )
        
        # Basic statistics
        with st.expander("Basic Statistics", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Data Types**")
                dtype_df = pd.DataFrame({
                    'Column': sample_df.dtypes.index,
                    'Data Type': sample_df.dtypes.values
                })
                st.dataframe(dtype_df, use_container_width=True)
            
            with col2:
                st.markdown("**Missing Values**")
                missing_df = pd.DataFrame({
                    'Column': sample_df.columns,
                    'Missing Count': sample_df.isnull().sum().values,
                    'Missing %': (sample_df.isnull().sum() / len(sample_df) * 100).round(1).values
                })
                missing_df = missing_df[missing_df['Missing Count'] > 0]  # Only show columns with missing values
                
                if len(missing_df) > 0:
                    st.dataframe(missing_df, use_container_width=True)
                else:
                    st.success("No missing values detected!")
        
        # Column selection for detailed view
        with st.expander("Column Detail View", expanded=False):
            selected_column = st.selectbox(
                "Select column to examine:",
                sample_df.columns,
                key=f"column_select_{schema_name}"
            )
            
            if selected_column:
                col_data = sample_df[selected_column]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**{selected_column} - Statistics**")
                    st.write(f"• **Count:** {len(col_data):,}")
                    st.write(f"• **Unique:** {col_data.nunique():,}")
                    st.write(f"• **Missing:** {col_data.isnull().sum():,}")
                    
                    if pd.api.types.is_numeric_dtype(col_data):
                        st.write(f"• **Mean:** {col_data.mean():.2f}")
                        st.write(f"• **Min:** {col_data.min()}")
                        st.write(f"• **Max:** {col_data.max()}")
                
                with col2:
                    st.markdown(f"**{selected_column} - Top Values**")
                    top_values = col_data.value_counts().head(8)
                    for value, count in top_values.items():
                        percentage = (count / len(col_data)) * 100
                        st.write(f"• `{value}`: {count:,} ({percentage:.1f}%)")