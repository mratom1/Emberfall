#!/usr/bin/env python3
"""Guardian v5 — reference-matched smooth premium pass.

Goal: move the first Emberfall Army unit much closer to the approved Guardian
concept direction: long heroic proportions, clean blue/silver/gold armor,
large elegant kite shield, restrained sword, increasingly ornate equipment,
helmet/fur at late levels, and luminous prestige at L15.

The MakeHuman HM08 CC0 base mesh is used as a smooth anatomy under-mesh.
All Guardian armor, cloth, shield, weapon, progression and effects are original.
"""
from __future__ import annotations

import importlib.util
import math
import os
from pathlib import Path

import bpy
from mathutils import Vector, Matrix

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("guardian_v4", HERE / "generate_guardian_v4.py")
v4 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v4)
v3 = v4.v3

MH_PATH = Path(os.environ.get("MAKEHUMAN_BASE_OBJ", "/tmp/makehuman-base.obj"))
_BODY_CACHE = None


def materials(level):
    t = (level - 1) / 14.0
    M = v3.M
    blue = (0.020, 0.105 + .050*t, 0.34 + .08*t)
    royal = (0.018, 0.16 + .04*t, 0.48 + .08*t)
    steel = (.42 + .16*t, .48 + .15*t, .56 + .14*t)
    silver = (.67 + .12*t, .71 + .11*t, .78 + .10*t)
    gold = (.72 + .14*t, .45 + .10*t, .11 + .03*t)
    glow = (.025, .45 + .12*t, 1.0)
    return {
        "skin": M("Skin", (.64, .43, .30), 0, .43),
        "skin_hi": M("SkinWarm", (.76, .54, .39), 0, .40),
        "hair": M("Hair", (.055, .028, .018), 0, .50),
        "eye": M("Eye", (.86, .90, .92), 0, .18),
        "iris": M("Iris", (.025, .08, .12), 0, .16),
        "mouth": M("Mouth", (.15, .035, .028), 0, .50),
        "blue": M("RoyalBlue", blue, 0, .34),
        "blue_dark": M("RoyalBlueDark", (.010, .035, .11), 0, .44),
        "blue_light": M("RoyalBlueLight", royal, 0, .30),
        "steel": M("Steel", steel, .78, .20),
        "silver": M("Silver", silver, .82, .16),
        "darksteel": M("DarkSteel", (.09, .12, .18), .72, .22),
        "gold": M("Gold", gold, .82, .16),
        "gold_dark": M("GoldDark", (.34, .19, .045), .78, .20),
        "leather": M("Leather", (.19, .072, .026), 0, .54),
        "leather2": M("LeatherLight", (.34, .15, .055), 0, .49),
        "cloth": M("Cloth", blue, 0, .48),
        "cloth_dark": M("ClothDark", (.012, .04, .10), 0, .54),
        "whitefur": M("WhiteFur", (.89, .90, .92), 0, .66),
        "glow": M("AzureGlow", glow, .04, .10, glow, 1.1 + 1.8*t),
        "warmglow": M("WarmGlow", (1.0, .66, .18), .03, .10, (1.0, .50, .08), .9 + 1.7*t),
    }


