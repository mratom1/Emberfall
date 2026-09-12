#!/usr/bin/env python3
"""Emberfall Army v4 art-direction pass.

Imports the tested v3 pipeline and replaces generic presentation pieces with
class-specific armor, weapon silhouettes, creature faces and elemental details.
The CLI is identical to generate_army_v3.py.
"""
from pathlib import Path
import importlib.util
import math

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("emberfall_army_v3", HERE / "generate_army_v3.py")
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)

_old_palette = v3.palette
_old_special = v3.special_accessories


def palette(spec, level):
    p = _old_palette(spec, level)
    r = (level - 1) / 14
    # Extra readable materials used by the class-specific pass.
    primary = v3.hexrgb(spec["primary"])
    secondary = v3.hexrgb(spec["secondary"])
    accent = v3.hexrgb(spec["accent"])
    p["cloth_rich"] = v3.material("RichCloth", v3.hsv_shift(primary, v=-.12+.03*r, s=.18), 0, .62)
    p["leather_light"] = v3.material("LightLeather", (.29,.13,.055), 0, .66)
    p["stone"] = v3.material("Stone", v3.hsv_shift(primary, v=-.09, s=-.08), .02, .78)
    p["stone_dark"] = v3.material("StoneDark", v3.hsv_shift(secondary, v=-.13, s=-.06), .03, .82)
    p["bronze"] = v3.material("Bronze", (.42+.10*r,.24+.06*r,.09), .72, .27)
    p["silver"] = v3.material("Silver", (.46+.12*r,.52+.12*r,.55+.12*r), .88, .18)
    p["leaf"] = v3.material("Leaf", (.10,.28+.05*r,.13), 0, .75)
    p["purple_magic"] = v3.material("VoidMagic", (.38,.17,.62), .10, .16, (.47,.18,.92), 1.0+1.0*r)
    return p


