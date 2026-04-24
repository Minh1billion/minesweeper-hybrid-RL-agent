import random

from environment import Board
from agent import QAgent


VR = 2


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

        if board.flag_count == self.mines:
            result = board.check_flags_terminal()
            won = result == "win"
            reward = 30.0 if won else -30.0
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
            reward = 2.0
            s2 = board.get_obs(r2, c2, VR)
            qa.update(s, "flag", reward, s2, False)
            self._record("flag", "constraint:mine", reward, (r2, c2))
            return False

        if safe:
            r2, c2 = safe[0]
            s = board.get_obs(r2, c2, VR)
            res = board.reveal(r2, c2)
            reward = 30.0 if res == "win" else 2.0 if res == "ok" else -20.0
            s2 = board.get_obs(r2, c2, VR)
            done = res in ("win", "mine")
            qa.update(s, "reveal", reward, s2, done)
            self._record("reveal", "constraint:safe", reward, (r2, c2))
            if done:
                self._end_episode(res == "win")
                return True
            return False

        frontier = board.frontier(VR)
        self.frontier_debug = []

        if frontier:
            best_cell = None
            best_conf = -1e9
            for r2, c2 in frontier:
                s = board.get_obs(r2, c2, VR)
                act, conf = qa.confidence(s)
                qr = qa.qval(s, "reveal")
                qf = qa.qval(s, "flag")
                self.frontier_debug.append((r2, c2, qr, qf, act, conf))
                if conf > best_conf:
                    best_conf = conf
                    best_cell = (r2, c2)
            self.frontier_debug.sort(key=lambda x: -x[5])

            if best_cell and best_conf >= qa.conf_thresh:
                r2, c2 = best_cell
                s = board.get_obs(r2, c2, VR)
                act = qa.choose(s)
                if act == "flag":
                    board.flag(r2, c2)
                    reward = 0.5
                    s2 = board.get_obs(r2, c2, VR)
                    qa.update(s, "flag", reward, s2, False)
                    self._record("flag", "q-table", reward, (r2, c2))
                    return False
                else:
                    res = board.reveal(r2, c2)
                    reward = 30.0 if res == "win" else 1.0 if res == "ok" else -20.0
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
        reward = 30.0 if res == "win" else 0.2 if res == "ok" else -20.0
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
        key = reason.split(":")[0] + ":" + reason.split(":")[1] if ":" in reason else reason
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