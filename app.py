import json
from tempfile import NamedTemporaryFile
from typing import List, Dict, Any
from pathlib import Path

import pandas as pd
import streamlit as st

from error_handler import ErrorCollector, DataError
from project_manager import ProjectRegistry, Project
from schema_validator import validate_schema_data
from upload_workflow import upload_workbook


st.set_page_config(layout="wide", page_title="Schema Mapper", page_icon="🗺️")
st.markdown(
    "<style>" + Path("styles.css").read_text() + "</style>", unsafe_allow_html=True
)


# --- Navigation helpers ----------------------------------------------------

def _set_page(page: str, project: str | None = None) -> None:
    """Update the current page and optional selected project.

    The function mutates :data:`st.session_state` but does **not** trigger a
    rerun. Callers should invoke :func:`st.rerun` after changing the state to
    immediately update the UI.
    """
    st.session_state.page = page
    if project is not None:
        st.session_state.selected_project = project


# --- Page implementations ---------------------------------------------------

def landing_page() -> None:
    """Initial landing page with navigation options."""
    st.title("Schema Mapper")
    st.markdown("Map and manage your project's schemas with ease.")

    center_col = st.columns([1, 1, 1])[1]
    with center_col:
        st.markdown('<div class="primary-button">', unsafe_allow_html=True)
        open_clicked = st.button(
            "Open Existing Project", use_container_width=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div class="secondary-button">', unsafe_allow_html=True)
        create_clicked = st.button(
            "Create New Project", use_container_width=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if open_clicked:
        _set_page("list_projects")
        st.rerun()
    if create_clicked:
        _set_page("list_projects")
        st.rerun()


def list_projects(registry: ProjectRegistry) -> None:
    """Display list of existing projects."""
    st.title("Project Dashboard")
    st.header("Existing Projects")

    projects = registry.list_projects()
    if projects:
        data = [
            {
                "Name": p.name,
                "Sources": p.num_source_schemas,
                "Target": p.target_schema,
            }
            for p in projects
        ]
        df = pd.DataFrame(data)
        df["Open"] = False
        edited = st.data_editor(
            df,
            column_config={
                "Name": st.column_config.TextColumn("Name", disabled=True),
                "Sources": st.column_config.NumberColumn("Sources", disabled=True),
                "Target": st.column_config.TextColumn("Target", disabled=True),
                "Open": st.column_config.CheckboxColumn("Open"),
            },
            hide_index=True,
        )
        for idx, open_flag in enumerate(edited["Open"]):
            if open_flag:
                _set_page("project", projects[idx].name)
                st.rerun()
    else:
        st.info("No projects available")

    st.divider()
    st.header("Add Project")
    create_project(registry)


def create_project(registry: ProjectRegistry) -> None:
    """Form to create a new project."""
    with st.form("add_project_form"):
        name = st.text_input("Name")
        num_sources = st.number_input(
            "Number of source schemas", min_value=0, step=1, value=0
        )
        target = st.text_input("Target schema")
        st.markdown('<div class="primary-button">', unsafe_allow_html=True)
        submitted = st.form_submit_button("Create")
        st.markdown("</div>", unsafe_allow_html=True)
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
                _set_page("list_projects")
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
        st.markdown('<div class="secondary-button">', unsafe_allow_html=True)
        if st.button("Back"):
            _set_page("list_projects")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return
    st.sidebar.markdown('<div class="secondary-button">', unsafe_allow_html=True)
    if st.sidebar.button("Back to projects"):
        _set_page("list_projects")
        st.rerun()
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    st.title(f"Project: {project.name}")
    st.write(f"Source schemas: {project.num_source_schemas}")
    st.write(f"Target schema: {project.target_schema}")

    src_schema = st.file_uploader("Source schema", type=["json"], key="src_schema")
    tgt_schema = st.file_uploader("Target schema", type=["json"], key="tgt_schema")
    sample_data = st.file_uploader(
        "Sample data", type=["json", "csv", "xlsx", "xls"], key="sample_data"
    )

    collector = ErrorCollector()

    st.markdown('<div class="primary-button">', unsafe_allow_html=True)
    if st.button("Validate Sample Data"):
        schema = _load_json(src_schema)
        data = _load_json(sample_data)
        valid, errors = validate_schema_data(schema, data)
        if valid:
            st.success("Sample data validated successfully")
        else:
            for field, msgs in errors.items():
                for msg in msgs:
                    collector.add_error(
                        DataError(field_name=field, row_number=None, message=msg)
                    )
            for err in collector.errors:
                st.error(str(err))
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="primary-button">', unsafe_allow_html=True)
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
    st.markdown("</div>", unsafe_allow_html=True)


# --- Application entry point -----------------------------------------------

def main() -> None:
    """Streamlit application entry point."""
    if "page" not in st.session_state:
        st.session_state.page = "landing"
    registry = ProjectRegistry()
    page = st.session_state.page
    if page == "landing":
        landing_page()
    elif page == "list_projects":
        list_projects(registry)
    elif page == "project":
        project_name = st.session_state.get("selected_project", "")
        project_config(registry, project_name)
    else:
        st.write("Unknown page")


if __name__ == "__main__":
    main()
