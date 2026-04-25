import sys
from collections import deque

import pygame


BG        = (22,  26,  34)
PANEL_BG  = (28,  33,  44)
BORDER    = (50,  58,  78)
BORDER_LT = (70,  80, 105)
T1        = (230, 232, 238)
T2        = (155, 162, 180)
T3        = (80,   88, 108)

C_WIN     = (60,  210, 120)
C_LOSE    = (220,  70,  70)
C_EPS     = (80,  155, 245)
C_REWARD  = (220, 185,  60)
C_FLAG    = (215, 150,  40)
C_AGENT   = (80,  160, 245)
C_SAFE    = (60,  220, 160)
C_MINH    = (235, 195,  55)
C_PROB_S  = (80,  200, 140)
C_PROB_M  = (200, 130,  50)
C_HIDDEN  = (32,   38,  52)
C_REVL    = (20,   25,  36)
C_MINEC   = (170,  45,  45)
C_BA      = (80,  160, 245)
C_BI      = (60,  190, 115)
C_BV      = (40,   72, 135)

NUM_C = {
    1: (90,  140, 230),  2: (80,  200, 125),
    3: (225,  85,  85),  4: (130,  90, 210),
    5: (210,  95,  55),  6: (80,  210, 210),
    7: (210,  90, 210),  8: (170, 170, 170),
}

ROWS, COLS, MINES = 10, 10, 15
CELL    = 44
GAP     = 2
MPAD    = 16
BOARD_W = COLS * (CELL + GAP)
BOARD_H = ROWS * (CELL + GAP)
PX      = MPAD + BOARD_W + 18
PW      = 400
WIN_W   = PX + PW + 14
WIN_H   = max(BOARD_H + MPAD * 2 + 80, 820)
CHART_W = PW - 12
CHART_H = 52


def _mfont(sz, bold=False):
    try:
        return pygame.font.SysFont("JetBrains Mono,Consolas,Courier New", sz, bold=bold)
    except Exception:
        return pygame.font.SysFont("monospace", sz, bold=bold)


def _rrect(surf, col, rect, r=5, bw=0, bc=None):
    pygame.draw.rect(surf, col, rect, border_radius=r)
    if bw and bc:
        pygame.draw.rect(surf, bc, rect, bw, border_radius=r)


def _panel_bg(surf, x, y, w, h):
    pygame.draw.rect(surf, PANEL_BG, (x - 4, y - 4, w + 8, h + 8), border_radius=6)
    pygame.draw.rect(surf, BORDER,   (x - 4, y - 4, w + 8, h + 8), 1, border_radius=6)


def draw_cell(surf, cell, x, y, sz,
              is_agent=False, in_vis=False, in_iter=False,
              show_mine=False, is_safe=False, is_minh=False,
              fn=None, fn_sm=None):
    if cell.is_mine and show_mine and cell.is_revealed:
        bg = C_MINEC
    elif not cell.is_revealed and not cell.is_flagged:
        bg = C_HIDDEN
    elif cell.is_flagged:
        bg = (52, 42, 16)
    else:
        bg = C_REVL

    bc, bw = None, 0
    if is_minh:    bc, bw = C_MINH,  2
    elif is_safe:  bc, bw = C_SAFE,  2
    elif is_agent: bc, bw = C_BA,    2
    elif in_iter:  bc, bw = C_BI,    2
    elif in_vis:   bc, bw = C_BV,    1

    _rrect(surf, bg, (x, y, sz, sz), r=5, bw=bw, bc=bc)

    if in_vis and not is_agent:
        ov = pygame.Surface((sz, sz), pygame.SRCALPHA)
        ov.fill((80, 140, 230, 16))
        surf.blit(ov, (x, y))

    cx, cy = x + sz // 2, y + sz // 2
    if cell.is_flagged and fn_sm:
        t = fn_sm.render("F", True, C_FLAG)
        surf.blit(t, t.get_rect(center=(cx, cy)))
    elif cell.is_mine and show_mine and cell.is_revealed and fn_sm:
        t = fn_sm.render("*", True, (255, 210, 210))
        surf.blit(t, t.get_rect(center=(cx, cy)))
    elif cell.is_revealed and cell.val > 0 and fn:
        t = fn.render(str(cell.val), True, NUM_C.get(cell.val, T1))
        surf.blit(t, t.get_rect(center=(cx, cy)))
    if is_agent:
        pygame.draw.circle(surf, C_AGENT, (cx, cy - 1), 5)


