# SBNE_RD_GUI — Evolutionary Ecosystem Simulator (MD1/MD2 Reaction-Diffusion)

Simulation of an ecosystem of **agent-based micro-organisms** whose "brain" is a
**signed boolean network** (SBN). Agents move, see, eat and reproduce in a
**toroidal world** (wraps around: exiting right re-enters left). Each brain
mutates at reproduction — that is the source of evolution. The complete brain
history is stored in a SQLite database **as git-like deltas**.

**SBNE_RD_GUI variant**: food is modeled by a **2-matter reaction-diffusion
system** (MD1 and MD2) solved with the **ADI (Peaceman-Rachford)** scheme,
order 2 — see `ReactionDiffusion.py`.

- World: `1280 × 720` px, toroidal, pygame rendering + info bar.
  Window `1920 × 980`: world + **left panel** (explorer: parameters / agents)
  + **right panel** (brains / statistics tabs) + **control bar** (top)
  + **log console** (bottom).
- Interface: `pygame_gui` 0.6.9 (buttons, slider widgets) + custom pygame
  rendering (panels, SBN graphs, tabs, console). See `GUIInterface.py` and
  `gui_theme.json`.
- Initial population: 150 agents (configurable), each with ~1000 energy.
- **Global energy** (agents + MD1 + MD2) is **strictly conserved** at every
  step — this is the simulator's control invariant.

---

## 1. How the simulation works

### Agents
An agent has: position `(x, y)`, angle, **energy** (which it spends), and its
**SBN**. It dies when energy drops below **50** (`Agent.DEATH_ENERGY`); it
reproduces when it reaches **1200** (`DIVISION_ENERGY`): the child is placed
15 px away, in the parent's blind zone, with half the parent's energy and a
**mutated** brain.

### The brain (SBN)
- **Signed boolean network** neuron states: `0/1`, **integer** weights bounded
  by `VALEUR_MAX_POIDS` (5).
- 6 **organs** = fundamental neurons, **non-deletable** (fixed indices):

  | Index | Organ | Role |
  |---|---|---|
  | 0 | Eye (`EYE`) | Input: what the agent sees in its vision cone |
  | 1 | Mouth agents (`MOUTH`) | Action: eat another agent |
  | 2 | Mouth MD1 (`MOUTH_MD1`) | Action: consume diffuse matter 1 |
  | 3 | Mouth MD2 (`MOUTH_MD2`) | Action: consume diffuse matter 2 |
  | 4 | Fin F (`MOVE`) | Action: move forward |
  | 5 | Fin R (`ROTATE`) | Action: turn |

- The network starts with 10 nodes; other nodes and edges are free. At each
  birth, the child's brain undergoes mutations: **deletion** of node/edge
  (`PROBA_DELETION`), **insertion** (`PROBA_INSERTION`), **weight evolution**
  (`PROBA_EVOLUTION`).
- Each step: `state_out = (state @ weights > 0)`; organ outputs give actions
  (eat agent, consume MD1/MD2, move, turn).

### Energy and MD1/MD2 reaction-diffusion
- **3 mouths, 3 food sources**: an agent can eat **another agent** (duel:
  highest energy wins; tie = random), or directly consume **MD1** or **MD2**
  from the ground at its position. Each attempt costs `COST_EAT` (same for all
  3 mouths) and consumed matter becomes agent energy.
- **All spent energy is released as MD1**: metabolism, neuron costs and action
  costs (including mouths) are deposited as MD1 at the agent's position. On
  death, all remaining energy is released as MD1.
- **Diffusion**: MD1 and MD2 diffuse on the torus with coefficients `D_MD1`
  and `D_MD2` (px²/s). MD1 slowly converts to MD2 with rate `K_MD1_MD2`
  (0.1 s⁻¹; 1 iteration = 1 s).
- **Numerical scheme**: **ADI (Peaceman-Rachford)**, order 2 in space and
  time (generalized Crank-Nicolson). Each step is split into two 1D implicit
  half-steps (x then y) on the torus, solved with a **cyclic Thomas** solver
  (rank-2 correction via Woodbury — `ReactionDiffusion.py`). Matter is stored
  on a square grid with step `DX_GRID` (20 px default).
- **Conservation**: diffusion creates/destroys nothing; MD1→MD2 conversion
  transfers exactly the matter lost by MD1 to MD2. Global energy
  `Σ(agent energy) + total(MD1) + total(MD2)` is strictly constant.

