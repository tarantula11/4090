"""One-command T-2045 previs renderer (safer defaults).

This script fixes black/white frames by force-configuring each scene with:
- Eevee/Filmic settings and the compositor disabled
- A tinted world background with adjustable intensity
- A key light, ground plane, optional backdrop card, and camera that tracks origin
- Lightweight placeholders per scene (rocket, sun, portal, or labeled sign)
- Optional toon look (flat shading + inverted-hull outline)

Outputs MP4 (H.264) or PNG image sequences per scene. Designed for Blender 3.6.

Usage examples:
    # MP4 render with toon placeholders, darker BG
    OUT=/abs/renders FORMAT=MP4 CRF=18 PRESET=GOOD APPLY_TOON=1 BG="#1e2230" \
      blender -b your_project.blend -P tools/t2045_all_in_one_v2.py

    # PNG sequences at 1280x720 without toon look
    OUT=/abs/renders FORMAT=PNG RESX=1280 RESY=720 APPLY_TOON=0 \
      blender -b your_project.blend -P tools/t2045_all_in_one_v2.py
"""

from math import radians
import os
import bpy


# ---------------------- Environment controls ----------------------
OUT = os.environ.get("OUT", "//renders")
RESX = int(os.environ.get("RESX", "1920"))
RESY = int(os.environ.get("RESY", "1080"))
FPS = int(os.environ.get("FPS", "24"))
FORMAT = os.environ.get("FORMAT", "MP4").upper()  # MP4 or PNG
CRF = os.environ.get("CRF")
VBR = int(os.environ.get("VBR", "12000"))
GOP = int(os.environ.get("GOP", "24"))
PRESET_IN = os.environ.get("PRESET", "GOOD")
SKIP_MASTER = os.environ.get("SKIP_MASTER", "1") not in ("0", "false", "False")
APPLY_TOON = os.environ.get("APPLY_TOON", "0") in ("1", "true", "True")
BACKDROP = os.environ.get("BACKDROP", "1") in ("1", "true", "True")
FOG = os.environ.get("FOG", "0") in ("1", "true", "True")
WORLD_INT = float(os.environ.get("WORLD_INT", "0.8"))
BG = os.environ.get("BG", "#2a2f3a")


# ---------------------- Utility helpers ----------------------
def activate_scene(scene: bpy.types.Scene) -> None:
    """Ensure operators run on the intended scene in background mode."""
    window = getattr(bpy.context, "window", None)
    if window and window.scene != scene:
        window.scene = scene


def hex_to_rgba(hexstr: str, alpha: float = 1.0):
    hs = hexstr.strip().lstrip("#")
    if len(hs) == 3:
        hs = "".join(c * 2 for c in hs)
    r = int(hs[0:2], 16) / 255.0
    g = int(hs[2:4], 16) / 255.0
    b = int(hs[4:6], 16) / 255.0
    return (r, g, b, alpha)


def map_preset(preset: str) -> str:
    preset = (preset or "").upper()
    realtime = {"ULTRAFAST", "SUPERFAST", "VERYFAST", "FASTER", "FAST", "REALTIME"}
    best = {"SLOWER", "VERYSLOW", "BEST"}
    if preset in realtime:
        return "REALTIME"
    if preset in best:
        return "BEST"
    return "GOOD"


# ---------------------- Scene scaffolding ----------------------
def set_eevee(scene: bpy.types.Scene) -> None:
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = RESX
    scene.render.resolution_y = RESY
    scene.render.fps = FPS
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "Medium High Contrast"
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = 0.2
    scene.eevee.use_bloom = True
    scene.eevee.use_ssr = True
    scene.eevee.use_soft_shadows = True


def ensure_world(scene: bpy.types.Scene) -> None:
    if not scene.world:
        scene.world = bpy.data.worlds.new(f"{scene.name}_World")
    scene.world.use_nodes = True
    nodes = scene.world.node_tree.nodes
    bg = nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (*hex_to_rgba(BG)[:3], 1.0)
        bg.inputs[1].default_value = WORLD_INT
    if FOG and "Volume Scatter" not in nodes:
        vol = nodes.new("ShaderNodeVolumeScatter")
        vol.inputs["Density"].default_value = 0.02
        output = nodes.get("World Output")
        scene.world.node_tree.links.new(vol.outputs["Volume"], output.inputs["Volume"])


def ensure_key_light(scene: bpy.types.Scene) -> None:
    if any(obj.type == "LIGHT" for obj in scene.objects):
        return
    data = bpy.data.lights.new(f"{scene.name}_Key", type="AREA")
    data.energy = 1200
    data.size = 3.0
    obj = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(obj)
    obj.location = (3.0, -7.0, 5.0)
    obj.rotation_euler = (radians(60), 0.0, radians(-18))


def ensure_ground(scene: bpy.types.Scene) -> bpy.types.Object:
    ground = scene.objects.get("Ground")
    if ground:
        return ground
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    return ground


def ensure_backdrop(scene: bpy.types.Scene) -> None:
    if not BACKDROP:
        return
    if scene.objects.get("Backdrop"):
        return
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 10, 10))
    backdrop = bpy.context.active_object
    backdrop.name = "Backdrop"
    backdrop.rotation_euler = (radians(90), 0.0, 0.0)


