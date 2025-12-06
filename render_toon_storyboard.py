# /render_toon_storyboard.py
"""
Toon Storyboard Renderer for "TERMINATOR T-2045: BLOCKCHAIN MELTDOWN"

- Factory-resets Blender and builds everything (world, camera, toon lights/materials).
- Adds two simple characters (Robot + Cop), speech bubbles, and Freestyle outlines.
- Renders text-driven panels from ./scripts/*.txt (falls back to built-in panels).
- Headless-safe. Works in Blender 3.6+ (Eevee + Freestyle).
Run:
    blender -b -P render_toon_storyboard.py
Quick syntax check without Blender:
    python -m compileall render_toon_storyboard.py
Output:
    ./renders/panel_XX.png
"""

import os
from math import radians
from pathlib import Path

import bpy
from mathutils import Vector

# ----------------------------- Helpers -----------------------------

def factory_reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def first_view_layer(scene: bpy.types.Scene):
    # robustly get the first view layer regardless of name
    if scene.view_layers:
        return scene.view_layers[0]
    # create one if somehow missing
    bpy.ops.scene.view_layer_add()
    return scene.view_layers[0]

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

# ----------------------------- Render & world -----------------------------

def setup_render(output_dir: str):
    scn = bpy.context.scene
    scn.render.engine = "BLENDER_EEVEE"
    scn.render.resolution_x = 1920
    scn.render.resolution_y = 1080
    scn.render.film_transparent = False
    scn.view_settings.view_transform = "Filmic"
    scn.view_settings.look = "High Contrast"
    scn.eevee.use_gtao = True
    scn.eevee.gtao_distance = 0.2
    scn.eevee.use_bloom = True
    scn.eevee.use_ssr = True
    scn.eevee.use_soft_shadows = True
    scn.eevee.taa_render_samples = 64
    scn.render.image_settings.file_format = "PNG"
    scn.render.filepath = output_dir
    ensure_dir(output_dir)

def setup_world():
    world = bpy.data.worlds.new("ToonWorld")
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.96, 0.97, 1.0, 1.0)  # soft paper
        bg.inputs[1].default_value = 1.0
    bpy.context.scene.world = world

# ----------------------------- Camera & lights -----------------------------

def setup_camera():
    cam = bpy.data.cameras.new("Cam")
    cam.lens = 35
    o = bpy.data.objects.new("Cam", cam)
    bpy.context.collection.objects.link(o)
    o.location = (0.0, -7.0, 2.2)
    o.rotation_euler = (radians(68), 0.0, 0.0)
    bpy.context.scene.camera = o
    return o

def setup_lights():
    def area(name, loc, rot, power, size=2.6):
        data = bpy.data.lights.new(name=name, type="AREA")
        data.energy = power
        data.size = size
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = loc
        obj.rotation_euler = rot
        return obj
    area("Key",  (2.8, -3.0, 3.2), (radians(65), 0, radians(-20)), 1400)
    area("Fill", (-3.5, -1.0, 2.5), (radians(70), 0, radians(25)), 600)
    area("Rim",  (0.0,  3.0, 3.5),  (radians(110), 0, 0),          900)

# ----------------------------- Materials -----------------------------

def make_toon_mat(name, color=(0.85, 0.88, 0.95, 1), emission=0.0, rough=0.1, size=0.25, smooth=0.05):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    toon = nt.nodes.new("ShaderNodeBsdfToon")
    toon.inputs["Color"].default_value = color
    toon.inputs["Size"].default_value = size
    toon.inputs["Smooth"].default_value = smooth
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diff.inputs["Roughness"].default_value = rough
    diff.inputs["Color"].default_value = color
    emis = nt.nodes.new("ShaderNodeEmission")
    emis.inputs["Color"].default_value = color
    emis.inputs["Strength"].default_value = emission
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(toon.outputs[0], mix.inputs[1])
    nt.links.new(diff.outputs[0], mix.inputs[2])
    mix.inputs[0].default_value = 0.35
    nt.links.new(mix.outputs[0], add.inputs[0])
    nt.links.new(emis.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs[0])
    return mat

