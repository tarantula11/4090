# /render_toon_storyboard.py
"""
Toon Storyboard Renderer for "TERMINATOR T-2045: BLOCKCHAIN MELTDOWN"

- Factory-resets Blender and builds everything (world, camera, toon lights/materials).
- Adds two simple characters (Robot + Cop), speech bubbles with tails, and Freestyle outlines.
- Renders text-driven panels from ./scripts/*.txt (falls back to built-in panels).
- Supports per-speaker prefixes (L:/R:/NARRATOR:/CAPTION:) and clamps bubbles to a safe frame area.
- Headless-safe. Works in Blender 3.6+ (Eevee + Freestyle).
Run:
    blender -b -P render_toon_storyboard.py
Quick syntax check without Blender:
    python -m compileall render_toon_storyboard.py
Output:
    ./renders/panel_XX.png
Environment knobs:
    RESX/RESY     - output resolution (default 1280x720)
    BG            - world hex color (default #1e2230)
    WORLD_INT     - world intensity (default 1.0)
    SAFE          - safe-frame fraction (default 0.9)
    TAILS         - 1/0 to enable/disable bubble tails (default 1)
"""

import glob
import math
import os
import sys

import bpy
from mathutils import Euler, Vector

# --------------------------- Env helpers ---------------------------

def env_str(name, default):
    v = os.environ.get(name)
    return v if v not in (None, "") else default

def env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except Exception:
        return default

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path

def cwd_base():
    try:
        return os.path.abspath(os.getcwd())
    except Exception:
        return os.path.abspath(os.path.dirname(sys.argv[0]))

# --------------------------- Render defaults ---------------------------

def set_evee_filmic_defaults():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    ee = scene.eevee
    ee.use_soft_shadows = True
    ee.use_gtao = True
    ee.use_bloom = True
    ee.use_ssr = True
    ee.ssr_thickness = 1.0
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "High Contrast"
    scene.view_settings.exposure = 0.0
    scene.display_settings.display_device = "sRGB"
    scene.use_nodes = False  # disable compositor

def clean_factory_reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    set_evee_filmic_defaults()

# --------------------------- World / Camera / Lights ---------------------------

def set_world(bg_hex="#1e2230", intensity=1.0):
    hex_str = bg_hex.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join([c * 2 for c in hex_str])
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0
    world = bpy.data.worlds.new("World") if not bpy.data.worlds else bpy.data.worlds[0]
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (r, g, b, 1.0)
    bg.inputs["Strength"].default_value = intensity
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

def make_camera_ortho(name="Camera", ortho_scale=18.0, location=(0, -14, 7), look_at=(0, 0, 1.6)):
    cam_data = bpy.data.cameras.new(name)
    cam_obj = bpy.data.objects.new(name, cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = ortho_scale
    cam_obj.location = Vector(location)
    direction = Vector(look_at) - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam_obj
    return cam_obj

def make_area_light(name, energy=1000.0, size=3.0, location=(0, 0, 0), rotation=(0, 0, 0), color=(1, 1, 1)):
    light_data = bpy.data.lights.new(name=name, type="AREA")
    light_data.energy = energy
    light_data.color = color
    light_data.shape = "SQUARE"
    light_data.size = size
    light_obj = bpy.data.objects.new(name, light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.location = Vector(location)
    light_obj.rotation_euler = Euler(rotation, "XYZ")
    return light_obj

def build_three_point_rig():
    make_area_light("Key", 2500.0, 4.0, (-4, -6, 6), (math.radians(60), 0, math.radians(-20)))
    make_area_light("Fill", 900.0, 5.0, (5, -4, 4), (math.radians(55), 0, math.radians(20)))
    make_area_light("Rim", 1800.0, 3.0, (0, 6, 5), (math.radians(-110), 0, 0), (0.95, 1.0, 1.0))

# --------------------------- Materials & Characters ---------------------------

def make_toon_material(name="Toon", hue=0.6, sat=0.7, val=0.9, size=0.25, smooth=0.05):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    toon = nt.nodes.new("ShaderNodeBsdfToon")
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Hue"].default_value = hue
    hsv.inputs["Saturation"].default_value = sat
    hsv.inputs["Value"].default_value = val
    toon.inputs["Size"].default_value = size
    toon.inputs["Smooth"].default_value = smooth
    nt.links.new(hsv.outputs["Color"], toon.inputs["Color"])
    nt.links.new(hsv.outputs["Color"], diff.inputs["Color"])
    nt.links.new(toon.outputs["BSDF"], mix.inputs[1])
    nt.links.new(diff.outputs["BSDF"], mix.inputs[2])
    mix.inputs["Fac"].default_value = 0.35
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat

def make_capsule(name, height=3.0, radius=0.55, location=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=max(height - 2 * radius, 0.001), location=location)
    cyl = bpy.context.active_object
    cyl.name = name + "_Body"
    top_loc = (location[0], location[1], location[2] + height / 2 - radius)
    bot_loc = (location[0], location[1], location[2] - height / 2 + radius)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=radius, location=top_loc)
    top = bpy.context.active_object
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=radius, location=bot_loc)
    bot = bpy.context.active_object
    for o in [top, bot]:
        o.select_set(True)
    cyl.select_set(True)
    bpy.context.view_layer.objects.active = cyl
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    return obj

