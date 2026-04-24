# ⚙️ SETUP GUIDE

This project uses only **Python**, **pygame**, and **numpy**.  
Follow the steps below to run it locally.

---

## 📦 1. Requirements

- Python **3.10+**
- pip (Python package manager)

---

## 📥 2. Clone the Repository

```bash
git clone https://github.com/Minh1billion/minesweeper-hybrid-RL-agent.git
cd minesweeper-hybrid-RL-agent
```

---

## 📚 3. Install Dependencies

```bash
pip install pygame numpy
```

---

## ▶️ 4. Run Training

Train the agent (default: infinite training):

```bash
python gym.py
```

Train with a fixed number of episodes:

```bash
python gym.py --epochs 20000
```

After finishing, the Q-table will be saved automatically to:

```
qtable.json
```

---

## 🤖 5. Run Inference (Watch the Agent Play)

```bash
python inference.py
```

- Uses trained Q-table
- No learning (ε = 0, fully greedy)

---

## 🎮 Controls

### Training Mode

| Key        | Action |
|------------|--------|
| SPACE      | Toggle auto training |
| ENTER      | Step manually |
| +/-        | Adjust speed |
| S          | Save Q-table |
| N          | New episode |
| M          | Show/hide mines |
| Q / ESC    | Quit |

---

### Inference Mode

| Key        | Action |
|------------|--------|
| SPACE      | Toggle auto-play |
| ENTER      | Step / next game |
| +/-        | Adjust speed |
| N          | New game |
| M          | Show/hide mines |
| Q / ESC    | Quit |

---

## 📁 Project Structure

```
.
├── gym.py           # Training entry point
├── inference.py     # Inference entry point
├── agent.py         # Q-learning agent
├── trainer.py       # Training loop logic
├── environment.py   # Minesweeper board logic
├── ui.py            # Visualization (pygame)
├── qtable.json      # Saved Q-values
```

---

## 💡 Notes

- No external frameworks (like Gym) are used.
- Implement:
  - Q-learning
  - Constraint solving
  - Visualization

---

## 🚀 Quick Start

```bash
pip install pygame numpy
python gym.py --epochs 20000
python inference.py
```

---

## 🧠 Tip

For best results:
- Train at least **20,000+ episodes**
- Let ε decay naturally
- Watch win rate stabilize in UI

---

Enjoy exploring AI + Minesweeper! 🎯