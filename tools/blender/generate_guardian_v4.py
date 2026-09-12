#!/usr/bin/env python3
"""Guardian v4 premium pass.

Uses the CC0 MakeHuman HM08 BODY topology only as a facial/head base, while the
armor, clothing, shield, sword, cape, progression and overall Guardian design
remain original Emberfall work. This avoids the primitive/bobble-head look of
procedural spheres and gives the first Army unit a much smoother mobile-MOBA
quality silhouette.

Expected env var in CI: MAKEHUMAN_BASE_OBJ=/tmp/makehuman-base.obj
The MakeHuman core base mesh is explicitly CC0.
"""
from __future__ import annotations

import importlib.util
import math
import os
from pathlib import Path

import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("guardian_v3",HERE/"generate_guardian_v3.py")
v3=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(v3)

MH_PATH=Path(os.environ.get("MAKEHUMAN_BASE_OBJ","/tmp/makehuman-base.obj"))
_HEAD_CACHE=None


def _load_makehuman_head_geometry():
    """Parse only faces in OBJ group 'body', then crop to head/upper-neck.

    MakeHuman OBJ coordinates are X(horizontal), Y(vertical), Z(depth). We map
    them to Blender X, -Y(depth), Z(vertical), then normalize into our Guardian
    proportions. No helper/joint geometry is imported.
    """
    global _HEAD_CACHE
    if _HEAD_CACHE is not None:return _HEAD_CACHE
    if not MH_PATH.exists():
        _HEAD_CACHE=None;return None
    verts=[None]
    body_faces=[]
    group=""
    with MH_PATH.open("r",encoding="utf-8",errors="ignore") as f:
        for raw in f:
            if raw.startswith("v "):
                _,x,y,z=raw.split()[:4];verts.append((float(x),float(y),float(z)))
            elif raw.startswith("g "):
                group=raw.strip().split(maxsplit=1)[1]
            elif group=="body" and raw.startswith("f "):
                ids=[]
                for tok in raw.split()[1:]:
                    ids.append(int(tok.split('/')[0]))
                if len(ids)>=3:body_faces.append(ids)
    used_all={i for f in body_faces for i in f}
    ys=[verts[i][1] for i in used_all]
    ymin,ymax=min(ys),max(ys)
    # Top ~22% of full body: head plus a short neck, not chest/shoulders.
    cut=ymin+(ymax-ymin)*.775
    head_faces=[f for f in body_faces if min(verts[i][1] for i in f)>=cut]
    used=sorted({i for f in head_faces for i in f})
    if not used:return None
    # Raw mapped coordinates before scale.
    rawpts={i:Vector((verts[i][0],-verts[i][2],verts[i][1])) for i in used}
    xs=[rawpts[i].x for i in used];ys2=[rawpts[i].y for i in used];zs=[rawpts[i].z for i in used]
    cx=(min(xs)+max(xs))/2;cy=(min(ys2)+max(ys2))/2;z0=min(zs);z1=max(zs)
    scale=.455/max(.001,z1-z0)
    # Normalize head to neck base 1.80 and top around 2.255.
    mapped=[];index={}
    for new_i,old_i in enumerate(used):
        q=rawpts[old_i]
        x=(q.x-cx)*scale
        y=(q.y-cy)*scale
        z=1.80+(q.z-z0)*scale
        frac=(z-1.80)/.455
        # Subtle stylization: stronger jaw, slightly narrower cranium.
        if frac<.43:x*=1.055
        elif frac>.70:x*=.965
        y*=.96
        mapped.append((x,y,z));index[old_i]=new_i
    faces=[tuple(index[i] for i in f) for f in head_faces]
    _HEAD_CACHE=(mapped,faces)
    return _HEAD_CACHE


def _fallback_head(root,p,level):
    return v3.build_head(root,p,level)


def build_head(root,p,level):
    geo=_load_makehuman_head_geometry()
    if not geo:return _fallback_head(root,p,level)
    verts,faces=geo
    head=v3.mesh_obj("HumanHead",verts,faces,p["skin_hi"],root,.0015,1,True)
    # Proper eyeballs/irises at the MakeHuman face plane. They are intentionally
    # restrained so the face reads mature rather than toy-like.
    for s,l in ((-1,"L"),(1,"R")):
        v3.uv(f"Eye.{l}",(s*.052,-.174,2.087),(.026,.013,.018),p["eye"],root,20,12,0)
        v3.uv(f"Iris.{l}",(s*.052,-.186,2.087),(.010,.005,.010),p["iris"],root,16,8,0)
    # Separate brows add stylized hero readability at game-card scale.
    for s,l in ((-1,"L"),(1,"R")):
        v3.beam(f"HeroBrow.{l}",(s*.094,-.184,2.132),(s*.020,-.184,2.127),.006,.0035,p["hair"],root)
    # Smooth swept hair cap + curved locks.
    v3.uv("HairMass",(0,.030,2.200),(.158,.122,.095),p["hair"],root,30,18,1)
    lock_specs=[(-.125,2.225,-.16),(-.075,2.245,-.09),(-.025,2.254,-.03),(.030,2.250,.04),(.080,2.238,.10),(.125,2.218,.17)]
    for i,(x,ztip,bend) in enumerate(lock_specs):
        v3.tube(f"HairLock.{i}",[(x,-.105,2.205),(x*.92,-.135,ztip)],[.022,.008],p["hair"],root,10,.002,1)


