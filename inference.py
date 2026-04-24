"""
inference.py — Load trained Q-table and watch the agent play (no training).

Controls:
  SPACE       auto-play on/off
  ENTER       manual step (when paused)
  N           new game
  +/-         speed ±5 steps/frame
  M           show/hide mines
  Q / ESC     quit
"""

import sys
import random
from collections import deque

import pygame

from agent import QAgent
from environment import Board
from trainer import VR


BG      = (10,  12,  16)
PANEL   = (16,  20,  26)
BORDER  = (28,  34,  44)
T1      = (210, 210, 205)
T2      = (85,  95,  110)
T3      = (40,  46,  58)
C_WIN   = (55,  200, 110)
C_LOSE  = (200,  60,  60)
C_FLAG  = (195, 135,  35)
C_AGENT = (50,  140, 230)
C_SAFE  = (55,  220, 160)
C_MINH  = (220, 180,  50)
C_HIDDEN= (26,   32,  42)
C_REVL  = (18,   22,  30)
C_MINEC = (160,  40,  40)
C_BA    = (50,  140, 230)
C_BI    = (55,  185, 105)
C_BV    = (32,   65, 120)
NUM_C = {
    1: (75,  125, 215),
    2: (75,  185, 115),
    3: (215,  75,  75),
    4: (115,  75, 195),
    5: (195,  75,  45),
    6: (75,  195, 195),
    7: (195,  75, 195),
    8: (145, 145, 145),
}


ROWS, COLS, MINES = 10, 10, 15
CELL    = 42
GAP     = 2
MPAD    = 14
BOARD_W = COLS * (CELL + GAP)
BOARD_H = ROWS * (CELL + GAP)
PX      = MPAD + BOARD_W + 16
PW      = 320
WIN_W   = PX + PW + 12
WIN_H   = max(BOARD_H + MPAD * 2 + 20, 680)


def mfont(sz, bold=False):
    try:
        return pygame.font.SysFont("JetBrains Mono,Consolas,Courier New", sz, bold=bold)
    except Exception:
        return pygame.font.SysFont("monospace", sz, bold=bold)


def rrect(surf, col, rect, r=4, bw=0, bc=None):
    pygame.draw.rect(surf, col, rect, border_radius=r)
    if bw and bc:
        pygame.draw.rect(surf, bc, rect, bw, border_radius=r)


def draw_cell(surf, cell, x, y, sz, is_agent=False, in_vis=False,
              show_mine=False, is_safe=False, is_minh=False, fn=None, fn_sm=None):
    if cell.is_mine and show_mine and cell.is_revealed:
        bg = C_MINEC
    elif not cell.is_revealed and not cell.is_flagged:
        bg = C_HIDDEN
    elif cell.is_flagged:
        bg = (40, 34, 14)
    else:
        bg = C_REVL

    bc, bw = None, 0
    if is_minh:
        bc, bw = C_MINH, 2
    elif is_safe:
        bc, bw = C_SAFE, 2
    elif is_agent:
        bc, bw = C_BA, 2
    elif in_vis:
        bc, bw = C_BV, 1

    rrect(surf, bg, (x, y, sz, sz), r=4, bw=bw, bc=bc)

    if in_vis and not is_agent:
        ov = pygame.Surface((sz, sz), pygame.SRCALPHA)
        ov.fill((50, 140, 230, 14))
        surf.blit(ov, (x, y))

    cx, cy = x + sz // 2, y + sz // 2

    if cell.is_flagged and fn_sm:
        t = fn_sm.render("F", True, C_FLAG)
        surf.blit(t, t.get_rect(center=(cx, cy)))
    elif cell.is_mine and show_mine and cell.is_revealed and fn_sm:
        t = fn_sm.render("*", True, (255, 200, 200))
        surf.blit(t, t.get_rect(center=(cx, cy)))
    elif cell.is_revealed and cell.val > 0 and fn:
        t = fn.render(str(cell.val), True, NUM_C.get(cell.val, T1))
        surf.blit(t, t.get_rect(center=(cx, cy)))

    if is_agent:
        pygame.draw.circle(surf, C_AGENT, (cx, cy - 1), 5)