def _load_body_geometry():
    global _BODY_CACHE
    if _BODY_CACHE is not None:
        return _BODY_CACHE
    if not MH_PATH.exists():
        return None

    verts = [None]
    faces = []
    group = ""
    with MH_PATH.open("r", encoding="utf-8", errors="ignore") as fh:
        for raw in fh:
            if raw.startswith("v "):
                _, x, y, z = raw.split()[:4]
                verts.append(Vector((float(x), -float(z), float(y))))
            elif raw.startswith("g "):
                group = raw.strip().split(maxsplit=1)[1]
            elif group == "body" and raw.startswith("f "):
                ids = [int(tok.split("/")[0]) for tok in raw.split()[1:]]
                if len(ids) >= 3:
                    faces.append(ids)

    used = sorted({i for f in faces for i in f})
    if not used:
        return None
    xs = [verts[i].x for i in used]
    ys = [verts[i].y for i in used]
    zs = [verts[i].z for i in used]
    cx = (min(xs) + max(xs)) * .5
    cy = (min(ys) + max(ys)) * .5
    zmin, zmax = min(zs), max(zs)
    scale = 2.255 / max(.001, zmax - zmin)

    mapped = {}
    for i in used:
        q = verts[i]
        p = Vector(((q.x - cx) * scale, (q.y - cy) * scale, (q.z - zmin) * scale))
        if p.z < 1.10:
            p.z *= 1.015
        if 1.05 < p.z < 1.72:
            p.y *= .92
        p.x *= 1.02

        if 1.02 < p.z < 1.78 and abs(p.x) > .28:
            side = 1.0 if p.x > 0 else -1.0
            shoulder = Vector((side * .31, 0.0, 1.62))
            reach = min(1.0, max(0.0, (abs(p.x) - .28) / .52))
            rot = Matrix.Rotation(side * math.radians(55.0), 4, 'Y')
            p = shoulder + rot @ (p - shoulder)
            if side < 0:
                p.y -= .13 * reach
                p.x -= .05 * reach
            else:
                p.y -= .055 * reach
                p.x += .07 * reach
        mapped[i] = p

    kept = []
    for f in faces:
        cz = sum(mapped[i].z for i in f) / len(f)
        if cz <= 1.84:
            kept.append(f)

    used2 = sorted({i for f in kept for i in f})
    idx = {old: n for n, old in enumerate(used2)}
    out_verts = [tuple(mapped[i]) for i in used2]
    out_faces = [tuple(idx[i] for i in f) for f in kept]
    _BODY_CACHE = (out_verts, out_faces)
    return _BODY_CACHE


def _base_anatomy(root, p):
    geo = _load_body_geometry()
    if not geo:
        return
    verts, faces = geo
    v3.mesh_obj("SmoothHumanUnderbody", verts, faces, p["blue_dark"], root, .0015, 1, True)


def build_body(root, p, level):
    _base_anatomy(root, p)
    v3.ring_body(
        "HeroTunic",
        [(1.03, .245, .145, .00), (1.17, .275, .16, -.005),
         (1.40, .325, .185, -.010), (1.61, .37, .205, .005),
         (1.73, .335, .18, .012)],
        p["blue"], root, 32, .0025, 2
    )
    v3.uv("ScarfFront", (0, -.165, 1.735), (.24, .052, .055), p["blue_light"], root, 32, 18, 1)
    v3.uv("ScarfBack", (0, .105, 1.735), (.25, .055, .062), p["blue_dark"], root, 32, 18, 1)
    v3.rounded_box("Belt", (0, -.010, 1.055), (.285, .155, .038), p["leather"], root, bevel=.028, subsurf=2)
    v3.rounded_box("Buckle", (0, -.170, 1.055), (.046, .014, .046), p["gold"], root, bevel=.014, subsurf=1)
    for s, lab in ((-1, "L"), (1, "R")):
        tab = v3.plate(
            f"Tabard.{lab}",
            [(s*.018, 1.03), (s*.18, 1.00), (s*.175, .55), (s*.085, .44), (s*.025, .52)],
            .020, p["cloth"], root, .012, 1
        )
        tab.location.y = -.175
    if level >= 2:
        for s, lab in ((-1, "L"), (1, "R")):
            v3.beam(f"TabardGold.{lab}", (s*.055, -.205, .53), (s*.145, -.205, .58), .011, .004, p["gold"], root)

    for s, lab in ((-1, "L"), (1, "R")):
        v3.uv(f"SleeveGuard.{lab}", (s*.37, -.015, 1.61), (.115, .085, .072), p["silver"], root, 28, 16, 1)
        if level >= 2:
            v3.uv(f"Pauldron.{lab}", (s*.415, -.035, 1.665), (.155 + .006*level, .105, .078), p["steel"], root, 32, 18, 1)
            v3.torus(f"PauldronRim.{lab}", (s*.415, -.135, 1.665), .105, .010, p["gold"], root, rot=(math.pi/2, 0, 0))

    if level >= 2:
        v3.ring_body(
            "Cuirass",
            [(1.18, .275, .17, -.020), (1.36, .325, .20, -.018),
             (1.57, .355, .215, -.012), (1.69, .315, .19, .00)],
            p["steel"], root, 32, .003, 1
        )
        front = v3.plate(
            "CuirassFront",
            [(-.24,1.62),(-.17,1.69),(0,1.72),(.17,1.69),(.24,1.62),
             (.20,1.35),(0,1.19),(-.20,1.35)],
            .040, p["silver"], root, .020, 1
        )
        front.location.y = -.205

    if level >= 3:
        for s, lab in ((-1, "L"), (1, "R")):
            hip = v3.plate(
                f"HipPlate.{lab}",
                [(s*.04,1.20),(s*.245,1.22),(s*.265,1.04),(s*.15,.94),(s*.055,1.00)],
                .028, p["steel"], root, .018, 1
            )
            hip.location.y = -.188

    if level >= 4:
        for s, lab in ((-1, "L"), (1, "R")):
            v3.uv(f"PauldronCap.{lab}", (s*.47, -.055, 1.69), (.145,.102,.062), p["silver"], root, 32, 18, 1)
            v3.beam(f"PauldronGold.{lab}", (s*.39,-.160,1.715),(s*.53,-.160,1.68), .012,.004,p["gold"],root)

    if level >= 5:
        crest = v3.plate("ChestGoldV",
            [(-.245,1.615),(0,1.455),(.245,1.615),(.17,1.67),(0,1.565),(-.17,1.67)],
            .018,p["gold"],root,.008,0)
        crest.location.y = -.265

    if level >= 6:
        v3.uv("ChestMedallion",(0,-.292,1.49),(.050,.012,.058),p["gold"],root,22,12,0)
    if level >= 8:
        v3.uv("ChestCore",(0,-.307,1.49),(.032,.007,.045),p["glow"],root,18,10,0)
    if level >= 10:
        for s, lab in ((-1, "L"), (1, "R")):
            v3.uv(f"ElitePauldron.{lab}", (s*.505,-.035,1.715),(.165,.115,.075),p["darksteel"],root,32,18,1)
            v3.cone(f"EliteFin.{lab}",(s*.615,-.020,1.76),.030,.003,.20,p["gold"],root,rot=(0,s*.70,0),vertices=16)
    if level >= 12:
        for s, lab in ((-1, "L"), (1, "R")):
            v3.uv(f"ShoulderRune.{lab}",(s*.49,-.158,1.685),(.028,.007,.034),p["glow"],root,16,8,0)
    if level >= 15:
        v3.torus("MasterChestRing",(0,-.320,1.49),.085,.008,p["warmglow"],root,rot=(math.pi/2,0,0))


