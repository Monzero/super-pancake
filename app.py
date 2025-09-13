import json
from tempfile import NamedTemporaryFile
from typing import List, Dict, Any

import pandas as pd
import streamlit as st

from error_handler import ErrorCollector, DataError
from project_manager import ProjectRegistry, Project
from schema_validator import validate_schema_data
from upload_workflow import upload_workbook


# --- Navigation helpers ----------------------------------------------------

def _set_page(page: str, project: str | None = None) -> None:
    """Update the current page and optional selected project."""
    st.session_state.page = page
    if project is not None:
        st.session_state.selected_project = project


# --- Page implementations ---------------------------------------------------

def landing_page() -> None:
    """Initial landing page with navigation options."""
    st.title("Welcome")
    if st.button("Open Existing Project"):
        _set_page("project_dashboard")
        st.rerun()
    if st.button("Create New Project"):
        _set_page("project_dashboard")
        st.rerun()


def project_dashboard(registry: ProjectRegistry) -> None:
    """Display existing projects and allow creation of new ones."""
    st.title("Project Dashboard")

    st.header("Existing Projects")
    projects = registry.list_projects()
    if projects:
        data = [
            {
                "Name": p.name,
                "Sources": p.num_source_schemas,
                "Target": p.target_schema,
                "Open": False,
            }
            for p in projects
        ]
        df = pd.DataFrame(data)
        edited_df = st.data_editor(
            df,
            column_config={
                "Open": st.column_config.ButtonColumn(
                    label="Open",
                    help="Open project",
                    icon="📂",
                )
            },
            hide_index=True,
            key="projects_table",
        )
        for _, row in edited_df.iterrows():
            if row.get("Open"):
                _set_page("project", row["Name"])
                st.rerun()
    else:
        st.info("No projects yet.")

    st.divider()

    st.header("Add Project")
    with st.form("add_project_form"):
        name = st.text_input("Name")
        num_sources = st.number_input(
            "Number of source schemas", min_value=0, step=1, value=0
        )
        target = st.text_input("Target schema")
        submitted = st.form_submit_button("Create", help="Create project")
        if submitted:
            try:
                registry.add_project(
                    Project(
                        name=name,
                        num_source_schemas=int(num_sources),
                        target_schema=target,
                    )
                )
                st.success(f"Project '{name}' added")
                _set_page("project_dashboard")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))


def _load_json(upload) -> List[Dict[str, Any]]:
    if upload is None:
        return []
    try:
        return json.loads(upload.getvalue().decode("utf-8"))
    except Exception:
        return []


def project_config(registry: ProjectRegistry, project_name: str) -> None:
    """Show project details and provide upload/validation widgets."""
    project = next(
        (p for p in registry.list_projects() if p.name == project_name), None
    )
    if not project:
        st.error("Project not found")
        if st.button("Back"):
            _set_page("project_dashboard")
            st.rerun()
        return
    if st.sidebar.button("Back to projects"):
        _set_page("project_dashboard")
        st.rerun()
    st.title(f"Project: {project.name}")
    st.write(f"Source schemas: {project.num_source_schemas}")
    st.write(f"Target schema: {project.target_schema}")

    src_schema = st.file_uploader("Source schema", type=["json"], key="src_schema")
    tgt_schema = st.file_uploader("Target schema", type=["json"], key="tgt_schema")
    sample_data = st.file_uploader(
        "Sample data", type=["json", "csv", "xlsx", "xls"], key="sample_data"
    )

    collector = ErrorCollector()

    if st.button("Validate Sample Data"):
        schema = _load_json(src_schema)
        data = _load_json(sample_data)
        valid, errors = validate_schema_data(schema, data)
        if valid:
            st.success("Sample data validated successfully")
        else:
            for field, msgs in errors.items():
                for msg in msgs:
                    collector.add_error(DataError(field_name=field, row_number=None, message=msg))
            for err in collector.errors:
                st.error(str(err))

    if st.button("Process Workbook") and sample_data is not None:
        with NamedTemporaryFile(delete=False) as tmp:
            tmp.write(sample_data.getvalue())
            tmp_path = tmp.name
        result = upload_workbook(tmp_path)
        if result.get("status") == "ok":
            st.success("Workbook uploaded successfully")
        else:
            collector.add_error(
                DataError(field_name="workbook", row_number=None, message=result.get("error", "Unknown error"))
            )
            for err in collector.errors:
                st.error(str(err))


# --- Application entry point -----------------------------------------------

def main() -> None:
    """Streamlit application entry point."""
    if "page" not in st.session_state:
        st.session_state.page = "landing"
    registry = ProjectRegistry()
    page = st.session_state.page
    if page == "landing":
        landing_page()
    elif page == "project_dashboard":
        project_dashboard(registry)
    elif page == "project":
        project_name = st.session_state.get("selected_project", "")
        project_config(registry, project_name)
    else:
        st.write("Unknown page")


if __name__ == "__main__":
    main()
