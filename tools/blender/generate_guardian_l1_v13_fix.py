#!/usr/bin/env python3
"""Guardian L1 v13 asset-based rebuild hotfix for Blender 4.5 look enum."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import bpy

BASE = Path(__file__).with_name("generate_guardian_l1_v13.py")
spec = importlib.util.spec_from_file_location("guardian_v13", BASE)
v13 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(v13)


def setup_studio_fixed(size):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.render.resolution_x = size
    sc.render.resolution_y = size
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    # Blender 4.5 enum uses this value without the old 'AgX - ' prefix.
    sc.view_settings.look = "Medium High Contrast"

    for o in list(sc.objects):
        if o.type in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(o, do_unlink=True)

    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.010, 0.020, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.28

    floor_mat = v13.mat("GuardianFloorV13", (0.028, 0.037, 0.052), 0.15, 0.32)
    bpy.ops.mesh.primitive_plane_add(size=18, location=(0, 0, -0.01))
    floor = bpy.context.object
    floor.name = "StudioFloor"
    floor.data.materials.append(floor_mat)

    def area(name, loc, energy, size_l, color):
        d = bpy.data.lights.new(name, "AREA")
        d.energy = energy
        d.shape = "DISK"
        d.size = size_l
        d.color = color
        o = bpy.data.objects.new(name, d)
        sc.collection.objects.link(o)
        o.location = loc
        v13.look_at(o, (0, 0, 0.95))

    area("Key", (3.2, -4.4, 4.2), 1200, 3.4, (1.0, 0.83, 0.68))
    area("Fill", (-3.4, -2.1, 3.0), 700, 3.0, (0.48, 0.64, 1.0))
    area("Rim", (1.1, 3.0, 3.4), 1100, 2.6, (0.35, 0.56, 1.0))

    cd = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cd.lens = 70
    return cam


v13.setup_studio = setup_studio_fixed

if __name__ == "__main__":
    v13.main()
