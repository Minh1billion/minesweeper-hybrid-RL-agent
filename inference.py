import random
from collections import deque

from agent import QAgent
from environment import Board
from trainer import VR, PROB_SAFE_THRESH, PROB_MINE_THRESH
from ui import GameUI, ROWS, COLS, MINES


class InferencePlayer:
    def __init__(self, rows, cols, mines, qa: QAgent):
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.qa = qa
        self.board = Board(rows, cols, mines)

        self.games = 0
        self.wins = 0
        self.losses = 0
        self.win_history = deque(maxlen=100)

        self.ep_steps = 0
        self.agent_pos = (rows // 2, cols // 2)
        self.last_action = "—"
        self.last_reason = "—"
        self.last_reward = 0.0
        self.game_over = False
        self.game_result = ""
        self.frontier_debug = []

        self.cnt = {
            "constraint:mine": 0,
            "constraint:safe": 0,
            "prob:safe": 0,
            "prob:mine": 0,
            "q-table": 0,
            "random": 0,
        }

        self._new_game()

    def _new_game(self):
        sr = random.randint(0, self.rows - 1)
        sc = random.randint(0, self.cols - 1)
        r, c = self.board.reset(sr, sc)
        self.agent_pos = (r, c)
        self.ep_steps = 0
        self.game_over = False
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
        qa = self.qa

        if board.flag_count == self.mines:
            result = board.check_flags_terminal()
            won = result == "win"
            self._record("END", "flag=mine check", 10.0 if won else -10.0, self.agent_pos)
            self._end_game(won)
            return True

        safe, mine_cells = board.constraint_solve()

        if mine_cells:
            r2, c2 = mine_cells[0]
            board.flag(r2, c2)
            self._record("flag", "constraint:mine", 5.0, (r2, c2))
            return False

        if safe:
            r2, c2 = safe[0]
            res = board.reveal(r2, c2)
            reward = 10.0 if res == "win" else 5.0 if res == "ok" else -10.0
            self._record("reveal", "constraint:safe", reward, (r2, c2))
            if res in ("win", "mine"):
                self._end_game(res == "win")
                return True
            return False

        frontier_revealed = board.frontier(VR)
        candidate_set = set()
        for r, c in frontier_revealed:
            for n in board.neighbors(r, c):
                if not n.is_revealed and not n.is_flagged:
                    candidate_set.add((n.row, n.col))

        self.frontier_debug = []

        if candidate_set:
            probs = {(r2, c2): board.mine_probability(r2, c2) for r2, c2 in candidate_set}

            for r2, c2 in candidate_set:
                s = board.get_obs(r2, c2, VR)
                qr, qf = qa.qval_debug(s)
                act = qa.best_a(s)
                conf = max(qr, qf)
                prob = probs[(r2, c2)]
                self.frontier_debug.append((r2, c2, qr, qf, act, conf, prob))
            self.frontier_debug.sort(key=lambda x: x[6])

            min_prob_cell = min(probs, key=probs.get)
            max_prob_cell = max(probs, key=probs.get)
            min_prob = probs[min_prob_cell]
            max_prob = probs[max_prob_cell]

            if max_prob >= PROB_MINE_THRESH:
                r2, c2 = max_prob_cell
                board.flag(r2, c2)
                self._record("flag", "prob:mine", 3.0, (r2, c2))
                return False

            if min_prob <= PROB_SAFE_THRESH:
                r2, c2 = min_prob_cell
                res = board.reveal(r2, c2)
                reward = 10.0 if res == "win" else 3.0 if res == "ok" else -10.0
                self._record("reveal", "prob:safe", reward, (r2, c2))
                if res in ("win", "mine"):
                    self._end_game(res == "win")
                    return True
                return False

            best = max(self.frontier_debug, key=lambda x: max(x[2], x[3]))
            r2, c2 = best[0], best[1]
            s = board.get_obs(r2, c2, VR)
            act = qa.best_a(s)

            if act == "flag":
                board.flag(r2, c2)
                self._record("flag", "q-table", 1.0, (r2, c2))
                return False
            else:
                res = board.reveal(r2, c2)
                reward = 10.0 if res == "win" else 2.0 if res == "ok" else -10.0
                self._record("reveal", "q-table", reward, (r2, c2))
                if res in ("win", "mine"):
                    self._end_game(res == "win")
                    return True
                return False

        hidden = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if not board.board[r][c].is_revealed and not board.board[r][c].is_flagged
        ]

        if not hidden:
            self._end_game(board.revealed >= self.rows * self.cols - self.mines)
            return True

        r2, c2 = random.choice(hidden)
        res = board.reveal(r2, c2)
        reward = 10.0 if res == "win" else 0.5 if res == "ok" else -10.0
        self._record("reveal", "random", reward, (r2, c2))
        if res in ("win", "mine"):
            self._end_game(res == "win")
            return True
        return False

    def _record(self, action, reason, reward, pos):
        self.last_action = action
        self.last_reason = reason
        self.last_reward = reward
        self.agent_pos = pos
        self.ep_steps += 1
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
        mode="infer",
        agent=qa,
        controller=player,
    )
    ui.run()


if __name__ == "__main__":
    main()