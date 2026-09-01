import pygame
import sys
import math
import random
import threading
import time

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    HAS_ML = True
except ImportError:
    HAS_ML = False

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
PLAY_WIDTH = 940
PANEL_X = 950
PANEL_WIDTH = 250
CONTEXT_Y = 590
CONTEXT_HEIGHT = 210
FPS = 60

BG_COLOR = (8, 8, 18)
PANEL_BG = (16, 16, 30)
CONTEXT_BG = (12, 12, 25)
GRID_COLOR = (20, 20, 38)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (50, 50, 60)
CYAN = (0, 230, 255)
GREEN = (0, 255, 100)
YELLOW = (255, 230, 0)
RED = (255, 50, 50)
ORANGE = (255, 165, 0)
BLUE = (50, 120, 255)
PURPLE = (180, 50, 255)
MAGENTA = (255, 0, 200)
TEAL = (0, 210, 200)
DARK_RED = (120, 20, 20)
NEON_GREEN = (57, 255, 20)

CONTENT_NOUNS = [
    "time", "world", "data", "model", "code", "system", "power", "light",
    "mind", "space", "network", "memory", "logic", "truth", "signal",
    "energy", "force", "field", "wave", "engine", "vector", "tensor",
    "gradient", "neuron", "layer", "token", "prompt", "context", "output",
    "input", "weight", "bias", "loss", "score", "reward", "future",
    "past", "dream", "vision", "chaos", "order", "pattern", "structure",
    "machine", "brain", "thought", "idea", "concept", "theory", "proof",
    "algorithm", "function", "process", "agent", "task", "goal", "plan",
    "reason", "answer", "question", "problem", "solution", "method",
]

CONTENT_VERBS = [
    "runs", "thinks", "learns", "grows", "builds", "finds", "sees",
    "knows", "makes", "takes", "creates", "processes", "generates",
    "computes", "analyzes", "solves", "transforms", "evolves", "emerges",
    "decodes", "encodes", "filters", "predicts", "converges", "diverges",
    "accelerates", "illuminates", "navigates", "optimizes", "synthesizes",
    "understands", "remembers", "forgets", "imagines", "discovers",
    "explores", "connects", "separates", "combines", "reduces", "expands",
]

CONTENT_ADJS = [
    "fast", "deep", "bright", "dark", "strong", "clear", "new", "real",
    "pure", "complex", "simple", "vast", "infinite", "digital", "neural",
    "quantum", "virtual", "smart", "powerful", "ancient", "hidden",
    "emergent", "latent", "dynamic", "stable", "chaotic", "abstract",
    "concrete", "sparse", "dense", "sharp", "smooth", "noisy", "clean",
    "strange", "beautiful", "elegant", "robust", "fragile", "adaptive",
]

FUNCTION_WORDS = [
    "the", "a", "an", "is", "are", "was", "were", "of", "in", "to",
    "and", "that", "it", "for", "on", "with", "as", "by", "at", "from",
    "but", "not", "or", "can", "will", "may", "has", "have", "had",
    "do", "does", "did", "be", "been", "being", "this", "these",
    "its", "their", "our", "your", "all", "some", "any", "each",
    "more", "less", "very", "so", "if", "then", "when", "where",
    "how", "what", "which", "who", "than", "into", "through", "about",
]

NOISE_WORDS = [
    "xkjl", "qwrt", "zxcv", "bnml", "asdf", "ghjk", "yuio", "pqwe",
    "rtzu", "iopz", "vnmb", "lkjh", "fdsa", "rewq", "poiu", "mnbv",
    "cxza", "sdfe", "wret", "yuop", "azbx", "qwer", "tyui", "opas",
    "dfgh", "jklz", "xcvb", "nmqw", "erty", "uiop", "sdfg", "hjkl",
    "zxqw", "asdg", "fghj", "klzx", "cvbn", "mqwe", "rtyu", "iopa",
]

SENTENCE_TEMPLATES = [
    ["the", "ADJ", "NOUN", "VERB", "the", "ADJ", "NOUN"],
    ["a", "ADJ", "NOUN", "VERB", "a", "NOUN"],
    ["the", "NOUN", "VERB", "in", "the", "ADJ", "NOUN"],
    ["the", "NOUN", "can", "VERB", "the", "NOUN"],
    ["ADJ", "NOUN", "VERB", "the", "ADJ", "NOUN"],
    ["a", "NOUN", "VERB", "through", "the", "NOUN"],
    ["the", "ADJ", "NOUN", "VERB", "with", "the", "NOUN"],
    ["the", "NOUN", "VERB", "a", "ADJ", "NOUN"],
    ["an", "ADJ", "NOUN", "VERB", "the", "NOUN"],
    ["the", "NOUN", "VERB", "from", "the", "ADJ", "NOUN"],
]

CONTEXT_CAPACITY = 15
BASE_SPAWN_INTERVAL = 1400
MIN_SPAWN_INTERVAL = 350
TOKEN_FALL_SPEED_MIN = 0.7
TOKEN_FALL_SPEED_MAX = 1.8
PLAYER_SPEED = 5.5
BULLET_SPEED = 9
TEMP_INCREASE_RATE = 0.0025
K_COEFFICIENT_MODEL = 0.001
K_COEFFICIENT_HEURISTIC = 0.03
PPL_OVERLOAD_MODEL = 2500
PPL_OVERLOAD_HEURISTIC = 80
SKILL_CHARGES_MAX = 3
TEMPLATE_SPAWN_CHANCE = 0.25


