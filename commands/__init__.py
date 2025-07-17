from pathlib import Path
import importlib

import versions
from .gluon import commands, Context

# This folder is used to define the commands used by Roentgenium.
# Editing this file directly is not recommended.

__version__ = versions.Version(3, 0, 0)     # This defines the version of the module's framework.

# Automatically import modules stored here.
for path in Path("commands").glob("*.py"):
    if path.stem in ("__init__", "gluon"):
        continue
    importlib.import_module("commands." + path.stem)

__all__ = ["commands", "Context"]
