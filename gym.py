"""
gym.py - Training entry-point for Minesweeper Q-Learning.

Usage:
  python gym.py                  # train indefinitely
  python gym.py --epochs 20000    # train 20 000 episodes then auto-save & stop

All rendering is handled by ui.py (GameUI, mode="train").
"""

import argparse

from agent import QAgent
from trainer import Trainer
from ui import GameUI, ROWS, COLS, MINES


def parse_args():
    parser = argparse.ArgumentParser(description="Minesweeper Q-Learning Trainer")
    parser.add_argument(
        "--epochs", type=int, default=None, metavar="N",
        help="Stop and auto-save after N episodes (relative to this session). "
             "Omit to train indefinitely.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    qa      = QAgent(qtable_path="qtable.json")
    trainer = Trainer(ROWS, COLS, MINES, qa)

    ui = GameUI(
        mode          ="train",
        agent         =qa,
        controller    =trainer,
        target_epochs =args.epochs,
    )
    ui.run()


if __name__ == "__main__":
    main()