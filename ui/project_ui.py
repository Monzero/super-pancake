import streamlit as st
from services.project_service import ProjectService
from models.project import ProjectConfig

class ProjectUI:
    """UI components for project management"""
    
    def __init__(self, project_service: ProjectService):
        self.project_service = project_service
    
    def render_project_selection(self):
        """Render project selection/creation interface"""
        st.title("Data Schema Management System")
        
        # Project selection mode
        mode = st.radio(
            "Choose an option:",
            ["Create New Project", "Open Existing Project"],
            horizontal=True
        )
        
        if mode == "Create New Project":
            self._render_create_project()
        else:
            self._render_open_project()
    
    def _render_create_project(self):
        """Render create new project form"""
        st.subheader("Create New Project")
        
        with st.form("create_project_form"):
            project_name = st.text_input("Project Name", placeholder="Enter project name")
            project_description = st.text_area("Description (Optional)", placeholder="Project description")
            
            # Input schemas configuration
            st.subheader("Input Schemas Configuration")
            num_input_schemas = st.number_input("Number of Input Schemas", min_value=1, max_value=10, value=2)
            
            input_schema_names = []
            for i in range(num_input_schemas):
                schema_name = st.text_input(f"Input Schema {i+1} Name", key=f"input_schema_{i}", placeholder=f"e.g., payer, member")
                if schema_name:
                    input_schema_names.append(schema_name)
            
            # Target schema configuration
            st.subheader("Target Schema Configuration")
            target_schema_name = st.text_input("Target Schema Name", placeholder="e.g., unified_data")
            
            # Data owners (optional)
            st.subheader("Data Owners (Optional)")
            data_owners_text = st.text_area("Data Owners", placeholder="Enter names separated by commas")
            data_owners = [owner.strip() for owner in data_owners_text.split(",") if owner.strip()]
            
            submitted = st.form_submit_button("Create Project")
            
            if submitted:
                if not project_name:
                    st.error("Project name is required")
                elif len(input_schema_names) != num_input_schemas:
                    st.error("Please provide names for all input schemas")
                elif not target_schema_name:
                    st.error("Target schema name is required")
                else:
                    project_config = ProjectConfig(
                        name=project_name,
                        description=project_description,
                        input_schema_names=input_schema_names,
                        target_schema_name=target_schema_name,
                        data_owners=data_owners
                    )
                    
                    if self.project_service.create_project(project_config):
                        st.success(f"Project '{project_name}' created successfully!")
                        st.session_state.current_project = project_config
                        st.rerun()
                    else:
                        st.error("Failed to create project. Project name might already exist.")
    
    def _render_open_project(self):
        """Render open existing project interface"""
        st.subheader("Open Existing Project")
        
        projects = self.project_service.list_projects()
        
        if not projects:
            st.info("No existing projects found. Create a new project to get started.")
            return
        
        selected_project = st.selectbox("Select Project", projects)
        
        if st.button("Open Project"):
            project_config = self.project_service.load_project(selected_project)
            if project_config:
                st.success(f"Project '{selected_project}' loaded successfully!")
                st.session_state.current_project = project_config
                # Load existing files into session state
                self._load_project_files(project_config)
                st.rerun()
            else:
                st.error("Failed to load project")
        
        # Show project preview
        if selected_project:
            project_config = self.project_service.load_project(selected_project)
            if project_config:
                st.subheader("Project Preview")
                
                # Basic info
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Description:** {project_config.description}")
                    st.write(f"**Input Schemas:** {', '.join(project_config.input_schema_names)}")
                    st.write(f"**Target Schema:** {project_config.target_schema_name}")
                    st.write(f"**Created:** {project_config.created_at.strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    # Project statistics
                    stats = self.project_service.get_project_stats(selected_project)
                    if stats:
                        st.write(f"**Total Files:** {stats.get('total_files', 0)}")
                        st.write(f"**Schema Files:** {stats.get('schema_files', 0)}")
                        st.write(f"**Sample Files:** {stats.get('sample_files', 0)}")
                        
                        total_size_mb = stats.get('total_size', 0) / (1024 * 1024)
                        st.write(f"**Total Size:** {total_size_mb:.2f} MB")
                        
                        if stats.get('last_updated'):
                            st.write(f"**Last Updated:** {stats['last_updated'].strftime('%Y-%m-%d %H:%M')}")
                
                # Show existing files
                if project_config.project_files:
                    st.subheader("Existing Files")
                    for pf in project_config.project_files:
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        with col1:
                            st.write(f"**{pf.original_filename}**")
                        with col2:
                            st.write(f"{pf.schema_name}")
                        with col3:
                            st.write(f"{pf.file_type}")
                        with col4:
                            file_size_kb = pf.file_size / 1024
                            st.write(f"{file_size_kb:.1f} KB")
    
    def _load_project_files(self, project_config: ProjectConfig):
        """Load existing project files into session state"""
        try:
            # Clear existing session state
            for key in list(st.session_state.keys()):
                if key.startswith(('schemas', 'sample_data')):
                    del st.session_state[key]
            
            # Load schema files
            for pf in project_config.project_files:
                if pf.file_type == 'schema':
                    df = self.project_service.load_project_file(project_config.name, pf)
                    if df is not None:
                        # Parse schema and store in session state
                        from services.schema_service import SchemaService
                        schema = SchemaService.parse_schema_from_csv(df)
                        schema.name = pf.schema_name
                        st.session_state.schemas[f"schema_{pf.schema_name}"] = schema
                
                elif pf.file_type == 'sample':
                    df = self.project_service.load_project_file(project_config.name, pf)
                    if df is not None:
                        st.session_state.sample_data[f"sample_{pf.schema_name}"] = df
                        
        except Exception as e:
            st.error(f"Error loading project files: {e}")