def build_legs(root, p, level):
    for s, lab in ((-1, "L"), (1, "R")):
        v3.tube(f"Trouser.{lab}", [(s*.16,0,1.01),(s*.19,-.01,.75),(s*.20,-.02,.56)],
                [.112,.106,.086], p["cloth_dark"], root, 20, .002, 1)
        v3.rounded_box(f"BootShaft.{lab}",(s*.205,-.045,.245),(.100,.095,.155),p["leather"],root,bevel=.045,subsurf=2)
        v3.rounded_box(f"BootFoot.{lab}",(s*.205,-.155,.080),(.110,.185,.065),p["leather2"],root,rot=(.05,0,0),bevel=.045,subsurf=2)
        if level >= 3:
            v3.uv(f"KneePlate.{lab}",(s*.20,-.125,.605),(.090,.050,.065),p["silver"],root,26,14,1)
        if level >= 4:
            v3.rounded_box(f"Greave.{lab}",(s*.205,-.105,.37),(.090,.052,.165),p["steel"],root,bevel=.050,subsurf=2)
        if level >= 7:
            v3.beam(f"GreaveGold.{lab}",(s*.205,-.162,.47),(s*.208,-.162,.28),.009,.0038,p["gold"],root)
        if level >= 13:
            v3.uv(f"KneeRune.{lab}",(s*.20,-.177,.605),(.018,.005,.023),p["glow"],root,14,8,0)


