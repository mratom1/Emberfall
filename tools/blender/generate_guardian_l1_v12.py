#!/usr/bin/env python3
"""Guardian L1 v12 — full original mobile-MOBA-quality rebuild.

This pass rebuilds the complete visible character in one shot from the Blender
Studio CC0 human base. It deliberately hides any imported hair/headwear, uses a
clean fitted human silhouette, adds one continuous dark-brown hairstyle with
swept strand curves, anatomical layered armor, human-scale weapons, cloth, boots,
and premium blue/silver/gold materials. No helmet is used at L1.
"""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

V8_PATH = Path(__file__).with_name("generate_guardian_l1_v8.py")
spec = importlib.util.spec_from_file_location("guardian_v8", V8_PATH)
v8 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(v8)


def mat(name, rgb, metallic=0.0, roughness=0.4):
    return v8.material(name, rgb, metallic, roughness)


def hide_imported_headwear(loaded):
    # L1 must show a clean human head and hairstyle, never a helmet/cap/headpiece.
    bad = ("hair", "helmet", "headwear", "hat", "cap", "hood")
    for o in loaded:
        low = o.name.lower()
        if any(k in low for k in bad):
            o.hide_render = True
            try:
                o.hide_set(True)
            except Exception:
                pass


def curve_lock(name, points, bevel, material):
    cu = bpy.data.curves.new(name + "Curve", "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 3
    cu.bevel_resolution = 4
    cu.bevel_depth = bevel
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, co in zip(sp.bezier_points, points):
        bp.co = co
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def hair_shell(material):
    # Closed continuous hair shell: full top/side/back coverage, natural hairline.
    cx, cy, cz = 0.0, 0.015, 1.758
    rx, ry, rz = 0.148, 0.126, 0.154
    rings, sides = 22, 112
    verts, faces = [], []
    for r in range(rings + 1):
        t = r / rings
        for i in range(sides):
            phi = 2.0 * math.pi * i / sides
            front = max(0.0, -math.sin(phi))
            back = max(0.0, math.sin(phi))
            theta_max = math.radians(101.0 - 10.0 * front + 7.0 * back)
            theta = math.radians(1.0) + (theta_max - math.radians(1.0)) * t
            st, ct = math.sin(theta), math.cos(theta)
            x = cx + rx * st * math.cos(phi)
            y = cy + ry * st * math.sin(phi)
            z = cz + rz * ct
            # Side-swept crown lift encoded into the shell, not a separate forehead strip.
            crown = max(0.0, 1.0 - t / 0.75)
            if y < -0.02:
                z += crown * (0.014 + 0.010 * max(0.0, -x / rx))
                x -= crown * 0.008
            verts.append((x, y, z))
    for r in range(rings):
        for i in range(sides):
            a = r*sides+i; b = r*sides+(i+1)%sides
            c = (r+1)*sides+(i+1)%sides; d = (r+1)*sides+i
            faces.append((a,b,c,d))
    me = bpy.data.meshes.new("GuardianHairShellMesh")
    me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new("GuardianHairShell", me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(material)
    v8.smooth(o, 2)
    sol = o.modifiers.new("HairThickness", "SOLIDIFY"); sol.thickness = 0.009

    # Groomed swept strands over the shell. These are intentional locks, not tiles.
    strand_specs = [
        [(-.120,-.060,1.785),(-.090,-.105,1.835),(-.035,-.118,1.872)],
        [(-.080,-.030,1.815),(-.050,-.105,1.862),( .010,-.120,1.884)],
        [(-.025,-.010,1.826),( .010,-.100,1.870),( .065,-.110,1.874)],
        [( .030, .000,1.815),( .065,-.080,1.850),( .105,-.092,1.846)],
        [( .090, .018,1.790),( .110,-.035,1.820),( .125,-.065,1.824)],
        [(-.135, .015,1.770),(-.145,-.015,1.790),(-.130,-.060,1.800)],
        [( .135, .020,1.770),( .145,-.005,1.790),( .132,-.050,1.800)],
    ]
    for i, pts in enumerate(strand_specs):
        curve_lock(f"GuardianHairLock.{i}", pts, 0.015 if i < 5 else 0.012, material)
    return o


def custom_panel(name, pts2d, y_front, depth, material, bevel=.010):
    verts = [(x, y_front, z) for x,z in pts2d] + [(x, y_front+depth, z) for x,z in pts2d]
    n = len(pts2d)
    faces = [tuple(range(n)), tuple(range(n,2*n))[::-1]]
    for i in range(n):
        faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    me=bpy.data.meshes.new(name+"Mesh"); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); o.data.materials.append(material)
    b=o.modifiers.new("Bevel","BEVEL"); b.width=bevel; b.segments=5
    v8.smooth(o,1)
    return o


def breastplate(silver, gold, blue):
    # Sculpted front plate shaped to ribcage/waist: narrow waist, broad upper chest.
    zs=[1.08,1.17,1.28,1.40,1.50,1.55]
    ws=[.180,.205,.235,.265,.255,.225]
    cols=[-1,-.55,0,.55,1]
    verts=[]
    for z,w in zip(zs,ws):
        for c in cols:
            x=c*w
            y=-.135 - .052*(1-c*c) - .010*max(0,z-1.35)/.2
            verts.append((x,y,z))
    faces=[]; nc=len(cols)
    for r in range(len(zs)-1):
        for c in range(nc-1):
            a=r*nc+c; b=a+1; d=(r+1)*nc+c; cc=d+1
            faces.append((a,b,cc,d))
    me=bpy.data.meshes.new("GuardianCuirassMeshV12"); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new("GuardianCuirassV12",me); bpy.context.collection.objects.link(o); o.data.materials.append(silver)
    sol=o.modifiers.new("Thickness","SOLIDIFY"); sol.thickness=.018
    bev=o.modifiers.new("EdgeSoftening","BEVEL"); bev.width=.012; bev.segments=5
    v8.smooth(o,1)
    # gold center motif and collar accents
    v8.box("CuirassSpine",(0,-.201,1.335),(.012,.009,.176),gold,.007)
    v8.uv("CuirassGem",(0,-.214,1.425),(.035,.012,.040),blue,28,14)
    for s in (-1,1):
        custom_panel(f"CollarWing.{s}",[(0,1.50),(s*.16,1.46),(s*.19,1.51),(s*.04,1.55)],-.160,.020,gold,.007)
    return o


def pauldron(side, silver, darksilver, gold):
    s=side
    pts=[(s*.300,1.515),(s*.370,1.565),(s*.455,1.525),(s*.445,1.455),(s*.360,1.430),(s*.305,1.465)]
    p=custom_panel(f"PauldronMain.{s}",pts,-.060,.095,silver,.015)
    pts2=[(s*.330,1.475),(s*.390,1.505),(s*.440,1.475),(s*.425,1.438),(s*.350,1.428)]
    custom_panel(f"PauldronLayer.{s}",pts2,-.085,.070,darksilver,.012)
    v8.box(f"PauldronGold.{s}",(s*.386,-.164,1.486),(.060,.010,.010),gold,.006,rot=(0,0,math.radians(-s*8)))
    return p


def tapered_tube(name,x,z_top,z_bottom,r_top,r_bottom,y,material,sides=42):
    verts=[]
    for z,r in ((z_top,r_top),(z_bottom,r_bottom)):
        for i in range(sides):
            a=2*math.pi*i/sides
            verts.append((x+r*math.cos(a),y+r*.80*math.sin(a),z))
    faces=[]
    for i in range(sides): faces.append((i,(i+1)%sides,(i+1)%sides+sides,i+sides))
    me=bpy.data.meshes.new(name+"Mesh"); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); o.data.materials.append(material)
    sol=o.modifiers.new("Thickness","SOLIDIFY"); sol.thickness=.009
    bev=o.modifiers.new("Bevel","BEVEL"); bev.width=.009; bev.segments=4
    v8.smooth(o,1)
    return o


