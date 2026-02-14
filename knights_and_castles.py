#!/usr/bin/env python3
"""Рыцари и Замки — тактическая пошаговая игра."""

import pygame
import sys
import os
import random

# ========================== КОНСТАНТЫ ==========================
COLS = 10
ROWS = 20
FPS = 30

# Автоматический размер ячейки под экран
pygame.init()
_info = pygame.display.Info()
_max_h = _info.current_h - 60  # запас под панель задач
CELL_SIZE = min(48, _max_h // ROWS)
SIDEBAR_WIDTH = min(280, int(CELL_SIZE * 5.8))
WIDTH = COLS * CELL_SIZE + SIDEBAR_WIDTH
HEIGHT = ROWS * CELL_SIZE

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "Tiny Swords", "Tiny Swords (Free Pack)")

# Цвета
C_BG = (40, 30, 20)
C_GRID = (60, 50, 40)
C_HIGHLIGHT_MOVE = (0, 200, 0, 100)
C_HIGHLIGHT_ATTACK = (200, 0, 0, 100)
C_HIGHLIGHT_SEL = (255, 255, 0, 120)
C_SIDEBAR = (30, 25, 18)
C_TEXT = (220, 210, 190)
C_P1 = (80, 140, 220)
C_P2 = (220, 60, 60)
C_TOWER = (100, 50, 150)
C_RUINS = (80, 80, 60)
C_HP = (0, 200, 0)
C_ARMOR = (100, 100, 255)
C_WHITE = (255, 255, 255)
C_BLACK = (0, 0, 0)
C_GOLD = (255, 215, 0)
C_GRAY = (120, 110, 90)
C_LOCKED = (100, 80, 80)

# ========================== АРТЕФАКТЫ И РЕЦЕПТЫ ==========================

ARTIFACT_NAMES = [
    "Трава серебряных",
    "Палочка заклинаний",
    "Трава С.",
    "Посох огня",
    "Волшебная палочка",
    "Солнечные часы",
    "Вода серебряных трав",
]

ARTIFACT_COLORS = {
    "Трава серебряных":   (180, 220, 180),
    "Палочка заклинаний": (200, 180, 255),
    "Трава С.":           (100, 200, 100),
    "Посох огня":         (255, 120, 50),
    "Волшебная палочка":  (220, 160, 255),
    "Солнечные часы":     (255, 230, 100),
    "Вода серебряных трав":  (100, 180, 255),
}

# Рецепты заклинаний (башня мага)
SPELL_RECIPES = [
    {
        "name": "Дождь защиты",
        "desc": "+2 HP всем своим",
        "recipe": {"Трава серебряных": 2, "Палочка заклинаний": 1, "Трава С.": 1},
    },
    {
        "name": "Сталь свободы",
        "desc": "+2 Armor всем своим",
        "recipe": {"Посох огня": 1, "Трава серебряных": 1, "Волшебная палочка": 1},
    },
    {
        "name": "Небо огня",
        "desc": "Щит на 1 ход противника",
        "recipe": {"Трава С.": 3, "Палочка заклинаний": 1, "Солнечные часы": 1},
    },
]

# Рецепты оружия (крафт из инвентаря)
WEAPON_RECIPES = [
    {
        "name": "Солнечный меч",
        "desc": "Урон +3 (любому юниту)",
        "recipe": {"Посох огня": 1, "Палочка заклинаний": 1, "Солнечные часы": 1},
        "stat": "damage",
        "value": 3,
        "target": "any",
    },
    {
        "name": "Синий лук",
        "desc": "Урон лучника +2",
        "recipe": {"Вода серебряных трав": 1, "Трава С.": 2,
                   "Посох огня": 1, "Палочка заклинаний": 1},
        "stat": "damage",
        "value": 2,
        "target": "archer",
    },
]


def can_craft(inventory, recipe):
    """Проверить, хватает ли артефактов для рецепта."""
    for item, count in recipe.items():
        if inventory.get(item, 0) < count:
            return False
    return True


def spend_recipe(inventory, recipe):
    """Потратить артефакты из инвентаря."""
    for item, count in recipe.items():
        inventory[item] -= count


# ========================== ЗАГРУЗКА СПРАЙТОВ ==========================

def load_sprite(path, size=None):
    full = os.path.join(ASSETS, path)
    if not os.path.exists(full):
        print(f"[ОШИБКА] Файл не найден: {full}")
        return None
    img = pygame.image.load(full).convert_alpha()
    if size:
        img = pygame.transform.smoothscale(img, size)
    return img


def extract_frame(sheet, frame_idx, frame_w, frame_h, target_size):
    if sheet is None:
        return None
    rect = pygame.Rect(frame_idx * frame_w, 0, frame_w, frame_h)
    frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
    frame.blit(sheet, (0, 0), rect)
    return pygame.transform.smoothscale(frame, target_size)


class SpriteManager:
    def __init__(self):
        cs = CELL_SIZE
        self.units = {}
        for color, team in [("Blue", 1), ("Red", 2)]:
            prefix = f"Units/{color} Units"
            w_sheet = load_sprite(f"{prefix}/Warrior/Warrior_Idle.png")
            self.units[(team, "knight")] = extract_frame(w_sheet, 0, 192, 192, (cs, cs))
            a_sheet = load_sprite(f"{prefix}/Archer/Archer_Idle.png")
            self.units[(team, "archer")] = extract_frame(a_sheet, 0, 192, 192, (cs, cs))
            l_sheet = load_sprite(f"{prefix}/Lancer/Lancer_Idle.png")
            self.units[(team, "cavalry")] = extract_frame(l_sheet, 0, 320, 320, (cs, cs))

        self.castle_img = {}
        self.castle_img[1] = load_sprite("Buildings/Blue Buildings/Castle.png",
                                          (cs * 4, cs * 4))
        self.castle_img[2] = load_sprite("Buildings/Red Buildings/Castle.png",
                                          (cs * 4, cs * 4))
        self.tower_img = load_sprite("Buildings/Blue Buildings/Tower.png", (cs, cs))
        self.monastery_img = load_sprite("Buildings/Blue Buildings/Monastery.png",
                                          (cs * 2, cs * 2))

        # Flat checkerboard ground tiles (no 3D trapezoid effect)
        self.ground_tile_a = pygame.Surface((cs, cs))
        self.ground_tile_a.fill((85, 120, 50))
        self.ground_tile_b = pygame.Surface((cs, cs))
        self.ground_tile_b.fill((78, 112, 45))
        self.ground_tile = self.ground_tile_a  # kept for compat

        # Cavalry rendered larger for clarity
        large_cs = int(cs * 1.8)
        self.cavalry_size = large_cs
        for color, team in [("Blue", 1), ("Red", 2)]:
            prefix = f"Units/{color} Units"
            l_sheet = load_sprite(f"{prefix}/Lancer/Lancer_Idle.png")
            self.units[(team, "cavalry")] = extract_frame(l_sheet, 0, 320, 320, (large_cs, large_cs))

    def get_unit(self, player, unit_type):
        return self.units.get((player, unit_type))

    def get_ground(self):
        return self.ground_tile


# ========================== ЮНИТЫ ==========================

class Unit:
    def __init__(self, player, row, col, hp, damage, armor, max_moves, unit_type):
        self.player = player
        self.row = row
        self.col = col
        self.hp = hp
        self.max_hp = hp
        self.damage = damage
        self.armor = armor
        self.max_armor = armor
        self.max_moves = max_moves
        self.moves_left = 0
        self.unit_type = unit_type
        self.active = False
        self.done = False

    def take_damage(self, dmg):
        if self.armor > 0:
            absorbed = min(self.armor, dmg)
            self.armor -= absorbed
            dmg -= absorbed
        self.hp -= dmg
        return self.hp <= 0

    def is_alive(self):
        return self.hp > 0

    def reset_moves(self):
        self.moves_left = self.max_moves
        self.done = False
        self.active = False