def enable_freestyle(thickness_px=1.5):
    scn = bpy.context.scene
    scn.render.use_freestyle = True
    vl = bpy.context.view_layer
    fs = vl.freestyle_settings
    fs.use_smoothness = True
    fs.linesets.clear()
    line_set = fs.linesets.new("LineSet")
    styles = bpy.data.linestyles
    style = styles["ToonStyle"] if "ToonStyle" in styles else styles.new("ToonStyle")
    style.color = (0, 0, 0)
    style.thickness = thickness_px
    line_set.linestyle = style
    line_set.select_silhouette = True
    line_set.select_border = True
    line_set.select_crease = True
    scn.view_layers.update()

def make_text(name, text, size=0.6, location=(0, 0, 0), alignment="CENTER"):
    bpy.ops.object.text_add(location=location)
    txt = bpy.context.active_object
    txt.name = name
    txt.data.body = text
    txt.data.align_x = alignment
    txt.data.align_y = "CENTER"
    txt.data.extrude = 0.0
    txt.data.space_line = 1.0
    txt.data.size = size
    txt.rotation_euler = Euler((math.radians(90), 0, math.radians(180)), "XYZ")
    return txt

# --------------------------- Bubble system ---------------------------

def new_backplate(size=(10, 4), color=(1, 1, 1, 1)):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0))
    pl = bpy.context.active_object
    sx, sy = size
    pl.scale = (sx / 2, sy / 2, 1)
    bpy.ops.object.modifier_add(type="BEVEL")
    pl.modifiers["Bevel"].segments = 3
    pl.modifiers["Bevel"].width = 0.15
    mat = bpy.data.materials.new("BubbleMat")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.9
    bsdf.inputs["Specular"].default_value = 0.0
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    pl.data.materials.append(mat)
    return pl

def new_tail(name="Tail", length=1.2, width=0.5):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    import bmesh

    bm = bmesh.new()
    v0 = bm.verts.new((0, 0, 0))
    v1 = bm.verts.new((length, width / 2, 0))
    v2 = bm.verts.new((length, -width / 2, 0))
    bm.faces.new((v0, v1, v2))
    bm.to_mesh(mesh)
    bm.free()
    return obj

def make_bubble(name, text_size=0.55, with_tail=True):
    grp = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(grp)
    txt = make_text(name + "_Text", "", size=text_size, location=(0, 0, 0))
    plate = new_backplate()
    txt.parent = plate
    tail = None
    if with_tail:
        tail = new_tail(name + "_Tail")
        tail.parent = plate
    return {"group": grp, "plate": plate, "text": txt, "tail": tail, "active": True}

def approx_text_box(obj, char_w=0.45, char_h=0.8, padding=(0.8, 0.6)):
    lines = obj.data.body.splitlines() or [""]
    width = max(len(l) for l in lines) * char_w + padding[0]
    height = len(lines) * char_h + padding[1]
    return width, height