def boot(side, leather, silver, gold):
    x=side*.145
    tapered_tube(f"BootShaft.{side}",x,.34,.10,.072,.080,-.005,leather,40)
    foot=v8.box(f"BootFoot.{side}",(x,-.105,.080),(.083,.135,.052),leather,.032)
    v8.uv(f"BootToe.{side}",(x,-.220,.080),(.082,.072,.050),leather,34,17)
    custom_panel(f"BootPlate.{side}",[(x-.065,.28),(x+.065,.28),(x+.055,.14),(x-.055,.14)],-.090,.018,silver,.008)
    v8.box(f"BootGold.{side}",(x,-.112,.285),(.050,.010,.009),gold,.005)
    return foot


def shield(blue,gold,silver):
    pts=[(-.19,.31),(.19,.31),(.225,.13),(.160,-.18),(0,-.35),(-.160,-.18),(-.225,.13)]
    fy,by=-.305,-.262
    verts=[]
    for y in (fy,by): verts += [(x-.49,y,z+1.07) for x,z in pts]
    n=len(pts); faces=[tuple(range(n)),tuple(range(n,2*n))[::-1]]
    for i in range(n): faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    me=bpy.data.meshes.new("GuardianShieldMeshV12"); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new("GuardianShield",me); bpy.context.collection.objects.link(o); o.data.materials.append(blue)
    b=o.modifiers.new("ShieldBevel","BEVEL"); b.width=.020; b.segments=6
    for i in range(n):
        p1=Vector((pts[i][0]-.49,fy-.018,pts[i][1]+1.07)); p2=Vector((pts[(i+1)%n][0]-.49,fy-.018,pts[(i+1)%n][1]+1.07))
        mid=(p1+p2)*.5; d=p2-p1
        e=v8.box(f"ShieldRim.{i}",mid,(0.008,.010,d.length*.5),gold,.005); e.rotation_euler[1]=math.atan2(d.x,d.z)
    v8.uv("ShieldCore",(-.49,fy-.038,1.11),(.045,.016,.045),gold,28,14)
    v8.box("ShieldStarV",(-.49,fy-.053,1.11),(.010,.008,.072),silver,.004)
    v8.box("ShieldStarH",(-.49,fy-.055,1.12),(.042,.008,.009),silver,.004,rot=(0,0,math.radians(-8)))
    return o


