"""Sphinx configuration for garm-proxmox-provider docs."""

import os
import sys

# Prefer building docs with `uv run ...` so autodoc imports use the uv-managed environment.
# When building via `uv`, the project's packages are installed into the uv-managed
# environment and imports will resolve correctly. If you run Sphinx directly (for
# example, `sphinx-build`), the local `src` directory is added below so autodoc
# can still import the package from the source tree as a fallback.
if os.getenv("UV_RUN"):
    # Running under `uv run` — rely on the uv environment to provide package imports.
    pass

# Fallback to local source tree so `sphinx-build` works when not using `uv run`.
sys.path.insert(0, os.path.abspath("../src"))

project = "garm-proxmox-provider"
copyright = "2024, nikolai-in"
author = "nikolai-in"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinxcontrib.mermaid",
]

html_theme = "furo"

autodoc_member_order = "bysource"
napoleon_google_docstring = True
napoleon_numpy_docstring = False