class Knight(Unit):
    def __init__(self, player, row, col):
        super().__init__(player, row, col, hp=3, damage=5, armor=4,
                         max_moves=2, unit_type="knight")


class Cavalry(Unit):
    def __init__(self, player, row, col):
        super().__init__(player, row, col, hp=5, damage=6, armor=3,
                         max_moves=3, unit_type="cavalry")


class Archer(Unit):
    def __init__(self, player, row, col):
        super().__init__(player, row, col, hp=3, damage=2, armor=1,
                         max_moves=3, unit_type="archer")


# ========================== ЗАМОК ==========================

class Castle:
    def __init__(self, player, top_row, left_col):
        self.player = player
        self.top_row = top_row
        self.left_col = left_col
        self.cells = set()
        for r in range(top_row, top_row + 4):
            for c in range(left_col, left_col + 4):
                self.cells.add((r, c))

    def contains(self, r, c):
        return (r, c) in self.cells


# ========================== БАШНЯ МАГА ==========================

class MageTower:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.occupant = None

    def contains(self, r, c):
        return r == self.row and c == self.col

    def cast_spell(self, spell_idx, all_units, inventory):
        """Применить заклинание, потратив артефакты."""
        if self.occupant is None:
            return None
        recipe_info = SPELL_RECIPES[spell_idx]
        if not can_craft(inventory, recipe_info["recipe"]):
            return None
        spend_recipe(inventory, recipe_info["recipe"])

        player = self.occupant.player
        name = recipe_info["name"]

        if spell_idx == 0:  # Дождь защиты
            for u in all_units:
                if u.player == player and u.is_alive():
                    u.hp = min(u.hp + 2, u.max_hp + 2)
            return f"{name}: +2 HP"
        elif spell_idx == 1:  # Сталь свободы
            for u in all_units:
                if u.player == player and u.is_alive():
                    u.armor = min(u.armor + 2, u.max_armor + 4)
            return f"{name}: +2 Armor"
        elif spell_idx == 2:  # Небо огня
            return f"{name}: Щит активирован"
        return None


# ========================== РУИНЫ ==========================

class Ruins:
    def __init__(self, top_row, left_col):
        self.top_row = top_row
        self.left_col = left_col
        self.cells = set()
        for r in range(top_row, top_row + 2):
            for c in range(left_col, left_col + 2):
                self.cells.add((r, c))

    def contains(self, r, c):
        return (r, c) in self.cells

    def draw_card(self):
        """Вытянуть артефакт из бесконечной колоды."""
        return random.choice(ARTIFACT_NAMES)


# ========================== ДОСКА ==========================

class Board:
    def __init__(self):
        self.units = []
        self.castle1 = Castle(1, 0, 3)
        self.castle2 = Castle(2, 16, 3)
        self.mage_towers = [
            MageTower(5, 3), MageTower(5, 6),
            MageTower(14, 3), MageTower(14, 6),
        ]
        self.ruins = Ruins(9, 4)

        # P1 (верх)
        self.units.append(Cavalry(1, 3, 4))
        self.units.append(Cavalry(1, 3, 5))
        self.units.append(Knight(1, 1, 3))
        self.units.append(Knight(1, 1, 6))
        self.units.append(Knight(1, 2, 3))
        self.units.append(Knight(1, 2, 6))
        self.units.append(Knight(1, 0, 3))
        self.units.append(Archer(1, 0, 4))
        self.units.append(Archer(1, 0, 5))
        self.units.append(Knight(1, 0, 6))

        # P2 (низ, та же ориентация что и у P1)
        self.units.append(Cavalry(2, 16, 4))
        self.units.append(Cavalry(2, 16, 5))
        self.units.append(Knight(2, 17, 3))
        self.units.append(Knight(2, 17, 6))
        self.units.append(Knight(2, 18, 3))
        self.units.append(Knight(2, 18, 6))
        self.units.append(Knight(2, 19, 3))
        self.units.append(Archer(2, 19, 4))
        self.units.append(Archer(2, 19, 5))
        self.units.append(Knight(2, 19, 6))

    def unit_at(self, r, c):
        for u in self.units:
            if u.is_alive() and u.row == r and u.col == c:
                return u
        return None

    def is_free(self, r, c):
        if r < 0 or r >= ROWS or c < 0 or c >= COLS:
            return False
        return self.unit_at(r, c) is None

    def remove_dead(self):
        self.units = [u for u in self.units if u.is_alive()]

    def player_units(self, player):
        return [u for u in self.units if u.player == player and u.is_alive()]

    def is_in_mage_tower(self, r, c):
        for mt in self.mage_towers:
            if mt.contains(r, c):
                return mt
        return None

    def is_in_ruins(self, r, c):
        return self.ruins.contains(r, c)


# ========================== МЕНЮ ==========================

