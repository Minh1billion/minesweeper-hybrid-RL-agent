import sys
from collections import deque

import pygame

from agent import QAgent
from environment import Board
from trainer import Trainer, VR


BG       = (10, 12, 16)
PANEL    = (16, 20, 26)
BORDER   = (28, 34, 44)
T1       = (210, 210, 205)
T2       = (85, 95, 110)
T3       = (40, 46, 58)
C_WIN    = (55, 200, 110)
C_LOSE   = (200, 60, 60)
C_EPS    = (55, 130, 220)
C_REWARD = (200, 170, 50)
C_FLAG   = (195, 135, 35)
C_AGENT  = (50, 140, 230)
C_ITER   = (55, 185, 105)
C_SAFE   = (55, 220, 160)
C_MINH   = (220, 180, 50)
C_HIDDEN = (26, 32, 42)
C_REVL   = (18, 22, 30)
C_MINEC  = (160, 40, 40)
C_BA     = (50, 140, 230)
C_BI     = (55, 185, 105)
C_BV     = (32, 65, 120)
NUM_C = {
    1: (75, 125, 215),
    2: (75, 185, 115),
    3: (215, 75, 75),
    4: (115, 75, 195),
    5: (195, 75, 45),
    6: (75, 195, 195),
    7: (195, 75, 195),
    8: (145, 145, 145),
}

ROWS, COLS, MINES = 10, 10, 15
CELL    = 42
GAP     = 2
MPAD    = 14
BOARD_W = COLS * (CELL + GAP)
BOARD_H = ROWS * (CELL + GAP)
PX      = MPAD + BOARD_W + 16
PW      = 340
WIN_W   = PX + PW + 12
WIN_H   = max(BOARD_H + MPAD * 2 + 20, 740)
CHART_H = 56
CHART_W = PW - 8


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
              in_iter=False, show_mine=False, is_safe=False, is_minh=False,
              fn=None, fn_sm=None):
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
    elif in_iter:
        bc, bw = C_BI, 2
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


def sparkline(surf, data, x, y, w, h, col, label, font, baseline=None):
    pygame.draw.rect(surf, (12, 16, 22), (x, y, w, h), border_radius=3)
    pygame.draw.rect(surf, BORDER, (x, y, w, h), 1, border_radius=3)
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
        fill_col = (*col, 30)
        fill_s = pygame.Surface((w, h), pygame.SRCALPHA)
        adjusted = [(p[0] - x, p[1] - y) for p in fill_pts]
        pygame.draw.polygon(fill_s, fill_col, adjusted)
        surf.blit(fill_s, (x, y))
    t = font.render(label, True, T2)
    surf.blit(t, (x + 4, y + 3))