### Boundary conditions
- **Matter (MD1, MD2)**: `TORIC` (wrap), `NEUMANN` (zero flux), or `DIRICHLET`
  (fixed value) — configurable per side (LEFT/RIGHT/TOP/BOTTOM) and per
  matter. Dirichlet values are editable per side/matter
  (`CL_DIRICHLET_{side}_{matter}`).
- **Agents**: `TORIC` (wrap) or `SOLID` (blocked). With `SOLID`, each side has
  a wall behavior: `AGENT_STOP` (agent stays at the wall) or `AGENT_REBOUNCE`
  (elastic reflection, like a billiard ball).

### One simulation step
1. Activate waste that has reached maturity.
2. Shuffle agents (fairness: no privileged order).
3. Rebuild the **spatial grid** (O(1) neighbor lookup instead of O(n²),
   with toroidal wrapping).
4. For each agent: **perception** (neighbors in vision cone), **SBN step**,
   actions (eat agent / consume MD1 / consume MD2 / move / turn), possible
   **division** (child acts next step) + recording mutated brain to database.
   All spent energy is released as MD1 at the agent's position.
5. Resolve duels, clean up dead (mark-and-sweep), then **reaction-diffusion**
   of MD1/MD2 field (ADI): matter diffuses and MD1 converts to MD2.

---

## 2. Graphical Interface (SBNE_RD_GUI)

The `1920 × 980` window is organized in 5 zones:

```
┌──────────────────────────────────────────────────────────────────┐
│ Control bar: [⏸ Pause][⏹ Stop][↺ Restart][🖼 Graphics] [☰ Menu] │
│                 [Refresh: 30 FPS ●──────]                        │
├──────────┬────────────────────────────────────┬──────────────────┤
│ LEFT     │  Info bar (STEPS/POP/ENERGY)       │  RIGHT PANEL     │
│ PANEL    ├────────────────────────────────────┤  BRAINS / STATS  │
│          │                                    │  [61][139][104]  │
│ EXPLORER │         WORLD (1280×720)           │  SBN graph       │
│          │         agents + matter            │                  │
│ Params   │                                    │  STATISTICS      │
│ Agents   │                                    │  Pop: 150 ...    │
│          │                                    │                  │
├──────────┴────────────────────────────────────┴──────────────────┤
│ CONSOLE (colored logs: green=info, yellow=warning, red=error)   │
└──────────────────────────────────────────────────────────────────┘
```

### Control bar (top, below info bar)
| Control | Effect |
|---|---|
| **⏸ Pause** | Toggle pause/resume (equivalent to `Space`) |
| **⏹ Stop** | Stops simulation and closes |
| **↺ Restart** | Resets simulation (new population, new `simulations/` folder) |
| **🖼 Graphics: ON/OFF** | Enable/disable rendering (compute-intensive, equivalent to `G`) |
| **☰ Menu** | Save/restore simulation and parameters (see below) |
| **Refresh: N FPS** (slider 1–60) | Graphics update frequency (sim continues without rendering) |

### Left Panel — Explorer
Two selectable tabs at the top:
- **Parameters** (default): collapsible sub-sections with editable values
  (click a value to edit, Enter = validate, Escape = cancel):
  - **Simulation**: `TEST_NAME`, `SEED`, `MAX_ITERATIONS`, `DISPLAY_REFRESH_FPS`,
    `MAX_SELECTED_SBN`
  - **Agents**: `NUM_AGENTS`, `BASE_ENERGY`, `DIVISION_ENERGY`,
    `DISTANCE_VISION`, `VISION_ANGLE`, `CONSUME_QTY`, `VALEUR_MAX_POIDS`,
    `COST_NEURON`, `COST_MOVE`, `COST_ROTATE`, `COST_EAT`, `COST_METABOLISM`
  - **Evolution**: `PROBA_EVOLUTION`, `PROBA_INSERTION`, `PROBA_DELETION`
  - **Environment**: `DX_GRID`, `NUM_MD1_INIT`, `MD1_INIT_QTY`, `D_MD1`, `D_MD2`,
    `K_MD1_MD2` + boundary conditions (see §1)
- **Agents**: list of living agents (`†` = dead). **Click = select/deselect**
  an agent for the brain tabs (click in world zone = same effect).

