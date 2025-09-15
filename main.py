import streamlit as st
import os
from datetime import datetime

# Import services
from services.project_service import ProjectService

# Import UI components
from ui.project_ui import ProjectUI
from ui.schema_ui import SchemaUI
from ui.project_settings_ui import ProjectSettingsUI

def configure_page():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="Data Schema Management System",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def initialize_session_state():
    """Initialize session state variables"""
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'schemas'  # 'schemas' or 'settings'
    if 'schemas' not in st.session_state:
        st.session_state.schemas = {}
    if 'sample_data' not in st.session_state:
        st.session_state.sample_data = {}
    if 'profiler_results' not in st.session_state:
        st.session_state.profiler_results = {}

def render_sidebar():
    """Render sidebar navigation and help"""
    with st.sidebar:
        st.title("Navigation")
        
        # Current project info
        if st.session_state.current_project:
            st.success(f"**Project:** {st.session_state.current_project.name}")
            
            # Project navigation
            st.markdown("### Project Navigation")
            view_option = st.radio(
                "Select View:",
                ["Schema Management", "Project Settings"],
                index=0 if st.session_state.current_view == 'schemas' else 1,
                key="view_selector"
            )
            
            # Update current view
            if view_option == "Schema Management":
                st.session_state.current_view = 'schemas'
            else:
                st.session_state.current_view = 'settings'
            
            # Project details
            project = st.session_state.current_project
            with st.expander("Project Details"):
                st.write(f"**Description:** {project.description}")
                st.write(f"**Input Schemas:** {', '.join(project.input_schema_names)}")
                st.write(f"**Target Schema:** {project.target_schema_name}")
                st.write(f"**Created:** {project.created_at.strftime('%Y-%m-%d %H:%M')}")
                if project.data_owners:
                    st.write(f"**Data Owners:** {', '.join(project.data_owners)}")
            
            # Change project button
            if st.button("Change Project", help="Switch to a different project"):
                st.session_state.current_project = None
                st.session_state.current_view = 'schemas'
                # Clear all schema-related session state
                for key in list(st.session_state.keys()):
                    if key.startswith(('schemas', 'sample_data', 'profiler_results')):
                        del st.session_state[key]
                st.rerun()
        
        st.markdown("---")
        
        # Quick Help Section
        st.markdown("### Quick Help")
        
        with st.expander("Schema CSV Format"):
            st.markdown("""
            **Required columns:**
            - field_name (name of the field)
            - data_type (string, number, date, etc.)
            
            **Optional columns:**
            - description (field description)
            - length (max length for strings)
            - nullable (Y/N, defaults to Y)
            - primary_key (Y/N, defaults to N)
            - foreign_key_ref (reference to other table)
            - example_values (sample values)
            - tags (metadata tags)
            """)
        
        with st.expander("Data Types"):
            st.markdown("""
            **Supported types:**
            - string, varchar, text
            - int, integer, number
            - float, decimal
            - date, datetime
            - boolean
            - email, phone
            """)
        
        with st.expander("Project Settings"):
            st.markdown("""
            **Configuration:**
            - Change number of schemas
            - Rename schemas
            - Update project details
            
            **File Management:**
            - View uploaded files
            - Clean orphaned files
            - Export file lists
            
            **Danger Zone:**
            - Delete entire project
            """)
        
        st.markdown("---")
        
        # System info
        st.markdown("### System Info")
        st.caption(f"**Version:** 1.0.0")
        st.caption(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}")
        
        # Feedback
        st.markdown("### Feedback")
        st.caption("Have suggestions? Found a bug?")
        if st.button("Send Feedback"):
            st.info("Please send feedback to: support@yourcompany.com")

def main():
    """Main Streamlit application"""
    # Configure page
    configure_page()
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize services
    project_service = ProjectService()
    
    # Initialize UI components
    project_ui = ProjectUI(project_service)
    schema_ui = SchemaUI()
    settings_ui = ProjectSettingsUI(project_service)
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    if st.session_state.current_project is None:
        # Show project selection/creation
        project_ui.render_project_selection()
    else:
        # Show either schema management or project settings
        if st.session_state.current_view == 'settings':
            # Project Settings View
            settings_ui.render_project_settings(st.session_state.current_project)
        else:
            # Schema Management View (default)
            # Simple header with just project name
            st.title(st.session_state.current_project.name)
            
            # Schema management tabs
            schema_ui.render_schema_management(st.session_state.current_project)
            
            # Footer with progress indicator (only in schema view)
            st.markdown("---")
            
            # Progress tracking
            total_schemas = len(st.session_state.current_project.input_schema_names) + 1  # +1 for target
            schemas_loaded = len([k for k in st.session_state.schemas.keys() if k.startswith('schema_')])
            sample_data_loaded = len([k for k in st.session_state.sample_data.keys() if k.startswith('sample_')])
            profiles_generated = len([k for k in st.session_state.profiler_results.keys() if k.startswith('profile_')])
            
            st.markdown("### Project Progress")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Schemas Loaded", 
                    f"{schemas_loaded}/{total_schemas}",
                    f"{(schemas_loaded/total_schemas*100):.0f}%" if total_schemas > 0 else "0%"
                )
            
            with col2:
                st.metric(
                    "Sample Data", 
                    f"{sample_data_loaded}/{total_schemas}",
                    f"{(sample_data_loaded/total_schemas*100):.0f}%" if total_schemas > 0 else "0%"
                )
            
            with col3:
                st.metric(
                    "Profiles Generated", 
                    f"{profiles_generated}/{sample_data_loaded}" if sample_data_loaded > 0 else "0/0",
                    f"{(profiles_generated/sample_data_loaded*100):.0f}%" if sample_data_loaded > 0 else "0%"
                )
            
            with col4:
                overall_progress = (schemas_loaded + sample_data_loaded + profiles_generated) / (total_schemas * 3) * 100 if total_schemas > 0 else 0
                st.metric(
                    "Overall Progress", 
                    f"{overall_progress:.0f}%"
                )
            
            # Progress bar
            progress_bar = st.progress(overall_progress / 100)
            
            # Next steps suggestions
            if schemas_loaded < total_schemas:
                st.info("**Next Step:** Upload schema definitions for all domains")
            elif sample_data_loaded < total_schemas:
                st.info("**Next Step:** Upload sample data files (optional but recommended)")
            elif profiles_generated < sample_data_loaded:
                st.info("**Next Step:** Generate data profiles to analyze quality")
            else:
                st.success("**Project Complete!** All schemas loaded and profiled")

if __name__ == "__main__":
    # Ensure required directories exist
    os.makedirs("projects", exist_ok=True)
    
    # Run the application
    main()