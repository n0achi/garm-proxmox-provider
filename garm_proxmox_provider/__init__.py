# Shim package to make `garm_proxmox_provider` importable when running tests from the
# repository root. Some test runners import the top-level package name and expect to
# find the modules; this file adjusts the package `__path__` at runtime to prefer the
# copy inside `src/garm_proxmox_provider` if it exists.
#
# This shim is intentionally small and defensive: it only mutates `__path__` when the
# expected `src` layout is present, and it doesn't raise on import failures so test
# collection can control import semantics.

from __future__ import annotations

import os
from typing import List

# Compute the absolute path to this file's directory
_here = os.path.abspath(os.path.dirname(__file__))

# Expected location of the real package when working in the repository:
# <repo>/src/garm_proxmox_provider
_src_pkg = os.path.abspath(os.path.join(_here, "..", "src", "garm_proxmox_provider"))

# If the source-layout package exists, prefer it by inserting at the front of __path__
try:
    if os.path.isdir(_src_pkg):
        # Prepend so this path is preferred when importing submodules
        __path__.insert(0, _src_pkg)  # type: ignore[name-defined]
except Exception:
    # Be silent on any filesystem/permission issues; downstream imports will surface errors.
    pass

# Attempt to export a convenient symbol if present (useful for `import garm_proxmox_provider`)
__all__: List[str]
try:
    # Try to expose the CLI entrypoint when available.
    from .cli import cli  # type: ignore[import]

    __all__ = ["cli"]
except Exception:
    # If importing fails, leave __all__ empty. Consumers can still import submodules
    # like `garm_proxmox_provider.commands` which will be resolved via the modified __path__.
    __all__ = []