def hbar(surf, x, y, w, h, frac, col, font, label=""):
    pygame.draw.rect(surf, (12, 16, 22), (x, y, w, h), border_radius=3)
    fw = max(0, int(w * max(0, min(1, frac))))
    if fw:
        pygame.draw.rect(surf, col, (x, y, fw, h), border_radius=3)
    pygame.draw.rect(surf, BORDER, (x, y, w, h), 1, border_radius=3)
    if label:
        t = font.render(label, True, T1)
        surf.blit(t, t.get_rect(midright=(x + w - 4, y + h // 2)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Minesweeper Q-Learning Trainer")
    clock = pygame.time.Clock()

    FN   = mfont(16, True)
    FN_S = mfont(13)
    FN_H = mfont(10, True)
    FN_T = mfont(9)
    FN_B = mfont(8)

    qa      = QAgent(qtable_path="qtable.json")
    trainer = Trainer(ROWS, COLS, MINES, qa)

    auto       = False
    speed      = 50
    show_mine  = False
    log        = deque(maxlen=16)
    log.append(f"Board {ROWS}x{COLS}  mines={MINES}  VR={VR}")
    log.append(f"Loaded: ep={qa.episode} wins={qa.wins} q={len(qa.q)}")

    def add_log(msg):
        log.append(msg)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                qa.save()
                running = False
            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k == pygame.K_SPACE:
                    auto = not auto
                    add_log(f"Auto train: {'ON  (+/- = speed)' if auto else 'OFF'}")
                elif k == pygame.K_RETURN and not auto:
                    trainer.step()
                elif k == pygame.K_n:
                    trainer._new_episode()
                    add_log("New episode")
                elif k == pygame.K_s:
                    qa.save()
                    add_log(f"Saved  q-states={len(qa.q)}")
                elif k in (pygame.K_EQUALS, pygame.K_PLUS):
                    speed = min(1000, speed + 10)
                    add_log(f"Speed={speed}/frame")
                elif k == pygame.K_MINUS:
                    speed = max(1, speed - 10)
                    add_log(f"Speed={speed}/frame")
                elif k == pygame.K_m:
                    show_mine = not show_mine

        if auto:
            for _ in range(speed):
                trainer.step()
            if qa.episode % 100 == 0 and qa.episode > 0:
                add_log(
                    f"ep={qa.episode:6d}  wr={trainer.win_rate * 100:.1f}%"
                    f"  ε={qa.eps:.4f}  q={len(qa.q)}"
                )

        screen.fill(BG)
        board = trainer.board
        ar, ac = trainer.agent_pos
        safe_h, mine_h = board.constraint_solve()
        safe_set  = set(safe_h)
        mine_set  = set(mine_h)
        iter_set  = {(r, c) for r, c in board.frontier(VR)}

        for r in range(ROWS):
            for c in range(COLS):
                cell = board.board[r][c]
                x = MPAD + c * (CELL + GAP)
                y = MPAD + r * (CELL + GAP)
                in_v = abs(r - ar) <= VR and abs(c - ac) <= VR
                draw_cell(
                    surf=screen, cell=cell, x=x, y=y, sz=CELL,
                    is_agent=(r == ar and c == ac),
                    in_vis=in_v,
                    in_iter=(r, c) in iter_set,
                    show_mine=show_mine,
                    is_safe=(r, c) in safe_set and not cell.is_revealed,
                    is_minh=(r, c) in mine_set and not cell.is_flagged,
                    fn=FN, fn_sm=FN_S,
                )

        vx0 = MPAD + max(0, ac - VR) * (CELL + GAP)
        vy0 = MPAD + max(0, ar - VR) * (CELL + GAP)
        vx1 = MPAD + min(COLS - 1, ac + VR) * (CELL + GAP) + CELL
        vy1 = MPAD + min(ROWS - 1, ar + VR) * (CELL + GAP) + CELL
        pygame.draw.rect(screen, C_BA, (vx0, vy0, vx1 - vx0, vy1 - vy0), 1, border_radius=4)

        bst = (
            f"ep={qa.episode}  wr(200)={trainer.win_rate * 100:.1f}%"
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

        t = FN_H.render("Q-LEARNING MINESWEEPER TRAINER", True, C_AGENT)
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

        heading("Training Metrics")
        kv("Episode",        qa.episode)
        kv("Wins / Losses",  f"{qa.wins} / {qa.losses}",
           C_WIN if qa.wins >= qa.losses else C_LOSE)
        kv("Win rate (all)", f"{trainer.win_rate_all * 100:.2f}%",
           C_WIN if trainer.win_rate_all > 0.25 else C_LOSE)
        kv("Win rate (200)", f"{trainer.win_rate * 100:.1f}%",
           C_WIN if trainer.win_rate > 0.25 else C_LOSE)
        kv("Total steps",    f"{qa.total_steps:,}")
        kv("Q-states",       f"{len(qa.q):,}")
        kv("Speed",          f"{speed} steps/frame")
        sep()

        heading("Exploration  ε-greedy")
        kv("ε now", f"{qa.eps:.5f}", C_EPS)
        kv("ε min", f"{qa.eps_min}")
        kv("α / γ", f"{qa.alpha} / {qa.gamma}")
        hbar(screen, PX, py, PW - 8, 8, qa.eps, C_EPS, FN_B, f"ε={qa.eps:.4f}")
        py += 11
        sep()

        heading("Decision Source  (lifetime steps)")
        total_cnt = sum(trainer.cnt.values()) or 1
        src_items = [
            ("constraint:mine", C_MINH),
            ("constraint:safe", C_SAFE),
            ("q-table",         C_AGENT),
            ("random",          T2),
        ]
        for src, col in src_items:
            n   = trainer.cnt.get(src, 0)
            pct = n / total_cnt
            bw2, bh2 = PW - 8, 9
            pygame.draw.rect(screen, (12, 16, 22), (PX, py, bw2, bh2), border_radius=2)
            fw2 = int(bw2 * pct)
            if fw2:
                pygame.draw.rect(screen, col, (PX, py, fw2, bh2), border_radius=2)
            pygame.draw.rect(screen, BORDER, (PX, py, bw2, bh2), 1, border_radius=2)
            label_t = FN_T.render(f"{src}", True, col)
            count_t = FN_T.render(f"{n:,}  {pct * 100:.1f}%", True, T2)
            screen.blit(label_t, (PX + 3, py + bh2 + 1))
            screen.blit(count_t, (PX + PW - 8 - count_t.get_width(), py + bh2 + 1))
            py += bh2 + label_t.get_height() + 3
        sep()

        heading("Win Rate  (roll-20, last 200 ep)")
        CH = 50
        if len(qa.win_history) >= 2:
            wd     = list(qa.win_history)
            rolled = []
            for i in range(len(wd)):
                sl = wd[max(0, i - 19): i + 1]
                rolled.append(sum(sl) / len(sl))
            sparkline(screen, rolled, PX, py, CHART_W, CH, C_WIN, "", FN_B, baseline=0.5)
            cur_wr = rolled[-1]
            wt = FN_B.render(
                f"now={cur_wr * 100:.1f}%  best={max(rolled) * 100:.1f}%", True, C_WIN
            )
            screen.blit(wt, (PX + 4, py + CH - 12))
        else:
            pygame.draw.rect(screen, (12, 16, 22), (PX, py, CHART_W, CH), border_radius=3)
            t = FN_T.render("need data — press SPACE to start auto train", True, T3)
            screen.blit(t, (PX + 4, py + CH // 2 - 5))
        py += CH + 4

        heading("Episode Reward  (last 200)")
        if len(qa.reward_history) >= 2:
            rd = list(qa.reward_history)
            sparkline(screen, rd, PX, py, CHART_W, CH, C_REWARD, "", FN_B, baseline=0)
            rt = FN_B.render(
                f"last={rd[-1]:+.1f}  avg={sum(rd) / len(rd):+.1f}  max={max(rd):+.1f}",
                True, C_REWARD,
            )
            screen.blit(rt, (PX + 4, py + CH - 12))
        else:
            pygame.draw.rect(screen, (12, 16, 22), (PX, py, CHART_W, CH), border_radius=3)
        py += CH + 4
        sep()

        heading("Last Step  (debug)")
        reason_col = (
            C_MINH  if "mine"    in trainer.last_reason else
            C_SAFE  if "safe"    in trainer.last_reason else
            C_AGENT if "q-table" in trainer.last_reason else
            T2
        )
        kv("Pos",       f"({ar},{ac})")
        kv("Action",    trainer.last_action,
           C_WIN if trainer.last_action == "reveal" else C_FLAG)
        kv("Source",    trainer.last_reason, reason_col)
        kv("Reward",    f"{trainer.last_reward:+.1f}",
           C_WIN if trainer.last_reward > 0 else C_LOSE if trainer.last_reward < 0 else T2)
        kv("Ep reward", f"{trainer.ep_reward:+.1f}", C_REWARD)
        kv("Ep steps",  trainer.ep_steps)
        kv("Revealed",  f"{board.revealed}/{ROWS * COLS - MINES}")
        kv("Flags",     f"{board.flag_count}/{MINES}")
        sep()

        heading("Frontier Q-Values  (top 5 by confidence)")
        hdr_t = FN_B.render(" cell      Q[rev]   Q[flg]  best", True, T3)
        screen.blit(hdr_t, (PX, py))
        py += hdr_t.get_height() + 2
        pygame.draw.line(screen, BORDER, (PX, py), (PX + PW - 8, py))
        py += 3

        dbg = trainer.frontier_debug[:5]
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
            t = FN_T.render("  (no frontier — all moves random)", True, T3)
            screen.blit(t, (PX, py))
            py += t.get_height() + 2
        sep()

        heading("Log")
        visible = list(log)[-9:]
        for i, line in enumerate(visible):
            frac = (i + 1) / max(len(visible), 1)
            col  = T3 if frac < 0.3 else T2 if frac < 0.7 else T1
            t    = FN_T.render(line[:52], True, col)
            screen.blit(t, (PX, py))
            py += t.get_height() + 2
        sep()

        for k, v in [
            ("SPACE", "auto train on/off"),
            ("ENTER", "manual step"),
            ("+/-",   "speed ±10"),
            ("S",     "save qtable"),
            ("N",     "new episode"),
            ("M",     "show/hide mines"),
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