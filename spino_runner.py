import pygame
import random
import os
import math

# ---------------------------
# Настройки окна и игры
# ---------------------------
WIDTH, HEIGHT = 800, 400
FPS = 60
TITLE = "Спинозавр: кактусы и птеранодоны"
ASSETS_DIR = "assets"
RECORD_FILE = "records.txt"

# ---------------------------
# Путь к звукам
# (папка, из которой запущена игра)\sounds\
# ---------------------------
SOUND_DIR = os.path.join(os.getcwd(), "sounds")
SND_JUMP = os.path.join(SOUND_DIR, "jump.wav")
SND_CHECKPOINT = os.path.join(SOUND_DIR, "checkpoint.wav")
SND_DEATH = os.path.join(SOUND_DIR, "death.wav")
SND_MENU_CLICK = os.path.join(SOUND_DIR, "menu_click.wav")
SND_MENU_HOVER = os.path.join(SOUND_DIR, "menu_hover.wav")

# ---------------------------
# Константы размеров
# ---------------------------
SPINO_STAND_W, SPINO_STAND_H = 150, 150
SPINO_DUCK_W,  SPINO_DUCK_H  = 192, 84
CACTUS_W,      CACTUS_H      = 66, 126
PTERA_W,       PTERA_H       = 144, 90

SCROLL_SPEED = 7
GRAVITY = 0.7
JUMP_V = 18.0
DISTANCE_SPEED = 20.0

# Шаг дистанции для "меток" (чекпоинтов)
CHECKPOINT_STEP = 500.0

HITBOX_SCALE = 0.7
SAFE_GAP = 10

# ---------------------------
# Разметка фона
# ---------------------------
GROUND_H = 70
HILLS_H  = 160
SKY_H    = HEIGHT - GROUND_H - HILLS_H
GROUND_TOP = HEIGHT - GROUND_H

PIXELATE_FACTOR = 2

# ---------------------------
# Цвета
# ---------------------------
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

SKY_COLOR   = (130, 185, 240)
SUN_COLOR   = (255, 230, 120)
CLOUD_COLOR = (245, 245, 255)

HILL_FAR_COLOR  = (45, 100, 60)
HILL_NEAR_COLOR = (60, 120, 70)

GROUND_COLOR = (70, 160, 80)
FERN_COLOR   = (25, 85, 50)

# ---------------------------
# Деревья (текстуры)
# ---------------------------
TREE_BASE_W, TREE_BASE_H = 48, 64
TREE_SPACING = 200
TREE_Y_OFFSET = 14

# ---------------------------
# Облака
# ---------------------------
CLOUD_COUNT = 4
CLOUD_SPAWN_OFFSET_MAX = 150

# ---------------------------
# Оптимизация холмов
# ---------------------------
HILL_SAMPLE_STEP = 2

# ---------------------------
# Утилиты
# ---------------------------
def load_image(name, size):
    path = os.path.join(ASSETS_DIR, name)
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, size)

def try_load_image(path):
    if os.path.exists(path):
        return pygame.image.load(path).convert_alpha()
    return None

