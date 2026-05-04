import pygame
import sys
import copy
import utils
import hc

# ── Palette ────────────────────────────────────────────────────────────────
BG         = (15,  17,  26)
GRID_LINE  = (40,  46,  70)
CELL_EMPTY = (22,  26,  42)
CELL_HOVER = (38,  46,  72)
HOSPITAL_C = (52,  211, 153)
HOUSE_C    = (251, 191,  36)
COST_LINE  = (99,  102, 241)
COST_BEST  = (52,  211, 153)
TEXT_MAIN  = (230, 232, 245)
TEXT_DIM   = (110, 118, 155)
BTN_RUN    = (52,  211, 153)
BTN_RST    = (99,  102, 241)
PANEL_BG   = (18,  21,  34)
ACCENT     = (52,  211, 153)
FLASH_C    = (52,  211, 153)

INITIAL_MAP = [
    [None, None, None, None, None, None, None, None, utils.OBJECT_HOUSE, None],
    [None, None, utils.OBJECT_HOUSE, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None],
    [None, utils.OBJECT_HOUSE, None, None, None, None, None, None, None, utils.OBJECT_HOSPITAL],
    [None, None, None, None, None, None, utils.OBJECT_HOUSE, None, None, None],
]
ROWS = len(INITIAL_MAP)
COLS = len(INITIAL_MAP[0])
FPS  = 60
ANIM_DELAY = 0.55