def build_arms(root, p, level):
    right = [(.38,-.015,1.59),(.46,-.035,1.38),(.50,-.080,1.13)]
    left  = [(-.38,-.020,1.59),(-.47,-.095,1.40),(-.51,-.205,1.23)]
    for pts, lab in ((right,"R"),(left,"L")):
        v3.tube(f"ForearmSkin.{lab}", pts[1:], [.070,.052], p["skin"], root, 20, .002, 1)
        v3.uv(f"Hand.{lab}",pts[-1],(.054,.045,.058),p["skin_hi"],root,26,14,1)
        if level >= 4:
            mid=((pts[0][0]+pts[1][0])*.5,(pts[0][1]+pts[1][1])*.5,(pts[0][2]+pts[1][2])*.5)
            v3.uv(f"UpperArmArmor.{lab}",mid,(.086,.060,.112),p["steel"],root,26,14,1)
        if level >= 6:
            mid2=((pts[1][0]+pts[2][0])*.5,(pts[1][1]+pts[2][1])*.5,(pts[1][2]+pts[2][2])*.5)
            v3.tube(f"Bracer.{lab}",[pts[1],mid2],[.080,.068],p["silver"],root,18,.003,1)
        if level >= 11:
            v3.torus(f"WristRank.{lab}",pts[-1],.055,.006,p["gold"],root,rot=(math.pi/2,0,0))


def build_helmet(root, p, level):
    v4.build_head(root, p, level)
    if level < 11:
        return
    z = 2.075
    v3.uv("HelmBack",(0,.045,z+.085),(.168,.132,.140),p["darksteel"],root,34,20,1)
    v3.rounded_box("HelmBrow",(0,-.150,z+.108),(.145,.024,.027),p["silver"],root,bevel=.018,subsurf=2)
    v3.cone("CrownCrest",(0,.045,z+.34),.036,.004,.31,p["gold"],root,vertices=16)
    v3.cone("BlueCrest",(0,.050,z+.39),.030,.004,.26,p["blue_light"],root,vertices=16)
    for s,lab in ((-1,"L"),(1,"R")):
        cg=v3.plate(f"CheekGuard.{lab}",
            [(s*.10,z+.035),(s*.148,z+.010),(s*.128,z-.090),(s*.085,z-.120)],
            .026,p["silver"],root,.014,1); cg.location.y=-.128
    if level >= 12:
        for s,lab in ((-1,"L"),(1,"R")):
            v3.cone(f"HelmWing.{lab}",(s*.19,.025,z+.20),.027,.003,.24,p["gold"],root,rot=(0,s*.74,0),vertices=16)
            v3.cone(f"HelmFeather.{lab}",(s*.23,.035,z+.25),.018,.002,.20,p["silver"],root,rot=(0,s*.90,0),vertices=16)
    if level >= 14:
        v3.uv("HelmGem",(0,-.173,z+.115),(.023,.007,.032),p["glow"],root,16,8,0)


def build_cape(root, p, level):
    if level < 4:
        return
    rows, cols = (9, 9) if level >= 11 else (8, 8)
    length = .90 + .018*max(0, level-4)
    verts=[]; faces=[]
    for r in range(rows):
        t=r/(rows-1)
        z=1.66-t*length
        y=.16+.10*t+.025*math.sin(t*math.pi)
        half=.27+.13*t
        sweep=.10*t
        for c in range(cols):
            u=c/(cols-1)
            x=(u-.5)*2*half+sweep
            wave=.028*math.sin(u*math.pi*2+t*2.8)
            verts.append((x,y+wave,z+.018*math.cos(u*math.pi)))
    for r in range(rows-1):
        for c in range(cols-1):
            a=r*cols+c
            faces.append((a,a+1,a+1+cols,a+cols))
    cape=v3.mesh_obj("Cape",verts,faces,p["blue"],root,.002,2,True)
    sol=cape.modifiers.new("CapeThickness","SOLIDIFY"); sol.thickness=.014
    v3.rounded_box("CapeClasp",(0,.14,1.67),(.11,.030,.030),p["gold"],root,bevel=.018,subsurf=1)
    if level >= 11:
        for s,i in ((-1,0),(0,1),(1,2)):
            v3.uv(f"FurMantle.{i}",(s*.20,.10,1.69),(.205,.072,.070),p["whitefur"],root,28,16,1)


def _shield_pts(x,z,w,h):
    return [(x,z+h*.53),(x-w*.48,z+h*.30),(x-w*.43,z-h*.18),
            (x,z-h*.58),(x+w*.43,z-h*.18),(x+w*.48,z+h*.30)]


