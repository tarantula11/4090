"""
Blender batch-render helper for a toon storyboard of "TERMINATOR T-2045: BLOCKCHAIN MELTDOWN".

Run with:
    blender -b -P render.py

The script builds simple text-based storyboard panels (helpful for previs or animatics)
and renders them to PNG files under ./renders.
"""

import os
from pathlib import Path

import bpy


# Clean out the default cube/light/camera to start from a blank slate.
def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in bpy.data.meshes:
        bpy.data.meshes.remove(block)
    for block in bpy.data.cameras:
        bpy.data.cameras.remove(block)
    for block in bpy.data.lights:
        bpy.data.lights.remove(block)
    for block in bpy.data.worlds:
        bpy.data.worlds.remove(block)


def setup_camera():
    cam_data = bpy.data.cameras.new("StoryboardCamera")
    cam_obj = bpy.data.objects.new("StoryboardCamera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = (0.0, -6.0, 0.5)
    cam_obj.rotation_euler = (1.57, 0.0, 0.0)  # Point toward the origin.
    bpy.context.scene.camera = cam_obj
    return cam_obj


def setup_text_object():
    font_curve = bpy.data.curves.new(type="FONT", name="PanelText")
    font_obj = bpy.data.objects.new("PanelText", font_curve)
    font_obj.data.align_x = "CENTER"
    font_obj.data.align_y = "CENTER"
    font_obj.data.size = 0.5
    font_obj.location = (0.0, 0.0, 0.0)
    bpy.context.collection.objects.link(font_obj)
    return font_obj


def setup_world():
    world = bpy.data.worlds.new("StoryboardWorld")
    world.use_nodes = True
    nodes = world.node_tree.nodes
    background = nodes.get("Background")
    if background:
        background.inputs[0].default_value = (0.35, 0.35, 0.4, 1.0)
        background.inputs[1].default_value = 4.0
    bpy.context.scene.world = world


def setup_lighting():
    light_data = bpy.data.lights.new(name="StoryboardKeyLight", type="AREA")
    light_data.energy = 2000
    light_obj = bpy.data.objects.new(name="StoryboardKeyLight", object_data=light_data)
    light_obj.location = (0.0, -3.5, 2.5)
    light_obj.rotation_euler = (0.9, 0.0, 0.0)
    bpy.context.collection.objects.link(light_obj)

    fill_data = bpy.data.lights.new(name="StoryboardFillLight", type="AREA")
    fill_data.energy = 750
    fill_data.shape = "DISK"
    fill_obj = bpy.data.objects.new(name="StoryboardFillLight", object_data=fill_data)
    fill_obj.location = (-3.0, 2.5, 1.5)
    fill_obj.rotation_euler = (1.0, 0.0, 2.2)
    bpy.context.collection.objects.link(fill_obj)


def apply_emission_to_text(text_obj):
    mat = bpy.data.materials.new(name="PanelTextEmission")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    emission = nodes.new(type="ShaderNodeEmission")
    emission.inputs[1].default_value = 25.0
    output = nodes.new(type="ShaderNodeOutputMaterial")
    mat.node_tree.links.new(emission.outputs[0], output.inputs[0])
    text_obj.data.materials.clear()
    text_obj.data.materials.append(mat)


# Default panels used when no custom script files are found in ./scripts.
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
            "TERMINATOR T-2045 was cast out toward Earth...",
        ],
    },
    {
        "title": "PAGE 2 - THE SUN ACCIDENTALLY POWERS HIM UP",
        "lines": [
            "The robot slingshots around the sun like a CGI spaghetti noodle.",
            "Power at 900%.",
            "I am now hotter than influencer drama.",
            "Power at 9000%.",
            "He blasts toward Earth like a possessed frying pan.",
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
    {
        "title": "PAGE 4 - PANDEMIC CONFUSION",
        "lines": [
            "T-2045 tries to follow the rules.",
            "Is this sufficient distancing?",
            "PUT THAT THING AWAY!",
            "*SCREAMING*",
        ],
    },
    {
        "title": "PAGE 5 — MISSION UPDATE",
        "lines": [
            "Objective: Make money. Buy weapons. Buy cool suit. Destroy civilization (standard).",
            "Money is digital now; cryptocurrency rules the world.",
            "Perfect. I will extract all digital coins. Especially... RNDR.",
            "*cough* *COUGH* Apologies. *SWEATS*",
        ],
    },
    {
        "title": "PAGE 6 - THE 'BLOCKCHAIN SHOVEL' AGAIN",
        "lines": [
            "BLOCKCHAIN SHOVEL: What are you doing?",
            "Mining Render Token... in a sandbox?",
            "Onlookers walk away.",
        ],
    },
    {
        "title": "PAGE 7 - RUBBER KNIFE REWARD",
        "lines": [
            "With 4 RNDR you can buy... one rubber knife.",
            "I will take it.",
            "I will take... refund.",
        ],
    },
    {
        "title": "PAGE 8 - THE BLOCKCHAIN HEIST",
        "lines": [
            "Entire neighborhood blacks out.",
            "MMFF... ZZT. Extraction complete: 0.000000013 tokens.",
            "AAAUUGH! I was watching my soap opera!!",
        ],
    },
    {
        "title": "PAGE 9 - FINALLY GETTING SOME RNDR",
        "lines": [
            "He figures out GPU marketplaces.",
            "He hacks a mining farm in Kazakhstan.",
            "You have successfully stolen: 4 RNDR. VICTORY!",
            "Weapons store: I come.",
        ],
    },
    {
        "title": "PAGE 10 - FUTURE POLICE REACT",
        "lines": [
            "Year: 2035. Location: Empty HQ.",
            "Sir! A temporal anomaly! Someone in 2020 stole RNDR illegally!",
            "Chef? Oh god.",
            "Deploy the Time Police.",
        ],
    },
    {
        "title": "PAGE 11 - T-2045 GOES SHOPPING",
        "lines": [
            "With 4 RNDR you can buy... one rubber knife.",
            "Give me a refund or fear my Fish-Man costume!",
            "FEAR MY FISH-MAN COSTUME!",
        ],
    },
    {
        "title": "PAGE 12 — BUYING A SUIT",
        "lines": [
            "T-2045 vs Rubber Knife physics.",
            "4 RNDR gets you... a kid's Fish-Man costume.",
            "I feel powerful.",
            "I feel powerful.",
        ],
    },
    {
        "title": "PAGE 13 - DISTANCING MAYHEM",
        "lines": [
            "T-2045 tries to follow the rules.",
            "IS THIS SUFFICIENT DISTANCING?",
            "AAAH! AAAHH!",
            "PUT THAT THING AWAY!",
        ],
    },
    {
        "title": "PAGE 14 - TIME POLICE DEPLOYED",
        "lines": [
            "TIME POLICE DEPLOYED.",
            "BZZZAAAAAР! Freeze, blockchain criminal!",
            "You travel from the future? ...No.",
            "Does my Fish-Man suit intimidate you?",
        ],
    },
    {
        "title": "PAGE 15 - COPS USE FUTURE TECH",
        "lines": [
            "Anti-robot EMP grenade! FWO!",
            "That tickle. BOOM. Hah!",
            "T-2045 shrugs off the blast.",
        ],
    },
    {
        "title": "PAGE 16 — ROBOT REBOOT",
        "lines": [
            "What is this... sacred relic?",
            "Apologies. Continue your feast.",
            "TERMINATOR T-2045: BLOCKCHAIN MELTDOWN",
        ],
    },
    {
        "title": "PAGE 17 - FISH-MAN SHOWDOWN",
        "lines": [
            "Time Police arrive, portals blazing.",
            "Freeze, blockchain criminal!",
            "Intriguing. Does my Fish-Man suit intimidate you?",
            "Cue awkward standoff.",
        ],
    },
    {
        "title": "PAGE 18 - CHAOTIC SHOWDOWN",
        "lines": [
            "Activating... MAXIMUM STUPIDITY MODE",
            "Is that supposed to do something?",
            "The confetti is VERY itchy.",
            "OH GOD IT'S IN MY ARMOR!!",
        ],
    },
    {
        "title": "PAGE 19 - LAST-DITCH PLAN",
        "lines": [
            "This USB contains every cat meme in existence.",
            "If I upload it to 2035... your timeline collapses.",
            "NO- THE SERVERS WILL CRASH!",
            "AAAAHH!!",
        ],
    },
    {
        "title": "PAGE 20 - FINAL JOKE",
        "lines": [
            "Victory. I remain the supreme being.",
            "Nice Fish-Man costume, bro!",
            "...emotional damage detected.",
            "...emotional damage. THE END",
        ],
    },
]


def load_panels_from_directory(base_dir: Path):
    scripts_dir = base_dir / "scripts"
    if not scripts_dir.exists():
        return None

    panel_files = sorted(p for p in scripts_dir.glob("*.txt") if p.is_file())
    if not panel_files:
        return None

    panels = []
    for panel_file in panel_files:
        text = panel_file.read_text(encoding="utf-8").splitlines()
        if not text:
            continue
        title = text[0].strip()
        lines = [line.strip() for line in text[1:] if line.strip()]
        panels.append({"title": title, "lines": lines})

    return panels or None


def configure_render(output_dir: str):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = output_dir
    os.makedirs(output_dir, exist_ok=True)


def build_panel_text(panel):
    title = panel.get("title", "")
    lines = panel.get("lines", [])
    return title + "\n\n" + "\n".join(lines)


def render_panels(text_obj, output_dir, panels):
    for idx, panel in enumerate(panels, start=1):
        text_obj.data.body = build_panel_text(panel)
        panel_path = os.path.join(output_dir, f"panel_{idx:02d}")
        bpy.context.scene.render.filepath = panel_path
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {panel_path}.png")


def build_storyboard_scene():
    """Reset Blender and create a minimal storyboard setup from scratch."""

    reset_scene()
    setup_world()
    setup_camera()
    text_obj = setup_text_object()
    setup_lighting()
    apply_emission_to_text(text_obj)
    return text_obj


if __name__ == "__main__":
    text_obj = build_storyboard_scene()

    base_dir = Path(bpy.path.abspath("//"))
    output_dir = os.path.join(base_dir, "renders")
    panels = load_panels_from_directory(base_dir) or DEFAULT_PANELS
    configure_render(output_dir)
    render_panels(text_obj, output_dir, panels)