Boundary conditions in the Environment sub-section:
- **Matter (MD1, MD2)**: 4 sides × (MD1, MD2) buttons cycling
  `TORIC → NEUMANN → DIRICHLET`. When `DIRICHLET` is active, the value is
  editable (click to edit).
- **Agents**: 4 sides × (Agents) buttons cycling `TORIC → SOLID`. When `SOLID`
  is active, a second button appears: `AGENT_STOP` or `AGENT_REBOUNCE`
  (billiard-ball elastic reflection).

### Right Panel
- **BRAINS**: tab row (1 per selected agent, max `MAX_SELECTED_SBN` = 5).
  Each tab shows the agent's SBN (organ/internal nodes, edges +/− with weights).
  Selecting more than 5 agents → red console message.
- **STATISTICS**: population, mean energy, mean nodes, max age, agent energy,
  MD1 total, MD2 total, global energy, steps, selected agents — updated every
  frame.
- **Matter display**: keys `1` (MD1 only, green), `2` (MD2 only, red), `3`
  (MD1+MD2 blend — yellow/orange where both coexist).

### Menu (☰ button)
- **Save simulation**: pickle state (agents, field, stats, RNG) to a file.
- **Restore simulation**: load a previously saved pickle.
- **Save parameters as default**: store current PARAMS as default.
- **Save parameters to file**: JSON to a chosen path (filesystem navigation).
- **Restore default parameters**: load last saved defaults.
- **Save original parameters**: save the "origin" reference parameters.
- **Restore original parameters**: restore the origin reference.
- **Load parameters file**: load a JSON parameter file.

### Console (bottom)
Color-coded operation log:
- 🟢 **green**: common actions (start, pause, selection/deselection, tabs…)
- 🟡 **yellow**: warnings (all agents dead → pause)
- 🔴 **red**: critical errors (exceeding `MAX_SELECTED_SBN`, limits reached)

### Shortcuts (window mode)
| Key | Action |
|---|---|
| `Space` | Pause / resume |
| `G` | Enable / disable rendering |
| `V` | Show / hide vision cones |
| `1` / `2` / `3` | Matter display: MD1 / MD2 / blend |
| Left click on agent | Select/deselect agent (brain tab) |
| Left click on empty | Clear selection |

---

## 3. Project structure

| File | Role |
|---|---|
| `Environnement.py` | **Core**: `Simulation` class (main loop, logic/rendering/database orchestration, pygame_gui widgets). Entry point. |
| `GUIInterface.py` | Custom pygame widgets: `ConsoleLog`, `TabButton`, `LeftPanelTree`, `StatsPanel`, `MenuOverlay` |
| `gui_theme.json` | pygame_gui theme (button/slider/label colors) |
| `SbNetwork.py` | The brain: signed boolean network, mutations, logic step. |
| `Agent.py` | The agent: state, perception, actions, energy, division, boundary behavior. |
| `ReactionDiffusion.py` | MD1/MD2 grids + ADI solver (cyclic Thomas) for reaction-diffusion. |
| `SpatialGrid.py` | Toroidal spatial index (neighbor lookup). |
| `Interface.py` | pygame rendering: info bar, pause overlay, vision cone opacity. |
| `GraphVisualisation.py` | matplotlib graphics (summary, SBN graph). |
| `evolution_tracker.py` | **Git-like history**: snapshots + jsonpatch deltas in SQLite, reconstruction. |
| `ExportData.py` | Brain export (`save_nodes_influence`) every 50,000 steps, to `exports/`. |
| `launcher.py` | **Parallel campaign launcher** with web interface (see §8). |
| `Analyse.py` | Post-analysis pipeline on exports (pandas/seaborn/matplotlib graphics). |
| `analyse_evolution.py` | Example: reconstruct a brain at a given iteration. |
| `genealogy_viewer.py` / `genealogy_viewerv2.py` | Tkinter genealogy viewers (v2 recommended). |
| `get_agent_lineage_with_visualization.py` | Genealogy + networkx visualization (used by viewers). |
| `lignéfixv2.py` | Genealogy variant on `evolution.db` in current folder. |
| `simulations/` | One sub-folder per simulation (see §6) — local, git-ignored. |

---

## 4. Installation

