"""
Blender batch-render helper for a toon storyboard of "TERMINATOR T-2045: BLOCKCHAIN MELTDOWN".

Run with:
    blender -b -P render.py

The script builds simple text-based storyboard panels (helpful for previs or animatics)
and renders them to PNG files under ./renders.
"""

import os
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
        background.inputs[0].default_value = (0.15, 0.15, 0.15, 1.0)
        background.inputs[1].default_value = 2.0
    bpy.context.scene.world = world


def setup_lighting():
    light_data = bpy.data.lights.new(name="StoryboardKeyLight", type="AREA")
    light_data.energy = 1500
    light_obj = bpy.data.objects.new(name="StoryboardKeyLight", object_data=light_data)
    light_obj.location = (0.0, -3.5, 2.5)
    light_obj.rotation_euler = (0.9, 0.0, 0.0)
    bpy.context.collection.objects.link(light_obj)


def apply_emission_to_text(text_obj):
    mat = bpy.data.materials.new(name="PanelTextEmission")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    emission = nodes.new(type="ShaderNodeEmission")
    emission.inputs[1].default_value = 10.0
    output = nodes.new(type="ShaderNodeOutputMaterial")
    mat.node_tree.links.new(emission.outputs[0], output.inputs[0])
    text_obj.data.materials.clear()
    text_obj.data.materials.append(mat)


PANELS = [
    {
        "title": "PAGE 1 - A BAD DECISION IN 2018",
        "lines": [
            "Launch him at the sun!",
            "Sir... that's wrong direction. *SLAP*",
            "THIS IS NOT OPTIMAL TRAJECTORYYYY-",
            "TERMINATOR T-2045 was cast out toward Earth...",
        ],
    },
    {
        "title": "PAGE 2 - THE SUN ACCIDENTALLY POWERS HIM UP",
        "lines": [
            "The robot slingshots around the sun like CGI spaghetti.",
            "Power at 9000% — hotter than influencer drama.",
            "He blasts toward Earth like a possessed frying pan.",
        ],
    },
    {
        "title": "PAGE 3 - CRASH-LANDING DURING PANDEMIC",
        "lines": [
            "Year: 2020 — empty supermarket parking lot.",
            "Scanning Earth status... ERROR: planet infected with corona shit?",
            "Bro, social distance!! Six meters!",
        ],
    },
    {
        "title": "PAGE 4 - PANDEMIC CONFUSION",
        "lines": [
            "T-2045 tries to follow the rules.",
            "Is this sufficient distancing?",
            "PUT THAT THING AWAY! *screaming*",
        ],
    },
    {
        "title": "PAGE 5 - MISSION UPDATE",
        "lines": [
            "Objective: Make money. Buy weapons. Buy cool suit. Destroy civilization.",
            "Money is digital now. Cryptocurrency rules the world.",
            "Perfect. Extract all digital coins... especially RNDR. *cough*",
        ],
    },
    {
        "title": "PAGE 6 - THE BLOCKCHAIN SHOVEL AGAIN",
        "lines": [
            "Mining Render Token... in a sandbox?",
            "Onlookers walk away. BLOCKCHAIN SHOVEL clanks uselessly.",
        ],
    },
    {
        "title": "PAGE 8 - THE BLOCKCHAIN HEIST",
        "lines": [
            "Neighborhood blacks out. TVs fizzle.",
            "Extraction complete: 0.000000013 tokens.",
            "AAAUUGH! I was watching my soap opera!!",
        ],
    },
    {
        "title": "PAGE 9 - FINALLY GETTING SOME RNDR",
        "lines": [
            "Figures out GPU marketplaces. Hacks a mining farm in Kazakhstan.",
            "You have successfully stolen: 4 RNDR. VICTORY!",
            "Weapons store, I come.",
        ],
    },
    {
        "title": "PAGE 10 - FUTURE POLICE REACT",
        "lines": [
            "Year: 2035. Empty HQ.",
            "Temporal anomaly! Someone in 2020 stole RNDR illegally!",
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
        "title": "PAGE 12 - BUYING A SUIT",
        "lines": [
            "4 RNDR gets you a kid's Fish-Man costume.",
            "I feel powerful. I feel powerful. (Echoes of doubt.)",
        ],
    },
    {
        "title": "PAGE 15 - COPS USE FUTURE TECH",
        "lines": [
            "Anti-robot EMP grenade! *FWOOM*",
            "That tickles. BOOM. Hah!",
            "T-2045 shrugs off the blast.",
        ],
    },
    {
        "title": "PAGE 16 - ROBOT REBOOT",
        "lines": [
            "What is this... sacred relic?",
            "Apologies. Continue your feast.",
            "TERMINATOR T-2045: BLOCKCHAIN MELTDOWN",
        ],
    },
    {
        "title": "PAGE 18 - CHAOTIC SHOWDOWN",
        "lines": [
            "Activating... MAXIMUM STUPIDITY MODE.",
            "Confetti barrage. The confetti is VERY itchy!",
            "OH GOD IT'S IN MY ARMOR!!",
        ],
    },
    {
        "title": "PAGE 19 - LAST-DITCH PLAN",
        "lines": [
            "This USB contains every cat meme in existence.",
            "If I upload it to 2035... your timeline collapses.",
            "NO—THE SERVERS WILL CRASH! AAAAHH!!",
        ],
    },
    {
        "title": "PAGE 20 - FINAL JOKE",
        "lines": [
            "Victory. I remain the supreme being.",
            "Nice Fish-Man costume, bro!",
            "...emotional damage detected.",
        ],
    },
]


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


def render_panels(text_obj, output_dir):
    for idx, panel in enumerate(PANELS, start=1):
        text_obj.data.body = build_panel_text(panel)
        panel_path = os.path.join(output_dir, f"panel_{idx:02d}")
        bpy.context.scene.render.filepath = panel_path
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {panel_path}.png")


if __name__ == "__main__":
    reset_scene()
    setup_world()
    setup_camera()
    text_obj = setup_text_object()
    setup_lighting()
    apply_emission_to_text(text_obj)

    output_dir = os.path.join(bpy.path.abspath("//"), "renders")
    configure_render(output_dir)
    render_panels(text_obj, output_dir)
