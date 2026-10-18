# Digital Cell Maze Lab

An offline-first research project exploring whether an evolvable, biologically inspired computational organism can solve previously unseen mazes efficiently.

**Core concept:** One organism processes an entire maze. Its genome defines local reaction rules operating over a shared spatial substrate. A population of organisms evolves via mutation and selection. Grid sites are not separate LLM agents.

The initial project archive is available in the original ChatGPT discussion and should be imported into this repository before development. It includes `cellular_maze_lab.py`, benchmarks, tests, visualizations, and extended research documents.

## Quick start after import

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python cellular_maze_lab.py --sizes 33,65,129 --samples 6 --render --out-dir output
```

Read `AGENTS.md` and `CODEX_START_HERE.md` to continue development.

**Scientific caution:** Existing cellular implementations did not demonstrate a general speedup over compiled BFS. Do not claim an algorithmic breakthrough without fair, repeatable benchmarks.