def sword(silver,gold,leather,blue):
    cx,cy=.470,-.115
    verts=[(cx-.028,cy-.009,.815),(cx+.028,cy-.009,.815),(cx+.038,cy-.009,.315),(cx,cy-.009,.095),(cx-.038,cy-.009,.315),
           (cx-.028,cy+.009,.815),(cx+.028,cy+.009,.815),(cx+.038,cy+.009,.315),(cx,cy+.009,.095),(cx-.038,cy+.009,.315)]
    faces=[(0,1,2,3,4),(9,8,7,6,5),(0,5,6,1),(1,6,7,2),(2,7,8,3),(3,8,9,4),(4,9,5,0)]
    me=bpy.data.meshes.new("GuardianSwordMeshV12"); me.from_pydata(verts,[],faces); me.update()
    blade=bpy.data.objects.new("GuardianSwordBlade",me); bpy.context.collection.objects.link(blade); blade.data.materials.append(silver)
    bb=blade.modifiers.new("BladeBevel","BEVEL"); bb.width=.005; bb.segments=3
    v8.box("SwordGuard",(cx,cy,.836),(.105,.018,.014),gold,.009)
    v8.box("SwordGrip",(cx,cy,.918),(.023,.023,.060),leather,.009)
    v8.uv("SwordGem",(cx,cy-.022,.838),(.018,.010,.018),blue,20,10)
    v8.uv("SwordPommel",(cx,cy,.993),(.031,.026,.031),gold,22,11)
    return blade


