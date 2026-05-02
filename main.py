#!/usr/bin/env python3
# =============================================================================
# Sudoku Calm — pygame / pygbag version
# Works locally and on itch.io via pygbag.
#
# Features : 4 difficulty levels (Easy / Medium / Hard / Expert)
#            Unique-solution puzzle generation (guaranteed)
#            Heat map — empty cells colored by how constrained they are
#            Row/column highlight when a cell is selected
#            Match highlight — all cells sharing the selected number glow gold
#            Conflict highlight — immediate red on illegal digit entry
#            Conflict warning — sidebar notice when a conflict is entered
#            Logic assistant — shows available numbers for the selected cell
#            Validate — checks your answers, marks wrong cells red
#            Solve (Cheat) — reveals the full solution in yellow
#            Erase button — clear the selected cell with one click
#            Undo / Redo — Ctrl+Z / Ctrl+Y or sidebar buttons
#            Numpad support — numpad 1-9 works for input
#
# Controls : Click a cell to select it
#            Type 1-9 (top row or numpad) to enter a number
#            Backspace / Delete / Numpad-0 / Erase button to clear a cell
#            Ctrl+Z to undo, Ctrl+Y to redo
#            Arrow keys to move selection
#
# To run locally : python3 sudoku_calm.py
# To run on web  : pygbag sudoku_calm.py  →  zip build/web  →  upload to itch.io
# =============================================================================

import asyncio
import random

import pygame


# =============================================================================
# LAYOUT CONSTANTS
# =============================================================================
CELL        = 56
GRID_PX     = CELL * 9
SIDEBAR     = 220
TOPBAR      = 60
SCREEN_W    = GRID_PX + SIDEBAR
SCREEN_H    = GRID_PX + TOPBAR

SB_PAD      = 10
BTN_H       = 34
BTN_GAP     = 6
SECTION_GAP = 10

SX = GRID_PX + SB_PAD
SW = SIDEBAR - SB_PAD * 2

DIFFICULTIES = [
    ("Easy",   30),
    ("Medium", 45),
    ("Hard",   55),
    ("Expert", 64),
]

_y              = TOPBAR + SB_PAD
SB_ROW1_Y       = _y;  _y += BTN_H + BTN_GAP
SB_ROW2_Y       = _y;  _y += BTN_H + SECTION_GAP
SB_DIFF_LABEL_Y = _y + 6;  _y += 20 + BTN_GAP
SB_DIFF_Y       = _y
SB_DIFF_SLOT    = BTN_H + BTN_GAP
_y             += len(DIFFICULTIES) * SB_DIFF_SLOT + SECTION_GAP
SB_ASST_Y       = _y;  _y += 60 + SECTION_GAP
SB_SEP_Y        = _y;  _y += 1  + SECTION_GAP
SB_BTN_VAL_Y    = _y;  _y += BTN_H + BTN_GAP
SB_BTN_SOL_Y    = _y;  _y += BTN_H + SECTION_GAP
SB_MSG_Y        = _y


# =============================================================================
# COLOR PALETTE
# =============================================================================
BG_DARK      = ( 18,  18,  18)
BG_CELL      = ( 30,  30,  30)
BG_CLUE      = ( 18,  18,  18)
BG_SELECTED  = ( 68,  68,  68)
BG_HIGHLIGHT = ( 45,  45,  45)
BG_MATCH     = ( 55,  55,  20)
BG_CONFLICT  = ( 60,  18,  18)
BG_SIDEBAR   = ( 24,  24,  24)

WHITE      = (255, 255, 255)
GRAY       = (100, 100, 100)
LIGHT_GRAY = (160, 160, 160)

FG_CLUE     = (  0, 184, 148)
FG_USER     = (255, 255, 255)
FG_WRONG    = (255, 118, 117)
FG_CHEAT    = (253, 203, 110)
FG_CONFLICT = (255, 118, 117)

ACCENT_BLUE   = (  9, 132, 227)
ACCENT_GREEN  = (  0, 184, 148)
ACCENT_PURPLE = (108,  92, 231)
ACCENT_RED    = (214,  48,  49)
ACCENT_ORANGE = (225, 112,  85)
ACCENT_GRAY   = ( 55,  55,  65)

BORDER_OUTER = ( 85,  85,  85)
BORDER_BOX   = ( 68,  68,  68)
BORDER_SEL   = (255, 255, 255)