def place_bubble(bub, center: Vector, text_body: str, clamp_rect, target=None, side="C", tail_on=True):
    bub["text"].data.body = text_body
    w, h = approx_text_box(bub["text"])
    plate = bub["plate"]
    plate.scale = (max(3.2, w / 2), max(1.4, h / 2), 1)
    pos = Vector(center)
    minx, maxx, minz, maxz = clamp_rect
    pos.x = max(minx, min(maxx, pos.x))
    pos.z = max(minz, min(maxz, pos.z))
    plate.location = (pos.x, -0.05, pos.z)
    if bub.get("tail") and tail_on and target is not None:
        tail = bub["tail"]
        sx = plate.scale.x
        edge_local = Vector((-sx if side == "L" else (sx if side == "R" else 0), 0, 0))
        world_edge = plate.matrix_world @ Vector((edge_local.x, edge_local.y, 0))
        vec = Vector((target.x - world_edge.x, 0, target.z - world_edge.z))
        angle = math.atan2(vec.z, vec.x)
        tail.location = edge_local
        tail.rotation_euler = Euler((0, 0, angle), "XYZ")
        dist = max(0.5, min(2.5, vec.length))
        tail.scale = (dist, 1.0, 1.0)
    elif bub.get("tail"):
        bub["tail"].location = (0, 0, -1000)

def toggle_bubble(bub, show=True):
    objs = [bub.get("plate"), bub.get("text"), bub.get("tail")]
    for obj in objs:
        if not obj:
            continue
        obj.hide_viewport = not show
        obj.hide_render = not show
    bub["active"] = show

# --------------------------- Camera safe area ---------------------------

def camera_safe_rect(cam_obj, resx, resy, safe=0.9):
    scale_w = cam_obj.data.ortho_scale
    aspect = resy / resx
    half_w = scale_w / 2.0
    half_h = (scale_w * aspect) / 2.0
    half_w *= safe
    half_h *= safe
    return (-half_w, half_w, 0.5, 0.5 + 2 * half_h)

# --------------------------- Panel parsing ---------------------------

def discover_script_files(scripts_dir):
    return sorted(glob.glob(os.path.join(scripts_dir, "*.txt")))

def parse_panel_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        lines = [ln.rstrip() for ln in handle.readlines() if ln.strip() != ""]
    title = lines[0] if lines else "Untitled"
    body_lines = lines[1:] if len(lines) > 1 else []
    return title, body_lines

def builtin_story():
    return [
        (
            "TERMINATOR T-2045 — BLOCKCHAIN MELTDOWN (Cover)",
            ["CAPTION: When ledgers go sentient, only one node can roll back time."],
        ),
        (
            "Page 1: A New Fork",
            ["L: Consensus achieved. Humanity… not so much.", "NARRATOR: Night falls over Silicon Wasteland."],
        ),
        (
            "Page 2: Gas Fees",
            ["R: Deploying patch…", "L: Denied. Immutable.", "CAPTION: *hashrate screams*"],
        ),
        (
            "Page 3: Cold Storage",
            ["NARRATOR: In the ruins, two wallets meet.", "R: You with me?", "L: I am inevitable."],
        ),
    ]

def load_panels_from_folder(scripts_dir):
    files = discover_script_files(scripts_dir)
    if not files:
        return builtin_story()
    panels = []
    for file_path in files:
        title, body_lines = parse_panel_file(file_path)
        panels.append((title, body_lines))
    return panels

# --------------------------- Stage setup ---------------------------

def build_stage():
    clean_factory_reset()
    set_world(bg_hex=env_str("BG", "#1e2230"), intensity=env_float("WORLD_INT", 1.0))
    cam = make_camera_ortho(ortho_scale=18.0, location=(0, -14, 7), look_at=(0, 0, 1.6))
    build_three_point_rig()
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.001))
    bpy.context.active_object.name = "Ground"
    left = make_capsule("Hero_T2045", 3.2, 0.6, (-2.5, 0, 1.6), make_toon_material("ToonBlue", 0.6, 0.6, 0.9))
    right = make_capsule("Hacker", 3.0, 0.55, (2.5, 0, 1.5), make_toon_material("ToonRed", 0.0, 0.7, 0.95))
    title = make_text("PanelTitle", "TITLE", size=0.7, location=(0, 0.0, 6.2))
    enable_freestyle(1.5)
    tails_enabled = int(env_float("TAILS", 1)) != 0
    pool = [make_bubble(f"Bubble_{i:02d}", text_size=0.55, with_tail=tails_enabled) for i in range(1, 7)]
    return {"camera": cam, "left": left, "right": right, "title": title, "bubbles": pool}

