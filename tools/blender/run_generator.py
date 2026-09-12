#!/usr/bin/env python3
"""Z-up entry point for the Emberfall procedural Blender generator.

This wrapper keeps the character authoring helpers in their game-style Y-up local
coordinates, then rotates the finished asset into Blender Z-up before rendering and
GLB export. GitHub Actions should call this file.
"""
from pathlib import Path
import importlib.util
import math
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
mod_spec = importlib.util.spec_from_file_location("emberfall_generate_unit", HERE / "generate_unit.py")
g = importlib.util.module_from_spec(mod_spec)
mod_spec.loader.exec_module(g)

_original_build = g.build_unit


def build_unit_zup(spec, level, kind, mats):
    root = _original_build(spec, level, kind, mats)
    root.rotation_euler.x = math.radians(90)
    return root


def setup_stage_zup(spec, root, preview_size):
    ground_mat = g.material("PreviewGround", (0.055, 0.07, 0.065), roughness=.92)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.55, depth=.10, location=(0, 0, -.055))
    ground = bpy.context.object
    ground.name = "preview_ground"
    ground.data.materials.append(ground_mat)

    def aim(obj, target):
        obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

    bpy.ops.object.light_add(type="AREA", location=(3.4, -4.5, 4.8))
    key = bpy.context.object
    key.data.energy = 900
    key.data.shape = 'DISK'
    key.data.size = 4.0
    aim(key, (0, 0, 1.1))

    bpy.ops.object.light_add(type="AREA", location=(-3.0, -2.2, 2.8))
    fill = bpy.context.object
    fill.data.energy = 500
    fill.data.size = 3.5
    aim(fill, (0, 0, 1.0))

    bpy.ops.object.light_add(type="AREA", location=(0.5, 3.8, 4.0))
    rim = bpy.context.object
    rim.data.energy = 800
    rim.data.size = 3.0
    aim(rim, (0, 0, 1.2))

    bpy.ops.object.camera_add(location=(4.8, -6.5, 3.25))
    cam = bpy.context.object
    aim(cam, (0, 0, 1.12))
    cam.data.lens = 58

    scene = bpy.context.scene
    scene.camera = cam
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = preview_size
    scene.render.resolution_y = preview_size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = True
    scene.world.color = (0.018, 0.024, 0.028)


g.build_unit = build_unit_zup
g.setup_stage = setup_stage_zup

g.main()