def add_full_guardian_v12():
    blue=mat("GuardianRoyalBlueV12",(.020,.095,.36),0,.34)
    blue_hi=mat("GuardianBlueClothV12",(.028,.18,.58),0,.42)
    navy=mat("GuardianNavyV12",(.018,.035,.075),0,.50)
    silver=mat("GuardianSilverV12",(.62,.70,.79),.88,.16)
    darksilver=mat("GuardianDarkSilverV12",(.12,.16,.23),.76,.22)
    gold=mat("GuardianGoldV12",(.95,.62,.14),.86,.15)
    leather=mat("GuardianLeatherV12",(.16,.050,.020),0,.48)
    hairmat=mat("GuardianHairV12",(.035,.014,.008),0,.50)

    hair_shell(hairmat)

    # fitted cloth foundation and blue scarf
    v8.loft("GuardianUnderTunicV12",[(.77,.178,.095,-.002),(.95,.195,.103,-.004),(1.12,.215,.112,-.006),(1.30,.238,.120,-.006),(1.47,.258,.128,-.002),(1.535,.262,.130,0)],blue_hi,64,.008)
    v8.uv("ScarfBack",(0,.020,1.605),(.180,.075,.040),blue,44,22)
    v8.uv("ScarfFront",(0,-.100,1.593),(.154,.030,.045),blue_hi,40,20)

    breastplate(silver,gold,blue_hi)
    v8.box("GuardianBelt",(0,-.135,1.00),(.210,.022,.030),leather,.014)
    v8.box("GuardianBuckle",(0,-.164,1.00),(.041,.017,.041),gold,.012)

    # noble front tabard
    custom_panel("FrontTabard",[(-.10,.965),(.10,.965),(.085,.62),(0,.55),(-.085,.62)],-.140,.016,blue,.010)
    v8.box("TabardTrim",(0,-.159,.635),(.067,.008,.009),gold,.004)

    for s in (-1,1):
        pauldron(s,silver,darksilver,gold)
        tapered_tube(f"Sleeve.{s}",s*.335,1.47,1.28,.078,.069,-.006,blue_hi,40)
        tapered_tube(f"Bracer.{s}",s*.452,1.14,.94,.066,.058,-.015,darksilver,38)
        v8.uv(f"Glove.{s}",(s*.463,-.022,.842),(.052,.046,.065),leather,32,16)
        tapered_tube(f"TrouserThigh.{s}",s*.145,.88,.57,.100,.082,.008,navy,42)
        tapered_tube(f"TrouserShin.{s}",s*.145,.58,.28,.080,.067,.004,navy,40)
        tapered_tube(f"Greave.{s}",s*.145,.59,.30,.071,.060,-.025,silver,40)
        v8.uv(f"KneeGuard.{s}",(s*.145,-.075,.602),(.055,.021,.043),gold,28,14)
        boot(s,leather,silver,gold)

    shield(blue,gold,silver)
    sword(silver,gold,leather,blue_hi)


def export_glb(out: Path):
    for o in bpy.context.scene.objects: o.select_set(False)
    for o in bpy.context.scene.objects:
        if o.name in {"StudioFloor","Camera","Key","Fill","Rim"}: continue
        if o.type in {'MESH','ARMATURE','EMPTY','CURVE'}: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out/'guardian-level-01.glb'),export_format='GLB',use_selection=True,export_apply=True)


def main():
    a=v8.parse_args(); out=Path(a.output).resolve(); out.mkdir(parents=True,exist_ok=True)
    v8.clear_scene()
    root, loaded=v8.append_human(Path(a.base_dir).resolve())
    hide_imported_headwear(loaded)
    add_full_guardian_v12()
    v8.render_views(out,a.preview_size)
    export_glb(out)
    if a.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'guardian-level-01.blend'))
    data={
        "unit":"guardian","level":1,"pass":"v12-full-moba-rebuild",
        "base":"Blender Studio Human Base Meshes v1.4.1 (CC0)",
        "goal":"original premium mobile-MOBA-quality human Guardian",
        "rules":["no helmet at L1","full natural hair coverage","fitted anatomical armor","human-scale shield and sword","complete visible character rebuilt together"]
    }
    (out/'metadata.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    print('GUARDIAN_L1_V12_COMPLETE')


if __name__=='__main__':
    main()