class MenuScreen:
    """Предигровой экран: обложка + правила + выбор режима."""

    RULES_PLACEHOLDER = [
        "ПРАВИЛА ИГРЫ",
        "",
        "Цель: уничтожить все юниты противника.",
        "",
        "ЮНИТЫ:",
        "  Рыцарь    — HP 3  | Урон 5 | Броня 4 | Ходы 2",
        "  Кон. рыцарь — HP 5  | Урон 6 | Броня 3 | Ходы 3",
        "  Лучник    — HP 3  | Урон 2 | Броня 1 | Ходы 3",
        "",
        "ХОД:",
        "  Каждый ход вы активируете до 3 юнитов.",
        "  ЛКМ — выбрать юнит, затем кликнуть клетку.",
        "  ПКМ / Space — пропустить юнит.",
        "",
        "АТАКА:",
        "  Рыцарь/Конный — прыжковая атака (2 хода).",
        "  Лучник — стреляет в соседнюю клетку (1 ход).",
        "  Броня поглощает часть урона.",
        "",
        "БАШНЯ МАГА:",
        "  Зайди юнитом в башню.",
        "  При наличии артефактов — можно применить заклинание.",
        "  Дождь защиты: +2 HP всем своим.",
        "  Сталь свободы: +2 Броня всем своим.",
        "  Небо огня: щит на 1 ход противника (-2 к урону).",
        "",
        "РУИНЫ (центр поля):",
        "  Зайди юнитом в руины → кнопка 'Тянуть артефакт'.",
        "  Артефакты нужны для заклинаний и крафта оружия.",
        "",
        "КРАФТ ОРУЖИЯ:",
        "  Солнечный меч (+3 урон, любому юниту).",
        "  Синий лук (+2 урон, только лучнику).",
        "",
        "ПОБЕДА:",
        "  Игрок победивший уничтоживший всех юнитов врага — побеждает.",
        "",
        "",
        "  (Дополнительные правила будут добавлены позже)",
        "",
    ]

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.font       = pygame.font.SysFont("Arial", 14)
        self.font_big   = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_title = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 12)

        # Обложка
        cover_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "Knights_and_Castles_1920x1080.png")
        if os.path.exists(cover_path):
            raw = pygame.image.load(cover_path).convert()
            self.cover = pygame.transform.smoothscale(raw, (WIDTH, HEIGHT))
        else:
            self.cover = None

        # Контент правил в пикселях
        self.rule_line_h = 20
        self.rules_top   = HEIGHT        # правила начинаются ниже обложки
        self.rules_h     = len(self.RULES_PLACEHOLDER) * self.rule_line_h + 40
        self.total_h     = self.rules_top + self.rules_h + 100  # +100 запас

        self.scroll_y   = 0             # текущий скролл (в пикселях)
        self.max_scroll  = max(0, self.total_h - HEIGHT + 80)  # 80 под кнопки

        # Кнопки (фиксированы внизу экрана)
        self.btn_h = 50
        self.btn_w = (WIDTH - 60) // 2
        self.btn1_rect = pygame.Rect(20,          HEIGHT - self.btn_h - 10, self.btn_w, self.btn_h)
        self.btn2_rect = pygame.Rect(WIDTH // 2 + 10, HEIGHT - self.btn_h - 10, self.btn_w, self.btn_h)

    def run(self):
        """Главный цикл меню. Возвращает '2p' или 'ai'."""
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mode = self._handle_click(*event.pos)
                        if mode:
                            return mode
                    elif event.button == 4:   # колёсико вверх
                        self.scroll_y = max(0, self.scroll_y - 40)
                    elif event.button == 5:   # колёсико вниз
                        self.scroll_y = min(self.max_scroll, self.scroll_y + 40)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.scroll_y = min(self.max_scroll, self.scroll_y + 40)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self.scroll_y = max(0, self.scroll_y - 40)
            self._draw()

    def _handle_click(self, mx, my):
        if self.btn1_rect.collidepoint(mx, my):
            return "2p"
        if self.btn2_rect.collidepoint(mx, my):
            return "ai"
        return None

    def _draw(self):
        self.screen.fill((20, 15, 10))
        sy = self.scroll_y

        # --- Обложка (первый экран) ---
        if self.cover:
            self.screen.blit(self.cover, (0, -sy))
        else:
            # Заглушка если файл не найден
            pygame.draw.rect(self.screen, (60, 40, 20), (0, -sy, WIDTH, HEIGHT))
            t = self.font_title.render("Рыцари и Замки", True, (255, 215, 0))
            self.screen.blit(t, ((WIDTH - t.get_width()) // 2, HEIGHT // 2 - sy - 20))

        # Затемнение в нижней части обложки (переход к правилам)
        if sy < HEIGHT:
            fade_start = max(0, HEIGHT - sy - 120)
            fade_h = min(120, HEIGHT - fade_start)
            fade = pygame.Surface((WIDTH, fade_h), pygame.SRCALPHA)
            for i in range(fade_h):
                alpha = int(255 * i / fade_h)
                pygame.draw.line(fade, (20, 15, 10, alpha), (0, i), (WIDTH, i))
            self.screen.blit(fade, (0, fade_start))

        # --- Правила (ниже обложки) ---
        rules_screen_y = self.rules_top - sy
        if rules_screen_y < HEIGHT:
            # Фон правил
            rules_rect_y = max(0, rules_screen_y)
            pygame.draw.rect(self.screen, (25, 18, 12),
                             (0, rules_rect_y, WIDTH, HEIGHT - rules_rect_y))

            x0 = 40
            y0 = rules_screen_y + 20
            for line in self.RULES_PLACEHOLDER:
                if y0 > HEIGHT:
                    break
                if y0 < -self.rule_line_h:
                    y0 += self.rule_line_h
                    continue
                if line == "ПРАВИЛА ИГРЫ":
                    t = self.font_title.render(line, True, (255, 215, 0))
                    self.screen.blit(t, ((WIDTH - t.get_width()) // 2, y0))
                elif line.isupper() and line:
                    t = self.font_big.render(line, True, (200, 170, 100))
                    self.screen.blit(t, (x0, y0))
                elif line:
                    t = self.font.render(line, True, (200, 190, 170))
                    self.screen.blit(t, (x0, y0))
                y0 += self.rule_line_h

        # --- Кнопки (фиксированы внизу) ---
        btn_bg = (30, 22, 12)
        # Кнопка «2 Игрока»
        pygame.draw.rect(self.screen, btn_bg, self.btn1_rect, border_radius=8)
        pygame.draw.rect(self.screen, (80, 140, 220), self.btn1_rect, 3, border_radius=8)
        t1 = self.font_big.render("⚔ 2 Игрока", True, (80, 160, 255))
        self.screen.blit(t1, (self.btn1_rect.centerx - t1.get_width() // 2,
                               self.btn1_rect.centery - t1.get_height() // 2))
        # Кнопка «Против ИИ»
        pygame.draw.rect(self.screen, btn_bg, self.btn2_rect, border_radius=8)
        pygame.draw.rect(self.screen, (200, 60, 60), self.btn2_rect, 3, border_radius=8)
        t2 = self.font_big.render("🤖 Против ИИ", True, (255, 80, 80))
        self.screen.blit(t2, (self.btn2_rect.centerx - t2.get_width() // 2,
                               self.btn2_rect.centery - t2.get_height() // 2))

        # Подсказка скролла
        hint = self.font_small.render("↑↓ / колёсико мыши — прокрутка правил", True, (100, 90, 70))
        self.screen.blit(hint, ((WIDTH - hint.get_width()) // 2, HEIGHT - self.btn_h - 28))

        pygame.display.flip()


# ========================== ИИ-ПРОТИВНИК ==========================

class AIPlayer:
    """Тактический ИИ для Игрока 2. Использует эвристическую оценку ходов."""

    DELAY_FRAMES = 18  # задержка между действиями (для визуальности)

    def __init__(self, game):
        self.game = game
        self.player = 2
        self._action_queue = []   # [(func, args), ...]
        self._delay = 0

    # ---------- Публичный интерфейс ----------

    def start_turn(self):
        """Планируем все ходы AI на этот ход и складываем в очередь."""
        self._action_queue = []
        g = self.game
        alive = g.board.player_units(self.player)
        max_act = min(g.max_units_per_turn, len(alive))
        units_to_act = [u for u in alive if not u.done][:max_act]
        for unit in units_to_act:
            self._plan_unit(unit)
        # Финальное: завершить ход
        self._action_queue.append((g.end_turn, ()))

    def step(self):
        """Вызывается каждый кадр во время хода AI. Выполняет одно действие с задержкой."""
        if not self._action_queue:
            return
        self._delay -= 1
        if self._delay > 0:
            return
        fn, args = self._action_queue.pop(0)
        fn(*args)
        self._delay = self.DELAY_FRAMES

    def is_done(self):
        return len(self._action_queue) == 0

    # ---------- Планирование хода юнита ----------

    def _plan_unit(self, unit):
        """Планируем действия одного юнита — добавляем в очередь."""
        g = self.game
        # Выбираем юнит
        self._action_queue.append((self._select, (unit,)))

        # Ищем лучшее действие для каждого очка хода
        actions = self._best_actions(unit)
        for fn, args in actions:
            self._action_queue.append((fn, args))

        # Пропускаем (заканчиваем ход юнита)
        self._action_queue.append((g.next_unit, ()))

    def _select(self, unit):
        g = self.game
        g.selected_unit = unit
        unit.active = True
        unit.moves_left = unit.max_moves
        g.state = "move"
        g.calc_moves(unit)

    # ---------- Оценочная функция ----------

    def _dist(self, r1, c1, r2, c2):
        return abs(r1 - r2) + abs(c1 - c2)

    def _nearest_enemy(self, unit):
        g = self.game
        enemies = g.board.player_units(1)
        if not enemies:
            return None, 9999
        nearest = min(enemies, key=lambda e: self._dist(unit.row, unit.col, e.row, e.col))
        return nearest, self._dist(unit.row, unit.col, nearest.row, nearest.col)

    def _score_move(self, unit, nr, nc, is_attack=False, attack_target=None):
        """Оценить конкретный ход/атаку — возвращает числовой счёт."""
        score = 0
        g = self.game

        if is_attack and attack_target:
            # Сколько урона нанесём
            dmg = unit.damage
            if g.fire_shield.get(1, False):
                dmg = max(0, dmg - 2)
            effective_dmg = max(0, dmg - max(0, attack_target.armor))
            # Убиваем — огромный бонус
            if attack_target.hp - effective_dmg <= 0:
                score += 10000
            else:
                score += 100 * effective_dmg
            # Добиваем слабого врага
            if attack_target.hp <= unit.damage:
                score += 500
            return score

        # Движение — оцениваем позицию
        enemy, dist_before = self._nearest_enemy(unit)
        if enemy:
            dist_after = self._dist(nr, nc, enemy.row, enemy.col)
            if dist_after < dist_before:
                score += 20 * (dist_before - dist_after)

        # Руины — тянуть артефакты выгодно
        if g.board.is_in_ruins(nr, nc):
            score += 50

        # Башня мага — полезно если есть ингредиенты
        mt = g.board.is_in_mage_tower(nr, nc)
        if mt:
            inv = g.inventory[self.player]
            for sp in SPELL_RECIPES:
                if can_craft(inv, sp["recipe"]):
                    score += 200
                    break
            else:
                score += 5

        # Кавалерия агрессивнее
        if unit.unit_type == "cavalry" and enemy:
            dist_after = self._dist(nr, nc, enemy.row, enemy.col)
            score += max(0, 10 - dist_after) * 3

        # Лучник предпочитает держать дистанцию
        if unit.unit_type == "archer" and enemy:
            dist_after = self._dist(nr, nc, enemy.row, enemy.col)
            if dist_after >= 2:
                score += 10

        return score

    def _best_actions(self, unit):
        """Возвращает список (fn, args) — лучшие действия для юнита."""
        g = self.game
        result = []
        g.calc_moves(unit)

        # Спецдействия: руины
        if g.board.is_in_ruins(unit.row, unit.col) and unit.moves_left > 0:
            result.append((g.try_draw_card, ()))
            return result

        # Спецдействия: башня мага
        mt = g.board.is_in_mage_tower(unit.row, unit.col)
        if mt:
            mt.occupant = unit
            inv = g.inventory[self.player]
            for i, sp in enumerate(SPELL_RECIPES):
                if can_craft(inv, sp["recipe"]):
                    idx = i
                    result.append((g.try_cast_spell, (idx,)))
                    return result

        # Крафт оружия если выгодно
        inv = g.inventory[self.player]
        for i, wp in enumerate(WEAPON_RECIPES):
            if can_craft(inv, wp["recipe"]):
                if wp["target"] == "any" or wp["target"] == unit.unit_type:
                    result.append((g.try_craft_weapon, (i,)))

        # Атака — ищем лучшую
        best_atk_score = -1
        best_atk_pos = None
        for (ar, ac), target in g.jump_targets.items():
            sc = self._score_move(unit, ar, ac, is_attack=True, attack_target=target)
            if sc > best_atk_score:
                best_atk_score = sc
                best_atk_pos = (ar, ac)

        # Лучник — стрельба
        if unit.unit_type == "archer":
            for (ar, ac) in g.attack_highlights:
                target = g.board.unit_at(ar, ac)
                if target and target.player != self.player:
                    sc = self._score_move(unit, ar, ac, is_attack=True, attack_target=target)
                    if sc > best_atk_score:
                        best_atk_score = sc
                        best_atk_pos = (ar, ac)

        # Движение — ищем лучшее
        best_mv_score = -1
        best_mv_pos = None
        for (mr, mc) in g.move_highlights:
            sc = self._score_move(unit, mr, mc)
            if sc > best_mv_score:
                best_mv_score = sc
                best_mv_pos = (mr, mc)

        # Выбираем: атака или движение
        if best_atk_pos and best_atk_score >= best_mv_score:
            r, c = best_atk_pos
            if unit.unit_type == "archer":
                result.append((g.do_archer_shoot, (r, c)))
            else:
                result.append((g.do_jump_attack, (r, c)))
        elif best_mv_pos:
            result.append((g.move_unit, (best_mv_pos[0], best_mv_pos[1])))
            # После движения — проверим атаку снова (рекурсивно не идём, просто добавляем)
            # Планировщик добавит next_unit после

        return result


# ========================== ИГРА ==========================

class Game:
    def __init__(self, ai_mode=False, screen=None, clock=None):
        if screen is None:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption("Рыцари и Замки")
        else:
            self.screen = screen
        self.clock = clock if clock else pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 13)
        self.font_big = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_title = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 11)

        self.sprites = SpriteManager()
        self.board = Board()

        # Инвентари артефактов для каждого игрока
        self.inventory = {
            1: {name: 0 for name in ARTIFACT_NAMES},
            2: {name: 0 for name in ARTIFACT_NAMES},
        }

        self.current_player = 1
        self.units_acted = 0
        self.max_units_per_turn = 3
        self.selected_unit = None
        self.move_highlights = []
        self.attack_highlights = []
        self.jump_targets = {}
        self.move_costs = {}
        self.jump_costs = {}

        self.state = "select"
        self.message = "Ход Игрока 1: выберите юнит"
        self.popup_text = None
        self.popup_timer = 0
        self.fire_shield = {1: False, 2: False}
        self.winner = None

        # Скролл сайдбара
        self.sidebar_scroll = 0

        # Предпросмотр фигурки
        self.preview_unit = None

        # AI режим
        self.ai_mode = ai_mode
        self.ai_player = AIPlayer(self) if ai_mode else None
        self._ai_thinking = False  # True когда AI планирует ход

        self.start_turn()

    # -------------------- Ходы --------------------

    def start_turn(self):
        self.units_acted = 0
        self.selected_unit = None
        self.state = "select"
        for u in self.board.player_units(self.current_player):
            u.reset_moves()
        self.update_message()
        # Если ход AI — запускаем планирование
        if self.ai_mode and self.current_player == 2 and self.ai_player:
            self.ai_player.start_turn()
            self._ai_thinking = True

    def end_turn(self):
        enemy = 2 if self.current_player == 1 else 1
        if self.fire_shield[self.current_player]:
            self.fire_shield[self.current_player] = False
        self.current_player = enemy
        self.start_turn()
        self.check_win()

    def next_unit(self):
        if self.selected_unit:
            self.selected_unit.done = True
            self.selected_unit.active = False
        self.units_acted += 1
        self.selected_unit = None
        self.move_highlights = []
        self.attack_highlights = []
        self.jump_targets = {}
        self.move_costs = {}
        self.jump_costs = {}
        alive = self.board.player_units(self.current_player)
        max_can = min(self.max_units_per_turn, len(alive))
        if self.units_acted >= max_can:
            self.end_turn()
        else:
            self.state = "select"
            self.update_message()

    def update_message(self):
        p = self.current_player
        left = min(self.max_units_per_turn, len(self.board.player_units(p))) - self.units_acted
        self.message = f"Игрок {p}: выберите юнит ({left} ост.)"

    def show_popup(self, text):
        self.popup_text = text
        self.popup_timer = FPS * 2

    # -------------------- Вычисление ходов --------------------

    def calc_moves(self, unit):
        self.move_highlights = []
        self.attack_highlights = []
        self.jump_targets = {}
        self.move_costs = {}
        self.jump_costs = {}
        if unit.moves_left <= 0:
            return
        if unit.unit_type == "archer":
            self._calc_archer_moves(unit)
        else:
            self._calc_melee_moves(unit)

    def _calc_melee_moves(self, unit):
        r, c = unit.row, unit.col
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                target = self.board.unit_at(nr, nc)
                if target is None:
                    self.move_highlights.append((nr, nc))
                    self.move_costs[(nr, nc)] = 1
                elif target.player != unit.player:
                    land_r, land_c = nr + dr, nc + dc
                    if unit.moves_left >= 2 and self.board.is_free(land_r, land_c):
                        self.attack_highlights.append((land_r, land_c))
                        self.jump_targets[(land_r, land_c)] = target
                        self.jump_costs[(land_r, land_c)] = 2

    def _calc_archer_moves(self, unit):
        r, c = unit.row, unit.col
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for dist in range(1, 3):
                if unit.moves_left < dist:
                    break
                nr, nc = r + dr * dist, c + dc * dist
                if not self.board.is_free(nr, nc):
                    break
                self.move_highlights.append((nr, nc))
                self.move_costs[(nr, nc)] = dist
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                target = self.board.unit_at(nr, nc)
                if target and target.player != unit.player:
                    self.attack_highlights.append((nr, nc))

    # -------------------- Действия --------------------

    def select_unit(self, r, c):
        unit = self.board.unit_at(r, c)
        if unit and unit.player == self.current_player and not unit.done:
            self.selected_unit = unit
            unit.active = True
            unit.moves_left = unit.max_moves
            self.state = "move"
            self.calc_moves(unit)
            mt = self.board.is_in_mage_tower(r, c)
            if mt:
                mt.occupant = unit
            return True
        return False

    def move_unit(self, r, c):
        if (r, c) not in self.move_highlights:
            return False
        unit = self.selected_unit
        cost = self.move_costs.get((r, c), 1)
        if unit.moves_left < cost:
            return False
        unit.row = r
        unit.col = c
        unit.moves_left -= cost
        mt = self.board.is_in_mage_tower(r, c)
        if mt:
            mt.occupant = unit
        if unit.moves_left <= 0:
            self.next_unit()
        else:
            self.calc_moves(unit)
        return True

    def do_jump_attack(self, r, c):
        if (r, c) not in self.attack_highlights:
            return False
        unit = self.selected_unit
        target = self.jump_targets.get((r, c))
        if target is None:
            return self.do_archer_shoot(r, c)
        cost = self.jump_costs.get((r, c), 1)
        if unit.moves_left < cost:
            return False
        unit.row = r
        unit.col = c
        unit.moves_left -= cost
        dmg = unit.damage
        if self.fire_shield.get(target.player, False):
            dmg = max(0, dmg - 2)
        target.take_damage(dmg)
        self.board.remove_dead()
        self.check_win()
        if unit.moves_left <= 0:
            self.next_unit()
        else:
            self.calc_moves(unit)
        return True

    def do_archer_shoot(self, r, c):
        unit = self.selected_unit
        target = self.board.unit_at(r, c)
        if target is None or target.player == unit.player:
            return False
        unit.moves_left -= 1
        dmg = unit.damage
        if self.fire_shield.get(target.player, False):
            dmg = max(0, dmg - 2)
        target.take_damage(dmg)
        self.board.remove_dead()
        self.check_win()
        if unit.moves_left <= 0:
            self.next_unit()
        else:
            self.calc_moves(unit)
        return True

    def try_draw_card(self):
        """Тянуть артефакт из руин."""
        unit = self.selected_unit
        if unit and self.board.is_in_ruins(unit.row, unit.col) and unit.moves_left > 0:
            artifact = self.board.ruins.draw_card()
            self.inventory[unit.player][artifact] += 1
            unit.moves_left -= 1
            self.show_popup(f"Найден: {artifact}")
            if unit.moves_left <= 0:
                self.next_unit()
            else:
                self.calc_moves(unit)
            return True
        return False

    def try_cast_spell(self, spell_idx):
        """Применить заклинание из башни, тратя артефакты."""
        unit = self.selected_unit
        if unit is None or unit.moves_left <= 0:
            return False
        mt = self.board.is_in_mage_tower(unit.row, unit.col)
        if mt is None or mt.occupant != unit:
            return False

        inv = self.inventory[unit.player]
        recipe_info = SPELL_RECIPES[spell_idx]
        if not can_craft(inv, recipe_info["recipe"]):
            self.show_popup("Не хватает артефактов!")
            return False

        result = mt.cast_spell(spell_idx, self.board.units, inv)
        if spell_idx == 2:
            self.fire_shield[unit.player] = True

        unit.moves_left -= 1
        self.show_popup(result or "Заклинание применено")

        if unit.moves_left <= 0:
            self.next_unit()
        else:
            self.calc_moves(unit)
        return True

    def try_craft_weapon(self, weapon_idx):
        """Скрафтить оружие, применить к выбранному юниту."""
        unit = self.selected_unit
        if unit is None:
            return False
        inv = self.inventory[unit.player]
        w = WEAPON_RECIPES[weapon_idx]
        if not can_craft(inv, w["recipe"]):
            self.show_popup("Не хватает артефактов!")
            return False
        # Проверка целевого типа
        if w["target"] == "archer" and unit.unit_type != "archer":
            self.show_popup("Только для лучника!")
            return False

        spend_recipe(inv, w["recipe"])
        if w["stat"] == "damage":
            unit.damage += w["value"]
        self.show_popup(f"{w['name']}: +{w['value']} урон")
        return True

    def check_win(self):
        if len(self.board.player_units(1)) == 0:
            self.winner = 2
            self.state = "game_over"
            self.message = "ПОБЕДА ИГРОКА 2!"
        elif len(self.board.player_units(2)) == 0:
            self.winner = 1
            self.state = "game_over"
            self.message = "ПОБЕДА ИГРОКА 1!"

    def skip_unit(self):
        if self.selected_unit:
            self.next_unit()

    # -------------------- Клики --------------------

    def handle_click(self, mx, my):
        if self.state == "game_over":
            return
        if mx >= COLS * CELL_SIZE:
            self.handle_sidebar_click(mx, my)
            return

        # Закрыть превью кликом вне юнита
        col = mx // CELL_SIZE
        row = my // CELL_SIZE
        clicked_unit = self.board.unit_at(row, col)
        if self.preview_unit is not None:
            if clicked_unit == self.preview_unit:
                self.preview_unit = None
                return
            else:
                self.preview_unit = None

        # Открыть превью при клике на любую фигурку (и сохранить обычный выбор)
        if clicked_unit:
            self.preview_unit = clicked_unit

        if self.state == "select":
            self.select_unit(row, col)
        elif self.state == "move":
            if (row, col) in self.attack_highlights:
                if self.selected_unit.unit_type == "archer":
                    target = self.board.unit_at(row, col)
                    if target and target.player != self.selected_unit.player:
                        self.do_archer_shoot(row, col)
                    else:
                        self.do_jump_attack(row, col)
                else:
                    self.do_jump_attack(row, col)
            elif (row, col) in self.move_highlights:
                self.move_unit(row, col)
            elif self.board.unit_at(row, col) and \
                 self.board.unit_at(row, col).player == self.current_player and \
                 not self.board.unit_at(row, col).done:
                if self.selected_unit and \
                   self.selected_unit.moves_left == self.selected_unit.max_moves:
                    self.selected_unit.active = False
                    self.select_unit(row, col)
            elif self.selected_unit and \
                 self.selected_unit.moves_left == self.selected_unit.max_moves:
                self.selected_unit.active = False
                self.selected_unit = None
                self.move_highlights = []
                self.attack_highlights = []
                self.jump_targets = {}
                self.move_costs = {}
                self.jump_costs = {}
                self.state = "select"

    def handle_sidebar_click(self, mx, my):
        for bx, by, bw, bh, action in getattr(self, '_sidebar_buttons', []):
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                action()
                return

    # -------------------- РЕНДЕРИНГ --------------------

    def draw(self):
        self.screen.fill(C_BG)
        self.draw_ground()
        self.draw_structures()
        self.draw_highlights()
        self.draw_units()
        self.draw_grid()
        self.draw_sidebar()
        self.draw_unit_preview_popup()
        self.draw_popup()
        if self.state == "game_over":
            self.draw_game_over()
        pygame.display.flip()

    def draw_ground(self):
        for r in range(ROWS):
            for c in range(COLS):
                x, y = c * CELL_SIZE, r * CELL_SIZE
                tile = self.sprites.ground_tile_a if (r + c) % 2 == 0 else self.sprites.ground_tile_b
                self.screen.blit(tile, (x, y))

    def draw_structures(self):
        c1 = self.board.castle1
        cx, cy = c1.left_col * CELL_SIZE, c1.top_row * CELL_SIZE
        img1 = self.sprites.castle_img.get(1)
        if img1:
            self.screen.blit(img1, (cx, cy))
        else:
            pygame.draw.rect(self.screen, C_P1,
                             (cx, cy, 4 * CELL_SIZE, 4 * CELL_SIZE), 3)

        c2 = self.board.castle2
        cx2, cy2 = c2.left_col * CELL_SIZE, c2.top_row * CELL_SIZE
        img2 = self.sprites.castle_img.get(2)
        if img2:
            self.screen.blit(img2, (cx2, cy2))
        else:
            pygame.draw.rect(self.screen, C_P2,
                             (cx2, cy2, 4 * CELL_SIZE, 4 * CELL_SIZE), 3)

        for mt in self.board.mage_towers:
            tx, ty = mt.col * CELL_SIZE, mt.row * CELL_SIZE
            if self.sprites.tower_img:
                self.screen.blit(self.sprites.tower_img, (tx, ty))
            else:
                pygame.draw.rect(self.screen, C_TOWER,
                                 (tx, ty, CELL_SIZE, CELL_SIZE))
                t = self.font.render("M", True, C_WHITE)
                self.screen.blit(t, (tx + 16, ty + 16))

        ruins = self.board.ruins
        rx, ry = ruins.left_col * CELL_SIZE, ruins.top_row * CELL_SIZE
        self._draw_ruins(rx, ry)

    def _draw_ruins(self, rx, ry):
        """Рисует руины программно: разрушенные стены, обломки, мох."""
        cs = CELL_SIZE
        w, h = cs * 2, cs * 2
        # Тёмная каменная основа
        pygame.draw.rect(self.screen, (62, 57, 47), (rx, ry, w, h))
        # Левый сломанный столб
        pygame.draw.rect(self.screen, (105, 95, 80), (rx + 4, ry + 6, 10, h - 14))
        pygame.draw.polygon(self.screen, (80, 72, 60), [
            (rx + 4, ry + 6), (rx + 14, ry + 6),
            (rx + 11, ry + 1), (rx + 7, ry + 3)])
        # Правый сломанный столб (короче)
        pygame.draw.rect(self.screen, (105, 95, 80), (rx + 22, ry + 14, 9, h - 22))
        pygame.draw.polygon(self.screen, (80, 72, 60), [
            (rx + 22, ry + 14), (rx + 31, ry + 14),
            (rx + 28, ry + 10), (rx + 25, ry + 12)])
        # Частичная стена (горизонтальный сегмент)
        pygame.draw.rect(self.screen, (95, 87, 72), (rx + 4, ry + cs - 4, cs - 8, 6))
        # Обломки и камни (случайные, но фиксированные позиции)
        rubble = [
            (rx + 18, ry + cs + 8,  14, 6),
            (rx + 36, ry + cs + 2,  10, 5),
            (rx + cs + 6, ry + 10,  12, 5),
            (rx + cs + 18, ry + cs - 2, 16, 6),
            (rx + cs + 4, ry + cs + 12, 10, 4),
            (rx + 8,  ry + cs + 20, 18, 5),
            (rx + cs - 4, ry + cs + 18, 12, 5),
        ]
        for bx, by, bw, bh in rubble:
            pygame.draw.ellipse(self.screen, (92, 84, 68), (bx, by, bw, bh))
            pygame.draw.ellipse(self.screen, (68, 62, 52), (bx + 1, by + 1, bw - 2, bh - 2), 1)
        # Мох
        moss = [(rx + 16, ry + cs + 16, 8, 4),
                (rx + cs + 10, ry + cs + 8, 10, 4)]
        for mx_, my_, mw, mh in moss:
            pygame.draw.ellipse(self.screen, (55, 88, 42), (mx_, my_, mw, mh))
        # Подпись
        t = self.font_small.render("Руины", True, (160, 150, 120))
        self.screen.blit(t, (rx + 4, ry + h - 14))

    def draw_highlights(self):
        if self.state != "move":
            return
        if self.selected_unit:
            sx = self.selected_unit.col * CELL_SIZE
            sy = self.selected_unit.row * CELL_SIZE
            s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            s.fill(C_HIGHLIGHT_SEL)
            self.screen.blit(s, (sx, sy))
        for (r, c) in self.move_highlights:
            x, y = c * CELL_SIZE, r * CELL_SIZE
            s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            s.fill(C_HIGHLIGHT_MOVE)
            self.screen.blit(s, (x, y))
        for (r, c) in self.attack_highlights:
            x, y = c * CELL_SIZE, r * CELL_SIZE
            s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            s.fill(C_HIGHLIGHT_ATTACK)
            self.screen.blit(s, (x, y))

    def draw_units(self):
        cs = CELL_SIZE
        for u in self.board.units:
            if not u.is_alive():
                continue
            x = u.col * cs
            y = u.row * cs
            sprite = self.sprites.get_unit(u.player, u.unit_type)

            if u.unit_type == "cavalry":
                # Кавалерия — крупный спрайт, центрирован на клетке
                large = self.sprites.cavalry_size
                off = (large - cs) // 2
                draw_x = x - off
                draw_y = y - off
                if sprite:
                    self.screen.blit(sprite, (draw_x, draw_y))
                else:
                    color = C_P1 if u.player == 1 else C_P2
                    pygame.draw.rect(self.screen, color,
                                     (draw_x + 4, draw_y + 4, large - 8, large - 8))
                    t = self.font.render("C", True, C_WHITE)
                    self.screen.blit(t, (x + cs // 3, y + cs // 3))
                # Бронзовая рамка для кавалерии
                border_col = (200, 160, 50) if u.player == 1 else (200, 80, 50)
                pygame.draw.rect(self.screen, border_col, (x, y, cs, cs), 2)
            else:
                if sprite:
                    self.screen.blit(sprite, (x, y))
                else:
                    color = C_P1 if u.player == 1 else C_P2
                    pygame.draw.rect(self.screen, color,
                                     (x + 4, y + 4, cs - 8, cs - 8))
                    t = self.font.render(u.unit_type[0].upper(), True, C_WHITE)
                    self.screen.blit(t, (x + 16, y + 14))

            # HP/Armor бары
            bw = cs - 4
            bx = x + 2
            by_hp = y + cs - 10
            mhp = max(u.max_hp, u.hp, 1)
            pygame.draw.rect(self.screen, C_BLACK, (bx, by_hp, bw, 4))
            pygame.draw.rect(self.screen, C_HP,
                             (bx, by_hp, max(0, int(bw * u.hp / mhp)), 4))
            by_ar = by_hp - 5
            mar = max(u.max_armor, u.armor, 1)
            pygame.draw.rect(self.screen, C_BLACK, (bx, by_ar, bw, 4))
            pygame.draw.rect(self.screen, C_ARMOR,
                             (bx, by_ar, max(0, int(bw * u.armor / mar)), 4))
            if u.active:
                pygame.draw.rect(self.screen, C_GOLD, (x, y, cs, cs), 2)
            if u.done:
                s = pygame.Surface((cs, cs), pygame.SRCALPHA)
                s.fill((0, 0, 0, 60))
                self.screen.blit(s, (x, y))

    def draw_grid(self):
        for r in range(ROWS + 1):
            pygame.draw.line(self.screen, C_GRID,
                             (0, r * CELL_SIZE), (COLS * CELL_SIZE, r * CELL_SIZE))
        for c in range(COLS + 1):
            pygame.draw.line(self.screen, C_GRID,
                             (c * CELL_SIZE, 0), (c * CELL_SIZE, ROWS * CELL_SIZE))

    def draw_sidebar(self):
        sx = COLS * CELL_SIZE
        pygame.draw.rect(self.screen, C_SIDEBAR, (sx, 0, SIDEBAR_WIDTH, HEIGHT))
        pygame.draw.line(self.screen, C_GRID, (sx, 0), (sx, HEIGHT), 2)

        self._sidebar_buttons = []
        y = 8
        pad = sx + 8
        w = SIDEBAR_WIDTH - 16

        # === Заголовок ===
        color = C_P1 if self.current_player == 1 else C_P2
        t = self.font_title.render(f"Игрок {self.current_player}", True, color)
        self.screen.blit(t, (pad, y))
        y += 28

        # === Сообщение ===
        t = self.font.render(self.message, True, C_TEXT)
        self.screen.blit(t, (pad, y))
        y += 18

        # === Счёт ===
        p1c = len(self.board.player_units(1))
        p2c = len(self.board.player_units(2))
        t = self.font.render(f"P1: {p1c} | P2: {p2c}", True, C_TEXT)
        self.screen.blit(t, (pad, y))
        y += 18

        # Щиты
        for p in [1, 2]:
            if self.fire_shield[p]:
                t = self.font.render(f"Щит P{p} активен", True, C_GOLD)
                self.screen.blit(t, (pad, y))
                y += 16

        y += 5
        pygame.draw.line(self.screen, C_GRID, (pad, y), (pad + w, y))
        y += 5

        # === Инвентарь артефактов ===
        inv = self.inventory[self.current_player]
        t = self.font_big.render("Артефакты:", True, C_GOLD)
        self.screen.blit(t, (pad, y))
        y += 20
        for name in ARTIFACT_NAMES:
            count = inv[name]
            col = ARTIFACT_COLORS.get(name, C_TEXT)
            if count > 0:
                col_actual = col
            else:
                col_actual = C_GRAY
            t = self.font_small.render(f"{name}: {count}", True, col_actual)
            self.screen.blit(t, (pad + 4, y))
            y += 14

        y += 5
        pygame.draw.line(self.screen, C_GRID, (pad, y), (pad + w, y))
        y += 5

        # === Инфо о юните ===
        if self.selected_unit:
            u = self.selected_unit
            names = {"knight": "Рыцарь", "cavalry": "Конный", "archer": "Лучник"}
            t = self.font_big.render(names.get(u.unit_type, "?"), True, C_WHITE)
            self.screen.blit(t, (pad, y))
            y += 20
            for s_text in [f"HP:{u.hp}/{u.max_hp} ARM:{u.armor}/{u.max_armor}",
                           f"DMG:{u.damage} Ходы:{u.moves_left}/{u.max_moves}"]:
                t = self.font.render(s_text, True, C_TEXT)
                self.screen.blit(t, (pad, y))
                y += 16
            y += 5

            # === Кнопка «Тянуть артефакт» (руины) ===
            if self.board.is_in_ruins(u.row, u.col) and u.moves_left > 0:
                btn_h = 30
                pygame.draw.rect(self.screen, (80, 60, 30),
                                 (pad, y, w, btn_h), border_radius=4)
                pygame.draw.rect(self.screen, C_GOLD,
                                 (pad, y, w, btn_h), 2, border_radius=4)
                t = self.font.render("Тянуть артефакт (1 ход)", True, C_GOLD)
                self.screen.blit(t, (pad + 8, y + 7))
                self._sidebar_buttons.append(
                    (pad, y, w, btn_h, self.try_draw_card))
                y += btn_h + 5

            # === Заклинания (башня мага) ===
            mt = self.board.is_in_mage_tower(u.row, u.col)
            if mt and mt.occupant == u and u.moves_left > 0:
                t = self.font_big.render("Заклинания:", True, (200, 150, 255))
                self.screen.blit(t, (pad, y))
                y += 20
                for i, sp in enumerate(SPELL_RECIPES):
                    craftable = can_craft(inv, sp["recipe"])
                    btn_h = 42
                    bg = (50, 30, 80) if craftable else (40, 30, 40)
                    border = (150, 100, 255) if craftable else C_LOCKED
                    pygame.draw.rect(self.screen, bg,
                                     (pad, y, w, btn_h), border_radius=4)
                    pygame.draw.rect(self.screen, border,
                                     (pad, y, w, btn_h), 2, border_radius=4)
                    tc = (200, 150, 255) if craftable else C_LOCKED
                    t = self.font.render(sp["name"], True, tc)
                    self.screen.blit(t, (pad + 6, y + 3))
                    # Рецепт
                    recipe_str = ", ".join(
                        f"{v}x {k}" for k, v in sp["recipe"].items())
                    t2 = self.font_small.render(recipe_str, True,
                                                C_TEXT if craftable else C_GRAY)
                    self.screen.blit(t2, (pad + 6, y + 17))
                    t3 = self.font_small.render(sp["desc"], True,
                                                C_GOLD if craftable else C_GRAY)
                    self.screen.blit(t3, (pad + 6, y + 29))
                    if craftable:
                        idx = i
                        self._sidebar_buttons.append(
                            (pad, y, w, btn_h,
                             lambda ii=idx: self.try_cast_spell(ii)))
                    y += btn_h + 3

            # === Крафт оружия ===
            t = self.font_big.render("Крафт оружия:", True, (255, 180, 80))
            self.screen.blit(t, (pad, y))
            y += 20
            for i, wp in enumerate(WEAPON_RECIPES):
                craftable = can_craft(inv, wp["recipe"])
                # Проверка типа юнита
                type_ok = (wp["target"] == "any" or
                           wp["target"] == u.unit_type)
                usable = craftable and type_ok
                btn_h = 42
                bg = (60, 50, 20) if usable else (40, 35, 25)
                border = (255, 180, 80) if usable else C_LOCKED
                pygame.draw.rect(self.screen, bg,
                                 (pad, y, w, btn_h), border_radius=4)
                pygame.draw.rect(self.screen, border,
                                 (pad, y, w, btn_h), 2, border_radius=4)
                tc = (255, 200, 100) if usable else C_LOCKED
                t = self.font.render(wp["name"], True, tc)
                self.screen.blit(t, (pad + 6, y + 3))
                recipe_str = ", ".join(
                    f"{v}x {k}" for k, v in wp["recipe"].items())
                t2 = self.font_small.render(recipe_str, True,
                                            C_TEXT if usable else C_GRAY)
                self.screen.blit(t2, (pad + 6, y + 17))
                desc_text = wp["desc"]
                if wp["target"] == "archer":
                    desc_text += " [лучник]"
                t3 = self.font_small.render(desc_text, True,
                                            C_GOLD if usable else C_GRAY)
                self.screen.blit(t3, (pad + 6, y + 29))
                if usable:
                    idx = i
                    self._sidebar_buttons.append(
                        (pad, y, w, btn_h,
                         lambda ii=idx: self.try_craft_weapon(ii)))
                y += btn_h + 3

        y += 10

        # === Кнопки внизу (фиксированные) ===
        btn_y = HEIGHT - 90
        bh = 30
        # Пропустить
        pygame.draw.rect(self.screen, (60, 60, 40),
                         (pad, btn_y, w, bh), border_radius=4)
        pygame.draw.rect(self.screen, C_TEXT,
                         (pad, btn_y, w, bh), 1, border_radius=4)
        t = self.font.render("Пропустить (ПКМ/Space)", True, C_TEXT)
        self.screen.blit(t, (pad + 8, btn_y + 7))
        self._sidebar_buttons.append(
            (pad, btn_y, w, bh, self.skip_unit))

        # Сдаться
        btn_y2 = HEIGHT - 50
        pygame.draw.rect(self.screen, (80, 20, 20),
                         (pad, btn_y2, w, bh), border_radius=4)
        pygame.draw.rect(self.screen, (200, 50, 50),
                         (pad, btn_y2, w, bh), 1, border_radius=4)
        t = self.font.render("Сдаться", True, (200, 50, 50))
        self.screen.blit(t, (pad + w // 2 - 25, btn_y2 + 7))

        def do_surrender():
            self.winner = 2 if self.current_player == 1 else 1
            self.state = "game_over"
            self.message = f"Игрок {self.current_player} сдался!"

        self._sidebar_buttons.append(
            (pad, btn_y2, w, bh, do_surrender))

    def draw_unit_preview_popup(self):
        """Увеличенный спрайт фигурки при клике на неё."""
        u = self.preview_unit
        if u is None:
            return
        cs = CELL_SIZE
        ps = cs * 4  # размер превью-спрайта
        pw, ph = ps + 20, ps + 90
        board_w = COLS * cs
        px = (board_w - pw) // 2
        py = (HEIGHT - ph) // 2

        # Фон
        bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
        bg.fill((15, 12, 8, 220))
        self.screen.blit(bg, (px, py))

        # Рамка в цвете игрока
        border_col = C_P1 if u.player == 1 else C_P2
        pygame.draw.rect(self.screen, border_col, (px, py, pw, ph), 3, border_radius=8)

        # Большой спрайт
        raw_sprite = None
        if u.unit_type == "cavalry":
            l_sheet_path = f"Units/{'Blue' if u.player == 1 else 'Red'} Units/Lancer/Lancer_Idle.png"
            raw_sheet = load_sprite(l_sheet_path)
            if raw_sheet:
                raw_sprite = extract_frame(raw_sheet, 0, 320, 320, (ps, ps))
        else:
            key_map = {"knight": "Warrior/Warrior_Idle.png",
                       "archer": "Archer/Archer_Idle.png"}
            color = "Blue" if u.player == 1 else "Red"
            path = f"Units/{color} Units/{key_map.get(u.unit_type, 'Warrior/Warrior_Idle.png')}"
            raw_sheet = load_sprite(path)
            if raw_sheet:
                raw_sprite = extract_frame(raw_sheet, 0, 192, 192, (ps, ps))

        sp_x = px + 10
        sp_y = py + 5
        if raw_sprite:
            self.screen.blit(raw_sprite, (sp_x, sp_y))
        else:
            color = C_P1 if u.player == 1 else C_P2
            pygame.draw.rect(self.screen, color, (sp_x, sp_y, ps, ps), border_radius=6)

        # Имя и статы
        names = {"knight": "Рыцарь", "cavalry": "Конный рыцарь", "archer": "Лучник"}
        ty = py + ps + 10
        t = self.font_big.render(names.get(u.unit_type, "?"), True, C_WHITE)
        self.screen.blit(t, (px + (pw - t.get_width()) // 2, ty))
        ty += 20
        player_label = f"Игрок {u.player}"
        t2 = self.font.render(player_label, True, border_col)
        self.screen.blit(t2, (px + (pw - t2.get_width()) // 2, ty))
        ty += 16
        stats = f"HP {u.hp}/{u.max_hp}  Броня {u.armor}/{u.max_armor}  Урон {u.damage}  Ходы {u.max_moves}"
        t3 = self.font_small.render(stats, True, C_TEXT)
        self.screen.blit(t3, (px + (pw - t3.get_width()) // 2, ty))

        # Подсказка
        hint = self.font_small.render("Нажми снова чтобы закрыть", True, C_GRAY)
        self.screen.blit(hint, (px + (pw - hint.get_width()) // 2, py + ph - 14))

    def draw_popup(self):
        if self.popup_text and self.popup_timer > 0:
            self.popup_timer -= 1
            pw, ph = 320, 50
            px = (COLS * CELL_SIZE - pw) // 2
            py = (HEIGHT - ph) // 2
            s = pygame.Surface((pw, ph), pygame.SRCALPHA)
            s.fill((0, 0, 0, 190))
            self.screen.blit(s, (px, py))
            pygame.draw.rect(self.screen, C_GOLD,
                             (px, py, pw, ph), 2, border_radius=6)
            t = self.font_big.render(self.popup_text, True, C_GOLD)
            self.screen.blit(t, (px + (pw - t.get_width()) // 2, py + 14))
            if self.popup_timer <= 0:
                self.popup_text = None

    def draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        color = C_P1 if self.winner == 1 else C_P2
        t = self.font_title.render(self.message, True, color)
        self.screen.blit(t, ((WIDTH - t.get_width()) // 2, HEIGHT // 2 - 30))
        t2 = self.font.render("R = рестарт | ESC = выход", True, C_TEXT)
        self.screen.blit(t2, ((WIDTH - t2.get_width()) // 2, HEIGHT // 2 + 20))

    # -------------------- ГЛАВНЫЙ ЦИКЛ --------------------

    def run_once(self):
        """Запустить один матч. Возвращает управление после конца игры или ESC."""
        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Во время хода AI не принимаем клики на доску
                    if self.ai_mode and self.current_player == 2:
                        pass
                    elif event.button == 1:
                        self.handle_click(*event.pos)
                    elif event.button == 3:
                        if self.selected_unit:
                            self.next_unit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False   # возврат в меню
                    elif event.key == pygame.K_r and self.state == "game_over":
                        running = False   # перезапуск через меню
                    elif event.key == pygame.K_SPACE:
                        if not (self.ai_mode and self.current_player == 2):
                            self.skip_unit()

            # Шаг AI (если его ход)
            if (self.ai_mode and self.current_player == 2
                    and self.ai_player and self.state != "game_over"):
                self.ai_player.step()

            self.draw()

    # Оставляем run() для совместимости
    def run(self):
        self.run_once()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Рыцари и Замки")
    clock = pygame.time.Clock()

    while True:
        menu = MenuScreen(screen, clock)
        mode = menu.run()
        ai_mode = (mode == "ai")
        game = Game(ai_mode=ai_mode, screen=screen, clock=clock)
        game.run_once()       # играем один матч — по ESC/R возвращаемся в меню