def get_or_create(name, build_fn):
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    return build_fn()

# ----------------------------- Freestyle (outlines) -----------------------------

def setup_freestyle():
    scn = bpy.context.scene
    vl = first_view_layer(scn)
    vl.use_freestyle = True
    fs = vl.freestyle_settings
    for ls in list(fs.linesets):
        fs.linesets.remove(ls)
    style = bpy.data.linestyles.get("ToonLines")
    if not style:
        style = bpy.data.linestyles.new("ToonLines")
    style.thickness = 1.5
    style.color = (0, 0, 0)
    style.use_chaining = True
    style.chaining = 'PLAIN'
    lset = fs.linesets.new("ToonLineSet")
    lset.linestyle = style
    lset.select_by_visibility = True
    lset.select_silhouette = True
    lset.select_border = True
    lset.select_crease = True

# ----------------------------- Characters -----------------------------

def make_robot():
    parts = []

    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.6, location=(0, 0, 1.7))
    head = bpy.context.active_object
    parts.append(head)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.65, depth=1.2, location=(0, 0, 0.9))
    torso = bpy.context.active_object
    parts.append(torso)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=1.0, location=(-0.35, 0, 0.15))
    leg_l = bpy.context.active_object
    parts.append(leg_l)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=1.0, location=(0.35, 0, 0.15))
    leg_r = bpy.context.active_object
    parts.append(leg_r)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.8, location=(-0.75, 0, 1.2))
    arm_l = bpy.context.active_object
    parts.append(arm_l)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.8, location=(0.75, 0, 1.2))
    arm_r = bpy.context.active_object
    parts.append(arm_r)

    bot = bpy.data.objects.new("Robot", None)
    bpy.context.collection.objects.link(bot)
    for p in parts:
        p.parent = bot

    steel = get_or_create("ToonSteel", lambda: make_toon_mat("ToonSteel", (0.65, 0.7, 0.75, 1), emission=0.0))
    visor = get_or_create("ToonVisor", lambda: make_toon_mat("ToonVisor", (0.1, 0.4, 1.0, 1), emission=0.4))
    for p in [head, torso, leg_l, leg_r, arm_l, arm_r]:
        p.data.materials.clear()
        p.data.materials.append(steel)

    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0.55, 1.8))
    v = bpy.context.active_object
    v.scale = (0.6, 0.05, 0.18)
    v.data.materials.append(visor)
    v.parent = bot

    bot.location = (-0.8, 0, 0)
    bot.rotation_euler = (0, 0, radians(10))
    return bot

def make_cop():
    parts = []
    bpy.ops.mesh.primitive_cube_add(size=1.2, location=(0, 0, 1.0))
    body = bpy.context.active_object
    parts.append(body)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 1.8))
    head = bpy.context.active_object
    parts.append(head)
    bpy.ops.mesh.primitive_cone_add(radius1=0.7, depth=0.25, location=(0, 0, 2.25))
    hat = bpy.context.active_object
    parts.append(hat)
    char = bpy.data.objects.new("Cop", None)
    bpy.context.collection.objects.link(char)
    for p in parts:
        p.parent = char

    blue = get_or_create("ToonBlue", lambda: make_toon_mat("ToonBlue", (0.1, 0.2, 0.7, 1)))
    skin = get_or_create("ToonSkin", lambda: make_toon_mat("ToonSkin", (1.0, 0.83, 0.7, 1)))
    hatm = get_or_create("ToonHat", lambda: make_toon_mat("ToonHat", (0.05, 0.05, 0.05, 1)))
    body.data.materials.clear()
    body.data.materials.append(blue)
    head.data.materials.clear()
    head.data.materials.append(skin)
    hat.data.materials.clear()
    hat.data.materials.append(hatm)

    char.location = (1.1, 0, 0)
    char.rotation_euler = (0, 0, radians(-8))
    return char

# ----------------------------- Speech bubbles -----------------------------

