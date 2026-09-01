import pygame
import sys
import math
import random
import threading
import time
import json
import os

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

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
PINK = (255, 105, 180)
HEART_RED = (255, 30, 60)

HIGH_FREQ_WORDS = [
    "I", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those",
    "who", "what", "which",
    "am", "is", "are", "was", "were",
    "do", "does", "did", "have", "has", "had",
    "will", "would", "can", "could", "may", "might", "should",
    "in", "on", "at", "to", "for", "with",
    "by", "from", "about", "of", "up", "down",
    "and", "but", "or", "so", "because", "if", "when",
    "a", "an", "the",
    "very", "too", "just", "only",
    "here", "there", "now", "often", "always",
    "what", "where", "when", "who", "why", "how",
]

VERB_WORDS = [
    "go", "come", "make", "take", "get", "give",
    "say", "see", "look", "want", "need", "like",
    "know", "think", "feel", "use", "find",
    "run", "walk", "talk", "play", "work", "live", "love", "help",
    "open", "close", "start", "stop", "read", "write", "eat", "drink",
    "sleep", "wake", "move", "turn", "fall", "rise", "stand", "sit",
    "runs", "thinks", "learns", "grows", "builds", "finds", "sees",
    "knows", "makes", "takes", "creates", "processes", "generates",
    "computes", "analyzes", "solves", "transforms", "evolves", "emerges",
]

NOUN_WORDS = [
    "time", "world", "data", "model", "code", "system", "power", "light",
    "mind", "space", "network", "memory", "logic", "truth", "signal",
    "energy", "force", "field", "wave", "engine", "vector", "tensor",
    "gradient", "neuron", "layer", "token", "prompt", "context", "output",
    "input", "weight", "bias", "loss", "score", "reward", "future",
    "past", "dream", "vision", "chaos", "order", "pattern", "structure",
    "machine", "brain", "thought", "idea", "concept", "theory", "proof",
    "algorithm", "function", "process", "agent", "task", "goal", "plan",
    "reason", "answer", "question", "problem", "solution", "method",
    "man", "woman", "child", "people", "person", "friend", "family",
    "house", "home", "room", "door", "window", "table", "chair",
    "water", "food", "air", "fire", "earth", "sun", "moon", "star",
    "day", "night", "morning", "evening", "year", "month", "week",
    "school", "book", "word", "letter", "name", "story", "song",
    "car", "road", "city", "country", "place", "way", "thing",
    "hand", "head", "eye", "face", "body", "foot", "heart", "life",
]

DESCRIBER_WORDS = [
    "good", "bad", "big", "small", "new", "old",
    "happy", "sad", "many", "some", "all",
    "fast", "deep", "bright", "dark", "strong", "clear", "real",
    "pure", "complex", "simple", "vast", "infinite", "digital", "neural",
    "quantum", "virtual", "smart", "powerful", "ancient", "hidden",
]

NOISE_CHARS = "abcdefghijklmnopqrstuvwxyz"
NOISE_WORD_LEN_RANGE = (3, 6)

SECTION_DURATION = 30
PLAYER_SPEED = 5.5
PLAYER_BULLET_SPEED = 10
ENEMY_HP = 3
INVINCIBLE_DURATION = 5.0
GRAZE_DISTANCE = 20
LIFE_FRAGMENT_VALUE = 0.10
INITIAL_LIVES = 2
SPAWN_INTERVAL_BASE = 1.2
SPAWN_INTERVAL_MIN = 0.3
RESPONSE_DROP_DELAY = 0.6

LLM_PROMPT = (
    "You will receive a sentence. Judge if it is a reasonably coherent English sentence. "
    "Minor informalities or slight word-choice quirks are acceptable, "
    "but sentences with obvious grammatical errors (wrong verb tense, missing subject/object, wrong word order) should be considered invalid. "
    "Only reply True when the sentence reads as natural, understandable English with no glaring grammar mistakes. "
    'When True, include a short natural response sentence (under 20 tokens). '
    'Strictly use this format: {True, your response sentence} or {False}. '
    "Do not output anything else."
)

PRESET_RESPONSES = [
    "That is very interesting to hear.",
    "I agree with what you said.",
    "Can you tell me more about that?",
    "That makes a lot of sense.",
    "I never thought about it that way.",
    "What a wonderful idea you have.",
    "Please go on, I am listening.",
    "That sounds really amazing to me.",
    "I think you are absolutely right.",
    "Let me think about that for a moment.",
]

def get_config_path():
    # 打包后运行：读取exe同级目录的配置文件（方便你修改）
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(os.path.dirname(sys.executable), "api_config.json")
    # 开发运行：读取代码目录的配置文件
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_config.json")

CONFIG_PATH = get_config_path()

def generate_noise_word():
    length = random.randint(*NOISE_WORD_LEN_RANGE)
    return "".join(random.choice(NOISE_CHARS) for _ in range(length))


def is_noise_word(word):
    return not all(c in "abcdefghijklmnopqrstuvwxyz" and c.islower() for c in word.lower()) or len(word) <= 2 and word not in HIGH_FREQ_WORDS


def classify_word(word):
    if word in HIGH_FREQ_WORDS:
        return "function"
    elif word in VERB_WORDS:
        return "verb"
    elif word in NOUN_WORDS:
        return "noun"
    elif word in DESCRIBER_WORDS:
        return "describer"
    else:
        return "noise"


