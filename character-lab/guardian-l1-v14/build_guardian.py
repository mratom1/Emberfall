#!/usr/bin/env python3
"""Guardian L1 v14 — isolated character-lab build.

Goal: produce one original premium stylized human Guardian using a real rigged
mobile-ready knight base. The visual direction is informed by the three user
references (Javanese Blacksmith, PirateBum, Chibi_Karen): human male anatomy and
weight, layered outfit/boots/belts, and clean stylized hair/surface finish.
The main Emberfall game assets are not modified by this script.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


def args():
    import sys
    av = sys.argv
    av = av[av.index("--") + 1:] if "--" in av else []
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--preview-size", type=int, default=900)
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


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def world_bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def character_meshes():
    return [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render]


def clean_source_scene():
    for c in bpy.data.collections:
        c.hide_viewport = False
        c.hide_render = False
    for o in bpy.context.scene.objects:
        o.hide_set(False)
        o.hide_viewport = False
        o.hide_render = False
    # Source cameras/lights are not part of the finished game asset.
    for o in list(bpy.context.scene.objects):
        if o.type in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(o, do_unlink=True)


def normalize():
    meshes = character_meshes()
    if not meshes:
        raise RuntimeError("No character mesh found in source")
    root = bpy.data.objects.new("GuardianRoot", None)
    bpy.context.scene.collection.objects.link(root)
    source = [o for o in bpy.context.scene.objects if o != root and o.type in {"MESH", "ARMATURE", "EMPTY"}]
    source_set = set(source)
    for o in source:
        if o.parent not in source_set:
            mw = o.matrix_world.copy()
            o.parent = root
            o.matrix_world = mw
    bpy.context.view_layer.update()
    mn, mx = world_bbox(meshes)
    h = max(0.001, mx.z - mn.z)
    root.scale = (1.88 / h,) * 3
    bpy.context.view_layer.update()
    mn, mx = world_bbox(meshes)
    center = (mn + mx) * 0.5
    root.location += Vector((-center.x, -center.y, -mn.z))
    bpy.context.view_layer.update()
    return root


def hide_bad_headwear():
    hidden = []
    for o in bpy.context.scene.objects:
        n = o.name.lower()
        if o.type == "MESH" and any(k in n for k in ("helmet", "helm", "hat", "hood")):
            o.hide_render = True
            o.hide_viewport = True
            hidden.append(o.name)
    return hidden


def polish_existing_meshes():
    """Smooth real topology while keeping deformation-safe geometry."""
    for o in character_meshes():
        for p in o.data.polygons:
            p.use_smooth = True
        # Mild bevel for hard-surface pieces only.
        name = o.name.lower()
        if any(k in name for k in ("armor", "armour", "plate", "pauld", "boot", "gaunt", "shield")):
            if not any(m.type == "BEVEL" for m in o.modifiers):
                bev = o.modifiers.new("GuardianEdgePolish", "BEVEL")
                bev.width = 0.003
                bev.segments = 2


def restyle_materials():
    silver = mat("GuardianSilverV14", (0.48, 0.58, 0.72), 0.86, 0.18)
    darksilver = mat("GuardianDarkSteelV14", (0.075, 0.10, 0.16), 0.70, 0.24)
    gold = mat("GuardianGoldV14", (0.92, 0.57, 0.12), 0.83, 0.16)
    blue = mat("GuardianBlueV14", (0.025, 0.095, 0.36), 0.02, 0.37)
    blue2 = mat("GuardianBlueClothV14", (0.035, 0.19, 0.54), 0.0, 0.46)
    leather = mat("GuardianLeatherV14", (0.13, 0.045, 0.022), 0.0, 0.52)
    hair = mat("GuardianHairV14", (0.030, 0.014, 0.008), 0.0, 0.43)
    skin = mat("GuardianSkinV14", (0.46, 0.255, 0.175), 0.0, 0.50)

    report = []
    # Preserve unknown textured materials. Replace only clearly-classifiable pieces.
    for o in character_meshes():
        key = (o.name + " " + " ".join(m.name for m in o.data.materials if m)).lower()
        chosen = None
        if any(k in key for k in ("hair", "brow")):
            chosen = hair
        elif any(k in key for k in ("skin", "body", "face", "head", "hand")) and not any(k in key for k in ("armor", "armour", "helmet")):
            chosen = skin
        elif any(k in key for k in ("cloth", "cape", "tabard", "tunic", "shirt", "fabric")):
            chosen = blue2
        elif any(k in key for k in ("belt", "leather", "strap", "glove")):
            chosen = leather
        elif any(k in key for k in ("gold", "trim", "ornament", "crest", "emblem")):
            chosen = gold
        elif any(k in key for k in ("armor", "armour", "plate", "steel", "metal", "pauld", "greave", "gaunt", "boot")):
            chosen = silver
        if chosen:
            o.data.materials.clear()
            o.data.materials.append(chosen)
            report.append([o.name, chosen.name])
        else:
            report.append([o.name, "preserved-source"])
    return {"silver": silver, "darksilver": darksilver, "gold": gold, "blue": blue,
            "blue2": blue2, "leather": leather, "hair": hair, "skin": skin,
            "report": report}


def make_short_hair(material):
    """One continuous fitted short-hair mesh — no forehead strip, no bald gap."""
    cx, cy, cz = 0.0, 0.01, 1.735
    rx, ry, rz = 0.145, 0.122, 0.155
    rings, sides = 24, 96
    verts, faces = [], []
    for r in range(rings + 1):
        t = r / rings
        for i in range(sides):
            phi = 2 * math.pi * i / sides
            front = max(0.0, -math.sin(phi))
            side = abs(math.cos(phi))
            back = max(0.0, math.sin(phi))
            # Natural hairline: forehead slightly higher than temples/back.
            end_deg = 108.0 - 17.0 * front + 3.0 * side + 5.0 * back
            theta = math.radians(2.0 + (end_deg - 2.0) * t)
            st, ct = math.sin(theta), math.cos(theta)
            x = cx + rx * st * math.cos(phi)
            y = cy + ry * st * math.sin(phi)
            z = cz + rz * ct
            # Side-swept crown volume encoded directly into the shell.
            crown = max(0.0, 1.0 - t / 0.72)
            if front > 0.05:
                z += 0.020 * crown * (0.75 + 0.25 * max(0.0, -math.cos(phi)))
                x -= 0.012 * crown
            z += 0.0025 * math.sin(phi * 6 + t * 5) * (1.0 - 0.45 * t)
            verts.append((x, y, z))
    for r in range(rings):
        for i in range(sides):
            a = r*sides+i; b = r*sides+(i+1)%sides
            c = (r+1)*sides+(i+1)%sides; d = (r+1)*sides+i
            faces.append((a,b,c,d))
    me = bpy.data.meshes.new("GuardianHairV14Mesh")
    me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new("GuardianHairV14", me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(material)
    for p in me.polygons: p.use_smooth = True
    sol = o.modifiers.new("HairThickness", "SOLIDIFY"); sol.thickness = 0.008
    sub = o.modifiers.new("HairSmooth", "SUBSURF"); sub.levels = 1; sub.render_levels = 1
    return o


def prism(name, pts, yf, yb, material, bevel=0.012):
    verts = [(x,yf,z) for x,z in pts] + [(x,yb,z) for x,z in pts]
    n = len(pts)
    faces = [tuple(range(n)), tuple(range(n,2*n))[::-1]]
    for i in range(n): faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    me = bpy.data.meshes.new(name+"Mesh"); me.from_pydata(verts,[],faces); me.update()
    o = bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(o); o.data.materials.append(material)
    for p in me.polygons: p.use_smooth=True
    b=o.modifiers.new("Bevel","BEVEL"); b.width=bevel; b.segments=4
    return o


def add_guardian_identity(m):
    # Compact scarf / collar, closer to layered stylized references than a rigid ring.
    bpy.ops.mesh.primitive_torus_add(major_radius=.205, minor_radius=.034, major_segments=64, minor_segments=16,
                                    location=(0,-.005,1.52), rotation=(math.radians(7),0,0))
    scarf=bpy.context.object; scarf.name="GuardianScarfV14"; scarf.scale=(1.08,.80,.72); scarf.data.materials.append(m["blue2"])

    # Front tabard, narrow enough to preserve human leg readability.
    tab = [(-.105,1.02),(.105,1.02),(.090,.58),(0,.49),(-.090,.58)]
    prism("GuardianTabardV14",tab,-.145,-.125,m["blue"],.008)

    # Original noble kite shield at human scale.
    sh=[(-.19,1.39),(.19,1.39),(.225,1.20),(.145,.91),(0,.69),(-.145,.91),(-.225,1.20)]
    prism("GuardianShieldV14",[(x-.48,z) for x,z in sh],-.315,-.270,m["blue"],.017)
    inset=[(-.148,1.34),(.148,1.34),(.175,1.19),(.112,.94),(0,.76),(-.112,.94),(-.175,1.19)]
    prism("GuardianShieldGoldV14",[(x-.48,z) for x,z in inset],-.337,-.326,m["gold"],.009)

    # Elegant readable longsword.
    blade=[(.440,.92),(.500,.92),(.505,.35),(.470,.09),(.435,.35)]
    prism("GuardianSwordBladeV14",blade,-.125,-.105,m["silver"],.005)
    bpy.ops.mesh.primitive_cube_add(location=(.470,-.115,.955),scale=(.105,.018,.014))
    g=bpy.context.object; g.name="GuardianSwordGuardV14"; g.data.materials.append(m["gold"])
    bpy.ops.mesh.primitive_cube_add(location=(.470,-.115,1.045),scale=(.023,.022,.068))
    h=bpy.context.object; h.name="GuardianSwordGripV14"; h.data.materials.append(m["leather"])

    # Small chest crest: prestige without overdesigning L1.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=(0,-.205,1.34), scale=(.037,.014,.037))
    crest=bpy.context.object; crest.name="GuardianChestGemV14"; crest.data.materials.append(m["blue2"])


def find_bone(arm, groups):
    for pb in arm.pose.bones:
        n=pb.name.lower()
        if all(any(tok in n for tok in group) for group in groups):
            return pb
    return None


def pose_heroic():
    arms=[o for o in bpy.context.scene.objects if o.type=="ARMATURE"]
    if not arms: return []
    arm=max(arms,key=lambda x:len(x.pose.bones)); changed=[]
    def r(groups,xyz):
        b=find_bone(arm,groups)
        if not b:return
        b.rotation_mode="XYZ"; b.rotation_euler=tuple(math.radians(v) for v in xyz); changed.append(b.name)
    # Moderate asymmetry: shield-side braced, sword-side relaxed-ready.
    r((("upper","arm"),("l",)),(8,-4,-16)); r((("fore","arm"),("l",)),(10,0,-18))
    r((("upper","arm"),("r",)),(5,5,12)); r((("fore","arm"),("r",)),(8,0,10))
    r((("thigh",),("l",)),(0,0,-3)); r((("thigh",),("r",)),(0,0,4))
    r((("spine",),),(0,0,-2))
    bpy.context.view_layer.update(); return changed


def studio(size):
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE_NEXT"
    sc.render.resolution_x=size; sc.render.resolution_y=size; sc.render.resolution_percentage=100
    sc.render.image_settings.file_format="PNG"
    sc.view_settings.look="Medium High Contrast"
    world=bpy.data.worlds.get("World") or bpy.data.worlds.new("World"); sc.world=world; world.use_nodes=True
    world.node_tree.nodes["Background"].inputs["Color"].default_value=(.004,.008,.018,1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value=.22
    floor=mat("GuardianStudioFloor",(.020,.028,.045),.10,.30)
    bpy.ops.mesh.primitive_plane_add(size=18,location=(0,0,-.01)); bpy.context.object.data.materials.append(floor)
    def area(name,loc,energy,size_l,color):
        d=bpy.data.lights.new(name,"AREA"); d.energy=energy; d.shape="DISK"; d.size=size_l; d.color=color
        o=bpy.data.objects.new(name,d); sc.collection.objects.link(o); o.location=loc; look_at(o,(0,0,.95))
    area("Key",(3.0,-4.2,4.0),1250,3.2,(1,.82,.67)); area("Fill",(-3.2,-2.0,2.8),720,3.0,(.42,.60,1)); area("Rim",(1.1,3.0,3.2),1150,2.5,(.34,.54,1))
    cd=bpy.data.cameras.new("GuardianCamera"); cam=bpy.data.objects.new("GuardianCamera",cd); sc.collection.objects.link(cam); sc.camera=cam; cd.lens=72
    return cam


def render(out,size):
    cam=studio(size)
    for name,loc in {"front":(0,-4.7,1.82),"threequarter":(2.55,-4.25,1.90),"side":(4.45,-.05,1.82)}.items():
        cam.location=loc; look_at(cam,(0,-.01,.96)); bpy.context.scene.render.filepath=str(out/f"guardian-l1-{name}.png"); bpy.ops.render.render(write_still=True)


def export(out):
    skip={"GuardianCamera","Key","Fill","Rim"}
    for o in bpy.context.scene.objects:o.select_set(False)
    for o in bpy.context.scene.objects:
        if o.name in skip or o.name.startswith("Plane"): continue
        if o.type in {"MESH","ARMATURE","EMPTY"}: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out/"guardian-l1.glb"),export_format="GLB",use_selection=True,export_apply=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"guardian-l1.blend"))


def main():
    a=args(); out=Path(a.output).resolve(); out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(Path(a.source).resolve()))
    clean_source_scene(); normalize(); hidden=hide_bad_headwear(); polish_existing_meshes(); mats=restyle_materials()
    make_short_hair(mats["hair"]); add_guardian_identity(mats); posed=pose_heroic(); render(out,a.preview_size); export(out)
    meta={
      "unit":"guardian","level":1,"pass":"v14-isolated-character-lab",
      "references":[
        "Javanese Blacksmith (BlendSwap CC-BY 3.0) — human male anatomy/weight reference",
        "PirateBum (BlendSwap CC-BY 3.0) — outfit, belt, boots and silhouette reference",
        "Chibi_Karen (BlendSwap CC-BY 3.0) — clean stylized finish/hair reference only"
      ],
      "base_asset":"Cartoon Medieval Knight by Lucian Pavel, OpenGameArt, CC0, mobile optimized",
      "hidden_source_headwear":hidden,"pose_bones_changed":posed,"materials":mats["report"],
      "main_project_modified":False,"status":"review-required"
    }
    (out/"metadata.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print("GUARDIAN_L1_V14_COMPLETE")

if __name__=="__main__": main()
