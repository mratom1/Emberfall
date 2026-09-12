#!/usr/bin/env python3
"""Guardian L1 v8 — majestic human knight pass.

Only Guardian Level 1 is generated. The body stays recognizably human; prestige
comes from fitted layered armor, cape, hair, materials, shield and sword rather
than oversized anatomy. Uses Blender Studio Human Base Meshes v1.4.1 (CC0).
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    import sys
    av = sys.argv
    av = av[av.index("--") + 1:] if "--" in av else []
    p = argparse.ArgumentParser()
    p.add_argument("--base-dir", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--preview-size", type=int, default=768)
    p.add_argument("--save-blend", action="store_true")
    return p.parse_args(av)


def clear_scene():
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
    if subdiv and len(obj.data.vertices) < 110000:
        s = obj.modifiers.new("GuardianSubsurf", "SUBSURF")
        s.levels = subdiv
        s.render_levels = subdiv


def bbox_world(meshes):
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def append_human(base_dir: Path):
    candidates = []
    for blend in sorted(base_dir.rglob("*.blend")):
        try:
            with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
                for col in src.collections:
                    low = col.lower()
                    if "male" not in low or "body" not in low:
                        continue
                    score = 0
                    if "real" in low: score += 1200
                    if "average" in low: score += 900
                    if "generic" in low: score += 760
                    if "athlet" in low: score += 540
                    if "base" in low: score += 150
                    if "styl" in low: score -= 1800
                    candidates.append((score, blend, col))
        except Exception:
            pass
    if not candidates:
        raise RuntimeError("No natural male body collection found")
    candidates.sort(key=lambda x: (x[0], x[2]), reverse=True)
    score, blend, col_name = candidates[0]
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
        dst.collections = [col_name]
    col = bpy.data.collections.get(col_name)
    if col:
        try:
            bpy.context.scene.collection.children.link(col)
        except RuntimeError:
            pass
    loaded = [o for o in bpy.data.objects if o not in before]
    if not loaded and col:
        loaded = list(col.all_objects)
    meshes = [o for o in loaded if o.type == "MESH" and not o.hide_render]
    if not meshes:
        raise RuntimeError(f"Base {col_name} has no visible mesh")

    root = bpy.data.objects.new("GuardianHumanRoot", None)
    bpy.context.collection.objects.link(root)
    loaded_set = set(loaded)
    for o in loaded:
        if o.parent not in loaded_set:
            mw = o.matrix_world.copy()
            o.parent = root
            o.matrix_world = mw

    bpy.context.view_layer.update()
    mn, mx = bbox_world(meshes)
    h = max(0.001, mx.z - mn.z)
    s = 1.88 / h
    root.scale = (s, s, s)
    bpy.context.view_layer.update()
    mn, mx = bbox_world(meshes)
    center = (mn + mx) * 0.5
    root.location += Vector((-center.x, -center.y, -mn.z))
    bpy.context.view_layer.update()

    # Preserve anatomy; only a tiny heroic vertical emphasis, not cartoon scaling.
    root.scale.z *= 1.015
    root.scale.x *= 0.995

    for o in meshes:
        smooth(o, 1)

    # Give skin-like material only to meshes that have no useful material.
    skin = material("GuardianSkin", (0.43, 0.235, 0.145), 0.0, 0.48)
    for o in meshes:
        if len(o.data.materials) == 0:
            o.data.materials.append(skin)

    print(f"GUARDIAN_V8_BASE: {blend.name} :: {col_name} :: score={score}")
    return root, loaded


def uv(name, loc, scl, mat, seg=48, rings=24, rot=(0,0,0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scl
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    smooth(o, 1)
    o.data.materials.append(mat)
    return o


def box(name, loc, scl, mat, bevel=0.02, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scl
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    b = o.modifiers.new("GuardianBevel", "BEVEL")
    b.width = bevel
    b.segments = 5
    smooth(o, 1)
    o.data.materials.append(mat)
    return o


def loft(name, rings, mat, sides=56, thickness=0.010):
    verts, faces = [], []
    for z, rx, ry, yoff in rings:
        for i in range(sides):
            a = 2 * math.pi * i / sides
            verts.append((math.cos(a)*rx, yoff + math.sin(a)*ry, z))
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
    sol = o.modifiers.new("GuardianThickness", "SOLIDIFY")
    sol.thickness = thickness
    return o


def cape_mesh(mat_blue, mat_gold):
    # Slightly curved royal cape, narrow at shoulders and opening toward calves.
    zs = [1.60, 1.38, 1.12, .84, .57, .34]
    half = [.24, .28, .34, .40, .43, .40]
    verts=[]
    for z,w in zip(zs,half):
        for x in (-w, w):
            y = 0.10 + (1.60-z)*0.06 + 0.018*(abs(x)/max(w,.001))
            verts.append((x,y,z))
    faces=[]
    for r in range(len(zs)-1):
        i=r*2; faces.append((i,i+1,i+3,i+2))
    me=bpy.data.meshes.new("GuardianCapeMesh"); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new("GuardianCape",me); bpy.context.collection.objects.link(o)
    o.data.materials.append(mat_blue)
    sol=o.modifiers.new("CapeThickness","SOLIDIFY"); sol.thickness=.012
    smooth(o,2)
    # gold edge accents on both sides
    for side in (-1,1):
        for i in range(len(zs)-1):
            z=(zs[i]+zs[i+1])*.5; w=(half[i]+half[i+1])*.5
            y=0.11+(1.60-z)*.06
            box(f"CapeGold.{side}.{i}",(side*w,y-.008,z),(.010,.012,(zs[i]-zs[i+1])*.48),mat_gold,.008)
    return o


def hair(mat_hair):
    # Clean swept heroic hair mass around the natural head, without hiding the face.
    uv("HairCrown", (0,.035,1.785), (.125,.105,.090), mat_hair, 44,22, rot=(math.radians(-8),0,0))
    for i,(x,y,z,sx,sy,sz,rz) in enumerate([
        (-.09,-.055,1.79,.060,.042,.090,-18),
        (-.035,-.085,1.82,.055,.035,.105,-6),
        (.035,-.080,1.82,.055,.035,.105,7),
        (.095,-.045,1.79,.060,.042,.090,18),
        (-.11,.025,1.75,.040,.045,.095,-22),
        (.11,.025,1.75,.040,.045,.095,22),
    ]):
        uv(f"HairLock.{i}",(x,y,z),(sx,sy,sz),mat_hair,36,18,rot=(0,math.radians(rz),0))


def shield(mat_blue, mat_gold, mat_silver):
    pts=[(-.24,.36),(.24,.36),(.29,.15),(.20,-.21),(0,-.43),(-.20,-.21),(-.29,.15)]
    fy,by=-.315,-.267
    verts=[]
    for y in (fy,by): verts += [(x-.52,y,z+1.06) for x,z in pts]
    n=len(pts); faces=[tuple(range(n)),tuple(range(n,2*n))[::-1]]
    for i in range(n): faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    me=bpy.data.meshes.new("GuardianShieldMesh"); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new("GuardianShield",me); bpy.context.collection.objects.link(o)
    o.data.materials.append(mat_blue)
    bv=o.modifiers.new("ShieldBevel","BEVEL"); bv.width=.025; bv.segments=6
    smooth(o,1)
    # controlled gold rim
    for i in range(n):
        p1=Vector((pts[i][0]-.52,fy-.020,pts[i][1]+1.06)); p2=Vector((pts[(i+1)%n][0]-.52,fy-.020,pts[(i+1)%n][1]+1.06))
        mid=(p1+p2)*.5; d=p2-p1
        e=box(f"ShieldRim.{i}",mid,(0.010,.014,d.length*.5),mat_gold,.007)
        e.rotation_euler[1]=math.atan2(d.x,d.z)
    uv("ShieldBoss",(-.52,fy-.038,1.12),(.055,.020,.055),mat_gold,32,16)
    uv("ShieldCore",(-.52,fy-.062,1.13),(.020,.010,.090),mat_silver,24,12)
    return o


def sword(mat_silver, mat_gold, mat_leather):
    cx,cy=.48,-.12
    verts=[
        (cx-.026,cy-.010,.80),(cx+.026,cy-.010,.80),(cx+.038,cy-.010,.28),(cx,cy-.010,.06),(cx-.038,cy-.010,.28),
        (cx-.026,cy+.010,.80),(cx+.026,cy+.010,.80),(cx+.038,cy+.010,.28),(cx,cy+.010,.06),(cx-.038,cy+.010,.28),
    ]
    faces=[(0,1,2,3,4),(9,8,7,6,5),(0,5,6,1),(1,6,7,2),(2,7,8,3),(3,8,9,4),(4,9,5,0)]
    me=bpy.data.meshes.new("GuardianSwordMesh"); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new("GuardianSwordBlade",me); bpy.context.collection.objects.link(o)
    o.data.materials.append(mat_silver)
    b=o.modifiers.new("BladeBevel","BEVEL"); b.width=.006; b.segments=3
    box("SwordGuard",(cx,cy,.825),(.115,.020,.018),mat_gold,.012)
    box("SwordGrip",(cx,cy,.925),(.025,.025,.070),mat_leather,.012)
    uv("SwordPommel",(cx,cy,1.015),(.038,.030,.038),mat_gold,24,12)


def add_majestic_armor():
    blue = material("GuardianRoyalBlue",(.025,.11,.40),0,.40)
    blue_hi = material("GuardianBlueCloth",(.035,.22,.62),0,.36)
    silver = material("GuardianSilver",(.66,.72,.80),.90,.15)
    silver_dark = material("GuardianDarkSilver",(.18,.22,.28),.78,.20)
    gold = material("GuardianGold",(.95,.64,.16),.86,.14)
    leather = material("GuardianLeather",(.18,.055,.020),0,.50)
    hair_mat = material("GuardianHair",(.055,.026,.016),0,.42)

    cape_mesh(blue, gold)
    hair(hair_mat)

    # Close-fitting blue under-tunic, human waist still visible.
    loft("GuardianUnderTunic",[
        (.76,.195,.105,-.002),(.92,.210,.115,-.005),(1.08,.225,.125,-.006),
        (1.25,.250,.140,-.004),(1.42,.278,.150,.000),(1.53,.286,.152,.002)
    ],blue_hi,60,.009)

    # Separate fitted chest cuirass: stronger silhouette without changing anatomy.
    loft("GuardianCuirass",[
        (1.12,.235,.145,-.016),(1.26,.265,.158,-.020),(1.40,.292,.166,-.016),(1.52,.285,.160,-.010)
    ],silver,60,.012)
    # center gold spine / emblem
    box("CuirassGoldCenter",(0,-.178,1.34),(.018,.014,.18),gold,.010)
    uv("ChestCrest",(0,-.205,1.43),(.052,.016,.060),gold,32,16)

    box("Belt",(0,-.150,1.00),(.235,.026,.034),leather,.018)
    box("Buckle",(0,-.182,1.00),(.046,.020,.046),gold,.016)

    # layered waist faulds, narrow and elegant
    for i,(x,z) in enumerate([(-.16,.90),(0,.88),(.16,.90)]):
        plate=box(f"Fauld.{i}",(x,-.145,z),(.075,.025,.115),silver_dark,.025,rot=(math.radians(4),0,math.radians(-x*18)))
        box(f"FauldGold.{i}",(x,-.175,z-.085),(.060,.012,.010),gold,.007)

    # neck scarf / cowl kept compact
    uv("ScarfBack",(0,.018,1.605),(.205,.095,.050),blue,44,22)
    uv("ScarfFront",(0,-.108,1.590),(.175,.034,.054),blue_hi,40,20)

    # elegant layered shoulders rather than giant balls
    for s,lab in ((-1,"L"),(1,"R")):
        p=uv(f"PauldronMain.{lab}",(s*.355,-.025,1.50),(.125,.090,.062),silver,48,24,rot=(0,math.radians(s*8),0))
        uv(f"PauldronLayer.{lab}",(s*.380,-.010,1.455),(.100,.078,.050),silver_dark,42,20,rot=(0,math.radians(s*10),0))
        uv(f"PauldronGold.{lab}",(s*.366,-.102,1.505),(.082,.019,.034),gold,34,17)
        uv(f"Bracer.{lab}",(s*.455,-.020,1.02),(.065,.056,.128),silver_dark,36,18)
        uv(f"BracerGold.{lab}",(s*.455,-.078,1.04),(.054,.014,.038),gold,28,14)
        uv(f"Glove.{lab}",(s*.468,-.018,.845),(.060,.052,.073),leather,34,17)

    # slim greaves and boots, preserving human leg shape
    for s,lab in ((-1,"L"),(1,"R")):
        uv(f"Greave.{lab}",(s*.155,-.030,.385),(.073,.060,.178),silver,40,20)
        uv(f"Knee.{lab}",(s*.155,-.092,.575),(.068,.028,.052),gold,32,16)
        uv(f"Boot.{lab}",(s*.155,-.082,.102),(.085,.138,.056),leather,38,19)

    shield(blue, gold, silver)
    sword(silver, gold, leather)


def look_at(o, target):
    o.rotation_euler = (Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()


def setup_studio(size):
    sc=bpy.context.scene
    sc.render.engine='BLENDER_EEVEE_NEXT'
    sc.render.resolution_x=size; sc.render.resolution_y=size; sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'; sc.view_settings.look='AgX - Medium High Contrast'
    world=bpy.data.worlds.new("GuardianWorld") if not bpy.data.worlds.get("GuardianWorld") else bpy.data.worlds["GuardianWorld"]
    sc.world=world; world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.006,.010,.020,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.28
    fm=material("Floor",(.030,.040,.055),.10,.34)
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,-.01)); floor=bpy.context.object; floor.name="StudioFloor"; floor.data.materials.append(fm)
    def area(name,loc,energy,size_l,color):
        d=bpy.data.lights.new(name,'AREA'); d.energy=energy; d.shape='DISK'; d.size=size_l; d.color=color
        o=bpy.data.objects.new(name,d); bpy.context.collection.objects.link(o); o.location=loc; look_at(o,(0,0,.98))
    area("Key",(3.5,-4.5,4.5),1150,3.8,(1,.83,.67))
    area("Fill",(-3.8,-2.4,3.1),700,3.2,(.47,.64,1))
    area("Rim",(1.3,3.3,3.7),1250,2.8,(.38,.58,1))
    cd=bpy.data.cameras.new("Camera"); c=bpy.data.objects.new("Camera",cd); bpy.context.collection.objects.link(c); sc.camera=c; cd.lens=70
    return c


def render_views(out: Path, size: int):
    c=setup_studio(size)
    for name,loc in {
        "front":(0,-4.75,1.86),
        "threequarter":(2.72,-4.45,1.98),
        "side":(4.65,-.10,1.86),
    }.items():
        c.location=loc; look_at(c,(0,-.01,.96))
        bpy.context.scene.render.filepath=str(out/f"guardian-l1-{name}.png")
        bpy.ops.render.render(write_still=True)


def export_glb(out: Path):
    for o in bpy.context.scene.objects: o.select_set(False)
    for o in bpy.context.scene.objects:
        if o.name in {"StudioFloor","Camera","Key","Fill","Rim"}: continue
        if o.type in {'MESH','ARMATURE','EMPTY'}: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out/'guardian-level-01.glb'), export_format='GLB', use_selection=True, export_apply=True)


def main():
    a=parse_args(); out=Path(a.output).resolve(); out.mkdir(parents=True,exist_ok=True)
    clear_scene()
    append_human(Path(a.base_dir).resolve())
    add_majestic_armor()
    render_views(out,a.preview_size)
    export_glb(out)
    if a.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'guardian-level-01.blend'))
    (out/'metadata.json').write_text('''{\n  "unit": "guardian",\n  "level": 1,\n  "pass": "v8-majestic-human",\n  "base": "Blender Studio Human Base Meshes v1.4.1 (CC0)",\n  "goal": "human-proportion premium majestic knight",\n  "status": "prototype-review-required"\n}\n''',encoding='utf-8')
    print("GUARDIAN_L1_V8_COMPLETE")

if __name__=='__main__':
    main()
