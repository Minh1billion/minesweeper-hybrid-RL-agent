# 🧠 Minesweeper AI - Hybrid Q-Learning Agent

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![RL](https://img.shields.io/badge/AI-Reinforcement%20Learning-green)
![Built With](https://img.shields.io/badge/Built%20With-Pygame-black)
![Q-Learning](https://img.shields.io/badge/Algorithm-Q--Learning-red)
![Visualization](https://img.shields.io/badge/UI-Debuggable-blueviolet)
![Game AI](https://img.shields.io/badge/Domain-Minesweeper-orange)
![Architecture](https://img.shields.io/badge/Architecture-Hybrid%20AI-purple)
![Win Rate](https://img.shields.io/badge/Win%20Rate-~46%25-brightgreen)
![Status](https://img.shields.io/badge/Status-Stable-success)
![License](https://img.shields.io/badge/License-MIT-yellow)

A high-performance **hybrid AI system** that learns to play Minesweeper by combining **rule-based reasoning + reinforcement learning (Q-table)**.

> 🎯 Achieves ~46% win rate on a 10x10 board (15 mines) - near the practical ceiling for this architecture.

---

## 🚀 Overview

This project explores how **symbolic reasoning and reinforcement learning can complement each other** in a partially observable, stochastic environment like Minesweeper.

Instead of relying purely on RL, the agent is designed as a **multi-layer decision system**:

1. **Constraint Solver (Deterministic Logic)**

   * Identifies guaranteed safe cells and mines
   * Handles all logically solvable situations

2. **Q-Learning Agent (Experience-Based)**

   * Learns patterns from local board states (5×5 window)
   * Makes decisions under uncertainty

3. **Fallback Strategy (Exploration)**

   * Handles unavoidable guess scenarios

---

## 🧠 Key Design Decisions

### 🔹 Local State Representation (5×5 Window)

* Reduces state space dramatically
* Enables tabular Q-learning to be feasible
* Focuses learning on **relevant frontier regions**

### 🔹 Frontier-Based Processing

* Only evaluates cells adjacent to revealed tiles
* Avoids unnecessary computation on irrelevant areas

### 🔹 Confidence-Guided Decision Making

* Q-table actions are used **only when confidence exceeds a threshold**
* Prevents early-stage noisy learning from degrading performance

### 🔹 Hybrid Architecture

* Rule-based logic handles certainty
* RL handles ambiguity
* Randomness handles irreducible uncertainty

---

## 📊 Results

### Training

* ~45,000 episodes
* ~1.17 million steps
* ~1.9M Q-states learned

### Performance

* **Win rate (all): ~46%**
* **Win rate (rolling 200, training): ~50%**
* **Win rate (rolling 100, inference): tracked separately**
* Stable convergence after training

### Decision Breakdown

* Constraint (safe/mine): ~85%
* Q-learning decisions: ~4–9%
* Random fallback: ~10–15%

> 💡 Insight: The system relies heavily on logical reasoning, with RL improving decision quality in ambiguous states.

---

## 🎯 Why This Matters

Minesweeper is not a fully solvable game - it inherently requires **probabilistic guessing**.

This project demonstrates:

* How to **combine symbolic AI and RL effectively**
* How to handle **partial observability**
* How to design systems where **learning complements logic**

---

## 🛠️ Tech Stack

* Python
* Pygame (visualization + debugging UI)
* Tabular Q-Learning
* Custom constraint solver

---

## 📈 Key Learnings

* Pure RL performs poorly on Minesweeper due to sparse rewards and hidden state
* Rule-based systems are strong but incomplete
* A hybrid approach yields **significantly better and more stable performance**

---

## 🔮 Future Improvements

* Probability-based reasoning (risk estimation per cell)
* Feature-based state encoding (instead of raw grid)
* Deep RL (CNN) for global pattern recognition
* Constraint propagation beyond single-step inference

---

## 🧪 Demo Features

* Real-time training visualization
* Decision source tracking (constraint vs Q-table vs random)
* Frontier Q-value inspection
* Win rate & reward analytics

---

## 👨‍💻 Author

Built as a practical exploration of **applied reinforcement learning in imperfect-information environments**.

---

## ⭐ Highlights

* Clean hybrid AI architecture
* Strong engineering focus (debuggable, visualized, measurable)
* Near-optimal performance for chosen design

---

> If you're interested in AI systems that balance **logic, learning, and uncertainty**, this project is a great case study.
