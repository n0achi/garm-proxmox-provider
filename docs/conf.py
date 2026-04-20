"""Sphinx configuration for garm-proxmox-provider docs."""

import os
import sys

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
