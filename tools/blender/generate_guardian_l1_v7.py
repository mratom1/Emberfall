#!/usr/bin/env python3
"""Guardian L1 v7 — human-proportion-first Blender pass.

Only Army #1 Guardian Level 1 is generated.
This pass deliberately prioritizes believable human anatomy and silhouette over
ornament. It uses Blender Studio Human Base Meshes (CC0), strongly preferring a
realistic/generic/average male base and avoiding the stylized body used by v6.
Armor is fitted to the body instead of replacing the body with oversized forms.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import bpy
from mathutils import Vector


def args():
    import sys
    av = sys.argv
    av = av[av.index("--") + 1:] if "--" in av else []
    p = argparse.ArgumentParser()
    p.add_argument("--base-dir", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--preview-size", type=int, default=768)
    p.add_argument("--save-blend", action="store_true")
    return p.parse_args(av)


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def material(name, rgb, metallic=0.0, roughness=0.4):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = roughness
    return m


def smooth(obj, subdiv=1):
    if obj.type != "MESH":
        return
    for p in obj.data.polygons:
        p.use_smooth = True
    if subdiv and len(obj.data.vertices) < 90000:
        s = obj.modifiers.new("Smooth", "SUBSURF")
        s.levels = subdiv
        s.render_levels = subdiv


def choose_natural_male(base_dir: Path):
    candidates = []
    for blend in sorted(base_dir.rglob("*.blend")):
        try:
            with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
                for col in src.collections:
                    low = col.lower()
                    if "male" not in low or "body" not in low:
                        continue
                    score = 100
                    if "real" in low:
                        score += 500
                    if "average" in low:
                        score += 420
                    if "generic" in low:
                        score += 360
                    if "athlet" in low:
                        score += 250
                    if "base" in low:
                        score += 80
                    if "styl" in low:
                        score -= 1000
                    candidates.append((score, blend, col))
        except Exception:
            pass
    if not candidates:
        raise RuntimeError("No male body collection found in Human Base Meshes bundle")

    candidates.sort(key=lambda x: (x[0], x[2]), reverse=True)
    score, blend, col_name = candidates[0]
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
        dst.collections = [col_name]
    col = bpy.data.collections.get(col_name)
    if col and col.name not in bpy.context.scene.collection.children:
        try:
            bpy.context.scene.collection.children.link(col)
        except RuntimeError:
            pass
    loaded = [o for o in bpy.data.objects if o not in before]
    if not loaded and col:
        loaded = list(col.all_objects)
    meshes = [o for o in loaded if o.type == "MESH" and not o.hide_render]
    if not meshes:
        raise RuntimeError(f"Selected base {col_name} has no visible meshes")

    root = bpy.data.objects.new("GuardianHumanRoot", None)
    bpy.context.collection.objects.link(root)
    loaded_set = set(loaded)
    for o in loaded:
        if o.parent not in loaded_set:
            mw = o.matrix_world.copy()
            o.parent = root
            o.matrix_world = mw

    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    h = max(0.001, mx.z - mn.z)
    scale = 1.90 / h
    root.scale = (scale, scale, scale)
    bpy.context.view_layer.update()

    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (mn + mx) * 0.5
    root.location += Vector((-center.x, -center.y, -mn.z))

    for o in meshes:
        smooth(o, 1)

    print("BASE_CANDIDATES:")
    for s, b, c in candidates[:8]:
        print(f"  {s:4d} :: {c}")
    print(f"GUARDIAN_V7_BASE: {blend.name} :: {col_name} :: score={score}")
    return root, loaded


def uv(name, loc, scl, mat, seg=40, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scl
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    smooth(o, 1)
    o.data.materials.append(mat)
    return o


def box(name, loc, scl, mat, bevel=0.02, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scl
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    b = o.modifiers.new("Bevel", "BEVEL")
    b.width = bevel
    b.segments = 4
    smooth(o, 1)
    o.data.materials.append(mat)
    return o


def loft(name, rings, mat, sides=48):
    verts, faces = [], []
    for z, rx, ry, yoff in rings:
        for i in range(sides):
            a = 2 * math.pi * i / sides
            verts.append((math.cos(a) * rx, yoff + math.sin(a) * ry, z))
    for r in range(len(rings)-1):
        for i in range(sides):
            a = r*sides+i; b = r*sides+(i+1)%sides
            c = (r+1)*sides+(i+1)%sides; d = (r+1)*sides+i
            faces.append((a,b,c,d))
    me = bpy.data.meshes.new(name+"Mesh")
    me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    o.data.materials.append(mat)
    smooth(o, 2)
    sol = o.modifiers.new("Thickness", "SOLIDIFY"); sol.thickness = 0.010
    return o


def add_fitted_equipment():
    blue = material("GuardianBlue", (0.025,0.12,0.42), 0.0, .42)
    blue_hi = material("GuardianBlueHi", (0.035,0.22,0.62), 0.0, .38)
    silver = material("GuardianSilver", (.62,.69,.76), .84, .18)
    gold = material("GuardianGold", (.90,.60,.14), .82, .17)
    leather = material("GuardianLeather", (.20,.065,.024), 0.0, .52)

    # Slim, body-following tunic. Waist stays visibly narrower than chest.
    loft("GuardianTunic", [
        (.73,.205,.115,-.005),
        (.90,.220,.125,-.008),
        (1.05,.235,.135,-.008),
        (1.22,.255,.145,-.005),
        (1.40,.285,.155,0.000),
        (1.52,.300,.160,0.004),
    ], blue_hi, 56)

    box("Belt", (0,-.145,.98), (.235,.025,.032), leather, .018)
    box("Buckle", (0,-.176,.98), (.040,.018,.040), gold, .016)

    # Small scarf, intentionally not a giant donut around the neck.
    uv("ScarfBack", (0,.02,1.59), (.205,.095,.050), blue, 44, 22)
    uv("ScarfFront", (0,-.105,1.575), (.175,.035,.055), blue_hi, 40, 20)

    # Compact pauldrons that preserve shoulder width and arm articulation.
    for s, lab in ((-1,"L"),(1,"R")):
        p = uv(f"Pauldron.{lab}", (s*.355,-.02,1.49), (.115,.090,.060), silver, 44, 22)
        p.rotation_euler[1] = math.radians(s*7)
        uv(f"PauldronTrim.{lab}", (s*.365,-.090,1.49), (.078,.020,.032), gold, 32, 16)
        uv(f"Bracer.{lab}", (s*.455,-.015,1.01), (.062,.055,.125), silver, 34, 17)
        uv(f"Glove.{lab}", (s*.470,-.020,.835), (.060,.052,.075), leather, 32, 16)

    # Narrow greaves/boots; keep the human calves/feet readable.
    for s, lab in ((-1,"L"),(1,"R")):
        uv(f"Greave.{lab}", (s*.155,-.025,.37), (.070,.060,.170), silver, 36, 18)
        uv(f"Boot.{lab}", (s*.155,-.075,.095), (.085,.135,.055), leather, 36, 18)

    # Human-scale kite shield next to left forearm, not covering the entire torso.
    pts = [(-.23,.33),(.23,.33),(.27,.14),(.18,-.20),(0,-.39),(-.18,-.20),(-.27,.14)]
    fy, by = -.30, -.255
    verts=[]
    for y in (fy,by):
        verts += [(x-.53,y,z+1.06) for x,z in pts]
    n=len(pts); faces=[tuple(range(n)),tuple(range(n,2*n))[::-1]]
    for i in range(n): faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    me=bpy.data.meshes.new("ShieldMesh"); me.from_pydata(verts,[],faces); me.update()
    sh=bpy.data.objects.new("GuardianShield",me); bpy.context.collection.objects.link(sh)
    sh.data.materials.append(blue)
    bv=sh.modifiers.new("ShieldBevel","BEVEL"); bv.width=.022; bv.segments=5
    smooth(sh,1)
    uv("ShieldBoss",(-.53,fy-.028,1.12),(.050,.016,.050),gold,28,14)

    # Sword hangs naturally from the right hand, blade pointing downward.
    cx, cy = .49, -.11
    verts=[
        (cx-.025,cy-.010,.78),(cx+.025,cy-.010,.78),(cx+.040,cy-.010,.26),(cx,cy-.010,.08),(cx-.040,cy-.010,.26),
        (cx-.025,cy+.010,.78),(cx+.025,cy+.010,.78),(cx+.040,cy+.010,.26),(cx,cy+.010,.08),(cx-.040,cy+.010,.26),
    ]
    faces=[(0,1,2,3,4),(9,8,7,6,5),(0,5,6,1),(1,6,7,2),(2,7,8,3),(3,8,9,4),(4,9,5,0)]
    me=bpy.data.meshes.new("SwordBladeMesh"); me.from_pydata(verts,[],faces); me.update()
    sw=bpy.data.objects.new("GuardianSwordBlade",me); bpy.context.collection.objects.link(sw)
    sw.data.materials.append(silver)
    bb=sw.modifiers.new("BladeBevel","BEVEL"); bb.width=.006; bb.segments=3
    box("SwordGuard",(cx,cy,.81),(.105,.020,.018),gold,.012)
    box("SwordGrip",(cx,cy,.90),(.025,.025,.070),leather,.012)
    uv("SwordPommel",(cx,cy,.985),(.037,.030,.037),gold,24,12)

    uv("ChestBadge",(0,-.180,1.32),(.040,.012,.050),gold,28,14)


def look_at(o, target):
    o.rotation_euler = (Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()


def studio(size):
    sc=bpy.context.scene
    sc.render.engine='BLENDER_EEVEE_NEXT'
    sc.render.resolution_x=size; sc.render.resolution_y=size; sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'; sc.view_settings.look='AgX - Medium High Contrast'
    world=bpy.data.worlds.new("World") if not bpy.data.worlds.get("World") else bpy.data.worlds["World"]
    sc.world=world; world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.006,.010,.020,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.32
    fm=material("Floor",(.035,.045,.060),.08,.36)
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,-.01)); bpy.context.object.data.materials.append(fm)
    bpy.context.object.name="StudioFloor"
    def area(name,loc,energy,size_l,color):
        d=bpy.data.lights.new(name,'AREA'); d.energy=energy; d.shape='DISK'; d.size=size_l; d.color=color
        o=bpy.data.objects.new(name,d); bpy.context.collection.objects.link(o); o.location=loc; look_at(o,(0,0,.95))
    area("Key",(3.4,-4.4,4.4),1050,3.8,(1,.84,.70))
    area("Fill",(-3.7,-2.4,3.0),650,3.2,(.50,.66,1))
    area("Rim",(1.2,3.2,3.5),1000,2.8,(.42,.62,1))
    cd=bpy.data.cameras.new("Camera"); c=bpy.data.objects.new("Camera",cd); bpy.context.collection.objects.link(c); sc.camera=c
    cd.lens=68
    return c


def render(out: Path, size: int):
    c=studio(size)
    for name,loc in {
        "front":(0,-4.6,1.82),
        "threequarter":(2.65,-4.3,1.95),
        "side":(4.55,-.10,1.82),
    }.items():
        c.location=loc; look_at(c,(0,-.01,.94))
        bpy.context.scene.render.filepath=str(out/f"guardian-l1-{name}.png")
        bpy.ops.render.render(write_still=True)


def export_glb(out: Path):
    for o in bpy.context.scene.objects: o.select_set(False)
    for o in bpy.context.scene.objects:
        if o.name in {"StudioFloor","Camera","Key","Fill","Rim"}: continue
        if o.type in {'MESH','ARMATURE','EMPTY'}: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out/'guardian-level-01.glb'), export_format='GLB', use_selection=True, export_apply=True)


def main():
    a=args(); out=Path(a.output).resolve(); out.mkdir(parents=True,exist_ok=True)
    clear(); choose_natural_male(Path(a.base_dir).resolve()); add_fitted_equipment(); render(out,a.preview_size); export_glb(out)
    if a.save_blend: bpy.ops.wm.save_as_mainfile(filepath=str(out/'guardian-level-01.blend'))
    (out/'metadata.json').write_text('''{\n  "unit":"guardian",\n  "level":1,\n  "pass":"v7-human-proportion-first",\n  "base":"Blender Studio Human Base Meshes v1.4.1 (CC0)",\n  "gate":"approve human anatomy before L2"\n}\n''',encoding='utf-8')
    print("GUARDIAN_L1_V7_COMPLETE")


if __name__ == '__main__':
    main()