# ── Lerp ───────────────────────────────────────────────────────────────────
def lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ── Draw hospital / house shapes ───────────────────────────────────────────
def draw_hospital(surf, cx, cy, size):
    """Green rounded square with a white plus sign."""
    half = size // 2
    r = pygame.Rect(cx - half, cy - half, size, size)
    pygame.draw.rect(surf, HOSPITAL_C, r, border_radius=size // 6)
    # white cross
    arm_w = max(4, size // 5)
    arm_l = size - size // 4
    pygame.draw.rect(surf, (255, 255, 255),
                     (cx - arm_w // 2, cy - arm_l // 2, arm_w, arm_l))
    pygame.draw.rect(surf, (255, 255, 255),
                     (cx - arm_l // 2, cy - arm_w // 2, arm_l, arm_w))


def draw_house(surf, cx, cy, size):
    """Amber house: square body + triangular roof."""
    half  = size // 2
    roof_h = size // 3
    body_h = size - roof_h
    body_y = cy - half + roof_h

    # body
    pygame.draw.rect(surf, HOUSE_C,
                     (cx - half, body_y, size, body_h), border_radius=4)
    # door
    door_w = size // 4
    door_h = size // 3
    pygame.draw.rect(surf, lerp_color(HOUSE_C, (10, 10, 10), 0.4),
                     (cx - door_w // 2, body_y + body_h - door_h, door_w, door_h),
                     border_radius=2)
    # roof
    roof_pts = [
        (cx - half - 4, body_y),
        (cx + half + 4, body_y),
        (cx, cy - half - 2),
    ]
    pygame.draw.polygon(surf, lerp_color(HOUSE_C, (180, 100, 0), 0.45), roof_pts)


# ── Cost chart ─────────────────────────────────────────────────────────────
class CostChart:
    def __init__(self):
        self.data = []

    def push(self, v):  self.data.append(v)
    def clear(self):    self.data.clear()

    def draw(self, surf, rect, font_small):
        rx, ry, rw, rh = rect
        pygame.draw.rect(surf, (26, 30, 50), rect, border_radius=10)
        pygame.draw.rect(surf, GRID_LINE,    rect, 1,  border_radius=10)

        if len(self.data) < 2:
            hint = font_small.render("Run to see chart", True, TEXT_DIM)
            surf.blit(hint, hint.get_rect(center=(rx + rw // 2, ry + rh // 2)))
            return

        mn, mx = min(self.data), max(self.data)
        span   = mx - mn or 1
        pad    = 12

        pts = []
        for i, v in enumerate(self.data):
            px = rx + pad + int(i / (len(self.data) - 1) * (rw - pad * 2))
            py = ry + rh - pad - int((v - mn) / span * (rh - pad * 2))
            pts.append((px, py))

        for i in range(len(pts) - 1):
            t     = i / max(len(pts) - 2, 1)
            color = lerp_color(COST_LINE, COST_BEST, t)
            pygame.draw.line(surf, color, pts[i], pts[i + 1], 3)

        pygame.draw.circle(surf, ACCENT, pts[-1], 7)
        pygame.draw.circle(surf, (255, 255, 255), pts[-1], 3)

        hi_lbl = font_small.render(str(mx), True, TEXT_DIM)
        lo_lbl = font_small.render(str(mn), True, TEXT_DIM)
        surf.blit(hi_lbl, (rx + pad, ry + pad))
        surf.blit(lo_lbl, (rx + pad, ry + rh - pad - lo_lbl.get_height()))


# ── Button ─────────────────────────────────────────────────────────────────
class Button:
    def __init__(self, rect, label, color):
        self.rect  = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.hover = False

    def update(self, mx, my):
        self.hover = self.rect.collidepoint(mx, my)

    def draw(self, surf, font):
        c = lerp_color(self.color, (255, 255, 255), 0.22 if self.hover else 0)
        r = self.rect.inflate(6 if self.hover else 0, 4 if self.hover else 0)
        pygame.draw.rect(surf, c, r, border_radius=12)
        lbl = font.render(self.label, True, (10, 12, 20))
        surf.blit(lbl, lbl.get_rect(center=r.center))

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


# ── Algorithm step generators ──────────────────────────────────────────────
# Both algorithms live in hc.py and are generators that yield (grid, cost).
# main.py simply calls them directly — no logic is duplicated here.



# ── Main ───────────────────────────────────────────────────────────────────
def main():
    pygame.init()

    info   = pygame.display.Info()
    SW, SH = info.current_w, info.current_h
    screen = pygame.display.set_mode((SW, SH), pygame.FULLSCREEN)
    pygame.display.set_caption("Hill Climbing — Hospital Optimizer")
    clock  = pygame.time.Clock()

    # ── Layout ────────────────────────────────────────────────────────────
    PAD     = max(24, SW // 50)
    PANEL_W = max(340, SW // 4)
    AVAIL_W = SW - PANEL_W - PAD * 3
    AVAIL_H = SH - PAD * 2

    CELL = min(AVAIL_W // COLS, AVAIL_H // ROWS)
    CELL = max(CELL, 48)

    GRID_W = COLS * CELL
    GRID_H = ROWS * CELL
    GX     = PAD + (AVAIL_W - GRID_W) // 2
    GY     = PAD + (AVAIL_H - GRID_H) // 2
    PX     = SW - PANEL_W - PAD

    # ── Fonts ─────────────────────────────────────────────────────────────
    F_TITLE  = max(30, SH // 26)
    F_BODY   = max(24, SH // 36)
    F_SMALL  = max(18, SH // 48)
    F_COORD  = max(13, SH // 70)
    F_METRIC = max(36, SH // 20)

    font_title  = pygame.font.SysFont("dejavusans", F_TITLE, bold=True)
    font_body   = pygame.font.SysFont("dejavusans", F_BODY)
    font_small  = pygame.font.SysFont("dejavusans", F_SMALL)
    font_coord  = pygame.font.SysFont("dejavusans", F_COORD)
    font_metric = pygame.font.SysFont("dejavusans", F_METRIC, bold=True)

    # ── App state ─────────────────────────────────────────────────────────
    current_map  = copy.deepcopy(INITIAL_MAP)
    initial_cost = utils.cost(current_map)
    current_cost = initial_cost

    chart = CostChart()
    chart.push(current_cost)

    steps        = []
    step_idx     = 0
    running_anim = False
    done         = False
    anim_timer   = 0.0
    hover_cell   = None
    flash        = {}
    active_algo  = None   # "hc" | "sa"

    BTN_H   = max(36, SH // 22)
    BTN_GAP = 10
    CHART_H = max(150, SH // 7)

    btn_run = Button(
        (PX, SH - PAD - BTN_H * 3 - BTN_GAP * 2, PANEL_W - PAD, BTN_H),
        "Run Hill Climbing", BTN_RUN)
    btn_sa  = Button(
        (PX, SH - PAD - BTN_H * 2 - BTN_GAP, PANEL_W - PAD, BTN_H),
        "Run Annealing", (251, 146, 60))
    btn_rst = Button(
        (PX, SH - PAD - BTN_H, PANEL_W - PAD, BTN_H),
        "Reset", BTN_RST)

    # ── State helpers ─────────────────────────────────────────────────────
    def start_run(algo="hc"):
        nonlocal steps, step_idx, running_anim, done, current_map, current_cost, active_algo
        active_algo  = algo
        initial      = copy.deepcopy(INITIAL_MAP)
        if algo == "hc":
            steps = list(hc.hill_climbing(initial))
        else:
            steps = list(hc.simulated_annealing(
                initial, T_min=0.1, T_initial=100.0, cooling_rate=0.92))
        step_idx     = 0
        running_anim = True
        done         = False
        current_map  = copy.deepcopy(INITIAL_MAP)
        current_cost = utils.cost(current_map)
        chart.clear(); chart.push(current_cost)
        flash.clear()

    def do_reset():
        nonlocal current_map, current_cost, steps, step_idx, running_anim, done, active_algo
        current_map  = copy.deepcopy(INITIAL_MAP)
        current_cost = utils.cost(current_map)
        steps = []; step_idx = 0
        running_anim = False; done = False
        active_algo  = None
        chart.clear(); chart.push(current_cost)
        flash.clear()

    # ── Draw grid ─────────────────────────────────────────────────────────
    def draw_grid(surf):
        nonlocal hover_cell
        mx, my     = pygame.mouse.get_pos()
        hover_cell = None

        for r in range(ROWS):
            for c in range(COLS):
                rx  = GX + c * CELL
                ry  = GY + r * CELL
                cr  = pygame.Rect(rx, ry, CELL - 2, CELL - 2)

                is_hov = cr.collidepoint(mx, my)
                if is_hov:
                    hover_cell = (r, c)

                pygame.draw.rect(surf, CELL_HOVER if is_hov else CELL_EMPTY,
                                 cr, border_radius=8)

                # flash overlay
                key = (r, c)
                if key in flash:
                    ov = pygame.Surface((CELL - 2, CELL - 2), pygame.SRCALPHA)
                    ov.fill((*FLASH_C, int(flash[key] * 160)))
                    surf.blit(ov, (rx, ry))
                    flash[key] = max(0.0, flash[key] - 0.055)
                    if flash[key] == 0.0:
                        del flash[key]

                cx2 = rx + CELL // 2
                cy2 = ry + CELL // 2
                obj = current_map[r][c]
                sz  = CELL - 22

                if obj == utils.OBJECT_HOSPITAL:
                    draw_hospital(surf, cx2, cy2, sz)
                elif obj == utils.OBJECT_HOUSE:
                    draw_house(surf, cx2, cy2, sz)

                coord = font_coord.render(f"{c},{r}", True, (50, 56, 82))
                surf.blit(coord, (rx + 5, ry + 5))

        for r in range(ROWS + 1):
            pygame.draw.line(surf, GRID_LINE,
                             (GX, GY + r * CELL), (GX + GRID_W, GY + r * CELL))
        for c in range(COLS + 1):
            pygame.draw.line(surf, GRID_LINE,
                             (GX + c * CELL, GY), (GX + c * CELL, GY + GRID_H))
        pygame.draw.rect(surf, (55, 62, 95), (GX, GY, GRID_W, GRID_H), 2, border_radius=4)

    # ── Draw panel ────────────────────────────────────────────────────────
    def draw_panel(surf):
        panel_bg = pygame.Surface((PANEL_W + PAD, SH))
        panel_bg.fill(PANEL_BG)
        surf.blit(panel_bg, (PX - PAD // 2, 0))
        pygame.draw.line(surf, GRID_LINE,
                         (PX - PAD // 2, 0), (PX - PAD // 2, SH), 2)

        y = PAD

        t1 = font_title.render("Hospital Optimizer", True, TEXT_MAIN)
        surf.blit(t1, (PX, y));  y += t1.get_height() + 6
        algo_label = ("Simulated Annealing" if active_algo == "sa"
                      else "Hill Climbing" if active_algo == "hc"
                      else "Hill Climbing / Annealing")
        t2 = font_small.render(f"{algo_label}  ·  Local Search", True, ACCENT)
        surf.blit(t2, (PX, y));  y += t2.get_height() + 20
        pygame.draw.line(surf, GRID_LINE, (PX, y), (PX + PANEL_W - PAD, y)); y += 20

        saving = initial_cost - current_cost

        def metric_block(label, value, color):
            nonlocal y
            lbl = font_small.render(label, True, TEXT_DIM)
            val = font_metric.render(str(value), True, color)
            surf.blit(lbl, (PX, y));  y += lbl.get_height() + 4
            surf.blit(val, (PX, y));  y += val.get_height() + 18

        metric_block("Initial Cost",  initial_cost, TEXT_DIM)
        metric_block("Current Cost",  current_cost,
                     ACCENT if current_cost < initial_cost else TEXT_MAIN)
        metric_block("Improvement",
                     f"-{saving}" if saving > 0 else "0",
                     HOSPITAL_C if saving > 0 else TEXT_DIM)
        metric_block("Steps Taken",
                     max(0, step_idx - 1) if steps else 0, TEXT_MAIN)

        pygame.draw.line(surf, GRID_LINE, (PX, y), (PX + PANEL_W - PAD, y)); y += 16

        # Status badge
        if done:
            algo_name = "Annealing" if active_algo == "sa" else "Hill Climbing"
            status, sc = f"Optimal Found ({algo_name})", HOSPITAL_C
        elif running_anim:
            status, sc = "Optimizing...", COST_LINE
        else:
            status, sc = "Ready", TEXT_DIM

        badge = pygame.Rect(PX, y, PANEL_W - PAD, BTN_H - 6)
        ov    = pygame.Surface((badge.w, badge.h), pygame.SRCALPHA)
        ov.fill((*sc, 35))
        surf.blit(ov, badge.topleft)
        pygame.draw.rect(surf, sc, badge, 2, border_radius=10)
        st = font_body.render(status, True, sc)
        surf.blit(st, st.get_rect(center=badge.center))
        y += badge.h + 20

        # Chart — size it to fill remaining space above the legend
        icon_sz   = F_BODY
        legend_h  = (icon_sz + 10) * 2 + 14 + 10   # separator + 2 rows + padding
        buttons_h = BTN_H * 3 + BTN_GAP * 2 + PAD
        chart_bottom = SH - buttons_h - legend_h
        available_chart_h = max(60, chart_bottom - y - font_small.get_height() - 6 - 20)

        chart_lbl = font_small.render("Cost over steps", True, TEXT_DIM)
        surf.blit(chart_lbl, (PX, y)); y += chart_lbl.get_height() + 6
        chart_rect = (PX, y, PANEL_W - PAD, available_chart_h)
        chart.draw(surf, chart_rect, font_small)

        # Legend — anchored just above the buttons
        ly = SH - buttons_h - legend_h
        pygame.draw.line(surf, GRID_LINE, (PX, ly), (PX + PANEL_W - PAD, ly)); ly += 14
        for draw_fn, label in [
            (lambda s, cx, cy: draw_hospital(s, cx, cy, icon_sz), "Hospital (movable)"),
            (lambda s, cx, cy: draw_house(s, cx, cy, icon_sz),    "House (fixed)"),
        ]:
            draw_fn(surf, PX + icon_sz // 2, ly + icon_sz // 2)
            lt = font_small.render(label, True, TEXT_DIM)
            surf.blit(lt, (PX + icon_sz + 10, ly + (icon_sz - lt.get_height()) // 2))
            ly += icon_sz + 10

        # Hover info
        if hover_cell:
            r, c = hover_cell
            obj  = current_map[r][c]
            kind = ("Hospital" if obj == utils.OBJECT_HOSPITAL
                    else "House" if obj == utils.OBJECT_HOUSE
                    else "Empty")
            ht = font_small.render(f"Cell ({c}, {r}) - {kind}", True, TEXT_DIM)
            surf.blit(ht, (PX, btn_run.rect.top - ht.get_height() - 12))

        esc = font_coord.render("ESC to exit", True, (50, 56, 80))
        surf.blit(esc, (PX, SH - esc.get_height() - 6))

    # ── Event loop ────────────────────────────────────────────────────────
    while True:
        dt = clock.tick(FPS) / 1000.0
        mx, my = pygame.mouse.get_pos()
        btn_run.update(mx, my)
        btn_sa.update(mx, my)
        btn_rst.update(mx, my)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit(); sys.exit()
            if btn_run.clicked(event) and not running_anim:
                start_run("hc")
            if btn_sa.clicked(event) and not running_anim:
                start_run("sa")
            if btn_rst.clicked(event):
                do_reset()

        if running_anim and steps:
            anim_timer += dt
            if anim_timer >= ANIM_DELAY:
                anim_timer = 0.0
                if step_idx < len(steps):
                    prev_map = current_map
                    current_map, current_cost = steps[step_idx]
                    for r in range(ROWS):
                        for c in range(COLS):
                            if current_map[r][c] != prev_map[r][c]:
                                flash[(r, c)] = 1.0
                    chart.push(current_cost)
                    step_idx += 1
                else:
                    running_anim = False
                    done         = True

        screen.fill(BG)
        draw_grid(screen)
        draw_panel(screen)
        btn_run.draw(screen, font_body)
        btn_sa.draw(screen, font_body)
        btn_rst.draw(screen, font_body)
        pygame.display.flip()


if __name__ == "__main__":
    main()