NUMPAD_KEYS = {
    pygame.K_KP1: 1, pygame.K_KP2: 2, pygame.K_KP3: 3,
    pygame.K_KP4: 4, pygame.K_KP5: 5, pygame.K_KP6: 6,
    pygame.K_KP7: 7, pygame.K_KP8: 8, pygame.K_KP9: 9,
}

HEAT_MAP = {
    1: (255, 118, 117),
    2: ( 85, 239, 196),
    3: (116, 185, 255),
    4: (129, 236, 236),
    5: (162, 155, 254),
    6: (255, 234, 167),
}
HEAT_DEFAULT = (45, 52, 54)


# =============================================================================
# SOLVER
# =============================================================================

def is_valid(board, r, c, n):
    for i in range(9):
        if board[r][i] == n or board[i][c] == n:
            return False
    br, bc = (r // 3) * 3, (c // 3) * 3
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            if board[i][j] == n:
                return False
    return True


def fill_board(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] != 0:
                continue
            digits = list(range(1, 10))
            random.shuffle(digits)
            for n in digits:
                if is_valid(board, r, c, n):
                    board[r][c] = n
                    if fill_board(board):
                        return True
                    board[r][c] = 0
            return False
    return True


def count_solutions(board, limit=2):
    best_r, best_c, best_count = -1, -1, 10
    for r in range(9):
        for c in range(9):
            if board[r][c] != 0:
                continue
            cnt = sum(1 for n in range(1, 10) if is_valid(board, r, c, n))
            if cnt == 0:
                return 0
            if cnt < best_count:
                best_r, best_c, best_count = r, c, cnt
                if cnt == 1:
                    break
        if best_count == 1:
            break
    if best_r == -1:
        return 1
    total = 0
    for n in range(1, 10):
        if is_valid(board, best_r, best_c, n):
            board[best_r][best_c] = n
            total += count_solutions(board, limit)
            board[best_r][best_c] = 0
            if total >= limit:
                return total
    return total


def make_puzzle(remove_count):
    board = [[0] * 9 for _ in range(9)]
    fill_board(board)
    solution = [row[:] for row in board]
    positions = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(positions)
    removed = 0
    for r, c in positions:
        if removed >= remove_count:
            break
        backup = board[r][c]
        board[r][c] = 0
        if count_solutions(board) == 1:
            removed += 1
        else:
            board[r][c] = backup
    return board, solution


# =============================================================================
# CELL QUERY HELPERS
# =============================================================================

def affected_cells(r, c):
    cells = set()
    for i in range(9):
        cells.add((r, i))
        cells.add((i, c))
    br, bc = (r // 3) * 3, (c // 3) * 3
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            cells.add((i, j))
    return cells


def get_used(board, user, r, c):
    used = set()
    for i in range(9):
        used.update([board[r][i], user[r][i], board[i][c], user[i][c]])
    br, bc = (r // 3) * 3, (c // 3) * 3
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            used.update([board[i][j], user[i][j]])
    return used


def possible_count(board, user, r, c):
    return sum(1 for d in range(1, 10) if d not in get_used(board, user, r, c))


def available_digits(board, user, r, c):
    return [str(d) for d in range(1, 10) if d not in get_used(board, user, r, c)]


def has_conflict(board, user, r, c, n):
    for i in range(9):
        if i != c and (board[r][i] == n or user[r][i] == n):
            return True
        if i != r and (board[i][c] == n or user[i][c] == n):
            return True
    br, bc = (r // 3) * 3, (c // 3) * 3
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            if (i != r or j != c) and (board[i][j] == n or user[i][j] == n):
                return True
    return False


# =============================================================================
# CELL CACHE
# =============================================================================

class CellCache:
    def __init__(self):
        self._heat  = {}
        self._avail = {}

    def dirty(self, r, c):
        for pos in affected_cells(r, c):
            self._heat.pop(pos, None)
            self._avail.pop(pos, None)

    def dirty_all(self):
        self._heat.clear()
        self._avail.clear()

    def heat(self, board, user, r, c):
        if (r, c) not in self._heat:
            self._heat[(r, c)] = possible_count(board, user, r, c)
        return self._heat[(r, c)]

    def avail(self, board, user, r, c):
        if (r, c) not in self._avail:
            self._avail[(r, c)] = available_digits(board, user, r, c)
        return self._avail[(r, c)]


# =============================================================================
# GAME CLASS
# =============================================================================

class Game:
    def __init__(self):
        self._cache    = CellCache()
        self._history  = []
        self._future   = []
        self._board    = [[0]*9 for _ in range(9)]
        self._solution = [[0]*9 for _ in range(9)]
        self._user     = [[0]*9 for _ in range(9)]
        self._wrong    = [[False]*9 for _ in range(9)]
        self._conflict = [[False]*9 for _ in range(9)]
        self._cheat    = [[False]*9 for _ in range(9)]

    def load_puzzle(self, puzzle):
        board, solution = puzzle
        self._board    = board
        self._solution = solution
        self._user     = [[0]     * 9 for _ in range(9)]
        self._wrong    = [[False] * 9 for _ in range(9)]
        self._conflict = [[False] * 9 for _ in range(9)]
        self._cheat    = [[False] * 9 for _ in range(9)]
        self._history.clear()
        self._future.clear()
        self._cache.dirty_all()

    def place(self, r, c, n):
        if self._board[r][c] != 0:
            return
        self._save_history()
        self._user[r][c]  = n
        self._wrong[r][c] = False
        self._cheat[r][c] = False
        self._sync(r, c)

    def clear(self, r, c):
        if self._board[r][c] != 0 or self._user[r][c] == 0:
            return
        self._save_history()
        self._user[r][c]     = 0
        self._wrong[r][c]    = False
        self._cheat[r][c]    = False
        self._conflict[r][c] = False
        self._sync(r, c)

    def undo(self):
        if not self._history:
            return False
        self._future.append(self._snapshot())
        self._restore(self._history.pop())
        return True

    def redo(self):
        if not self._future:
            return False
        self._history.append(self._snapshot())
        self._restore(self._future.pop())
        return True

    def validate(self):
        for r in range(9):
            for c in range(9):
                self._wrong[r][c] = False
        all_ok = True
        for r in range(9):
            for c in range(9):
                if self._board[r][c] != 0:
                    continue
                v = self._user[r][c]
                if v == 0:
                    all_ok = False
                elif v != self._solution[r][c]:
                    self._wrong[r][c] = True
                    all_ok = False
        return all_ok

    def solve_cheat(self):
        for r in range(9):
            for c in range(9):
                if self._board[r][c] == 0:
                    self._user[r][c]     = self._solution[r][c]
                    self._cheat[r][c]    = True
                    self._wrong[r][c]    = False
                    self._conflict[r][c] = False
        self._history.clear()
        self._future.clear()
        self._cache.dirty_all()

    def is_clue(self, r, c):     return self._board[r][c] != 0
    def value(self, r, c):       return self._board[r][c] or self._user[r][c]
    def is_wrong(self, r, c):    return self._wrong[r][c]
    def is_conflict(self, r, c): return self._conflict[r][c]
    def is_cheat(self, r, c):    return self._cheat[r][c]
    def can_undo(self):          return bool(self._history)
    def can_redo(self):          return bool(self._future)

    def heat(self, r, c):
        return self._cache.heat(self._board, self._user, r, c)

    def avail(self, r, c):
        return self._cache.avail(self._board, self._user, r, c)

    def has_any_empty(self):
        return any(
            self._board[r][c] == 0 and self._user[r][c] == 0
            for r in range(9) for c in range(9)
        )

    def _snapshot(self):
        return [row[:] for row in self._user]

    def _save_history(self):
        self._history.append(self._snapshot())
        self._future.clear()

    def _restore(self, saved_user):
        self._user = saved_user
        for r in range(9):
            for c in range(9):
                v = self._user[r][c]
                if v == 0 or self._board[r][c] != 0:
                    self._conflict[r][c] = False
                    self._wrong[r][c]    = False
                else:
                    self._conflict[r][c] = has_conflict(
                        self._board, self._user, r, c, v)
        self._cache.dirty_all()

    def _sync(self, r, c):
        for pr, pc in affected_cells(r, c):
            v = self._user[pr][pc]
            if v == 0 or self._board[pr][pc] != 0:
                self._conflict[pr][pc] = False
            else:
                self._conflict[pr][pc] = has_conflict(
                    self._board, self._user, pr, pc, v)
        self._cache.dirty(r, c)


# =============================================================================
# DRAW HELPERS
# =============================================================================

def draw_text(surface, font, text, color, cx, cy):
    surf = font.render(text, True, color)
    surface.blit(surf, surf.get_rect(center=(cx, cy)))


def draw_button(surface, font, text, color, rect, hover=False, disabled=False):
    if disabled:
        col, text_col = ACCENT_GRAY, (80, 80, 80)
    else:
        col      = tuple(min(255, ch + 20) for ch in color) if hover else color
        text_col = WHITE
    pygame.draw.rect(surface, col, rect, border_radius=6)
    draw_text(surface, font, text, text_col, rect.centerx, rect.centery)


def cell_bg_color(game, r, c, sel_r, sel_c, sel_val, selected):
    val = game.value(r, c)
    if selected and r == sel_r and c == sel_c:  return BG_SELECTED
    if selected and sel_val and val == sel_val:  return BG_MATCH
    if selected and (r == sel_r or c == sel_c): return BG_HIGHLIGHT
    if game.is_clue(r, c):                      return BG_CLUE
    if game.is_wrong(r, c):                     return (60, 20, 20)
    if game.is_conflict(r, c):                  return BG_CONFLICT
    if game.is_cheat(r, c):                     return (50, 40, 10)
    if val == 0:                                return HEAT_MAP.get(game.heat(r, c), HEAT_DEFAULT)
    return BG_CELL


def cell_fg_color(game, r, c):
    if game.is_clue(r, c):     return FG_CLUE
    if game.is_cheat(r, c):    return FG_CHEAT
    if game.is_conflict(r, c): return FG_CONFLICT
    if game.is_wrong(r, c):    return FG_WRONG
    return FG_USER


# =============================================================================
# MAIN
# =============================================================================

async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Sudoku Calm")
    clock = pygame.time.Clock()

    font_big   = pygame.font.SysFont("monospace", 32, bold=True)
    font_med   = pygame.font.SysFont("monospace", 18, bold=True)
    font_small = pygame.font.SysFont("monospace", 14)
    font_tiny  = pygame.font.SysFont("monospace", 12)

    game       = Game()
    diff_idx   = 0
    selected   = (-1, -1)
    generating = True   # start in generating state to show loading on first open

    message       = ""
    message_col   = WHITE
    message_timer = 0
    loading_dots  = 0
    loading_timer = 0

    half = (SW - BTN_GAP) // 2
    btn_new      = pygame.Rect(SX,                  SB_ROW1_Y, half, BTN_H)
    btn_erase    = pygame.Rect(SX + half + BTN_GAP, SB_ROW1_Y, half, BTN_H)
    btn_undo     = pygame.Rect(SX,                  SB_ROW2_Y, half, BTN_H)
    btn_redo     = pygame.Rect(SX + half + BTN_GAP, SB_ROW2_Y, half, BTN_H)
    btn_validate = pygame.Rect(SX, SB_BTN_VAL_Y, SW, BTN_H)
    btn_solve    = pygame.Rect(SX, SB_BTN_SOL_Y, SW, BTN_H)
    diff_btns    = [
        pygame.Rect(SX, SB_DIFF_Y + i * SB_DIFF_SLOT, SW, BTN_H)
        for i in range(len(DIFFICULTIES))
    ]

    # ------------------------------------------------------------------
    # MAIN LOOP  — matches snake's pattern exactly:
    #   events → update → draw → flip → sleep(0) → tick
    # ------------------------------------------------------------------
    while True:
        mx, my = pygame.mouse.get_pos()

        # Message timer
        if message_timer > 0:
            message_timer -= clock.get_time()
            if message_timer <= 0:
                message = ""

        # Loading dot animation
        if generating:
            loading_timer += clock.get_time()
            if loading_timer >= 400:
                loading_dots  = (loading_dots + 1) % 4
                loading_timer = 0

        # --------------------------------------------------------------
        # INPUT
        # --------------------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if generating:
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                if btn_new.collidepoint(mx, my):
                    generating = True

                elif btn_erase.collidepoint(mx, my):
                    sr, sc = selected
                    if sr != -1:
                        game.clear(sr, sc)

                elif btn_undo.collidepoint(mx, my):
                    if not game.undo():
                        message, message_col = "Nothing to undo.", LIGHT_GRAY
                        message_timer = 1500

                elif btn_redo.collidepoint(mx, my):
                    if not game.redo():
                        message, message_col = "Nothing to redo.", LIGHT_GRAY
                        message_timer = 1500

                elif btn_validate.collidepoint(mx, my):
                    ok = game.validate()
                    if ok:
                        message, message_col = "Perfect! You solved it!", FG_CLUE
                    elif game.has_any_empty():
                        message, message_col = "Board isn't full yet!", FG_CHEAT
                    else:
                        message, message_col = "Some answers are wrong.", FG_WRONG
                    message_timer = 3000

                elif btn_solve.collidepoint(mx, my):
                    game.solve_cheat()
                    message, message_col = "Solved by cheat!", FG_CHEAT
                    message_timer = 3000
                    selected = (-1, -1)

                else:
                    for i, btn in enumerate(diff_btns):
                        if btn.collidepoint(mx, my):
                            diff_idx   = i
                            generating = True
                            break

                gx, gy = mx, my - TOPBAR
                if not generating and 0 <= gx < GRID_PX and 0 <= gy < GRID_PX:
                    selected = (gy // CELL, gx // CELL)

            if event.type == pygame.KEYDOWN:
                ctrl = pygame.key.get_mods() & pygame.KMOD_CTRL
                if ctrl and event.key == pygame.K_z:
                    if not game.undo():
                        message, message_col = "Nothing to undo.", LIGHT_GRAY
                        message_timer = 1500
                elif ctrl and event.key == pygame.K_y:
                    if not game.redo():
                        message, message_col = "Nothing to redo.", LIGHT_GRAY
                        message_timer = 1500
                elif not generating:
                    r, c = selected
                    if r != -1:
                        if event.key in (pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_KP0):
                            game.clear(r, c)
                        else:
                            digit = None
                            if event.unicode in "123456789":
                                digit = int(event.unicode)
                            elif event.key in NUMPAD_KEYS:
                                digit = NUMPAD_KEYS[event.key]
                            if digit is not None:
                                game.place(r, c, digit)
                                if game.is_conflict(r, c):
                                    message, message_col = "Conflict! Check row, col, box.", FG_CONFLICT
                                    message_timer = 2000

                        if event.key in (pygame.K_UP, pygame.K_DOWN,
                                         pygame.K_LEFT, pygame.K_RIGHT):
                            dr = -1 if event.key == pygame.K_UP   else \
                                  1 if event.key == pygame.K_DOWN else 0
                            dc = -1 if event.key == pygame.K_LEFT  else \
                                  1 if event.key == pygame.K_RIGHT else 0
                            selected = (max(0, min(8, r + dr)), max(0, min(8, c + dc)))

        # --------------------------------------------------------------
        # UPDATE / GENERATE
        # --------------------------------------------------------------
        if generating:
            # Draw loading screen, flip, yield to browser, then generate
            screen.fill(BG_DARK)
            draw_text(screen, font_big,   "One moment" + "." * loading_dots,
                      FG_CLUE, SCREEN_W // 2, SCREEN_H // 2 - 20)
            draw_text(screen, font_small, "Generating puzzle...",
                      LIGHT_GRAY, SCREEN_W // 2, SCREEN_H // 2 + 20)
            pygame.display.flip()
            await asyncio.sleep(0)
            clock.tick(30)
            # Generate after yielding so browser doesn't show black screen
            game.load_puzzle(make_puzzle(DIFFICULTIES[diff_idx][1]))
            generating = False
            selected   = (-1, -1)
            continue

        # --------------------------------------------------------------
        # RENDER
        # --------------------------------------------------------------
        screen.fill(BG_DARK)

        # Title bar
        pygame.draw.rect(screen, (28, 28, 28), (0, 0, SCREEN_W, TOPBAR))
        draw_text(screen, font_big, "Sudoku Calm", FG_CLUE, SCREEN_W // 2, TOPBAR // 2)

        sel_r, sel_c = selected
        sel_val      = game.value(sel_r, sel_c) if sel_r != -1 else 0

        # Grid cells
        for r in range(9):
            for c in range(9):
                x = c * CELL
                y = TOPBAR + r * CELL
                pygame.draw.rect(screen,
                                 cell_bg_color(game, r, c, sel_r, sel_c, sel_val, sel_r != -1),
                                 (x, y, CELL, CELL))
                val = game.value(r, c)
                if val:
                    draw_text(screen, font_big, str(val),
                              cell_fg_color(game, r, c),
                              x + CELL // 2, y + CELL // 2)

        # Grid lines
        for i in range(10):
            w   = 3 if i % 3 == 0 else 1
            col = BORDER_OUTER if i % 3 == 0 else BORDER_BOX
            pygame.draw.line(screen, col, (i * CELL, TOPBAR),     (i * CELL, TOPBAR + GRID_PX), w)
            pygame.draw.line(screen, col, (0, TOPBAR + i * CELL), (GRID_PX,  TOPBAR + i * CELL), w)

        if sel_r != -1:
            pygame.draw.rect(screen, BORDER_SEL,
                             (sel_c * CELL, TOPBAR + sel_r * CELL, CELL, CELL), 2)

        # Sidebar
        pygame.draw.rect(screen, BG_SIDEBAR, (GRID_PX, 0, SIDEBAR, SCREEN_H))
        pygame.draw.line(screen, BORDER_OUTER, (GRID_PX, 0), (GRID_PX, SCREEN_H), 2)

        draw_button(screen, font_med, "New", ACCENT_BLUE, btn_new,
                    hover=btn_new.collidepoint(mx, my))
        sel_editable = (sel_r != -1 and
                        not game.is_clue(sel_r, sel_c) and
                        game.value(sel_r, sel_c) != 0)
        draw_button(screen, font_med, "Erase", ACCENT_ORANGE, btn_erase,
                    hover=btn_erase.collidepoint(mx, my) and sel_editable,
                    disabled=not sel_editable)

        draw_button(screen, font_med, "Undo", ACCENT_GRAY, btn_undo,
                    hover=btn_undo.collidepoint(mx, my) and game.can_undo(),
                    disabled=not game.can_undo())
        draw_button(screen, font_med, "Redo", ACCENT_GRAY, btn_redo,
                    hover=btn_redo.collidepoint(mx, my) and game.can_redo(),
                    disabled=not game.can_redo())

        draw_text(screen, font_small, "Difficulty", LIGHT_GRAY,
                  GRID_PX + SIDEBAR // 2, SB_DIFF_LABEL_Y)
        for i, (label, _) in enumerate(DIFFICULTIES):
            btn_col = ACCENT_GREEN if i == diff_idx else (50, 50, 60)
            draw_button(screen, font_med, label, btn_col, diff_btns[i],
                        hover=diff_btns[i].collidepoint(mx, my) and i != diff_idx)

        asst_rect = pygame.Rect(SX, SB_ASST_Y, SW, 60)
        pygame.draw.rect(screen, (30, 30, 40), asst_rect, border_radius=6)
        pygame.draw.rect(screen, BORDER_BOX,   asst_rect, 1, border_radius=6)
        draw_text(screen, font_small, "Available digits", LIGHT_GRAY,
                  GRID_PX + SIDEBAR // 2, SB_ASST_Y + 12)
        if sel_r != -1:
            avail = game.avail(sel_r, sel_c)
            if avail:
                draw_text(screen, font_med, " ".join(avail[:5]), WHITE,
                          GRID_PX + SIDEBAR // 2, SB_ASST_Y + 32)
                if avail[5:]:
                    draw_text(screen, font_med, " ".join(avail[5:]), WHITE,
                              GRID_PX + SIDEBAR // 2, SB_ASST_Y + 50)
            else:
                draw_text(screen, font_small, "No moves here!", FG_WRONG,
                          GRID_PX + SIDEBAR // 2, SB_ASST_Y + 36)
        else:
            draw_text(screen, font_tiny, "Click a cell", GRAY,
                      GRID_PX + SIDEBAR // 2, SB_ASST_Y + 36)

        pygame.draw.line(screen, BORDER_BOX, (SX, SB_SEP_Y), (SX + SW, SB_SEP_Y), 1)

        draw_button(screen, font_med, "Validate",      ACCENT_PURPLE, btn_validate,
                    hover=btn_validate.collidepoint(mx, my))
        draw_button(screen, font_med, "Solve (Cheat)", ACCENT_RED,    btn_solve,
                    hover=btn_solve.collidepoint(mx, my))

        if message:
            msg_rect = pygame.Rect(SX, SB_MSG_Y, SW, 44)
            pygame.draw.rect(screen, (30, 30, 40), msg_rect, border_radius=6)
            words = message.split()
            draw_text(screen, font_small, " ".join(words[:4]), message_col,
                      GRID_PX + SIDEBAR // 2, SB_MSG_Y + 14)
            if words[4:]:
                draw_text(screen, font_small, " ".join(words[4:]), message_col,
                          GRID_PX + SIDEBAR // 2, SB_MSG_Y + 30)

        pygame.display.flip()
        await asyncio.sleep(0)   # required by pygbag
        clock.tick(30)


# =============================================================================
if __name__ == "__main__":
    asyncio.run(main())