def build_body(root,p,level):
    # Athletic cloth under-suit.
    v3.ring_body("Tunic",[(1.02,.245,.150,.012),(1.18,.275,.165,.0),(1.44,.335,.195,.0),(1.63,.385,.210,.008),(1.72,.345,.185,.015)],p["blue"],root,28,.003,1)
    # Blue scarf/collar is a permanent Guardian identity cue.
    v3.uv("ScarfFront",(0,-.165,1.735),(.245,.055,.060),p["blue_light"],root,28,14,1)
    v3.uv("ScarfBack",(0,.105,1.735),(.255,.060,.070),p["blue_dark"],root,28,14,1)
    v3.rounded_box("Belt",(0,-.015,1.055),(.285,.160,.042),p["leather"],root,bevel=.024,subsurf=1)
    v3.rounded_box("Buckle",(0,-.183,1.055),(.047,.016,.050),p["gold"],root,bevel=.012,subsurf=1)
    # Split cloth/tabard, slimmer than previous drafts.
    for s,l in ((-1,"L"),(1,"R")):
        pts=[(s*.025,1.03),(s*.19,1.00),(s*.165,.58),(s*.09,.46),(s*.030,.54)]
        tab=v3.plate(f"Tabard.{l}",pts,.018,p["cloth"],root,.010,1);tab.location.y=-.175
    if level>=2:
        for s,l in ((-1,"L"),(1,"R")):
            v3.beam(f"TabardTrim.{l}",(s*.055,-.202,.55),(s*.145,-.202,.59),.010,.0045,p["gold"],root)
    if level>=3:
        # Layered *front* cuirass instead of a metallic barrel around the torso.
        main=[(-.30,1.62),(-.21,1.69),(0,1.72),(.21,1.69),(.30,1.62),(.275,1.34),(.16,1.18),(0,1.13),(-.16,1.18),(-.275,1.34)]
        q=v3.plate("Breastplate",main,.060,p["steel"],root,.026,1);q.location.y=-.205
        core=[(-.075,1.61),(0,1.66),(.075,1.61),(.095,1.34),(0,1.21),(-.095,1.34)]
        c=v3.plate("BreastplateCore",core,.026,p["darksteel"],root,.012,1);c.location.y=-.270
        # waist plates create a heroic V silhouette
        for s,l in ((-1,"L"),(1,"R")):
            hip=[(s*.04,1.20),(s*.245,1.24),(s*.275,1.05),(s*.16,.94),(s*.055,1.00)]
            hp=v3.plate(f"HipPlate.{l}",hip,.030,p["steel"],root,.018,1);hp.location.y=-.190
    if level>=4:
        for s,l in ((-1,"L"),(1,"R")):
            # three-piece smooth pauldrons make the shoulder silhouette layered.
            v3.uv(f"PauldrBase.{l}",(s*.415,-.005,1.635),(.165,.112,.082),p["darksteel"],root,28,16,1)
            v3.rounded_box(f"PauldrTop.{l}",(s*.455,-.075,1.675),(.145,.050,.054),p["silver"],root,rot=(0,s*.12,s*.05),bevel=.035,subsurf=1)
            v3.rounded_box(f"PauldrEdge.{l}",(s*.495,-.130,1.650),(.100,.024,.030),p["gold_dark"],root,rot=(0,s*.16,s*.08),bevel=.015,subsurf=1)
    if level>=5:
        chest=v3.plate("GoldChestV",[(-.235,1.61),(0,1.45),(.235,1.61),(.17,1.665),(0,1.555),(-.17,1.665)],.018,p["gold"],root,.007,0);chest.location.y=-.282
    if level>=6:v3.uv("GuardianMedallion",(0,-.306,1.49),(.045,.012,.053),p["gold"],root,18,10,0)
    if level>=8:v3.uv("GuardianCore",(0,-.320,1.49),(.030,.008,.041),p["glow"],root,16,8,0)
    if level>=9:
        for s,l in ((-1,"L"),(1,"R")):v3.rounded_box(f"ShoulderGold.{l}",(s*.46,-.148,1.67),(.083,.009,.015),p["gold"],root,bevel=.006,subsurf=0)
    if level>=10:
        for s,l in ((-1,"L"),(1,"R")):
            v3.rounded_box(f"EliteShoulder.{l}",(s*.51,-.015,1.705),(.138,.090,.044),p["darksteel"],root,rot=(0,s*.16,0),bevel=.032,subsurf=1)
            v3.cone(f"ShoulderFin.{l}",(s*.61,-.005,1.755),.026,.003,.19,p["gold"],root,rot=(0,s*.72,0),vertices=12)
    if level>=12:
        for s,l in ((-1,"L"),(1,"R")):v3.uv(f"ShoulderRune.{l}",(s*.485,-.155,1.675),(.025,.007,.031),p["glow"],root,14,8,0)
    if level>=15:v3.torus("ChestMaster",(0,-.329,1.49),.078,.007,p["warmglow"],root,rot=(math.pi/2,0,0))


