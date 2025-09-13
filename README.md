# Super Pancake Project Registry

This repository provides a minimal command line interface for managing projects.

## Features
- Persistent registry stored in `projects.json`.
- Lists existing projects and allows creating new ones.
- Prompts for project name, number of source schemas, and target schema when creating a project.

## Usage
Run the project manager:

```bash
python project_manager.py
```

Follow the prompts to create or view projects. The registry is saved to `projects.json` in the repository root.

## Theming

The Streamlit UI uses a lightweight theming system defined in `styles.css`. The file
contains CSS variables for colors and fonts along with utility classes such as
`main-container` and `primary-button`. The stylesheet is loaded in `app.py` using:

```python
st.set_page_config(layout="wide")
st.markdown("<style>" + Path("styles.css").read_text() + "</style>", unsafe_allow_html=True)
```

Wrap Streamlit elements with these classes via `st.markdown` to apply the theme:

```python
st.markdown('<div class="main-container">', unsafe_allow_html=True)
# UI elements
st.markdown('</div>', unsafe_allow_html=True)
```

Buttons can be wrapped in a `primary-button` div to give them a consistent look.
Future contributors can extend the theme by editing `styles.css` with additional
variables or classes.