class LLMClient:
    def __init__(self):
        self.api_key = ""
        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-3.5-turbo"
        self.available = False
        self.no_api_mode = False
        self.client = None

    def configure(self, api_key, base_url, model):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        if HAS_OPENAI and api_key:
            try:
                self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
                self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5,
                )
                self.available = True
                return True, "API test passed!"
            except Exception as e:
                self.available = False
                return False, str(e)
        return False, "openai package not installed"

    def set_no_api(self):
        self.no_api_mode = True
        self.available = False

    def query(self, sentence, callback):
        if self.no_api_mode or not self.available:
            result = self._fallback(sentence)
            callback(result)
            return

        def _worker():
            try:
                full_prompt = LLM_PROMPT + "\n\nSentence: " + sentence
                print("\n" + "=" * 60)
                print(f"[LLM CALL] Model: {self.model} | Section input:")
                print(f"  SENTENCE: {sentence}")
                print(f"  PROMPT: {full_prompt[:200]}{'...' if len(full_prompt)>200 else ''}")
                print("-" * 60)

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": full_prompt}],
                    max_tokens=60,
                    temperature=0.3,
                )
                raw_text = response.choices[0].message.content.strip()
                print(f"[LLM RESPONSE] Raw: {raw_text}")

                result = self._parse_response(raw_text, sentence)
                print(f"[PARSED] is_true={result['is_true']} | response_words={result.get('response_words', [])}")
                if not result["success"]:
                    print(f"[WARN] Parse failed, using fallback")
                print("=" * 60 + "\n")
                callback(result)
            except Exception as e:
                print(f"\n[LLM ERROR] {type(e).__name__}: {e}\n")
                result = {"success": False, "error": str(e), "is_true": False, "response_words": [], "sentence": sentence}
                callback(result)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _parse_response(self, text, sentence):
        text = text.strip()
        try:
            if "{" in text and "}" in text:
                inner = text[text.index("{") + 1:text.rindex("}")].strip()
                if inner.startswith("True"):
                    comma_idx = inner.find(",")
                    if comma_idx != -1:
                        response_text = inner[comma_idx + 1:].strip()
                        words = response_text.split()
                        return {"success": True, "is_true": True, "response_words": words, "sentence": sentence}
                    else:
                        return {"success": True, "is_true": True, "response_words": [], "sentence": sentence}
                elif inner.startswith("False"):
                    return {"success": True, "is_true": False, "response_words": [], "sentence": sentence}
            lower = text.lower().strip()
            if lower.startswith("true") or lower.startswith("yes"):
                rest = text[4:].strip().lstrip(":,").strip()
                if rest:
                    words = rest.split()
                    return {"success": True, "is_true": True, "response_words": words[:20], "sentence": sentence}
                return {"success": True, "is_true": True, "response_words": [], "sentence": sentence}
            elif lower.startswith("false") or lower.startswith("no"):
                return {"success": True, "is_true": False, "response_words": [], "sentence": sentence}
        except Exception as e:
            print(f"[PARSE ERROR] {e} | raw={text}")
        return {"success": False, "error": "format_error", "is_true": False, "response_words": [], "sentence": sentence}

    def _fallback(self, sentence):
        is_coherent = self._naive_check(sentence)
        print(f"\n[FALLBACK] Sentence: {sentence} | coherent={is_coherent}")
        if is_coherent:
            response = random.choice(PRESET_RESPONSES)
            words = response.split()
            print(f"  → Response: {response}")
            return {"success": True, "is_true": True, "response_words": words, "sentence": sentence}
        else:
            print(f"  → Not coherent (noise incoming)")
            return {"success": True, "is_true": False, "response_words": [], "sentence": sentence}

    def _naive_check(self, sentence):
        words = sentence.lower().split()
        if len(words) < 2:
            return False
        noise_count = 0
        has_verb = False
        has_content = False
        verb_like = {"am", "is", "are", "was", "were", "do", "does", "did", "have", "has", "had",
                     "will", "would", "can", "could", "may", "might", "should",
                     "go", "come", "make", "take", "get", "give", "say", "see", "look",
                     "want", "need", "like", "know", "think", "feel", "use", "find",
                     "run", "walk", "talk", "play", "work", "live", "love", "help"}
        for w in words:
            if w in verb_like:
                has_verb = True
            if w in HIGH_FREQ_WORDS or w in VERB_WORDS or w in NOUN_WORDS or w in DESCRIBER_WORDS:
                has_content = True
            else:
                noise_count += 1
        if noise_count > len(words) * 0.4:
            return False
        if not has_verb:
            return False
        if len(words) < 3:
            return False
        return True


class EnemyBullet:
    def __init__(self, x, y, color, velocity, angle_deg, aim_player, player_x, player_y, gravity=0):
        self.x = x
        self.y = y
        self.color = color
        self.speed = velocity
        self.gravity = gravity
        self.grazed = False

        if aim_player:
            base_angle = math.atan2(player_y - y, player_x - x)
            offset = math.radians(angle_deg)
            final_angle = base_angle + offset
        else:
            final_angle = math.radians(angle_deg)

        self.vx = math.cos(final_angle) * velocity
        self.vy = math.sin(final_angle) * velocity
        self.alive = True
        self.radius = 8

    def update(self, dt):
        self.x += self.vx * dt * 60
        self.vy += self.gravity * dt * 60
        self.y += self.vy * dt * 60
        if self.x < -20 or self.x > PLAY_WIDTH + 20 or self.y < -20 or self.y > SCREEN_HEIGHT + 20:
            self.alive = False

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        inner_color = tuple(min(255, c + 80) for c in self.color)
        pygame.draw.circle(surface, inner_color, (int(self.x), int(self.y)), max(1, self.radius - 3))


class EnemyWord:
    def __init__(self, word, word_type, x, y, fall_speed):
        self.word = word
        self.word_type = word_type
        self.x = x
        self.y = y
        self.fall_speed = fall_speed
        self.hp = ENEMY_HP
        self.max_hp = ENEMY_HP
        self.alive = True
        self.fire_timer = random.uniform(1.0, 3.0)
        self.has_fired = False
        self._fire_consumed = False
        self._drops_fragment = False
        self.pulse_time = random.uniform(0, math.pi * 2)

        if word_type == "function":
            self.color = YELLOW
        elif word_type == "verb":
            self.color = ORANGE
        elif word_type == "noun":
            self.color = CYAN
        elif word_type == "describer":
            self.color = TEAL
        elif word_type == "response":
            self.color = WHITE
        elif word_type == "noise":
            self.color = RED
        else:
            self.color = GRAY

        if word_type == "response":
            self.base_font_size = 24
        elif word_type == "noise":
            self.base_font_size = 18
        else:
            self.base_font_size = 20

    def update(self, dt):
        self.y += self.fall_speed * dt * 60
        self.pulse_time += dt * 3
        if not self.has_fired:
            self.fire_timer -= dt
            if self.fire_timer <= 0:
                self.has_fired = True
        elif not self._fire_consumed:
            self._fire_consumed = True
        if self.y > CONTEXT_Y + 20:
            self.alive = False

    def get_rect(self):
        w = len(self.word) * self.base_font_size * 0.62 + 12
        h = self.base_font_size + 8
        return pygame.Rect(self.x - w / 2, self.y - h / 2, w, h)

    def get_hit_radius(self):
        w = len(self.word) * self.base_font_size * 0.62 + 12
        h = self.base_font_size + 8
        return max(w, h) / 2

    def draw(self, surface, font_cache):
        if self.base_font_size not in font_cache:
            font_cache[self.base_font_size] = pygame.font.SysFont("consolas", self.base_font_size, bold=True)
        font = font_cache[self.base_font_size]

        pulse = abs(math.sin(self.pulse_time)) * 0.2 + 0.8
        color = [min(255, int(c * pulse)) for c in self.color]
        if self.word_type == "noise":
            flicker = random.uniform(0.5, 1.0)
            color = [int(c * flicker) for c in self.color]

        text_surf = font.render(self.word, True, tuple(color))
        rect = text_surf.get_rect(center=(int(self.x), int(self.y)))

        if self.word_type == "response":
            border_rect = rect.inflate(8, 4)
            pygame.draw.rect(surface, NEON_GREEN, border_rect, 2, border_radius=3)

        surface.blit(text_surf, rect)

        if self.hp < self.max_hp:
            bar_w = max(30, len(self.word) * 10)
            bar_h = 3
            bar_x = self.x - bar_w / 2
            bar_y = self.y - self.base_font_size / 2 - 8
            pygame.draw.rect(surface, DARK_GRAY, (int(bar_x), int(bar_y), bar_w, bar_h))
            hp_w = int(bar_w * self.hp / self.max_hp)
            if hp_w > 0:
                hp_color = GREEN if self.hp > self.max_hp // 2 else (YELLOW if self.hp > 1 else RED)
                pygame.draw.rect(surface, hp_color, (int(bar_x), int(bar_y), hp_w, bar_h))


class PlayerBullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = PLAYER_BULLET_SPEED
        self.alive = True
        self.radius = 4
        self.color = CYAN

    def update(self, dt):
        self.y -= self.speed * dt * 60
        if self.y < -10:
            self.alive = False

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), max(1, self.radius - 2))


class LifeFragment:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.fall_speed = 1.5
        self.alive = True
        self.radius = 8
        self.value = LIFE_FRAGMENT_VALUE
        self.pulse_time = random.uniform(0, math.pi * 2)
        self.attract_speed = 0.0

    def update(self, dt, player_x=None, player_y=None):
        if player_x is not None and player_y is not None:
            dx = player_x - self.x
            dy = player_y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 5:
                self.attract_speed += dt * 200
                self.attract_speed = min(self.attract_speed, 12.0)
                move_speed = self.attract_speed * dt * 60
                self.x += (dx / dist) * move_speed
                self.y += (dy / dist) * move_speed
                return
        self.y += self.fall_speed * dt * 60
        self.pulse_time += dt * 4
        if self.y > CONTEXT_Y + 20:
            self.alive = False

    def draw(self, surface, font_cache):
        pulse = abs(math.sin(self.pulse_time)) * 0.3 + 0.7
        alpha = int(160 * pulse)

        s = pygame.Surface((self.radius * 2 + 4, self.radius * 2 + 4), pygame.SRCALPHA)
        center = self.radius + 2

        glow_r = self.radius + 3
        for r in range(glow_r, self.radius, -1):
            a = int(alpha * (glow_r - r) / (glow_r - self.radius) * 0.4)
            pygame.draw.circle(s, (*PINK[:3], max(10, a)), (center, center), r)

        core_color = tuple(int(c * pulse) for c in PINK)
        pygame.draw.circle(s, (*core_color[:3], alpha), (center, center), self.radius)

        highlight_offset = int(self.radius * 0.25)
        hl_r = max(2, self.radius // 3)
        pygame.draw.circle(s, (255, 255, 255, int(100 * pulse)), (center - highlight_offset, center - highlight_offset), hl_r)

        surface.blit(s, (int(self.x) - center, int(self.y) - center))


class Player:
    def __init__(self):
        self.x = PLAY_WIDTH // 2
        self.y = CONTEXT_Y - 60
        self.hitbox_radius = 4
        self.visual_radius = 16
        self.speed = PLAYER_SPEED
        self.shoot_cooldown = 0
        self.shoot_delay = 0.12
        self.lives = INITIAL_LIVES
        self.life_percent = 0.0
        self.invincible_timer = 0
        self.pulse_time = 0

    def update(self, dt, keys):
        self.pulse_time += dt
        dx = 0
        dy = 0
        if keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_DOWN]:
            dy += 1
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707
        self.x += dx * self.speed * dt * 60
        self.y += dy * self.speed * dt * 60
        self.x = max(self.visual_radius + 5, min(PLAY_WIDTH - self.visual_radius - 5, self.x))
        self.y = max(30, min(CONTEXT_Y - 20, self.y))
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
        if self.invincible_timer > 0:
            self.invincible_timer -= dt

    def can_shoot(self):
        return self.shoot_cooldown <= 0

    def shoot(self):
        self.shoot_cooldown = self.shoot_delay
        return PlayerBullet(self.x, self.y - self.visual_radius)

    def hit(self):
        if self.invincible_timer > 0:
            return False
        self.lives -= 1
        self.invincible_timer = INVINCIBLE_DURATION
        return True

    def add_life_fragment(self, value):
        self.life_percent += value
        if self.life_percent >= 1.0:
            self.lives += 1
            self.life_percent -= 1.0

    def is_dead(self):
        return self.lives < 0

    def draw(self, surface):
        if self.invincible_timer > 0 and int(self.invincible_timer * 8) % 2 == 0:
            pass
        else:
            pulse = abs(math.sin(self.pulse_time * 4)) * 0.3 + 0.7
            glow = tuple(int(c * pulse) for c in CYAN)
            points = [
                (self.x, self.y - self.visual_radius - 4),
                (self.x - self.visual_radius - 2, self.y + self.visual_radius + 2),
                (self.x + self.visual_radius + 2, self.y + self.visual_radius + 2),
            ]
            pygame.draw.polygon(surface, glow, points)
            pygame.draw.polygon(surface, WHITE, points, 2)
            inner = [
                (self.x, self.y - self.visual_radius // 2),
                (self.x - self.visual_radius // 2, self.y + self.visual_radius // 2),
                (self.x + self.visual_radius // 2, self.y + self.visual_radius // 2),
            ]
            pygame.draw.polygon(surface, CYAN, inner)

        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.hitbox_radius)
        pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), max(1, self.hitbox_radius - 1))


class DanmakuAPI:
    def __init__(self, game):
        self.game = game

    def createBullet(self, color, velocity, angle, aimPlayer=False, gravity=0):
        bullet = EnemyBullet(
            0, 0, color, velocity, angle, aimPlayer,
            self.game.player.x, self.game.player.y, gravity
        )
        return bullet

    def fire_from(self, enemy, color, velocity, angle, aimPlayer=False, gravity=0):
        bullet = EnemyBullet(
            enemy.x, enemy.y, color, velocity, angle, aimPlayer,
            self.game.player.x, self.game.player.y, gravity
        )
        self.game.enemy_bullets.append(bullet)


