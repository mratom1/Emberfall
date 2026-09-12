#!/usr/bin/env python3
"""Guardian L1 v10 — full visual overhaul in one pass.

This pass fixes the entire visible character together instead of doing one isolated
part at a time. It keeps the natural Blender Studio CC0 male anatomy from v8, then
rebuilds hair, under-clothes, torso armor, shoulders, gloves, trousers, greaves,
boots, shield, sword and L1 silhouette as one coherent human knight.
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


def _mat(name, rgb, metallic=0.0, roughness=0.4):
    return v8.material(name, rgb, metallic, roughness)


def _hair_cap(mat_hair):
    """Continuous groomed short-hair shell: no scalp hole and no mushroom ring."""
    cx, cy, cz = 0.0, 0.022, 1.770
    rx, ry, rz = 0.132, 0.108, 0.137
    rings, sides = 14, 72
    verts, faces = [], []
    for r in range(rings + 1):
        t = r / rings
        theta = math.radians(2.0 + 96.0 * t)
        st, ct = math.sin(theta), math.cos(theta)
        for i in range(sides):
            phi = 2.0 * math.pi * i / sides
            x = cx + rx * st * math.cos(phi)
            y = cy + ry * st * math.sin(phi)
            z = cz + rz * ct
            # Front = -Y. Raise the hairline slightly in the center and taper at temples.
            front = max(0.0, -math.sin(phi))
            temple = abs(math.cos(phi))
            if t > 0.72:
                z += 0.010 * front - 0.005 * temple
            # Gentle side-part lift, not a central bald channel.
            if x < 0.015 and y < -0.025 and t < 0.72:
                z += 0.010 * (1.0 - t)
            verts.append((x, y, z))
    for r in range(rings):
        for i in range(sides):
            a = r*sides+i; b = r*sides+(i+1)%sides
            c = (r+1)*sides+(i+1)%sides; d = (r+1)*sides+i
            faces.append((a,b,c,d))
    me = bpy.data.meshes.new("GuardianHairCapMesh")
    me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new("GuardianHairCap", me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat_hair)
    v8.smooth(o, 2)
    sol = o.modifiers.new("HairThickness", "SOLIDIFY"); sol.thickness = 0.008

    # Small controlled swept fringe: deliberately subtle, never bubble-like.
    fringe = [
        (-.074,-.079,1.846,.050,.022,.032,-18),
        (-.026,-.092,1.854,.052,.021,.034,-8),
        (.028,-.090,1.850,.048,.020,.032,3),
        (.074,-.073,1.837,.043,.021,.030,14),
    ]
    for i,(x,y,z,sx,sy,sz,rz) in enumerate(fringe):
        lock = v8.uv(f"HairFringe.{i}",(x,y,z),(sx,sy,sz),mat_hair,36,18,
                     rot=(math.radians(-10),0,math.radians(rz)))
        lock.scale.z *= 0.78
    for side,lab in ((-1,"L"),(1,"R")):
        v8.uv(f"HairTemple.{lab}",(side*.112,-.046,1.748),(.021,.025,.051),mat_hair,30,15,
              rot=(0,math.radians(side*8),math.radians(side*6)))


def _curved_breastplate(mat_silver, mat_gold):
    """Anatomical tapered front cuirass, replacing the barrel/box chest."""
    zs = [1.095, 1.19, 1.31, 1.43, 1.515]
    widths = [.185, .205, .235, .255, .238]
    y_base = [-.135, -.140, -.145, -.142, -.133]
    cols = [-1.0,-.50,0.0,.50,1.0]
    verts=[]
    for z,w,y0 in zip(zs,widths,y_base):
        for c in cols:
            x = c*w
            bulge = .047*(1.0-c*c)
            y = y0 - bulge
            verts.append((x,y,z))
    faces=[]; nc=len(cols)
    for r in range(len(zs)-1):
        for c in range(nc-1):
            a=r*nc+c; b=a+1; d=(r+1)*nc+c; cc=d+1
            faces.append((a,b,cc,d))
    me=bpy.data.meshes.new("GuardianBreastplateMesh")
    me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new("GuardianBreastplate",me); bpy.context.collection.objects.link(o)
    o.data.materials.append(mat_silver)
    sol=o.modifiers.new("PlateThickness","SOLIDIFY"); sol.thickness=.022
    bev=o.modifiers.new("PlateBevel","BEVEL"); bev.width=.014; bev.segments=4
    v8.smooth(o,1)

    # Elegant center ridge and collar accents.
    v8.box("BreastplateRidge",(0,-.198,1.335),(.013,.010,.175),mat_gold,.008)
    v8.uv("GuardianChestCrest",(0,-.215,1.425),(.040,.012,.047),mat_gold,30,15)
    v8.box("BreastplateLowerTrim",(0,-.166,1.105),(.175,.012,.010),mat_gold,.007)
    return o


def _panel(name, x0, x1, z_top, z_bottom, y, mat, mat_trim=None):
    # Slightly tapered cloth/armor panel with thickness and rounded edges.
    top_half=(x1-x0)*.5; cx=(x0+x1)*.5
    bot_half=top_half*.72
    verts=[
        (cx-top_half,y,z_top),(cx+top_half,y,z_top),
        (cx+bot_half,y-.004,z_bottom),(cx-bot_half,y-.004,z_bottom),
    ]
    me=bpy.data.meshes.new(name+"Mesh"); me.from_pydata(verts,[],[(0,1,2,3)]); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); o.data.materials.append(mat)
    sol=o.modifiers.new("PanelThickness","SOLIDIFY"); sol.thickness=.012
    bev=o.modifiers.new("PanelBevel","BEVEL"); bev.width=.012; bev.segments=4
    v8.smooth(o,1)
    if mat_trim:
        v8.box(name+"Trim",(cx,y-.020,z_bottom+.018),(bot_half*.88,.010,.010),mat_trim,.006)
    return o


def _tapered_tube(name, x, z_top, z_bottom, r_top, r_bottom, y, mat, sides=40):
    verts=[]
    for z,r in ((z_top,r_top),(z_bottom,r_bottom)):
        for i in range(sides):
            a=2*math.pi*i/sides
            verts.append((x+r*math.cos(a), y+r*.82*math.sin(a), z))
    faces=[]
    for i in range(sides):
        faces.append((i,(i+1)%sides,(i+1)%sides+sides,i+sides))
    me=bpy.data.meshes.new(name+"Mesh"); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); o.data.materials.append(mat)
    sol=o.modifiers.new("TubeThickness","SOLIDIFY"); sol.thickness=.010
    bev=o.modifiers.new("TubeBevel","BEVEL"); bev.width=.010; bev.segments=3
    v8.smooth(o,1)
    return o


def _boot(name, x, mat_leather, mat_gold):
    # Proper boot: ankle shaft + foot/toe, covering the base feet instead of oval blobs.
    shaft=_tapered_tube(name+"Shaft",x,.36,.10,.075,.082,-.010,mat_leather,36)
    foot=v8.box(name+"Foot",(x,-.105,.085),(.090,.145,.055),mat_leather,.040,
                rot=(math.radians(-3),0,0))
    toe=v8.uv(name+"Toe",(x,-.225,.082),(.088,.080,.052),mat_leather,36,18)
    v8.box(name+"TopTrim",(x,-.012,.345),(.070,.012,.012),mat_gold,.007)
    return shaft,foot,toe


def _shield(mat_blue, mat_gold, mat_silver):
    # Reduced human-scale shield. Still heroic, no longer covering most of the body.
    pts=[(-.185,.285),(.185,.285),(.218,.12),(.150,-.165),(0,-.325),(-.150,-.165),(-.218,.12)]
    fy,by=-.315,-.270
    verts=[]
    for y in (fy,by): verts += [(x-.475,y,z+1.065) for x,z in pts]
    n=len(pts); faces=[tuple(range(n)),tuple(range(n,2*n))[::-1]]
    for i in range(n): faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    me=bpy.data.meshes.new("GuardianShieldMeshV10"); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new("GuardianShield",me); bpy.context.collection.objects.link(o); o.data.materials.append(mat_blue)
    bv=o.modifiers.new("ShieldBevel","BEVEL"); bv.width=.020; bv.segments=5
    v8.smooth(o,1)
    for i in range(n):
        p1=Vector((pts[i][0]-.475,fy-.018,pts[i][1]+1.065)); p2=Vector((pts[(i+1)%n][0]-.475,fy-.018,pts[(i+1)%n][1]+1.065))
        mid=(p1+p2)*.5; d=p2-p1
        e=v8.box(f"ShieldRimV10.{i}",mid,(0.008,.011,d.length*.5),mat_gold,.006)
        e.rotation_euler[1]=math.atan2(d.x,d.z)
    v8.uv("ShieldBoss",(-.475,fy-.034,1.105),(.043,.016,.043),mat_gold,28,14)
    # slim star/guardian mark
    v8.box("ShieldEmblemV",(-.475,fy-.050,1.105),(.010,.009,.074),mat_silver,.005)
    v8.box("ShieldEmblemH",(-.475,fy-.052,1.125),(.047,.009,.010),mat_silver,.005,rot=(0,0,math.radians(-8)))
    return o


def _sword(mat_silver, mat_gold, mat_leather):
    # Elegant hand-scale longsword with a readable blade and proper grip.
    cx,cy=.470,-.120
    verts=[
        (cx-.027,cy-.009,.805),(cx+.027,cy-.009,.805),(cx+.038,cy-.009,.315),(cx,cy-.009,.105),(cx-.038,cy-.009,.315),
        (cx-.027,cy+.009,.805),(cx+.027,cy+.009,.805),(cx+.038,cy+.009,.315),(cx,cy+.009,.105),(cx-.038,cy+.009,.315),
    ]
    faces=[(0,1,2,3,4),(9,8,7,6,5),(0,5,6,1),(1,6,7,2),(2,7,8,3),(3,8,9,4),(4,9,5,0)]
    me=bpy.data.meshes.new("GuardianSwordMeshV10"); me.from_pydata(verts,[],faces); me.update()
    blade=bpy.data.objects.new("GuardianSwordBlade",me); bpy.context.collection.objects.link(blade); blade.data.materials.append(mat_silver)
    b=blade.modifiers.new("BladeBevel","BEVEL"); b.width=.005; b.segments=3
    v8.box("SwordGuard",(cx,cy,.825),(.100,.018,.014),mat_gold,.010)
    v8.box("SwordGrip",(cx,cy,.905),(.023,.023,.062),mat_leather,.010)
    v8.uv("SwordPommel",(cx,cy,.982),(.031,.027,.031),mat_gold,22,11)
    return blade


def add_complete_guardian_v10():
    blue=_mat("GuardianRoyalBlueV10",(.026,.105,.36),0,.39)
    blue_hi=_mat("GuardianBlueClothV10",(.035,.205,.56),0,.42)
    navy=_mat("GuardianNavyClothV10",(.020,.045,.090),0,.48)
    silver=_mat("GuardianSilverV10",(.64,.70,.77),.86,.17)
    darksilver=_mat("GuardianDarkSilverV10",(.16,.20,.27),.74,.23)
    gold=_mat("GuardianGoldV10",(.92,.60,.14),.82,.16)
    leather=_mat("GuardianLeatherV10",(.145,.047,.020),0,.50)
    hairmat=_mat("GuardianHairV10",(.030,.016,.010),0,.44)

    # HAIR — one clean style, full coverage, small locks only.
    _hair_cap(hairmat)

    # CLOTH FOUNDATION — slim torso, sleeves and trousers so skin never reads unfinished.
    v8.loft("GuardianUnderTunicV10",[
        (.78,.180,.092,-.002),(.94,.195,.100,-.004),(1.10,.212,.108,-.006),
        (1.26,.232,.118,-.006),(1.42,.252,.125,-.002),(1.515,.260,.128,.000)
    ],blue_hi,60,.008)
    # short blue sleeves
    for s,lab in ((-1,"L"),(1,"R")):
        _tapered_tube(f"Sleeve.{lab}",s*.335,1.47,1.275,.080,.070,-.006,blue_hi,38)
        # dark fitted trousers: upper and lower legs
        _tapered_tube(f"TrouserThigh.{lab}",s*.145,.86,.56,.105,.085,.010,navy,42)
        _tapered_tube(f"TrouserShin.{lab}",s*.145,.58,.25,.082,.068,.005,navy,40)

    # TORSO ARMOR — curved/tapered breastplate, not a cylinder or rectangular barrel.
    _curved_breastplate(silver,gold)
    v8.box("GuardianBelt",(0,-.135,1.00),(.215,.022,.030),leather,.016)
    v8.box("GuardianBuckle",(0,-.163,1.00),(.041,.017,.041),gold,.014)

    # Tabard panels — give nobility without a giant L1 cape.
    _panel("FrontTabard",-.105,.105,.965,.62,-.142,blue,gold)
    _panel("BackTabard",-.115,.115,.955,.58,.090,blue,None)

    # Compact scarf/cowl with no donut silhouette.
    v8.uv("ScarfBack",(0,.025,1.600),(.176,.072,.039),blue,40,20)
    v8.uv("ScarfFront",(0,-.092,1.584),(.145,.026,.042),blue_hi,38,19)

    # SHOULDERS / ARMS — layered but human-scale.
    for s,lab in ((-1,"L"),(1,"R")):
        v8.uv(f"PauldronMain.{lab}",(s*.335,-.018,1.475),(.105,.073,.050),silver,42,21,
              rot=(0,math.radians(s*9),0))
        v8.uv(f"PauldronLayer.{lab}",(s*.360,-.004,1.435),(.080,.063,.038),darksilver,38,19,
              rot=(0,math.radians(s*11),0))
        v8.box(f"PauldronGoldBand.{lab}",(s*.348,-.082,1.480),(.050,.010,.010),gold,.006,
               rot=(0,0,math.radians(s*7)))
        # forearm bracer and glove sized to the human arm
        _tapered_tube(f"Bracer.{lab}",s*.445,1.105,.945,.060,.055,-.020,darksilver,36)
        v8.uv(f"Glove.{lab}",(s*.458,-.026,.842),(.052,.046,.065),leather,32,16)

    # LEGS / BOOTS — fitted greaves + actual boots, no disconnected oval blobs.
    for s,lab in ((-1,"L"),(1,"R")):
        _tapered_tube(f"Greave.{lab}",s*.145,.575,.285,.071,.061,-.028,silver,38)
        v8.uv(f"KneeGuard.{lab}",(s*.145,-.077,.594),(.056,.022,.043),gold,28,14)
        _boot(f"Boot.{lab}",s*.145,leather,gold)

    # EQUIPMENT — both rescaled to the human body.
    _shield(blue,gold,silver)
    _sword(silver,gold,leather)

    # Small prestige details only; L1 remains readable and not over-designed.
    v8.uv("BeltGem",(0,-.183,1.00),(.017,.010,.017),blue,20,10)


def main():
    # Replace the whole visual kit at once. This is intentionally not a one-part patch.
    v8.add_majestic_armor = add_complete_guardian_v10
    parsed=v8.parse_args()
    v8.main()
    out=Path(parsed.output).resolve()
    meta=out/"metadata.json"
    if meta.exists():
        data=json.loads(meta.read_text(encoding="utf-8"))
        data["pass"]="v10-full-visual-overhaul"
        data["goal"]="single-pass complete Guardian L1 visual fix"
        data["changes"]=[
            "continuous neat short hair",
            "curved anatomical breastplate",
            "covered fitted sleeves and trousers",
            "human-scale layered pauldrons/bracers",
            "proper greaves and boots",
            "smaller proportional shield",
            "rescaled elegant sword",
            "compact scarf and tabard instead of oversized cape"
        ]
        meta.write_text(json.dumps(data,indent=2),encoding="utf-8")
    print("GUARDIAN_L1_V10_COMPLETE")


if __name__=="__main__":
    main()