class PPLScorer:
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.loaded = False
        self.loading = False
        self.lock = threading.Lock()
        self.pending_result = None
        self.pending_event = threading.Event()

    def load_model(self):
        if self.loading or self.loaded:
            return
        self.loading = True
        t = threading.Thread(target=self._load, daemon=True)
        t.start()

    def _load(self):
        try:
            print("[PPL] Loading Qwen3-0.6B model...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path, trust_remote_code=True
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float32,
                device_map="cpu",
                trust_remote_code=True,
            )
            self.model.eval()
            self.loaded = True
            print("[PPL] Model loaded successfully.")
        except Exception as e:
            print(f"[PPL] Failed to load model: {e}")
            self.loaded = False
        self.loading = False

    def compute_ppl_async(self, text, callback):
        def _worker():
            score, ppl, overload = self.compute_score(text)
            callback(score, ppl, overload)
        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def compute_ppl(self, text):
        if not self.loaded:
            return self._heuristic_ppl(text)
        try:
            with self.lock:
                inputs = self.tokenizer(text, return_tensors="pt")
                with torch.no_grad():
                    outputs = self.model(**inputs, labels=inputs["input_ids"])
                loss = outputs.loss.item()
                ppl = math.exp(min(loss, 20))
                return ppl
        except Exception as e:
            print(f"[PPL] Computation error: {e}")
            return self._heuristic_ppl(text)

    def _heuristic_ppl(self, text):
        words = text.lower().split()
        if len(words) < 2:
            return 200.0
        content_count = sum(
            1
            for w in words
            if w in CONTENT_NOUNS + CONTENT_VERBS + CONTENT_ADJS
        )
        function_count = sum(1 for w in words if w in FUNCTION_WORDS)
        noise_count = sum(1 for w in words if w in NOISE_WORDS)
        total = len(words)
        noise_ratio = noise_count / total if total > 0 else 0
        content_ratio = content_count / total if total > 0 else 0
        has_verb = any(w in CONTENT_VERBS for w in words)
        has_noun = any(w in CONTENT_NOUNS for w in words)
        has_adj = any(w in CONTENT_ADJS for w in words)
        has_func = any(w in FUNCTION_WORDS for w in words)
        base_ppl = 60.0
        if has_verb and has_noun:
            base_ppl -= 25
        if has_adj:
            base_ppl -= 5
        if has_func:
            base_ppl -= 8
        if content_ratio > 0.4:
            base_ppl -= 10
        if total >= 4:
            base_ppl -= 5
        if total >= 6:
            base_ppl -= 5
        base_ppl += noise_ratio * 120
        if total < 3:
            base_ppl += 40
        return max(1.0, base_ppl)

    def compute_score(self, text):
        ppl = self.compute_ppl(text)
        if self.loaded:
            k = K_COEFFICIENT_MODEL
            overload = ppl > PPL_OVERLOAD_MODEL
        else:
            k = K_COEFFICIENT_HEURISTIC
            overload = ppl > PPL_OVERLOAD_HEURISTIC
        score = 100 * math.exp(-k * (ppl - 1))
        return score, ppl, overload


class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, lifetime=30, size=3):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-3, 3)
        self.vy = vy if vy is not None else random.uniform(-3, 3)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.vx *= 0.96
        self.vy *= 0.96

    def draw(self, surface):
        if self.lifetime <= 0:
            return
        alpha = self.lifetime / self.max_lifetime
        r = min(255, int(self.color[0] * alpha))
        g = min(255, int(self.color[1] * alpha))
        b = min(255, int(self.color[2] * alpha))
        s = max(1, int(self.size * alpha))
        pygame.draw.circle(surface, (r, g, b), (int(self.x), int(self.y)), s)

    @property
    def alive(self):
        return self.lifetime > 0


