# 4090

## Blender storyboard renderer
Use `render.py` to build quick storyboard frames for **TERMINATOR T-2045: BLOCKCHAIN MELTDOWN**.

Run in Blender (headless or GUI):
```bash
blender -b -P render.py
```
Frames render to `./renders/panel_XX.png` alongside your current working directory. No existing `.blend` file is required because the script builds the scene from scratch.