def torso(root,p,spec,level,robe=False,heavy=False):
    uid = spec.get("_id", "")
    caster = uid in {"mage","healer","frostweaver","stormcaller"}
    light = uid in {"ranger","raider","bomber","assassin","duelist"}
    fur = uid == "berserker"
    # Base clothing: saturated class color, never skin-toned.
    v3.cone("Tunic",(0,0,1.30),.31,.39,.70,p["cloth_rich"],root,vertices=10)
    v3.cube("TunicFront",(0,-.245,1.28),(.29,.025,.29),p["primary_dark"],root,bevel=.035)
    v3.cube("Belt",(0,-.01,.96),(.34,.205,.045),p["leather"],root,bevel=.02)
    v3.cube("BeltBuckle",(0,-.222,.96),(.055,.018,.055),p["accent"],root,bevel=.012)
    # Role-appropriate lower silhouette.
    if caster:
        v3.cone("Robe",(0,.01,.69),.38,.27,.62,p["primary_dark"],root,vertices=12)
        v3.cube("RobePanel",(0,-.255,.68),(.18,.020,.27),p["cloth_rich"],root,bevel=.025)
    elif uid in {"musketeer","duelist"}:
        v3.cone("CoatWaist",(0,0,.84),.34,.28,.30,p["primary_dark"],root,vertices=10)
    else:
        v3.cone("WaistGuard",(0,0,.87),.31,.28,.22,p["secondary"],root,vertices=10)

    # Every single level adds a visible rank/detail beat.
    if level >= 2:
        v3.cube("RankTrim",(0,-.274,1.49),(.25,.015,.022),p["accent"],root,bevel=.008)
    if level >= 3:
        v3.ico("BeltRune",(0,-.242,.96),(.045,.020,.055),p["glow"],root)

    if caster:
        # Casters evolve through cloth, runes, crystals, not generic plate armor.
        if level >= 4:
            v3.torus("ArcaneCollar",(0,-.03,1.50),.29,.022,p["accent"],root,rot=(math.pi/2,0,0))
        if level >= 5:
            for side,label in ((-1,"L"),(1,"R")):
                v3.ico(f"FocusShoulder.{label}",(side*.39,-.05,1.49),(.10,.08,.12),p["glow"],root)
        if level >= 6:
            v3.cube("RobeTrim",(0,-.285,1.18),(.23,.012,.028),p["accent"],root,bevel=.008)
        if level >= 7:
            for side,label in ((-1,"L"),(1,"R")):
                v3.cube(f"CasterBootGuard.{label}",(side*.19,-.055,.36),(.10,.075,.15),p["accent"],root,bevel=.03)
        if level >= 8:
            for side,label in ((-1,"L"),(1,"R")):
                v3.torus(f"WristRune.{label}",(side*.50,-.04,1.06),.075,.012,p["glow"],root,rot=(math.pi/2,0,0))
        if level >= 9:
            v3.ico("ArcaneChest",(0,-.305,1.34),(.075,.025,.095),p["glow"],root)
        if level >= 10:
            v3.torus("RuneBelt",(0,-.01,.90),.34,.016,p["glow"],root,rot=(math.pi/2,0,0))
        if level >= 11:
            for side,label in ((-1,"L"),(1,"R")):
                v3.ico(f"OrbitShard.{label}",(side*.35,-.10,1.64),(.045,.025,.070),p["glow"],root)
        if level >= 12:
            v3.cube("MasterRobeTrim",(0,-.287,.62),(.18,.012,.020),p["gold"],root,bevel=.006)
        if level >= 13:
            v3.torus("ArcaneChestRing",(0,-.315,1.34),.13,.012,p["glow"],root,rot=(math.pi/2,0,0))
        if level >= 14:
            for side,label in ((-1,"L"),(1,"R")):
                v3.ico(f"MasterShard.{label}",(side*.46,-.05,1.52),(.050,.030,.080),p["glow"],root)
        if level >= 15:
            v3.torus("MasteryAura",(0,0,.055),.60,.022,p["glow"],root)
        return

    if light:
        # Leather / asymmetrical light armor preserves ranger/rogue silhouettes.
        if level >= 4:
            v3.cube("LeatherVest",(0,-.258,1.31),(.28,.035,.24),p["leather_light"],root,bevel=.055)
            v3.beam("Harness",(-.25,-.298,1.52),(.20,-.298,1.08),.028,.010,p["accent"],root,.006)
        if level >= 5:
            v3.sphere("SinglePauldron",(-.405,-.01,1.49),(.15,.16,.12),p["leather_light"],root,16,10)
        if level >= 6:
            v3.cube("VestEdge",(0,-.300,1.13),(.23,.012,.022),p["accent"],root,bevel=.007)
        if level >= 7:
            for side,label in ((-1,"L"),(1,"R")):
                v3.cube(f"ShinWrap.{label}",(side*.19,-.055,.37),(.095,.070,.16),p["leather_light"],root,bevel=.025)
        if level >= 8:
            v3.cube("ArmGuard",(.50,-.03,1.06),(.075,.080,.16),p["darksteel"],root,bevel=.026)
        if level >= 9:
            v3.ico("VestRune",(0,-.310,1.34),(.060,.020,.075),p["glow"],root)
        if level >= 10:
            v3.cube("EliteHarness",(-.20,-.307,1.12),(.18,.010,.018),p["gold"],root,rot=(0,0,-.55),bevel=.005)
        if level >= 11:
            v3.torus("BeltRune",(0,-.02,.90),.34,.014,p["glow"],root,rot=(math.pi/2,0,0))
        if level >= 12:
            v3.cone("ShoulderPin",(-.48,-.01,1.57),.043,.0,.18,p["accent"],root,rot=(0,-.55,0),vertices=7)
        if level >= 13:
            v3.cube("MasterVestEdge",(0,-.314,1.51),(.22,.010,.018),p["gold"],root,bevel=.006)
        if level >= 14:
            v3.ico("ShoulderRune",(-.41,-.17,1.50),(.040,.018,.050),p["glow"],root)
        if level >= 15:
            v3.torus("MasteryAura",(0,0,.055),.58,.021,p["glow"],root)
        return

    if fur:
        # Berserker uses fur and straps instead of a polished cuirass.
        if level >= 4:
            v3.beam("ChestStrap",(-.27,-.288,1.52),(.22,-.288,1.08),.045,.014,p["leather_light"],root,.008)
        if level >= 5:
            for side,label in ((-1,"L"),(1,"R")):
                v3.sphere(f"FurPad.{label}",(side*.41,.00,1.50),(.18,.17,.13),p["fur"],root,14,8)
        if level >= 6:
            v3.cube("FurBelt",(0,-.02,.91),(.35,.21,.060),p["fur"],root,bevel=.025)
        if level >= 7:
            for side,label in ((-1,"L"),(1,"R")):
                v3.cube(f"IronBoot.{label}",(side*.19,-.055,.37),(.105,.080,.18),p["darksteel"],root,bevel=.030)
        if level >= 8:
            v3.cube("IronBracer",(.50,-.03,1.06),(.080,.085,.17),p["darksteel"],root,bevel=.030)
        if level >= 9: v3.ico("RageRune",(0,-.300,1.31),(.075,.025,.090),p["fire"],root)
        if level >= 10: v3.torus("RageBelt",(0,-.02,.90),.35,.016,p["fire"],root,rot=(math.pi/2,0,0))
        if level >= 11:
            for side,label in ((-1,"L"),(1,"R")): v3.cone(f"BoneSpike.{label}",(side*.50,0,1.58),.045,.0,.20,p["accent"],root,rot=(0,side*.52,0),vertices=7)
        if level >= 12: v3.cube("WarMark",(0,-.302,1.47),(.17,.012,.018),p["fire"],root,bevel=.006)
        if level >= 13: v3.ico("RageCore",(0,-.310,1.33),(.070,.022,.085),p["fire"],root)
        if level >= 14: v3.torus("RageChest",(0,-.315,1.33),.13,.012,p["fire"],root,rot=(math.pi/2,0,0))
        if level >= 15: v3.torus("MasteryAura",(0,0,.055),.62,.024,p["fire"],root)
        return

    # Heavy / soldier plate progression.  Plate uses class accent and layered silhouette.
    plate = p["steel"]
    if level >= 4:
        v3.cone("Cuirass",(0,-.035,1.31),.315,.36,.53,plate,root,vertices=10)
        v3.cube("CuirassFront",(0,-.260,1.33),(.285,.035,.235),plate,root,bevel=.045)
    if level >= 5:
        for side,label in ((-1,"L"),(1,"R")):
            v3.sphere(f"Pauldron.{label}",(side*(.41 if not heavy else .45),-.01,1.51),(.16 if not heavy else .19,.17,.13),plate,root,16,10)
    if level >= 6: v3.cube("ChestBand",(0,-.302,1.34),(.24,.018,.040),p["accent"],root,bevel=.010)
    if level >= 7:
        for side,label in ((-1,"L"),(1,"R")): v3.cube(f"Greave.{label}",(side*.19,-.055,.39),(.105,.085,.20),plate,root,bevel=.035)
    if level >= 8:
        for side,label in ((-1,"L"),(1,"R")): v3.cube(f"Bracer.{label}",(side*.50,-.03,1.06),(.075,.082,.16),p["darksteel"],root,bevel=.028)
    if level >= 9: v3.ico("ChestGem",(0,-.315,1.36),(.065,.026,.082),p["glow"],root)
    if level >= 10:
        for side,label in ((-1,"L"),(1,"R")): v3.cube(f"ShoulderTrim.{label}",(side*(.41 if not heavy else .45),-.165,1.51),(.11,.018,.040),p["accent"],root,bevel=.01)
    if level >= 11: v3.torus("WaistRune",(0,-.02,.88),.35,.016,p["glow"],root,rot=(math.pi/2,0,0))
    if level >= 12:
        for side,label in ((-1,"L"),(1,"R")): v3.cone(f"EliteSpike.{label}",(side*.51,-.005,1.60),.048,.0,.20,p["accent"],root,rot=(0,side*.56,0),vertices=7)
    if level >= 13: v3.cube("EliteChestTrim",(0,-.325,1.18),(.235,.015,.022),p["gold"],root,bevel=.008)
    if level >= 14:
        for side,label in ((-1,"L"),(1,"R")): v3.ico(f"ShoulderRune.{label}",(side*.41,-.178,1.53),(.040,.018,.048),p["glow"],root)
    if level >= 15: v3.torus("MasteryAura",(0,0,.055),.60,.022,p["glow"],root)