def danmaku_function(api, enemy, rank):
    api.fire_from(enemy, YELLOW, 2.5 + rank * 0.2, 0, aimPlayer=True)
    if rank >= 2:
        api.fire_from(enemy, YELLOW, 2.2 + rank * 0.15, 8, aimPlayer=True)
        api.fire_from(enemy, YELLOW, 2.2 + rank * 0.15, -8, aimPlayer=True)
    if rank >= 4:
        api.fire_from(enemy, (255, 200, 50), 2.5 + rank * 0.12, 20, aimPlayer=True)
        api.fire_from(enemy, (255, 200, 50), 2.5 + rank * 0.12, -20, aimPlayer=True)


def danmaku_verb(api, enemy, rank):
    api.fire_from(enemy, ORANGE, 3.0 + rank * 0.2, 0, aimPlayer=True)
    api.fire_from(enemy, ORANGE, 2.5 + rank * 0.18, 6, aimPlayer=True)
    api.fire_from(enemy, ORANGE, 2.5 + rank * 0.18, -6, aimPlayer=True)
    if rank >= 3:
        for a in [-18, 0, 18]:
            api.fire_from(enemy, (255, 150, 50), 2.2 + rank * 0.15, a, aimPlayer=True)


def danmaku_noun(api, enemy, rank):
    count = 6 + rank * 2
    for i in range(count):
        angle = i * (360 / count) + random.uniform(-2, 2)
        api.fire_from(enemy, CYAN, 1.5 + rank * 0.12, angle)
    if rank >= 2:
        inner_count = 4 + rank // 2
        for i in range(inner_count):
            angle = i * (360 / inner_count) + (180 / inner_count) + random.uniform(-1, 1)
            api.fire_from(enemy, TEAL, 1.2 + rank * 0.08, angle)
    if rank >= 4:
        ring_r = 30
        for i in range(8 + rank):
            angle = i * (360 / (8 + rank))
            ax = math.cos(math.radians(angle)) * ring_r
            ay = math.sin(math.radians(angle)) * ring_r
            b = api.createBullet(CYAN, 1.3 + rank * 0.06, angle)
            b.x = enemy.x + ax
            b.y = enemy.y + ay
            api.game.enemy_bullets.append(b)


def danmaku_describer(api, enemy, rank):
    count = 5 + rank
    for i in range(count):
        angle = random.uniform(0, 360)
        speed = 1.0 + rank * 0.08 + random.uniform(-0.15, 0.15)
        api.fire_from(enemy, TEAL, speed, angle)
    if rank >= 2:
        spread_angle = 30 + rank * 2
        for a in range(int(-spread_angle), int(spread_angle) + 1, max(1, int(spread_angle / 4))):
            api.fire_from(enemy, (100, 220, 200), 1.5 + rank * 0.08, a)
    if rank >= 4:
        wave_t = pygame.time.get_ticks() / 300.0
        for i in range(10):
            base_a = i * (360 / 10)
            offset = math.sin(wave_t + i * 0.5) * 15
            api.fire_from(enemy, (80, 200, 180), 1.2 + rank * 0.06, base_a + offset)


def danmaku_response(api, enemy, rank):
    count = 4 + rank
    for _ in range(count):
        angle = random.uniform(0, 360)
        speed = 0.7 + rank * 0.04 + random.uniform(0, 0.3)
        api.fire_from(enemy, WHITE, speed, angle)


def danmaku_noise(api, enemy, rank):
    count = 8 + rank * 3
    for i in range(count):
        angle = random.uniform(160, 380)
        speed = 1.0 + rank * 0.1 + random.uniform(0, 0.5)
        g = 0.015 + rank * 0.003 + random.uniform(0, 0.01)
        api.fire_from(enemy, RED, speed, angle, gravity=g)
    burst = 2 + rank // 2
    for _ in range(burst):
        angle = random.uniform(0, 360)
        speed = 1.5 + rank * 0.15 + random.uniform(0, 0.4)
        api.fire_from(enemy, MAGENTA, speed, angle)
    if rank >= 3:
        rain_count = 5 + rank
        for _ in range(rain_count):
            angle = random.uniform(80, 100)
            speed = 0.6 + random.uniform(0, 0.7)
            api.fire_from(enemy, (255, 80, 80), speed, angle, gravity=0.02 + rank * 0.004)


