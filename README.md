# DnD ML

Welcome to **DnD ML** — a set of small experiments combining Dungeons & Dragons with machine learning. I built these tools because I enjoy applying AI/ML to creative projects, and because I’m developing a DnD-inspired game that can directly benefit from them.

## Tools

| Tool | Description |
|------|-------------|
| **Battlemaps LoRA (SDXL)** | A LoRA for generating DnD-style battlemaps, built on **SDXL Base 1.0**. <br>Available here: https://civitai.com/models/2164519/dnd-battlemaps-generator |
| **Terrain Labeling** <br>`src/terrain_labeling` | Uses CLIP and depth models to analyze top-down battlemaps, label terrain types, and estimate walkable areas. Outputs a structured grid for further use. |
| **More soon** | More tools will be added as development continues. |

## Installation

I use `uv` to manage dependencies because it’s fast and lightweight.

1. Install uv: https://github.com/astral-sh/uv  
2. Sync the environment:

```bash
uv sync
```

## Usage

Run any tool through uv run. For example:

```bash
uv run src/terrain_labeling/main.py
```

That’s it. Thanks for checking out the project, all contribution are welcomed.