### Full installation (new machine)
```bash
cd SBNE_RD_GUI
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Existing venv
```bash
.venv/bin/pip install -r requirements.txt
```

### The 8 dependencies (`requirements.txt`)

| Package | Used for |
|---|---|
| `numpy` | SBN (matrix ops), diffusion grid, network history |
| `pygame` | Window, simulation loop, toroidal world rendering |
| `pygame_gui` | UI widgets (buttons, slider, labels) — version 0.6.9 |
| `jsonpatch` | Git-like history: brain delta computation and replay |
| `seaborn` | Summary statistics and graphics |
| `matplotlib` | Summaries, SBN graphs, genealogies |
| `pandas` | Post-hoc analysis (`Analyse.py`) |
| `networkx` | Brain export (`ExportData.py`), genealogy graphs |

> ⚠️ `pygame_gui` requires `pygame ≥ 2.6.1`. Version 0.6.9 is tested and
> functional; versions ≥ 0.6.12 require `pygame ≥ 2.6.2` (not yet available
> on this machine).

Python ≥ 3.10 (tested on 3.12 and 3.13, with a clean **venv** without
`--system-site-packages`: installation + headless run verified).
**Always run with `.venv/bin/python`** (dependencies are not in system Python).

> ⚠️ **The venv is not movable.** `.venv/bin/` scripts have absolute-path
> shebangs: if you move or copy the project folder, the copied venv is broken
> (`zsh: .venv/bin/pip: bad interpreter: ... no such file or directory`).
> Worse, `python3 -m venv .venv` on an existing venv does not regenerate the
> scripts. Solution: delete and recreate in place —
> `rm -rf .venv && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.

---

## 5. Running a simulation

### With window (default)
```bash
.venv/bin/python Environnement.py
```

### Without window (compute only — for campaigns, CI, benchmarks)
```bash
.venv/bin/python Environnement.py --headless --max-steps 2000 --seed 7
```

### CLI options

| Option | Effect |
|---|---|
| `--headless` | No window (SDL dummy mode), compute only. |
| `--max-steps N` | Auto-stop after N steps. **Overrides** `PARAMS["MAX_ITERATIONS"]`. |
| `--seed N` | Override `PARAMS["SEED"]` (reproducibility). |
| `--param KEY=VALUE` | Override a `PARAMS` value (repeatable). Ex: `--param NUM_AGENTS=300 --param PROBA_INSERTION=0.6`. Values coerced to int/float/bool/str; unknown key → error (no silent typo). |
| `--outdir NAME` | Name of sub-folder created in `simulations/` (default: timestamp). |

> **Max time**: `PARAMS["MAX_ITERATIONS"]` (default `0` = unlimited) is the
> base parameter; `--max-steps` overrides it if passed.

Keyboard and mouse shortcuts are documented in §2 (graphical interface).

---

## 6. Simulation parameters (`PARAMS` in `Environnement.py`)

| Key | Default | Meaning |
|---|---|---|
| `TEST_NAME` | `RD_MD1_MD2_reaction_diffusion` | Experiment name (displayed, traced in exports). |
| `SEED` | `42` | Random seed (reproducibility). |
| `NUM_AGENTS` | `150` | Initial population. |
| `MAX_ITERATIONS` | `0` | **Max time**: max step count (0 = unlimited). |
| `BASE_ENERGY` | `1000` | Initial agent energy. |
| `DIVISION_ENERGY` | `1200` | Reproduction threshold. |
| `PROBA_DELETION` | `0.4` | Probability (at birth) of deleting a node/edge. |
| `PROBA_INSERTION` | `0.4` | Probability of inserting a node/edge. |
| `PROBA_EVOLUTION` | `0.8` | Probability of evolving a weight. |
| `VALEUR_MAX_POIDS` | `5` | Max weight amplitude (integers). |
| `DISTANCE_VISION` | `70` | Vision range (px). |
| `VISION_ANGLE` | `30` | Half-angle of vision cone (degrees). |
| `COST_NEURON` | `0.1` | Cost per neuron, per step. |
| `COST_MOVE` | `0.3` | Cost of moving. |
| `COST_ROTATE` | `0.1` | Cost of turning. |
| `COST_EAT` | `0.01` | Cost of eating / consuming MD1 / MD2 (same for 3 mouths). |
| `COST_METABOLISM` | `0.1` | Base cost per step. |
| `CONSUME_QTY` | `100.0` | Matter (MD1/MD2) consumed per mouth attempt. |
| `MAX_SELECTED_SBN` | `5` | Max selected agents (brain tabs). Exceeding → red console message. |
| `DISPLAY_REFRESH_FPS` | `30` | Graphics update frequency (render FPS; slider 1–60 in control bar). |
| `DX_GRID` | `20.0` | Matter grid step (px). |
| `D_MD1` / `D_MD2` | `0.5` | MD1/MD2 diffusion coefficients (px²/s). |
| `K_MD1_MD2` | `0.1` | MD1→MD2 conversion rate (s⁻¹). |
| `NUM_MD1_INIT` | `10` | Initial MD1 deposits. |
| `MD1_INIT_QTY` | `500.0` | Energy per initial deposit (px²·energy). |
| `CL_MD1_{side}` / `CL_MD2_{side}` | `TORIC` | Matter BC per side (TORIC / NEUMANN / DIRICHLET). |
| `CL_DIRICHLET_{side}_{matter}` | `0.0` | Dirichlet value per side and matter (MD1/MD2). |
| `CL_AGENTS_{side}` | `TORIC` | Agent BC per side (TORIC / SOLID). |
| `CL_AGENTS_WALL_{side}` | `AGENT_STOP` | Solid wall behavior per side (AGENT_STOP / AGENT_REBOUNCE). |
| `WIDTH` / `HEIGHT` | `1280` / `720` | *(options, outside PARAMS)*: world size, read if present in dict. |
| `N_ITER` | `1` | *(options, outside PARAMS)*: logic steps per frame (speeds up simulated time). |

