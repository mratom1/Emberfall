#!/usr/bin/env python3
"""Guardian L1 v13 — asset-based rebuild.

Uses a real CC0 rigged knight base instead of procedurally assembling the whole
character from primitive parts. The script opens the downloaded Knight.blend,
normalizes the character, applies an original blue/silver/gold Guardian art
pass, adds proportional custom shield/sword only if needed, sets a restrained
heroic pose when a compatible Rigify armature is present, and renders/export
reviews for approval.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    import sys
    av = sys.argv
    av = av[av.index("--") + 1:] if "--" in av else []
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--preview-size", type=int, default=768)
    return p.parse_args(av)


def mat(name, rgb, metallic=0.0, roughness=0.4):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    if bs:
        bs.inputs["Base Color"].default_value = (*rgb, 1.0)
        bs.inputs["Metallic"].default_value = metallic
        bs.inputs["Roughness"].default_value = roughness
    return m


def set_single_material(obj, material):
    if obj.type != "MESH":
        return
    obj.data.materials.clear()
    obj.data.materials.append(material)


def visible_meshes():
    return [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render]


def world_bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def unhide_everything():
    for c in bpy.data.collections:
        c.hide_viewport = False
        c.hide_render = False
    for o in bpy.context.scene.objects:
        o.hide_set(False)
        o.hide_viewport = False
        o.hide_render = False


def normalize_character():
    meshes = visible_meshes()
    if not meshes:
        raise RuntimeError("No visible meshes in source Knight.blend")

    # Parent top-level character objects under one root so scale/location remain coherent.
    root = bpy.data.objects.new("GuardianRoot", None)
    bpy.context.scene.collection.objects.link(root)
    source = [o for o in bpy.context.scene.objects if o != root and o.type in {"MESH", "ARMATURE", "EMPTY"}]
    sset = set(source)
    for o in source:
        if o.parent not in sset:
            mw = o.matrix_world.copy()
            o.parent = root
            o.matrix_world = mw

    bpy.context.view_layer.update()
    mn, mx = world_bbox(meshes)
    h = max(0.001, mx.z - mn.z)
    scale = 1.90 / h
    root.scale = (scale, scale, scale)
    bpy.context.view_layer.update()
    mn, mx = world_bbox(meshes)
    center = (mn + mx) * 0.5
    root.location += Vector((-center.x, -center.y, -mn.z))
    bpy.context.view_layer.update()
    return root


def classify_and_restyle():
    silver = mat("GuardianSilverV13", (0.52, 0.61, 0.72), 0.88, 0.18)
    dark = mat("GuardianDarkSteelV13", (0.075, 0.10, 0.15), 0.72, 0.24)
    gold = mat("GuardianGoldV13", (0.95, 0.60, 0.13), 0.82, 0.17)
    blue = mat("GuardianRoyalBlueV13", (0.025, 0.10, 0.38), 0.02, 0.37)
    leather = mat("GuardianLeatherV13", (0.16, 0.045, 0.018), 0.0, 0.50)
    skin = mat("GuardianSkinV13", (0.44, 0.245, 0.16), 0.0, 0.48)
    hair = mat("GuardianHairV13", (0.035, 0.016, 0.008), 0.0, 0.42)

    report = []
    for o in visible_meshes():
        low = (o.name + " " + " ".join(m.name for m in o.data.materials if m)).lower()
        chosen = None
        if any(k in low for k in ("hair", "brow")):
            chosen = hair
        elif any(k in low for k in ("skin", "body", "man", "head", "face", "hand")) and not any(k in low for k in ("armor", "armour", "helmet")):
            chosen = skin
        elif any(k in low for k in ("cloth", "cape", "tabard", "shirt", "tunic", "fabric")):
            chosen = blue
        elif any(k in low for k in ("leather", "belt", "strap", "boot", "glove")):
            chosen = leather
        elif any(k in low for k in ("gold", "trim", "ornament", "emblem", "crest")):
            chosen = gold
        elif any(k in low for k in ("armor", "armour", "plate", "metal", "steel", "iron", "helm", "guard", "greave", "pauldron")):
            chosen = silver

        if chosen:
            set_single_material(o, chosen)
            report.append((o.name, chosen.name))
        else:
            # Preserve original texture/material if classification is uncertain.
            report.append((o.name, "preserved"))

        # Clean smoothing on real mesh; do not deform with aggressive subdivision.
        for p in o.data.polygons:
            p.use_smooth = True

    return {"silver": silver, "dark": dark, "gold": gold, "blue": blue,
            "leather": leather, "skin": skin, "hair": hair, "report": report}


def bone_by_tokens(arm, tokens):
    for pb in arm.pose.bones:
        n = pb.name.lower()
        if all(t in n for t in tokens):
            return pb
    return None


def pose_if_possible():
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    if not arms:
        return []
    arm = max(arms, key=lambda a: len(a.pose.bones))
    changed = []

    def rot(tokens, xyz_deg):
        b = bone_by_tokens(arm, tokens)
        if not b:
            return
        b.rotation_mode = "XYZ"
        b.rotation_euler = tuple(math.radians(v) for v in xyz_deg)
        changed.append(b.name)

    # Restrained heroic stance. Values intentionally modest to avoid destroying unfamiliar rigs.
    rot(("upper_arm", ".l"), (8, -3, -18))
    rot(("forearm", ".l"), (10, 0, -18))
    rot(("upper_arm", ".r"), (5, 5, 14))
    rot(("forearm", ".r"), (12, 0, 12))
    rot(("thigh", ".l"), (0, 0, -3))
    rot(("thigh", ".r"), (0, 0, 4))
    rot(("spine",), (0, 0, -2))
    bpy.context.view_layer.update()
    return changed


def make_prism(name, pts2d, y_front, y_back, material, bevel=0.018):
    verts = [(x, y_front, z) for x, z in pts2d] + [(x, y_back, z) for x, z in pts2d]
    n = len(pts2d)
    faces = [tuple(range(n)), tuple(range(n, 2*n))[::-1]]
    for i in range(n):
        faces.append((i, (i+1)%n, (i+1)%n+n, i+n))
    me = bpy.data.meshes.new(name + "Mesh")
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(material)
    bv = o.modifiers.new("Bevel", "BEVEL")
    bv.width = bevel
    bv.segments = 5
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def ensure_guardian_equipment(mats):
    names = " ".join(o.name.lower() for o in bpy.context.scene.objects)
    if "shield" not in names:
        pts = [(-.18,.28),(.18,.28),(.215,.12),(.145,-.16),(0,-.33),(-.145,-.16),(-.215,.12)]
        shield = make_prism("GuardianShield", [(x-.50, z+1.05) for x,z in pts], -.32, -.275, mats["blue"], .018)
        # gold border as inset duplicate slightly forward
        rim = make_prism("GuardianShieldGoldInset", [(x-.50, z+1.05) for x,z in [(-.145,.235),(.145,.235),(.175,.105),(.118,-.125),(0,-.265),(-.118,-.125),(-.175,.105)]], -.342, -.334, mats["gold"], .010)
        rim.scale.x = 0.98
    if not any(k in names for k in ("sword", "blade")):
        # Clean longsword; custom equipment is acceptable here because the body/armor are asset-based.
        blade_pts = [(.445,.79),(.495,.79),(.505,.30),(.470,.08),(.435,.30)]
        make_prism("GuardianSwordBlade", blade_pts, -.130, -.112, mats["silver"], .006)
        bpy.ops.mesh.primitive_cube_add(location=(.470,-.121,.825), scale=(.105,.018,.015))
        guard = bpy.context.object; guard.name="GuardianSwordGuard"; guard.data.materials.append(mats["gold"])
        bpy.ops.mesh.primitive_cube_add(location=(.470,-.121,.915), scale=(.024,.024,.065))
        grip = bpy.context.object; grip.name="GuardianSwordGrip"; grip.data.materials.append(mats["leather"])


def look_at(o, target):
    o.rotation_euler = (Vector(target) - o.location).to_track_quat("-Z", "Y").to_euler()


def setup_studio(size):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.render.resolution_x = size
    sc.render.resolution_y = size
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.look = "AgX - Medium High Contrast"

    # Remove source cameras/lights only; preserve the actual character.
    for o in list(sc.objects):
        if o.type in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(o, do_unlink=True)

    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    sc.world = world; world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006,0.010,0.020,1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.28

    floor_mat = mat("GuardianFloorV13", (0.028,0.037,0.052), 0.15, 0.32)
    bpy.ops.mesh.primitive_plane_add(size=18, location=(0,0,-.01))
    floor = bpy.context.object; floor.name="StudioFloor"; floor.data.materials.append(floor_mat)

    def area(name, loc, energy, size_l, color):
        d = bpy.data.lights.new(name, "AREA"); d.energy=energy; d.shape="DISK"; d.size=size_l; d.color=color
        o = bpy.data.objects.new(name, d); sc.collection.objects.link(o); o.location=loc; look_at(o,(0,0,.95))

    area("Key", (3.2,-4.4,4.2), 1200, 3.4, (1.0,.83,.68))
    area("Fill", (-3.4,-2.1,3.0), 700, 3.0, (.48,.64,1.0))
    area("Rim", (1.1,3.0,3.4), 1100, 2.6, (.35,.56,1.0))

    cd = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cd.lens = 70
    return cam


def render_views(out, size):
    cam = setup_studio(size)
    views = {
        "front": (0,-4.7,1.85),
        "threequarter": (2.70,-4.35,1.95),
        "side": (4.55,-.10,1.85),
    }
    for name, loc in views.items():
        cam.location = loc
        look_at(cam, (0,-.01,.96))
        bpy.context.scene.render.filepath = str(out / f"guardian-l1-{name}.png")
        bpy.ops.render.render(write_still=True)


def export(out):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in bpy.context.scene.objects:
        if o.name in {"StudioFloor","Camera","Key","Fill","Rim"}:
            continue
        if o.type in {"MESH","ARMATURE","EMPTY"}:
            o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out / "guardian-level-01.glb"), export_format="GLB", use_selection=True, export_apply=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "guardian-level-01.blend"))


def main():
    a = parse_args()
    out = Path(a.output).resolve(); out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(Path(a.source).resolve()))
    unhide_everything()
    normalize_character()
    mats = classify_and_restyle()
    posed = pose_if_possible()
    ensure_guardian_equipment(mats)
    render_views(out, a.preview_size)
    export(out)

    metadata = {
        "unit": "guardian",
        "level": 1,
        "pass": "v13-asset-based-rebuild",
        "base_asset": "Knight (Rigged - Mid Poly) by crownjoshua, OpenGameArt, CC0",
        "source_url": "https://opengameart.org/sites/default/files/Knight_0.blend",
        "goal": "original premium mobile-MOBA-inspired Guardian using real rigged knight topology instead of primitive-built anatomy",
        "pose_bones_changed": posed,
        "materials": mats["report"],
        "status": "review-required"
    }
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print("GUARDIAN_L1_V13_COMPLETE")


if __name__ == "__main__":
    main()
