from pathlib import Path
import json
import math
import bpy

REPO = Path(__file__).resolve().parents[3]
BASE = REPO / "assets" / "characters" / "troops" / "guardian"
SOURCE = BASE / "source"
EXPORTS = BASE / "exports"
SOURCE.mkdir(parents=True, exist_ok=True)
EXPORTS.mkdir(parents=True, exist_ok=True)

LEVEL_CHANGES = {
    1: "Recruit kit: leather underlayer, iron chest plate, short sword and compact shield.",
    2: "Adds iron shin caps, reinforced belt and shield rim for a sturdier frontline silhouette.",
    3: "Adds layered chest armor and helmet cheek guards; sword grows slightly longer.",
    4: "Adds first heavy pauldron and a reinforced sword guard.",
    5: "Adds matching pauldrons and twin waist plates, widening the armored silhouette.",
    6: "Adds metal bracers, shield boss and a reinforced blade spine.",
    7: "Adds helmet crest and knee guards, making the upper silhouette visibly taller.",
    8: "Adds armored boots and a short rear mantle/back cloth.",
    9: "Adds hanging tassets, raised collar and shield side fins.",
    10: "Veteran tier: dark plate, shoulder spikes, ember chest core and larger sword/shield.",
    11: "Adds plated upper arms and segmented chest bands.",
    12: "Adds tower-shield crown plates and a stronger crossguard/pommel assembly.",
    13: "Adds horned helmet crown, back plate and shin fins for an elite silhouette.",
    14: "Adds ember blade-edge strips, extended shield wings and a crown crest.",
    15: "Ascendant Guardian: full mantle, layered crown, ember core, oversized shield and master sword details.",
}


def mat(name, color, metallic=0.0, roughness=0.55, emission=None):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 1.6
        elif "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = (*emission, 1.0)
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = 1.6
    return m


def assign(obj, material):
    if obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.append(material)


def tag(obj, bone):
    if obj.type == "MESH":
        vg = obj.vertex_groups.new(name=bone)
        vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    return obj


