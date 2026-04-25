import random

from environment import Board
from agent import QAgent


VR = 2
MAX_EP_STEPS = 200
PROB_SAFE_THRESH = 0.20
PROB_MINE_THRESH = 0.80


class Trainer:
    def __init__(self, rows, cols, mines, qa: QAgent):
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.qa = qa
        self.board = Board(rows, cols, mines)
        self.ep_reward = 0.0
        self.ep_steps = 0
        self.agent_pos = (rows // 2, cols // 2)
        self.last_action = "—"
        self.last_reason = "—"
        self.last_reward = 0.0
        self.cnt = {
            "constraint:mine": 0,
            "constraint:safe": 0,
            "prob:safe": 0,
            "prob:mine": 0,
            "q-table": 0,
            "random": 0,
        }
        self.frontier_debug = []
        self._new_episode()

    def _new_episode(self):
        sr = random.randint(0, self.rows - 1)
        sc = random.randint(0, self.cols - 1)
        r, c = self.board.reset(sr, sc)
        self.agent_pos = (r, c)
        self.ep_reward = 0.0
        self.ep_steps = 0

    def step(self):
        board = self.board
        qa = self.qa

        if self.ep_steps >= MAX_EP_STEPS:
            self._end_episode(False)
            return True

        if board.flag_count == self.mines:
            result = board.check_flags_terminal()
            won = result == "win"
            reward = 10.0 if won else -10.0
            self.ep_reward += reward
            self.last_action = "END"
            self.last_reason = "flag=mine check"
            self.last_reward = reward
            self._end_episode(won)
            return True

        safe, mine_cells = board.constraint_solve()

        if mine_cells:
            r2, c2 = mine_cells[0]
            s = board.get_obs(r2, c2, VR)
            board.flag(r2, c2)
            reward = 5.0
            s2 = board.get_obs(r2, c2, VR)
            qa.update(s, "flag", reward, s2, False)
            self._record("flag", "constraint:mine", reward, (r2, c2))
            return False

        if safe:
            r2, c2 = safe[0]
            s = board.get_obs(r2, c2, VR)
            res = board.reveal(r2, c2)
            reward = 10.0 if res == "win" else 5.0 if res == "ok" else -10.0
            s2 = board.get_obs(r2, c2, VR)
            done = res in ("win", "mine")
            qa.update(s, "reveal", reward, s2, done)
            self._record("reveal", "constraint:safe", reward, (r2, c2))
            if done:
                self._end_episode(res == "win")
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
                s = board.get_obs(r2, c2, VR)
                board.flag(r2, c2)
                reward = 3.0
                s2 = board.get_obs(r2, c2, VR)
                qa.update(s, "flag", reward, s2, False)
                self._record("flag", "prob:mine", reward, (r2, c2))
                return False

            if min_prob <= PROB_SAFE_THRESH:
                r2, c2 = min_prob_cell
                s = board.get_obs(r2, c2, VR)
                res = board.reveal(r2, c2)
                reward = 10.0 if res == "win" else 3.0 if res == "ok" else -10.0
                s2 = board.get_obs(r2, c2, VR)
                done = res in ("win", "mine")
                qa.update(s, "reveal", reward, s2, done)
                self._record("reveal", "prob:safe", reward, (r2, c2))
                if done:
                    self._end_episode(res == "win")
                    return True
                return False

            best = max(self.frontier_debug, key=lambda x: max(x[2], x[3]))
            r2, c2 = best[0], best[1]
            s = board.get_obs(r2, c2, VR)
            act = qa.choose(s)

            if act == "flag":
                board.flag(r2, c2)
                reward = 1.0
                s2 = board.get_obs(r2, c2, VR)
                qa.update(s, "flag", reward, s2, False)
                self._record("flag", "q-table", reward, (r2, c2))
                return False
            else:
                res = board.reveal(r2, c2)
                reward = 10.0 if res == "win" else 2.0 if res == "ok" else -10.0
                s2 = board.get_obs(r2, c2, VR)
                done = res in ("win", "mine")
                qa.update(s, "reveal", reward, s2, done)
                self._record("reveal", "q-table", reward, (r2, c2))
                if done:
                    self._end_episode(res == "win")
                    return True
                return False

        hidden = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if not board.board[r][c].is_revealed and not board.board[r][c].is_flagged
        ]

        if not hidden:
            self._end_episode(board.revealed >= self.rows * self.cols - self.mines)
            return True

        r2, c2 = random.choice(hidden)
        s = board.get_obs(r2, c2, VR)
        res = board.reveal(r2, c2)
        reward = 10.0 if res == "win" else 0.5 if res == "ok" else -10.0
        s2 = board.get_obs(r2, c2, VR)
        done = res in ("win", "mine")
        qa.update(s, "reveal", reward, s2, done)
        self._record("reveal", "random", reward, (r2, c2))
        if done:
            self._end_episode(res == "win")
            return True
        return False

    def _record(self, action, reason, reward, pos):
        self.last_action = action
        self.last_reason = reason
        self.last_reward = reward
        self.agent_pos = pos
        self.ep_reward += reward
        self.ep_steps += 1
        self.qa.total_steps += 1
        key = ":".join(reason.split(":")[:2]) if ":" in reason else reason
        if key in self.cnt:
            self.cnt[key] += 1

    def _end_episode(self, won):
        qa = self.qa
        if won:
            qa.wins += 1
        else:
            qa.losses += 1
        qa.episode += 1
        qa.decay()
        qa.reward_history.append(self.ep_reward)
        qa.win_history.append(1 if won else 0)
        self._new_episode()

    @property
    def win_rate(self):
        if not self.qa.win_history:
            return 0.0
        return sum(self.qa.win_history) / len(self.qa.win_history)

    @property
    def win_rate_all(self):
        t = self.qa.wins + self.qa.losses
        return self.qa.wins / t if t else 0.0