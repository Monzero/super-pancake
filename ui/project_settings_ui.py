import streamlit as st
from datetime import datetime
from services.project_service import ProjectService
from models.project import ProjectConfig

class ProjectSettingsUI:
    """UI components for project settings management"""
    
    def __init__(self, project_service: ProjectService):
        self.project_service = project_service
    
    def render_project_settings(self, project_config: ProjectConfig):
        """Render project settings interface"""
        st.title(f"Project Settings: {project_config.name}")
        
        # Create tabs for different settings
        tab1, tab2, tab3 = st.tabs(["Configuration", "Files & Storage", "Danger Zone"])
        
        with tab1:
            self._render_configuration_settings(project_config)
        
        with tab2:
            self._render_storage_settings(project_config)
        
        with tab3:
            self._render_danger_zone(project_config)
    
    def _render_configuration_settings(self, project_config: ProjectConfig):
        """Render configuration editing interface"""
        st.subheader("Project Configuration")
        
        with st.form("project_config_form"):
            # Basic project info
            st.markdown("#### Basic Information")
            new_description = st.text_area(
                "Project Description", 
                value=project_config.description,
                help="Update the project description"
            )
            
            # Data owners
            current_owners = ", ".join(project_config.data_owners) if project_config.data_owners else ""
            new_owners_text = st.text_area(
                "Data Owners", 
                value=current_owners,
                help="Enter names separated by commas"
            )
            new_data_owners = [owner.strip() for owner in new_owners_text.split(",") if owner.strip()]
            
            # Schema configuration
            st.markdown("#### Schema Configuration")
            st.info("Note: Changing schema configuration will not delete existing files, but may affect functionality if schemas are removed.")
            
            # Input schemas
            st.write("**Current Input Schemas:**", ", ".join(project_config.input_schema_names))
            
            new_num_input_schemas = st.number_input(
                "Number of Input Schemas", 
                min_value=1, 
                max_value=10, 
                value=len(project_config.input_schema_names)
            )
            
            new_input_schema_names = []
            for i in range(new_num_input_schemas):
                # Pre-fill with existing names if available
                default_name = project_config.input_schema_names[i] if i < len(project_config.input_schema_names) else ""
                
                schema_name = st.text_input(
                    f"Input Schema {i+1} Name", 
                    value=default_name,
                    key=f"new_input_schema_{i}",
                    placeholder=f"e.g., schema_{i+1}"
                )
                if schema_name:
                    new_input_schema_names.append(schema_name)
            
            # Target schema
            new_target_schema_name = st.text_input(
                "Target Schema Name", 
                value=project_config.target_schema_name,
                help="Name of the target/output schema"
            )
            
            # Show changes summary
            changes_detected = self._detect_changes(
                project_config, new_description, new_data_owners, 
                new_input_schema_names, new_target_schema_name
            )
            
            if changes_detected:
                st.markdown("#### Changes Summary")
                st.info("The following changes will be applied:")
                self._show_changes_summary(
                    project_config, new_description, new_data_owners,
                    new_input_schema_names, new_target_schema_name
                )
            
            # Submit button
            col1, col2 = st.columns([1, 1])
            with col1:
                save_button = st.form_submit_button("Save Changes", type="primary")
            with col2:
                if st.form_submit_button("Reset to Current"):
                    st.rerun()
            
            if save_button:
                if len(new_input_schema_names) != new_num_input_schemas:
                    st.error("Please provide names for all input schemas")
                elif not new_target_schema_name:
                    st.error("Target schema name is required")
                elif not changes_detected:
                    st.info("No changes detected")
                else:
                    # Apply changes
                    success = self._apply_configuration_changes(
                        project_config, new_description, new_data_owners,
                        new_input_schema_names, new_target_schema_name
                    )
                    
                    if success:
                        st.success("Project configuration updated successfully!")
                        # Update session state
                        st.session_state.current_project = project_config
                        st.rerun()
                    else:
                        st.error("Failed to save project configuration")
    
    def _render_storage_settings(self, project_config: ProjectConfig):
        """Render storage and files information"""
        st.subheader("Files & Storage")
        
        # Project statistics
        stats = self.project_service.get_project_stats(project_config.name)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Files", stats.get('total_files', 0))
        with col2:
            st.metric("Schema Files", stats.get('schema_files', 0))
        with col3:
            st.metric("Sample Files", stats.get('sample_files', 0))
        with col4:
            total_size_mb = stats.get('total_size', 0) / (1024 * 1024)
            st.metric("Total Size", f"{total_size_mb:.2f} MB")
        
        # File listing
        if project_config.project_files:
            st.markdown("#### Project Files")
            
            files_data = []
            for pf in project_config.project_files:
                files_data.append({
                    "Schema": pf.schema_name,
                    "Type": pf.file_type.title(),
                    "Original Name": pf.original_filename,
                    "Size (KB)": f"{pf.file_size / 1024:.1f}",
                    "Uploaded": pf.uploaded_at.strftime("%Y-%m-%d %H:%M")
                })
            
            files_df = st.dataframe(files_data, use_container_width=True)
            
            # File management options
            st.markdown("#### File Management")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Clean Orphaned Files", help="Remove files for schemas that no longer exist"):
                    orphaned_files = self._find_orphaned_files(project_config)
                    if orphaned_files:
                        st.warning(f"Found {len(orphaned_files)} orphaned files")
                        # Show orphaned files
                        for pf in orphaned_files:
                            st.write(f"- {pf.original_filename} (schema: {pf.schema_name})")
                        
                        if st.button("Remove Orphaned Files", key="confirm_remove_orphaned"):
                            self._remove_orphaned_files(project_config, orphaned_files)
                            st.success("Orphaned files removed")
                            st.rerun()
                    else:
                        st.success("No orphaned files found")
            
            with col2:
                if st.button("Export File List", help="Download list of project files"):
                    import pandas as pd
                    df = pd.DataFrame(files_data)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "Download File List CSV",
                        csv,
                        f"{project_config.name}_files.csv",
                        "text/csv"
                    )
        else:
            st.info("No files uploaded yet")
        
        # Project metadata
        st.markdown("#### Project Metadata")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Created:** {project_config.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"**Last Updated:** {project_config.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        with col2:
            project_age = datetime.now() - project_config.created_at
            st.write(f"**Project Age:** {project_age.days} days")
            st.write(f"**Total Schemas:** {len(project_config.input_schema_names) + 1}")
    
    def _render_danger_zone(self, project_config: ProjectConfig):
        """Render dangerous operations like project deletion"""
        st.subheader("Danger Zone")
        st.error("⚠️ Warning: Operations in this section are irreversible!")
        
        # Project deletion
        with st.expander("Delete Project", expanded=False):
            st.markdown("#### Delete This Project")
            st.warning("""
            **This will permanently delete:**
            - Project configuration
            - All uploaded files (schema and sample data)
            - All profiling results
            - Project directory and all contents
            
            **This action cannot be undone!**
            """)
            
            # Confirmation steps
            st.write("To delete this project, please:")
            
            # Step 1: Type project name
            confirmation_name = st.text_input(
                f"1. Type the project name '{project_config.name}' to confirm:",
                placeholder=project_config.name
            )
            
            name_confirmed = confirmation_name == project_config.name
            
            # Step 2: Checkbox confirmation
            danger_confirmed = st.checkbox(
                "2. I understand this action is permanent and cannot be undone",
                disabled=not name_confirmed
            )
            
            # Delete button
            if name_confirmed and danger_confirmed:
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button(
                        "🗑️ DELETE PROJECT", 
                        type="primary",
                        help="This will permanently delete the project"
                    ):
                        if self._delete_project(project_config):
                            st.success("Project deleted successfully!")
                            # Clear session state and return to project selection
                            for key in list(st.session_state.keys()):
                                if key.startswith(('current_project', 'schemas', 'sample_data', 'profiler_results')):
                                    del st.session_state[key]
                            st.rerun()
                        else:
                            st.error("Failed to delete project")
            elif confirmation_name and not name_confirmed:
                st.error("Project name doesn't match")
    
    def _detect_changes(self, project_config, new_description, new_data_owners, 
                       new_input_schema_names, new_target_schema_name):
        """Detect if any changes were made to the configuration"""
        return (
            new_description != project_config.description or
            new_data_owners != project_config.data_owners or
            new_input_schema_names != project_config.input_schema_names or
            new_target_schema_name != project_config.target_schema_name
        )
    
    def _show_changes_summary(self, project_config, new_description, new_data_owners,
                             new_input_schema_names, new_target_schema_name):
        """Show summary of detected changes"""
        if new_description != project_config.description:
            st.write("- Description updated")
        
        if new_data_owners != project_config.data_owners:
            st.write("- Data owners updated")
        
        if new_input_schema_names != project_config.input_schema_names:
            st.write("- Input schemas changed:")
            st.write(f"  - From: {project_config.input_schema_names}")
            st.write(f"  - To: {new_input_schema_names}")
            
            # Warn about removed schemas
            removed_schemas = set(project_config.input_schema_names) - set(new_input_schema_names)
            if removed_schemas:
                st.warning(f"Removed schemas: {', '.join(removed_schemas)} (files will remain but may not be accessible)")
        
        if new_target_schema_name != project_config.target_schema_name:
            st.write(f"- Target schema: '{project_config.target_schema_name}' → '{new_target_schema_name}'")
    
    def _apply_configuration_changes(self, project_config, new_description, new_data_owners,
                                   new_input_schema_names, new_target_schema_name):
        """Apply configuration changes to the project"""
        try:
            # Update project configuration
            project_config.description = new_description
            project_config.data_owners = new_data_owners
            project_config.input_schema_names = new_input_schema_names
            project_config.target_schema_name = new_target_schema_name
            project_config.updated_at = datetime.now()
            
            # Save to disk
            return self.project_service.save_project(project_config)
            
        except Exception as e:
            st.error(f"Error applying changes: {e}")
            return False
    
    def _find_orphaned_files(self, project_config):
        """Find files that belong to schemas no longer in the configuration"""
        all_current_schemas = set(project_config.input_schema_names + [project_config.target_schema_name])
        orphaned_files = []
        
        for pf in project_config.project_files:
            if pf.schema_name not in all_current_schemas:
                orphaned_files.append(pf)
        
        return orphaned_files
    
    def _remove_orphaned_files(self, project_config, orphaned_files):
        """Remove orphaned files from disk and project configuration"""
        try:
            for pf in orphaned_files:
                # Delete from disk
                self.project_service.delete_project_file(project_config.name, pf)
                # Remove from project configuration
                project_config.project_files.remove(pf)
            
            # Save updated configuration
            project_config.updated_at = datetime.now()
            self.project_service.save_project(project_config)
            
        except Exception as e:
            st.error(f"Error removing orphaned files: {e}")
    
    def _delete_project(self, project_config: ProjectConfig):
        """Delete the entire project"""
        try:
            # Delete all project files
            for pf in project_config.project_files:
                self.project_service.delete_project_file(project_config.name, pf)
            
            # Delete project directory
            import shutil
            import os
            project_dir = os.path.join(self.project_service.projects_dir, project_config.name)
            if os.path.exists(project_dir):
                shutil.rmtree(project_dir)
            
            # Delete project configuration file
            project_file = os.path.join(self.project_service.projects_dir, f"{project_config.name}.json")
            if os.path.exists(project_file):
                os.remove(project_file)
            
            return True
            
        except Exception as e:
            st.error(f"Error deleting project: {e}")
            return False