def sword(root,p,level,curved=False):
    # Move sword clearly outside the right silhouette; use broad rectangular blade.
    grip_a=(.62,-.06,.82);grip_b=(.72,-.06,1.10)
    blade_a=(.72,-.06,1.08);blade_b=(1.02,-.08,1.93+.015*level)
    v3.rod("SwordGrip",grip_a,grip_b,.045,p["leather"],root,10)
    v3.beam("SwordBlade",blade_a,blade_b,.085 if level<8 else .105,.030,p["silver"],root,.018)
    v3.beam("SwordGuard",(.55,-.07,1.11),(.86,-.07,1.11),.033,.030,p["accent"],root,.010)
    tip=Vector(blade_b);v3.cone("SwordTip",tuple(tip+Vector((.032,0,.11))),.090,0,.22,p["silver"],root,rot=(0,.28,0),vertices=8)
    if level>=8: v3.ico("SwordRune",(.91,-.11,1.62),(.045,.018,.060),p["glow"],root)
    if level>=14: v3.rod("SwordGlow",(.87,-.115,1.49),(.98,-.115,1.82),.012,p["glow"],root,8)


def special_accessories(root,p,spec,level):
    _old_special(root,p,spec,level)
    uid=spec.get("_id","")
    if uid=="guardian":
        # Cross-body straps and rank medallion keep early levels from looking bare.
        v3.beam("GuardianStrap",(-.24,-.283,1.51),(.21,-.283,1.09),.032,.010,p["leather_light"],root,.006)
        v3.ico("GuardianBadge",(-.03,-.300,1.32),(.050,.018,.060),p["accent"],root)
    elif uid=="ranger":
        v3.cube("RangerShoulderCape",(-.20,.16,1.45),(.25,.045,.22),p["leaf"],root,rot=(-.18,0,-.14),bevel=.035)
        v3.cube("BowArmBracer",(.50,-.03,1.05),(.075,.080,.16),p["leather_light"],root,bevel=.025)
    elif uid=="raider":
        for i in range(3): v3.sphere(f"CoinPouch.{i}",(-.28+i*.12,-.03,.88),(.060,.045,.075),p["leather_light"],root,12,7)
    elif uid=="mage":
        for side in (-1,1): v3.ico(f"EmberSatellite.{side}",(side*.32,-.05,1.64),(.052,.030,.072),p["fire"],root)
    elif uid=="breaker":
        v3.beam("BreakerMark",(-.15,-.324,1.42),(.15,-.324,1.20),.024,.010,p["accent"],root,.006)
    elif uid=="bomber":
        v3.torus("FuseBadge",(0,-.310,1.34),.090,.014,p["fire"],root,rot=(math.pi/2,0,0))
    elif uid=="healer":
        v3.cube("MedicMarkV",(0,-.310,1.34),(.028,.012,.095),p["glow"],root,bevel=.008)
        v3.cube("MedicMarkH",(0,-.312,1.34),(.095,.012,.028),p["glow"],root,bevel=.008)
    elif uid=="hammerguard":
        v3.cube("RuneTabard",(0,-.310,1.17),(.20,.018,.26),p["cloth_rich"],root,bevel=.02)
    elif uid=="assassin":
        v3.cube("ScarfTail.L",(-.08,.22,1.33),(.055,.025,.38),p["primary"],root,rot=(-.18,0,-.10),bevel=.018)
        v3.cube("ScarfTail.R",(.08,.22,1.30),(.055,.025,.34),p["primary_dark"],root,rot=(-.14,0,.10),bevel=.018)
    elif uid=="lancer":
        v3.ico("SunBadge",(0,-.312,1.34),(.065,.020,.065),p["gold"],root)
        if level>=10:
            for a in range(6):
                angle=a*math.tau/6
                v3.rod(f"SunRay.{a}",(math.sin(angle)*.07,-.314,1.34+math.cos(angle)*.07),(math.sin(angle)*.12,-.314,1.34+math.cos(angle)*.12),.008,p["glow"],root,6)