DANMAKU_FUNCTIONS = {
    "function": danmaku_function,
    "verb": danmaku_verb,
    "noun": danmaku_noun,
    "describer": danmaku_describer,
    "response": danmaku_response,
    "noise": danmaku_noise,
}


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


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("TOKEN HELL · 令牌炼狱")
        self.clock = pygame.time.Clock()
        self.font_cache = {}
        self.llm_client = LLMClient()
        self.danmaku_api = DanmakuAPI(self)
        self.rank = 0
        self.state = "MENU"
        self.high_score = 0
        self.api_status = ""
        self.api_status_color = GRAY
        self.load_config_and_connect()
        self.reset_game()
        self.llm_pending = False
        self.llm_result = None
        self.llm_submitted_text = ""
        self.llm_result_ready = False
        self.llm_release_timer = 0
        self.popup_message = ""
        self.popup_timer = 0

    def load_config_and_connect(self):
        api_key = ""
        base_url = "https://api.openai.com/v1"
        model = "gpt-3.5-turbo"
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    cfg = json.load(f)
                api_key = cfg.get("api_key", "")
                base_url = cfg.get("base_url", "https://api.openai.com/v1")
                model = cfg.get("model", "gpt-3.5-turbo")
            except Exception:
                pass
        if api_key and HAS_OPENAI:
            success, msg = self.llm_client.configure(api_key, base_url, model)
            if success:
                self.api_status = f"LLM Connected | {model}"
                self.api_status_color = NEON_GREEN
            else:
                self.api_status = f"API Error: {msg[:40]}"
                self.api_status_color = RED
                self.llm_client.set_no_api()
        else:
            self.llm_client.set_no_api()
            if not api_key:
                self.api_status = "No API config (edit api_config.json)"
                self.api_status_color = ORANGE
            else:
                self.api_status = "openai package not installed"
                self.api_status_color = ORANGE

    def reset_game(self):
        self.player = Player()
        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.life_fragments = []
        self.particles = []
        self.candidate_words = []
        self.score = 0
        self.graze_count = 0
        self.rank = 0
        self.section_timer = SECTION_DURATION
        self.section_number = 0
        self.game_time = 0
        self.spawn_timer = 0
        self.response_queue = []
        self.response_drop_timer = 0
        self.llm_pending = False
        self.llm_result = None
        self.popup_message = ""
        self.popup_timer = 0

    def spawn_enemy(self, word=None, word_type=None, x=None, is_response=False):
        if word is None:
            roll = random.random()
            func_chance = 0.60
            verb_chance = 0.18
            noun_chance = 0.15
            if roll < func_chance:
                word = random.choice(HIGH_FREQ_WORDS)
                word_type = "function"
            elif roll < func_chance + verb_chance:
                word = random.choice(VERB_WORDS)
                word_type = "verb"
            elif roll < func_chance + verb_chance + noun_chance:
                word = random.choice(NOUN_WORDS)
                word_type = "noun"
            else:
                word = random.choice(DESCRIBER_WORDS)
                word_type = "describer"

        if x is None:
            x = random.randint(60, PLAY_WIDTH - 60)

        fall_speed = random.uniform(1.0, 2.0) + self.rank * 0.08
        enemy = EnemyWord(word, word_type, x, -20, fall_speed)
        if is_response:
            enemy.word_type = "response"
            enemy.color = WHITE
            enemy.fall_speed = 1.7
            enemy._drops_fragment = True
        self.enemies.append(enemy)

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
                    elif event.key == pygame.K_F5:
                        self.load_config_and_connect()
                elif self.state == "PLAYING":
                    pass
                elif self.state == "GAME_OVER":
                    if event.key == pygame.K_RETURN:
                        self.state = "MENU"
                    elif event.key == pygame.K_ESCAPE:
                        return False
        return True

    def submit_sentence(self):
        if self.llm_pending:
            return
        if not self.candidate_words:
            self.llm_result = {
                "success": True, "is_true": False,
                "response_words": [], "sentence": ""
            }
            return
        sentence = " ".join(w for w, _ in self.candidate_words)
        self.llm_submitted_text = sentence
        self.llm_pending = True
        self.llm_result = None

        def on_result(result):
            self.llm_result = result
            self.llm_pending = False

        self.llm_client.query(sentence, on_result)

    def process_llm_result(self):
        result = self.llm_result
        if result is None:
            return
        self.llm_result = None

        if not result["success"]:
            err = result.get("error", "")
            if err == "format_error":
                self.popup_message = f"Parse failed ({err}) - Treating as Not Coherent"
                self.popup_timer = 2.0
            else:
                self.popup_message = f"LLM Error: {err} - Using fallback"
                self.popup_timer = 3.0
                fallback_result = self.llm_client._fallback(result["sentence"])
                result = fallback_result

        if result["is_true"]:
            self.score += 100
            words = result["response_words"]
            self.popup_message = f"Accepted! +100 | Response: {' '.join(words[:5])}{'...' if len(words) > 5 else ''}"
            self.popup_timer = 2.5
            self._pending_response_words = words
        else:
            noise_count = 5 + self.rank
            self.popup_message = f"Not coherent! -{noise_count} noise words incoming!"
            self.popup_timer = 2.5
            self._pending_noise_count = noise_count

        self.llm_result_ready = True
        self.llm_release_timer = 1.5

    def update(self, dt):
        if self.popup_timer > 0:
            self.popup_timer -= dt

        if self.state != "PLAYING":
            return

        self.game_time += dt

        keys = pygame.key.get_pressed()
        self.player.update(dt, keys)

        if keys[pygame.K_z] and self.player.can_shoot():
            self.player_bullets.append(self.player.shoot())

        self.section_timer -= dt
        if self.section_timer <= 0:
            self.section_number += 1
            self.rank = self.section_number
            self.section_timer = SECTION_DURATION
            self.submit_sentence()

        if self.llm_result is not None:
            self.process_llm_result()

        if self.llm_result_ready:
            self.llm_release_timer -= dt
            if self.llm_release_timer <= 0:
                self.llm_result_ready = False
                self.candidate_words.clear()
                if hasattr(self, "_pending_response_words") and self._pending_response_words:
                    words = self._pending_response_words
                    if words:
                        margin = 80
                        usable_width = PLAY_WIDTH - 2 * margin
                        spacing = usable_width / (len(words) + 1)
                        for i, w in enumerate(words):
                            wx = margin + spacing * (i + 1)
                            self.response_queue.append({"word": w, "x": int(wx), "delay": 0})
                    self._pending_response_words = []
                elif hasattr(self, "_pending_noise_count") and self._pending_noise_count:
                    noise_count = self._pending_noise_count
                    for _ in range(noise_count):
                        self.spawn_enemy(word=generate_noise_word(), word_type="noise")
                    self._pending_noise_count = 0

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            spawn_interval = max(SPAWN_INTERVAL_MIN, SPAWN_INTERVAL_BASE - self.rank * 0.05)
            self.spawn_timer = spawn_interval
            self.spawn_enemy()

        if self.response_queue:
            self.response_drop_timer -= dt
            if self.response_drop_timer <= 0:
                item = self.response_queue.pop(0)
                self.spawn_enemy(word=item["word"], word_type="response", x=item["x"], is_response=True)
                self.response_drop_timer = RESPONSE_DROP_DELAY
                if not self.response_queue:
                    self.response_drop_timer = 0

        for enemy in self.enemies:
            enemy.update(dt)
            if enemy.has_fired and not enemy._fire_consumed:
                danmaku_fn = DANMAKU_FUNCTIONS.get(enemy.word_type, danmaku_noun)
                danmaku_fn(self.danmaku_api, enemy, self.rank)

        self.enemies = [e for e in self.enemies if e.alive]

        for bullet in self.player_bullets:
            bullet.update(dt)
        self.player_bullets = [b for b in self.player_bullets if b.alive]

        for bullet in self.enemy_bullets:
            bullet.update(dt)
        self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]

        for frag in self.life_fragments:
            frag.update(dt, self.player.x, self.player.y)
        self.life_fragments = [f for f in self.life_fragments if f.alive]

        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

        self.check_collisions()
        self.check_graze()

        if self.player.is_dead():
            self.high_score = max(self.high_score, int(self.score))
            self.state = "GAME_OVER"

    def check_collisions(self):
        for bullet in self.player_bullets:
            if not bullet.alive:
                continue
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                dx = bullet.x - enemy.x
                dy = bullet.y - enemy.y
                dist = math.sqrt(dx * dx + dy * dy)
                hit_r = enemy.get_hit_radius() + bullet.radius
                if dist < hit_r:
                    bullet.alive = False
                    enemy.hp -= 1
                    for _ in range(4):
                        self.particles.append(Particle(
                            enemy.x, enemy.y, enemy.color,
                            random.uniform(-2, 2), random.uniform(-2, 2), 15, 2
                        ))
                    if enemy.hp <= 0:
                        enemy.alive = False
                        if enemy.word_type == "response":
                            self.score += 50
                            frag = LifeFragment(enemy.x, enemy.y)
                            frag.value = 0.02
                            self.life_fragments.append(frag)
                        elif enemy.word_type == "noise":
                            pass
                        elif enemy.word_type in ("function", "verb", "noun", "describer"):
                            self.score += 20
                        for _ in range(8):
                            self.particles.append(Particle(
                                enemy.x, enemy.y, enemy.color,
                                random.uniform(-4, 4), random.uniform(-4, 4), 25, 3
                            ))
                    break

        pr = self.player
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            dx = pr.x - enemy.x
            dy = pr.y - enemy.y
            dist = math.sqrt(dx * dx + dy * dy)
            hit_r = enemy.get_hit_radius() + pr.hitbox_radius
            if dist < hit_r:
                enemy.alive = False
                if enemy.word_type == "noise":
                    self.score -= 10
                    self.candidate_words.append((enemy.word, enemy.word_type))
                elif enemy.word_type in ("function", "verb", "noun", "describer"):
                    self.score += 10
                    self.candidate_words.append((enemy.word, enemy.word_type))
                elif enemy.word_type == "response":
                    self.candidate_words.append((enemy.word, enemy.word_type))
                for _ in range(4):
                    self.particles.append(Particle(
                        enemy.x, enemy.y, enemy.color,
                        random.uniform(-2, 2), random.uniform(-2, 2), 15, 2
                    ))

        for frag in self.life_fragments:
            if not frag.alive:
                continue
            dx = pr.x - frag.x
            dy = pr.y - frag.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < frag.radius + pr.hitbox_radius + 10:
                frag.alive = False
                self.player.add_life_fragment(frag.value)
                for _ in range(6):
                    self.particles.append(Particle(
                        frag.x, frag.y, PINK,
                        random.uniform(-3, 3), random.uniform(-3, 3), 20, 2
                    ))

        if self.player.invincible_timer <= 0:
            for bullet in self.enemy_bullets:
                if not bullet.alive:
                    continue
                dx = pr.x - bullet.x
                dy = pr.y - bullet.y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < bullet.radius + pr.hitbox_radius:
                    if self.player.hit():
                        bullet.alive = False
                        for _ in range(15):
                            self.particles.append(Particle(
                                pr.x, pr.y, RED,
                                random.uniform(-5, 5), random.uniform(-5, 5), 30, 3
                            ))
                    break

    def check_graze(self):
        pr = self.player
        for bullet in self.enemy_bullets:
            if not bullet.alive or bullet.grazed:
                continue
            dx = pr.x - bullet.x
            dy = pr.y - bullet.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < GRAZE_DISTANCE + bullet.radius:
                bullet.grazed = True
                self.graze_count += 1
                self.score += 1
                for _ in range(2):
                    self.particles.append(Particle(
                        bullet.x, bullet.y, WHITE,
                        random.uniform(-1, 1), random.uniform(-1, 1), 10, 1
                    ))

    def draw_background(self):
        self.screen.fill(BG_COLOR)
        for x in range(0, PLAY_WIDTH, 50):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, CONTEXT_Y), 1)
        for y in range(0, CONTEXT_Y, 50):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (PLAY_WIDTH, y), 1)

    def draw_candidate_area(self):
        rect = pygame.Rect(8, CONTEXT_Y + 5, PLAY_WIDTH - 16, CONTEXT_HEIGHT - 10)
        pygame.draw.rect(self.screen, CONTEXT_BG, rect, border_radius=6)
        pygame.draw.rect(self.screen, CYAN, rect, 2, border_radius=6)

        if 13 not in self.font_cache:
            self.font_cache[13] = pygame.font.SysFont("consolas", 13)
        if 15 not in self.font_cache:
            self.font_cache[15] = pygame.font.SysFont("consolas", 15)
        if 11 not in self.font_cache:
            self.font_cache[11] = pygame.font.SysFont("consolas", 11)

        label = self.font_cache[13].render("SENTENCE CANDIDATE", True, CYAN)
        self.screen.blit(label, (rect.x + 10, rect.y + 6))

        section_label = f"SECTION {self.section_number}"
        sl = self.font_cache[13].render(section_label, True, NEON_GREEN)
        self.screen.blit(sl, (rect.x + rect.width // 2 - sl.get_width() // 2, rect.y + 4))

        bar_x = rect.x + 12
        bar_y = rect.y + 24
        bar_w = rect.width - 24
        bar_h = 8
        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        progress = max(0.0, min(1.0, self.section_timer / SECTION_DURATION))
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            bar_color = NEON_GREEN if progress > 0.3 else (YELLOW if progress > 0.15 else RED)
            pygame.draw.rect(self.screen, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=3)
        time_text = f"{int(self.section_timer)}s"
        ttl = self.font_cache[11].render(time_text, True, WHITE)
        self.screen.blit(ttl, (rect.x + rect.width - ttl.get_width() - 14, rect.y + 25))

        words_y = rect.y + 40
        words_x = rect.x + 12
        max_x = rect.x + rect.width - 12

        for word, wtype in self.candidate_words:
            if wtype == "function":
                color = YELLOW
            elif wtype == "verb":
                color = ORANGE
            elif wtype == "noun":
                color = CYAN
            elif wtype == "describer":
                color = TEAL
            elif wtype == "response":
                color = NEON_GREEN
            elif wtype == "noise":
                color = RED
            else:
                color = GRAY

            word_surf = self.font_cache[15].render(word, True, color)
            if words_x + word_surf.get_width() > max_x:
                words_x = rect.x + 12
                words_y += 22
                if words_y > rect.y + rect.height - 30:
                    more = self.font_cache[11].render("...", True, GRAY)
                    self.screen.blit(more, (words_x, words_y))
                    break
            self.screen.blit(word_surf, (words_x, words_y))
            words_x += word_surf.get_width() + 8

        if self.llm_pending or self.llm_result_ready:
            overlay = pygame.Surface((rect.width - 16, rect.height - 50), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(120 * (abs(math.sin(pygame.time.get_ticks() / 200.0)) * 0.5 + 0.5))))
            self.screen.blit(overlay, (rect.x + 8, rect.y + 38))
            if self.llm_pending:
                proc_text = ">>> LLM PROCESSING... <<<"
                proc_color = YELLOW
            else:
                proc_text = ">>> RESULT READY <<<"
                proc_color = NEON_GREEN
            proc_surf = self.font_cache[15].render(proc_text, True, proc_color)
            pr = proc_surf.get_rect(center=(rect.x + rect.width // 2, rect.y + rect.height // 2 + 10))
            self.screen.blit(proc_surf, pr)

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
        if 18 not in self.font_cache:
            self.font_cache[18] = pygame.font.SysFont("consolas", 18)

        title = self.font_cache[16].render("TOKEN HELL", True, CYAN)
        self.screen.blit(title, (PANEL_X + 25, 12))
        pygame.draw.line(self.screen, DARK_GRAY, (PANEL_X + 10, 35), (PANEL_X + PANEL_WIDTH - 10, 35), 1)

        ly = 50
        lives_label = self.font_cache[13].render("LIVES", True, GRAY)
        self.screen.blit(lives_label, (PANEL_X + 25, ly))

        for i in range(self.player.lives + 1):
            hx = PANEL_X + 25 + i * 28
            hy = ly + 20
            self._draw_heart(hx, hy, 10, HEART_RED)

        life_bar_x = PANEL_X + 25
        life_bar_y = ly + 40
        life_bar_w = 200
        life_bar_h = 10
        pygame.draw.rect(self.screen, DARK_GRAY, (life_bar_x, life_bar_y, life_bar_w, life_bar_h), border_radius=4)
        fill_w = int(life_bar_w * self.player.life_percent)
        if fill_w > 0:
            pygame.draw.rect(self.screen, PINK, (life_bar_x, life_bar_y, fill_w, life_bar_h), border_radius=4)
        pygame.draw.rect(self.screen, WHITE, (life_bar_x, life_bar_y, life_bar_w, life_bar_h), 1, border_radius=4)
        pct_label = self.font_cache[11].render(f"{int(self.player.life_percent * 100)}%", True, WHITE)
        self.screen.blit(pct_label, (life_bar_x + life_bar_w + 5, life_bar_y - 1))

        sy = 120
        sl = self.font_cache[13].render("SCORE", True, GRAY)
        self.screen.blit(sl, (PANEL_X + 25, sy))
        sv = self.font_cache[22].render(f"{int(self.score)}", True, WHITE)
        self.screen.blit(sv, (PANEL_X + 25, sy + 18))

        gl = self.font_cache[11].render(f"GRAZE: {self.graze_count}", True, WHITE)
        self.screen.blit(gl, (PANEL_X + 25, sy + 48))

        rl = self.font_cache[11].render(f"RANK: {self.rank}", True, ORANGE)
        self.screen.blit(rl, (PANEL_X + 25, sy + 64))

        tl = self.font_cache[11].render(f"TIME: {int(self.game_time)}s", True, GRAY)
        self.screen.blit(tl, (PANEL_X + 25, sy + 80))

        sec_l = self.font_cache[11].render(f"SECTION: {self.section_number}", True, CYAN)
        self.screen.blit(sec_l, (PANEL_X + 25, sy + 96))

        if self.high_score > 0:
            hsl = self.font_cache[11].render(f"HIGH: {self.high_score}", True, YELLOW)
            self.screen.blit(hsl, (PANEL_X + 25, sy + 120))

        pygame.draw.line(self.screen, DARK_GRAY, (PANEL_X + 10, sy + 140), (PANEL_X + PANEL_WIDTH - 10, sy + 140), 1)

        cy = sy + 150
        controls = [
            ("Arrows", "Move"),
            ("Z", "Shoot"),
            ("Auto", "Submit per Section"),
        ]
        ctl = self.font_cache[11].render("CONTROLS", True, GRAY)
        self.screen.blit(ctl, (PANEL_X + 25, cy))
        for i, (key, desc) in enumerate(controls):
            kl = self.font_cache[11].render(f"{key}", True, CYAN)
            dl = self.font_cache[11].render(f" {desc}", True, DARK_GRAY)
            self.screen.blit(kl, (PANEL_X + 25, cy + 16 + i * 14))
            self.screen.blit(dl, (PANEL_X + 25 + kl.get_width(), cy + 16 + i * 14))

        pygame.draw.line(self.screen, DARK_GRAY, (PANEL_X + 10, cy + 60), (PANEL_X + PANEL_WIDTH - 10, cy + 60), 1)

        wy = cy + 70
        wl = self.font_cache[13].render("WORD TYPES", True, GRAY)
        self.screen.blit(wl, (PANEL_X + 25, wy))
        types_info = [
            ("High-Freq", YELLOW, "Aimed bullet"),
            ("Misc", CYAN, "Flower pattern"),
            ("Response", NEON_GREEN, "Slow aimed"),
            ("Noise", RED, "Hard pattern"),
        ]
        for i, (name, color, desc) in enumerate(types_info):
            nl = self.font_cache[11].render(f"{name}", True, color)
            dl = self.font_cache[11].render(f" {desc}", True, DARK_GRAY)
            self.screen.blit(nl, (PANEL_X + 25, wy + 18 + i * 14))
            self.screen.blit(dl, (PANEL_X + 25 + nl.get_width(), wy + 18 + i * 14))

        if self.llm_client.available:
            mode_l = self.font_cache[11].render("API: Connected", True, NEON_GREEN)
        elif self.llm_client.no_api_mode:
            mode_l = self.font_cache[11].render("API: No-API mode", True, ORANGE)
        else:
            mode_l = self.font_cache[11].render("API: Not configured", True, RED)
        self.screen.blit(mode_l, (PANEL_X + 25, SCREEN_HEIGHT - 30))

    def _draw_heart(self, x, y, size, color):
        points = []
        for angle_deg in range(360):
            angle = math.radians(angle_deg)
            t = angle
            hx = 16 * math.sin(t) ** 3
            hy = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
            points.append((x + hx * size / 16, y + hy * size / 16))
        if len(points) > 2:
            pygame.draw.polygon(self.screen, color, points)

    def draw_popup(self):
        if self.popup_timer <= 0:
            return
        if 16 not in self.font_cache:
            self.font_cache[16] = pygame.font.SysFont("consolas", 16)
        alpha = min(1.0, self.popup_timer / 1.0)
        overlay = pygame.Surface((PLAY_WIDTH, 40), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(180 * alpha)))
        self.screen.blit(overlay, (0, SCREEN_HEIGHT // 2 - 20))
        msg_surf = self.font_cache[16].render(self.popup_message, True, YELLOW)
        msg_rect = msg_surf.get_rect(center=(PLAY_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(msg_surf, msg_rect)

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
        if 13 not in self.font_cache:
            self.font_cache[13] = pygame.font.SysFont("consolas", 13)

        t = pygame.time.get_ticks() / 1000.0
        cx = SCREEN_WIDTH // 2

        title1 = self.font_cache[52].render("TOKEN HELL", True, CYAN)
        title2 = self.font_cache[26].render("Token Danmaku Survival", True, NEON_GREEN)
        self.screen.blit(title1, (cx - title1.get_width() // 2, 100))
        self.screen.blit(title2, (cx - title2.get_width() // 2, 165))

        status_rect = pygame.Rect(cx - 280, 200, 560, 32)
        status_bg = (*self.api_status_color[:3], 25)
        status_surf = pygame.Surface((status_rect.width, status_rect.height), pygame.SRCALPHA)
        status_surf.fill(status_bg)
        pygame.draw.rect(status_surf, self.api_status_color, (0, 0, status_rect.width, status_rect.height), 2, border_radius=4)
        self.screen.blit(status_surf, status_rect.topleft)

        mode_label = "LLM MODE" if self.llm_client.available else "FALLBACK MODE"
        mode_color = NEON_GREEN if self.llm_client.available else ORANGE
        mode_text = self.font_cache[14].render(mode_label, True, mode_color)
        self.screen.blit(mode_text, (status_rect.x + 12, status_rect.y + 8))

        detail = self.font_cache[13].render(self.api_status, True, WHITE)
        self.screen.blit(detail, (status_rect.x + status_rect.width - detail.get_width() - 12, status_rect.y + 9))

        sub = self.font_cache[18].render(
            "Eat words to build sentences. Shoot to destroy. Survive the danmaku!", True, YELLOW
        )
        self.screen.blit(sub, (cx - sub.get_width() // 2, 245))

        pygame.draw.line(self.screen, DARK_GRAY, (cx - 300, 280), (cx + 300, 280), 1)

        instructions = [
            ("HOW TO PLAY", CYAN),
            ("Arrow keys to move, Z to shoot", WHITE),
            ("Collide with words to EAT them into your sentence", WHITE),
            ("Shoot words to DESTROY them (4 hits to kill)", WHITE),
            ("Each Section auto-submits your sentence to LLM", WHITE),
            ("", GRAY),
            ("SCORING", CYAN),
            ("LLM accepts sentence: +100, Response word destroyed: +50", WHITE),
            ("Normal word eaten: +10, Normal word destroyed: +20", WHITE),
            ("Noise word eaten: -10, Graze bullet: +1", WHITE),
            ("", GRAY),
            ("DANMAKU", CYAN),
            ("High-freq words: aimed bullet | Misc words: flower pattern", WHITE),
            ("Response words: slow aimed | Noise words: hard pattern", RED),
            ("", GRAY),
            ("LIFE SYSTEM", CYAN),
            ("2 extra lives (hearts). Collect fragments to heal!", PINK),
        ]

        for i, (line, color) in enumerate(instructions):
            if line:
                text = self.font_cache[14].render(line, True, color)
                self.screen.blit(text, (cx - text.get_width() // 2, 300 + i * 20))

        pulse = abs(math.sin(t * 2.5)) * 0.5 + 0.5
        sc = tuple(int(c * pulse) for c in CYAN)
        start = self.font_cache[26].render("PRESS ENTER TO START", True, sc)
        self.screen.blit(start, (cx - start.get_width() // 2, 640))

        if self.high_score > 0:
            hs = self.font_cache[18].render(f"HIGH SCORE: {self.high_score}", True, YELLOW)
            self.screen.blit(hs, (cx - hs.get_width() // 2, 690))

        if self.llm_client.available:
            ms, mc = f"API: {self.llm_client.model}", NEON_GREEN
        elif self.llm_client.no_api_mode:
            ms, mc = "No-API mode (fallback scoring)", ORANGE
        else:
            ms, mc = "API not configured", RED
        mt = self.font_cache[12].render(ms, True, mc)
        self.screen.blit(mt, (cx - mt.get_width() // 2, 730))

        esc = self.font_cache[12].render("ESC: Quit | F5: Reload API config", True, DARK_GRAY)
        self.screen.blit(esc, (cx - esc.get_width() // 2, 760))

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

        cx = SCREEN_WIDTH // 2

        go = self.font_cache[44].render("GAME OVER", True, RED)
        self.screen.blit(go, (cx - go.get_width() // 2, 180))

        sub = self.font_cache[16].render("All lives lost. The danmaku was too strong.", True, ORANGE)
        self.screen.blit(sub, (cx - sub.get_width() // 2, 240))

        pygame.draw.line(self.screen, DARK_GRAY, (cx - 200, 275), (cx + 200, 275), 1)

        stats = [
            (f"Final Score: {int(self.score)}", WHITE),
            (f"Survived: {int(self.game_time)}s", GRAY),
            (f"Rank Reached: {self.rank}", ORANGE),
            (f"Sections Completed: {self.section_number}", CYAN),
            (f"Graze Count: {self.graze_count}", WHITE),
        ]

        for i, (text, color) in enumerate(stats):
            s = self.font_cache[16].render(text, True, color)
            self.screen.blit(s, (cx - s.get_width() // 2, 295 + i * 28))

        if self.score >= self.high_score and self.score > 0:
            nh = self.font_cache[22].render("NEW HIGH SCORE!", True, YELLOW)
            self.screen.blit(nh, (cx - nh.get_width() // 2, 460))

        t = pygame.time.get_ticks() / 1000.0
        pulse = abs(math.sin(t * 2.5)) * 0.5 + 0.5
        rc = tuple(int(c * pulse) for c in CYAN)
        restart = self.font_cache[16].render("PRESS ENTER TO RESTART", True, rc)
        self.screen.blit(restart, (cx - restart.get_width() // 2, 510))

    def draw(self):
        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "PLAYING":
            self.draw_background()
            for enemy in self.enemies:
                enemy.draw(self.screen, self.font_cache)
            for bullet in self.player_bullets:
                bullet.draw(self.screen)
            for bullet in self.enemy_bullets:
                bullet.draw(self.screen)
            for frag in self.life_fragments:
                frag.draw(self.screen, self.font_cache)
            for p in self.particles:
                p.draw(self.screen)
            self.player.draw(self.screen)
            self.draw_candidate_area()
            self.draw_panel()
            self.draw_popup()
        elif self.state == "GAME_OVER":
            self.draw_background()
            for enemy in self.enemies:
                enemy.draw(self.screen, self.font_cache)
            for bullet in self.enemy_bullets:
                bullet.draw(self.screen)
            self.player.draw(self.screen)
            self.draw_candidate_area()
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