def ensure_camera_track(scene: bpy.types.Scene) -> bpy.types.Object:
    target = scene.objects.get("LookTarget")
    if target is None:
        target = bpy.data.objects.new("LookTarget", None)
        scene.collection.objects.link(target)
        target.location = (0.0, 0.0, 1.2)

    camera = scene.camera
    if camera is None:
        camera = next((obj for obj in scene.objects if obj.type == "CAMERA"), None)
    if camera is None:
        camera = bpy.data.objects.new(f"{scene.name}_AutoCam", bpy.data.cameras.new(f"{scene.name}_AutoCam"))
        scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.lens = 35
    camera.location = (0.0, -10.0, 4.0)
    camera.rotation_euler = (radians(70), 0.0, 0.0)
    if not any(c.type == "TRACK_TO" for c in camera.constraints):
        constraint = camera.constraints.new(type="TRACK_TO")
        constraint.target = target
        constraint.track_axis = "TRACK_NEGATIVE_Z"
        constraint.up_axis = "UP_Y"
    return camera


# ---------------------- Previz placeholders ----------------------
def make_if_missing(scene: bpy.types.Scene, name: str, builder) -> bpy.types.Object:
    existing = scene.objects.get(name)
    if existing:
        return existing
    activate_scene(scene)
    obj = builder()
    obj.name = name
    return obj


def make_rocket():
    bpy.ops.mesh.primitive_cone_add(radius1=0.7, depth=2.5, location=(0, 0, 1.6))
    rocket = bpy.context.active_object
    bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=1.4, location=(0, 0, 0.7))
    body = bpy.context.active_object
    body.parent = rocket
    return rocket


def make_sun():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=3.0, location=(0, 6, 3))
    sun = bpy.context.active_object
    sun.data.materials.clear()
    mat = bpy.data.materials.new("SunMat")
    mat.use_nodes = True
    nt = mat.node_tree
    emis = nt.nodes.new("ShaderNodeEmission")
    output = nt.nodes.get("Material Output")
    emis.inputs[0].default_value = (1.0, 0.7, 0.1, 1.0)
    emis.inputs[1].default_value = 4.0
    nt.links.new(emis.outputs[0], output.inputs[0])
    sun.data.materials.append(mat)
    return sun


def make_ship():
    bpy.ops.mesh.primitive_cube_add(size=2.2, location=(0, 0, 1.2))
    return bpy.context.active_object


def make_portal():
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 2.0), major_radius=2.0, minor_radius=0.2)
    return bpy.context.active_object


def make_sign(text: str = "SCENE"):
    curve = bpy.data.curves.new(type="FONT", name="SignCurve")
    obj = bpy.data.objects.new("Sign", curve)
    bpy.context.scene.collection.objects.link(obj)
    curve.size = 0.8
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.body = text
    obj.location = (0, 0, 2.6)
    return obj


def populate_scene(scene: bpy.types.Scene) -> None:
    name = scene.name.lower()
    if name.startswith("s01"):
        make_if_missing(scene, "Rocket", make_rocket)
    elif name.startswith("s02"):
        make_if_missing(scene, "Sun", make_sun)
    elif name.startswith("s03"):
        make_if_missing(scene, "Ship", make_ship)
    elif name.startswith("s09"):
        make_if_missing(scene, "Portal", make_portal)
    elif name.startswith("s04"):
        make_if_missing(scene, "Sign", lambda: make_sign("DISTANCE!!"))
    elif name.startswith("s05"):
        make_if_missing(scene, "Sign", lambda: make_sign("0.000000013 RNDR"))
    elif name.startswith("s06"):
        make_if_missing(scene, "Sign", lambda: make_sign("BLACKOUT"))
    elif name.startswith("s07"):
        make_if_missing(scene, "Sign", lambda: make_sign("RUBBER KNIFE"))
    elif name.startswith("s08"):
        make_if_missing(scene, "Sign", lambda: make_sign("FISH-MAN"))
    elif name.startswith("s10"):
        make_if_missing(scene, "Sign", lambda: make_sign("MAX STUPIDITY"))
    elif name.startswith("s11"):
        make_if_missing(scene, "Sign", lambda: make_sign("UPLOAD MEMES"))
    elif name.startswith("s12"):
        make_if_missing(scene, "Sign", lambda: make_sign("THE END"))
    else:
        make_if_missing(scene, "Sign", lambda: make_sign(scene.name))


# ---------------------- Toon look (optional) ----------------------
def make_toon_mat(name: str, color=(0.9, 0.9, 0.9, 1), emis: float = 0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for node in list(nt.nodes):
        nt.nodes.remove(node)
    output = nt.nodes.new("ShaderNodeOutputMaterial")
    toon = nt.nodes.new("ShaderNodeBsdfToon")
    toon.inputs["Color"].default_value = color
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diff.inputs["Color"].default_value = color
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = 0.35
    add = nt.nodes.new("ShaderNodeAddShader")
    emis_node = nt.nodes.new("ShaderNodeEmission")
    emis_node.inputs[1].default_value = emis
    nt.links.new(toon.outputs[0], mix.inputs[1])
    nt.links.new(diff.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], add.inputs[0])
    nt.links.new(emis_node.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], output.inputs[0])
    return mat