def giant(uid,spec,level,p):
    root=v3.root_empty();r=(level-1)/14
    # Boulder clusters instead of one blank egg-shaped body.
    v3.sphere("CoreBoulder",(0,0,1.16),(.50,.39,.58),p["stone"],root,16,10)
    v3.sphere("ChestBoulder",(0,-.27,1.24),(.37,.20,.37),p["stone_dark"],root,14,8)
    v3.sphere("Head",(0,-.06,1.84),(.31,.28,.29),p["stone"],root,14,8)
    # Face: glowing eyes + stone jaw.
    for side,label in ((-1,"L"),(1,"R")):
        v3.ico(f"Eye.{label}",(side*.085,-.318,1.89),(.037,.018,.034),p["glow"],root)
        v3.sphere(f"ShoulderBoulder.{label}",(side*.48,.02,1.44),(.27,.25,.25),p["stone_dark"],root,14,8)
        v3.rod(f"Arm.{label}",(side*.50,0,1.39),(side*.69,-.03,.70),.20,p["stone"],root,10)
        v3.sphere(f"Fist.{label}",(side*.72,-.08,.52),(.26,.23,.24),p["stone_dark"],root,14,8)
        v3.rod(f"Leg.{label}",(side*.23,0,.69),(side*.28,0,.20),.20,p["stone_dark"],root,10)
        v3.cube(f"Foot.{label}",(side*.28,-.09,.09),(.28,.28,.11),p["stone"],root,bevel=.07)
    v3.cube("StoneJaw",(0,-.310,1.73),(.17,.040,.075),p["stone_dark"],root,bevel=.035)
    # Front rune grows every level, so the progression reads from the game camera.
    v3.torus("ChestRune",(0,-.482,1.24),.13+.006*level,.015,p["glow"],root,rot=(math.pi/2,0,0))
    for i in range(2+level):
        side=-1 if i%2==0 else 1
        row=i//2
        x=side*(.30+.035*(row%3));z=1.30+(row%5)*.12
        v3.cone(f"CrystalGrowth.{i}",(x,-.31,z),.035+.001*level,.004,.14+.008*level,p["glow"] if level>=8 else p["accent"],root,rot=(math.pi/2,0,-side*.35),vertices=7)
    if level>=10:
        for side,label in ((-1,"L"),(1,"R")): v3.cube(f"StonePlate.{label}",(side*.34,-.34,1.43),(.15,.035,.14),p["stone_dark"],root,bevel=.04)
    if level>=15:v3.torus("GiantAura",(0,0,.055),.72,.026,p["glow"],root)
    s=float(spec.get("scale",1.38))*(1+.025*r);root.scale=(s,s,s);return root