def build_shield(root, p, level):
    x,z=-.62,1.19
    w=.54+.012*max(0,level-2)+.010*max(0,level-10)
    h=1.05+.015*max(0,level-2)+.012*max(0,level-10)
    pts=_shield_pts(x,z,w,h)
    v3.extruded_poly("ShieldBody",pts,-.34,-.25,p["darksteel"],root,.035,2)
    v3.extruded_poly("ShieldGoldFrame",_shield_pts(x,z,w*.98,h*.98),-.370,-.345,p["gold"],root,.018,1)
    v3.extruded_poly("ShieldBlueFace",_shield_pts(x,z,w*.89,h*.89),-.392,-.374,p["blue"],root,.018,1)
    if level >= 2:
        v3.extruded_poly("ShieldSilverInset",_shield_pts(x,z,w*.82,h*.82),-.405,-.394,p["steel"],root,.010,1)
        v3.extruded_poly("ShieldBlueCore",_shield_pts(x,z,w*.75,h*.75),-.414,-.407,p["blue_light"],root,.008,1)

    v3.uv("ShieldBoss",(x,-.430,z+.035),(.058,.014,.076),p["gold"],root,22,12,1)
    for sx,sz,name in ((-.18,.18,"UL"),(.18,.18,"UR"),(-.16,-.20,"LL"),(.16,-.20,"LR")):
        if level >= 3:
            v3.beam("ShieldRay"+name,(x,-.434,z+.035),(x+sx*w,-.434,z+sz*h),.012,.005,p["gold"],root)
    if level >= 8:
        v3.uv("ShieldCrystal",(x,-.448,z+.035),(.034,.007,.053),p["glow"],root,18,10,0)
    if level >= 9:
        v3.torus("ShieldRune",(x,-.452,z+.035),.135,.008,p["glow"],root,rot=(math.pi/2,0,0))
    if level >= 11:
        for s,lab in ((-1,"L"),(1,"R")):
            v3.cone(f"ShieldCrown.{lab}",(x+s*w*.31,-.315,z+h*.43),.024,.002,.18,p["gold"],root,rot=(0,s*.46,0),vertices=16)
    if level >= 13:
        v3.torus("ShieldRune2",(x,-.456,z+.035),.205,.009,p["glow"],root,rot=(math.pi/2,.15,0))
    if level >= 15:
        v3.torus("ShieldMaster",(x,-.461,z+.035),.265,.010,p["warmglow"],root,rot=(math.pi/2,-.20,0))


def build_sword(root, p, level):
    hand=Vector((.50,-.080,1.13))
    grip=Vector((.56,-.090,1.00))
    start=Vector((.59,-.100,.96))
    end=Vector((.86,-.155,.20))
    v3.tube("SwordGrip",[hand,grip],[.026,.026],p["leather"],root,14,.0025,1)
    v3.beam("SwordGuard",(.44,-.105,1.045),(.67,-.105,1.045),.021,.014,p["gold"],root)
    width=.040+.0025*max(0,level-5)+.003*max(0,level-11)
    v3.blade("SwordBlade",start,end,width,p["silver"],root)
    v3.uv("SwordPommel",(.485,-.076,1.18),(.030,.020,.032),p["gold"],root,18,10,1)
    if level>=8:
        v3.uv("SwordGem",(.59,-.117,.94),(.017,.005,.022),p["glow"],root,14,8,0)
    if level>=10:
        v3.beam("SwordGoldSpine",(.62,-.120,.88),(.82,-.160,.32),.0055,.0035,p["gold"],root)
    if level>=14:
        v3.beam("SwordEnergy",(.63,-.126,.86),(.84,-.166,.28),.006,.003,p["glow"],root)
    if level>=15:
        v3.beam("SwordWarmEdge",(.635,-.130,.84),(.845,-.170,.27),.004,.0025,p["warmglow"],root)