def sparkline(surf, data, x, y, w, h, col, font, baseline=None):
    pygame.draw.rect(surf, (12, 16, 22), (x, y, w, h), border_radius=3)
    pygame.draw.rect(surf, BORDER,       (x, y, w, h), 1, border_radius=3)
    if len(data) >= 2:
        mn, mx = min(data), max(data)
        rng = mx - mn if mx != mn else 1
        pts = []
        for i, v in enumerate(data):
            px_ = x + int(i / (len(data) - 1) * (w - 4)) + 2
            py_ = y + h - 4 - int((v - mn) / rng * (h - 8))
            pts.append((px_, py_))
        if baseline is not None and mn != mx:
            by_ = y + h - 4 - int((baseline - mn) / rng * (h - 8))
            pygame.draw.line(surf, (50, 55, 65), (x + 2, by_), (x + w - 2, by_), 1)
        pygame.draw.lines(surf, col, False, pts, 2)
        fill_pts = [(x + 2, y + h - 4)] + pts + [(x + w - 2, y + h - 4)]
        fs = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.polygon(fs, (*col, 30), [(p[0] - x, p[1] - y) for p in fill_pts])
        surf.blit(fs, (x, y))


class InferencePlayer:
    def __init__(self, rows, cols, mines, qa: QAgent):
        self.rows  = rows
        self.cols  = cols
        self.mines = mines
        self.qa    = qa
        self.board = Board(rows, cols, mines)

        self.games      = 0
        self.wins       = 0
        self.losses     = 0
        self.win_history= deque(maxlen=100)

        self.ep_steps   = 0
        self.agent_pos  = (rows // 2, cols // 2)
        self.last_action= "—"
        self.last_reason= "—"
        self.last_reward= 0.0
        self.game_over  = False
        self.game_result= ""
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
        self.agent_pos  = (r, c)
        self.ep_steps   = 0
        self.game_over  = False
        self.game_result= ""
        self.frontier_debug = []

    def _end_game(self, won: bool):
        self.games  += 1
        if won:
            self.wins   += 1
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
            self._record("END", "flag=mine check", 30.0 if won else -30.0,
                         self.agent_pos)
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
                s        = board.get_obs(r2, c2, VR)
                act, conf= qa.confidence(s)
                qr       = qa.qval(s, "reveal")
                qf       = qa.qval(s, "flag")
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


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Minesweeper — Inference (no training)")
    clock = pygame.time.Clock()

    FN   = mfont(16, True)
    FN_S = mfont(13)
    FN_H = mfont(10, True)
    FN_T = mfont(9)
    FN_B = mfont(8)

    qa = QAgent(eps=0.0, eps_min=0.0, eps_decay=1.0, qtable_path="qtable.json")
    qa.eps = 0.0

    player = InferencePlayer(ROWS, COLS, MINES, qa)

    auto       = False
    speed      = 5
    show_mine  = False
    log        = deque(maxlen=14)
    log.append(f"Board {ROWS}x{COLS}  mines={MINES}  VR={VR}")
    log.append(f"Loaded: ep={qa.episode}  q-states={len(qa.q)}")
    log.append("ε forced to 0 — pure greedy inference")

    pause_frames = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k == pygame.K_SPACE:
                    auto = not auto
                    log.append(f"Auto: {'ON' if auto else 'OFF'}")
                elif k in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif k == pygame.K_RETURN and not auto:
                    if player.game_over:
                        player._new_game()
                    else:
                        player.step()
                elif k == pygame.K_n:
                    player._new_game()
                    log.append("New game")
                elif k in (pygame.K_EQUALS, pygame.K_PLUS):
                    speed = min(500, speed + 5)
                    log.append(f"Speed={speed}/frame")
                elif k == pygame.K_MINUS:
                    speed = max(1, speed - 5)
                    log.append(f"Speed={speed}/frame")
                elif k == pygame.K_m:
                    show_mine = not show_mine

        if auto:
            if player.game_over:
                if pause_frames > 0:
                    pause_frames -= 1
                else:
                    result_str = player.game_result.upper()
                    log.append(
                        f"Game {player.games:4d} │ {result_str:4s} │ "
                        f"steps={player.ep_steps:3d} │ "
                        f"wr={player.win_rate * 100:.1f}%"
                    )
                    player._new_game()
                    pause_frames = 0
            else:
                for _ in range(speed):
                    ended = player.step()
                    if ended:
                        pause_frames = 18
                        break

        screen.fill(BG)

        board = player.board
        ar, ac = player.agent_pos
        safe_h, mine_h = board.constraint_solve()
        safe_set  = set(safe_h)
        mine_set  = set(mine_h)

        for r in range(ROWS):
            for c in range(COLS):
                cell = board.board[r][c]
                x    = MPAD + c * (CELL + GAP)
                y    = MPAD + r * (CELL + GAP)
                in_v = abs(r - ar) <= VR and abs(c - ac) <= VR
                draw_cell(
                    surf=screen, cell=cell, x=x, y=y, sz=CELL,
                    is_agent  =(r == ar and c == ac),
                    in_vis    =in_v,
                    show_mine =show_mine,
                    is_safe   =(r, c) in safe_set and not cell.is_revealed,
                    is_minh   =(r, c) in mine_set and not cell.is_flagged,
                    fn=FN, fn_sm=FN_S,
                )

        vx0 = MPAD + max(0, ac - VR) * (CELL + GAP)
        vy0 = MPAD + max(0, ar - VR) * (CELL + GAP)
        vx1 = MPAD + min(COLS - 1, ac + VR) * (CELL + GAP) + CELL
        vy1 = MPAD + min(ROWS - 1, ar + VR) * (CELL + GAP) + CELL
        pygame.draw.rect(screen, C_BA, (vx0, vy0, vx1 - vx0, vy1 - vy0), 1, border_radius=4)

        if player.game_over:
            ov_col = (0, 180, 80, 55) if player.game_result == "win" else (180, 30, 30, 55)
            ov = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
            ov.fill(ov_col)
            screen.blit(ov, (MPAD, MPAD))
            msg   = "✔ WIN!" if player.game_result == "win" else "✘ BOOM"
            col   = C_WIN if player.game_result == "win" else C_LOSE
            mt    = FN.render(msg, True, col)
            screen.blit(mt, mt.get_rect(center=(MPAD + BOARD_W // 2, MPAD + BOARD_H // 2)))

        bst = (
            f"games={player.games}  wins={player.wins}  losses={player.losses}"
            f"  wr={player.win_rate_all * 100:.1f}%"
            f"  flags={board.flag_count}/{MINES}  revealed={board.revealed}"
        )
        screen.blit(FN_T.render(bst, True, T2), (MPAD, MPAD + BOARD_H + 4))

        py = 8

        def sep():
            nonlocal py
            pygame.draw.line(screen, BORDER, (PX, py), (PX + PW - 6, py))
            py += 6

        def heading(txt, col=C_AGENT):
            nonlocal py
            t = FN_H.render(txt.upper(), True, col)
            screen.blit(t, (PX, py))
            py += t.get_height() + 3

        def kv(k, v, vc=T1):
            nonlocal py
            kt = FN_T.render(k, True, T2)
            vt = FN_T.render(str(v), True, vc)
            screen.blit(kt, (PX, py))
            screen.blit(vt, (PX + PW - 8 - vt.get_width(), py))
            py += kt.get_height() + 3

        t = FN_H.render("Q-LEARNING  MINESWEEPER  INFERENCE", True, C_AGENT)
        screen.blit(t, (PX, py))
        py += t.get_height() + 2
        mode_col = C_WIN if auto else T3
        mt = FN_T.render(
            ("▶ AUTO" if auto else "⏸ MANUAL  (ENTER=step)") + " — SPACE",
            True, mode_col,
        )
        screen.blit(mt, (PX, py))
        py += mt.get_height() + 3
        sep()

        heading("Session Stats")
        kv("Games played",   player.games)
        kv("Wins / Losses",  f"{player.wins} / {player.losses}",
           C_WIN if player.wins >= player.losses else C_LOSE)
        kv("Win rate (all)", f"{player.win_rate_all * 100:.2f}%",
           C_WIN if player.win_rate_all > 0.25 else C_LOSE)
        kv("Win rate (100)", f"{player.win_rate * 100:.1f}%",
           C_WIN if player.win_rate > 0.25 else C_LOSE)
        kv("Steps this game", player.ep_steps)
        sep()

        heading("Model Info")
        kv("Trained episodes", qa.episode)
        kv("Q-states loaded",  f"{len(qa.q):,}")
        kv("ε (epsilon)",      f"{qa.eps:.3f}  (greedy)", T2)
        kv("α / γ",            f"{qa.alpha} / {qa.gamma}")
        sep()

        heading("Decision Source  (this session)")
        total_cnt = sum(player.cnt.values()) or 1
        src_items = [
            ("constraint:mine", C_MINH),
            ("constraint:safe", C_SAFE),
            ("q-table",         C_AGENT),
            ("random",          T2),
        ]
        for src, col in src_items:
            n   = player.cnt.get(src, 0)
            pct = n / total_cnt
            bw2, bh2 = PW - 8, 9
            pygame.draw.rect(screen, (12, 16, 22), (PX, py, bw2, bh2), border_radius=2)
            fw2 = int(bw2 * pct)
            if fw2:
                pygame.draw.rect(screen, col, (PX, py, fw2, bh2), border_radius=2)
            pygame.draw.rect(screen, BORDER, (PX, py, bw2, bh2), 1, border_radius=2)
            lt = FN_T.render(src, True, col)
            ct = FN_T.render(f"{n:,}  {pct * 100:.1f}%", True, T2)
            screen.blit(lt, (PX + 3, py + bh2 + 1))
            screen.blit(ct, (PX + PW - 8 - ct.get_width(), py + bh2 + 1))
            py += bh2 + lt.get_height() + 3
        sep()

        heading("Win Rate  (last 100 games)")
        CH = 48
        if len(player.win_history) >= 2:
            wd     = list(player.win_history)
            rolled = []
            for i in range(len(wd)):
                sl = wd[max(0, i - 9): i + 1]
                rolled.append(sum(sl) / len(sl))
            sparkline(screen, rolled, PX, py, PW - 8, CH, C_WIN, FN_B, baseline=0.5)
            wt = FN_B.render(
                f"now={rolled[-1] * 100:.1f}%  best={max(rolled) * 100:.1f}%",
                True, C_WIN,
            )
            screen.blit(wt, (PX + 4, py + CH - 12))
        else:
            pygame.draw.rect(screen, (12, 16, 22), (PX, py, PW - 8, CH), border_radius=3)
            nt = FN_T.render("press SPACE to start auto-play", True, T3)
            screen.blit(nt, (PX + 4, py + CH // 2 - 5))
        py += CH + 4
        sep()

        heading("Last Step")
        reason_col = (
            C_MINH  if "mine"    in player.last_reason else
            C_SAFE  if "safe"    in player.last_reason else
            C_AGENT if "q-table" in player.last_reason else T2
        )
        kv("Pos",       f"({ar},{ac})")
        kv("Action",    player.last_action,
           C_WIN if player.last_action == "reveal" else C_FLAG)
        kv("Source",    player.last_reason, reason_col)
        kv("Reward",    f"{player.last_reward:+.1f}",
           C_WIN if player.last_reward > 0 else C_LOSE if player.last_reward < 0 else T2)
        kv("Revealed",  f"{board.revealed}/{ROWS * COLS - MINES}")
        kv("Flags",     f"{board.flag_count}/{MINES}")
        sep()

        heading("Frontier Q-Values  (top 5)")
        hdr = FN_B.render(" cell      Q[rev]   Q[flg]  best", True, T3)
        screen.blit(hdr, (PX, py))
        py += hdr.get_height() + 2
        pygame.draw.line(screen, BORDER, (PX, py), (PX + PW - 8, py))
        py += 3
        dbg = player.frontier_debug[:5]
        if dbg:
            for r2, c2, qr, qf, act, conf in dbg:
                act_col = C_WIN if act == "reveal" else C_FLAG
                line    = f"({r2:2d},{c2:2d})   {qr:+.3f}  {qf:+.3f}  {act}"
                lt      = FN_B.render(line, True, act_col)
                bar_w   = int(max(0, min(1, (conf + 1) / 2)) * (PW - 8))
                if bar_w:
                    bs = pygame.Surface((bar_w, lt.get_height()), pygame.SRCALPHA)
                    bs.fill((*act_col, 18))
                    screen.blit(bs, (PX, py))
                screen.blit(lt, (PX + 2, py))
                py += lt.get_height() + 2
        else:
            screen.blit(FN_T.render("  (no frontier — random move)", True, T3), (PX, py))
            py += FN_T.get_height() + 2
        sep()

        heading("Log")
        visible = list(log)[-8:]
        for i, line in enumerate(visible):
            frac = (i + 1) / max(len(visible), 1)
            col  = T3 if frac < 0.3 else T2 if frac < 0.7 else T1
            screen.blit(FN_T.render(line[:50], True, col), (PX, py))
            py += FN_T.get_height() + 2
        sep()

        for k, v in [
            ("SPACE", "auto-play on/off"),
            ("ENTER", "manual step / next game"),
            ("+/-",   "speed ±5"),
            ("N",     "new game"),
            ("M",     "show/hide mines"),
            ("Q/ESC", "quit"),
        ]:
            kt = FN_T.render(k, True, C_AGENT)
            vt = FN_T.render(v, True, T3)
            screen.blit(kt, (PX, py))
            screen.blit(vt, (PX + PW - 8 - vt.get_width(), py))
            py += kt.get_height() + 2

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()