def flying(uid,spec,level,p):
    root=v3.root_empty();r=(level-1)/14
    phoenix=uid=="phoenix";drake=uid=="drake";wyvern=uid=="wyvern"
    bodymat=p["fire"] if phoenix else p["primary"]
    chestmat=p["primary_dark"] if not phoenix else p["accent"]
    v3.sphere("Body",(0,.03,1.10),(.36,.43,.48),bodymat,root,16,10)
    v3.sphere("Chest",(0,-.34,1.14),(.26,.16,.31),chestmat,root,14,8)
    v3.rod("Neck",(0,-.16,1.45),(0,-.36,1.66),.16,bodymat,root,10)
    v3.sphere("Head",(0,-.43,1.79),(.24,.27,.22),bodymat,root,14,8)
    v3.cone("Snout",(0,-.69,1.77),.11,.025,.38,p["accent"],root,rot=(math.pi/2,0,0),vertices=9)
    for side,label in ((-1,"L"),(1,"R")):
        v3.ico(f"Eye.{label}",(side*.085,-.647,1.84),(.034,.018,.034),p["glow"],root)
        v3.rod(f"Leg.{label}",(side*.15,0,.80),(side*.19,-.05,.40),.050,chestmat,root,9)
        for j in (-1,0,1):v3.rod(f"Talon.{label}.{j}",(side*.19,-.05,.40),(side*.19+j*.05,-.18,.27),.014,p["accent"],root,7)
    # Species-specific wings instead of generic rods only.
    for side,label in ((-1,"L"),(1,"R")):
        wingmat=p["fire"] if phoenix else p["ice"] if drake else p["primary"]
        membrane=p["accent"] if wyvern else wingmat
        v3.rod(f"WingBone.{label}",(side*.22,.17,1.45),(side*1.22,.24,1.48),.055,p["darksteel"] if not phoenix else p["fire"],root,10)
        v3.beam(f"WingMembrane.{label}",(side*.35,.25,1.43),(side*1.12,.28,.92),.20,.025,membrane,root,.018)
        count=5+(2 if level>=10 else 0)
        for i in range(count):
            x=side*(.45+i*.14);z=1.36-i*.09
            v3.cone(f"WingTip.{label}.{i}",(x,.27,z),.060,.008,.27,wingmat,root,rot=(0,side*.30,0),vertices=7)
    if phoenix:
        # Flame crown and long tail plumes create an unmistakable phoenix silhouette.
        for i in range(5):
            v3.cone(f"FlameCrest.{i}",((i-2)*.045,-.37,2.03+abs(i-2)*.015),.040,.004,.20+.025*(2-abs(i-2)),p["fire"],root,vertices=7)
        for i in range(5+level//3):
            x=(i-(4+level//3)/2)*.07
            v3.rod(f"FlameTail.{i}",(x,.28,.93),(x*1.5,.55,.20-i*.015),.040,p["fire"],root,8)
    elif drake:
        for i in range(4+level//2):v3.cone(f"CrystalSpine.{i}",(0,.27,.82+i*.12),.045,.004,.18,p["ice"],root,rot=(math.pi/2,0,0),vertices=7)
    else:
        for side,label in ((-1,"L"),(1,"R")):v3.cone(f"Horn.{label}",(side*.15,-.44,2.00),.045,.004,.24,p["accent"],root,rot=(0,side*.45,0),vertices=7)
    if level>=8:v3.torus("FlightRune",(0,0,.30),.48,.018,p["glow"],root)
    if level>=15:v3.torus("FlightAura",(0,0,.08),.68,.026,p["glow"],root)
    s=float(spec.get("scale",1.25))*(1+.025*r);root.scale=(s,s,s);return root

# Apply art-direction overrides.
v3.palette = palette
v3.torso = torso
v3.sword = sword
v3.special_accessories = special_accessories
v3.build_giant = giant
v3.build_flying = flying

v3.main()
