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

The Streamlit application (`app.py`) uses a lightweight theming system to keep
styling consistent:

- Global colors, fonts, and button styles live in `styles.css`.
- The stylesheet is injected at startup via `st.markdown` so updates are picked
  up automatically.
- UI elements are wrapped in `<div>` containers with classes such as
  `.primary-button` or `.secondary-button`, allowing the CSS to target specific
  components.

To adjust the theme, edit `styles.css` and apply new classes around elements in
`app.py` as needed.