def make_rounded_rect(name="BubbleRect", size=(3.2, 1.6), radius=0.25, loc=(0, 0, 0.0)):
    w, h = size
    r = min(radius, min(w, h) / 2 - 1e-3)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc)
    rect = bpy.context.active_object
    rect.name = name
    rect.scale = (w / 2, h / 2, 1)
    bpy.ops.object.modifier_add(type='BEVEL')
    rect.modifiers["Bevel"].width = r
    rect.modifiers["Bevel"].segments = 8
    rect.modifiers["Bevel"].affect = 'EDGES'
    bpy.ops.object.shade_smooth()
    return rect

def add_tail(parent_obj, side=1):
    bpy.ops.mesh.primitive_cone_add(radius1=0.18, depth=0.35, location=(0, 0, 0))
    tri = bpy.context.active_object
    tri.rotation_euler = (radians(90), 0, radians(90 if side > 0 else -90))
    tri.location = (parent_obj.location.x + (parent_obj.scale.x + 0.2) * side,
                    parent_obj.location.y, parent_obj.location.z - parent_obj.scale.y * 0.6)
    tri.parent = parent_obj
    return tri

def make_text_obj(body, size=0.28, wrap_width=24):
    words = body.split()
    lines = []
    cur = ""
    for w in words:
        if len(cur) + len(w) + 1 > wrap_width:
            lines.append(cur.strip())
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    txt_data = bpy.data.curves.new(type="FONT", name="BubbleTextCurve")
    txt = bpy.data.objects.new("BubbleText", txt_data)
    bpy.context.collection.objects.link(txt)
    txt.data.align_x = "CENTER"
    txt.data.align_y = "CENTER"
    txt.data.size = size
    txt.location = (0, 0, 0)
    txt.data.body = "\n".join(lines)
    return txt

def make_speech_bubble(text, loc=(0, 0, 2.9), side=1):
    rect = make_rounded_rect(size=(3.2, 1.6), radius=0.25, loc=loc)
    white = get_or_create("ToonWhite", lambda: make_toon_mat("ToonWhite", (1, 1, 1, 1), rough=0.0))
    rect.data.materials.clear()
    rect.data.materials.append(white)

    tail = add_tail(rect, side=side)
    tail.data.materials.clear()
    tail.data.materials.append(white)

    txt = make_text_obj(text)
    txt.location = rect.location.copy()
    txt.location.z += 0.02
    txt.parent = rect
    tmat = get_or_create("TextBlack", lambda: make_toon_mat("TextBlack", (0, 0, 0, 1)))
    txt.data.materials.clear()
    txt.data.materials.append(tmat)

    grp = bpy.data.objects.new("Bubble", None)
    bpy.context.collection.objects.link(grp)
    rect.parent = grp
    tail.parent = grp
    grp.location = (0, 0, 0)
    return grp

def clear_old_bubbles():
    for o in [o for o in bpy.context.scene.objects if o.name.startswith(("Bubble", "BubbleText", "BubbleRect"))]:
        bpy.data.objects.remove(o, do_unlink=True)

# ----------------------------- Titles -----------------------------

def ensure_title_obj():
    if "PanelTitle" in bpy.data.objects:
        return bpy.data.objects["PanelTitle"]
    curv = bpy.data.curves.new(type="FONT", name="PanelTitleCurve")
    o = bpy.data.objects.new("PanelTitle", curv)
    bpy.context.collection.objects.link(o)
    o.data.align_x = "CENTER"
    o.data.align_y = "TOP_BASELINE"
    o.data.size = 0.35
    o.location = (0, 0, 3.8)
    o.data.body = ""
    mat = get_or_create("TextBlack", lambda: make_toon_mat("TextBlack", (0, 0, 0, 1)))
    o.data.materials.append(mat)
    return o

# ----------------------------- Ground & shots -----------------------------

def place_ground():
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    p = bpy.context.active_object
    p.name = "Ground"
    p.data.materials.append(get_or_create("ToonGround", lambda: make_toon_mat("ToonGround", (0.95, 0.96, 1.0, 1))))
    return p