def sparkline(surf, data, x, y, w, h, col, font, baseline=None, label=""):
    pygame.draw.rect(surf, (14, 18, 26), (x, y, w, h), border_radius=4)
    pygame.draw.rect(surf, BORDER,       (x, y, w, h), 1, border_radius=4)
    if len(data) >= 2:
        mn, mx = min(data), max(data)
        rng = mx - mn if mx != mn else 1
        pts = []
        for i, v in enumerate(data):
            px_ = x + int(i / (len(data) - 1) * (w - 6)) + 3
            py_ = y + h - 5 - int((v - mn) / rng * (h - 10))
            pts.append((px_, py_))
        if baseline is not None and mn != mx:
            by_ = y + h - 5 - int((baseline - mn) / rng * (h - 10))
            pygame.draw.line(surf, BORDER_LT, (x + 3, by_), (x + w - 3, by_), 1)
        pygame.draw.lines(surf, col, False, pts, 2)
        fill_pts = [(x + 3, y + h - 5)] + pts + [(x + w - 3, y + h - 5)]
        fs = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.polygon(fs, (*col, 35), [(p[0] - x, p[1] - y) for p in fill_pts])
        surf.blit(fs, (x, y))
    if label and font:
        surf.blit(font.render(label, True, T2), (x + 5, y + 4))


