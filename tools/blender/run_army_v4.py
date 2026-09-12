#!/usr/bin/env python3
"""Execute generate_army_v4.py with Blender math globals prebound.

The v4 art pass intentionally layers on top of the tested v3 generator. This runner
keeps the art script unchanged while supplying Blender's Vector helper in its global
namespace before execution.
"""
from pathlib import Path
from mathutils import Vector

SCRIPT = Path(__file__).resolve().with_name("generate_army_v4.py")
namespace = {
    "__name__": "__main__",
    "__file__": str(SCRIPT),
    "Vector": Vector,
}
code = compile(SCRIPT.read_text(encoding="utf-8"), str(SCRIPT), "exec")
exec(code, namespace, namespace)