def ensure_outline_mat():
    existing = bpy.data.materials.get("OutlineBlack")
    if existing:
        return existing
    mat = bpy.data.materials.new("OutlineBlack")
    mat.use_nodes = True
    nt = mat.node_tree
    for node in list(nt.nodes):
        nt.nodes.remove(node)
    output = nt.nodes.new("ShaderNodeOutputMaterial")
    emission = nt.nodes.new("ShaderNodeEmission")
    emission.inputs[0].default_value = (0, 0, 0, 1)
    emission.inputs[1].default_value = 1.0
    nt.links.new(emission.outputs[0], output.inputs[0])
    mat.shadow_method = "NONE"
    mat.use_backface_culling = False
    return mat


def add_outline(obj: bpy.types.Object, thickness: float = 0.03) -> None:
    if not getattr(obj.data, "polygons", None):
        return
    outline_mat = ensure_outline_mat()
    dup = obj.copy()
    dup.data = obj.data.copy()
    dup.name = f"{obj.name}_Outline"
    obj.users_collection[0].objects.link(dup)
    dup.parent = obj
    dup.data.materials.clear()
    dup.data.materials.append(outline_mat)
    mod = dup.modifiers.new(name="OutlineSolidify", type="SOLIDIFY")
    mod.thickness = -thickness
    mod.offset = 1.0
    mod.use_flip_normals = True
    dup.hide_select = True


def apply_toon(scene: bpy.types.Scene) -> None:
    if not APPLY_TOON:
        return
    base = make_toon_mat("ToonBase", (*hex_to_rgba("#dfe7f2")[:3], 1), 0.0)
    accent = make_toon_mat("ToonAccent", (*hex_to_rgba("#3a7bd5")[:3], 1), 0.2)
    for obj in scene.objects:
        if obj.type == "MESH" and obj.name in {"Rocket", "Ship", "Portal", "Sun", "Sign", "Ground", "Backdrop"}:
            obj.data.materials.clear()
            obj.data.materials.append(accent if obj.name in {"Sun", "Portal", "Sign"} else base)
            add_outline(obj, 0.025)


# ---------------------- Output configuration ----------------------
def set_output_mp4(scene: bpy.types.Scene) -> None:
    scene.render.use_file_extension = True
    scene.render.image_settings.file_format = "FFMPEG"
    ff = scene.render.ffmpeg
    ff.format = "MPEG4"
    ff.codec = "H264"
    ff.ffmpeg_preset = map_preset(PRESET_IN)
    ff.gopsize = GOP
    ff.audio_codec = "AAC"
    ff.audio_bitrate = 192
    ff.audio_channels = "STEREO"
    if hasattr(ff, "use_max_b_frames"):
        ff.use_max_b_frames = True
    if CRF not in (None, ""):
        try:
            crf = int(CRF)
        except ValueError:
            crf = 18
        ff.constant_rate_factor = "HIGH" if crf <= 18 else ("MEDIUM" if crf <= 23 else "LOW")
        ff.video_bitrate = 0
    else:
        ff.constant_rate_factor = "MEDIUM"
        ff.video_bitrate = max(1000, VBR)


def set_output_png(scene: bpy.types.Scene) -> None:
    scene.render.image_settings.file_format = "PNG"


# ---------------------- Main per-scene processing ----------------------
def process_scene(scene: bpy.types.Scene, out_dir: str) -> None:
    activate_scene(scene)
    scene.use_nodes = False  # disable compositor to avoid accidental black frames
    set_eevee(scene)
    ensure_world(scene)
    ensure_key_light(scene)
    ensure_ground(scene)
    ensure_backdrop(scene)
    populate_scene(scene)
    apply_toon(scene)
    camera = ensure_camera_track(scene)

    target_dir = os.path.join(out_dir, scene.name)
    os.makedirs(target_dir, exist_ok=True)

    if FORMAT == "MP4":
        set_output_mp4(scene)
        scene.render.filepath = os.path.join(target_dir, scene.name)
        print(f"[Render:MP4] {scene.name} -> {scene.render.filepath}.mp4 (cam={camera.name})")
        bpy.ops.render.render(animation=True, scene=scene.name)
    else:
        set_output_png(scene)
        scene.render.filepath = os.path.join(target_dir, scene.name + "_")
        print(f"[Render:PNG] {scene.name} -> {scene.render.filepath}####.png (cam={camera.name})")
        bpy.ops.render.render(animation=True, scene=scene.name)


def main():
    out_dir = bpy.path.abspath(OUT)
    os.makedirs(out_dir, exist_ok=True)
    for scene in bpy.data.scenes:
        if SKIP_MASTER and scene.name.upper() == "MASTER":
            print(f"[Skip] {scene.name} (MASTER)")
            continue
        process_scene(scene, out_dir)
    print("All-in-one v2 render complete.")


if __name__ == "__main__":
    main()
