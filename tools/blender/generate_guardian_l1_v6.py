#!/usr/bin/env python3
"""Guardian L1 v6 premium prototype.

This pass intentionally builds ONLY Army #1 Guardian Level 1.
It uses Blender Studio's official CC0 Human Base Meshes bundle as the anatomy
foundation, then adds original Emberfall blue/silver/gold Guardian equipment.
The goal is to validate a smooth premium hero-quality base before any L2-L15 work.
"""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    import sys
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--base-dir", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--preview-size", type=int, default=768)
    p.add_argument("--save-blend", action="store_true")
    return p.parse_args(argv)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        pass


def mat(name, color, metallic=0.0, roughness=0.4, emission=None, emission_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission_strength
        elif "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = (*emission, 1.0)
    return m


def smooth_object(obj, subdiv=1):
    if obj.type != "MESH":
        return
    for p in obj.data.polygons:
        p.use_smooth = True
    if subdiv > 0 and len(obj.data.vertices) < 120000:
        mod = obj.modifiers.new("GuardianSmooth", "SUBSURF")
        mod.levels = subdiv
        mod.render_levels = subdiv


def append_best_male_base(base_dir: Path):
    blend_files = sorted(base_dir.rglob("*.blend"))
    if not blend_files:
        raise RuntimeError(f"No .blend files found in {base_dir}")

    candidates = []
    for blend in blend_files:
        try:
            with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
                for col in src.collections:
                    low = col.lower()
                    if "body male" in low or ("male" in low and "body" in low):
                        score = 0
                        if "styl" in low:
                            score += 100
                        if "real" in low:
                            score += 60
                        if "generic" in low:
                            score += 40
                        if "body male" in low:
                            score += 20
                        candidates.append((score, blend, col))
        except Exception:
            continue

    if not candidates:
        # Fallback: inspect object names if no collection names matched.
        for blend in blend_files:
            try:
                with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
                    names = [n for n in src.objects if "male" in n.lower()]
                    if names:
                        dst.objects = names
                loaded = [o for o in bpy.data.objects if o.name in names]
                if loaded:
                    root = bpy.data.objects.new("GuardianAnatomyRoot", None)
                    bpy.context.collection.objects.link(root)
                    for o in loaded:
                        if o.parent is None:
                            o.parent = root
                    return root, loaded
            except Exception:
                continue
        raise RuntimeError("Could not find a male body asset in Blender Human Base Meshes bundle")

    candidates.sort(key=lambda x: (x[0], str(x[1]), x[2]), reverse=True)
    score, blend, collection_name = candidates[0]
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
        dst.collections = [collection_name]
    appended_col = bpy.data.collections.get(collection_name)
    if appended_col is None:
        raise RuntimeError(f"Failed to append collection {collection_name} from {blend}")
    if appended_col.name not in bpy.context.scene.collection.children:
        try:
            bpy.context.scene.collection.children.link(appended_col)
        except RuntimeError:
            pass
    loaded = [o for o in bpy.data.objects if o not in before and o.type in {"MESH", "ARMATURE", "EMPTY"}]
    if not loaded:
        loaded = list(appended_col.all_objects)

    root = bpy.data.objects.new("GuardianAnatomyRoot", None)
    bpy.context.collection.objects.link(root)
    loaded_set = set(loaded)
    for o in loaded:
        if o.parent not in loaded_set:
            mw = o.matrix_world.copy()
            o.parent = root
            o.matrix_world = mw

    bpy.context.view_layer.update()
    mesh_objs = [o for o in loaded if o.type == "MESH" and not o.hide_render]
    if not mesh_objs:
        raise RuntimeError("Male base collection contained no visible meshes")

    coords = []
    for o in mesh_objs:
        coords.extend([o.matrix_world @ Vector(corner) for corner in o.bound_box])
    mn = Vector((min(v.x for v in coords), min(v.y for v in coords), min(v.z for v in coords)))
    mx = Vector((max(v.x for v in coords), max(v.y for v in coords), max(v.z for v in coords)))
    height = max(0.001, mx.z - mn.z)
    scale = 2.02 / height
    root.scale = (scale, scale, scale)
    bpy.context.view_layer.update()

    coords = []
    for o in mesh_objs:
        coords.extend([o.matrix_world @ Vector(corner) for corner in o.bound_box])
    mn = Vector((min(v.x for v in coords), min(v.y for v in coords), min(v.z for v in coords)))
    mx = Vector((max(v.x for v in coords), max(v.y for v in coords), max(v.z for v in coords)))
    center = (mn + mx) * 0.5
    root.location.x -= center.x
    root.location.y -= center.y
    root.location.z -= mn.z

    for o in mesh_objs:
        smooth_object(o, subdiv=1)

    print(f"GUARDIAN_BASE: {blend.name} :: {collection_name} :: score={score}")
    return root, loaded


def add_uv(name, loc, scale, material, segments=48, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    smooth_object(o, 1)
    o.data.materials.append(material)
    return o


def add_beveled_box(name, loc, scale, material, bevel=0.05, rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rotation)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    b = o.modifiers.new("SoftBevel", "BEVEL")
    b.width = bevel
    b.segments = 5
    smooth_object(o, 1)
    o.data.materials.append(material)
    return o


def make_loft(name, rings, material, sides=48):
    verts = []
    faces = []
    for z, rx, ry, yoff in rings:
        for i in range(sides):
            a = 2.0 * math.pi * i / sides
            verts.append((math.cos(a)*rx, yoff + math.sin(a)*ry, z))
    for r in range(len(rings)-1):
        for i in range(sides):
            a = r*sides+i
            b = r*sides+(i+1)%sides
            c = (r+1)*sides+(i+1)%sides
            d = (r+1)*sides+i
            faces.append((a,b,c,d))
    mesh = bpy.data.meshes.new(name+"Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(material)
    smooth_object(o, 2)
    solid = o.modifiers.new("ClothThickness", "SOLIDIFY")
    solid.thickness = 0.014
    return o


def make_kite_shield(material_blue, material_gold, material_steel):
    # Convex, tapered kite shield with rounded/beveled thickness.
    front_y, back_y = -0.50, -0.43
    pts = [(-0.34,0.49), (0.34,0.49), (0.39,0.22), (0.27,-0.28), (0.0,-0.61), (-0.27,-0.28), (-0.39,0.22)]
    verts=[]
    for y in (front_y, back_y):
        verts += [(x-0.55, y, z+1.12) for x,z in pts]
    n=len(pts)
    faces=[tuple(range(n)), tuple(range(n,2*n))[::-1]]
    for i in range(n):
        faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    me=bpy.data.meshes.new("GuardianShieldMesh")
    me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new("GuardianShield",me); bpy.context.collection.objects.link(o)
    o.data.materials.append(material_blue)
    b=o.modifiers.new("ShieldBevel","BEVEL"); b.width=.035; b.segments=6
    smooth_object(o,1)

    # Gold border as slightly larger duplicate outline represented by tapered beams.
    border=[]
    for i in range(n):
        p1=Vector((pts[i][0]-0.55, front_y-0.018, pts[i][1]+1.12))
        p2=Vector((pts[(i+1)%n][0]-0.55, front_y-0.018, pts[(i+1)%n][1]+1.12))
        mid=(p1+p2)*.5; length=(p2-p1).length
        bpy.ops.mesh.primitive_cube_add(location=mid)
        e=bpy.context.object; e.name=f"ShieldGoldRim.{i}"
        e.scale=(.016,.018,length*.5)
        direction=p2-p1
        e.rotation_euler[1]=math.atan2(direction.x,direction.z)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        bv=e.modifiers.new("RimBevel","BEVEL"); bv.width=.012; bv.segments=4
        e.data.materials.append(material_gold); border.append(e)
    add_uv("ShieldBoss",(-0.55,front_y-0.045,1.23),(.075,.025,.075),material_gold,32,16)
    add_uv("ShieldStar",(-0.55,front_y-0.07,1.28),(.032,.010,.105),material_steel,24,12)
    return o


def make_sword(mat_silver, mat_gold, mat_leather):
    # Blade is a long tapered prism rather than a cylinder/needle.
    cx, cy = 0.56, -0.34
    verts=[
        (cx-.035,cy-.014,.54),(cx+.035,cy-.014,.54),(cx+.060,cy-.014,1.32),(cx,cy-.014,1.52),(cx-.060,cy-.014,1.32),
        (cx-.035,cy+.014,.54),(cx+.035,cy+.014,.54),(cx+.060,cy+.014,1.32),(cx,cy+.014,1.52),(cx-.060,cy+.014,1.32),
    ]
    faces=[(0,1,2,3,4),(9,8,7,6,5),(0,5,6,1),(1,6,7,2),(2,7,8,3),(3,8,9,4),(4,9,5,0)]
    me=bpy.data.meshes.new("GuardianBladeMesh"); me.from_pydata(verts,[],faces); me.update()
    blade=bpy.data.objects.new("GuardianSwordBlade",me); bpy.context.collection.objects.link(blade)
    blade.data.materials.append(mat_silver)
    be=blade.modifiers.new("BladeBevel","BEVEL"); be.width=.008; be.segments=3
    smooth_object(blade,1)
    add_beveled_box("SwordCrossguard",(cx,cy,.50),(.19,.035,.025),mat_gold,.02)
    add_beveled_box("SwordGrip",(cx,cy,.37),(.035,.035,.105),mat_leather,.025)
    add_uv("SwordPommel",(cx,cy,.245),(.055,.045,.055),mat_gold,24,12)
    # Rotate whole sword assembly into a relaxed outward angle around common origin.
    for o in [blade,bpy.data.objects.get("SwordCrossguard"),bpy.data.objects.get("SwordGrip"),bpy.data.objects.get("SwordPommel")]:
        if o:
            o.rotation_euler[1]=math.radians(-12)
    return blade


def add_guardian_equipment():
    blue=mat("Guardian Royal Blue",(0.025,0.12,0.43),0.05,.31)
    blue2=mat("Guardian Blue Cloth",(0.035,0.18,0.58),0.0,.46)
    steel=mat("Guardian Silver",(0.61,0.69,0.78),.86,.16)
    darksteel=mat("Guardian Dark Steel",(.10,.14,.20),.72,.20)
    gold=mat("Guardian Gold",(.92,.63,.16),.83,.15)
    leather=mat("Guardian Leather",(.22,.075,.025),0,.48)

    # Smooth fitted blue tunic around the high-quality body base.
    make_loft("GuardianTunic",[
        (.74,.27,.17,-.005),(.96,.30,.18,-.006),(1.18,.32,.19,-.004),(1.40,.35,.20,0.0),(1.58,.37,.205,.004)
    ],blue2,52)
    add_beveled_box("GuardianBelt",(0,-.205,1.00),(.30,.035,.045),leather,.035)
    add_beveled_box("GuardianBuckle",(0,-.245,1.00),(.055,.025,.055),gold,.025)

    # Scarf / cowl: three overlapping organic forms, not a hard ring.
    add_uv("ScarfCore",(0,-.015,1.67),(.285,.19,.085),blue2,48,24)
    add_uv("ScarfFront",(0,-.18,1.64),(.24,.055,.10),blue,40,20)
    tail=add_beveled_box("ScarfTail",(-.10,.06,1.39),(.11,.025,.27),blue2,.07,rotation=(math.radians(-8),0,math.radians(5)))

    # Curved pauldrons from flattened UV surfaces.
    for s,lab in ((-1,"L"),(1,"R")):
        pa=add_uv(f"Pauldron.{lab}",(s*.43,-.03,1.55),(.17,.13,.09),steel,48,24)
        pa.rotation_euler[1]=math.radians(s*8)
        rim=add_uv(f"PauldronGold.{lab}",(s*.45,-.13,1.56),(.12,.025,.052),gold,36,18)
        # Bracers and soft leather gloves.
        add_uv(f"Bracer.{lab}",(s*.50,-.04,1.05),(.09,.08,.16),darksteel,36,18)
        add_uv(f"Glove.{lab}",(s*.53,-.04,.86),(.085,.075,.10),leather,36,18)

    # Boots/greaves, shaped by overlapping ellipsoids instead of boxes.
    for s,lab in ((-1,"L"),(1,"R")):
        add_uv(f"BootShaft.{lab}",(s*.19,.00,.29),(.105,.105,.23),leather,40,20)
        foot=add_uv(f"BootFoot.{lab}",(s*.19,-.10,.095),(.115,.20,.075),leather,40,20)
        foot.rotation_euler[0]=math.radians(-5)
        add_uv(f"KneeGuard.{lab}",(s*.19,-.10,.57),(.10,.045,.075),steel,36,18)

    make_kite_shield(blue, gold, steel)
    make_sword(steel, gold, leather)

    # Small chest emblem with curved forms.
    add_uv("ChestBadge",(0,-.255,1.40),(.060,.018,.060),gold,32,16)
    add_uv("ChestBadgeCore",(0,-.278,1.40),(.023,.010,.075),steel,24,12)


def look_at(obj, target):
    direction=Vector(target)-obj.location
    obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()


def setup_scene(size):
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE_NEXT'
    scene.render.resolution_x=size
    scene.render.resolution_y=size
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.render.image_settings.color_mode='RGBA'
    scene.view_settings.look='AgX - Medium High Contrast'

    world=bpy.data.worlds.new("GuardianWorld") if bpy.data.worlds.get("GuardianWorld") is None else bpy.data.worlds["GuardianWorld"]
    scene.world=world
    world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.008,0.014,0.030,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.30

    floor_mat=mat("Floor",(.035,.045,.060),.15,.36)
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,-.01))
    floor=bpy.context.object; floor.name="StudioFloor"; floor.data.materials.append(floor_mat)

    # soft three-point lighting
    def area(name,loc,energy,size_l,color):
        data=bpy.data.lights.new(name,'AREA'); data.energy=energy; data.shape='DISK'; data.size=size_l; data.color=color
        o=bpy.data.objects.new(name,data); bpy.context.collection.objects.link(o); o.location=loc; look_at(o,(0,0,1.05)); return o
    area("Key",(3.5,-4.8,4.7),1150,4.0,(1.0,.82,.64))
    area("Fill",(-4.2,-2.5,3.2),750,3.5,(.48,.64,1.0))
    area("Rim",(1.0,3.6,4.0),1250,3.0,(.40,.58,1.0))

    camdata=bpy.data.cameras.new("Camera")
    cam=bpy.data.objects.new("Camera",camdata); bpy.context.collection.objects.link(cam); scene.camera=cam
    camdata.lens=62
    return cam


def render_views(out: Path, size: int):
    cam=setup_scene(size)
    views={
        "front":(0,-5.3,2.15),
        "threequarter":(3.25,-5.2,2.35),
        "side":(5.5,-.25,2.15),
    }
    for name,loc in views.items():
        cam.location=loc
        look_at(cam,(0,-.02,1.03))
        bpy.context.scene.render.filepath=str(out/f"guardian-l1-{name}.png")
        bpy.ops.render.render(write_still=True)


def export_glb(out: Path):
    # Exclude studio-only objects from export.
    for o in bpy.context.scene.objects:
        o.select_set(False)
    exportable=[]
    for o in bpy.context.scene.objects:
        if o.name in {"StudioFloor","Camera","Key","Fill","Rim"}:
            continue
        if o.type in {'MESH','ARMATURE','EMPTY'}:
            o.select_set(True); exportable.append(o)
    bpy.ops.export_scene.gltf(filepath=str(out/'guardian-level-01.glb'), export_format='GLB', use_selection=True, export_apply=True)


def main():
    args=parse_args()
    out=Path(args.output).resolve(); out.mkdir(parents=True,exist_ok=True)
    clear_scene()
    root, loaded=append_best_male_base(Path(args.base_dir).resolve())
    add_guardian_equipment()
    render_views(out,args.preview_size)
    export_glb(out)
    if args.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'guardian-level-01.blend'))
    (out/'metadata.json').write_text('''{\n  "unit": "guardian",\n  "level": 1,\n  "pass": "v6-premium-l1",\n  "base": "Blender Studio Human Base Meshes v1.4.1 (CC0)",\n  "status": "prototype-review-required"\n}\n''',encoding='utf-8')
    print("GUARDIAN_L1_V6_COMPLETE")


if __name__=='__main__':
    main()