To test a parameter variation in one command:
```bash
.venv/bin/python Environnement.py --headless --seed 3 \
    --param NUM_AGENTS=300 --param PROBA_INSERTION=0.6 --param MAX_ITERATIONS=5000 \
    --outdir essai_insertion_06
```

---

## 7. Simulation output (`simulations/<name>/`)

| File | Content |
|---|---|
| `parameters.json` | Parameters actually used (PARAMS + overrides). |
| `stats.json` | Stats history (every 100 steps): population, mean network size, mean energy, **global energy**, + final totals. |
| `evolution.db` | SQLite brain history database (see §9). |
| `simulation_summary.png` | Graphical summary at simulation end. |
| `exports/` | *(beyond 50,000 steps)* brain exports every 50,000 steps (CSV + graphs) via `ExportData.py` — feeds `Analyse.py`. |
| `campaign.json` | *(launcher)* provenance: campaign, run, seed, overrides. |
| `run.log` | *(launcher)* process output. |

---

## 8. Brain history (git-like SQLite database)

**`evolution.db`** contains three tables:

- `agents`: `id_agent`, `id_parent`, `iteration_creation` — genealogical tree.
- `networks`: `id_agent`, `iteration`, `network_data` (full JSON: states,
  weights, node identifiers), `network_hash`, `is_snapshot`.
- `commits`: `id_agent`, `iteration`, `diff_data` (**jsonpatch delta** relative
  to parent's brain), `id_parent_commit`, `message`.

Writes:
- **At each birth**: child's network recorded (full JSON in `networks` +
  **delta** relative to parent in `commits`) — a mutation = a commit.
- **Every 50,000 steps**: periodic snapshot of each living agent
  (`is_snapshot=TRUE`).

Read / reconstruction — from any Python script:
```python
from evolution_tracker import rebuild_network, close_all_connections

# Brain of agent 10 as it existed at iteration 60,000:
network = rebuild_network("simulations/<name>/evolution.db", 10, 60000)
# -> {"states": [...], "weights": [[...]]}  (network size = len(states))
close_all_connections()
```
`rebuild_network` starts from the last snapshot ≤ target iteration and
**replays deltas** (jsonpatch) — the git path. Without snapshot, it reads the
full network directly. (Full example: `analyse_evolution.py`.)

---

## 9. Parallel campaign launcher (`launcher.py`)

The real research use case = **many simulations** (different seeds/parameters).
The machine has 32 cores; the launcher exploits them.

```bash
.venv/bin/python launcher.py            # web panel at http://127.0.0.1:8765
.venv/bin/python launcher.py --port 9000
```

**Web interface** (no external dependency):
- Form: label, run count, base seed (run *i* = base + *i*), max steps
  (`0` = `MAX_ITERATIONS` applies), max parallelism (empty = auto),
  parameter overrides (one `KEY=VALUE` per line).
- Real-time tracking per campaign / per run: state, duration, step count,
  final population, output folder, population curve, log tail.
- **Stop** button: SIGTERM then **SIGKILL** after 3 s (necessary: see §11),
  unstarted runs become `skipped`.