class TokenBullet:
    def __init__(self, word, word_type, x, y, speed, path_type="straight", temperature=0.0):
        self.word = word
        self.word_type = word_type
        self.x = x
        self.y = y
        self.speed = speed
        self.path_type = path_type
        self.temperature = temperature
        self.time_offset = random.uniform(0, math.pi * 2)
        self.amplitude = random.uniform(30, 80)
        self.frequency = random.uniform(0.02, 0.05)
        self.base_x = x
        self.alive = True
        self.weighted = False
        self.weighted_timer = 0
        self.hallucinating = False
        self.hallucinate_timer = 0
        self.pulse_time = random.uniform(0, math.pi * 2)
        self.age = 0

        if word_type == "content_noun":
            self.color = CYAN
            self.base_font_size = 22
        elif word_type == "content_verb":
            self.color = GREEN
            self.base_font_size = 21
        elif word_type == "content_adj":
            self.color = TEAL
            self.base_font_size = 20
        elif word_type == "function":
            self.color = YELLOW
            self.base_font_size = 16
        else:
            self.color = RED
            self.base_font_size = 18

    def update(self, dt, temperature):
        self.age += dt
        self.pulse_time += dt * 3
        self.temperature = temperature
        self.y += self.speed * dt * 60

        if self.path_type == "sine":
            self.x = self.base_x + math.sin(self.age * self.frequency * 60 + self.time_offset) * self.amplitude
        elif self.path_type == "zigzag":
            period = 2.0
            phase = (self.age % period) / period
            self.x = self.base_x + self.amplitude * 0.6 * (1 if phase < 0.5 else -1)
        elif self.path_type == "random_walk" and temperature > 0.4:
            self.base_x += random.uniform(-1.5, 1.5) * temperature
            self.x = self.base_x

        if self.weighted:
            self.weighted_timer -= dt
            if self.weighted_timer <= 0:
                self.weighted = False

        if self.hallucinating:
            self.hallucinate_timer -= dt
            if self.hallucinate_timer <= 0:
                self.hallucinating = False

        self.x = max(30, min(PLAY_WIDTH - 30, self.x))

        if self.y > CONTEXT_Y + 20:
            self.alive = False

    def get_rect(self):
        font_size = self.base_font_size
        if self.weighted:
            font_size = int(font_size * 1.4)
        w = len(self.word) * font_size * 0.62 + 12
        h = font_size + 8
        return pygame.Rect(self.x - w / 2, self.y - h / 2, w, h)

    def draw(self, surface, font_cache):
        font_size = self.base_font_size
        display_word = self.word

        if self.weighted:
            font_size = int(font_size * 1.4)
            display_word = f"[{self.word}]"

        if self.hallucinating:
            chars = list(display_word)
            for i in range(len(chars)):
                if random.random() < 0.4:
                    chars[i] = random.choice("abcdefghijklmnopqrstuvwxyz")
            display_word = "".join(chars)

        if font_size not in font_cache:
            font_cache[font_size] = pygame.font.SysFont("consolas", font_size, bold=True)

        font = font_cache[font_size]
        pulse = abs(math.sin(self.pulse_time)) * 0.25 + 0.75

        color = list(self.color)
        if self.word_type == "noise":
            flicker = random.uniform(0.4, 1.0)
            color = [int(c * flicker) for c in self.color]

        glow_color = [min(255, int(c * pulse)) for c in color]

        text_surf = font.render(display_word, True, tuple(glow_color))
        rect = text_surf.get_rect(center=(int(self.x), int(self.y)))

        if self.word_type.startswith("content"):
            shadow_surf = font.render(display_word, True, (color[0] // 5, color[1] // 5, color[2] // 5))
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                surface.blit(shadow_surf, (rect.x + dx, rect.y + dy))

        surface.blit(text_surf, rect)

        if self.weighted:
            border_rect = rect.inflate(10, 6)
            pygame.draw.rect(surface, PURPLE, border_rect, 2, border_radius=4)

        if self.word_type == "noise":
            border_rect = rect.inflate(6, 4)
            pygame.draw.rect(surface, (RED[0] // 2, RED[1] // 2, RED[2] // 2), border_rect, 1, border_radius=2)


class PlayerBullet:
    def __init__(self, x, y, mode="delete"):
        self.x = x
        self.y = y
        self.mode = mode
        self.speed = BULLET_SPEED
        self.alive = True
        self.trail = []
        self.age = 0

        if mode == "delete":
            self.color = RED
            self.size = 4
        else:
            self.color = PURPLE
            self.size = 6

    def update(self, dt):
        self.age += dt
        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)
        self.y -= self.speed * dt * 60
        if self.y < -10:
            self.alive = False

    def get_rect(self):
        return pygame.Rect(
            self.x - self.size, self.y - self.size, self.size * 2, self.size * 2
        )

    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail) * 0.5
            s = max(1, int(self.size * alpha))
            c = (int(self.color[0] * alpha), int(self.color[1] * alpha), int(self.color[2] * alpha))
            pygame.draw.circle(surface, c, (int(tx), int(ty)), s)

        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)
        inner_size = max(1, self.size - 2)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), inner_size)

        if self.mode == "delete":
            for dx in [-1, 1]:
                ex = self.x + dx * (self.size + 2)
                ey = self.y
                pygame.draw.circle(surface, (RED[0] // 2, 0, 0), (int(ex), int(ey)), 2)
        else:
            for angle in range(0, 360, 90):
                rad = math.radians(angle + self.age * 200)
                ex = self.x + math.cos(rad) * (self.size + 3)
                ey = self.y + math.sin(rad) * (self.size + 3)
                pygame.draw.circle(surface, (PURPLE[0] // 2, 0, PURPLE[2] // 2), (int(ex), int(ey)), 2)


class Player:
    def __init__(self):
        self.x = PLAY_WIDTH // 2
        self.y = CONTEXT_Y - 55
        self.width = 36
        self.height = 28
        self.speed = PLAYER_SPEED
        self.shoot_cooldown = 0
        self.shoot_delay = 0.13
        self.mode = "delete"
        self.skill_charges = 0
        self.invincible = 0
        self.pulse_time = 0

    def update(self, dt, keys):
        self.pulse_time += dt
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed * dt * 60
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed * dt * 60
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed * dt * 60 * 0.6
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed * dt * 60 * 0.6

        self.x = max(self.width // 2 + 5, min(PLAY_WIDTH - self.width // 2 - 5, self.x))
        self.y = max(200, min(CONTEXT_Y - 30, self.y))

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
        if self.invincible > 0:
            self.invincible -= dt

    def can_shoot(self):
        return self.shoot_cooldown <= 0

    def shoot(self):
        self.shoot_cooldown = self.shoot_delay
        return PlayerBullet(self.x, self.y - self.height // 2, self.mode)

    def get_rect(self):
        return pygame.Rect(
            self.x - self.width // 2,
            self.y - self.height // 2,
            self.width,
            self.height,
        )

    def draw(self, surface):
        if self.invincible > 0 and int(self.invincible * 10) % 2 == 0:
            return

        pulse = abs(math.sin(self.pulse_time * 4)) * 0.3 + 0.7
        mode_color = RED if self.mode == "delete" else PURPLE
        glow = tuple(int(c * pulse) for c in mode_color)

        points = [
            (self.x, self.y - self.height // 2 - 4),
            (self.x - self.width // 2 - 2, self.y + self.height // 2 + 2),
            (self.x + self.width // 2 + 2, self.y + self.height // 2 + 2),
        ]
        pygame.draw.polygon(surface, glow, points)
        pygame.draw.polygon(surface, WHITE, points, 2)

        inner = [
            (self.x, self.y - self.height // 4),
            (self.x - self.width // 4, self.y + self.height // 4),
            (self.x + self.width // 4, self.y + self.height // 4),
        ]
        pygame.draw.polygon(surface, mode_color, inner)

        engine_glow = abs(math.sin(self.pulse_time * 8)) * 0.5 + 0.5
        eg_color = tuple(int(c * engine_glow) for c in CYAN)
        pygame.draw.circle(surface, eg_color, (int(self.x), int(self.y + self.height // 2 + 4)), 4)
        pygame.draw.circle(surface, CYAN, (int(self.x), int(self.y + self.height // 2 + 4)), 2)


class ContextWindow:
    def __init__(self):
        self.words = []
        self.capacity = CONTEXT_CAPACITY
        self.overload = 0
        self.flash_timer = 0
        self.flash_color = None
        self.last_score = 0
        self.last_ppl = 0
        self.score_display_timer = 0
        self.computing = False

    def add_word(self, word, word_type):
        if len(self.words) >= self.capacity:
            self.overload += 12
            self.flash_timer = 0.3
            self.flash_color = RED
            return False
        self.words.append((word, word_type))
        if word_type == "noise":
            self.overload += 8
            self.flash_timer = 0.2
            self.flash_color = RED
        elif word_type == "function":
            self.overload += 1
        return True

    def remove_last(self):
        if self.words:
            word, word_type = self.words.pop()
            if word_type == "noise":
                self.overload = max(0, self.overload - 8)
            elif word_type == "function":
                self.overload = max(0, self.overload - 1)

    def clear(self):
        self.words = []
        self.overload = max(0, self.overload - 15)

    def get_text(self):
        return " ".join(w for w, _ in self.words)

    def is_overloaded(self):
        return self.overload >= 100

    def update(self, dt):
        if self.flash_timer > 0:
            self.flash_timer -= dt
        if self.score_display_timer > 0:
            self.score_display_timer -= dt

    def draw(self, surface, font_cache):
        rect = pygame.Rect(8, CONTEXT_Y + 5, PLAY_WIDTH - 16, CONTEXT_HEIGHT - 10)
        bg = list(CONTEXT_BG)
        if self.flash_timer > 0 and self.flash_color:
            t = min(1.0, self.flash_timer / 0.3)
            bg = [
                int(CONTEXT_BG[i] + (self.flash_color[i] - CONTEXT_BG[i]) * t)
                for i in range(3)
            ]
        pygame.draw.rect(surface, tuple(bg), rect, border_radius=6)

        border_color = CYAN if self.overload < 40 else (YELLOW if self.overload < 70 else RED)
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=6)

        if 13 not in font_cache:
            font_cache[13] = pygame.font.SysFont("consolas", 13)
        if 15 not in font_cache:
            font_cache[15] = pygame.font.SysFont("consolas", 15)
        if 11 not in font_cache:
            font_cache[11] = pygame.font.SysFont("consolas", 11)

        label = font_cache[13].render("CONTEXT WINDOW [GENERATION BOX]", True, CYAN)
        surface.blit(label, (rect.x + 10, rect.y + 6))

        cap_text = f"[{len(self.words)}/{self.capacity}]"
        cap_label = font_cache[13].render(cap_text, True, GRAY)
        surface.blit(cap_label, (rect.x + rect.width - 70, rect.y + 6))

        bar_rect = pygame.Rect(rect.x + 10, rect.y + 24, rect.width - 20, 8)
        pygame.draw.rect(surface, DARK_GRAY, bar_rect, border_radius=4)
        ow = int(bar_rect.width * min(1.0, self.overload / 100))
        if ow > 0:
            oc = GREEN if self.overload < 30 else (YELLOW if self.overload < 55 else (ORANGE if self.overload < 75 else RED))
            pygame.draw.rect(surface, oc, pygame.Rect(bar_rect.x, bar_rect.y, ow, bar_rect.height), border_radius=4)

        ol_label = font_cache[11].render(f"OVERLOAD: {int(self.overload)}%", True, GRAY)
        surface.blit(ol_label, (rect.x + 10, rect.y + 35))

        if self.computing:
            comp_label = font_cache[11].render("COMPUTING PPL...", True, YELLOW)
            surface.blit(comp_label, (rect.x + 150, rect.y + 35))

        words_y = rect.y + 52
        words_x = rect.x + 12
        max_x = rect.x + rect.width - 12

        for i, (word, wtype) in enumerate(self.words):
            if wtype == "content_noun":
                color = CYAN
            elif wtype == "content_verb":
                color = GREEN
            elif wtype == "content_adj":
                color = TEAL
            elif wtype == "function":
                color = YELLOW
            else:
                color = RED

            word_surf = font_cache[15].render(word, True, color)
            if words_x + word_surf.get_width() > max_x:
                words_x = rect.x + 12
                words_y += 22
                if words_y > rect.y + rect.height - 30:
                    more = font_cache[11].render("...", True, GRAY)
                    surface.blit(more, (words_x, words_y))
                    break

            surface.blit(word_surf, (words_x, words_y))
            words_x += word_surf.get_width() + 8

        if self.score_display_timer > 0:
            alpha = min(1.0, self.score_display_timer / 1.5)
            sc = tuple(int(c * alpha) for c in NEON_GREEN)
            ppl_str = f"+{self.last_score:.1f}  PPL:{self.last_ppl:.1f}"
            sc_surf = font_cache[15].render(ppl_str, True, sc)
            surface.blit(sc_surf, (rect.x + rect.width - 220, rect.y + 35))

        hint = font_cache[11].render("ENTER:Submit  BKSP:RemoveLast  Q:Skill", True, DARK_GRAY)
        surface.blit(hint, (rect.x + 10, rect.y + rect.height - 18))


class TemperatureSystem:
    def __init__(self):
        self.temperature = 0.0
        self.hallucination_cooldown = 0
        self.events = []

    def update(self, dt):
        self.temperature = min(1.0, self.temperature + TEMP_INCREASE_RATE * dt)
        if self.hallucination_cooldown > 0:
            self.hallucination_cooldown -= dt
        if self.temperature > 0.45 and self.hallucination_cooldown <= 0:
            chance = 0.008 * self.temperature
            if random.random() < chance:
                self.trigger_hallucination()
                self.hallucination_cooldown = max(1.5, 4.0 / (self.temperature + 0.1))

    def trigger_hallucination(self):
        etype = random.choice(["split", "mutate", "delete_context", "speed_burst", "duplicate"])
        self.events.append({"type": etype, "timer": 2.5})

    def get_path_type(self):
        if self.temperature < 0.25:
            return "straight"
        elif self.temperature < 0.45:
            return random.choice(["straight", "sine"])
        elif self.temperature < 0.65:
            return random.choice(["sine", "zigzag"])
        else:
            return random.choice(["sine", "zigzag", "random_walk"])

    def get_speed_multiplier(self):
        return 1.0 + self.temperature * 0.7

    def get_innovation_bonus(self):
        if self.temperature > 0.65:
            return (self.temperature - 0.65) / 0.35 * 50
        return 0

    def draw(self, surface, font_cache):
        bar_x = PANEL_X + 30
        bar_y = 60
        bar_width = 28
        bar_height = 280

        if 13 not in font_cache:
            font_cache[13] = pygame.font.SysFont("consolas", 13)
        if 11 not in font_cache:
            font_cache[11] = pygame.font.SysFont("consolas", 11)

        label = font_cache[13].render("TEMPERATURE", True, WHITE)
        surface.blit(label, (bar_x - 12, bar_y - 22))

        pygame.draw.rect(surface, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height), border_radius=6)

        fill_h = int(bar_height * self.temperature)
        if fill_h > 0:
            t = self.temperature
            if t < 0.3:
                c = BLUE
            elif t < 0.55:
                c = YELLOW
            elif t < 0.75:
                c = ORANGE
            else:
                c = RED
            fill_rect = pygame.Rect(bar_x, bar_y + bar_height - fill_h, bar_width, fill_h)
            pygame.draw.rect(surface, c, fill_rect, border_radius=6)

        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 2, border_radius=6)

        for i in range(1, 10):
            y = bar_y + int(bar_height * i / 10)
            pygame.draw.line(surface, GRAY, (bar_x, y), (bar_x + bar_width, y), 1)

        tv = font_cache[11].render(f"{self.temperature:.2f}", True, WHITE)
        surface.blit(tv, (bar_x - 2, bar_y + bar_height + 8))

        if self.temperature < 0.25:
            state, sc = "PRECISE", BLUE
        elif self.temperature < 0.55:
            state, sc = "CREATIVE", YELLOW
        elif self.temperature < 0.75:
            state, sc = "UNSTABLE", ORANGE
        else:
            state, sc = "HALLUCINATE", RED

        sl = font_cache[11].render(state, True, sc)
        surface.blit(sl, (bar_x - 8, bar_y + bar_height + 24))

        if self.temperature > 0.65:
            bonus = self.get_innovation_bonus()
            bl = font_cache[11].render(f"INNOVATION +{int(bonus)}", True, NEON_GREEN)
            surface.blit(bl, (bar_x - 15, bar_y + bar_height + 40))


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Token Survivor: Context War | Token幸存者：上下文之战")
        self.clock = pygame.time.Clock()
        self.font_cache = {}

        self.ppl_scorer = PPLScorer(r"C:\my_software\code\py\Qwen3-0.6b")
        if HAS_ML:
            self.ppl_scorer.load_model()

        self.state = "MENU"
        self.high_score = 0
        self.reset_game()

    def reset_game(self):
        self.player = Player()
        self.tokens = []
        self.bullets = []
        self.particles = []
        self.context = ContextWindow()
        self.temp_system = TemperatureSystem()
        self.score = 0
        self.game_time = 0
        self.spawn_timer = 0
        self.skill_active = False
        self.skill_timer = 0
        self.screen_shake = 0
        self.combo = 0
        self.max_combo = 0
        self.wave = 1
        self.template_queue = []
        self.sentences_completed = 0
        self.tokens_destroyed = 0

    def _resolve_template_word(self, placeholder):
        if placeholder == "NOUN":
            return random.choice(CONTENT_NOUNS), "content_noun"
        elif placeholder == "VERB":
            return random.choice(CONTENT_VERBS), "content_verb"
        elif placeholder == "ADJ":
            return random.choice(CONTENT_ADJS), "content_adj"
        else:
            return placeholder, "function"

    def spawn_token(self, forced_word=None, forced_type=None):
        temp = self.temp_system.temperature

        if forced_word and forced_type:
            word, word_type = forced_word, forced_type
        else:
            noise_chance = 0.15 + temp * 0.2
            func_chance = 0.22
            roll = random.random()
            if roll < noise_chance:
                word = random.choice(NOISE_WORDS)
                word_type = "noise"
            elif roll < noise_chance + func_chance:
                word = random.choice(FUNCTION_WORDS)
                word_type = "function"
            else:
                r = random.random()
                if r < 0.4:
                    word = random.choice(CONTENT_NOUNS)
                    word_type = "content_noun"
                elif r < 0.7:
                    word = random.choice(CONTENT_VERBS)
                    word_type = "content_verb"
                else:
                    word = random.choice(CONTENT_ADJS)
                    word_type = "content_adj"

        x = random.randint(50, PLAY_WIDTH - 50)
        speed = random.uniform(TOKEN_FALL_SPEED_MIN, TOKEN_FALL_SPEED_MAX) * self.temp_system.get_speed_multiplier()
        speed *= 1.0 + (self.wave - 1) * 0.05
        path = self.temp_system.get_path_type()

        token = TokenBullet(word, word_type, x, -20, speed, path, temp)
        self.tokens.append(token)

    def spawn_template_sequence(self):
        template = random.choice(SENTENCE_TEMPLATES)
        self.template_queue = []
        for item in template:
            word, wtype = self._resolve_template_word(item)
            self.template_queue.append((word, wtype))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if self.state == "MENU":
                    if event.key == pygame.K_RETURN:
                        self.state = "PLAYING"
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        return False
                elif self.state == "PLAYING":
                    if event.key == pygame.K_TAB:
                        self.player.mode = "weighted" if self.player.mode == "delete" else "delete"
                    elif event.key == pygame.K_RETURN:
                        self.submit_context()
                    elif event.key == pygame.K_BACKSPACE:
                        self.context.remove_last()
                    elif event.key == pygame.K_q:
                        self.activate_skill()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "MENU"
                elif self.state == "GAME_OVER":
                    if event.key == pygame.K_RETURN:
                        self.state = "MENU"
                    elif event.key == pygame.K_ESCAPE:
                        return False
        return True

    def submit_context(self):
        if self.context.computing:
            return
        text = self.context.get_text()
        if len(text.split()) < 2:
            self.context.flash_timer = 0.2
            self.context.flash_color = ORANGE
            return

        self.context.computing = True

        def on_score_ready(score_val, ppl, overload):
            self.context.computing = False
            innovation = self.temp_system.get_innovation_bonus()
            combo_bonus = self.combo * 5
            total = score_val + innovation + combo_bonus

            if not overload:
                self.score += total
                self.context.last_score = total
                self.context.last_ppl = ppl
                self.context.score_display_timer = 2.5
                self.player.skill_charges = min(SKILL_CHARGES_MAX, self.player.skill_charges + 1)
                self.combo += 1
                self.max_combo = max(self.max_combo, self.combo)
                self.sentences_completed += 1
                self.temp_system.temperature = max(0, self.temp_system.temperature - 0.05)

                for _ in range(40):
                    self.particles.append(
                        Particle(
                            random.randint(100, PLAY_WIDTH - 100),
                            CONTEXT_Y,
                            NEON_GREEN,
                            random.uniform(-5, 5),
                            random.uniform(-10, -3),
                            45,
                            random.randint(2, 5),
                        )
                    )
                self.context.clear()
            else:
                self.context.overload += 18
                self.context.flash_timer = 0.5
                self.context.flash_color = RED
                self.screen_shake = 0.4
                self.combo = 0
                for _ in range(25):
                    self.particles.append(
                        Particle(
                            PLAY_WIDTH // 2,
                            CONTEXT_Y,
                            RED,
                            random.uniform(-6, 6),
                            random.uniform(-8, -2),
                            35,
                            random.randint(2, 4),
                        )
                    )

        self.ppl_scorer.compute_ppl_async(text, on_score_ready)

    def activate_skill(self):
        if self.player.skill_charges <= 0:
            return
        self.player.skill_charges -= 1
        self.skill_active = True
        self.skill_timer = 1.2

        for token in self.tokens:
            for _ in range(6):
                self.particles.append(
                    Particle(
                        token.x, token.y, token.color,
                        random.uniform(-5, 5), random.uniform(-5, 5), 30, 3
                    )
                )

        self.tokens.clear()
        self.context.overload = max(0, self.context.overload - 25)
        self.score += 30
        self.screen_shake = 0.2

    def check_collisions(self):
        for bullet in self.bullets:
            if not bullet.alive:
                continue
            br = bullet.get_rect()
            for token in self.tokens:
                if not token.alive:
                    continue
                tr = token.get_rect()
                if br.colliderect(tr):
                    bullet.alive = False
                    if bullet.mode == "delete":
                        if token.word_type in ("function", "noise"):
                            self.score += 5
                            self.tokens_destroyed += 1
                            for _ in range(10):
                                self.particles.append(
                                    Particle(
                                        token.x, token.y, RED,
                                        random.uniform(-4, 4), random.uniform(-4, 4), 25, 2
                                    )
                                )
                        else:
                            self.score += 1
                            for _ in range(6):
                                self.particles.append(
                                    Particle(
                                        token.x, token.y, ORANGE,
                                        random.uniform(-3, 3), random.uniform(-3, 3), 18, 2
                                    )
                                )
                        token.alive = False
                    else:
                        if token.word_type.startswith("content"):
                            token.weighted = True
                            token.weighted_timer = 4.0
                            for _ in range(8):
                                self.particles.append(
                                    Particle(
                                        token.x, token.y, PURPLE,
                                        random.uniform(-3, 3), random.uniform(-3, 3), 20, 2
                                    )
                                )
                        else:
                            token.alive = False
                            for _ in range(6):
                                self.particles.append(
                                    Particle(
                                        token.x, token.y, YELLOW,
                                        random.uniform(-3, 3), random.uniform(-3, 3), 18, 2
                                    )
                                )
                    break

        pr = self.player.get_rect()
        for token in self.tokens:
            if not token.alive:
                continue
            tr = token.get_rect()
            if pr.colliderect(tr):
                self.context.add_word(token.word, token.word_type)
                token.alive = False
                for _ in range(4):
                    self.particles.append(
                        Particle(
                            token.x, token.y, token.color,
                            random.uniform(-2, 2), random.uniform(-2, 2), 18, 2
                        )
                    )

    def process_hallucinations(self, dt):
        for event in self.temp_system.events:
            event["timer"] -= dt
            if event["timer"] <= 0:
                continue

            if event["type"] == "split" and self.tokens and random.random() < 0.02:
                targets = [t for t in self.tokens if t.alive and t.word_type.startswith("content")]
                if targets:
                    target = random.choice(targets)
                    new_word = random.choice(CONTENT_NOUNS + CONTENT_VERBS + CONTENT_ADJS)
                    new_type = random.choice(["content_noun", "content_verb", "content_adj"])
                    nt = TokenBullet(
                        new_word, new_type,
                        target.x + random.randint(-40, 40),
                        target.y + random.randint(-10, 10),
                        target.speed * 0.9,
                        self.temp_system.get_path_type(),
                        self.temp_system.temperature,
                    )
                    nt.hallucinating = True
                    nt.hallucinate_timer = 2.5
                    self.tokens.append(nt)
                    for _ in range(5):
                        self.particles.append(
                            Particle(target.x, target.y, MAGENTA,
                                     random.uniform(-3, 3), random.uniform(-3, 3), 15, 2)
                        )
                    event["type"] = "done"

            elif event["type"] == "mutate" and self.tokens and random.random() < 0.02:
                targets = [t for t in self.tokens if t.alive]
                if targets:
                    target = random.choice(targets)
                    target.hallucinating = True
                    target.hallucinate_timer = 3.0
                    if random.random() < 0.35:
                        target.word = random.choice(NOISE_WORDS)
                        target.word_type = "noise"
                        target.color = RED
                    for _ in range(4):
                        self.particles.append(
                            Particle(target.x, target.y, MAGENTA,
                                     random.uniform(-2, 2), random.uniform(-2, 2), 12, 2)
                        )
                    event["type"] = "done"

            elif event["type"] == "delete_context" and self.context.words and random.random() < 0.015:
                idx = random.randint(0, len(self.context.words) - 1)
                self.context.words.pop(idx)
                self.context.flash_timer = 0.15
                self.context.flash_color = ORANGE
                event["type"] = "done"

            elif event["type"] == "speed_burst" and random.random() < 0.01:
                for token in self.tokens:
                    token.speed *= 1.4
                event["type"] = "done"

            elif event["type"] == "duplicate" and self.tokens and random.random() < 0.015:
                targets = [t for t in self.tokens if t.alive]
                if targets:
                    target = random.choice(targets)
                    dup = TokenBullet(
                        target.word, target.word_type,
                        target.x + random.randint(-30, 30),
                        target.y - random.randint(10, 30),
                        target.speed,
                        target.path_type,
                        target.temperature,
                    )
                    dup.hallucinating = True
                    dup.hallucinate_timer = 2.0
                    self.tokens.append(dup)
                    event["type"] = "done"

        self.temp_system.events = [
            e for e in self.temp_system.events if e["timer"] > 0 and e["type"] != "done"
        ]

    def update(self, dt):
        if self.state != "PLAYING":
            return

        self.game_time += dt
        self.wave = 1 + int(self.game_time / 30)

        keys = pygame.key.get_pressed()
        self.player.update(dt, keys)

        if keys[pygame.K_SPACE] and self.player.can_shoot():
            self.bullets.append(self.player.shoot())

        spawn_interval = max(MIN_SPAWN_INTERVAL, BASE_SPAWN_INTERVAL - self.game_time * 8 - (self.wave - 1) * 50)
        self.spawn_timer += dt * 1000
        if self.spawn_timer >= spawn_interval:
            self.spawn_timer = 0

            if self.template_queue:
                word, wtype = self.template_queue.pop(0)
                self.spawn_token(word, wtype)
            elif random.random() < TEMPLATE_SPAWN_CHANCE and len(self.template_queue) == 0:
                self.spawn_template_sequence()
                if self.template_queue:
                    word, wtype = self.template_queue.pop(0)
                    self.spawn_token(word, wtype)
            else:
                self.spawn_token()

            if self.temp_system.temperature > 0.5 and random.random() < 0.25:
                self.spawn_token()
            if self.temp_system.temperature > 0.8 and random.random() < 0.2:
                self.spawn_token()

        self.temp_system.update(dt)

        for token in self.tokens:
            token.update(dt, self.temp_system.temperature)
        self.tokens = [t for t in self.tokens if t.alive]

        for bullet in self.bullets:
            bullet.update(dt)
        self.bullets = [b for b in self.bullets if b.alive]

        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

        self.context.update(dt)
        self.check_collisions()
        self.process_hallucinations(dt)

        if self.skill_active:
            self.skill_timer -= dt
            if self.skill_timer <= 0:
                self.skill_active = False

        if self.screen_shake > 0:
            self.screen_shake -= dt

        if self.context.is_overloaded():
            self.high_score = max(self.high_score, int(self.score))
            self.state = "GAME_OVER"

    def draw_background(self):
        self.screen.fill(BG_COLOR)
        for x in range(0, PLAY_WIDTH, 50):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, CONTEXT_Y), 1)
        for y in range(0, CONTEXT_Y, 50):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (PLAY_WIDTH, y), 1)

        scanline_y = int(self.game_time * 30) % 4
        for y in range(scanline_y, CONTEXT_Y, 4):
            pygame.draw.line(self.screen, (5, 5, 12), (0, y), (PLAY_WIDTH, y), 1)

    def draw_panel(self):
        panel_rect = pygame.Rect(PANEL_X, 0, PANEL_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect)
        pygame.draw.line(self.screen, CYAN, (PANEL_X, 0), (PANEL_X, SCREEN_HEIGHT), 2)

        if 13 not in self.font_cache:
            self.font_cache[13] = pygame.font.SysFont("consolas", 13)
        if 16 not in self.font_cache:
            self.font_cache[16] = pygame.font.SysFont("consolas", 16)
        if 22 not in self.font_cache:
            self.font_cache[22] = pygame.font.SysFont("consolas", 22, bold=True)
        if 11 not in self.font_cache:
            self.font_cache[11] = pygame.font.SysFont("consolas", 11)

        title = self.font_cache[16].render("CONTEXT WAR", True, CYAN)
        self.screen.blit(title, (PANEL_X + 25, 12))

        pygame.draw.line(self.screen, DARK_GRAY, (PANEL_X + 10, 35), (PANEL_X + PANEL_WIDTH - 10, 35), 1)

        self.temp_system.draw(self.screen, self.font_cache)

        sy = 400
        sl = self.font_cache[13].render("SCORE", True, GRAY)
        self.screen.blit(sl, (PANEL_X + 25, sy))
        sv = self.font_cache[22].render(f"{int(self.score)}", True, WHITE)
        self.screen.blit(sv, (PANEL_X + 25, sy + 18))

        cl = self.font_cache[11].render(f"COMBO: x{self.combo}", True, NEON_GREEN if self.combo > 1 else GRAY)
        self.screen.blit(cl, (PANEL_X + 25, sy + 48))

        wl = self.font_cache[11].render(f"WAVE: {self.wave}", True, CYAN)
        self.screen.blit(wl, (PANEL_X + 25, sy + 64))

        tl = self.font_cache[11].render(f"TIME: {int(self.game_time)}s", True, GRAY)
        self.screen.blit(tl, (PANEL_X + 25, sy + 80))

        scl = self.font_cache[11].render(f"SENTENCES: {self.sentences_completed}", True, TEAL)
        self.screen.blit(scl, (PANEL_X + 25, sy + 96))

        sdl = self.font_cache[11].render(f"DESTROYED: {self.tokens_destroyed}", True, RED)
        self.screen.blit(sdl, (PANEL_X + 25, sy + 112))

        if self.high_score > 0:
            hsl = self.font_cache[11].render(f"HIGH: {self.high_score}", True, YELLOW)
            self.screen.blit(hsl, (PANEL_X + 25, sy + 132))

        pygame.draw.line(self.screen, DARK_GRAY, (PANEL_X + 10, sy + 150), (PANEL_X + PANEL_WIDTH - 10, sy + 150), 1)

        my = sy + 160
        ml = self.font_cache[13].render("FIRE MODE", True, GRAY)
        self.screen.blit(ml, (PANEL_X + 25, my))
        mc = RED if self.player.mode == "delete" else PURPLE
        mn = "DELETE" if self.player.mode == "delete" else "WEIGHTED"
        mv = self.font_cache[16].render(mn, True, mc)
        self.screen.blit(mv, (PANEL_X + 25, my + 18))

        if self.player.mode == "delete":
            md = self.font_cache[11].render("Destroys func/noise", True, DARK_GRAY)
        else:
            md = self.font_cache[11].render("Boosts content words", True, DARK_GRAY)
        self.screen.blit(md, (PANEL_X + 25, my + 38))

        sky = my + 60
        skl = self.font_cache[13].render("SKILL: CONTEXT PURGE", True, GRAY)
        self.screen.blit(skl, (PANEL_X + 25, sky))
        for i in range(SKILL_CHARGES_MAX):
            c = CYAN if i < self.player.skill_charges else DARK_GRAY
            pygame.draw.rect(self.screen, c, (PANEL_X + 25 + i * 38, sky + 20, 32, 14), border_radius=3)
            if i < self.player.skill_charges:
                pygame.draw.rect(self.screen, WHITE, (PANEL_X + 25 + i * 38, sky + 20, 32, 14), 1, border_radius=3)

        pygame.draw.line(self.screen, DARK_GRAY, (PANEL_X + 10, sky + 42), (PANEL_X + PANEL_WIDTH - 10, sky + 42), 1)

        cy = sky + 52
        controls = [
            ("Arrows/WASD", "Move"),
            ("SPACE", "Shoot"),
            ("TAB", "Switch Mode"),
            ("ENTER", "Submit"),
            ("BKSP", "Remove Last"),
            ("Q", "Skill"),
            ("ESC", "Menu"),
        ]
        ctl = self.font_cache[11].render("CONTROLS", True, GRAY)
        self.screen.blit(ctl, (PANEL_X + 25, cy))
        for i, (key, desc) in enumerate(controls):
            kl = self.font_cache[11].render(f"{key}", True, CYAN)
            dl = self.font_cache[11].render(f" {desc}", True, DARK_GRAY)
            self.screen.blit(kl, (PANEL_X + 25, cy + 16 + i * 14))
            self.screen.blit(dl, (PANEL_X + 25 + kl.get_width(), cy + 16 + i * 14))

    def draw_skill_effect(self):
        if not self.skill_active:
            return
        progress = 1.0 - self.skill_timer / 1.2
        radius = int(progress * max(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.8)
        alpha = int(200 * (1.0 - progress))
        if alpha > 0 and radius > 0:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.circle(
                s, (0, 255, 255, min(alpha, 80)),
                (int(self.player.x), int(self.player.y)), radius, max(2, int(8 * (1 - progress)))
            )
            pygame.draw.circle(
                s, (255, 255, 255, min(alpha // 2, 40)),
                (int(self.player.x), int(self.player.y)), max(1, radius - 20), max(1, int(4 * (1 - progress)))
            )
            self.screen.blit(s, (0, 0))

    def draw_menu(self):
        self.screen.fill(BG_COLOR)

        if 52 not in self.font_cache:
            self.font_cache[52] = pygame.font.SysFont("consolas", 52, bold=True)
        if 26 not in self.font_cache:
            self.font_cache[26] = pygame.font.SysFont("consolas", 26)
        if 18 not in self.font_cache:
            self.font_cache[18] = pygame.font.SysFont("consolas", 18)
        if 14 not in self.font_cache:
            self.font_cache[14] = pygame.font.SysFont("consolas", 14)
        if 12 not in self.font_cache:
            self.font_cache[12] = pygame.font.SysFont("consolas", 12)

        t = pygame.time.get_ticks() / 1000.0

        title1 = self.font_cache[52].render("TOKEN SURVIVOR", True, CYAN)
        title2 = self.font_cache[26].render("CONTEXT WAR", True, NEON_GREEN)
        cx = SCREEN_WIDTH // 2
        self.screen.blit(title1, (cx - title1.get_width() // 2, 100))
        self.screen.blit(title2, (cx - title2.get_width() // 2, 165))

        sub = self.font_cache[18].render(
            '"Bullets are Context. Player is the Inference Engine."', True, YELLOW
        )
        self.screen.blit(sub, (cx - sub.get_width() // 2, 215))

        pygame.draw.line(self.screen, DARK_GRAY, (cx - 300, 250), (cx + 300, 250), 1)

        instructions = [
            ("MECHANIC A: BULLETS = TOKENS", CYAN),
            ("Words fall as tokens. Catch them to fill Context Window.", WHITE),
            ("Build coherent sentences to score and gain skills!", WHITE),
            ("Gibberish in context causes OVERLOAD -> Game Over!", RED),
            ("", GRAY),
            ("MECHANIC B: SHOOTING = SEMANTIC FILTERING", CYAN),
            ("DELETE mode: Destroys function/noise words (red bullets)", RED),
            ("WEIGHTED mode: Boosts content words (purple bullets)", PURPLE),
            ("", GRAY),
            ("MECHANIC C: TEMPERATURE = HALLUCINATION SYSTEM", CYAN),
            ("Low temp: Predictable patterns, low rewards", BLUE),
            ("High temp: Chaos, hallucinations, INNOVATION BONUS!", RED),
            ("", GRAY),
            ("SCORING: Score = 100 * exp(-k * (PPL - 1))", NEON_GREEN),
        ]

        for i, (line, color) in enumerate(instructions):
            if line:
                text = self.font_cache[14].render(line, True, color)
                self.screen.blit(text, (cx - text.get_width() // 2, 270 + i * 22))

        pulse = abs(math.sin(t * 2.5)) * 0.5 + 0.5
        sc = tuple(int(c * pulse) for c in CYAN)
        start = self.font_cache[26].render("PRESS ENTER TO START", True, sc)
        self.screen.blit(start, (cx - start.get_width() // 2, 610))

        if self.high_score > 0:
            hs = self.font_cache[18].render(f"HIGH SCORE: {self.high_score}", True, YELLOW)
            self.screen.blit(hs, (cx - hs.get_width() // 2, 660))

        if HAS_ML:
            if self.ppl_scorer.loading:
                ms, mc = "MODEL: LOADING...", YELLOW
            elif self.ppl_scorer.loaded:
                ms, mc = "MODEL: Qwen3-0.6B READY", NEON_GREEN
            else:
                ms, mc = "MODEL: NOT LOADED", ORANGE
        else:
            ms, mc = "MODEL: FALLBACK (heuristic scoring)", ORANGE
        mt = self.font_cache[12].render(ms, True, mc)
        self.screen.blit(mt, (cx - mt.get_width() // 2, 700))

        esc = self.font_cache[12].render("ESC to Quit", True, DARK_GRAY)
        self.screen.blit(esc, (cx - esc.get_width() // 2, 730))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        if 44 not in self.font_cache:
            self.font_cache[44] = pygame.font.SysFont("consolas", 44, bold=True)
        if 22 not in self.font_cache:
            self.font_cache[22] = pygame.font.SysFont("consolas", 22)
        if 16 not in self.font_cache:
            self.font_cache[16] = pygame.font.SysFont("consolas", 16)
        if 14 not in self.font_cache:
            self.font_cache[14] = pygame.font.SysFont("consolas", 14)

        cx = SCREEN_WIDTH // 2

        go = self.font_cache[44].render("CONTEXT OVERLOAD", True, RED)
        self.screen.blit(go, (cx - go.get_width() // 2, 180))

        sub = self.font_cache[16].render("The noise has overwhelmed your inference engine.", True, ORANGE)
        self.screen.blit(sub, (cx - sub.get_width() // 2, 240))

        pygame.draw.line(self.screen, DARK_GRAY, (cx - 200, 275), (cx + 200, 275), 1)

        stats = [
            (f"Final Score: {int(self.score)}", WHITE),
            (f"Survived: {int(self.game_time)}s", GRAY),
            (f"Wave Reached: {self.wave}", CYAN),
            (f"Sentences Completed: {self.sentences_completed}", NEON_GREEN),
            (f"Tokens Destroyed: {self.tokens_destroyed}", RED),
            (f"Max Combo: {self.max_combo}", YELLOW),
            (f"Final Temperature: {self.temp_system.temperature:.2f}", ORANGE),
        ]

        for i, (text, color) in enumerate(stats):
            s = self.font_cache[16].render(text, True, color)
            self.screen.blit(s, (cx - s.get_width() // 2, 295 + i * 28))

        if self.score >= self.high_score and self.score > 0:
            nh = self.font_cache[22].render("NEW HIGH SCORE!", True, YELLOW)
            self.screen.blit(nh, (cx - nh.get_width() // 2, 510))

        t = pygame.time.get_ticks() / 1000.0
        pulse = abs(math.sin(t * 2.5)) * 0.5 + 0.5
        rc = tuple(int(c * pulse) for c in CYAN)
        restart = self.font_cache[16].render("PRESS ENTER FOR MENU", True, rc)
        self.screen.blit(restart, (cx - restart.get_width() // 2, 560))

    def draw(self):
        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "PLAYING":
            ox = random.randint(-4, 4) if self.screen_shake > 0 else 0
            oy = random.randint(-4, 4) if self.screen_shake > 0 else 0

            self.draw_background()

            for token in self.tokens:
                token.draw(self.screen, self.font_cache)
            for bullet in self.bullets:
                bullet.draw(self.screen)
            for p in self.particles:
                p.draw(self.screen)

            self.player.draw(self.screen)
            self.draw_skill_effect()
            self.context.draw(self.screen, self.font_cache)
            self.draw_panel()

        elif self.state == "GAME_OVER":
            self.draw_background()
            for token in self.tokens:
                token.draw(self.screen, self.font_cache)
            self.player.draw(self.screen)
            self.context.draw(self.screen, self.font_cache)
            self.draw_panel()
            self.draw_game_over()

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)
            running = self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