def build_legs(root,p,level):
    # Wider athletic stance and tapered anatomy.
    for s,l in ((-1,"L"),(1,"R")):
        hip=(s*.155,0,1.02); thigh=(s*.185,-.005,.80); knee=(s*.205,-.015,.61); shin=(s*.220,-.030,.37); ankle=(s*.235,-.045,.17)
        v3.tube(f"Leg.{l}",[hip,thigh,knee,shin,ankle],[.105,.112,.094,.080,.068],p["blue_dark"],root,16,.003,1)
        v3.rounded_box(f"BootAnkle.{l}",(s*.235,-.070,.17),(.102,.100,.102),p["leather"],root,bevel=.036,subsurf=1)
        v3.rounded_box(f"BootFoot.{l}",(s*.235,-.155,.075),(.112,.175,.068),p["leather2"],root,rot=(.06,0,0),bevel=.040,subsurf=1)
        if level>=4:
            v3.rounded_box(f"Greave.{l}",(s*.218,-.108,.38),(.092,.056,.168),p["steel"],root,bevel=.040,subsurf=1)
            v3.uv(f"Knee.{l}",(s*.205,-.130,.615),(.090,.050,.068),p["silver"],root,22,12,1)
        if level>=7:v3.beam(f"GreaveGold.{l}",(s*.218,-.168,.48),(s*.222,-.168,.29),.010,.004,p["gold"],root)
        if level>=13:v3.uv(f"KneeRune.{l}",(s*.205,-.180,.615),(.018,.006,.024),p["glow"],root,12,7,0)


def build_arms(root,p,level):
    # Slight asymmetric hero pose: sword arm relaxed, shield arm forward/bent.
    right=[(.36,0,1.63),(.465,-.025,1.40),(.49,-.075,1.15)]
    left=[(-.36,0,1.63),(-.47,-.080,1.43),(-.50,-.215,1.25)]
    for pts,l in ((right,"R"),(left,"L")):
        v3.tube(f"UpperArm.{l}",pts[:2],[.086,.074],p["blue_dark"],root,16,.003,1)
        v3.tube(f"Forearm.{l}",pts[1:],[.071,.054],p["skin"],root,16,.003,1)
        v3.uv(f"Hand.{l}",pts[-1],(.055,.047,.061),p["skin_hi"],root,22,12,1)
        if level>=4:v3.uv(f"ArmGuard.{l}",((pts[0][0]+pts[1][0])*.5,-.045,1.515),(.082,.058,.118),p["steel"],root,22,12,1)
        if level>=6:
            mid=((pts[1][0]+pts[2][0])*.5,(pts[1][1]+pts[2][1])*.5,(pts[1][2]+pts[2][2])*.5)
            v3.tube(f"Bracer.{l}",[pts[1],mid],[.081,.070],p["silver"],root,16,.003,1)
        if level>=11:v3.torus(f"WristRank.{l}",pts[-1],.057,.006,p["gold"],root,rot=(math.pi/2,0,0))


def build_sword(root,p,level):
    # Wider polished sword, clearly readable in the 3/4 camera.
    hand=Vector((.49,-.075,1.15)); grip_end=Vector((.55,-.085,1.02)); start=Vector((.58,-.095,.98)); end=Vector((.88,-.15,.18))
    v3.tube("SwordGrip",[hand,grip_end],[.030,.030],p["leather"],root,12,.003,1)
    v3.beam("SwordGuard",(.43,-.105,1.055),(.69,-.105,1.055),.026,.019,p["gold"],root)
    width=.060+.004*max(0,level-5)+.004*max(0,level-11)
    v3.blade("SwordBlade",start,end,width,p["silver"],root)
    v3.uv("SwordPommel",(.475,-.073,1.19),(.033,.023,.035),p["gold"],root,16,9,1)
    if level>=7:v3.uv("SwordGem",(.585,-.116,.96),(.018,.006,.024),p["glow"],root,12,7,0)
    if level>=10:v3.beam("SwordGoldSpine",(.62,-.121,.90),(.84,-.157,.30),.007,.004,p["gold"],root)
    if level>=14:v3.beam("SwordEnergy",(.63,-.128,.88),(.85,-.164,.28),.007,.004,p["glow"],root)
    if level>=15:v3.torus("SwordAura",(.84,-.16,.30),.075,.006,p["warmglow"],root,rot=(math.pi/2,0,.35))


# Replace selected v3 construction functions. Calls inside v3.build()/build_helmet()
# resolve globals from the module, so these overrides are used automatically.
v3.build_head=build_head
v3.build_body=build_body
v3.build_legs=build_legs
v3.build_arms=build_arms
v3.build_sword=build_sword

if __name__=="__main__":
    v3.main()