**API** (for scripting):
```
GET  /api/state                        → full state (campaigns, runs)
POST /api/campaign                     → create: {label, n_runs, seed_base, max_steps,
                                           max_parallel, params: "KEY=VALUE\n..."}
POST /api/campaign/<id>/stop           → stop a campaign
GET  /api/run/<camp_id>/<run_id>/log   → log tail (?lines=N)
GET  /api/run/<camp_id>/<run_id>/curve → population curve {steps:[...], pop:[...]}
```

Each run is an **independent subprocess** (`Environnement.py --headless ...`)
in its own `simulations/<campaign>_seed<S>_runNN/` folder — no interference,
and 32 cores are exploited for **campaigns** (not for a single simulation).

---

## 10. Post-analysis

| Tool | Usage |
|---|---|
| `Analyse.py` | Graphical pipeline on **exports** (CSV `agents_save_*.csv` produced by `ExportData.py` every 50,000 steps): `python Analyse.py` — scans `simulations/`, generates `1_temporel/`, `2_spatial/`, `3_moyennes_barplot/`. |
| `analyse_evolution.py` | Example of brain reconstruction at an iteration (adapt `db_path`, `agent_id`, `target_iteration`). |
| `genealogy_viewerv2.py` | Tkinter genealogy viewer (v2 recommended). |
| `lignéfixv2.py` | Genealogy networkx on `evolution.db` **of current folder** (copy the base or launch from the right folder). |

Ad-hoc scripts (`analyse_evolution.py`, `lignéfixv2.py`) have the base path
**hardcoded as relative**: launch from the folder containing the target
`evolution.db`.

---

## 11. Control invariant and verification

> **Global energy is strictly conserved at every step.**
> `Σ agent.energy + total(MD1) + total(MD2)` remains constant
> (155,000.0 on reference runs). Any simulator modification that makes this
> value drift has created an energy leak/bug.

Verifications to perform **after any modification** (and before saying "it's
good"):
1. `py_compile` of modified files.
2. Short headless run (`--max-steps 2000 --seed 7`): no crash, consistent stats.
3. Compare global energy start/end of run (expected drift: **0**).
4. For pure functions (`SbNetwork`, `ReactionDiffusion`, `SpatialGrid`):
   compare outputs with fixed seed, before/after.

---

## 12. Known pitfalls

- **Headless: SIGTERM does not kill the simulation.** pygame/SDL installs a
  handler that transforms SIGTERM into a `pygame.QUIT` event; QUIT is now
  ignored in headless mode (fix 2026-10-16 — before, headless runs died
  **randomly**, sometimes after 30 steps, with truncated stats and exit 0).
  Practical consequence: to kill a headless run you must **SIGKILL** — the
  launcher escadrons automatically after 3 s of SIGTERM. In window mode, QUIT
  (close button) stops normally.
- **Reproducibility**: with the same `SEED`, a headless run is reproducible;
  beware, any change in iteration order or seed shifts the trajectory.
- **Folder collisions**: default folder name is timestamp to the second; two
  manual launches in the same second would write to the same folder. The
  launcher circumvents by always passing explicit `--outdir`.
- **Cleanup 2026-10-16**: dead duplicates (`save_network_state.py`,
  `SpatialGridAgent.py`, `simulation_setup.py`) and `*.copy.py` backups were
  removed from the repo (originals remain in git history). The local backup
  convention `FILENAME.copy.py` is covered by `.gitignore`.
- **Performance** (measured, 2026-10-16): ~8 ms/step at 150 agents (of which
  ~7 ms = matplotlib tracking graph every 100 steps, **even in headless**),
  ~62 ms/step at 500, ~1000 ms/step at 2000 (super-linear growth: at high
  population, ~47% of time = SQLite commits (one per birth), ~24% =
  perception/neighbors). Biggest win: disable graphs in headless + async
  database writes.

---

## 13. Example sessions

```bash
# Classic interactive run
.venv/bin/python Environnement.py

# Reproducible benchmark
.venv/bin/python Environnement.py --headless --max-steps 2000 --seed 7

# Manual campaign: 10 seeds, 3000 steps, 200 agents
for s in $(seq 1 10); do
  .venv/bin/python Environnement.py --headless --seed $s --max-steps 3000 \
      --param NUM_AGENTS=200 --outdir campagneA_seed$s &
done; wait

# Campaign via web panel
.venv/bin/python launcher.py
# → http://127.0.0.1:8765
```