def load_tree_variants():
    names = ["tree1.png", "tree2.png", "tree3.png"]
    imgs = []
    for n in names:
        p = os.path.join(ASSETS_DIR, n)
        img = try_load_image(p)
        if img:
            imgs.append(img)
    if imgs:
        return imgs

    # Фоллбэк: простая «ёлка»
    surf = pygame.Surface((TREE_BASE_W, TREE_BASE_H), pygame.SRCALPHA)
    trunk_w, trunk_h = 8, 16
    trunk_rect = pygame.Rect((TREE_BASE_W - trunk_w)//2, TREE_BASE_H - trunk_h - 2, trunk_w, trunk_h)
    pygame.draw.rect(surf, (92, 64, 48), trunk_rect)
    levels = [(TREE_BASE_W//2, TREE_BASE_H - trunk_h - 6, TREE_BASE_W - 8),
              (TREE_BASE_W//2, TREE_BASE_H - trunk_h - 20, TREE_BASE_W - 18),
              (TREE_BASE_W//2, TREE_BASE_H - trunk_h - 32, TREE_BASE_W - 28)]
    for cx, cy, w in levels:
        h = w//2 + 4
        poly = [(cx, cy - h), (cx - w//2, cy), (cx + w//2, cy)]
        pygame.draw.polygon(surf, (40, 110, 55), poly)
        pygame.draw.polygon(surf, (28, 88, 46), poly, 2)
    return [surf]

def pixelate_surface(surface, factor):
    if factor <= 1:
        return surface
    w, h = surface.get_size()
    small_w = max(1, w // factor)
    small_h = max(1, h // factor)
    small = pygame.transform.scale(surface, (small_w, small_h))
    return pygame.transform.scale(small, (w, h))

# ---------------------------
# Рекорды
# ---------------------------
def load_records():
    if not os.path.exists(RECORD_FILE):
        return 0, 0
    try:
        with open(RECORD_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        score = int(lines[0].split("=")[1]) if len(lines) > 0 else 0
        distance = int(lines[1].split("=")[1]) if len(lines) > 1 else 0
        return score, distance
    except:
        return 0, 0

def save_records(score, distance):
    with open(RECORD_FILE, "w", encoding="utf-8") as f:
        f.write(f"score={score}\n")
        f.write(f"distance={distance}\n")

# ---------------------------
# Шрифты
# ---------------------------
def get_font_artegra(size, bold=False):
    # 1) пробуем TTF/OTF из assets
    candidates = [
        "ArtegraSans.ttf",
        "ArtegraSans-Regular.ttf",
        "ArtegraSans-Regular.otf",
        "ArtegraSansAlt.ttf",
        "ArtegraSansAlt-Regular.ttf",
    ]
    for fname in candidates:
        p = os.path.join(ASSETS_DIR, fname)
        if os.path.exists(p):
            f = pygame.font.Font(p, size)
            try:
                f.set_bold(bold)
            except:
                pass
            return f
    # 2) пробуем системный шрифт
    f = pygame.font.SysFont("artegra sans", size, bold=bold)
    return f

def draw_outlined_text(surface, text, font, center_pos, fg=WHITE, outline_color=BLACK, outline_w=2):
    # Рисуем обводку повторными смещениями, затем — основное белое
    ts_fg = font.render(text, True, fg)
    ts_outline = font.render(text, True, outline_color)
    cx, cy = center_pos
    rect_fg = ts_fg.get_rect(center=(cx, cy))
    rect_outline = ts_outline.get_rect(center=(cx, cy))
    # окружность из смещений
    for dx in range(-outline_w, outline_w + 1):
        for dy in range(-outline_w, outline_w + 1):
            if dx*dx + dy*dy <= outline_w * outline_w:
                r = rect_outline.copy()
                r.x += dx
                r.y += dy
                surface.blit(ts_outline, r)
    surface.blit(ts_fg, rect_fg)

# ---------------------------
# Шум для холмов
# ---------------------------
def _hash_u32(n):
    n = (n ^ 61) ^ (n >> 16)
    n = (n + (n << 3)) & 0xFFFFFFFF
    n = n ^ (n >> 4)
    n = (n * 0x27d4eb2d) & 0xFFFFFFFF
    n = n ^ (n >> 15)
    return n

def rand01_from_i(i, seed):
    return _hash_u32(i + 374761393 * seed) / 0xFFFFFFFF

def smoothstep(t):
    return t * t * (3 - 2 * t)

class FractalNoise1D:
    def __init__(self, seed=1, octaves=4, persistence=0.5, base_freq=1/220.0):
        self.seed = seed
        self.octaves = octaves
        self.persistence = persistence
        self.base_freq = base_freq

    def value_noise(self, x, octave):
        i0 = math.floor(x)
        i1 = i0 + 1
        t = smoothstep(x - i0)
        v0 = rand01_from_i(i0, self.seed + octave * 101)
        v1 = rand01_from_i(i1, self.seed + octave * 101)
        return v0 * (1 - t) + v1 * t

    def noise(self, x):
        amp = 1.0
        freq = 1.0
        total = 0.0
        norm = 0.0
        for o in range(self.octaves):
            n = self.value_noise(x * freq, o)
            total += n * amp
            norm += amp
            amp *= self.persistence
            freq *= 2.0
        return total / max(1e-6, norm)

# ---------------------------
# Кеш масштабов деревьев
# ---------------------------
class TreeBillboardCache:
    def __init__(self, images):
        self.images = images
        self.cache = {}  # (idx, w, h) -> Surface

    def get(self, idx, w, h):
        key = (idx, w, h)
        surf = self.cache.get(key)
        if surf is None:
            surf = pygame.transform.smoothscale(self.images[idx], (w, h))
            self.cache[key] = surf
        return surf

# ---------------------------
# Слои холмов
# ---------------------------
class HillNoiseLayer:
    def __init__(self, color, amplitude, speed_scale, band_bottom_y, seed, base_freq, poly_base_y=None):
        self.color = color
        self.amp = amplitude
        self.speed = SCROLL_SPEED * speed_scale
        self.offset = 0.0
        self.y_bottom = band_bottom_y
        self.y_top_limit = SKY_H
        self.noise = FractalNoise1D(seed=seed, octaves=4, persistence=0.55, base_freq=base_freq)
        self.poly_base_y = poly_base_y if poly_base_y is not None else self.y_bottom
        self.cached_heights = [self.y_bottom] * (WIDTH + 1)

    def get_height_at(self, x):
        base = self.y_bottom - self.amp * 0.6
        n = self.noise.noise((x + self.offset) * self.noise.base_freq)
        y = base - (n - 0.5) * 2.0 * self.amp
        y = max(self.y_top_limit, min(self.y_bottom, y))
        return y

    def update(self):
        self.offset += self.speed

    def precompute(self):
        step = max(1, int(HILL_SAMPLE_STEP))
        prev_y = self.get_height_at(0)
        self.cached_heights[0] = prev_y
        for x in range(step, WIDTH + 1, step):
            y = self.get_height_at(x)
            x0 = x - step
            dy = (y - prev_y) / step
            for xi in range(x0 + 1, x + 1):
                self.cached_heights[xi] = prev_y + dy * (xi - x0)
            prev_y = y

    def draw(self, surf):
        points = [(x, self.cached_heights[x]) for x in range(WIDTH + 1)]
        points.append((WIDTH, self.poly_base_y))
        points.append((0, self.poly_base_y))
        pygame.draw.polygon(surf, self.color, points)

    def draw_trees_billboards(self, surf, tree_cache):
        if not tree_cache or not tree_cache.images:
            return
        scroll = self.offset
        spacing = TREE_SPACING
        start_idx = math.floor((scroll - WIDTH) / spacing)
        end_idx = math.floor((scroll + WIDTH * 2) / spacing)
        for k in range(start_idx, end_idx + 1):
            screen_x = int(k * spacing - scroll)
            if screen_x < -spacing or screen_x > WIDTH + spacing:
                continue
            rng = random.Random(1000 + k * 7919)
            idx = rng.randrange(len(tree_cache.images))
            scale = round(rng.uniform(0.85, 1.20) / 0.05) * 0.05
            w = max(8, int(TREE_BASE_W * scale))
            h = max(8, int(TREE_BASE_H * scale))
            img_scaled = tree_cache.get(idx, w, h)
            x_clamped = max(0, min(WIDTH, screen_x))
            ground_y = int(self.cached_heights[x_clamped])
            rect = img_scaled.get_rect()
            rect.midbottom = (screen_x, ground_y + TREE_Y_OFFSET)
            surf.blit(img_scaled, rect)

# ---------------------------
# Фон: небо, холмы, земля
# ---------------------------
class Cloud:
    def __init__(self):
        self.w = random.randint(70, 110)
        self.h = random.randint(35, 55)
        self.x = WIDTH + random.randint(0, CLOUD_SPAWN_OFFSET_MAX)
        self.y = random.randint(10, max(10, SKY_H - self.h - 10))
        self.speed = random.uniform(0.8, 1.3)
        self.lobes = []
        for _ in range(random.randint(3, 4)):
            lw = int(self.w * random.uniform(0.35, 0.6))
            lh = int(self.h * random.uniform(0.5, 0.9))
            ox = random.randint(-self.w // 4, self.w // 4)
            oy = random.randint(-self.h // 5, self.h // 5)
            self.lobes.append((ox, oy, lw, lh))

    def update(self):
        self.x -= self.speed
        return self.x + self.w < 0

    def draw(self, surf):
        rect = pygame.Rect(self.x, self.y, self.w, self.h)
        pygame.draw.ellipse(surf, CLOUD_COLOR, rect)
        for ox, oy, lw, lh in self.lobes:
            r = pygame.Rect(self.x + ox, self.y + oy, lw, lh)
            pygame.draw.ellipse(surf, CLOUD_COLOR, r)

class Background:
    def __init__(self, tree_images):
        self.sun_pos = (WIDTH - 120, SKY_H // 2)
        self.sun_r = 30
        self.clouds = [Cloud() for _ in range(CLOUD_COUNT)]
        self.hills_far = HillNoiseLayer(
            HILL_FAR_COLOR,
            amplitude=28,
            speed_scale=0.18,
            band_bottom_y=SKY_H + HILLS_H - 35,
            seed=1337,
            base_freq=1/260.0,
            poly_base_y=GROUND_TOP
        )
        self.hills_near = HillNoiseLayer(
            HILL_NEAR_COLOR,
            amplitude=42,
            speed_scale=0.35,
            band_bottom_y=SKY_H + HILLS_H,
            seed=4242,
            base_freq=1/330.0,
            poly_base_y=GROUND_TOP
        )
        self.tree_cache = TreeBillboardCache(tree_images) if tree_images else None

    def update(self):
        self.hills_far.update()
        self.hills_near.update()
        for c in self.clouds[:]:
            if c.update():
                self.clouds.remove(c)
        while len(self.clouds) < CLOUD_COUNT:
            self.clouds.append(Cloud())

    def draw_to_surface(self, surf):
        surf.fill(SKY_COLOR)
        pygame.draw.circle(surf, SUN_COLOR, self.sun_pos, self.sun_r)
        pygame.draw.circle(surf, (255, 240, 160), self.sun_pos, self.sun_r + 6, 3)
        for c in self.clouds:
            c.draw(surf)
        self.hills_far.precompute()
        self.hills_near.precompute()
        self.hills_far.draw(surf)
        self.hills_near.draw(surf)
        if self.tree_cache:
            self.hills_near.draw_trees_billboards(surf, self.tree_cache)
        pygame.draw.rect(surf, GROUND_COLOR, (0, HEIGHT - GROUND_H, WIDTH, GROUND_H))

# ---------------------------
# Декор: папоротники
# ---------------------------
class Fern:
    def __init__(self):
        self.base_y = HEIGHT - 1
        self.x = WIDTH + random.randint(0, 160)
        self.speed = SCROLL_SPEED
        self.scale = random.uniform(0.9, 1.3)
        self.height = int(46 * self.scale)
        self.leaf_count = random.randint(6, 8)
        self.leaf_span = int(16 * self.scale)
        self.stroke = max(2, int(2 * self.scale))
        self.sway_phase = random.uniform(0, math.tau)

    def update(self, dt):
        self.x -= self.speed
        self.sway_phase += dt * 1.0
        return self.x + self.leaf_span < 0

    def draw(self, surf):
        base_x = int(self.x)
        base_y = self.base_y
        stem_top = (base_x, base_y - self.height)
        pygame.draw.line(surf, FERN_COLOR, (base_x, base_y), stem_top, self.stroke)
        for i in range(1, self.leaf_count + 1):
            t = i / (self.leaf_count + 1)
            y = base_y - int(self.height * t)
            leaf_len = int(self.leaf_span * (0.35 + 0.65 * (1 - t)))
            side = -1 if i % 2 == 0 else 1
            sway = math.sin(self.sway_phase + t * 3.0) * 3
            dx = int(side * (leaf_len + sway))
            dy = -int(leaf_len * 0.25)
            p0 = (base_x, y)
            p1 = (base_x + dx, y + dy)
            p2 = (base_x, y - max(2, self.stroke))
            pygame.draw.polygon(surf, FERN_COLOR, (p0, p1, p2), self.stroke)

class FernManager:
    def __init__(self):
        self.ferns = []
        self.timer = 0
        self.next_spawn = random.randint(12, 24)

    def update(self, dt):
        self.timer += 1
        if self.timer >= self.next_spawn:
            self.ferns.append(Fern())
            self.timer = 0
            self.next_spawn = random.randint(14, 30)
        for f in self.ferns[:]:
            if f.update(dt):
                self.ferns.remove(f)

    def draw(self, surf):
        for f in self.ferns:
            f.draw(surf)

# ---------------------------
# Игрок
# ---------------------------
class Player:
    def __init__(self, x=70):
        self.x = x
        self.on_ground = True
        self.vy = 0.0
        self.ducking = False

        self.image_stand = load_image("spino_stand.png", (SPINO_STAND_W, SPINO_STAND_H))
        self.image_duck = load_image("spino_duck.png", (SPINO_DUCK_W, SPINO_DUCK_H))

        self.vis_rect = self.image_stand.get_rect()
        self.vis_rect.left = self.x
        self.vis_rect.bottom = HEIGHT

        self.rect = pygame.Rect(0, 0, int(SPINO_STAND_W * HITBOX_SCALE), int(SPINO_STAND_H * HITBOX_SCALE))
        self._rebuild_hitbox()

    def _current_size(self):
        if self.ducking:
            return SPINO_DUCK_W, SPINO_DUCK_H
        return SPINO_STAND_W, SPINO_STAND_H

    def _rebuild_hitbox(self):
        w, h = self._current_size()
        hit_w = int(w * HITBOX_SCALE)
        hit_h = int(h * HITBOX_SCALE)
        self.rect.size = (hit_w, hit_h)
        self.rect.centerx = self.vis_rect.centerx
        self.rect.bottom = self.vis_rect.bottom

    def start_jump(self):
        if self.on_ground:
            self.on_ground = False
            self.ducking = False
            self.vy = -JUMP_V
            return True
        return False

    def update(self, keys):
        self.ducking = self.on_ground and (
            keys[pygame.K_s] or keys[pygame.K_DOWN] or keys[pygame.K_RCTRL]
        )
        if self.on_ground:
            if self.ducking:
                self.vis_rect.width, self.vis_rect.height = SPINO_DUCK_W, SPINO_DUCK_H
            else:
                self.vis_rect.width, self.vis_rect.height = SPINO_STAND_W, SPINO_STAND_H
            self.vis_rect.left = self.x
            self.vis_rect.bottom = HEIGHT
        else:
            self.vis_rect.width, self.vis_rect.height = SPINO_STAND_W, SPINO_STAND_H

        if not self.on_ground:
            self.vy += GRAVITY
            self.vis_rect.y += int(self.vy)
            if self.vis_rect.bottom >= HEIGHT:
                self.vis_rect.bottom = HEIGHT
                self.vy = 0.0
                self.on_ground = True

        self._rebuild_hitbox()

    def draw(self, surface):
        img = self.image_duck if self.ducking else self.image_stand
        surface.blit(img, (self.vis_rect.left, self.vis_rect.bottom - img.get_height()))

# ---------------------------
# Препятствия
# ---------------------------
class Obstacle:
    def __init__(self, image, w, h, hitbox_scale=HITBOX_SCALE):
        self.image = load_image(image, (w, h))
        self.vis_rect = self.image.get_rect()
        self.vis_rect.left = WIDTH

        hit_w = int(w * hitbox_scale)
        hit_h = int(h * hitbox_scale)
        self.rect = pygame.Rect(0, 0, hit_w, hit_h)
        self.rect.center = self.vis_rect.center

    def _anchor_bottom(self):
        self.rect.centerx = self.vis_rect.centerx
        self.rect.bottom = self.vis_rect.bottom

    def _anchor_top(self):
        self.rect.centerx = self.vis_rect.centerx
        self.rect.top = self.vis_rect.top

    def update(self):
        self.vis_rect.x -= SCROLL_SPEED
        self.rect.x -= SCROLL_SPEED

    def draw(self, surface):
        surface.blit(self.image, self.vis_rect)

    def is_offscreen(self):
        return self.vis_rect.right < 0

class Cactus(Obstacle):
    def __init__(self):
        super().__init__("cactus.png", CACTUS_W, CACTUS_H)
        self.vis_rect.bottom = HEIGHT
        self._anchor_bottom()

class Pteranodon(Obstacle):
    def __init__(self):
        super().__init__("pteranodon.png", PTERA_W, PTERA_H)
        stand_hit_top = HEIGHT - int(SPINO_STAND_H * HITBOX_SCALE)
        duck_hit_top  = HEIGHT - int(SPINO_DUCK_H  * HITBOX_SCALE)
        margin = 8
        min_bottom = stand_hit_top + margin
        max_bottom = duck_hit_top - SAFE_GAP
        min_bottom = max(min_bottom, PTERA_H)
        max_bottom = min(max_bottom, HEIGHT)
        if min_bottom > max_bottom:
            target_bottom = (stand_hit_top + duck_hit_top) // 2
        else:
            target_bottom = random.randint(min_bottom, max_bottom)
        self.vis_rect.bottom = target_bottom
        self._anchor_bottom()

# ---------------------------
# Кнопки UI
# ---------------------------
class Button:
    def __init__(self, rect, text, font, text_color, bg_color=(0,0,0,0), hover_color=None, border_color=WHITE, border_width=2, padding=12):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.text_color = text_color
        self.bg_color = bg_color
        self.hover_color = hover_color if hover_color else bg_color
        self.border_color = border_color
        self.border_width = border_width
        self.padding = padding

        if self.rect.w == 0 or self.rect.h == 0:
            surf = self.font.render(self.text, True, self.text_color)
            self.rect.size = (surf.get_width() + 2*self.padding, surf.get_height() + 2*self.padding)

    def is_hover(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self, surface, selected=False):
        mouse_hover = self.is_hover()
        base = self.bg_color
        hov  = self.hover_color
        if selected:
            # усиленная подсветка выбранной кнопки
            if len(hov) == 4:
                color = (hov[0], hov[1], hov[2], min(255, hov[3] + 40))
            else:
                color = hov
            bw = max(3, self.border_width + 1)
        elif mouse_hover:
            color = hov
            bw = self.border_width
        else:
            color = base
            bw = self.border_width

        if len(color) == 4 or color != (0,0,0,0):
            s = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            s.fill(color)
            surface.blit(s, self.rect.topleft)

        pygame.draw.rect(surface, self.border_color, self.rect, bw, border_radius=8)

        ts = self.font.render(self.text, True, self.text_color)
        surface.blit(ts, ts.get_rect(center=self.rect.center))

    def is_clicked(self, event_list):
        for e in event_list:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.rect.collidepoint(e.pos):
                    return True
        return False

# ---------------------------
# Меню-навигация (стрелки/мышь) + флаг смены выделения (для hover-озвучки)
# ---------------------------
def menu_navigation(buttons, selected_idx, events):
    prev_idx = selected_idx
    activated = None
    changed = False

    for e in events:
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w):
                selected_idx = (selected_idx - 1) % len(buttons)
                changed = True
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                selected_idx = (selected_idx + 1) % len(buttons)
                changed = True
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                activated = selected_idx

    mouse_pos = pygame.mouse.get_pos()
    for i, b in enumerate(buttons):
        if b.rect.collidepoint(mouse_pos) and selected_idx != i:
            selected_idx = i
            changed = True
        if b.is_clicked(events):
            activated = i

    hover_changed = changed or (selected_idx != prev_idx)
    return selected_idx, activated, hover_changed

# ---------------------------
# Создание новой игры (объекты)
# ---------------------------
def start_new_run(tree_images):
    game = {}
    game["player"] = Player()
    game["obstacles"] = []
    game["fern_mgr"] = FernManager()
    game["background"] = Background(tree_images)
    game["spawn_timer"] = 0
    game["next_spawn"] = random.randint(50, 95)
    game["score"] = 0
    game["distance"] = 0.0
    game["last_checkpoint_index"] = -1  # для звука "метки"
    return game

# ---------------------------
# Главная функция
# ---------------------------
def main():
    # Настройка аудио-буфера до init для меньшей задержки
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # Шрифты
    font_ui = pygame.font.SysFont("arial", 20)  # счёт/дистанция во время игры — Arial
    font_big = get_font_artegra(36, bold=False) # UI/кнопки — Artegra Sans
    font_huge = get_font_artegra(72, bold=True) # Заголовки — Artegra Sans

    # Рекорды
    best_score, best_distance = load_records()

    # Текстуры деревьев
    tree_images = load_tree_variants()

    # Звуки
    def load_sound(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception as e:
            print(f"[!] Не удалось загрузить звук: {path} ({e})")
            return None

    snd_jump = load_sound(SND_JUMP)
    snd_checkpoint = load_sound(SND_CHECKPOINT)
    snd_death = load_sound(SND_DEATH)
    snd_menu_click = load_sound(SND_MENU_CLICK)
    snd_menu_hover = load_sound(SND_MENU_HOVER)

    # Настройка громкости (можно подправить)
    if snd_jump: snd_jump.set_volume(0.8)
    if snd_checkpoint: snd_checkpoint.set_volume(0.6)
    if snd_death: snd_death.set_volume(0.9)
    if snd_menu_click: snd_menu_click.set_volume(0.55)
    if snd_menu_hover: snd_menu_hover.set_volume(0.35)

    # Состояния: "menu", "playing", "paused", "countdown", "game_over"
    state = "menu"
    game = None
    resume_timer = 0.0  # для countdown

    # Меню — кнопки
    btn_play = Button(pygame.Rect(0, 0, 260, 52), "Играть", font_big, WHITE, (0,0,0,80), (0,0,0,140))
    btn_exit = Button(pygame.Rect(0, 0, 260, 52), "Выход", font_big, WHITE, (0,0,0,80), (0,0,0,140))
    menu_buttons = [btn_play, btn_exit]
    menu_sel = 0

    # Пауза — кнопки
    btn_resume = Button(pygame.Rect(0, 0, 280, 52), "Продолжить", font_big, WHITE, (0,0,0,120), (0,0,0,180))
    btn_to_menu = Button(pygame.Rect(0, 0, 300, 52), "Выход в меню", font_big, WHITE, (0,0,0,120), (0,0,0,180))
    pause_buttons = [btn_resume, btn_to_menu]
    pause_sel = 0

    # Game Over — кнопки
    btn_restart = Button(pygame.Rect(0, 0, 280, 52), "Заново", font_big, WHITE, (0,0,0,120), (0,0,0,180))
    btn_go_menu = Button(pygame.Rect(0, 0, 300, 52), "Выход в меню", font_big, WHITE, (0,0,0,120), (0,0,0,180))
    over_buttons = [btn_restart, btn_go_menu]
    over_sel = 0

    # Фон для неигровых экранов
    bg_for_menus = Background(tree_images)

    running_app = True
    while running_app:
        dt_ms = clock.tick(FPS)
        dt = dt_ms / 1000.0
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                # сохранить рекорды при закрытии
                if game and state in ("playing", "paused", "countdown"):
                    if game["score"] > best_score or int(game["distance"]) > best_distance:
                        best_score = max(best_score, game["score"])
                        best_distance = max(best_distance, int(game["distance"]))
                        save_records(best_score, best_distance)
                running_app = False

        # Обновление по состояниям
        if state == "menu":
            bg_for_menus.update()

            # Рендер фона и меню
            bg_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            bg_for_menus.draw_to_surface(bg_surf)
            bg_surf = pixelate_surface(bg_surf, PIXELATE_FACTOR)
            screen.blit(bg_surf, (0, 0))

            # Заголовок: белый с чёрной обводкой
            draw_outlined_text(
                screen,
                "Spino Run",
                font_huge,
                center_pos=(WIDTH//2, 90),
                fg=WHITE,
                outline_color=BLACK,
                outline_w=3
            )

            # позиционируем кнопки
            btn_play.rect.center = (WIDTH//2, 180)
            btn_exit.rect.center = (WIDTH//2, 250)

            # навигация
            menu_sel, menu_act, hover_changed = menu_navigation(menu_buttons, menu_sel, events)
            if hover_changed and snd_menu_hover:
                snd_menu_hover.play()

            # отрисовка с выделением
            for i, b in enumerate(menu_buttons):
                b.draw(screen, selected=(i == menu_sel))

            # действия
            if menu_act is not None and snd_menu_click:
                snd_menu_click.play()
            if menu_act == 0:  # Играть
                game = start_new_run(tree_images)
                state = "playing"
                pause_sel = 0
                over_sel = 0
            elif menu_act == 1:  # Выход
                running_app = False

        elif state == "playing":
            keys = pygame.key.get_pressed()

            # Обработка событий клавиатуры для прыжка и паузы
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_w, pygame.K_UP, pygame.K_SPACE):
                        if game["player"].start_jump():
                            if snd_jump:
                                snd_jump.play()
                    elif e.key == pygame.K_ESCAPE:
                        state = "paused"
                        pause_sel = 0

            # Обновление игры
            game["player"].update(keys)
            game["distance"] += DISTANCE_SPEED * dt

            # Чекпоинты (метки)
            checkpoint_index = int(game["distance"] // CHECKPOINT_STEP)
            if checkpoint_index > game["last_checkpoint_index"]:
                game["last_checkpoint_index"] = checkpoint_index
                if checkpoint_index > 0 and snd_checkpoint:
                    snd_checkpoint.play()

            game["background"].update()

            game["spawn_timer"] += 1
            if game["spawn_timer"] >= game["next_spawn"]:
                allow_fliers = game["distance"] >= 500.0
                if allow_fliers and random.random() < 0.4:
                    game["obstacles"].append(Pteranodon())
                else:
                    game["obstacles"].append(Cactus())
                game["spawn_timer"] = 0
                game["next_spawn"] = random.randint(55, 100)

            for o in game["obstacles"][:]:
                o.update()
                if o.is_offscreen():
                    game["obstacles"].remove(o)
                    game["score"] += 1

            game["fern_mgr"].update(dt)

            # Столкновения
            if any(o.rect.colliderect(game["player"].rect) for o in game["obstacles"]):
                if snd_death:
                    snd_death.play()
                # сохранить рекорды
                if game["score"] > best_score or int(game["distance"]) > best_distance:
                    best_score = max(best_score, game["score"])
                    best_distance = max(best_distance, int(game["distance"]))
                    save_records(best_score, best_distance)
                state = "game_over"
                over_sel = 0

            # Рендер
            bg_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            game["background"].draw_to_surface(bg_surf)
            game["fern_mgr"].draw(bg_surf)
            bg_surf = pixelate_surface(bg_surf, PIXELATE_FACTOR)
            screen.blit(bg_surf, (0, 0))

            for o in game["obstacles"]:
                o.draw(screen)
            game["player"].draw(screen)

            # UI (только счёт и дистанция; без подсказок управления)
            dist_txt = int(game["distance"])
            ui1 = font_ui.render(f"Score: {game['score']}   Distance: {dist_txt}", True, BLACK)
            ui2 = font_ui.render(f"Best Score: {best_score}   Best Distance: {best_distance}", True, BLACK)
            screen.blit(ui1, (10, 10))
            screen.blit(ui2, (10, 35))

        elif state == "paused":
            # Отрисуем текущий кадр сцены (замороженной)
            if game:
                bg_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                game["background"].draw_to_surface(bg_surf)
                game["fern_mgr"].draw(bg_surf)
                bg_surf = pixelate_surface(bg_surf, PIXELATE_FACTOR)
                screen.blit(bg_surf, (0, 0))
                for o in game["obstacles"]:
                    o.draw(screen)
                game["player"].draw(screen)

            # Полупрозрачная плашка
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))

            pause_title_surf = font_huge.render("Пауза", True, WHITE)
            screen.blit(pause_title_surf, pause_title_surf.get_rect(center=(WIDTH//2, 110)))

            btn_resume.rect.center = (WIDTH//2, 190)
            btn_to_menu.rect.center = (WIDTH//2, 255)

            # навигация
            pause_sel, pause_act, hover_changed = menu_navigation(pause_buttons, pause_sel, events)
            if hover_changed and snd_menu_hover:
                snd_menu_hover.play()

            # отрисовка с выделением
            for i, b in enumerate(pause_buttons):
                b.draw(screen, selected=(i == pause_sel))

            # действия
            if pause_act is not None and snd_menu_click:
                snd_menu_click.play()
            if pause_act == 0:  # Продолжить — запускаем таймер
                resume_timer = 3.0
                state = "countdown"
            elif pause_act == 1:  # Выход в меню
                if game and (game["score"] > best_score or int(game["distance"]) > best_distance):
                    best_score = max(best_score, game["score"])
                    best_distance = max(best_distance, int(game["distance"]))
                    save_records(best_score, best_distance)
                state = "menu"
                game = None
                menu_sel = 0

        elif state == "countdown":
            # Кадр сцены (замороженной)
            if game:
                bg_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                game["background"].draw_to_surface(bg_surf)
                game["fern_mgr"].draw(bg_surf)
                bg_surf = pixelate_surface(bg_surf, PIXELATE_FACTOR)
                screen.blit(bg_surf, (0, 0))
                for o in game["obstacles"]:
                    o.draw(screen)
                game["player"].draw(screen)

            # Тёмная плашка + таймер в центре
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            screen.blit(overlay, (0, 0))

            resume_timer -= dt
            num = max(1, int(math.ceil(resume_timer)))
            timer_surf = font_huge.render(str(num), True, WHITE)
            screen.blit(timer_surf, timer_surf.get_rect(center=(WIDTH//2, HEIGHT//2)))

            if resume_timer <= 0:
                state = "playing"

        elif state == "game_over":
            # Отрисуем последнюю сцену
            if game:
                bg_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                game["background"].draw_to_surface(bg_surf)
                game["fern_mgr"].draw(bg_surf)
                bg_surf = pixelate_surface(bg_surf, PIXELATE_FACTOR)
                screen.blit(bg_surf, (0, 0))
                for o in game["obstacles"]:
                    o.draw(screen)
                game["player"].draw(screen)

            # Тёмная плашка + кнопки
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))

            title = font_huge.render("Game Over", True, WHITE)
            stats = font_big.render(f"Score: {game['score']}   Distance: {int(game['distance'])}", True, WHITE)
            screen.blit(title, title.get_rect(center=(WIDTH//2, 110)))
            screen.blit(stats, stats.get_rect(center=(WIDTH//2, 150)))

            btn_restart.rect.center = (WIDTH//2, 210)
            btn_go_menu.rect.center = (WIDTH//2, 270)

            # навигация
            over_sel, over_act, hover_changed = menu_navigation(over_buttons, over_sel, events)
            if hover_changed and snd_menu_hover:
                snd_menu_hover.play()

            # отрисовка с выделением
            for i, b in enumerate(over_buttons):
                b.draw(screen, selected=(i == over_sel))

            # действия
            if over_act is not None and snd_menu_click:
                snd_menu_click.play()
            if over_act == 0:  # Заново
                game = start_new_run(tree_images)
                state = "playing"
            elif over_act == 1:  # Выход в меню
                state = "menu"
                game = None
                menu_sel = 0

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
