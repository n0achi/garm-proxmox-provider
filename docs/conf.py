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

# Sphinx extensions
# - `sphinx_copybutton` removes prompts when copying code blocks
# - `sphinx_inline_tabs` enables inline tabbed content in docs
# - `sphinxext.opengraph` generates social preview metadata (social-cards)
# - `myst_parser` enables Markdown (MyST) support alongside RST
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinxcontrib.mermaid",
    "sphinx_copybutton",
    "sphinx_inline_tabs",
    "sphinxext.opengraph",
    "myst_parser",
]

html_theme = "furo"

# Autodoc / Napoleon options
autodoc_member_order = "bysource"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# myst-parser (Markdown / MyST) configuration
# Enable commonly used MyST extensions to allow richer Markdown content in the docs.
myst_enable_extensions = [
    "deflist",
    "colon_fence",
    "html_admonition",
    "html_image",
]
# Automatically add anchors for headings up to this level
myst_heading_anchors = 3

# sphinx-copybutton: strip common REPL / shell prompts when copying code
# This is a regexp that matches Python REPL, continuation, and shell prompts.
copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True

# sphinxext-opengraph: basic site metadata for social cards.
# Update `ogp_site_url` and `ogp_image` to your published site when available.
ogp_site_url = "https://example.com/"
ogp_site_name = project
ogp_image = "https://example.com/assets/og-image.png"
ogp_description_length = 200

# Static files
html_static_path = ["_static"]

# Development / live-preview notes:
# - sphinx-autobuild is a CLI tool (not an extension) that provides live-reload while
#   editing the docs. When using `uv` to manage dev deps, run:
#     uv sync --dev
#     uv run sphinx-autobuild docs docs/_build/html --open-browser
#
# - Alternatively, build once via the uv-managed environment:
#     uv sync --dev
#     uv run sphinx-build -b html docs docs/_build/html
#
# - The added extensions enable:
#   * copy-to-clipboard for code blocks (`sphinx_copybutton`)
#   * inline tabbed content in pages (`sphinx_inline_tabs`)
#   * Markdown (MyST) files alongside RST (`myst_parser`)
#   * Open Graph metadata for nicer social cards when publishing (`sphinxext.opengraph`)
#
# Keep conf.py minimal and deterministic so CI and local builds behave consistently.