def set_shot(cam, kind="two_shot"):
    if kind == "close_robot":
        cam.location = (-0.8, -4.5, 1.6)
        cam.rotation_euler = (radians(68), 0, radians(8))
    elif kind == "close_cop":
        cam.location = (1.2, -4.5, 1.6)
        cam.rotation_euler = (radians(68), 0, radians(-8))
    elif kind == "wide":
        cam.location = (0.0, -8.5, 2.6)
        cam.rotation_euler = (radians(70), 0, 0)
    else:
        cam.location = (0.0, -7.0, 2.2)
        cam.rotation_euler = (radians(68), 0, 0)

def layout_bubbles(lines):
    clear_old_bubbles()
    spots = [
        (Vector((-2.8, 0, 3.0)), 1),
        (Vector((2.8, 0, 3.0)), -1),
        (Vector((-2.6, 0, 1.0)), 1),
        (Vector((2.6, 0, 1.0)), -1),
    ]
    for i, text in enumerate(lines[:4]):
        loc, side = spots[i]
        make_speech_bubble(text, loc=tuple(loc), side=side)

# ----------------------------- Panels -----------------------------

DEFAULT_PANELS = [
    {
        "title": "TITLE - TERMINATOR T-2045: BLOCKCHAIN MELTDOWN",
        "lines": [
            "Cyber-comedy / sci-fi stupidity",
            "Use TERMINATOR T-2045",
            "BLOCKCHAIN MELTDOWN",
            "CYBER-COMEDY / SCI-FI STUPIDITY",
        ],
    },
    {
        "title": "PAGE 1 - A BAD DECISION IN 2018",
        "lines": [
            "Launch him at the sun!",
            "That'll show those aliens! *SLAP*",
            "Sir... that's wrong direction.",
            "THIS IS NOT OPTIMAL TRAJECTORYYYYY-",
        ],
    },
    {
        "title": "PAGE 2 - THE SUN ACCIDENTALLY POWERS HIM UP",
        "lines": [
            "The robot slingshots around the sun like a CGI spaghetti noodle.",
            "Power at 900%.",
            "I am now hotter than influencer drama.",
            "Power at 9000%.",
        ],
    },
    {
        "title": "PAGE 3 - CRASH-LANDING DURING PANDEMIC",
        "lines": [
            "Year: 2020. Location: Empty supermarket parking lot.",
            "Scanning Earth status... ERROR: planet infected with... corona shit?",
            "Bro, social distance!! Six meters! AT LEAST!",
        ],
    },
]

def load_panels_from_directory(base_dir: Path):
    scripts_dir = base_dir / "scripts"
    if not scripts_dir.exists():
        return None
    files = sorted(p for p in scripts_dir.glob("*.txt") if p.is_file())
    if not files:
        return None
    panels = []
    for f in files:
        rows = f.read_text(encoding="utf-8").splitlines()
        if not rows:
            continue
        title = rows[0].strip()
        lines = [r.strip() for r in rows[1:] if r.strip()]
        panels.append({"title": title, "lines": lines})
    return panels or None

# ----------------------------- Build & Render -----------------------------

def build_scene():
    factory_reset()
    setup_world()
    cam = setup_camera()
    setup_lights()
    place_ground()
    make_robot()
    make_cop()
    setup_freestyle()
    return cam

def render_panels(panels, output_dir, cam):
    title_obj = ensure_title_obj()
    for i, panel in enumerate(panels, start=1):
        shot = ("two_shot", "wide", "close_robot", "close_cop")[i % 4]
        set_shot(cam, shot)
        title_obj.data.body = panel.get("title", "")[:80]
        layout_bubbles(panel.get("lines", []))
        panel_path = os.path.join(output_dir, f"panel_{i:02d}.png")
        bpy.context.scene.render.filepath = panel_path
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {panel_path}")

def main():
    cam = build_scene()
    base_dir = Path(bpy.path.abspath("//"))
    output_dir = os.path.join(base_dir, "renders")
    panels = load_panels_from_directory(base_dir) or DEFAULT_PANELS
    setup_render(output_dir)
    render_panels(panels, output_dir, cam)

if __name__ == "__main__":
    main()
