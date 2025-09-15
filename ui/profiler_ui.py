import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import numpy as np
from typing import Dict, List, Any
from models.profiler import ProfilerResults, FieldProfile, TableProfile
from utils.validation_utils import ValidationUtils

class ProfilerUI:
    """UI components for displaying data profiler results"""
    
    def __init__(self):
        self.validation_utils = ValidationUtils()
    
    def render_profiler_dashboard(self, profiler_results: ProfilerResults, schema_name: str):
        """Render complete profiler dashboard"""
        st.markdown(f"#### Data Profiling Dashboard - {schema_name}")
        
        # Render overview metrics
        self._render_overview_metrics(profiler_results)
        
        # Render quality issues summary
        if profiler_results.quality_issues:
            self._render_quality_issues_summary(profiler_results.quality_issues)
        
        # Render detailed field profiles
        self._render_field_profiles(profiler_results.field_profiles)
        
        # Render table profile details
        self._render_table_profile(profiler_results.table_profiles)
        
        # Render improvement suggestions
        self._render_improvement_suggestions(profiler_results.quality_issues)
    
    def _render_overview_metrics(self, profiler_results: ProfilerResults):
        """Render overview metrics cards"""
        summary = profiler_results.schema_summary
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Fields Profiled", 
                summary.get('total_fields_profiled', 0)
            )
        
        with col2:
            issues_count = summary.get('total_quality_issues', 0)
            st.metric(
                "Quality Issues", 
                issues_count,
                delta=f"-{issues_count}" if issues_count > 0 else None,
                delta_color="inverse"
            )
        
        with col3:
            high_issues = summary.get('high_severity_issues', 0)
            st.metric(
                "High Severity", 
                high_issues,
                delta=f"-{high_issues}" if high_issues > 0 else None,
                delta_color="inverse"
            )
        
        with col4:
            quality_score = summary.get('overall_quality_score', 0)
            color = "normal" if quality_score >= 80 else "inverse"
            st.metric(
                "Quality Score", 
                f"{quality_score:.1f}%",
                delta=f"{quality_score - 100:.1f}%" if quality_score < 100 else None,
                delta_color=color
            )
    
    def _render_quality_issues_summary(self, quality_issues: List[Dict]):
        """Render quality issues summary with visualizations"""
        st.markdown("##### Quality Issues Overview")
        
        if not quality_issues:
            st.success("No quality issues detected!")
            return
        
        # Group issues by severity
        severity_counts = {}
        issue_type_counts = {}
        
        for issue in quality_issues:
            severity = issue.get('severity', 'UNKNOWN')
            issue_type = issue.get('issue_type', 'UNKNOWN')
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            issue_type_counts[issue_type] = issue_type_counts.get(issue_type, 0) + 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Severity distribution pie chart
            if severity_counts:
                fig_severity = px.pie(
                    values=list(severity_counts.values()),
                    names=list(severity_counts.keys()),
                    title="Issues by Severity",
                    color_discrete_map={
                        'HIGH': '#ff4b4b',
                        'MEDIUM': '#ffa500', 
                        'LOW': '#ffeb3b'
                    }
                )
                fig_severity.update_layout(height=300)
                st.plotly_chart(fig_severity, use_container_width=True)
        
        with col2:
            # Issue types bar chart
            if issue_type_counts:
                fig_types = px.bar(
                    x=list(issue_type_counts.values()),
                    y=list(issue_type_counts.keys()),
                    orientation='h',
                    title="Issues by Type",
                    color=list(issue_type_counts.values()),
                    color_continuous_scale='Reds'
                )
                fig_types.update_layout(height=300)
                st.plotly_chart(fig_types, use_container_width=True)
        
        # Detailed issues list
        with st.expander("Detailed Issues List", expanded=False):
            for i, issue in enumerate(quality_issues):
                severity_icon = {
                    "HIGH": "HIGH", 
                    "MEDIUM": "MEDIUM", 
                    "LOW": "LOW"
                }.get(issue.get('severity'), 'UNKNOWN')
                
                st.write(f"**[{severity_icon}] {issue.get('field', 'General')}**: {issue.get('description', 'No description')}")
    
    def _render_field_profiles(self, field_profiles: Dict[str, FieldProfile]):
        """Render detailed field profiles"""
        if not field_profiles:
            return
        
        st.markdown("##### Field Profiles")
        
        # Create tabs for different profile views
        tab1, tab2, tab3 = st.tabs(["Statistics", "Details", "Distributions"])
        
        with tab1:
            self._render_field_statistics_table(field_profiles)
        
        with tab2:
            self._render_field_details_expandable(field_profiles)
        
        with tab3:
            self._render_field_distributions(field_profiles)
    
    def _render_field_statistics_table(self, field_profiles: Dict[str, FieldProfile]):
        """Render field statistics in tabular format"""
        stats_data = []
        
        for field_profile in field_profiles.values():
            stats = field_profile.statistics
            
            row = {
                'Field Name': field_profile.field_name,
                'Data Type': stats.get('DATA_TYPE', 'Unknown'),
                'Records': stats.get('RECORDS', 0),
                'Null Count': stats.get('NULL_COUNT', 0),
                'Population %': f"{stats.get('POPULATION_PERCENTAGE', 0):.1f}%",
                'Distinct Count': stats.get('DISTINCT_COUNT', 0),
                'Quality': self._calculate_field_quality_score(stats)
            }
            
            # Add type-specific metrics
            if stats.get('DATA_TYPE') == 'numeric':
                row['Min Value'] = stats.get('MIN_VALUE', 'N/A')
                row['Max Value'] = stats.get('MAX_VALUE', 'N/A')
                row['Mean'] = f"{stats.get('MEAN_VALUE', 0):.2f}" if stats.get('MEAN_VALUE') else 'N/A'
            else:
                row['Min Length'] = stats.get('MIN_LENGTH', 'N/A')
                row['Max Length'] = stats.get('MAX_LENGTH', 'N/A')
                row['Avg Length'] = f"{stats.get('AVG_LENGTH', 0):.1f}" if stats.get('AVG_LENGTH') else 'N/A'
            
            stats_data.append(row)
        
        if stats_data:
            df = pd.DataFrame(stats_data)
            st.dataframe(df, use_container_width=True)
    
    def _render_field_details_expandable(self, field_profiles: Dict[str, FieldProfile]):
        """Render field details in expandable sections"""
        for field_profile in field_profiles.values():
            with st.expander(f"Field: {field_profile.field_name}", expanded=False):
                self._render_single_field_profile(field_profile)
    
    def _render_single_field_profile(self, field_profile: FieldProfile):
        """Render detailed profile for a single field"""
        stats = field_profile.statistics
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Basic Statistics**")
            st.write(f"Data Type: {stats.get('DATA_TYPE', 'Unknown')}")
            st.write(f"Total Records: {stats.get('RECORDS', 0):,}")
            st.write(f"Null Count: {stats.get('NULL_COUNT', 0):,}")
            st.write(f"Population: {stats.get('POPULATION_PERCENTAGE', 0):.1f}%")
            st.write(f"Distinct Values: {stats.get('DISTINCT_COUNT', 0):,}")
            
            # Quality score
            quality_score = self._calculate_field_quality_score(stats)
            st.metric("Quality Score", f"{quality_score:.1f}%")
        
        with col2:
            st.markdown("**Value Analysis**")
            
            # Type-specific statistics
            if stats.get('DATA_TYPE') == 'numeric':
                st.write(f"Min Value: {stats.get('MIN_VALUE', 'N/A')}")
                st.write(f"Mean Value: {stats.get('MEAN_VALUE', 'N/A'):.2f}" if stats.get('MEAN_VALUE') else "N/A")
                st.write(f"Median Value: {stats.get('MEDIAN_VALUE', 'N/A'):.2f}" if stats.get('MEDIAN_VALUE') else "N/A")
                st.write(f"Max Value: {stats.get('MAX_VALUE', 'N/A')}")
            else:
                st.write(f"Min Length: {stats.get('MIN_LENGTH', 'N/A')}")
                st.write(f"Avg Length: {stats.get('AVG_LENGTH', 'N/A'):.1f}" if stats.get('AVG_LENGTH') else "N/A")
                st.write(f"Max Length: {stats.get('MAX_LENGTH', 'N/A')}")
                
                if stats.get('LEADING_TRAILING_SPACES_COUNT', 0) > 0:
                    st.warning(f"Warning: {stats['LEADING_TRAILING_SPACES_COUNT']} values with leading/trailing spaces")
        
        # Most common values
        if 'MOST_COMMON_VALUES' in stats and stats['MOST_COMMON_VALUES']:
            st.markdown("**Most Common Values**")
            common_values = stats['MOST_COMMON_VALUES']
            for value, count in list(common_values.items())[:5]:
                percentage = (count / stats.get('RECORDS', 1)) * 100
                st.write(f"  • `{value}`: {count:,} ({percentage:.1f}%)")
    
    def _render_field_distributions(self, field_profiles: Dict[str, FieldProfile]):
        """Render field value distributions"""
        st.markdown("**Value Distributions**")
        
        # Select field for distribution view
        field_names = [fp.field_name for fp in field_profiles.values()]
        selected_field = st.selectbox("Select field to view distribution:", field_names)
        
        if selected_field:
            # Find the selected field profile
            selected_profile = None
            for fp in field_profiles.values():
                if fp.field_name == selected_field:
                    selected_profile = fp
                    break
            
            if selected_profile and 'MOST_COMMON_VALUES' in selected_profile.statistics:
                common_values = selected_profile.statistics['MOST_COMMON_VALUES']
                
                if common_values:
                    # Create bar chart of most common values
                    values = list(common_values.keys())[:10]  # Top 10
                    counts = list(common_values.values())[:10]
                    
                    fig = px.bar(
                        x=counts,
                        y=values,
                        orientation='h',
                        title=f"Top Values Distribution - {selected_field}",
                        labels={'x': 'Count', 'y': 'Value'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No value distribution data available for this field.")
    
    def _render_table_profile(self, table_profiles: Dict[str, TableProfile]):
        """Render table-level profile information"""
        if not table_profiles:
            return
        
        st.markdown("##### Table Profile")
        
        for table_profile in table_profiles.values():
            stats = table_profile.statistics
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Records", f"{stats.get('TOTAL_RECORDS', 0):,}")
                st.metric("Total Fields", stats.get('TOTAL_FIELDS', 0))
            
            with col2:
                st.metric("Schema Fields", stats.get('SCHEMA_FIELDS', 0))
                memory_kb = stats.get('MEMORY_USAGE_KB', 0)
                memory_mb = memory_kb / 1024
                st.metric("Memory Usage", f"{memory_mb:.1f} MB")
            
            with col3:
                duplicate_rows = stats.get('DUPLICATE_ROWS', 0)
                st.metric("Duplicate Rows", duplicate_rows)
                
                if 'PRIMARY_KEY_VIOLATIONS' in stats:
                    pk_violations = stats['PRIMARY_KEY_VIOLATIONS']
                    st.metric("PK Violations", pk_violations)
    
    def _render_improvement_suggestions(self, quality_issues: List[Dict]):
        """Render data improvement suggestions"""
        st.markdown("##### Improvement Suggestions")
        
        suggestions = ValidationUtils.suggest_data_improvements(quality_issues)
        
        if suggestions:
            for suggestion in suggestions:
                st.write(suggestion)
        else:
            st.success("Your data quality looks excellent! No specific improvements needed.")
    
    def _calculate_field_quality_score(self, stats: Dict[str, Any]) -> float:
        """Calculate quality score for individual field"""
        total_records = stats.get('RECORDS', 0)
        if total_records == 0:
            return 0.0
        
        null_count = stats.get('NULL_COUNT', 0)
        spaces_count = stats.get('LEADING_TRAILING_SPACES_COUNT', 0)
        
        # Base score from population percentage
        population_score = stats.get('POPULATION_PERCENTAGE', 0)
        
        # Deduct points for quality issues
        quality_deduction = 0
        if spaces_count > 0:
            quality_deduction += (spaces_count / total_records) * 20  # Up to 20% deduction
        
        final_score = max(0, population_score - quality_deduction)
        return round(final_score, 1)
    
    def export_profiler_results(self, profiler_results: ProfilerResults, schema_name: str):
        """Export profiler results to downloadable format"""
        st.markdown("##### Export Results")
        
        export_format = st.selectbox("Export Format", ["JSON", "CSV", "Excel"])
        
        if st.button("Generate Export"):
            try:
                if export_format == "JSON":
                    self._export_to_json(profiler_results, schema_name)
                elif export_format == "CSV":
                    self._export_to_csv(profiler_results, schema_name)
                elif export_format == "Excel":
                    self._export_to_excel(profiler_results, schema_name)
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
    
    def _convert_to_json_serializable(self, obj):
        """Convert numpy and pandas data types to JSON serializable types"""
        if isinstance(obj, dict):
            return {key: self._convert_to_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def _export_to_json(self, profiler_results: ProfilerResults, schema_name: str):
        """Export results to JSON format"""
        try:
            export_data = {
                'schema_name': schema_name,
                'field_profiles': {fid: fp.to_dict() for fid, fp in profiler_results.field_profiles.items()},
                'table_profiles': {tid: tp.to_dict() for tid, tp in profiler_results.table_profiles.items()},
                'quality_issues': profiler_results.quality_issues,
                'schema_summary': profiler_results.schema_summary
            }
            
            # Convert to JSON serializable format
            export_data = self._convert_to_json_serializable(export_data)
            
            json_str = json.dumps(export_data, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"{schema_name}_profile_results.json",
                mime="application/json"
            )
            st.success("JSON export ready for download!")
            
        except Exception as e:
            st.error(f"JSON export failed: {str(e)}")
    
    def _export_to_csv(self, profiler_results: ProfilerResults, schema_name: str):
        """Export field profiles to CSV format"""
        try:
            stats_data = []
            
            for field_profile in profiler_results.field_profiles.values():
                stats = field_profile.statistics
                row = {
                    'field_name': field_profile.field_name,
                    'data_type': stats.get('DATA_TYPE', ''),
                    'records': int(stats.get('RECORDS', 0)),
                    'null_count': int(stats.get('NULL_COUNT', 0)),
                    'population_percentage': float(stats.get('POPULATION_PERCENTAGE', 0)),
                    'distinct_count': int(stats.get('DISTINCT_COUNT', 0))
                }
                
                if stats.get('DATA_TYPE') == 'numeric':
                    row.update({
                        'min_value': float(stats.get('MIN_VALUE', 0)) if stats.get('MIN_VALUE') is not None else None,
                        'max_value': float(stats.get('MAX_VALUE', 0)) if stats.get('MAX_VALUE') is not None else None,
                        'mean_value': float(stats.get('MEAN_VALUE', 0)) if stats.get('MEAN_VALUE') is not None else None,
                        'median_value': float(stats.get('MEDIAN_VALUE', 0)) if stats.get('MEDIAN_VALUE') is not None else None
                    })
                else:
                    row.update({
                        'min_length': int(stats.get('MIN_LENGTH', 0)) if stats.get('MIN_LENGTH') is not None else None,
                        'max_length': int(stats.get('MAX_LENGTH', 0)) if stats.get('MAX_LENGTH') is not None else None,
                        'avg_length': float(stats.get('AVG_LENGTH', 0)) if stats.get('AVG_LENGTH') is not None else None,
                        'spaces_count': int(stats.get('LEADING_TRAILING_SPACES_COUNT', 0))
                    })
                
                stats_data.append(row)
            
            if stats_data:
                df = pd.DataFrame(stats_data)
                csv_str = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_str,
                    file_name=f"{schema_name}_field_profiles.csv",
                    mime="text/csv"
                )
                st.success("CSV export ready for download!")
            else:
                st.warning("No data to export")
                
        except Exception as e:
            st.error(f"CSV export failed: {str(e)}")
    
    def _export_to_excel(self, profiler_results: ProfilerResults, schema_name: str):
        """Export comprehensive results to Excel format"""
        st.info("Excel export feature coming soon! Use JSON or CSV export for now.")