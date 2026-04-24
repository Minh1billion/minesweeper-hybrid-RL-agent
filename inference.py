"""
inference.py - Inference entry-point for Minesweeper Q-Learning.

Loads a trained Q-table and watches the agent play with ε = 0 (pure greedy).
No learning, no saves.

Usage:
  python inference.py

All rendering is handled by ui.py (GameUI, mode="infer").
"""

import random
from collections import deque

from agent import QAgent
from environment import Board
from trainer import VR
from ui import GameUI, ROWS, COLS, MINES


class InferencePlayer:
    def __init__(self, rows, cols, mines, qa: QAgent):
        self.rows  = rows
        self.cols  = cols
        self.mines = mines
        self.qa    = qa
        self.board = Board(rows, cols, mines)

        self.games       = 0
        self.wins        = 0
        self.losses      = 0
        self.win_history = deque(maxlen=100)

        self.ep_steps    = 0
        self.agent_pos   = (rows // 2, cols // 2)
        self.last_action = "—"
        self.last_reason = "—"
        self.last_reward = 0.0
        self.game_over   = False
        self.game_result = ""
        self.frontier_debug = []

        self.cnt = {
            "constraint:mine": 0,
            "constraint:safe": 0,
            "q-table":         0,
            "random":          0,
        }

        self._new_game()

    def _new_game(self):
        sr = random.randint(0, self.rows - 1)
        sc = random.randint(0, self.cols - 1)
        r, c = self.board.reset(sr, sc)
        self.agent_pos   = (r, c)
        self.ep_steps    = 0
        self.game_over   = False
        self.game_result = ""
        self.frontier_debug = []

    def _end_game(self, won: bool):
        self.games += 1
        if won:
            self.wins += 1
            self.game_result = "win"
        else:
            self.losses += 1
            self.game_result = "lose"
        self.win_history.append(1 if won else 0)
        self.game_over = True

    def step(self) -> bool:
        if self.game_over:
            return True

        board = self.board
        qa    = self.qa

        if board.flag_count == self.mines:
            result = board.check_flags_terminal()
            won    = result == "win"
            self._record("END", "flag=mine check",
                         30.0 if won else -30.0, self.agent_pos)
            self._end_game(won)
            return True

        safe, mine_cells = board.constraint_solve()
        if mine_cells:
            r2, c2 = mine_cells[0]
            board.flag(r2, c2)
            self._record("flag", "constraint:mine", 2.0, (r2, c2))
            return False

        if safe:
            r2, c2 = safe[0]
            res    = board.reveal(r2, c2)
            reward = 30.0 if res == "win" else 2.0 if res == "ok" else -20.0
            self._record("reveal", "constraint:safe", reward, (r2, c2))
            if res in ("win", "mine"):
                self._end_game(res == "win")
                return True
            return False

        frontier = board.frontier(VR)
        self.frontier_debug = []

        if frontier:
            best_cell, best_conf = None, -1e9
            for r2, c2 in frontier:
                s         = board.get_obs(r2, c2, VR)
                act, conf = qa.confidence(s)
                qr        = qa.qval(s, "reveal")
                qf        = qa.qval(s, "flag")
                self.frontier_debug.append((r2, c2, qr, qf, act, conf))
                if conf > best_conf:
                    best_conf = conf
                    best_cell = (r2, c2)
            self.frontier_debug.sort(key=lambda x: -x[5])

            if best_cell and best_conf >= qa.conf_thresh:
                r2, c2 = best_cell
                s      = board.get_obs(r2, c2, VR)
                act    = qa.best_a(s)
                if act == "flag":
                    board.flag(r2, c2)
                    self._record("flag", "q-table", 0.5, (r2, c2))
                    return False
                else:
                    res    = board.reveal(r2, c2)
                    reward = 30.0 if res == "win" else 1.0 if res == "ok" else -20.0
                    self._record("reveal", "q-table", reward, (r2, c2))
                    if res in ("win", "mine"):
                        self._end_game(res == "win")
                        return True
                    return False

        hidden = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if not board.board[r][c].is_revealed
            and not board.board[r][c].is_flagged
        ]
        if not hidden:
            self._end_game(board.revealed >= self.rows * self.cols - self.mines)
            return True

        r2, c2 = random.choice(hidden)
        res    = board.reveal(r2, c2)
        reward = 30.0 if res == "win" else 0.2 if res == "ok" else -20.0
        self._record("reveal", "random", reward, (r2, c2))
        if res in ("win", "mine"):
            self._end_game(res == "win")
            return True
        return False

    def _record(self, action, reason, reward, pos):
        self.last_action = action
        self.last_reason = reason
        self.last_reward = reward
        self.agent_pos   = pos
        self.ep_steps   += 1
        key = ":".join(reason.split(":")[:2]) if ":" in reason else reason
        if key in self.cnt:
            self.cnt[key] += 1

    @property
    def win_rate(self):
        if not self.win_history:
            return 0.0
        return sum(self.win_history) / len(self.win_history)

    @property
    def win_rate_all(self):
        t = self.wins + self.losses
        return self.wins / t if t else 0.0

    @property
    def ep_reward(self):
        return 0.0


def main():
    qa = QAgent(eps=0.0, eps_min=0.0, eps_decay=1.0, qtable_path="qtable.json")
    qa.eps = 0.0

    player = InferencePlayer(ROWS, COLS, MINES, qa)

    ui = GameUI(
        mode      ="infer",
        agent     =qa,
        controller=player,
    )
    ui.run()


if __name__ == "__main__":
    main()