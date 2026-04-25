import random


class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.val = 0
        self.is_mine = False
        self.is_revealed = False
        self.is_flagged = False

    def reveal(self):
        self.is_revealed = True

    def flag(self):
        self.is_flagged = not self.is_flagged

    def get_encode(self):
        if self.is_flagged:
            return -2
        if not self.is_revealed:
            return -1
        return self.val


class Board:
    DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    def __init__(self, rows, cols, mine_count):
        self.rows = rows
        self.cols = cols
        self.mine_count = mine_count
        self.board = [[Cell(r, c) for c in range(cols)] for r in range(rows)]
        self.revealed = 0
        self.flag_count = 0

    def reset(self, first_r=None, first_c=None):
        self.board = [[Cell(r, c) for c in range(self.cols)] for r in range(self.rows)]
        self.revealed = 0
        self.flag_count = 0
        if first_r is None:
            first_r = self.rows // 2
        if first_c is None:
            first_c = self.cols // 2
        self._place_mines(first_r, first_c)
        self._flood(self.board[first_r][first_c])
        return first_r, first_c

    def _place_mines(self, safe_r, safe_c):
        pool = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) != (safe_r, safe_c)
        ]
        for r, c in random.sample(pool, self.mine_count):
            self.board[r][c].is_mine = True
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.board[r][c].is_mine:
                    self.board[r][c].val = sum(
                        1
                        for dr, dc in self.DIRS
                        if 0 <= r + dr < self.rows
                        and 0 <= c + dc < self.cols
                        and self.board[r + dr][c + dc].is_mine
                    )

    def _flood(self, cell):
        if cell.is_revealed or cell.is_flagged or cell.is_mine:
            return
        cell.reveal()
        self.revealed += 1
        if cell.val == 0:
            for dr, dc in self.DIRS:
                nr, nc = cell.row + dr, cell.col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    self._flood(self.board[nr][nc])

    def reveal(self, r, c):
        cell = self.board[r][c]
        if cell.is_revealed or cell.is_flagged:
            return "ok"
        if cell.is_mine:
            cell.reveal()
            return "mine"
        self._flood(cell)
        return "win" if self.revealed >= self.rows * self.cols - self.mine_count else "ok"

    def flag(self, r, c):
        cell = self.board[r][c]
        if cell.is_revealed:
            return
        was = cell.is_flagged
        cell.flag()
        self.flag_count += -1 if was else 1

    def neighbors(self, r, c):
        for dr, dc in self.DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                yield self.board[nr][nc]

    def get_obs(self, r, c, vr):
        obs = []
        for rr in range(r - vr, r + vr + 1):
            for cc in range(c - vr, c + vr + 1):
                if 0 <= rr < self.rows and 0 <= cc < self.cols:
                    obs.append(self.board[rr][cc].get_encode())
                else:
                    obs.append(-3)
        return tuple(obs)

    def frontier(self, vr):
        result = []
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.board[r][c].is_revealed:
                    continue
                obs = self.get_obs(r, c, vr)
                if -1 in obs:
                    result.append((r, c))
        return result

    def mine_probability(self, r, c):
        cell = self.board[r][c]
        if cell.is_revealed or cell.is_flagged:
            return None
        scores = []
        for n in self.neighbors(r, c):
            if not n.is_revealed or n.val == 0:
                continue
            nbrs = list(self.neighbors(n.row, n.col))
            hidden = [x for x in nbrs if not x.is_revealed and not x.is_flagged]
            flagged = [x for x in nbrs if x.is_flagged]
            rem = n.val - len(flagged)
            if hidden:
                scores.append(rem / len(hidden))
        if not scores:
            return 0.5
        return sum(scores) / len(scores)

    def constraint_solve(self):
        safe, mines = set(), set()
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.board[r][c]
                if not cell.is_revealed or cell.val == 0:
                    continue
                nbrs = list(self.neighbors(r, c))
                hidden = [n for n in nbrs if not n.is_revealed and not n.is_flagged]
                flagged = [n for n in nbrs if n.is_flagged]
                rem = cell.val - len(flagged)
                if rem == 0:
                    for n in hidden:
                        safe.add((n.row, n.col))
                elif rem == len(hidden) and rem > 0:
                    for n in hidden:
                        mines.add((n.row, n.col))
        return list(safe), list(mines)

    def check_flags_terminal(self):
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.board[r][c]
                if cell.is_flagged and not cell.is_mine:
                    return "lose"
        return "win"