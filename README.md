# 4090

## Blender toon storyboard renderer
Use `render_toon_storyboard.py` to build toon-style storyboard frames for **TERMINATOR T-2045: BLOCKCHAIN MELTDOWN**. The script constructs the entire scene from scratch (factory reset, world/camera, toon lights, toon materials, characters, speech bubbles, and Freestyle outlines) so no `.blend` starter file is required.

Run in Blender (headless or GUI):
```bash
blender -b -P render_toon_storyboard.py
```
Frames render to `./renders/panel_XX.png` alongside your working directory.

Quick syntax check without Blender (verifies the file parses):
```bash
python -m compileall render_toon_storyboard.py
```

### Authoring your own panels

1. Create a `scripts/` folder next to `render_toon_storyboard.py`.
2. Add numbered `.txt` files (e.g., `panel_01.txt`, `panel_02.txt`).
3. Put the panel title on the first line and the panel dialogue/action on the following lines. Blank lines are ignored.

When the folder exists, the renderer will render your custom files in alphabetical order. If no files are present, it falls back to the built-in Terminator T-2045 storyboard text.

### Included sample script

This repository ships with a prewritten **TERMINATOR T-2045** storyboard under `scripts/` (cover + pages 1–20). You can use it as-is to generate panels or as a template for your own `.txt` files.