def hbar(surf, x, y, w, h, frac, col, font, label=""):
    pygame.draw.rect(surf, (14, 18, 26), (x, y, w, h), border_radius=3)
    fw = max(0, int(w * max(0.0, min(1.0, frac))))
    if fw:
        pygame.draw.rect(surf, col, (x, y, fw, h), border_radius=3)
    pygame.draw.rect(surf, BORDER, (x, y, w, h), 1, border_radius=3)
    if label and font:
        t = font.render(label, True, T1)
        surf.blit(t, t.get_rect(midright=(x + w - 5, y + h // 2)))


def decision_bars(surf, cnt, x, py, pw, fn_t, fn_b):
    src_items = [
        ("constraint:mine", C_MINH),
        ("constraint:safe", C_SAFE),
        ("prob:mine",       C_PROB_M),
        ("prob:safe",       C_PROB_S),
        ("q-table",         C_AGENT),
        ("random",          T3),
    ]
    total = sum(cnt.values()) or 1
    for src, col in src_items:
        n = cnt.get(src, 0)
        pct = n / total
        bw2, bh2 = pw - 10, 9
        pygame.draw.rect(surf, (14, 18, 26), (x, py, bw2, bh2), border_radius=2)
        fw2 = int(bw2 * pct)
        if fw2:
            pygame.draw.rect(surf, col, (x, py, fw2, bh2), border_radius=2)
        pygame.draw.rect(surf, BORDER, (x, py, bw2, bh2), 1, border_radius=2)
        lt = fn_t.render(src, True, col)
        ct = fn_t.render(f"{n:,}  {pct * 100:.1f}%", True, T2)
        surf.blit(lt, (x + 3, py + bh2 + 2))
        surf.blit(ct, (x + pw - 10 - ct.get_width(), py + bh2 + 2))
        py += bh2 + lt.get_height() + 4
    return py


def frontier_table(surf, dbg, x, py, pw, fn_b, fn_t):
    hdr = fn_b.render(" cell    Q[rev]  Q[flg]  prob   best", True, T3)
    surf.blit(hdr, (x, py))
    py += hdr.get_height() + 2
    pygame.draw.line(surf, BORDER_LT, (x, py), (x + pw - 10, py))
    py += 4
    if dbg:
        for entry in dbg[:5]:
            r2, c2, qr, qf, act, conf = entry[0], entry[1], entry[2], entry[3], entry[4], entry[5]
            prob = entry[6] if len(entry) > 6 else None
            act_col = C_WIN if act == "reveal" else C_FLAG
            prob_str = f"{prob:.2f}" if prob is not None else "  — "
            prob_col = (C_PROB_S if prob is not None and prob <= 0.25 else
                        C_PROB_M if prob is not None and prob >= 0.75 else T2)
            line_txt = f"({r2:2d},{c2:2d})  {qr:+.2f}  {qf:+.2f}  "
            lt = fn_b.render(line_txt, True, act_col)
            surf.blit(lt, (x + 2, py))
            pt = fn_b.render(prob_str, True, prob_col)
            surf.blit(pt, (x + lt.get_width() + 2, py))
            at = fn_b.render(f"  {act}", True, act_col)
            surf.blit(at, (x + lt.get_width() + pt.get_width() + 2, py))
            py += lt.get_height() + 3
    else:
        t = fn_t.render("  (no frontier)", True, T3)
        surf.blit(t, (x, py))
        py += t.get_height() + 2
    return py


class GameUI:
    def __init__(self, mode: str, agent, controller,
                 target_epochs: int | None = None):
        assert mode in ("train", "infer"), f"Unknown mode: {mode}"
        self.mode = mode
        self.qa = agent
        self.ctrl = controller
        self.target_epochs = target_epochs

        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        caption = "Minesweeper Q-Learning — "
        if mode == "train":
            caption += f"TRAINER  [{target_epochs:,} ep]" if target_epochs else "TRAINER"
        else:
            caption += "INFERENCE  (no training)"
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()

        self.FN   = _mfont(17, True)
        self.FN_S = _mfont(14)
        self.FN_H = _mfont(11, True)
        self.FN_T = _mfont(10)
        self.FN_B = _mfont(9)

        self.auto = (mode == "train" and target_epochs is not None)
        self.speed = 50 if mode == "train" else 5
        self.show_mine = False
        self.done_saved = False
        self.log = deque(maxlen=16)
        self._pause_frames = 0
        self._ep_start = agent.episode

        self.log.append(f"Board {ROWS}x{COLS}  mines={MINES}")
        if mode == "train":
            self.log.append(f"Loaded ep={agent.episode}  wins={agent.wins}  q={len(agent.q)}")
            if target_epochs:
                self.log.append(f"Target {target_epochs:,} ep — auto-save on finish")
        else:
            self.log.append(f"Loaded ep={agent.episode}  q-states={len(agent.q)}")
            self.log.append("ε=0 — pure greedy + probability")

    def _ep_session(self):
        return self.qa.episode - self._ep_start

    def _log(self, msg):
        self.log.append(msg)

    def _make_panel_fns(self, py_box):
        surf = self.screen

        def sep():
            pygame.draw.line(surf, BORDER, (PX, py_box[0]), (PX + PW - 6, py_box[0]))
            py_box[0] += 7

        def heading(txt, col=None):
            c = col if col else C_EPS
            t = self.FN_H.render(txt.upper(), True, c)
            surf.blit(t, (PX, py_box[0]))
            py_box[0] += t.get_height() + 4

        def kv(k, v, vc=T1):
            kt = self.FN_T.render(k, True, T2)
            vt = self.FN_T.render(str(v), True, vc)
            surf.blit(kt, (PX, py_box[0]))
            surf.blit(vt, (PX + PW - 8 - vt.get_width(), py_box[0]))
            py_box[0] += kt.get_height() + 4

        def advance(n):
            py_box[0] += n

        return sep, heading, kv, advance

    def _draw_board(self, board, agent_pos):
        from trainer import VR
        ar, ac = agent_pos
        safe_h, mine_h = board.constraint_solve()
        safe_set = set(safe_h)
        mine_set = set(mine_h)
        iter_set = {(r, c) for r, c in board.frontier(VR)}

        pygame.draw.rect(self.screen, (18, 22, 32),
                         (MPAD - 4, MPAD - 4, BOARD_W + 8, BOARD_H + 8),
                         border_radius=6)

        for r in range(ROWS):
            for c in range(COLS):
                cell = board.board[r][c]
                x = MPAD + c * (CELL + GAP)
                y = MPAD + r * (CELL + GAP)
                in_v = abs(r - ar) <= VR and abs(c - ac) <= VR
                draw_cell(
                    surf=self.screen, cell=cell, x=x, y=y, sz=CELL,
                    is_agent=(r == ar and c == ac),
                    in_vis=in_v,
                    in_iter=(r, c) in iter_set,
                    show_mine=self.show_mine,
                    is_safe=(r, c) in safe_set and not cell.is_revealed,
                    is_minh=(r, c) in mine_set and not cell.is_flagged,
                    fn=self.FN, fn_sm=self.FN_S,
                )

        vx0 = MPAD + max(0, ac - VR) * (CELL + GAP)
        vy0 = MPAD + max(0, ar - VR) * (CELL + GAP)
        vx1 = MPAD + min(COLS - 1, ac + VR) * (CELL + GAP) + CELL
        vy1 = MPAD + min(ROWS - 1, ar + VR) * (CELL + GAP) + CELL
        pygame.draw.rect(self.screen, C_BA,
                         (vx0, vy0, vx1 - vx0, vy1 - vy0), 1, border_radius=5)

        return safe_set, mine_set

    def _draw_panel_bg(self):
        pygame.draw.rect(self.screen, PANEL_BG,
                         (PX - 6, 4, PW + 10, WIN_H - 8), border_radius=8)
        pygame.draw.rect(self.screen, BORDER,
                         (PX - 6, 4, PW + 10, WIN_H - 8), 1, border_radius=8)

    def _draw_train_panel(self):
        qa = self.qa
        ctrl = self.ctrl
        surf = self.screen
        py = [10]
        sep, heading, kv, advance = self._make_panel_fns(py)

        title = self.FN_H.render("Q-LEARNING  MINESWEEPER  TRAINER", True, C_AGENT)
        surf.blit(title, (PX, py[0]))
        py[0] += title.get_height() + 3

        mode_col = C_WIN if self.done_saved else (T2 if self.auto else T3)
        status = (
            "✔ DONE — saved!  (Q to exit)" if self.done_saved else
            ("▶ AUTO — SPACE to pause" if self.auto else "⏸ MANUAL — SPACE / ENTER")
        )
        surf.blit(self.FN_T.render(status, True, mode_col), (PX, py[0]))
        py[0] += self.FN_T.size("X")[1] + 4

        if self.target_epochs:
            done = self._ep_session()
            frac = min(1.0, done / self.target_epochs)
            col = C_WIN if self.done_saved else C_EPS
            hbar(surf, PX, py[0], PW - 8, 13, frac, col, self.FN_B,
                 f"{done:,} / {self.target_epochs:,} ep  {frac * 100:.1f}%")
            advance(17)
        sep()

        heading("Training Metrics")
        kv("Episode",        qa.episode)
        kv("Wins / Losses",  f"{qa.wins} / {qa.losses}",
           C_WIN if qa.wins >= qa.losses else C_LOSE)
        kv("Win rate (all)", f"{ctrl.win_rate_all * 100:.2f}%",
           C_WIN if ctrl.win_rate_all > 0.30 else C_LOSE)
        kv("Win rate (200)", f"{ctrl.win_rate * 100:.1f}%",
           C_WIN if ctrl.win_rate > 0.30 else C_LOSE)
        kv("Total steps",    f"{qa.total_steps:,}")
        kv("Q-states",       f"{len(qa.q):,}")
        kv("Speed",          f"{self.speed} steps/frame")
        sep()

        heading("Exploration  ε-greedy")
        kv("ε now", f"{qa.eps:.5f}", C_EPS)
        kv("ε min", f"{qa.eps_min}")
        kv("α / γ", f"{qa.alpha} / {qa.gamma}")
        hbar(surf, PX, py[0], PW - 8, 10, qa.eps, C_EPS, self.FN_B, f"ε={qa.eps:.4f}")
        advance(14)
        sep()

        heading("Decision Source  (lifetime steps)")
        py[0] = decision_bars(surf, ctrl.cnt, PX, py[0], PW, self.FN_T, self.FN_B)
        sep()

        heading("Win Rate  (roll-20, last 200 ep)")
        if len(qa.win_history) >= 2:
            wd = list(qa.win_history)
            rolled = [sum(wd[max(0, i - 19):i + 1]) / len(wd[max(0, i - 19):i + 1])
                      for i in range(len(wd))]
            sparkline(surf, rolled, PX, py[0], CHART_W, CHART_H, C_WIN,
                      self.FN_B, baseline=0.5)
            surf.blit(
                self.FN_B.render(
                    f"now={rolled[-1] * 100:.1f}%  best={max(rolled) * 100:.1f}%",
                    True, C_WIN),
                (PX + 5, py[0] + CHART_H - 14))
        else:
            pygame.draw.rect(surf, (14, 18, 26), (PX, py[0], CHART_W, CHART_H),
                             border_radius=4)
            surf.blit(self.FN_T.render("waiting for data — press SPACE", True, T3),
                      (PX + 5, py[0] + CHART_H // 2 - 5))
        advance(CHART_H + 5)

        heading("Episode Reward  (last 200)")
        if len(qa.reward_history) >= 2:
            rd = list(qa.reward_history)
            sparkline(surf, rd, PX, py[0], CHART_W, CHART_H, C_REWARD,
                      self.FN_B, baseline=0)
            surf.blit(
                self.FN_B.render(
                    f"last={rd[-1]:+.1f}  avg={sum(rd) / len(rd):+.1f}  max={max(rd):+.1f}",
                    True, C_REWARD),
                (PX + 5, py[0] + CHART_H - 14))
        else:
            pygame.draw.rect(surf, (14, 18, 26), (PX, py[0], CHART_W, CHART_H),
                             border_radius=4)
        advance(CHART_H + 5)
        sep()

        heading("Last Step  (debug)")
        ar, ac = ctrl.agent_pos
        reason_col = (C_MINH   if "constraint:mine" in ctrl.last_reason else
                      C_SAFE   if "constraint:safe" in ctrl.last_reason else
                      C_PROB_M if "prob:mine"       in ctrl.last_reason else
                      C_PROB_S if "prob:safe"       in ctrl.last_reason else
                      C_AGENT  if "q-table"         in ctrl.last_reason else T2)
        kv("Pos",       f"({ar},{ac})")
        kv("Action",    ctrl.last_action,
           C_WIN if ctrl.last_action == "reveal" else C_FLAG)
        kv("Source",    ctrl.last_reason, reason_col)
        kv("Reward",    f"{ctrl.last_reward:+.1f}",
           C_WIN if ctrl.last_reward > 0 else C_LOSE if ctrl.last_reward < 0 else T2)
        kv("Ep reward", f"{ctrl.ep_reward:+.1f}", C_REWARD)
        kv("Ep steps",  ctrl.ep_steps)
        board = ctrl.board
        kv("Revealed",  f"{board.revealed}/{ROWS * COLS - MINES}")
        kv("Flags",     f"{board.flag_count}/{MINES}")
        sep()

        heading("Frontier  (top 5 by mine prob ↑)")
        py[0] = frontier_table(surf, ctrl.frontier_debug, PX, py[0], PW,
                               self.FN_B, self.FN_T)
        sep()

        self._draw_log(py)

    def _draw_infer_panel(self):
        qa = self.qa
        ctrl = self.ctrl
        surf = self.screen
        py = [10]
        sep, heading, kv, advance = self._make_panel_fns(py)

        title = self.FN_H.render("Q-LEARNING  MINESWEEPER  INFERENCE", True, C_AGENT)
        surf.blit(title, (PX, py[0]))
        py[0] += title.get_height() + 3

        mode_col = C_WIN if self.auto else T3
        surf.blit(
            self.FN_T.render(
                "▶ AUTO — SPACE to pause" if self.auto else "⏸ MANUAL — SPACE / ENTER",
                True, mode_col),
            (PX, py[0]))
        py[0] += self.FN_T.size("X")[1] + 4
        sep()

        heading("Session Stats")
        kv("Games played",    ctrl.games)
        kv("Wins / Losses",   f"{ctrl.wins} / {ctrl.losses}",
           C_WIN if ctrl.wins >= ctrl.losses else C_LOSE)
        kv("Win rate (all)",  f"{ctrl.win_rate_all * 100:.2f}%",
           C_WIN if ctrl.win_rate_all > 0.30 else C_LOSE)
        kv("Win rate (100)",  f"{ctrl.win_rate * 100:.1f}%",
           C_WIN if ctrl.win_rate > 0.30 else C_LOSE)
        kv("Steps this game", ctrl.ep_steps)
        sep()

        heading("Model Info")
        kv("Trained episodes", qa.episode)
        kv("Q-states loaded",  f"{len(qa.q):,}")
        kv("ε (epsilon)",      "0.000  (greedy)", T2)
        kv("α / γ",            f"{qa.alpha} / {qa.gamma}")
        sep()

        heading("Decision Source  (this session)")
        py[0] = decision_bars(surf, ctrl.cnt, PX, py[0], PW, self.FN_T, self.FN_B)
        sep()

        heading("Win Rate  (last 100 games)")
        CH = 52
        if len(ctrl.win_history) >= 2:
            wd = list(ctrl.win_history)
            rolled = [sum(wd[max(0, i - 9):i + 1]) / len(wd[max(0, i - 9):i + 1])
                      for i in range(len(wd))]
            sparkline(surf, rolled, PX, py[0], PW - 10, CH, C_WIN,
                      self.FN_B, baseline=0.5)
            surf.blit(
                self.FN_B.render(
                    f"now={rolled[-1] * 100:.1f}%  best={max(rolled) * 100:.1f}%",
                    True, C_WIN),
                (PX + 5, py[0] + CH - 14))
        else:
            pygame.draw.rect(surf, (14, 18, 26), (PX, py[0], PW - 10, CH),
                             border_radius=4)
            surf.blit(self.FN_T.render("press SPACE to start", True, T3),
                      (PX + 5, py[0] + CH // 2 - 5))
        advance(CH + 5)
        sep()

        heading("Last Step")
        ar, ac = ctrl.agent_pos
        board = ctrl.board
        reason_col = (C_MINH   if "constraint:mine" in ctrl.last_reason else
                      C_SAFE   if "constraint:safe" in ctrl.last_reason else
                      C_PROB_M if "prob:mine"       in ctrl.last_reason else
                      C_PROB_S if "prob:safe"       in ctrl.last_reason else
                      C_AGENT  if "q-table"         in ctrl.last_reason else T2)
        kv("Pos",      f"({ar},{ac})")
        kv("Action",   ctrl.last_action,
           C_WIN if ctrl.last_action == "reveal" else C_FLAG)
        kv("Source",   ctrl.last_reason, reason_col)
        kv("Reward",   f"{ctrl.last_reward:+.1f}",
           C_WIN if ctrl.last_reward > 0 else C_LOSE if ctrl.last_reward < 0 else T2)
        kv("Revealed", f"{board.revealed}/{ROWS * COLS - MINES}")
        kv("Flags",    f"{board.flag_count}/{MINES}")
        sep()

        heading("Frontier  (top 5 by mine prob ↑)")
        py[0] = frontier_table(surf, ctrl.frontier_debug, PX, py[0], PW,
                               self.FN_B, self.FN_T)
        sep()

        self._draw_log(py)

    def _draw_log(self, py):
        self.screen.blit(self.FN_H.render("LOG", True, T2), (PX, py[0]))
        py[0] += self.FN_H.size("X")[1] + 4
        visible = list(self.log)[-9:]
        for i, line in enumerate(visible):
            frac = (i + 1) / max(len(visible), 1)
            col = T3 if frac < 0.3 else T2 if frac < 0.7 else T1
            self.screen.blit(self.FN_T.render(line[:58], True, col), (PX, py[0]))
            py[0] += self.FN_T.size("X")[1] + 3
        pygame.draw.line(self.screen, BORDER, (PX, py[0]), (PX + PW - 6, py[0]))
        py[0] += 6

    def _draw_hotkeys_below_board(self, mode):
        y_start = MPAD + BOARD_H + 30
        keys_train = [
            ("SPACE", "auto train on/off"), ("ENTER", "manual step"),
            ("+/-",   "speed ±10"),         ("S",     "save qtable"),
            ("N",     "new episode"),       ("M",     "show/hide mines"),
            ("Q/ESC", "quit"),
        ]
        keys_infer = [
            ("SPACE", "auto-play on/off"),  ("ENTER", "manual step / next game"),
            ("+/-",   "speed ±5"),          ("N",     "new game"),
            ("M",     "show/hide mines"),   ("Q/ESC", "quit"),
        ]
        keys = keys_train if mode == "train" else keys_infer
        col1_x, col2_x = MPAD, MPAD + 200
        for i, (k, v) in enumerate(keys):
            x = col1_x if i < (len(keys) + 1) // 2 else col2_x
            y = y_start + (i % ((len(keys) + 1) // 2)) * (self.FN_T.size("X")[1] + 4)
            kt = self.FN_T.render(k, True, C_AGENT)
            vt = self.FN_T.render(v, True, T3)
            self.screen.blit(kt, (x, y))
            self.screen.blit(vt, (x + kt.get_width() + 8, y))

    def _draw_status_bar(self, board):
        qa, ctrl = self.qa, self.ctrl
        if self.mode == "train":
            txt = (f"ep={qa.episode}  wr(200)={ctrl.win_rate * 100:.1f}%"
                   f"  flags={board.flag_count}/{MINES}  revealed={board.revealed}")
        else:
            txt = (f"games={ctrl.games}  wins={ctrl.wins}  losses={ctrl.losses}"
                   f"  wr={ctrl.win_rate_all * 100:.1f}%"
                   f"  flags={board.flag_count}/{MINES}  revealed={board.revealed}")
        self.screen.blit(self.FN_T.render(txt, True, T2),
                         (MPAD, MPAD + BOARD_H + 8))

    def _draw_infer_overlay(self):
        ctrl = self.ctrl
        if not ctrl.game_over:
            return
        ov_col = (0, 190, 90, 60) if ctrl.game_result == "win" else (190, 35, 35, 60)
        ov = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        ov.fill(ov_col)
        self.screen.blit(ov, (MPAD, MPAD))
        msg = "✔  WIN!" if ctrl.game_result == "win" else "✘  BOOM"
        col = C_WIN if ctrl.game_result == "win" else C_LOSE
        mt = self.FN.render(msg, True, col)
        self.screen.blit(mt, mt.get_rect(center=(MPAD + BOARD_W // 2, MPAD + BOARD_H // 2)))

    def _handle_train_events(self, event):
        qa, ctrl = self.qa, self.ctrl
        if event.type == pygame.QUIT:
            if not self.done_saved:
                qa.save()
            return False
        if event.type != pygame.KEYDOWN:
            return True
        k = event.key
        if k in (pygame.K_q, pygame.K_ESCAPE):
            if not self.done_saved:
                qa.save()
            return False
        if k == pygame.K_SPACE and not self.done_saved:
            self.auto = not self.auto
            self._log(f"Auto: {'ON' if self.auto else 'OFF'}")
        elif k == pygame.K_RETURN and not self.auto and not self.done_saved:
            ctrl.step()
        elif k == pygame.K_n and not self.done_saved:
            ctrl._new_episode()
            self._log("New episode")
        elif k == pygame.K_s:
            qa.save()
            self._log(f"Saved  q-states={len(qa.q)}")
        elif k in (pygame.K_EQUALS, pygame.K_PLUS):
            self.speed = min(1000, self.speed + 10)
            self._log(f"Speed={self.speed}/frame")
        elif k == pygame.K_MINUS:
            self.speed = max(1, self.speed - 10)
            self._log(f"Speed={self.speed}/frame")
        elif k == pygame.K_m:
            self.show_mine = not self.show_mine
        return True

    def _handle_infer_events(self, event):
        ctrl = self.ctrl
        if event.type == pygame.QUIT:
            return False
        if event.type != pygame.KEYDOWN:
            return True
        k = event.key
        if k in (pygame.K_q, pygame.K_ESCAPE):
            return False
        if k == pygame.K_SPACE:
            self.auto = not self.auto
            self._log(f"Auto: {'ON' if self.auto else 'OFF'}")
        elif k == pygame.K_RETURN:
            if ctrl.game_over:
                ctrl._new_game()
            elif not self.auto:
                ctrl.step()
        elif k == pygame.K_n:
            ctrl._new_game()
            self._log("New game")
        elif k in (pygame.K_EQUALS, pygame.K_PLUS):
            self.speed = min(500, self.speed + 5)
            self._log(f"Speed={self.speed}/frame")
        elif k == pygame.K_MINUS:
            self.speed = max(1, self.speed - 5)
            self._log(f"Speed={self.speed}/frame")
        elif k == pygame.K_m:
            self.show_mine = not self.show_mine
        return True

    def _train_tick(self):
        qa, ctrl = self.qa, self.ctrl

        if self.target_epochs and not self.done_saved:
            if self._ep_session() >= self.target_epochs:
                self.auto = False
                self.done_saved = True
                qa.save()
                self._log("─" * 30)
                self._log(f"✔ {self.target_epochs:,} epochs done — saved!")
                self._log(f"  total ep={qa.episode}  wr={ctrl.win_rate * 100:.1f}%")
                self._log(f"  q-states={len(qa.q):,}")
                self._log("Close window or press Q to exit.")
                return

        if self.auto and not self.done_saved:
            for _ in range(self.speed):
                ctrl.step()
                if self.target_epochs and self._ep_session() >= self.target_epochs:
                    break
            if qa.episode % 100 == 0 and qa.episode > 0:
                self._log(f"ep={qa.episode:6d}  wr={ctrl.win_rate * 100:.1f}%"
                          f"  ε={qa.eps:.4f}  q={len(qa.q)}")

    def _infer_tick(self):
        ctrl = self.ctrl
        if self.auto:
            if ctrl.game_over:
                if self._pause_frames > 0:
                    self._pause_frames -= 1
                else:
                    self._log(f"Game {ctrl.games:4d} │ "
                              f"{'WIN ' if ctrl.game_result == 'win' else 'LOSE'} │ "
                              f"steps={ctrl.ep_steps:3d} │ "
                              f"wr={ctrl.win_rate * 100:.1f}%")
                    ctrl._new_game()
            else:
                for _ in range(self.speed):
                    ended = ctrl.step()
                    if ended:
                        self._pause_frames = 18
                        break

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if self.mode == "train":
                    running = self._handle_train_events(event)
                else:
                    running = self._handle_infer_events(event)
                if not running:
                    break

            if self.mode == "train":
                self._train_tick()
            else:
                self._infer_tick()

            self.screen.fill(BG)
            board = self.ctrl.board
            agent_pos = self.ctrl.agent_pos

            self._draw_panel_bg()
            self._draw_board(board, agent_pos)

            if self.mode == "infer":
                self._draw_infer_overlay()

            self._draw_status_bar(board)
            self._draw_hotkeys_below_board(self.mode)

            if self.mode == "train":
                self._draw_train_panel()
            else:
                self._draw_infer_panel()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()