# --------------------------- Layout & Render ---------------------------

def actor_heads(stage):
    left = stage["left"].location.copy()
    right = stage["right"].location.copy()
    left.z += 1.2
    right.z += 1.1
    return left, right

def layout_panel(stage, title_txt: str, lines, resx, resy):
    cam = stage["camera"]
    safe = float(env_float("SAFE", 0.9))
    minx, maxx, minz, maxz = camera_safe_rect(cam, resx, resy, safe=safe)
    title = stage["title"]
    title.data.body = title_txt
    title.location = Vector((0, 0.0, maxz - 0.4))
    left_head, right_head = actor_heads(stage)
    items = []
    for raw in lines:
        text = raw.strip()
        lower = text.lower()
        if lower.startswith("l:"):
            items.append(("L", text[2:].strip()))
        elif lower.startswith("r:"):
            items.append(("R", text[2:].strip()))
        elif lower.startswith("narrator:") or lower.startswith("caption:"):
            items.append(("C", text.split(":", 1)[1].strip()))
        else:
            items.append(("C", text))
    if not items:
        items = [("C", "")]
    y_top = maxz - 1.2
    y_left = maxz - 2.2
    y_right = maxz - 2.2
    col_left = (minx + (minx + maxx) / 2) * 0.5
    col_right = (maxx + (minx + maxx) / 2) * 0.5
    center_x = 0.0
    for bubble in stage["bubbles"]:
        toggle_bubble(bubble, False)
    idx = 0
    for role, text in items:
        if idx >= len(stage["bubbles"]):
            break
        bubble = stage["bubbles"][idx]
        toggle_bubble(bubble, True)
        if role == "C":
            pos = Vector((center_x, 0, y_top))
            y_top -= 1.6
            place_bubble(bubble, pos, text, (minx, maxx, minz, maxz), target=None, side="C", tail_on=False)
        elif role == "L":
            pos = Vector((col_left, 0, y_left))
            y_left -= 1.8
            place_bubble(bubble, pos, text, (minx, maxx, minz, maxz), target=left_head, side="L", tail_on=True)
        elif role == "R":
            pos = Vector((col_right, 0, y_right))
            y_right -= 1.8
            place_bubble(bubble, pos, text, (minx, maxx, minz, maxz), target=right_head, side="R", tail_on=True)
        idx += 1

def set_render_output(base_dir, filename, resx=1280, resy=720):
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = os.path.join(base_dir, filename)
    scene.render.resolution_x = int(resx)
    scene.render.resolution_y = int(resy)
    scene.render.resolution_percentage = 100

def render_panels(stage, panels, out_dir, resx=1280, resy=720):
    ensure_dir(out_dir)
    for idx, (title, body_lines) in enumerate(panels, start=1):
        layout_panel(stage, title, body_lines, resx, resy)
        fname = f"panel_{idx:02d}.png"
        set_render_output(out_dir, fname, resx=resx, resy=resy)
        bpy.ops.render.render(write_still=True, use_viewport=False)
        print(f"[OK] Rendered {os.path.join(out_dir, fname)}")

# --------------------------- Main ---------------------------

def main():
    base = cwd_base()
    scripts_dir = os.path.join(base, "scripts")
    out_dir = os.path.join(base, "renders")
    resx = int(env_float("RESX", 1280))
    resy = int(env_float("RESY", 720))
    panels = load_panels_from_folder(scripts_dir)
    stage = build_stage()
    render_panels(stage, panels, out_dir, resx=resx, resy=resy)

if __name__ == "__main__":
    main()