def box(name, loc, scale, material, bone, bevel=0.06, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    if bevel:
        mod = o.modifiers.new("SoftBevel", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    assign(o, material)
    return tag(o, bone)


def cylinder(name, loc, radius, depth, material, bone, verts=10, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    assign(o, material)
    return tag(o, bone)


def sphere(name, loc, scale, material, bone):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o, material)
    return tag(o, bone)


def cone(name, loc, radius, depth, material, bone, verts=8, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=radius, radius2=0.0, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    assign(o, material)
    return tag(o, bone)


def blade(name, loc, length, width, thickness, material, bone):
    x = width * 0.5
    y = thickness * 0.5
    z0 = -length * 0.5
    z1 = length * 0.34
    z2 = length * 0.5
    verts = [
        (-x, -y, z0), (x, -y, z0), (x, y, z0), (-x, y, z0),
        (-x, -y, z1), (x, -y, z1), (x, y, z1), (-x, y, z1),
        (0, -y, z2), (0, y, z2),
    ]
    faces = [
        (0, 1, 2, 3), (0, 4, 5, 1), (3, 2, 6, 7),
        (0, 3, 7, 4), (1, 5, 6, 2), (4, 7, 9, 8),
        (5, 8, 9, 6), (4, 8, 5), (7, 6, 9)
    ]
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    o.location = loc
    assign(o, material)
    return tag(o, bone)


def shield(name, loc, width, height, depth, material, accent, bone):
    x = width * 0.5
    y = depth * 0.5
    z = height * 0.5
    verts = [
        (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z),
        (-x, -y, -z * 0.55), (x, -y, -z * 0.55), (x, y, -z * 0.55), (-x, y, -z * 0.55),
        (0, -y, -z), (0, y, -z),
    ]
    faces = [
        (0, 1, 2, 3), (0, 4, 5, 1), (3, 2, 6, 7), (0, 3, 7, 4),
        (1, 5, 6, 2), (4, 8, 5), (7, 6, 9), (4, 7, 9, 8), (5, 8, 9, 6)
    ]
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    o.location = loc
    assign(o, material)
    tag(o, bone)
    ridge = box(name + "_Ridge", (loc[0], loc[1] - depth * 0.62, loc[2]), (0.065, depth * 0.22, height * 0.43), accent, bone, bevel=0.02)
    return o, ridge


def create_armature():
    arm_data = bpy.data.armatures.new("GuardianRig")
    arm = bpy.data.objects.new("GuardianRig", arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    def bone(name, head, tail, parent=None):
        b = arm_data.edit_bones.new(name)
        b.head, b.tail = head, tail
        if parent:
            b.parent = arm_data.edit_bones[parent]
        return b

    bone("root", (0, 0, 0), (0, 0, 0.3))
    bone("pelvis", (0, 0, 0.65), (0, 0, 1.05), "root")
    bone("spine", (0, 0, 1.05), (0, 0, 1.85), "pelvis")
    bone("head", (0, 0, 1.85), (0, 0, 2.45), "spine")
    bone("upper_arm.L", (0.12, 0, 1.72), (0.62, 0, 1.55), "spine")
    bone("forearm.L", (0.62, 0, 1.55), (0.88, 0, 1.25), "upper_arm.L")
    bone("hand.L", (0.88, 0, 1.25), (0.95, 0, 1.12), "forearm.L")
    bone("upper_arm.R", (-0.12, 0, 1.72), (-0.62, 0, 1.55), "spine")
    bone("forearm.R", (-0.62, 0, 1.55), (-0.88, 0, 1.25), "upper_arm.R")
    bone("hand.R", (-0.88, 0, 1.25), (-0.95, 0, 1.12), "forearm.R")
    bone("thigh.L", (0.23, 0, 0.85), (0.23, 0, 0.38), "pelvis")
    bone("shin.L", (0.23, 0, 0.38), (0.23, 0, -0.18), "thigh.L")
    bone("thigh.R", (-0.23, 0, 0.85), (-0.23, 0, 0.38), "pelvis")
    bone("shin.R", (-0.23, 0, 0.38), (-0.23, 0, -0.18), "thigh.R")
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.show_in_front = True
    return arm


def bind(meshes, arm):
    for o in meshes:
        if o.type != "MESH":
            continue
        o.parent = arm
        mod = o.modifiers.new("GuardianRig", "ARMATURE")
        mod.object = arm


def triangle_count():
    total = 0
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            total += sum(max(1, len(p.vertices) - 2) for p in obj.data.polygons)
    return total


def build(level):
    bpy.ops.wm.read_factory_settings(use_empty=True)

    leather = mat("Leather", (0.16, 0.07, 0.035), 0.0, 0.72)
    cloth = mat("AshCloth", (0.12, 0.13, 0.14), 0.0, 0.86)
    skin = mat("Skin", (0.42, 0.22, 0.13), 0.0, 0.78)
    iron = mat("Iron", (0.22, 0.25, 0.27), 0.68, 0.30)
    steel = mat("Steel", (0.37, 0.42, 0.46), 0.82, 0.24)
    tempered = mat("TemperedSteel", (0.26, 0.31, 0.36), 0.88, 0.22)
    dark = mat("DarkPlate", (0.075, 0.09, 0.11), 0.90, 0.20)
    ember = mat("EmberAccent", (0.72, 0.14, 0.025), 0.28, 0.24, emission=(0.35, 0.025, 0.005))
    bronze = mat("Bronze", (0.45, 0.24, 0.08), 0.72, 0.30)
    gold = mat("GoldTrim", (0.62, 0.39, 0.10), 0.78, 0.24)

    if level <= 3:
        plate = iron
    elif level <= 6:
        plate = steel
    elif level <= 9:
        plate = tempered
    else:
        plate = dark

    accent = bronze if level <= 6 else (gold if level <= 9 else ember)
    arm = create_armature()
    meshes = []

    meshes += [
        box("Boot_L", (0.23, -0.03, -0.18), (0.18, 0.29, 0.14), leather, "shin.L", 0.05),
        box("Boot_R", (-0.23, -0.03, -0.18), (0.18, 0.29, 0.14), leather, "shin.R", 0.05),
        cylinder("Shin_L", (0.23, 0, 0.18), 0.15, 0.62, plate, "shin.L", 8),
        cylinder("Shin_R", (-0.23, 0, 0.18), 0.15, 0.62, plate, "shin.R", 8),
        cylinder("Thigh_L", (0.23, 0, 0.72), 0.19, 0.52, cloth, "thigh.L", 8),
        cylinder("Thigh_R", (-0.23, 0, 0.72), 0.19, 0.52, cloth, "thigh.R", 8),
        box("PelvisGuard", (0, 0, 0.92), (0.46, 0.27, 0.22), leather if level == 1 else plate, "pelvis", 0.08),
        box("Torso", (0, 0, 1.43), (0.48, 0.29, 0.50), cloth, "spine", 0.10),
        box("ChestPlate", (0, -0.06, 1.48), (0.52 + min(level, 10) * 0.008, 0.24, 0.39), plate, "spine", 0.09),
        sphere("Head", (0, 0, 2.08), (0.29, 0.27, 0.34), skin, "head"),
        cylinder("UpperArm_L", (0.66, 0, 1.52), 0.14, 0.55, cloth, "upper_arm.L", 8, (0, math.radians(73), 0)),
        cylinder("UpperArm_R", (-0.66, 0, 1.52), 0.14, 0.55, cloth, "upper_arm.R", 8, (0, math.radians(-73), 0)),
        cylinder("Forearm_L", (0.90, 0, 1.24), 0.12, 0.42, leather, "forearm.L", 8, (0, math.radians(38), 0)),
        cylinder("Forearm_R", (-0.90, 0, 1.24), 0.12, 0.42, leather, "forearm.R", 8, (0, math.radians(-38), 0)),
        box("Helmet", (0, 0.02, 2.22), (0.34, 0.30, 0.24), plate, "head", 0.09),
        box("HelmetBrow", (0, -0.29, 2.16), (0.35, 0.05, 0.07), accent, "head", 0.02),
    ]

    sword_len = 1.05 + (level - 1) * 0.035
    if level >= 10:
        sword_len += 0.10
    sword_width = 0.20 + min(level - 1, 10) * 0.007
    meshes += [
        cylinder("SwordGrip", (-1.02, -0.04, 1.03), 0.055 + level * 0.001, 0.38, leather, "hand.R", 10),
        box("SwordGuard", (-1.02, -0.04, 1.20), (0.20 + level * 0.008, 0.06, 0.045), accent, "hand.R", 0.02),
        blade("SwordBlade", (-1.02, -0.04, 1.66 + (sword_len - 1.05) * 0.18), sword_len, sword_width, 0.075, steel if level < 10 else tempered, "hand.R"),
    ]

    shield_w = 0.70 + (level - 1) * 0.018
    shield_h = 1.14 + (level - 1) * 0.028
    if level >= 10:
        shield_w += 0.08
        shield_h += 0.10
    shield_main, shield_ridge = shield("GuardianShield", (1.05, -0.02, 1.32), shield_w, shield_h, 0.12, plate, accent, "hand.L")
    meshes += [shield_main, shield_ridge]

    # Every level adds new geometry; upgrades are not simple recolors.
    if level >= 2:
        meshes += [
            box("ShinCap_L", (0.23, -0.15, 0.23), (0.18, 0.07, 0.19), iron, "shin.L", 0.035),
            box("ShinCap_R", (-0.23, -0.15, 0.23), (0.18, 0.07, 0.19), iron, "shin.R", 0.035),
            box("BeltPlate", (0, -0.285, 0.98), (0.24, 0.04, 0.10), bronze, "pelvis", 0.02),
            box("ShieldRimTop", (1.05, -0.095, 1.32 + shield_h * 0.42), (shield_w * 0.36, 0.035, 0.045), bronze, "hand.L", 0.015),
        ]

    if level >= 3:
        meshes += [
            box("ChestLayer", (0, -0.285, 1.50), (0.39, 0.035, 0.21), steel, "spine", 0.025),
            box("Cheek_L", (0.25, -0.25, 2.06), (0.07, 0.06, 0.16), iron, "head", 0.025, (0, 0, math.radians(-8))),
            box("Cheek_R", (-0.25, -0.25, 2.06), (0.07, 0.06, 0.16), iron, "head", 0.025, (0, 0, math.radians(8))),
        ]

    if level >= 4:
        meshes += [
            box("Pauldron_L", (0.57, 0, 1.76), (0.28, 0.34, 0.18), steel, "upper_arm.L", 0.09),
            box("GuardLanget", (-1.02, -0.04, 1.30), (0.07, 0.055, 0.15), bronze, "hand.R", 0.02),
        ]

    if level >= 5:
        meshes += [
            box("Pauldron_R", (-0.57, 0, 1.76), (0.28, 0.34, 0.18), steel, "upper_arm.R", 0.09),
            box("WaistPlate_L", (0.34, 0, 0.93), (0.15, 0.24, 0.28), steel, "pelvis", 0.055, (0, 0, math.radians(-8))),
            box("WaistPlate_R", (-0.34, 0, 0.93), (0.15, 0.24, 0.28), steel, "pelvis", 0.055, (0, 0, math.radians(8))),
        ]

    if level >= 6:
        meshes += [
            box("Bracer_L", (0.91, -0.03, 1.23), (0.15, 0.17, 0.20), steel, "forearm.L", 0.05),
            box("Bracer_R", (-0.91, -0.03, 1.23), (0.15, 0.17, 0.20), steel, "forearm.R", 0.05),
            cylinder("ShieldBoss", (1.05, -0.15, 1.32), 0.14, 0.10, bronze, "hand.L", 12, (math.pi / 2, 0, 0)),
            box("BladeSpine", (-1.02, -0.085, 1.70), (0.035, 0.022, sword_len * 0.33), bronze, "hand.R", 0.01),
        ]

    if level >= 7:
        meshes += [
            box("CrestSpine", (0, 0.03, 2.53), (0.065, 0.12, 0.27), gold, "head", 0.03),
            box("KneeGuard_L", (0.23, -0.17, 0.43), (0.20, 0.08, 0.16), tempered, "shin.L", 0.055),
            box("KneeGuard_R", (-0.23, -0.17, 0.43), (0.20, 0.08, 0.16), tempered, "shin.R", 0.055),
        ]

    if level >= 8:
        meshes += [
            box("BootArmor_L", (0.23, -0.18, -0.14), (0.20, 0.09, 0.12), tempered, "shin.L", 0.04),
            box("BootArmor_R", (-0.23, -0.18, -0.14), (0.20, 0.09, 0.12), tempered, "shin.R", 0.04),
            box("RearMantle", (0, 0.27, 1.36), (0.46, 0.035, 0.42), cloth, "spine", 0.025, (math.radians(-8), 0, 0)),
        ]

    if level >= 9:
        meshes += [
            box("Tasset_L", (0.29, -0.03, 0.70), (0.14, 0.23, 0.31), tempered, "thigh.L", 0.045, (0, 0, math.radians(-5))),
            box("Tasset_R", (-0.29, -0.03, 0.70), (0.14, 0.23, 0.31), tempered, "thigh.R", 0.045, (0, 0, math.radians(5))),
            box("RaisedCollar", (0, 0.02, 1.91), (0.33, 0.23, 0.10), tempered, "spine", 0.045),
            cone("ShieldFin_L", (1.05 + shield_w * 0.47, -0.03, 1.38), 0.09, 0.28, gold, "hand.L", 6, (0, math.radians(90), 0)),
            cone("ShieldFin_R", (1.05 - shield_w * 0.47, -0.03, 1.38), 0.09, 0.28, gold, "hand.L", 6, (0, math.radians(-90), 0)),
        ]

    if level >= 10:
        meshes += [
            cone("ShoulderSpike_L", (0.73, 0, 1.90), 0.10, 0.34, ember, "upper_arm.L", 6, (0, math.radians(72), 0)),
            cone("ShoulderSpike_R", (-0.73, 0, 1.90), 0.10, 0.34, ember, "upper_arm.R", 6, (0, math.radians(-72), 0)),
            sphere("EmberCore", (0, -0.31, 1.52), (0.105, 0.055, 0.105), ember, "spine"),
        ]

    if level >= 11:
        meshes += [
            box("UpperArmPlate_L", (0.68, -0.03, 1.48), (0.18, 0.21, 0.25), dark, "upper_arm.L", 0.055),
            box("UpperArmPlate_R", (-0.68, -0.03, 1.48), (0.18, 0.21, 0.25), dark, "upper_arm.R", 0.055),
            box("ChestBandTop", (0, -0.305, 1.69), (0.43, 0.035, 0.055), ember, "spine", 0.015),
            box("ChestBandLow", (0, -0.305, 1.30), (0.42, 0.035, 0.055), ember, "spine", 0.015),
        ]

    if level >= 12:
        meshes += [
            box("ShieldCrown", (1.05, -0.10, 1.32 + shield_h * 0.50), (shield_w * 0.34, 0.045, 0.075), dark, "hand.L", 0.02),
            cone("ShieldCrownTip", (1.05, -0.10, 1.32 + shield_h * 0.60), 0.08, 0.28, ember, "hand.L", 6),
            sphere("SwordPommel", (-1.02, -0.04, 0.83), (0.10, 0.10, 0.10), ember, "hand.R"),
            box("CrossguardCore", (-1.02, -0.04, 1.20), (0.32, 0.07, 0.055), dark, "hand.R", 0.02),
        ]

    if level >= 13:
        meshes += [
            cone("HelmetHorn_L", (0.22, 0.02, 2.49), 0.075, 0.34, dark, "head", 7, (0, math.radians(-25), math.radians(-16))),
            cone("HelmetHorn_R", (-0.22, 0.02, 2.49), 0.075, 0.34, dark, "head", 7, (0, math.radians(25), math.radians(16))),
            box("BackPlate", (0, 0.27, 1.51), (0.50, 0.06, 0.46), dark, "spine", 0.06),
            cone("ShinFin_L", (0.23, 0.08, 0.18), 0.065, 0.28, ember, "shin.L", 6, (math.radians(90), 0, 0)),
            cone("ShinFin_R", (-0.23, 0.08, 0.18), 0.065, 0.28, ember, "shin.R", 6, (math.radians(90), 0, 0)),
        ]

    if level >= 14:
        edge_h = sword_len * 0.34
        meshes += [
            box("BladeEmberEdge_L", (-1.02 - sword_width * 0.43, -0.085, 1.72), (0.018, 0.018, edge_h), ember, "hand.R", 0.008),
            box("BladeEmberEdge_R", (-1.02 + sword_width * 0.43, -0.085, 1.72), (0.018, 0.018, edge_h), ember, "hand.R", 0.008),
            cone("ShieldWing_L", (1.05 + shield_w * 0.58, -0.02, 1.34), 0.105, 0.42, dark, "hand.L", 6, (0, math.radians(90), 0)),
            cone("ShieldWing_R", (1.05 - shield_w * 0.58, -0.02, 1.34), 0.105, 0.42, dark, "hand.L", 6, (0, math.radians(-90), 0)),
            box("CrownCrest", (0, 0.02, 2.68), (0.10, 0.12, 0.18), ember, "head", 0.03),
        ]

    if level >= 15:
        meshes += [
            box("Mantle_L", (0.38, 0.18, 1.65), (0.30, 0.08, 0.42), dark, "spine", 0.07, (math.radians(-7), 0, math.radians(-8))),
            box("Mantle_R", (-0.38, 0.18, 1.65), (0.30, 0.08, 0.42), dark, "spine", 0.07, (math.radians(-7), 0, math.radians(8))),
            cone("CrownBlade_L", (0.14, 0.02, 2.72), 0.07, 0.30, ember, "head", 6, (0, 0, math.radians(-8))),
            cone("CrownBlade_R", (-0.14, 0.02, 2.72), 0.07, 0.30, ember, "head", 6, (0, 0, math.radians(8))),
            box("ShieldFaceBar", (1.05, -0.17, 1.32), (shield_w * 0.40, 0.035, 0.07), ember, "hand.L", 0.012),
            sphere("MasterPommelGem", (-1.02, -0.04, 0.73), (0.075, 0.075, 0.075), ember, "hand.R"),
        ]

    bind(meshes, arm)

    bpy.context.scene["emberfall_unit"] = "guardian"
    bpy.context.scene["emberfall_level"] = level
    bpy.context.scene["visual_change"] = LEVEL_CHANGES[level]

    blend_path = SOURCE / f"guardian_l{level}.blend"
    glb_path = EXPORTS / f"guardian_l{level}.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", export_yup=True)

    return {
        "level": level,
        "blend": str(blend_path.relative_to(REPO)).replace("\\", "/"),
        "glb": str(glb_path.relative_to(REPO)).replace("\\", "/"),
        "triangles": triangle_count(),
        "visual_change": LEVEL_CHANGES[level],
    }


def main():
    generated = [build(level) for level in range(1, 16)]
    manifest = {
        "unit": "guardian",
        "display_name": "Guardian",
        "generator": "scripts/blender/generators/generate_guardian.py",
        "blender_target": "5.0.x",
        "level_count": 15,
        "design_rule": "Every level adds geometry or silhouette changes; no level is a color-only upgrade.",
        "levels": generated,
    }
    (BASE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