def build_late_fx(root, p, level):
    if level >= 13:
        for s,lab in ((-1,"L"),(1,"R")):
            base=Vector((s*.38,.17,1.70))
            for i in range(3):
                tip=Vector((s*(.58+.08*i), .16+.02*i, 1.72+.12*i))
                v3.beam(f"EnergyFeather.{lab}.{i}",base,tip,.010-.001*i,.004,p["glow"],root)
    if level >= 14:
        v3.torus("BackRune",(0,.23,1.98),.30,.008,p["glow"],root,rot=(math.pi/2,0,0))
    if level >= 15:
        for s,lab in ((-1,"L"),(1,"R")):
            hub=Vector((s*.28,.19,1.73))
            for i in range(5):
                tip=Vector((s*(.62+.10*i), .20+.015*i, 1.70+.11*i))
                v3.beam(f"MasterWingBlue.{lab}.{i}",hub,tip,.012,.004,p["glow"],root)
                if i in (1,3,4):
                    v3.beam(f"MasterWingGold.{lab}.{i}",hub,tip+Vector((0,.006,.035)),.006,.003,p["warmglow"],root)
        v3.torus("BackHaloGold",(0,.24,2.03),.36,.010,p["warmglow"],root,rot=(math.pi/2,.16,0))
        v3.torus("GroundAura",(0,0,.045),.62,.012,p["glow"],root)


def stage(size):
    mn,mx=v3.bounds()
    center=(mn+mx)*.5
    center.z += .05
    height=mx.z-mn.z
    width=mx.x-mn.x
    bpy.ops.object.camera_add(location=(3.8,-8.8,2.75))
    cam=bpy.context.object
    cam.data.type='ORTHO'
    cam.data.ortho_scale=max(2.55,height*1.15,width*1.13)
    v3.aim(cam,center)
    scene=bpy.context.scene
    scene.camera=cam
    try:
        scene.render.engine='BLENDER_EEVEE_NEXT'
    except Exception:
        scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=size
    scene.render.resolution_y=size
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGBA'
    scene.render.film_transparent=True
    try:
        scene.view_settings.look='AgX - Medium High Contrast'
    except Exception:
        pass
    for name,loc,power,sz,col in [
        ("Key",(4.0,-5.4,6.2),1100,4.8,(1.0,.91,.80)),
        ("Fill",(-4.2,-3.4,4.0),430,4.0,(.52,.70,1.0)),
        ("BlueRim",(2.8,4.0,5.4),1250,3.2,(.34,.58,1.0)),
        ("GoldRim",(-3.2,2.8,4.6),680,3.0,(1.0,.62,.30)),
    ]:
        bpy.ops.object.light_add(type='AREA',location=loc)
        light=bpy.context.object
        light.name=name
        light.data.energy=power
        light.data.shape='DISK'
        light.data.size=sz
        light.data.color=col
        v3.aim(light,center)
    scene.world.color=(.004,.007,.014)
    try:
        scene.eevee.taa_render_samples=128
        scene.eevee.use_gtao=True
        scene.eevee.gtao_distance=3
        scene.eevee.gtao_factor=1.15
    except Exception:
        pass


LEVEL_CHANGE = {
    1:"Recruit — smooth heroic anatomy, royal-blue tunic, leather boots, simple sword and shield",
    2:"Silver cuirass and fuller pauldrons; layered shield trim",
    3:"Hip armor, knee plates and guardian shield emblem",
    4:"Broader polished pauldrons, greaves and first royal cape",
    5:"Gold chest V and stronger heraldic armor language",
    6:"Bracers and gold guardian medallion",
    7:"Longer cape and gold greave accents",
    8:"Azure chest/shield cores and sword gem",
    9:"Glowing shield rune and richer blue-gold contrast",
    10:"Elite pauldrons, fins and gold sword spine",
    11:"Open-face royal helmet, white mantle and crowned shield",
    12:"Winged helmet details and glowing shoulder runes",
    13:"Second shield rune, knee runes and blue energy feathers",
    14:"Back rune and enchanted sword edge",
    15:"Master Guardian — blue/gold energy wings, radiant halo and master shield"
}


v3.materials = materials
v3.build_body = build_body
v3.build_legs = build_legs
v3.build_arms = build_arms
v3.build_helmet = build_helmet
v3.build_cape = build_cape
v3.build_shield = build_shield
v3.build_sword = build_sword
v3.build_late_fx = build_late_fx
v3.stage = stage
v3.LEVEL_CHANGE = LEVEL_CHANGE

if __name__ == "__main__":
    v3.main()
