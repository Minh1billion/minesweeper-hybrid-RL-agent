import json
import os
import random
from collections import defaultdict, deque


ACTIONS = ["reveal", "flag"]


class QAgent:
    def __init__(
        self,
        alpha=0.15,
        gamma=0.90,
        eps=1.0,
        eps_min=0.05,
        eps_decay=0.9998,
        conf_thresh=0.3,
        qtable_path="qtable.json",
    ):
        self.alpha = alpha
        self.gamma = gamma
        self.eps = eps
        self.eps_min = eps_min
        self.eps_decay = eps_decay
        self.conf_thresh = conf_thresh
        self.path = qtable_path
        self.q = defaultdict(lambda: {"reveal": 0.0, "flag": 0.0})
        self.episode = 0
        self.wins = 0
        self.losses = 0
        self.total_steps = 0
        self.reward_history = deque(maxlen=200)
        self.win_history = deque(maxlen=200)
        self.load()

    def qval(self, s, a):
        return self.q[s][a]

    def best_a(self, s):
        return max(self.q[s], key=self.q[s].get)

    def best_q(self, s):
        return max(self.q[s].values())

    def choose(self, s):
        if random.random() < self.eps:
            return random.choice(ACTIONS)
        return self.best_a(s)

    def update(self, s, a, r, s2, done):
        old = self.qval(s, a)
        target = r if done else r + self.gamma * self.best_q(s2)
        self.q[s][a] = old + self.alpha * (target - old)

    def decay(self):
        self.eps = max(self.eps_min, self.eps * self.eps_decay)

    def confidence(self, s):
        a = self.best_a(s)
        return a, self.q[s][a]

    def save(self):
        data = {
            "eps": self.eps,
            "episode": self.episode,
            "wins": self.wins,
            "losses": self.losses,
            "total_steps": self.total_steps,
            "q": {k: dict(v) for k, v in self.q.items()},
        }
        with open(self.path, "w") as f:
            json.dump(data, f)

    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path) as f:
                data = json.load(f)
            self.eps = data.get("eps", self.eps)
            self.episode = data.get("episode", 0)
            self.wins = data.get("wins", 0)
            self.losses = data.get("losses", 0)
            self.total_steps = data.get("total_steps", 0)
            for k, v in data.get("q", {}).items():
                self.q[k] = v
        except Exception:
            pass