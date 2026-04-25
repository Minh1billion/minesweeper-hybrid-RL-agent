# 🧠 Minesweeper AI — Hybrid Q-Learning Agent

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![RL](https://img.shields.io/badge/AI-Reinforcement%20Learning-green)
![Built With](https://img.shields.io/badge/Built%20With-Pygame-black)
![Q-Learning](https://img.shields.io/badge/Algorithm-Q--Learning-red)
![Visualization](https://img.shields.io/badge/UI-Debuggable-blueviolet)
![Game AI](https://img.shields.io/badge/Domain-Minesweeper-orange)
![Architecture](https://img.shields.io/badge/Architecture-Hybrid%20AI-purple)
![Win Rate](https://img.shields.io/badge/Win%20Rate-~40%25-brightgreen)
![Status](https://img.shields.io/badge/Status-Stable-success)
![License](https://img.shields.io/badge/License-MIT-yellow)

A high-performance **hybrid AI system** that learns to play Minesweeper by combining **rule-based constraint reasoning + reinforcement learning (Q-table)**.

> 🎯 Achieves ~39–40% win rate (all-time) / ~55% (peak) rolling win rate on a 10×10 board with 15 mines after 50,000 training episodes.

---

## 🚀 Overview

This project explores how **symbolic reasoning and reinforcement learning can complement each other** in a partially observable, stochastic environment like Minesweeper.

The agent is designed as a **multi-layer decision system** with a strict priority chain:

```
Constraint Solver  →  Probability Filter  →  Q-Table  →  Random Fallback
     (certain)            (high-confidence)   (ambiguous)   (last resort)
```

Each layer only activates when the previous layer cannot produce a decision, ensuring the most logically grounded action is always preferred.

---

## 🧠 How It Works — Full Pipeline

### Layer 1: Constraint Solver (Deterministic Logic)

The agent scans all revealed cells and applies simple logical rules:

- If a revealed number cell has exactly as many hidden neighbors as its remaining mine count → **all hidden neighbors are mines** → flag them.
- If a revealed number cell has its mine count already satisfied by flags → **all remaining hidden neighbors are safe** → reveal them.

This handles the vast majority of moves (~87% of all decisions in training). It is completely deterministic and never makes mistakes.

**Coverage in training:** `constraint:mine` 32.8% + `constraint:safe` 54.7% = **~87.5% of all steps**

---

### Layer 2: Probability Filter (Statistical Heuristic)

When the constraint solver cannot determine a cell definitively, the agent estimates **mine probability** for each frontier cell (hidden cells adjacent to revealed numbers):

```
P(mine | cell) = average over all revealed neighbors of:
    (neighbor_value - flagged_count) / hidden_neighbor_count
```

Two thresholds apply:
- If `max_prob ≥ 0.80` → the highest-probability cell is flagged as a mine.
- If `min_prob ≤ 0.20` → the lowest-probability cell is revealed as safe.

**Coverage in training:** `prob:mine` ~0% + `prob:safe` ~7.3% = **~7.3% of all steps**

> The `prob:mine` rate is near zero because the constraint solver usually catches mines first. The probability filter primarily catches near-certain safe cells that single-constraint logic misses.

---

### Layer 3: Q-Learning Agent (Ambiguous Situations)

When neither certainty nor high-confidence probability is available, the Q-table decides. The agent:

1. Collects all **frontier candidates** (hidden cells adjacent to any revealed tile within a VR=2 radius).
2. Encodes each candidate as a **5×5 local observation window** — a tuple of cell states (hidden, flagged, number 0–8, or out-of-bounds).
3. Queries the Q-table: selects the candidate with the **highest max(Q_reveal, Q_flag)**.
4. Executes the chosen action.

**The Q-table maps local board states → action values (reveal / flag)** using standard Bellman update:

```
Q(s, a) ← Q(s, a) + α × (r + γ × max_a' Q(s', a') − Q(s, a))
```

- `α = 0.15` (learning rate)
- `γ = 0.90` (discount factor)
- ε-greedy exploration: starts at 1.0, decays to 0.05 over training

**Coverage in training:** ~5.2% of all steps

---

### Layer 4: Random Fallback (Irreducible Uncertainty)

When there are no frontier candidates at all (e.g., board is entirely disconnected from the revealed region), the agent picks a random hidden cell. This is the last resort and accounts for ~0% of steps in a trained agent, since the board almost always has a reachable frontier.

---

## 📦 Project Structure

```
.
├── gym.py           # Training entry point
├── inference.py     # Inference entry point (no learning)
├── agent.py         # Q-learning agent (Q-table, update, save/load)
├── trainer.py       # Training loop — executes decision pipeline + Q-updates
├── environment.py   # Minesweeper board, constraint solver, probability estimation
├── ui.py            # Real-time visualization (pygame)
├── qtable.json      # Persisted Q-values
```

---

## 📊 Training Results

| Metric | Value |
|---|---|
| Training episodes | 50,000 |
| Total steps | ~1,176,250 |
| Q-states learned | ~1,831,754 |
| Win rate (all-time) | **39.76%** |
| Win rate (rolling 200 ep) | **~37–55%** |
| Wins / Losses | 19,850 / 30,120 |
| ε at end of training | 0.05 (min) |

### Decision Source Breakdown (Lifetime Steps)

| Source | Count | Share |
|---|---|---|
| constraint:mine | 385,641 | 32.8% |
| constraint:safe | 643,107 | 54.7% |
| prob:safe | 86,115 | 7.3% |
| q-table | 61,180 | 5.2% |
| prob:mine | 166 | ~0% |
| random | 41 | ~0% |

> 💡 **Key insight:** The system relies on logical reasoning for ~87% of decisions. RL only intervenes in genuinely ambiguous situations — and does so meaningfully, not randomly.

---

## 🔬 Design Decisions

### Local State Representation (5×5 Window, VR=2)

Instead of encoding the full board, each cell is described by a 25-element tuple of its 5×5 neighborhood. This:
- Keeps the Q-table feasible (tabular, ~1.8M states)
- Focuses learning on the local spatial patterns that actually determine risk
- Avoids the combinatorial explosion of full-board state

### Frontier-Only Evaluation

The agent only considers **cells adjacent to the revealed frontier**, not the full hidden grid. This:
- Reduces irrelevant candidates
- Concentrates Q-learning on the cells where decisions actually matter
- Mimics how a human player thinks

### Confidence-Guided Q-Selection

Rather than choosing a Q-table action for any hidden cell, the agent picks the frontier candidate with the **highest Q-value magnitude** (max over both actions). This means the agent acts only where it has the most learned signal — low-confidence cells are left to the probability layer or random fallback.

### Hybrid Over Pure RL

Pure Q-learning on Minesweeper converges extremely slowly due to:
- Sparse and delayed rewards
- Partially observable state (the full mine layout is hidden)
- Large state space

The hybrid approach reaches near-optimal performance far faster by offloading deterministic decisions to the constraint solver, leaving RL to learn only the genuinely ambiguous cases.

---

## 🎯 Performance Context

Minesweeper on a 10×10 board with 15 mines has a **theoretical win ceiling of ~50–55%** for any non-guessing solver, because a significant fraction of games require at least one blind guess. The agent's ~40% all-time / ~55% rolling win rate is therefore near the practical ceiling for a local-state tabular approach.

---

## 🛠️ Tech Stack

- Python 3.10+
- Pygame (visualization + real-time debug UI)
- Tabular Q-Learning (custom implementation, no frameworks)
- Custom constraint solver + probability estimator

---

## 🔮 Future Improvements

- **Global constraint propagation** (subset reasoning between multiple numbered cells)
- **Feature-based state encoding** instead of raw grid (adjacency features, symmetry)
- **Deep RL (CNN)** for global board pattern recognition
- **Tank solver** for exact mine-counting across overlapping constraint sets

---

## 🧪 Debug UI Features

- Real-time board visualization with mine reveal toggle
- Per-step decision source label (constraint / prob / q-table / random)
- Frontier cell Q-value inspection (Q_reveal, Q_flag, probability)
- Win rate chart (rolling 200 games) + episode reward chart
- Training speed control (+/- keys)

---

## 🚀 Quick Start

```bash
pip install pygame numpy

# Train for 20,000 episodes
python gym.py --epochs 20000

# Watch the trained agent play
python inference.py
```

## 🎮 Controls

### Training Mode

| Key | Action |
|---|---|
| SPACE | Toggle auto training |
| ENTER | Step manually |
| +/- | Adjust speed |
| S | Save Q-table |
| N | New episode |
| M | Show/hide mines |
| Q / ESC | Quit |

### Inference Mode

| Key | Action |
|---|---|
| SPACE | Toggle auto-play |
| ENTER | Step / next game |
| +/- | Adjust speed |
| N | New game |
| M | Show/hide mines |
| Q / ESC | Quit |

---

## 👨‍💻 Author

Built as a hands-on exploration of **applied reinforcement learning in imperfect-information environments** — demonstrating how symbolic AI and RL can complement each other to exceed what either approach achieves alone.

---

> If you're interested in AI systems that balance **logic, learning, and uncertainty**, this project is a practical case study worth exploring.