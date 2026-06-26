# full script with drag + resize fixes (replace your current file with this)

import pygame
import sys
import datetime
import os
import random
import glob
import json
import time
import multiprocessing
from multiprocessing import Queue
from pygame import gfxdraw
import math
from utility import * # Import all helper functions
pygame.mixer.pre_init(44100, -16, 2, 2048) # Ensure high quality audio
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1000, 700
MIN_WIDTH, MIN_HEIGHT = 800, 600

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Foci : focus without losing time")
try:
    app_icon = pygame.image.load(resource_path(os.path.join("assets", "icon.ico")))
    pygame.display.set_icon(app_icon)
except Exception as e:
    print(f"Could not load window icon: {e}")

lofi_on = False

ASSETS_DIR = resource_path("assets")

try:
    BACKGROUND_IMAGE = pygame.image.load(
        os.path.join(ASSETS_DIR, "background.jpg")
    ).convert()
    BACKGROUND_IMAGE = pygame.transform.scale(BACKGROUND_IMAGE, (WIDTH, HEIGHT))
except Exception:
    BACKGROUND_IMAGE = pygame.Surface((WIDTH, HEIGHT))
    BACKGROUND_IMAGE.fill((245, 245, 250))

START_HOUR = 5  # Will be loaded from settings
END_HOUR = 23  # Will be loaded from settings

CHECKBOX_SIZE = 16
CHECKBOX_MARGIN = 12
HOUR_HEIGHT = 40  # Default, will be loaded from settings
TOP_Y = 120
TODO_WIDTH = 250
TIMELINE_GUTTER = 60  # Space for the hour markers
EVENT_X = TODO_WIDTH + TIMELINE_GUTTER
EVENT_RIGHT_MARGIN = 20

# --- Font Cache ---
font_cache = {}

# --- Colors ---
WHITE = (255, 255, 255)
BLUE = (0, 120, 215)
GRAY = (230, 230, 230)
BLACK = (0, 0, 0)
LIGHT_BLUE = (200, 220, 255)
EVENT_COLOR = (255, 220, 120)
EVENT_DONE_COLOR = (120, 220, 120)
PARTICLE_COLORS = [(120, 220, 120), (255, 255, 120), (180, 255, 180), (200, 255, 200)]

DING_SOUND = None
if os.path.exists(os.path.join(ASSETS_DIR, "ding.wav")):
    try:
        DING_SOUND = pygame.mixer.Sound(resource_path(os.path.join(ASSETS_DIR, "ding.wav")))
    except:
        DING_SOUND = None


# Wrapper to maintain simple `get_font(size)` call in main.py
def get_font_wrapper(size):
    return get_font(font_cache, settings.get("font_path"), size)

EVENT_ICONS = []
for i in range(6):
    try:
        EVENT_ICONS.append(
            pygame.image.load(resource_path(os.path.join(ASSETS_DIR, f"icon_{i}.png"))).convert_alpha()
        )
    except:
        EVENT_ICONS.append(None)

# Extended symbol collection (Lucide, ISC licensed) downloaded into
# assets/symbols/. Curated study/focus order; appended so the original six
# icon indices stay stable for existing saved events.
SYMBOL_ICON_NAMES = [
    "book-open", "graduation-cap", "brain", "calculator", "flask-conical",
    "atom", "code", "pencil", "music", "coffee", "dumbbell", "heart",
    "star", "clock", "target", "flame", "leaf", "lightbulb",
    "check-check", "calendar", "bell", "trophy", "rocket", "moon",
]
for _name in SYMBOL_ICON_NAMES:
    try:
        EVENT_ICONS.append(
            pygame.image.load(
                resource_path(os.path.join(ASSETS_DIR, "symbols", f"{_name}.png"))
            ).convert_alpha()
        )
    except Exception:
        pass  # Skip any symbol that isn't present rather than adding a blank slot

try:
    SETTINGS_ICON = pygame.image.load(
        os.path.join(ASSETS_DIR, "settings.png")
    ).convert_alpha()
    SETTINGS_ICON = pygame.transform.smoothscale(SETTINGS_ICON, (36, 36))
except:
    SETTINGS_ICON = pygame.Surface((36, 36))
    SETTINGS_ICON.fill((200, 200, 200))

MUSIC_DIR = os.path.join(ASSETS_DIR, "music")
MUSIC_FILES = []
if os.path.exists(MUSIC_DIR):
    for ext in ("*.mp3", "*.wav"):
        MUSIC_FILES.extend(glob.glob(os.path.join(MUSIC_DIR, ext)))

currently_playing_index = -1

if MUSIC_FILES:
    pygame.mixer.music.set_volume(0.5)
confetti_particles = []
CONFETTI_COLORS = [
    (124, 250, 70),  # bright green
    (180, 255, 180),  # pastel green
    (255, 255, 150),  # light yellow
    (200, 220, 255),  # soft blue
    (255, 105, 97),  # red
    (255, 179, 71),  # orange
    (255, 140, 203),  # pink
    (186, 85, 211),  # purple
    (30, 144, 255),  # dodger blue
    (255, 215, 0),  # gold
    (0, 191, 255),  # sky blue
    (152, 251, 152),  # pale green
    (255, 99, 71),  # tomato red
    (238, 130, 238),  # violet
    (255, 182, 193),  # light pink
    (135, 206, 250),  # light sky blue
    (255, 250, 205),  # lemon chiffon
    (221, 160, 221),  # plum
    (189, 224, 254),  # light blue
    (162, 210, 255),  # lavender
    (255, 200, 221),  # light rose
    (208, 180, 249),  # lavender purple
    (181, 234, 215),  # mint green
    (255, 228, 225),  # misty rose
    (255, 240, 245),  # lavender blush
    (219, 112, 147),  # pale violet red
    (255, 192, 203),  # pink
    (255, 105, 97),  # red
    (255, 179, 71),  # orange
    (255, 140, 203),  # pink
    (186, 85, 211),  # purple
    (30, 144, 255),  # dodger blue
    (255, 215, 0),  # gold
    (0, 191, 255),  # sky blue
    (152, 251, 152),  # pale green
    (255, 99, 71),  # tomato red
    (238, 130, 238),  # violet
    (255, 182, 193),  # light pink
    
]

THEMES = {
    "Serene Morning": {
        "background": (235, 240, 255), # Light lavender blue
        "text": (50, 50, 80),
        "event_done_color": (180, 220, 200),
        "event_dimmed": (210, 215, 230),
        "hour_line": (200, 210, 230),
        "title_color": (80, 90, 130),
        "progress_bar": (100, 149, 237), # Cornflower Blue
        "current_event_dim": (173, 216, 230), # Light Blue
        "settings_bg": (250, 250, 255),
        "todo_bg": (220, 225, 240),
        "todo_item_bg": (240, 245, 255),
        "todo_item_hover": (230, 235, 250),
        "button_bg": (210, 220, 240),
        "gradient_start": (209, 190, 247),
        "gradient_end": (162, 210, 255),
        "use_gradient_bg": True,
        "color_choices": [
            (173, 216, 230), # Light Blue
            (255, 204, 204), # Soft Pink
            (181, 234, 215), # Mint Green
            (255, 229, 180), # Soft Peach
            (208, 180, 249), # Lavender
        ],
    },
    "Golden Hour": {
        "background": (255, 248, 238), # Creamy white
        "text": (90, 70, 50),
        "event_done_color": (210, 230, 200),
        "event_dimmed": (230, 220, 210),
        "hour_line": (240, 225, 205),
        "title_color": (218, 165, 32), # Goldenrod
        "progress_bar": (255, 165, 0), # Orange
        "current_event_dim": (255, 215, 0), # Gold
        "settings_bg": (255, 253, 250),
        "todo_bg": (255, 245, 230),
        "todo_item_bg": (255, 250, 245),
        "todo_item_hover": (255, 248, 240),
        "button_bg": (255, 235, 215),
        "gradient_start": (255, 228, 181), # Navaho White
        "gradient_end": (255, 160, 122), # Light Salmon
        "use_gradient_bg": True,
        "color_choices": [
            (255, 160, 122), # Light Salmon
            (240, 230, 140), # Khaki
            (152, 251, 152), # Pale Green
            (255, 182, 193), # Light Pink
            (176, 224, 230), # Powder Blue
        ],
    },
    "Midnight Deep": {
        "background": (23, 28, 42), # Very dark blue
        "text": (220, 225, 240),
        "event_done_color": (40, 50, 65),
        "event_dimmed": (50, 60, 80),
        "hour_line": (60, 70, 90),
        "title_color": (173, 216, 230), # Light Blue
        "progress_bar": (30, 144, 255), # Dodger Blue
        "current_event_dim": (0, 191, 255), # Deep Sky Blue
        "settings_bg": (30, 35, 50),
        "todo_bg": (28, 32, 48),
        "todo_item_bg": (40, 45, 65),
        "todo_item_hover": (50, 55, 75),
        "button_bg": (45, 50, 70),
        "use_gradient_bg": False,
        "color_choices": [
            (70, 130, 180),  # Steel Blue
            (106, 90, 205),  # Slate Blue
            (64, 224, 208),  # Turquoise
            (218, 112, 214), # Orchid
            (238, 130, 238), # Violet
        ],
    },
    "Cyberpunk Night": {
        "background": (10, 10, 25),
        "text": (225, 225, 255),
        "event_done_color": (30, 40, 50),
        "event_dimmed": (40, 50, 70),
        "hour_line": (255, 0, 255), # Magenta
        "title_color": (0, 255, 255), # Cyan
        "progress_bar": (255, 255, 0), # Yellow
        "current_event_dim": (0, 255, 0), # Lime
        "settings_bg": (20, 20, 40),
        "todo_bg": (15, 15, 30),
        "todo_item_bg": (25, 25, 50),
        "todo_item_hover": (35, 35, 65),
        "button_bg": (40, 40, 70),
        "use_gradient_bg": False,
        "color_choices": [
            (255, 0, 255),   # Magenta
            (0, 255, 255),   # Cyan
            (255, 255, 0),   # Yellow
            (255, 105, 180), # Hot Pink
            (0, 255, 0),     # Lime
        ],
    },
    "Forest Canopy": {
        "background": (240, 255, 240), # Honeydew
        "text": (30, 60, 40),
        "event_done_color": (180, 210, 180),
        "event_dimmed": (210, 230, 210),
        "hour_line": (180, 220, 180),
        "title_color": (34, 139, 34), # Forest Green
        "progress_bar": (50, 205, 50), # Lime Green
        "current_event_dim": (144, 238, 144), # Light Green
        "settings_bg": (250, 255, 250),
        "todo_bg": (230, 250, 230),
        "todo_item_bg": (245, 255, 245),
        "todo_item_hover": (235, 250, 235),
        "button_bg": (220, 240, 220),
        "gradient_start": (189, 252, 201), # Pale Green
        "gradient_end": (144, 238, 144), # Light Green
        "use_gradient_bg": True,
        "color_choices": [
            (143, 188, 143), # Dark Sea Green
            (135, 206, 235), # Sky Blue
            (245, 222, 179), # Wheat
            (255, 250, 205), # Lemon Chiffon
            (216, 191, 216), # Thistle
        ],   },
    
    "Classic Light": {
        "background": (255, 255, 255),
        "text": (0, 0, 0),
        "event_done_color": (220, 220, 220),
        "event_dimmed": (200, 200, 200),
        "hour_line": (230, 230, 230),
        "title_color": (0, 0, 0),
        "progress_bar": (0, 120, 215),
        "current_event_dim": (59, 255, 111),
        "settings_bg": (245, 245, 255),
        "todo_bg": (240, 240, 240),
        "todo_item_bg": (255, 255, 255),
        "todo_item_hover": (248, 248, 255),
        "button_bg": (220, 220, 220),
        "use_gradient_bg": False,
        "color_choices": [
            (255, 182, 193), # Light Pink
            (135, 206, 250), # Light Sky Blue
            (152, 251, 152), # Pale Green
            (255, 250, 205), # Lemon Chiffon
            (221, 160, 221), # Plum

        ],
        },
    "Classic Dark": {
        "background": (30, 30, 30),
        "text": (255, 255, 255),
        "event_done_color": (180, 180, 180),
        "event_dimmed": (150, 150, 150),
        "hour_line": (80, 80, 80),  
        "title_color": (255, 255, 255),
        "progress_bar": (0, 120, 215),
        "current_event_dim": (59, 255, 111),
        "settings_bg": (50, 50, 50),
        "todo_bg": (40, 40, 40),
        "todo_item_bg": (30, 30, 30),
        "todo_item_hover": (20, 20, 20),
        "button_bg": (70, 70, 70),
        "use_gradient_bg": False,
        "color_choices": [
            (135, 206, 235), # Light Sky Blue
            (255, 182, 193), # Light Pink
            (152, 251, 152), # Pale Green
            (255, 250, 205), # Lemon Chiffon
            (221, 160, 221), # Plum
        ],
    },    
    "Kyoto Spring": {
        "background": (255, 249, 249), # Off-white with a hint of pink
        "text": (80, 60, 70),
        "event_done_color": (210, 230, 220),
        "event_dimmed": (230, 225, 225),
        "hour_line": (220, 210, 215),
        "title_color": (219, 112, 147), # Pale Violet Red
        "progress_bar": (255, 182, 193), # Light Pink
        "current_event_dim": (255, 204, 204),
        "settings_bg": (255, 252, 252),
        "todo_bg": (255, 240, 245),
        "todo_item_bg": (255, 245, 248),
        "todo_item_hover": (255, 240, 242),
        "button_bg": (255, 230, 235),
        "gradient_start": (255, 228, 225), # Misty Rose
        "gradient_end": (255, 192, 203), # Pink
        "use_gradient_bg": True,
        "color_choices": [
            (255, 182, 193), # Light Pink
            (255, 228, 225), # Misty Rose
            (255, 240, 245), # Lavender Blush
            (219, 112, 147), # Pale Violet Red
            (255, 192, 203), # Pink
        ],
    },
    }
    
current_theme = "Serene Morning"

AVAILABLE_FONTS = find_fonts(ASSETS_DIR)

def set_theme(name):
    global current_theme, THEME
    current_theme = name
    THEME = THEMES[name]


set_theme(current_theme)

SETTINGS_FILE = f"{ASSETS_DIR}/settings.json"

# Default settings
settings = {
    "theme": "Serene Morning",
    "start_hour": 5,
    "end_hour": 23,
    "sounds_on": True,
    "hour_height": 40,
    "confetti_on": True,
    "font_path": os.path.join(ASSETS_DIR, "Domine.ttf"),
}


def load_settings():
    global settings, START_HOUR, END_HOUR, current_theme, HOUR_HEIGHT
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                loaded_settings = json.load(f)
                settings.update(loaded_settings)  # Update defaults with loaded values
        except (json.JSONDecodeError, TypeError):
            print("Warning: Could not read settings.json. Using defaults.")

    # Ensure a default font path is set if not in settings
    if "font_path" not in settings:
        settings["font_path"] = resource_path(os.path.join(ASSETS_DIR, "Domine.ttf"))

    set_theme(settings["theme"])
    START_HOUR = settings["start_hour"]
    END_HOUR = settings["end_hour"]
    HOUR_HEIGHT = settings["hour_height"]


def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


DATA_FILE = resource_path(os.path.join(ASSETS_DIR, "events.json"))
TODO_FILE = resource_path(os.path.join(ASSETS_DIR, "todos.json"))
all_events = {}
events = []
todos = []
selected_date = datetime.date.today()
user_coins = 0
active_quotes = [] # For the new non-blocking quote system

# --- Coin Animation State ---
coin_sprite_sheet = None
coin_animation = {
    "frames_per_row": 5,  # As per your request
    "num_rows": 1,          # Number of coin types (e.g., gold, silver, bronze)
    "current_coin_type": 0, # The row to animate (0 for gold, 1 for silver, etc.)
    "current_frame": 0,
    "frame_width": 0,
    "frame_height": 0,
    "last_update": 0,
    "frame_rate": 120,      # milliseconds per frame (a bit slower can look better)
}
animating_out = {}  # For check-off animations
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def load_todos():
    global todos
    if os.path.exists(TODO_FILE):
        try:
            with open(TODO_FILE, "r", encoding="utf-8") as f:
                todos = json.load(f)
        except (json.JSONDecodeError, TypeError):
            todos = []
    else:
        todos = []

    # Update tags for items scheduled on previous days
    today = datetime.date.today()
    for todo in todos:
        if todo.get("tag") == "today" and "date" in todo:
            try:
                todo_date = datetime.datetime.strptime(todo["date"], "%Y-%m-%d").date()
                if todo_date < today:
                    todo["tag"] = f"on {todo_date.strftime('%a')}"
            except (ValueError, TypeError):
                continue  # Ignore if date is malformed
        elif todo.get("tag") == "tmr" and "date" in todo:
            try:
                todo_date = datetime.datetime.strptime(todo["date"], "%Y-%m-%d").date()
                if todo_date < today:
                    todo["tag"] = f"on {todo_date.strftime('%a')}"
            except (ValueError, TypeError):
                continue  # Ignore if date is malformed

            if todo_date == today:
                todo["tag"] = "today"


def save_todos():
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2)
    # After saving, reload to re-apply sorting logic
    load_todos()


def load_events():
    global all_events, events, user_coins
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            all_events = json.load(f)
    else:
        all_events = {}
    
    date_str = selected_date.strftime("%Y-%m-%d")
    events.clear()

    if date_str in all_events:
        events.extend(all_events[date_str])
    
    # Load coins from a separate simple file
    try:
        with open(resource_path(os.path.join(ASSETS_DIR, "player_data.json")), "r") as f:
            player_data = json.load(f)
            user_coins = player_data.get("coins", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        user_coins = 0


def load_coin_animation():
    """Loads the coin sprite sheet and initializes animation parameters."""
    global coin_sprite_sheet, coin_animation
    try:
        # Assuming the sprite sheet is in assets/coins/
        # Let's use a generic name. Please rename your sprite sheet to this.
        sprite_sheet_path = resource_path(os.path.join(ASSETS_DIR, "coins", "coins_all.png"))
        coin_sprite_sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
        
        # Calculate frame dimensions based on rows and columns
        coin_animation["frame_width"] = coin_sprite_sheet.get_width() // coin_animation["frames_per_row"]
        coin_animation["frame_height"] = coin_sprite_sheet.get_height() // coin_animation["num_rows"]
        coin_animation["last_update"] = pygame.time.get_ticks()
    except Exception as e:
        print(f"Could not load coin animation sprite sheet: {e}")


def save_events():
    date_str = selected_date.strftime("%Y-%m-%d")
    all_events[date_str] = events
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)


def get_event_at_time(hour, minute):
    for event in events:
        eh, em = event["hour"], event.get("minute", 0)
        dur = event.get("duration", 60)
        start = eh * 60 + em
        end = start + dur
        t = hour * 60 + minute
        if start <= t < end:
            return event
    return None


def get_current_event():
    now = datetime.datetime.now()
    if selected_date == datetime.date.today():
        return get_event_at_time(now.hour, now.minute)
    return None


def spawn_confetti(x, y):
    for _ in range(80):  # Create 80 particles
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(7, 16)  # Much faster initial explosion
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed - 4  # Stronger upward pop
        confetti_particles.append(
            {
                "x": x,
                "y": y,
                "vx": vx,
                "vy": vy,
                "type": random.choice(["rect", "circle"]),
                "w": random.randint(8, 15),
                "h": random.randint(4, 8),
                "color": random.choice(CONFETTI_COLORS),
                "life": random.randint(40, 60),  # lifespan for a quicker effect
                "angle": random.uniform(0, 360),
                "angle_speed": random.uniform(-44, 44),
            }
        )


def update_confetti():
    for p in confetti_particles:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.4  # gravity
        p["vx"] *= 0.98  # A bit more air resistance to control the burst
        p["angle"] += p["angle_speed"]
        p["life"] -= 1
        # Shrink particles as they fall to simulate flutter and fading
        p["w"] *= 0.98
        p["h"] *= 0.98
    # Remove dead particles
    confetti_particles[:] = [p for p in confetti_particles if p["life"] > 0]


def draw_confetti():
    for p in confetti_particles:
        if p["type"] == "rect":
            # The width now shrinks over time in update_confetti
            pygame.draw.rect(screen, p["color"], (p["x"], p["y"], p["w"], p["h"]))
        else:  # circle
            # The radius now shrinks over time
            radius = int(p["w"] / 2)
            pygame.draw.circle(screen, p["color"], (int(p["x"]), int(p["y"])), radius)


def draw_strikethrough_text(text, font, color, x, y):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))
    line_y = y + text_surface.get_height() // 2
    pygame.draw.line(
        screen, color, (x, line_y), (x + text_surface.get_width(), line_y), 3
    )


def draw_checkbox(x, y, checked):
    pygame.draw.rect(screen, THEME["text"], (x, y, CHECKBOX_SIZE, CHECKBOX_SIZE), 2)
    if checked:
        pygame.draw.line(
            screen,
            THEME["text"],
            (x + 4, y + CHECKBOX_SIZE // 2),
            (x + CHECKBOX_SIZE // 2, y + CHECKBOX_SIZE - 6),
            3,
        )
        pygame.draw.line(
            screen,
            THEME["text"],
            (x + CHECKBOX_SIZE // 2, y + CHECKBOX_SIZE - 6),
            (x + CHECKBOX_SIZE - 4, y + 6),
            3,
        )


def load_icon_safe(name, size=(28, 28)):
    try:
        img = pygame.image.load(name).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    except:
        surf = pygame.Surface((28, 28), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        return surf


is_past = False
STATS_ICON = load_icon_safe(resource_path(os.path.join(ASSETS_DIR, "statistics.png")))
EDIT_ICON = load_icon_safe(resource_path(os.path.join(ASSETS_DIR, "edit.png")))
CREDIT_ICON = load_icon_safe(resource_path(os.path.join(ASSETS_DIR, "information.png")))
LOFI_OFF_ICON = load_icon_safe(resource_path(os.path.join(ASSETS_DIR, "music_off.png")))
LOFI_ON_ICON = load_icon_safe(resource_path(os.path.join(ASSETS_DIR, "music_on.png")))
EDIT_ICON = load_icon_safe(resource_path(os.path.join(ASSETS_DIR, "edit.png")))
DELETE_ICON = load_icon_safe(resource_path(os.path.join(ASSETS_DIR, "delete.png")))
WEEKLY_ICON = load_icon_safe(resource_path(os.path.join(ASSETS_DIR, "weekly.png")))
PLAY_ICON = load_icon_safe(resource_path(os.path.join(ASSETS_DIR, "play.png")))

color1 = (255, 255, 255)
color2 = (212, 166, 255)

# --- SCROLL STATE ---
scroll_offset = 0
scroll_velocity = 0
SCROLL_MIN = 0
SCROLL_MAX = 0
scrolling = False
scroll_drag_start = 0
scroll_start_offset = 0

todo_scroll_offset = 0


def draw_event_shadow(rect, alpha=80, blur=6):
    shadow = pygame.Surface(
        (rect.width + blur * 2, rect.height + blur * 2), pygame.SRCALPHA
    )
    pygame.draw.rect(
        shadow,
        (0, 0, 0, alpha),
        (blur, blur, rect.width, rect.height),
        border_radius=16,
    )
    for i in range(1, blur):
        pygame.draw.rect(
            shadow,
            (0, 0, 0, alpha // (i + 1)),
            (blur - i, blur - i, rect.width + 2 * i, rect.height + 2 * i),
            border_radius=16 + i,
        )
    screen.blit(shadow, (rect.x - blur, rect.y - blur))


def calculate_event_layout(events, view_width):
    """
    Calculates the width and horizontal position for a list of events
    to avoid overlaps.
    """
    if not events:
        return {}

    layout_props = {}
    sorted_events = sorted(events, key=lambda e: (e["hour"], e.get("minute", 0)))

    for i, event in enumerate(sorted_events):
        event_id = get_event_id(event)
        if event_id in layout_props:
            continue  # Already processed as part of a group

        start_time = event["hour"] * 60 + event.get("minute", 0)
        end_time = start_time + event.get("duration", 60)

        # Find all overlapping events for the current event
        overlapping_events = [event]
        for other_event in sorted_events[i + 1 :]:
            other_start = other_event["hour"] * 60 + other_event.get("minute", 0)
            other_end = other_start + other_event.get("duration", 60)
            if other_start < end_time:  # They overlap
                overlapping_events.append(other_event)

        # Determine the number of columns needed for this overlapping group
        num_cols = len(overlapping_events)
        col_width = view_width / num_cols

        # Assign columns to each event in the group
        overlapping_events.sort(key=lambda e: (e["hour"], e.get("minute", 0)))

        # This list tracks the end time of the event in each column
        cols_end_time = [-1] * num_cols

        for ov_event in overlapping_events:
            ov_start = ov_event["hour"] * 60 + ov_event.get("minute", 0)

            # Find the first available column
            for col_idx in range(num_cols):
                if cols_end_time[col_idx] <= ov_start:
                    # Place event in this column
                    ov_id = get_event_id(ov_event)
                    layout_props[ov_id] = {
                        "x": EVENT_X + col_idx * col_width,
                        "width": col_width,
                    }
                    cols_end_time[col_idx] = ov_start + ov_event.get("duration", 60)
                    break

    return layout_props

def find_and_remove_item(path_str, items):
    """Recursively finds and removes an item by its path string."""
    path_parts = path_str.split(':', 1)
    # The path is like "level-index". We only need the index part.
    try:
        index = int(path_parts[0].split('-')[1])
    except (IndexError, ValueError):
        return None # Invalid path format

    if index < 0 or index >= len(items):
        return None # Item not found at this level

    if len(path_parts) == 1:
        # This is the target item's level, pop it from the list.
        return items.pop(index)
    else:
        # Recurse into the children of the parent item.
        parent_item = items[index]
        if parent_item.get("type") == "folder" and "children" in parent_item:
            return find_and_remove_item(path_parts[1], parent_item["children"])
    return None


def find_item_by_id(item_id, items):
    """Recursively finds an item by its 'id'."""
    for item in items:
        if item.get("id") == item_id:
            return item
        if item.get("type") == "folder" and "children" in item:
            found = find_item_by_id(item_id, item.get("children", []))
            if found:
                return found
    return None


def get_parent_folder_name(path_str, items):
    """Finds the name of the parent folder given an item's path."""
    path_parts = path_str.split(':')
    if len(path_parts) > 1:
        parent_path = ':'.join(path_parts[:-1])
        parent, _, _ = find_item_at_pos_recursive(items, (-1,-1), 70, 0, 0, path_str=parent_path)
        if parent and parent.get("type") == "folder":
            return parent.get("name")
    return None



def draw_todo_items_recursive(items, y, level, mouse_pos, dragging_index_path, scroll_offset):
    """
    Recursively draws to-do items and folders, handling indentation and open/closed states.
    Returns the new y-coordinate after drawing.
    """
    font16 = get_font_wrapper(16)
    current_y = y
    item_height = 44
    indent_size = 20

    for i, item in enumerate(items):
        item_path = f"{level}-{i}"
        if item_path == dragging_index_path:
            continue  # Skip drawing the item being dragged

        item_rect = pygame.Rect(10 + level * indent_size, current_y, TODO_WIDTH - 20 - level * indent_size, item_height)

        # Removed custom culling logic because it breaks total height calculation
        # Pygame's set_clip handles rendering optimizations anyway

        is_hovered = item_rect.collidepoint(mouse_pos)
        bg_color = THEME["todo_item_hover"] if is_hovered else THEME["todo_item_bg"]
        pygame.draw.rect(screen, bg_color, item_rect, border_radius=8)

        is_folder = item.get("type") == "folder"
        
        if is_folder:
            # --- Draw Folder ---
            # Draw a polygon for the dropdown icon instead of a character
            icon_x = item_rect.x + 12
            icon_y = item_rect.centery
            if item.get("is_open"):
                # Down-pointing triangle ▼
                pygame.draw.polygon(screen, THEME["text"], [
                    (icon_x - 5, icon_y - 3),
                    (icon_x + 5, icon_y - 3),
                    (icon_x, icon_y + 4)
                ])
            else:
                # Right-pointing triangle ▶
                pygame.draw.polygon(screen, THEME["text"], [
                    (icon_x - 3, icon_y - 5),
                    (icon_x - 3, icon_y + 5),
                    (icon_x + 4, icon_y)
                ])
            text_x = item_rect.x + 25
            text_y = item_rect.centery - font16.get_height() // 2
            display_name = truncate_text(item.get("name", "Untitled Folder"), font16, item_rect.width - 30)
            folder_text = font16.render(display_name, True, THEME["text"])
            screen.blit(folder_text, (text_x, text_y))

        else:
            # --- Draw To-do Item ---
            if "color" in item:
                color_tag_rect = pygame.Rect(item_rect.x + 5, item_rect.y + 5, 5, item_rect.height - 10)
                pygame.draw.rect(screen, item["color"], color_tag_rect, border_radius=3)

            is_done = item.get("done", False)
            checkbox_x = item_rect.x + 8
            checkbox_y = item_rect.centery - CHECKBOX_SIZE // 2
            draw_checkbox(checkbox_x, checkbox_y, is_done)

            text_x = checkbox_x + CHECKBOX_SIZE + 8
            text_y = item_rect.centery - font16.get_height() // 2
            text_color = (150, 150, 150) if is_done else THEME["text"]
            
            max_text_width = item_rect.width - (text_x - item_rect.x) - 35
            display_title = truncate_text(item.get("title", "Untitled To-do"), font16, max_text_width)

            if is_done:
                draw_strikethrough_text(display_title, font16, text_color, text_x, text_y)
            else:
                todo_txt = font16.render(display_title, True, text_color)
                screen.blit(todo_txt, (text_x, text_y))

        # Delete button on hover for both folders and todos
        if is_hovered:
            delete_rect = pygame.Rect(item_rect.right - 28, item_rect.y + 10, 24, 24)
            pygame.draw.rect(screen, (255, 200, 200), delete_rect, border_radius=6)
            screen.blit(pygame.transform.smoothscale(DELETE_ICON, (16, 16)), (delete_rect.x + 4, delete_rect.y + 4))

        current_y += item_height + 6

        # If folder is open, recurse
        if is_folder and item.get("is_open"):
            children = item.get("children", [])
            current_y = draw_todo_items_recursive(children, current_y, level + 1, mouse_pos, dragging_index_path, scroll_offset)

    return current_y


def draw_todo_list(
    mouse_pos, dragging_index_path=None, is_event_widget_active=False, scroll_offset=0
):
    mx, my = mouse_pos
    pygame.draw.rect(screen, THEME["todo_bg"], (0, 0, TODO_WIDTH, HEIGHT))
    font = get_font_wrapper(24)

    # Define the vertical bounds for the list
    list_start_y = 70
    widget_space = 190 if is_event_widget_active else 0 # Space for the new progress bar at the bottom
    list_end_y = HEIGHT - 70 - widget_space - 50 # Make space for Add button

    title_txt = font.render("To-Do List", True, THEME["text"])
    screen.blit(title_txt, (TODO_WIDTH // 2 - title_txt.get_width() // 2, 20))

    add_btn = pygame.Rect(20, list_end_y + 10, TODO_WIDTH - 80, 40)
    is_hovered = add_btn.collidepoint(mx, my)

    # Polished button style
    base_color = (0, 150, 255) if current_theme == "light" else (0, 120, 215)
    hover_color = (20, 170, 255) if current_theme == "light" else (20, 140, 235) # noqa
    shadow_color = (0, 100, 180, 150) if current_theme == "light" else (0, 80, 160, 100)
    btn_color = hover_color if is_hovered else base_color

    # Shadow
    shadow_rect = add_btn.move(0, 3)
    pygame.draw.rect(screen, shadow_color, shadow_rect, border_radius=12)
    # Main button
    pygame.draw.rect(screen, btn_color, add_btn, border_radius=12)

    add_txt = get_font_wrapper(20).render(
        "Add To-do", True, (0, 0, 0)
    )  # Black text on light blue is fine
    screen.blit(
        add_txt,
        (
            add_btn.centerx - add_txt.get_width() // 2,
            add_btn.centery - add_txt.get_height() // 2,
        ),
    )

    # --- Delete Completed Button ---
    delete_completed_btn = pygame.Rect(add_btn.right + 10, add_btn.y, 40, 40)
    has_completed = any(t.get("done") for t in todos)
    if has_completed:
        del_base_color = (255, 180, 180)
        del_hover_color = (255, 200, 200)
        draw_polished_button(
            delete_completed_btn,
            icon=pygame.transform.smoothscale(DELETE_ICON, (20, 20)),
            base_color=del_base_color,
            hover_color=del_hover_color,
        )
    else:
        # Draw a disabled-looking button
        pygame.draw.rect(screen, (200, 200, 200), delete_completed_btn, border_radius=10)

    # --- Clipping area for scrollable todo list ---
    list_clip_rect = pygame.Rect(0, list_start_y, TODO_WIDTH, list_end_y - list_start_y)
    screen.set_clip(list_clip_rect)

    # Start the recursive drawing
    final_y = draw_todo_items_recursive(todos, list_start_y - scroll_offset, 0, mouse_pos, dragging_index_path, scroll_offset)

    # Reset clipping
    screen.set_clip(None)

    total_list_height = final_y - (list_start_y - scroll_offset)
    visible_height = list_end_y - list_start_y
    return {
        "add_todo_btn": add_btn,
        "delete_completed_btn": delete_completed_btn,
        "max_scroll": max(0, total_list_height - visible_height),
    }


def draw_current_event_widget(event):
    if not event:
        return None

    # --- Calculate Progress ---
    now = datetime.datetime.now()
    start_time = now.replace(
        hour=event["hour"], minute=event.get("minute", 0), second=0, microsecond=0
    )
    duration_minutes = event.get("duration", 60)
    end_time = start_time + datetime.timedelta(minutes=duration_minutes)

    if now < start_time or now > end_time:
        return None  # Event is not currently active

    elapsed_seconds = (now - start_time).total_seconds()
    total_seconds = duration_minutes * 60
    progress = clamp(elapsed_seconds / total_seconds, 0, 1)
    remaining_seconds = total_seconds - elapsed_seconds

    # --- Widget Setup ---
    center_x = TODO_WIDTH // 2
    center_y = HEIGHT - 100  # Positioned at the bottom
    radius = 65 # Reduced radius to prevent clipping
    thickness = 16

    # --- 2. Background Track ---
    track_color = THEME["todo_bg"]
    pygame.draw.circle(screen, track_color, (center_x, center_y), radius, thickness)

    # --- 3. Rotating "Shader" Progress Arc ---
    progress_color = (0, 255, 150)  # Bright green
    # Add padding to the surface to prevent the knob from being clipped
    padding = 20
    arc_rect = pygame.Rect(center_x - radius - padding, center_y - radius - padding, (radius + padding) * 2, (radius + padding) * 2)

    if progress > 0.005:
        start_angle = math.pi / 2
        end_angle = start_angle - (progress * 2 * math.pi)

        # --- Draw a high-quality, anti-aliased arc ---
        # Create a surface for the arc to be drawn on
        arc_surf = pygame.Surface(arc_rect.size, pygame.SRCALPHA)
        # Draw the arc with anti-aliasing by drawing multiple thin arcs
        for i in range(thickness):
            # Use a slightly smaller radius for each line to create thickness
            aa_radius = radius - (thickness // 2) + i
            pygame.draw.arc(
                arc_surf,
                progress_color,
                (
                    padding + radius - aa_radius,
                    padding + radius - aa_radius,
                    aa_radius * 2,
                    aa_radius * 2,
                ),
                end_angle,
                start_angle,
                1,
            )
        screen.blit(arc_surf, arc_rect.topleft)

        # --- "Translucent Bean" Knob ---
        knob_angle = end_angle
        knob_x = center_x + radius * math.cos(knob_angle)
        knob_y = center_y - radius * math.sin(knob_angle)

        bean_w, bean_h = 30, 14
        bean_surf = pygame.Surface((bean_w, bean_h), pygame.SRCALPHA)
        pygame.draw.rect(
            bean_surf, (255, 255, 255, 150), (0, 0, bean_w, bean_h), border_radius=7
        )
        pygame.draw.rect(
            bean_surf, (255, 255, 255, 200), (0, 0, bean_w, bean_h), 1, border_radius=7
        )

        rotated_bean = pygame.transform.rotate(bean_surf, math.degrees(knob_angle))
        bean_rect = rotated_bean.get_rect(center=(knob_x, knob_y))
        screen.blit(rotated_bean, bean_rect)

    # --- 4. Central Glass Button ---
    button_radius = (
        radius - thickness - 5
    )  # Make it slightly smaller than the inner ring
    button_center = (center_x, center_y)
    button_rect_for_collision = pygame.Rect(0, 0, button_radius * 2, button_radius * 2)
    button_rect_for_collision.center = button_center

    mx, my = pygame.mouse.get_pos()
    is_hovered = button_rect_for_collision.collidepoint(mx, my)
    base_color = (255, 255, 255, 20)
    hover_color = (255, 255, 255, 40)
    current_color = hover_color if is_hovered else base_color

    pygame.draw.circle(screen, current_color, button_center, button_radius)
    pygame.draw.circle(
        screen, (255, 255, 255, 60), button_center, button_radius, 1
    )  # Highlight

    # Display remaining time
    remaining_time_str = format_time(remaining_seconds)
    time_font = get_font_wrapper(24)
    time_surf = time_font.render(remaining_time_str, True, THEME["text"])
    screen.blit(
        time_surf,
        (
            center_x - time_surf.get_width() // 2,
            center_y - time_surf.get_height() // 2,
        ),
    )

    return {"checkbox_rect": button_rect_for_collision}


def draw_polished_button(
    rect,
    icon=None,
    text=None,
    base_color=(240, 240, 240),
    hover_color=(255, 255, 255),
    shadow_color=(0, 0, 0, 50),
):
    """Helper to draw consistent, polished buttons with hover effects and shadows."""
    mx, my = pygame.mouse.get_pos()
    is_hovered = rect.collidepoint(mx, my)

    btn_color = hover_color if is_hovered else base_color

    # Shadow
    shadow_rect = rect.move(2, 3)
    pygame.draw.rect(screen, shadow_color, shadow_rect, border_radius=12)

    # Main button
    pygame.draw.rect(screen, btn_color, rect, border_radius=10)
    pygame.draw.rect(screen, (0, 0, 0, 20), rect, 1, border_radius=10)  # Subtle border

    if icon:
        screen.blit(
            icon,
            (
                rect.centerx - icon.get_width() // 2,
                rect.centery - icon.get_height() // 2,
            ),
        )
    if text:
        screen.blit(
            text,
            (
                rect.centerx - text.get_width() // 2,
                rect.centery - text.get_height() // 2,
            ),
        )


def draw_day_view(event_layout, dragging_event=None, is_dragging_over_todo=False):
    global WIDTH, HEIGHT, scroll_offset, SCROLL_MAX, state, lofi_on, EVENT_X

    # --- Background ---
    # First, draw base background based on theme
    if current_theme == "light":
        screen.fill(
            THEME["background"], pygame.Rect(TODO_WIDTH, 0, WIDTH - TODO_WIDTH, HEIGHT)
        )
    elif THEME.get("background_gradient"): 
        draw_vertical_gradient(
            screen, THEME["background_gradient"][0], THEME["background_gradient"][1],
            pygame.Rect(TODO_WIDTH, 0, WIDTH - TODO_WIDTH, HEIGHT)
        )
    elif THEME.get("use_gradient_bg", False):
        t = (pygame.time.get_ticks() % 5000) / 5000
        wave = (math.sin(t * math.pi * 1) + 1) / 2
        top_color = lerp_color(THEME["gradient_start"], THEME["gradient_end"], wave)
        bottom_color = lerp_color(THEME["gradient_end"], THEME["gradient_start"], wave)
        draw_vertical_gradient(
            screen, top_color, bottom_color, pygame.Rect(TODO_WIDTH, 0, WIDTH - TODO_WIDTH, HEIGHT)
        )
    else:  # Dark theme
        screen.fill(
            THEME["background"], pygame.Rect(TODO_WIDTH, 0, WIDTH - TODO_WIDTH, HEIGHT)
        )

    # Calculate scrollable area first
    total_grid_height = (END_HOUR - START_HOUR + 1) * HOUR_HEIGHT
    visible_height = HEIGHT - TOP_Y - 40
    SCROLL_MAX = max(0, total_grid_height - visible_height)

    # --- Draw Timeline Background Gradient (Morning to Night) ---
    # We want a subtle overlay gradient over the timeline area representing time of day
    timeline_rect = pygame.Rect(TODO_WIDTH, TOP_Y, WIDTH - TODO_WIDTH, HEIGHT - TOP_Y)
    
    # We create an overlay surface for the hue shift (per-pixel alpha so the
    # tint blends softly over the timeline instead of painting solid bands).
    hue_surf = pygame.Surface((WIDTH - TODO_WIDTH, total_grid_height), pygame.SRCALPHA)

    # Colour keyframes for the arc of the day, anchored to real clock hours so the
    # tint reads as morning -> midday -> sunset -> night regardless of the
    # configured start/end hour. Each stop is (hour, R, G, B, Alpha); morning is
    # light and airy, the evening warms up, and night settles into a deep blue.
    DAY_ARC = [
        (4,  120, 140, 200, 60),   # early dawn, soft blue
        (7,  255, 200, 150, 58),   # sunrise warmth
        (10, 210, 232, 255, 36),   # bright airy morning (lightest)
        (13, 200, 226, 255, 34),   # clear midday
        (16, 255, 206, 150, 56),   # golden afternoon
        (18, 255, 140, 95,  82),   # sunset
        (20, 110, 82,  150, 104),  # dusk purple
        (23, 30,  32,  78,  126),  # night (darkest)
    ]

    def time_of_day_color(h):
        """Interpolate the day-arc colour (with alpha) for a fractional hour."""
        h = max(DAY_ARC[0][0], min(DAY_ARC[-1][0], h))
        for (h1, r1, g1, b1, a1), (h2, r2, g2, b2, a2) in zip(DAY_ARC, DAY_ARC[1:]):
            if h1 <= h <= h2:
                t = (h - h1) / max(1e-6, (h2 - h1))
                return (
                    int(r1 + (r2 - r1) * t),
                    int(g1 + (g2 - g1) * t),
                    int(b1 + (b2 - b1) * t),
                    int(a1 + (a2 - a1) * t),
                )
        last = DAY_ARC[-1]
        return (last[1], last[2], last[3], last[4])

    # Fill each hour row with a smooth vertical gradient between consecutive
    # hour colours, writing RGBA directly so the alpha is preserved.
    overlay_w = WIDTH - TODO_WIDTH
    for i, hour in enumerate(range(START_HOUR, END_HOUR + 1)):
        c1 = time_of_day_color(hour)
        c2 = time_of_day_color(hour + 1)
        y0 = i * HOUR_HEIGHT
        for dy in range(HOUR_HEIGHT):
            t = dy / max(1, HOUR_HEIGHT)
            row = (
                int(c1[0] + (c2[0] - c1[0]) * t),
                int(c1[1] + (c2[1] - c1[1]) * t),
                int(c1[2] + (c2[2] - c1[2]) * t),
                int(c1[3] + (c2[3] - c1[3]) * t),
            )
            pygame.draw.line(hue_surf, row, (0, y0 + dy), (overlay_w, y0 + dy))

    # Apply scroll offset to the hue overlay and clip it to the scrollable area
    screen.set_clip(timeline_rect)
    screen.blit(hue_surf, (TODO_WIDTH, TOP_Y - scroll_offset))
    screen.set_clip(None)

    EVENT_X = TODO_WIDTH + TIMELINE_GUTTER

    # --- Draw hour grid (apply scroll_offset) ---
    # Clip the grid to the same scrollable region as the events (extended slightly
    # upward so the top-most hour label isn't cut off). This keeps the lines,
    # labels and event boxes moving as one synchronized unit during over-scroll
    # bounce, instead of the grid bleeding up into the header while events stay
    # clipped at TOP_Y.
    grid_clip = pygame.Rect(TODO_WIDTH, TOP_Y - 22, WIDTH - TODO_WIDTH, HEIGHT - TOP_Y + 22)
    screen.set_clip(grid_clip)
    for i, hour in enumerate(range(START_HOUR, END_HOUR + 1)):
        y = TOP_Y + i * HOUR_HEIGHT - scroll_offset
        pygame.draw.line(
            screen, THEME["hour_line"], (EVENT_X, y), (WIDTH - EVENT_RIGHT_MARGIN, y), 1
        )
        hour_text = get_font_wrapper(18).render(f"{hour}:00", True, THEME["text"])
        screen.blit(hour_text, (TODO_WIDTH + 10, y - hour_text.get_height() - 2))
    screen.set_clip(None)

    font = get_font_wrapper(32)
    get_font_wrapper(16)
    font12 = get_font_wrapper(12)
    date_str = selected_date.strftime("%A, %d %B %Y")
    date_txt = font.render(date_str, True, THEME["title_color"])

    # --- Polished Buttons ---
    btn_base_color = tuple(c - 10 for c in THEME["background"]) if "Serene Morning" in current_theme else THEME["button_bg"]
    btn_hover_color = tuple(min(c + 15, 255) for c in btn_base_color)
    left_btn = pygame.Rect(TODO_WIDTH + 20, 20, 40, 40)
    right_btn = pygame.Rect(WIDTH - 80, 20, 40, 40)
    draw_polished_button(
        left_btn, base_color=btn_base_color, hover_color=btn_hover_color
    )
    draw_polished_button(
        right_btn, base_color=btn_base_color, hover_color=btn_hover_color
    )
    pygame.draw.polygon(
        screen,
        THEME["text"],
        [
            (left_btn.centerx - 3, left_btn.centery),
            (left_btn.centerx + 5, left_btn.centery - 8),
            (left_btn.centerx + 5, left_btn.centery + 8),
        ],
    )
    pygame.draw.polygon(
        screen,
        THEME["text"],
        [
            (right_btn.centerx + 3, right_btn.centery),
            (right_btn.centerx - 5, right_btn.centery - 8),
            (right_btn.centerx - 5, right_btn.centery + 8),
        ],
    )
    # Draw title over the top bar
    screen.blit(
        date_txt,
        (TODO_WIDTH + (WIDTH - TODO_WIDTH) // 2 - date_txt.get_width() // 2, 10),
    )
    

    settings_rect = pygame.Rect(WIDTH - 60, 70, 36, 36)
    stats_btn = pygame.Rect(WIDTH - 120, 70, 36, 36)
    credits_btn = pygame.Rect(WIDTH - 180, 70, 36, 36)
    lofi_btn = pygame.Rect(WIDTH - 240, 70, 36, 36)
    week_btn = pygame.Rect(TODO_WIDTH + 80, 20, 40, 40)
    
    draw_polished_button(
        settings_rect,
        icon=SETTINGS_ICON,
        base_color=btn_base_color,
        hover_color=btn_hover_color,
    )
    draw_polished_button(
        stats_btn,
        icon=STATS_ICON,
        base_color=btn_base_color,
        hover_color=btn_hover_color,
    )
    draw_polished_button(
        credits_btn,
        icon=CREDIT_ICON,
        base_color=btn_base_color,
        hover_color=btn_hover_color,
    )

    mx, my = pygame.mouse.get_pos()
    is_hovered = lofi_btn.collidepoint(mx, my)
    if lofi_on:
        base = (200, 255, 200)
        hover = (220, 255, 220)
        draw_polished_button(
            lofi_btn,
            icon=LOFI_ON_ICON,
            base_color=base,
            hover_color=hover,
        )
    else:
        base = (255, 200, 200)
        hover = (255, 220, 220)
        draw_polished_button(
            lofi_btn, icon=LOFI_OFF_ICON, base_color=base, hover_color=hover
        )

    total_minutes = sum(e.get("duration", 60) for e in events)
    font = get_font_wrapper(22)
    total_txt = font.render(f"Total: {total_minutes} min", True, THEME["text"])
    screen.blit(total_txt, (TODO_WIDTH + 20, 70))

    draw_polished_button(
        week_btn,
        icon=WEEKLY_ICON,
        base_color=THEME["button_bg"],
        hover_color=tuple(min(c + 15, 255) for c in THEME["button_bg"]),
    )

    # Calculate scrollable area
    total_grid_height = (END_HOUR - START_HOUR + 1) * HOUR_HEIGHT
    visible_height = HEIGHT - TOP_Y - 40
    SCROLL_MAX = max(0, total_grid_height - visible_height)
    # Removing clamp here to allow physics bounce for events too

    # Draw top border of the grid (now it will scroll)
    pygame.draw.line(
        screen,
        THEME["hour_line"],
        (EVENT_X, TOP_Y - scroll_offset),
        (WIDTH - EVENT_RIGHT_MARGIN, TOP_Y - scroll_offset),
        2,
    )

    # --- Draw events (with animation, shadow, hover, etc) ---
    now = datetime.datetime.now()
    now_minutes = (
        now.hour * 60 + now.minute if selected_date == datetime.date.today() else -1
    )
    full_event_width = WIDTH - EVENT_X - EVENT_RIGHT_MARGIN
    mouse_x, mouse_y = pygame.mouse.get_pos()

    # --- Clipping area for scrollable content ---
    scroll_area = pygame.Rect(TODO_WIDTH, TOP_Y, WIDTH - TODO_WIDTH, HEIGHT - TOP_Y)
    screen.set_clip(scroll_area)

    for event in events:
        event_id = get_event_id(event)
        if event_id in animating_out:
            # Skip drawing if it's part of the check-off animation
            continue

        if (
            event is dragging_event and is_dragging_over_todo
        ):  # Don't draw if being dragged to todo
            continue

        event_id = get_event_id(event)
        layout = event_layout.get(event_id, {"x": EVENT_X, "width": full_event_width})

        start_minutes = event["hour"] * 60 + event.get("minute", 0)
        end_minutes = start_minutes + event.get("duration", 60)
        event_y = (
            TOP_Y
            + (start_minutes - START_HOUR * 60) * (HOUR_HEIGHT / 60)
            - scroll_offset
        )
        event_height = event.get("duration", 60) * (HOUR_HEIGHT / 60)
        alpha = 255  # Always opaque

        is_dragged = event is dragging_event

        # Adjust rect for drag animation
        if is_dragged:
            # Use the temporary drag position if available
            event_x = event.get("temp_x", layout["x"] - 5)
            event_y = event.get("temp_y", event_y)
            event_width = layout["width"] + 10
            event_height += 10
        else:
            event_x, event_width = layout["x"], layout["width"]

        # Shadow
        event_rect = pygame.Rect(event_x, event_y + 5, event_width, event_height - 10)
        if is_dragged:
            # More pronounced shadow when dragging
            draw_event_shadow(event_rect, alpha=150, blur=15)
        else:
            draw_event_shadow(event_rect, alpha=60, blur=8)

        # --- Event Surface Creation ---
        # For high-quality rotation, render to a larger surface (supersampling)
        render_scale = 3  # Increased for higher quality rendering
        surf_w, surf_h = int(event_rect.width * render_scale), int(
            event_rect.height * render_scale
        )
        event_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)

        is_done = event.get("done")

        bg_color = event["color"]

        bg_color = tuple(bg_color)  # Ensure it's a tuple

        # Gradient fill
        for y in range(surf_h):
            t = y / max(1, surf_h)
            # Softer gradient from base color to a slightly lighter version
            lighter_color = tuple(min(255, c + 20) for c in bg_color)
            c = lerp_color(lighter_color, bg_color, t)
            pygame.draw.rect(
                event_surf,
                c + (alpha,),
                (0, y, surf_w, 1),
            )

        # Inner highlight for a more "glassy" look
        pygame.draw.rect(
            event_surf,
            (255, 255, 255, 80),
            (
                1 * render_scale,
                1 * render_scale,
                surf_w - 2 * render_scale,
                surf_h - 2 * render_scale,
            ),
            2 * render_scale,
            border_radius=16 * render_scale,
        )

        # Hover effect
        if event_rect.collidepoint(mouse_x, mouse_y) and not is_dragged:
            hover_overlay = pygame.Surface(event_surf.get_size(), pygame.SRCALPHA)
            hover_overlay.fill((255, 255, 255, 40))
            event_surf.blit(hover_overlay, (0, 0))

        # --- Blit the final surface (with drag animation if needed) ---
        if is_dragged and not is_dragging_over_todo:
            # Apply tilt
            rotated_surf = pygame.transform.rotate(event_surf, -2)  # Reduced tilt
            # Scale down the high-res rotated surface for anti-aliasing
            final_surf = pygame.transform.smoothscale(
                rotated_surf,
                (
                    rotated_surf.get_width() // render_scale,
                    rotated_surf.get_height() // render_scale,
                ),
            )
            # Get new rect to blit at the correct position, centered
            new_rect = final_surf.get_rect(center=event_rect.center)
            screen.blit(final_surf, new_rect.topleft)
        else:
            final_surf = pygame.transform.smoothscale(
                event_surf, (event_rect.width, event_rect.height)
            )
            screen.blit(final_surf, event_rect.topleft)

        # --- Vertical progress bar inside event ---
        if (
            selected_date == datetime.date.today() and not is_dragged
        ):  # Hide when dragging
            now_min = now.hour * 60 + now.minute
            if start_minutes <= now_min < end_minutes:
                # --- Blended Progress Overlay ---
                progress = (now_min - start_minutes) / max(
                    1, end_minutes - start_minutes
                )

                # Calculate the height of the progress overlay
                overlay_h = int((event_height - 10) * progress)
                overlay_rect = pygame.Rect(event_x, event_y + 5, event_width, overlay_h)

                # Create a semi-transparent surface to draw the overlay
                overlay_surface = pygame.Surface(overlay_rect.size, pygame.SRCALPHA)
                overlay_surface.fill((0, 0, 0, 50))  # Dark, semi-transparent fill

                # Blit the overlay onto the screen at the top of the event
                screen.blit(overlay_surface, overlay_rect.topleft)

        # Icon
        if "icon" in event and EVENT_ICONS[event["icon"]]:
            icon_size = min(28, int(event_height - 16))
            if icon_size > 0:
                # Use smoothscale for high-quality icon rendering
                scaled_icon = pygame.transform.smoothscale(
                    EVENT_ICONS[event["icon"]],
                    (icon_size, icon_size),
                )
                screen.blit(scaled_icon, (event_x + 10, event_y + 8))

        # Checkbox (aligned after icon area)
        icon_area_width = 40  # Consistent width for icon + padding
        checkbox_x = event_x + icon_area_width
        checkbox_y = event_y + 12  # Align near the top
        draw_checkbox(checkbox_x, checkbox_y, event.get("done"))

        # Event text
        text_color = (
            THEME["text"] if not (is_past or event.get("done")) else (120, 120, 120)
        )
        
        # --- Display coins earned from each event ---
        coins_for_event = int(event.get("duration", 60) / 5)
        coin_icon_small = pygame.transform.smoothscale(coin_sprite_sheet.subsurface(pygame.Rect(0,0,coin_animation['frame_width'], coin_animation['frame_height'])), (16, 16)) if coin_sprite_sheet else pygame.Surface((16,16))
        coin_val_text = get_font_wrapper(14).render(f"+{coins_for_event}", True, text_color)
        
        screen.blit(coin_icon_small, (event_rect.right - 12 - 10, event_y + event_height - 30))
        screen.blit(coin_val_text, (event_rect.right - 36 - 10, event_y + event_height - 32))
        font16 = get_font_wrapper(16)
        if event.get("done"):
            draw_strikethrough_text(
                event["title"],
                font16,
                text_color,
                checkbox_x + CHECKBOX_SIZE + 8,
                event_y + 10,  # Align with checkbox
            )
        else:
            event_text = font16.render(event["title"], True, text_color)
            screen.blit(event_text, (checkbox_x + CHECKBOX_SIZE + 8, event_y + 10))

        # Duration on right
        dur_text = font16.render(f"{event.get('duration', 60)} min", True, text_color)
        screen.blit(
            dur_text, (event_rect.right - dur_text.get_width() - 10, event_y + 10)
        )

        # Edit & delete buttons (show on hover, scroll with event)
        mx, my = pygame.mouse.get_pos()
        edit_btn_rect = pygame.Rect(event_rect.right - 80, event_rect.y + 5, 32, 32)
        play_btn_rect = pygame.Rect(event_rect.right - 120, event_rect.y + 5, 32, 32)
        delete_btn_rect = pygame.Rect(event_rect.right - 40, event_rect.y + 5, 32, 32) # noqa
        if event_rect.collidepoint(mx, my) and event_y <= my <= event_y + event_height:
            is_current_event = selected_date == datetime.date.today() and start_minutes <= now_minutes < end_minutes

            pygame.draw.rect(screen, (200, 200, 255), edit_btn_rect, border_radius=8)
            pygame.draw.rect(screen, (255, 180, 180), delete_btn_rect, border_radius=8)
            screen.blit(EDIT_ICON, (edit_btn_rect.x + 2, edit_btn_rect.y + 2))
            screen.blit(DELETE_ICON, (delete_btn_rect.x + 2, delete_btn_rect.y + 2))

            if is_current_event:
                pygame.draw.rect(screen, (180, 255, 180), play_btn_rect, border_radius=8)
                play_icon = pygame.transform.smoothscale(PLAY_ICON, (18, 18))
                screen.blit(play_icon, (play_btn_rect.x + play_btn_rect.width//2 - play_icon.get_width()//2, play_btn_rect.y + play_btn_rect.height//2 - play_icon.get_height()//2))
                

    # --- Reset clipping to draw fixed elements ---
    screen.set_clip(None)

    # --- Draw vertical lines and progress bar as before ---
    pygame.draw.line(
        screen,
        THEME["hour_line"],
        (WIDTH - EVENT_RIGHT_MARGIN, TOP_Y),
        (WIDTH - EVENT_RIGHT_MARGIN, HEIGHT - 40),
        2,
    )

    total_minutes = (END_HOUR - START_HOUR + 1) * 60
    minutes_passed = (
        ((now.hour - START_HOUR) * 60 + now.minute)
        if selected_date == datetime.date.today()
        else 0
    )
    progress = min(max(minutes_passed / total_minutes, 0), 1)
    pygame.draw.rect(
        screen,
        THEME["progress_bar"],
        (
            EVENT_X,
            HEIGHT - 30,
            int((WIDTH - EVENT_X - EVENT_RIGHT_MARGIN) * progress),
            20,
        ),
    )
    pygame.draw.rect(
        screen,
        THEME["hour_line"],
        (EVENT_X, HEIGHT - 30, WIDTH - EVENT_X - EVENT_RIGHT_MARGIN, 20),
        2,
    )

    # --- Animated current time line ---
    if START_HOUR <= now.hour <= END_HOUR and selected_date == datetime.date.today():
        minutes_from_start = (now.hour - START_HOUR) * 60 + now.minute
        y_now = TOP_Y + minutes_from_start * (HOUR_HEIGHT / 60) - scroll_offset

        # A subtle, glowing line
        line_color = (255, 80, 80)
        glow_color = (255, 150, 150, 100)  # Semi-transparent glow

        # Draw the main line
        pygame.draw.line(
            screen, line_color, (EVENT_X, y_now), (WIDTH - EVENT_RIGHT_MARGIN, y_now), 2
        )
        # Draw a "glow" effect using a thicker, transparent line
        pygame.draw.line(
            screen, glow_color, (EVENT_X, y_now), (WIDTH - EVENT_RIGHT_MARGIN, y_now), 6
        )

        # Add a leading circle/comet
        pulse = (math.sin(pygame.time.get_ticks() / 300.0) + 1) / 2  # 0 to 1
        comet_radius = int(3 + pulse * 3)
        pygame.draw.circle(screen, line_color, (EVENT_X, y_now), comet_radius)
    
    # draw_polished_button(
    #         btns["global_focus_btn"],
    #         icon=PLAY_ICON,
    #         base_color=(180, 255, 180),
    #         hover_color=(210, 255, 210),
    #     )
        # Add the new global focus button to the returned dict
    # btns["global_focus_btn"] = pygame.Rect(WIDTH - 320, 70, 36, 36)
    # draw_polished_button(
    #         btns["global_focus_btn"],
    #         icon=PLAY_ICON,
    #         base_color=(180, 255, 180),
    #         hover_color=(210, 255, 210),
    #     )

    return {
        "left_btn": pygame.Rect(TODO_WIDTH + 20, 20, 40, 40),
        "right_btn": pygame.Rect(WIDTH - 80, 20, 40, 40),
        "settings_rect": pygame.Rect(WIDTH - 60, 70, 36, 36),
        "stats_btn": pygame.Rect(WIDTH - 120, 70, 36, 36),
        "credits_btn": pygame.Rect(WIDTH - 180, 70, 36, 36),
        "lofi_btn": pygame.Rect(WIDTH - 240, 70, 36, 36),
        "week_btn": week_btn,
        "global_focus_btn": pygame.Rect(WIDTH - 320, 70, 36, 36),
    }
    

# --- WEEKLY VIEW (unchanged) ---
def draw_weekly_view(week_start_date):
    if current_theme == "light":
        # Use the same animated gradient as the day view
        t = (pygame.time.get_ticks() % 5000) / 5000
        wave = (math.sin(t * math.pi * 1) + 1) / 2
        top_color = lerp_color(color1, color2, wave)
        bottom_color = lerp_color(color2, color1, wave)
        draw_vertical_gradient(screen, top_color, bottom_color)
    else:
        screen.fill(THEME["background"])

    font = get_font_wrapper(32)
    font18 = get_font_wrapper(18)
    font16 = get_font_wrapper(16)
    mouse_x, mouse_y = pygame.mouse.get_pos()

    day_rects = []
    for i in range(7):
        day = week_start_date + datetime.timedelta(days=i)
        day_width = (WIDTH - 160) // 7
        x = 80 + i * (day_width + 8)
        day_rect = pygame.Rect(x, 80, day_width, HEIGHT - 160)
        day_rects.append((day, day_rect))

        # Draw shadow and background
        draw_event_shadow(day_rect, alpha=40, blur=6)
        bg_color = (
            (255, 255, 255, 100) if current_theme == "light" else (60, 60, 60, 100)
        )
        if day == datetime.date.today():
            bg_color = (
                (220, 255, 220, 150) if current_theme == "light" else (80, 120, 80, 150)
            )  # Highlight today
        elif day_rect.collidepoint(mouse_x, mouse_y):
            bg_color = (
                (255, 255, 255, 150) if current_theme == "light" else (80, 80, 80, 150)
            )  # Hover effect

        pygame.draw.rect(
            screen,
            bg_color,
            day_rect,
            border_radius=16,
        )

        # Day and Date text
        day_txt = font.render(WEEKDAYS[i], True, THEME["text"])
        screen.blit(day_txt, (day_rect.centerx - day_txt.get_width() // 2, 90))
        date_txt = font18.render(day.strftime("%d %b"), True, THEME["text"])
        screen.blit(date_txt, (day_rect.centerx - date_txt.get_width() // 2, 130))

        # Draw events for this day
        date_str = day.strftime("%Y-%m-%d")
        day_events = all_events.get(date_str, [])
        y = 160
        for ev in day_events:
            event_rect = pygame.Rect(x + 10, y, day_width - 20, 32)
            color = ev["color"] if not ev.get("done") else THEME["event_done_color"]
            pygame.draw.rect(screen, color, event_rect, border_radius=8)
            if "icon" in ev and EVENT_ICONS[ev["icon"]]:
                screen.blit(  # Icons are PNGs with alpha, should be fine
                    pygame.transform.smoothscale(EVENT_ICONS[ev["icon"]], (24, 24)),
                    (x + 14, y + 4),
                )
            title = ev["title"]
            if len(title) > 12:
                title = title[:11] + "..."
            ev_txt = font16.render(title, True, (0, 0, 0))
            # Use a readable text color based on the event color's brightness
            screen.blit(
                ev_txt, (x + 44, y + 8)
            )  # Black text is usually fine on light event colors
            y += 40

    # Navigation buttons for weekly view
    back_btn = pygame.Rect(40, 20, 120, 36)
    prev_week_btn = pygame.Rect(WIDTH // 2 - 150, HEIGHT - 60, 140, 36)
    next_week_btn = pygame.Rect(WIDTH // 2 + 10, HEIGHT - 60, 140, 36)

    return {
        "back": back_btn,
        "prev": prev_week_btn,
        "next": next_week_btn,
        "days": day_rects,
    }


# --- SETTINGS / CREDITS / STATS (unchanged) ---
def show_settings():  # Reworked settings
    global lofi_on, START_HOUR, END_HOUR, currently_playing_index, HOUR_HEIGHT

    # --- Helper to draw UI elements ---
    def draw_toggle(x, y, w, h, is_on, label):
        font = get_font_wrapper(18)
        label_surf = font.render(label, True, THEME["text"])
        screen.blit(label_surf, (x, y + h // 2 - label_surf.get_height() // 2))

        toggle_rect = pygame.Rect(x + 150, y, w, h)
        knob_radius = h // 2 - 4

        if is_on:
            bg_color = (0, 191, 255)  # Blue for ON
            knob_x = toggle_rect.right - knob_radius - 4
        else:
            bg_color = (100, 100, 100)  # Gray for OFF
            knob_x = toggle_rect.left + knob_radius + 4

        pygame.draw.rect(screen, bg_color, toggle_rect, border_radius=h // 2)
        pygame.draw.circle(
            screen, (255, 255, 255), (knob_x, toggle_rect.centery), knob_radius
        )
        return toggle_rect

    def draw_slider(x, y, w, h, label, min_val, max_val, current_val, suffix=""):
        font = get_font_wrapper(18)
        label_surf = font.render(f"{label}: {current_val}{suffix}", True, THEME["text"])
        screen.blit(label_surf, (x, y - 25))

        slider_rect = pygame.Rect(x, y, w, h)
        progress = (current_val - min_val) / max(1, (max_val - min_val))
        knob_x = slider_rect.x + int(w * progress)

        # Track
        pygame.draw.rect(screen, (180, 180, 180), slider_rect, border_radius=h // 2)
        # Filled part
        fill_rect = pygame.Rect(x, y, int(w * progress), h)
        pygame.draw.rect(screen, (0, 150, 255), fill_rect, border_radius=h // 2)
        # Knob
        pygame.draw.circle(screen, (255, 255, 255), (knob_x, slider_rect.centery), h)
        pygame.draw.circle(screen, (0, 120, 215), (knob_x, slider_rect.centery), h, 2)
        return slider_rect

    # --- Main settings loop ---
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))

    win_w, win_h = 500, 650
    win_x, win_y = WIDTH // 2 - win_w // 2, HEIGHT // 2 - win_h // 2

    dragging_start_hour = False
    dragging_end_hour = False
    dragging_hour_height = False
    scroll_offset = 0
    scroll_target = 0
    clock = pygame.time.Clock()

    while True:
        # Smooth scrolling
        if abs(scroll_target - scroll_offset) > 1:
            scroll_offset += (scroll_target - scroll_offset) * 0.2
        else:
            scroll_offset = scroll_target

        screen.blit(overlay, (0, 0))
        pygame.draw.rect(
            screen, THEME["settings_bg"], (win_x, win_y, win_w, win_h), border_radius=18
        )
        pygame.draw.rect(
            screen, (200, 200, 200), (win_x, win_y, win_w, win_h), 1, border_radius=18
        )

        # Title
        title = get_font_wrapper(32).render("Settings", True, THEME["text"])
        screen.blit(title, (win_x + win_w // 2 - title.get_width() // 2, win_y + 20))

        # --- Clipping area for scrollable content ---
        content_clip_rect = pygame.Rect(win_x, win_y + 70, win_w, win_h - 130)
        screen.set_clip(content_clip_rect)

        # The y_offset now represents the position within the scrollable content area
        y_offset = win_y + 80

        # --- Theme Selection ---
        theme_label = get_font_wrapper(20).render("Theme", True, THEME["text"])
        screen.blit(theme_label, (win_x + 40, y_offset - scroll_offset))
        y_offset += 35
        theme_btns = []
        for i, name in enumerate(THEMES.keys()):
            row = i // 2
            col = i % 2
            btn_x = win_x + 40 + col * 210
            btn_y = y_offset + row * 50 - scroll_offset
            theme = THEMES[name] # noqa
            btn_rect = pygame.Rect(btn_x, btn_y, 190, 40)
            theme_btns.append((name, btn_rect))
            # Draw theme preview
            pygame.draw.rect(screen, theme["background"], btn_rect, border_radius=8)
            if settings["theme"] == name:
                pygame.draw.rect(screen, (0, 150, 255), btn_rect, 3, border_radius=8)
            # Draw sample text
            sample_text = get_font_wrapper(14).render(name.capitalize(), True, theme["text"])
            screen.blit(
                sample_text,
                (btn_rect.centerx - sample_text.get_width() // 2, btn_rect.y + 10),
            )
        y_offset += ((len(THEMES) + 1) // 2) * 50 + 20

        # --- Divider ---
        pygame.draw.line(screen, (200,200,200), (win_x + 30, y_offset - scroll_offset), (win_x + win_w - 30, y_offset - scroll_offset), 1)
        y_offset += 20

        # --- Font Selection ---
        font_label = get_font_wrapper(20).render("Font", True, THEME["text"])
        screen.blit(font_label, (win_x + 40, y_offset - scroll_offset))
        y_offset += 35
        font_btns = []
        font_names = sorted(AVAILABLE_FONTS.keys())
        for i, name in enumerate(font_names):
            path = AVAILABLE_FONTS[name]
            row = i // 2
            col = i % 2
            btn_x = win_x + 40 + col * 210
            btn_y = y_offset + row * 45 - scroll_offset
            btn_rect = pygame.Rect(btn_x, btn_y, 190, 35)
            font_btns.append((path, btn_rect))

            is_selected = settings.get("font_path") == path
            bg_color = tuple(min(c + 20, 255) for c in THEME["button_bg"]) if is_selected else THEME["button_bg"]
            pygame.draw.rect(screen, bg_color, btn_rect, border_radius=8)
            if is_selected:
                pygame.draw.rect(screen, (0, 150, 255), btn_rect, 2, border_radius=8)
            
            try: # Use try-except in case a font file is invalid
                font_preview = pygame.font.Font(path, 14)
                text_surf = font_preview.render(name, True, THEME["text"])
                screen.blit(text_surf, (btn_rect.centerx - text_surf.get_width() // 2, btn_rect.centery - text_surf.get_height() // 2))
            except pygame.error:
                error_surf = get_font_wrapper(12).render("! Invalid Font", True, (255,100,100))
                screen.blit(error_surf, (btn_rect.centerx - error_surf.get_width() // 2, btn_rect.centery - error_surf.get_height() // 2))
        y_offset += ((len(font_names) + 1) // 2) * 45 + 20

        # --- Divider ---
        pygame.draw.line(screen, (200,200,200), (win_x + 30, y_offset - scroll_offset), (win_x + win_w - 30, y_offset - scroll_offset), 1)
        y_offset += 20

        # --- Hour Range Sliders ---
        hour_label = get_font_wrapper(20).render("Calendar Display", True, THEME["text"])
        screen.blit(hour_label, (win_x + 40, y_offset - scroll_offset))
        y_offset += 60
        start_hour_slider = draw_slider(
            win_x + 40,
            y_offset - scroll_offset,
            300,
            12,
            "Start Hour",
            0,
            12,
            settings["start_hour"],
            suffix=":00"
        )
        end_hour_slider = draw_slider(
            win_x + 40, y_offset + 60 - scroll_offset, 300, 12, "End Hour", 13, 23, settings["end_hour"]
            , suffix=":00"
        )
        y_offset += 120
        hour_height_slider = draw_slider(
            win_x + 40,
            y_offset - scroll_offset,
            300,
            12,
            "Calendar Scale",
            30, 80, settings["hour_height"], suffix="px"
        )

        y_offset += 80
        # --- Divider ---
        pygame.draw.line(screen, (200,200,200), (win_x + 30, y_offset - scroll_offset), (win_x + win_w - 30, y_offset - scroll_offset), 1)
        y_offset += 20

        # --- Toggles ---
        y_toggle = y_offset
        sound_toggle = draw_toggle(
            win_x + 40, y_toggle - scroll_offset, 60, 30, settings["sounds_on"], "Sound Effects"
        )
        confetti_toggle = draw_toggle(
            win_x + 40, y_toggle + 50 - scroll_offset, 60, 30, settings["confetti_on"], "Confetti"
        )
        lofi_toggle = draw_toggle(
            win_x + 40, y_toggle + 100 - scroll_offset, 60, 30, lofi_on, "Lofi Music"
        )

        # Calculate total content height to determine max scroll
        total_content_height = (y_toggle + 130) - (win_y + 80)
        visible_height = content_clip_rect.height
        max_scroll = max(0, total_content_height - visible_height)
        scroll_target = clamp(scroll_target, 0, max_scroll)
        scroll_offset = clamp(scroll_offset, 0, max_scroll)
        
        y_offset += 20

        # --- Reset clipping to draw fixed elements like the close button ---
        screen.set_clip(None)

        # --- Close Button ---
        close_btn = pygame.Rect(win_x + win_w // 2 - 60, win_y + win_h - 60, 120, 40)
        pygame.draw.rect(screen, (255, 100, 100), close_btn, border_radius=12) # noqa
        close_txt = get_font_wrapper(22).render("Close", True, (255, 255, 255))
        screen.blit(
            close_txt,
            (
                close_btn.centerx - close_txt.get_width() // 2,
                close_btn.centery - close_txt.get_height() // 2,
            ),
        )

        pygame.display.flip()
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                save_settings()
                pygame.quit()
                sys.exit()

            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 4: # Scroll up
                    scroll_target -= 60
                    continue
                elif e.button == 5: # Scroll down
                    scroll_target += 60
                    continue
                if e.button != 1:
                    continue
                mx, my = e.pos
                
                for name, rect in theme_btns:
                    if rect.collidepoint(mx, my):
                        settings["theme"] = name
                        set_theme(name)
                
                for path, rect in font_btns:
                    if rect.collidepoint(mx, my):
                        settings["font_path"] = path
                        # Font cache will be updated automatically by get_font

                if start_hour_slider.collidepoint(mx, my):
                    dragging_start_hour = True
                if end_hour_slider.collidepoint(mx, my):
                    dragging_end_hour = True
                if hour_height_slider.collidepoint(mx, my):
                    dragging_hour_height = True

                if sound_toggle.collidepoint(mx, my):
                    settings["sounds_on"] = not settings["sounds_on"]
                if confetti_toggle.collidepoint(mx, my):
                    settings["confetti_on"] = not settings["confetti_on"]
                if lofi_toggle.collidepoint(mx, my):
                    lofi_on = not lofi_on
                    if MUSIC_FILES:
                        if lofi_on:
                            if (
                                currently_playing_index == -1
                                or currently_playing_index >= len(MUSIC_FILES)
                            ):
                                currently_playing_index = random.randint(
                                    0, len(MUSIC_FILES) - 1
                                )
                            pygame.mixer.music.load(
                                MUSIC_FILES[currently_playing_index]
                            )
                            pygame.mixer.music.play(-1, fade_ms=1000)
                        else:
                            pygame.mixer.music.fadeout(500)

                if close_btn.collidepoint(mx, my):
                    save_settings()
                    # Apply hour changes
                    START_HOUR = settings["start_hour"]
                    END_HOUR = settings["end_hour"]
                    HOUR_HEIGHT = settings["hour_height"]
                    return

            elif e.type == pygame.MOUSEBUTTONUP:
                if e.button != 1:
                    continue
                dragging_start_hour = False
                dragging_end_hour = False
                dragging_hour_height = False

        
            elif e.type == pygame.MOUSEMOTION:
                mx, my = e.pos
                if dragging_start_hour:
                    progress = (mx - start_hour_slider.x) / start_hour_slider.width
                    val = int(0 + progress * (12 - 0))
                    settings["start_hour"] = clamp(val, 0, 12)
                if dragging_end_hour:
                    progress = (mx - end_hour_slider.x) / end_hour_slider.width
                    val = int(13 + progress * (23 - 13))
                    settings["end_hour"] = clamp(val, 13, 23)
                if dragging_hour_height:
                    progress = (mx - hour_height_slider.x) / hour_height_slider.width
                    val = int(30 + progress * (80 - 30))
                    settings["hour_height"] = clamp(val, 30, 80)

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    save_settings()
                    START_HOUR = settings["start_hour"]
                    END_HOUR = settings["end_hour"]
                    HOUR_HEIGHT = settings["hour_height"]
                    return


def show_confirmation_dialog(message):
    """Displays a modal confirmation dialog and returns True (Yes) or False (No)."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    win_w, win_h = 400, 180
    win_x, win_y = WIDTH // 2 - win_w // 2, HEIGHT // 2 - win_h // 2
    font_msg = get_font_wrapper(20)
    font_btn = get_font_wrapper(18)
    msg_surf = font_msg.render(message, True, THEME["text"])
    yes_btn = pygame.Rect(win_x + 50, win_y + 100, 120, 40)
    no_btn = pygame.Rect(win_x + win_w - 170, win_y + 100, 120, 40)

    while True:
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, THEME["settings_bg"], (win_x, win_y, win_w, win_h), border_radius=15)
        screen.blit(msg_surf, (win_x + win_w // 2 - msg_surf.get_width() // 2, win_y + 40))
        pygame.draw.rect(screen, (100, 220, 100), yes_btn, border_radius=10)
        pygame.draw.rect(screen, (220, 100, 100), no_btn, border_radius=10)
        yes_txt = font_btn.render("Yes, Delete", True, (0,0,0))
        no_txt = font_btn.render("No, Cancel", True, (0,0,0))
        screen.blit(yes_txt, (yes_btn.centerx - yes_txt.get_width()//2, yes_btn.centery - yes_txt.get_height()//2))
        screen.blit(no_txt, (no_btn.centerx - no_txt.get_width()//2, no_btn.centery - no_txt.get_height()//2))
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT: return False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: return False
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if yes_btn.collidepoint(e.pos): return True
                if no_btn.collidepoint(e.pos): return False


class SMTCController:
    """Publishes the music player's state to the Windows System Media Transport
    Controls (the media flyout / tray that normally shows Spotify, Chrome, etc.).

    We keep using pygame.mixer for the actual audio and drive a windowless
    WinRT MediaPlayer purely for its SMTC instance, updating the title/artist and
    play state manually. Media-key / tray button presses are pushed onto a
    thread-safe queue and consumed by the player loop. The whole thing is
    best-effort: if WinRT isn't available it silently becomes a no-op.
    """

    def __init__(self, thumb_path=None):
        self.ok = False
        self._cmds = None
        self._player = None
        self._smtc = None
        self._thumb = None
        self._last_playing = None
        try:
            import queue
            import winrt.windows.media as wm
            import winrt.windows.media.playback as playback

            # Give the process a stable identity in the tray (best-effort).
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Foci.FocusCalendar")
            except Exception:
                pass

            self._wm = wm
            self._cmds = queue.Queue()
            self._player = playback.MediaPlayer()
            # We drive the controls ourselves rather than letting the player do it.
            self._player.command_manager.is_enabled = False

            smtc = self._player.system_media_transport_controls
            smtc.is_enabled = True
            smtc.is_play_enabled = True
            smtc.is_pause_enabled = True
            smtc.is_next_enabled = True
            smtc.is_previous_enabled = True
            smtc.playback_status = wm.MediaPlaybackStatus.CLOSED
            smtc.add_button_pressed(self._on_button)
            self._smtc = smtc

            if thumb_path and os.path.exists(thumb_path):
                self._thumb = self._make_thumb(thumb_path)

            self.ok = True
        except Exception as exc:
            print(f"SMTC unavailable: {exc}")
            self.ok = False

    @staticmethod
    def _make_thumb(path):
        import asyncio
        from winrt.windows.storage.streams import (
            InMemoryRandomAccessStream, DataWriter, RandomAccessStreamReference,
        )
        data = open(path, "rb").read()

        async def _build():
            stream = InMemoryRandomAccessStream()
            writer = DataWriter(stream)
            writer.write_bytes(data)
            await writer.store_async()
            stream.seek(0)
            return RandomAccessStreamReference.create_from_stream(stream)

        return asyncio.run(_build())

    def _on_button(self, sender, args):
        # Fires on a WinRT background thread; queue.Queue is thread-safe.
        try:
            btn = args.button
            B = self._wm.SystemMediaTransportControlsButton
            mapping = {B.PLAY: "play", B.PAUSE: "pause", B.NEXT: "next", B.PREVIOUS: "prev"}
            cmd = mapping.get(btn)
            if cmd:
                self._cmds.put(cmd)
        except Exception:
            pass

    def get_command(self):
        if not self.ok:
            return None
        try:
            return self._cmds.get_nowait()
        except Exception:
            return None

    def set_metadata(self, title, artist="Foci"):
        if not self.ok:
            return
        try:
            du = self._smtc.display_updater
            du.type = self._wm.MediaPlaybackType.MUSIC
            du.music_properties.title = title or ""
            du.music_properties.artist = artist or ""
            if self._thumb is not None:
                du.thumbnail = self._thumb
            du.update()
        except Exception:
            pass

    def set_playing(self, is_playing):
        if not self.ok:
            return
        try:
            self._smtc.playback_status = (
                self._wm.MediaPlaybackStatus.PLAYING if is_playing
                else self._wm.MediaPlaybackStatus.PAUSED
            )
            self._last_playing = is_playing
        except Exception:
            pass

    def shutdown(self):
        if not self.ok:
            return
        try:
            self._smtc.playback_status = self._wm.MediaPlaybackStatus.CLOSED
            self._smtc.is_enabled = False
            self._player.close()
        except Exception:
            pass


def simple_music_player_process(font_path):
    """A new, simplified, and vibrant music player process."""
    pygame.init() # noqa
    pygame.mixer.pre_init(44100, -16, 2, 2048) # Higher quality audio
    pygame.mixer.init() # noqa

    try:
        import ctypes
        from ctypes import wintypes
        ctypes.windll.user32.SetProcessDPIAware()
    except (ImportError, AttributeError):
        ctypes = None

    try:
        import keyboard
        has_keyboard = True
    except ImportError:
        has_keyboard = False

    W, H = 300, 420
    screen = pygame.display.set_mode((W, H), pygame.RESIZABLE | pygame.NOFRAME, vsync=1)
    pygame.display.set_caption("Lofi Player")
    clock = pygame.time.Clock()

    music_dir = os.path.join(ASSETS_DIR, "music")
    music_files = []
    if os.path.exists(music_dir):
        for ext in ("*.mp3", "*.wav"):
            music_files.extend(glob.glob(os.path.join(music_dir, ext)))

    # --- Font Loading ---
    def get_font_local(size, bold=False):
        try:
            # Use the font path passed from the main app
            return pygame.font.Font(font_path, size) # noqa
        except:
            # Fallback to system font
            return pygame.font.SysFont("Segoe UI", size, bold=bold)


    if not music_files:
        # Handle no music case gracefully
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT or e.type == pygame.KEYDOWN: return
            screen.fill((40, 45, 60))
            msg = get_font_local(16).render("No music found in assets/music", True, (200, 200, 220))
            screen.blit(msg, msg.get_rect(center=(W/2, H/2)))
            pygame.display.flip()
            clock.tick(10)

    current_index = 0
    is_playing = False
    volume = 0.5
    pygame.mixer.music.set_volume(volume)
    song_length = 0
    seek_offset = 0

    dragging_volume = False
    dragging_progress = False
    is_dragging_window = False
    drag_offset = (0, 0)
    shuffle_on = False
    song_scroll_offset = 0

    play_rect = pygame.Rect(0,0,0,0)
    prev_rect = pygame.Rect(0,0,0,0)
    next_rect = pygame.Rect(0,0,0,0)
    shuffle_rect = pygame.Rect(0,0,0,0)
    prog_rect = pygame.Rect(0,0,0,0)
    vol_rect = pygame.Rect(0,0,0,0)
    song_rects = []

    # Windows media-tray (SMTC) integration: shows the current track and play
    # state in the system media flyout and accepts media-key / tray controls.
    _thumb_path = os.path.join(ASSETS_DIR, "music_on.png")
    smtc = SMTCController(thumb_path=_thumb_path)

    def _song_title(index):
        return os.path.basename(music_files[index]).rsplit(".", 1)[0]

    def play_music(index):
        nonlocal is_playing, current_index, song_length, seek_offset
        current_index = index % len(music_files)
        pygame.mixer.music.load(music_files[current_index])
        pygame.mixer.music.play()
        is_playing = True
        seek_offset = 0
        try:
            song_length = pygame.mixer.Sound(music_files[current_index]).get_length()
        except pygame.error:
            song_length = 0
        smtc.set_metadata(_song_title(current_index))
        smtc.set_playing(True)

    if has_keyboard:
        def toggle_play_pause(e=None):
            nonlocal is_playing
            if is_playing: pygame.mixer.music.pause(); is_playing = False
            else: pygame.mixer.music.unpause(); is_playing = True
        keyboard.on_press_key("play/pause media", toggle_play_pause)
        keyboard.on_press_key("next track", lambda _: play_music(current_index + 1))
        keyboard.on_press_key("previous track", lambda _: play_music(current_index - 1))

    def draw_icon(name, rect, color):
        if name == "play":
            pygame.draw.polygon(screen, color, [
                (rect.centerx - 5, rect.centery - 8),
                (rect.centerx - 5, rect.centery + 8),
                (rect.centerx + 7, rect.centery)
            ])
        elif name == "pause":
            pygame.draw.rect(screen, color, (rect.centerx - 7, rect.centery - 8, 5, 16), border_radius=2)
            pygame.draw.rect(screen, color, (rect.centerx + 2, rect.centery - 8, 5, 16), border_radius=2)
        elif name == "next":
            pygame.draw.polygon(screen, color, [
                (rect.centerx - 4, rect.centery - 7),
                (rect.centerx - 4, rect.centery + 7),
                (rect.centerx + 4, rect.centery)
            ])
            pygame.draw.rect(screen, color, (rect.centerx + 5, rect.centery - 7, 3, 14))
        elif name == "prev":
            pygame.draw.polygon(screen, color, [
                (rect.centerx + 4, rect.centery - 7),
                (rect.centerx + 4, rect.centery + 7),
                (rect.centerx - 4, rect.centery)
            ])
            pygame.draw.rect(screen, color, (rect.centerx - 8, rect.centery - 7, 3, 14))
        elif name == "shuffle":
            # Two crossing arrows
            start1, end1 = (rect.centerx - 6, rect.centery - 5), (rect.centerx + 6, rect.centery + 5)
            start2, end2 = (rect.centerx - 6, rect.centery + 5), (rect.centerx + 6, rect.centery - 5)
            pygame.draw.line(screen, color, start1, end1, 2)
            pygame.draw.line(screen, color, start2, end2, 2)
            # Arrowheads
            pygame.draw.polygon(screen, color, [(end1[0], end1[1]), (end1[0] - 5, end1[1]), (end1[0], end1[1] - 5)])
            pygame.draw.polygon(screen, color, [(end2[0], end2[1]), (end2[0] - 5, end2[1]), (end2[0], end2[1] + 5)])



    play_music(0)
    pygame.mixer.music.pause()
    is_playing = False
    smtc.set_playing(False)

    while True:
        # --- Apply commands coming from the Windows media tray / media keys ---
        cmd = smtc.get_command()
        while cmd:
            if cmd == "play":
                pygame.mixer.music.unpause(); is_playing = True
            elif cmd == "pause":
                pygame.mixer.music.pause(); is_playing = False
            elif cmd == "next":
                play_music(current_index + 1)
            elif cmd == "prev":
                play_music(current_index - 1)
            cmd = smtc.get_command()
        # Keep the tray's play/pause state in sync with ours.
        if smtc.ok and is_playing != smtc._last_playing:
            smtc.set_playing(is_playing)

        mx, my = pygame.mouse.get_pos()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: return
                if e.key == pygame.K_SPACE or getattr(e, 'key', 0) == getattr(pygame, 'K_AUDIOPLAY', 1073742085) or getattr(e, 'key', 0) == getattr(pygame, 'K_AUDIOPAUSE', 1073742084):
                    if is_playing: pygame.mixer.music.pause(); is_playing = False
                    else: pygame.mixer.music.unpause(); is_playing = True
                if getattr(e, 'key', 0) == getattr(pygame, 'K_AUDIONEXT', 1073742087):
                    play_music(current_index + 1)
                if getattr(e, 'key', 0) == getattr(pygame, 'K_AUDIOPREV', 1073742086):
                    play_music(current_index - 1)

            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    if W - 30 <= mx <= W - 10 and 10 <= my <= 30:
                        return
                    if play_rect.collidepoint(mx, my):
                        if is_playing: pygame.mixer.music.pause(); is_playing = False
                        else: pygame.mixer.music.unpause(); is_playing = True
                    elif prev_rect.collidepoint(mx, my):
                        play_music(current_index - 1)
                    elif next_rect.collidepoint(mx, my):
                        play_music(current_index + 1)
                    elif shuffle_rect.collidepoint(mx, my):
                        shuffle_on = not shuffle_on
                    elif vol_rect.inflate(0, 20).collidepoint(mx, my):
                        dragging_volume = True
                        volume = clamp((mx - vol_rect.x) / vol_rect.width, 0, 1)
                        pygame.mixer.music.set_volume(volume)
                    elif prog_rect.inflate(0, 20).collidepoint(mx, my):
                        dragging_progress = True
                        progress = clamp((mx - prog_rect.x) / prog_rect.width, 0, 1)
                        seek_offset = song_length * progress
                        if song_length > 0:
                            pygame.mixer.music.play(start=seek_offset)
                            if not is_playing: pygame.mixer.music.pause()
                    else:
                        for i, r in enumerate(song_rects):
                            if r.collidepoint(mx, my):
                                if i != current_index:
                                    play_music(i)
                                break

                    if my < 40 and not (play_rect.collidepoint(mx, my) or prev_rect.collidepoint(mx, my) or next_rect.collidepoint(mx, my) or shuffle_rect.collidepoint(mx, my)): # Draggable top bar
                        if ctypes:
                            hwnd = pygame.display.get_wm_info()["window"]
                            ctypes.windll.user32.ReleaseCapture()
                            ctypes.windll.user32.SendMessageW(hwnd, 0xA1, 2, 0)
                        else:
                            is_dragging_window = True
                            drag_offset = (mx, my)
                elif e.button == 4: # Scroll up
                    song_scroll_offset = max(0, song_scroll_offset - 30)
                elif e.button == 5: # Scroll down
                    list_h = H - 250
                    total_song_h = len(music_files) * 35
                    max_scroll = max(0, total_song_h - list_h)
                    song_scroll_offset = min(max_scroll, song_scroll_offset + 20)

            elif e.type == pygame.MOUSEBUTTONUP:
                if e.button == 1:
                    is_dragging_window = False
                    dragging_volume = False
                    dragging_progress = False

            elif e.type == pygame.MOUSEMOTION:
                if is_dragging_window and not ctypes:
                    pass # Not used on Windows anymore due to SendMessageW
                if dragging_volume:
                    vol_rect = pygame.Rect(30, 160, W - 60, 6)
                    volume = clamp((mx - vol_rect.x) / vol_rect.width, 0, 1)
                    pygame.mixer.music.set_volume(volume)
                if dragging_progress:
                    prog_rect = pygame.Rect(30, 80, W - 60, 6)
                    progress = clamp((mx - prog_rect.x) / prog_rect.width, 0, 1)
                    seek_offset = song_length * progress
                    if song_length > 0:
                        pygame.mixer.music.play(start=seek_offset)
                        if not is_playing: pygame.mixer.music.pause()

            elif e.type == pygame.VIDEORESIZE:
                W, H = e.w, e.h
                screen = pygame.display.set_mode((W, H), pygame.RESIZABLE | pygame.NOFRAME)

        if is_playing and not pygame.mixer.music.get_busy():
            if shuffle_on:
                next_index = random.randint(0, len(music_files) - 1)
                # Avoid playing the same song twice in a row if possible
                if next_index == current_index and len(music_files) > 1:
                    next_index = (next_index + 1) % len(music_files)
                play_music(next_index)
            else:
                play_music(current_index + 1)

        # --- Drawing ---
        BG_COLOR_1 = (40, 45, 60)
        BG_COLOR_2 = (25, 28, 38)
        ACCENT_COLOR = (110, 100, 255)
        TEXT_COLOR = (220, 220, 240)
        TEXT_DIM_COLOR = (150, 150, 170)

        draw_vertical_gradient(screen, BG_COLOR_1, BG_COLOR_2)

        # --- Close Button ---
        close_rect = pygame.Rect(W - 30, 10, 20, 20)
        close_hover = close_rect.collidepoint(mx, my)
        close_color = (255, 100, 100) if close_hover else (200, 80, 80)
        pygame.draw.line(screen, close_color, close_rect.topleft, close_rect.bottomright, 2)
        pygame.draw.line(screen, close_color, close_rect.topright, close_rect.bottomleft, 2)

        # --- Adaptive UI Logic ---
        is_compact_mode = H < 180
        is_micro_mode = W < 180

        # Define rects for all modes to avoid UnboundLocalError
        play_rect = pygame.Rect(0,0,0,0)
        prev_rect = pygame.Rect(0,0,0,0)
        next_rect = pygame.Rect(0,0,0,0)
        shuffle_rect = pygame.Rect(0,0,0,0)
        prog_rect = pygame.Rect(0,0,0,0)
        vol_rect = pygame.Rect(0,0,0,0)
        song_rects = []

        if is_micro_mode:
            # --- Micro Mode (Controls Only) ---
            play_rect.size = (40, 40); play_rect.center = (W/2, H/2)
            prev_rect.size = (30, 30); prev_rect.center = (W/2, H/2 - 45)
            next_rect.size = (30, 30); next_rect.center = (W/2, H/2 + 45)
            shuffle_rect.size = (25, 25); shuffle_rect.center = (W/2, H/2 + 85)
        elif is_compact_mode:
            # --- Compact Mode (No Playlist) ---
            song_name = os.path.basename(music_files[current_index]).split(".")[0]
            song_surf = get_font_local(16, bold=True).render(song_name, True, TEXT_COLOR)
            screen.blit(song_surf, song_surf.get_rect(center=(W/2, 30)))

            prog_rect = pygame.Rect(20, 55, W - 40, 5)
            play_rect.size = (45, 45); play_rect.center = (W/2, 95)
            prev_rect.size = (35, 35); prev_rect.center = (W/2 - 50, 95)
            next_rect.size = (35, 35); next_rect.center = (W/2 + 50, 95)
            shuffle_rect.size = (25, 25); shuffle_rect.center = (W/2 + 90, 95)
            vol_rect = pygame.Rect(20, 130, W - 40, 4)
        else:
            # --- Full Mode ---
            song_name = os.path.basename(music_files[current_index]).split(".")[0]
            song_surf = get_font_local(18, bold=True).render(song_name, True, TEXT_COLOR)
            screen.blit(song_surf, song_surf.get_rect(center=(W/2, 40)))

            prog_rect = pygame.Rect(30, 80, W - 60, 6)
            play_rect.size = (50, 50); play_rect.center = (W/2, 125)
            prev_rect.size = (40, 40); prev_rect.center = (W/2 - 60, 125)
            next_rect.size = (40, 40); next_rect.center = (W/2 + 60, 125)
            shuffle_rect.size = (30, 30); shuffle_rect.center = (W/2 + 105, 125)
            vol_rect = pygame.Rect(30, 170, W - 60, 6)

            # Playlist
            list_y_start = 200
            list_clip_rect = pygame.Rect(0, list_y_start, W, H - list_y_start)
            screen.set_clip(list_clip_rect)

            for i, song_path in enumerate(music_files):
                y_pos = list_y_start + i * 35 - song_scroll_offset
                song_item_rect = pygame.Rect(20, y_pos, W - 40, 30)
                song_rects.append(song_item_rect)

                if song_item_rect.bottom < list_y_start or song_item_rect.top > H:
                    continue

                is_selected = i == current_index
                text_color = ACCENT_COLOR if is_selected else TEXT_DIM_COLOR
                
                if song_item_rect.collidepoint(mx, my):
                    hover_surf = pygame.Surface(song_item_rect.size, pygame.SRCALPHA)
                    pygame.draw.rect(hover_surf, (255, 255, 255, 40), hover_surf.get_rect(), border_radius=5)
                    screen.blit(hover_surf, song_item_rect.topleft)
                    text_color = TEXT_COLOR

                song_name_playlist = os.path.basename(song_path).split(".")[0]
                song_list_surf = get_font_local(16).render(song_name_playlist, True, text_color)
                screen.blit(song_list_surf, (song_item_rect.x + 10, song_item_rect.centery - song_list_surf.get_height()//2))
            
            screen.set_clip(None)

        # --- Draw Common UI Elements ---
        if prog_rect.width > 0:
            play_time = seek_offset + (pygame.mixer.music.get_pos() / 1000)
            progress = play_time / song_length if song_length > 0 else 0
            pygame.draw.rect(screen, (0,0,0,50), prog_rect, border_radius=3)
            fill_w = prog_rect.width * progress
            pygame.draw.rect(screen, ACCENT_COLOR, (prog_rect.x, prog_rect.y, fill_w, prog_rect.height), border_radius=3)

        if vol_rect.width > 0:
            pygame.draw.rect(screen, (0,0,0,50), vol_rect, border_radius=3)
            vol_fill_w = vol_rect.width * volume
            pygame.draw.rect(screen, TEXT_DIM_COLOR, (vol_rect.x, vol_rect.y, vol_fill_w, vol_rect.height), border_radius=3)

        # Draw Controls
        pygame.draw.circle(screen, ACCENT_COLOR, play_rect.center, play_rect.width/2)
        draw_icon("pause" if is_playing else "play", play_rect, (255,255,255))
        draw_icon("prev", prev_rect, TEXT_COLOR)
        draw_icon("next", next_rect, TEXT_COLOR)
        shuffle_color = ACCENT_COLOR if shuffle_on else TEXT_DIM_COLOR
        draw_icon("shuffle", shuffle_rect, shuffle_color)

        # --- Handle Clicks ---
        # Click handling has been moved to MOUSEBUTTONDOWN event to avoid continuous triggering
        
        pygame.display.flip()
        clock.tick(30)


def run_music_player():
    """Starts a separate process for the music player window."""
    if any(p.name == "MusicPlayerProcess" for p in multiprocessing.active_children()):
        return

    font_path = settings.get("font_path") # Get font path from main app settings
    p = multiprocessing.Process(
        target=simple_music_player_process, args=(font_path,), name="MusicPlayerProcess", daemon=True
    )
    p.start()


def show_credits():
    # --- New Visuals & Animation ---
    start_time = time.time()
    anim_duration = 0.5

    # Colors
    BG_COLOR = (25, 30, 45)
    BORDER_COLOR = (60, 70, 90)
    TEXT_COLOR = (230, 230, 255)
    HIGHLIGHT_COLOR = (0, 255, 198)  # Vibrant Mint
    SHADOW_COLOR = (15, 20, 30)

    # Fonts
    font_title = get_font(48)
    font_subtitle = get_font(22)
    font_body = get_font_wrapper(18)

    win_w, win_h = 550, 450
    win_x, win_y = WIDTH // 2 - win_w // 2, HEIGHT // 2 - win_h // 2

    # Particle system for background
    particles = [
        {
            "pos": [random.uniform(0, win_w), random.uniform(0, win_h)],
            "vel": [random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2)],
            "radius": random.uniform(1, 3),
            "color": (
                random.randint(40, 60),
                random.randint(50, 70),
                random.randint(80, 100),
            ),
        }
        for _ in range(50)
    ]

    # Text content
    title_surf = font_title.render("Focus Calendar", True, TEXT_COLOR)
    subtitle_surf = font_subtitle.render(
        "Made by Akshit Kumar Lal", True, HIGHLIGHT_COLOR
    )
    lines = [
        "A modern planner designed for focus and productivity.",
        "Built with Python and Pygame.",
        "© 2025",
    ]
    line_surfs = [font_body.render(line, True, (180, 180, 200)) for line in lines] # noqa

    while True:
        # Redraw the underlying screen to create the overlay effect
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Animation and Parallax
        elapsed = time.time() - start_time
        anim_progress = min(1.0, elapsed / anim_duration)
        ease_out = 1 - pow(1 - anim_progress, 4)

        mx, my = pygame.mouse.get_pos()
        parallax_x = (mx - (win_x + win_w / 2)) / (win_w / 2)
        parallax_y = (my - (win_y + win_h / 2)) / (win_h / 2)

        # Draw window with animation
        current_w, current_h = win_w * ease_out, win_h * ease_out
        current_x, current_y = (
            win_x + (win_w - current_w) / 2,
            win_y + (win_h - current_h) / 2,
        )
        win_rect = pygame.Rect(current_x, current_y, current_w, current_h)

        pygame.draw.rect(screen, SHADOW_COLOR, win_rect.move(8, 8), border_radius=24)
        pygame.draw.rect(screen, BG_COLOR, win_rect, border_radius=24)
        pygame.draw.rect(screen, BORDER_COLOR, win_rect, 2, border_radius=24)

        # Update and draw particles
        for p in particles:
            p["pos"][0] = (p["pos"][0] + p["vel"][0]) % win_w
            p["pos"][1] = (p["pos"][1] + p["vel"][1]) % win_h
            px = win_rect.x + p["pos"][0] * ease_out
            py = win_rect.y + p["pos"][1] * ease_out
            pygame.draw.circle(screen, p["color"], (px, py), p["radius"] * ease_out)

        # Draw text with parallax and fade-in
        text_alpha = int(255 * anim_progress)
        title_surf.set_alpha(text_alpha)
        screen.blit(
            title_surf,
            (
                win_rect.centerx - title_surf.get_width() / 2 + parallax_x * -15,
                win_rect.y + 60 + parallax_y * -15,
            ),
        )
        subtitle_surf.set_alpha(text_alpha)
        screen.blit(
            subtitle_surf,
            (
                win_rect.centerx - subtitle_surf.get_width() / 2 + parallax_x * 5,
                win_rect.y + 130 + parallax_y * 5,
            ),
        )
        for i, surf in enumerate(line_surfs):
            surf.set_alpha(text_alpha)
            screen.blit(
                surf,
                (
                    win_rect.centerx - surf.get_width() / 2 + parallax_x * 12,
                    win_rect.y + 200 + i * 30 + parallax_y * 12,
                ),
            )

        # Close button
        close_btn = pygame.Rect(win_rect.centerx - 50, win_rect.bottom - 70, 100, 40)
        pygame.draw.rect(
            screen,
            (255, 100, 100, int(255 * anim_progress)),
            close_btn,
            border_radius=12,
        ) # noqa
        close_txt = get_font_wrapper(22).render("Close", True, (255, 230, 230))
        close_txt.set_alpha(text_alpha)
        screen.blit(
            close_txt,
            (
                close_btn.centerx - close_txt.get_width() / 2,
                close_btn.centery - close_txt.get_height() / 2,
            ),
        )

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if close_btn.collidepoint(mx, my):
                    return


def start_checkoff_animation(item_id, rect, surface_copy):
    """Initiates the shrink-and-fade animation for a completed item."""
    animating_out[item_id] = {
        "start_time": time.time(),
        "duration": 0.4,  # Animation duration in seconds
        "rect": rect.copy(),
        "surface": surface_copy,
    }



def toggle_checkbox_at_pos(pos, scroll_offset):
    x, y = pos
    global user_coins

    event_layout = calculate_event_layout(events, WIDTH - EVENT_X - EVENT_RIGHT_MARGIN)

    for ev in events:
        event_id = get_event_id(ev)
        layout = event_layout.get(
            event_id, {"x": EVENT_X, "width": WIDTH - EVENT_X - EVENT_RIGHT_MARGIN}
        )
        event_x = layout["x"]

        start_minutes = ev["hour"] * 60 + ev.get("minute", 0)
        event_start_y = (
            TOP_Y
            + (start_minutes - START_HOUR * 60) * (HOUR_HEIGHT / 60)
            - scroll_offset # This is the on-screen Y
        )

        # Use the exact same layout logic as in draw_day_view
        icon_area_width = 40
        checkbox_x = event_x + icon_area_width
        checkbox_y = event_start_y + 12
        checkbox_rect = pygame.Rect(
            checkbox_x, checkbox_y, CHECKBOX_SIZE, CHECKBOX_SIZE
        )
        if checkbox_rect.collidepoint(x, y):
            new_state = not ev.get("done", False)
            ev["done"] = new_state

            # Sync with linked to-do item if it exists
            if "todo_id" in ev:
                linked_todo = find_item_by_id(ev["todo_id"], todos)
                if linked_todo:
                    linked_todo["done"] = new_state
            if new_state:
                # --- Earn coins on check ---
                coins_earned = int(ev.get("duration", 60) / 5)
                user_coins += coins_earned
                with open(resource_path(os.path.join(ASSETS_DIR, "player_data.json")), "w") as f:
                    json.dump({"coins": user_coins}, f)

                # --- Start Check-off Animation ---
                event_height = ev.get("duration", 60) * (HOUR_HEIGHT / 60)
                anim_rect = pygame.Rect(
                    event_x, event_start_y, layout["width"], event_height
                )
                # Create a temporary surface to capture the event's appearance
                temp_surf = pygame.Surface(anim_rect.size, pygame.SRCALPHA)
                # We can't easily redraw just one event here, so we'll use a placeholder color
                # A more advanced implementation would capture the screen area.
                temp_surf.fill(tuple(ev["color"]) + (200,))
                start_checkoff_animation(event_id, anim_rect, temp_surf)

                if settings["confetti_on"]:
                    spawn_confetti(
                        checkbox_rect.centerx, checkbox_rect.centery
                    )
                if DING_SOUND:
                    try:
                        DING_SOUND.play()
                    except Exception:
                        pass
            else:
                # --- Lose coins on uncheck ---
                coins_lost = int(ev.get("duration", 60) / 5)
                user_coins = max(0, user_coins - coins_lost)
                with open(resource_path(os.path.join(ASSETS_DIR, "player_data.json")), "w") as f:
                    json.dump({"coins": user_coins}, f)

            save_events()
            return True
    return False

def find_item_at_pos_recursive(items, pos, y, level, scroll_offset, path_str=None):
    """
    Recursively finds an item. Can search by position (pos) or by path string (path_str). Returns (item, rect, path).
    """
    # --- Search by Position ---
    if pos != (-1, -1):
        mx, my = pos
        current_y = y
        item_height = 44
        indent_size = 20

        for i, item in enumerate(items):
            item_rect = pygame.Rect(10 + level * indent_size, current_y, TODO_WIDTH - 20 - level * indent_size, item_height)
            
            if item_rect.collidepoint(mx, my):
                return item, item_rect, f"{level}-{i}"

            current_y += item_height + 6

            if item.get("type") == "folder" and item.get("is_open"):
                children = item.get("children", [])
                found_item, found_rect, found_path = find_item_at_pos_recursive(children, pos, current_y, level + 1, scroll_offset, path_str=None)
                if found_item:
                    return found_item, found_rect, f"{level}-{i}:{found_path}"
                
                def get_recursive_height(inner_items):
                    h = 0
                    for inner_item in inner_items:
                        h += item_height + 6
                        if inner_item.get("type") == "folder" and inner_item.get("is_open"):
                            h += get_recursive_height(inner_item.get("children", []))
                    return h
                current_y += get_recursive_height(children)
        return None, None, None

    # --- Search by Path String (used by helper functions) ---
    if path_str:
        path_parts = path_str.split(':', 1)
        try:
            index = int(path_parts[0].split('-')[1])
        except (IndexError, ValueError):
            return None, None, None
        if index < 0 or index >= len(items): return None, None, None
        item = items[index]
        if len(path_parts) == 1:
            return item, None, path_str
        else:
            return find_item_at_pos_recursive(item.get("children", []), (-1,-1), 0, level + 1, 0, path_str=path_parts[1])
    return None, None, None

def check_or_delete_todo_at_pos(pos, scroll_offset=0):
    """Checks for clicks on a todo's checkbox or delete button."""
    x, my = pos
    item, item_rect, item_path = find_item_at_pos_recursive(todos, pos, 70 - scroll_offset, 0, scroll_offset)

    if not (item and item_rect):
        return False

    is_folder = item.get("type") == "folder"
    delete_rect = pygame.Rect(item_rect.right - 28, item_rect.y + 10, 24, 24)

    # --- Handle Delete Click ---
    if delete_rect.collidepoint(x, my):
        if is_folder:
            if show_confirmation_dialog(f"Delete '{item.get('name', 'folder')}'?"):
                find_and_remove_item(item_path, todos)
                save_todos()
                return True
        else: # It's a regular to-do
            find_and_remove_item(item_path, todos)
            save_todos()
            return True
        return False # If user cancels dialog

    # --- Handle Item-Specific Clicks (Toggle, Checkbox) ---
    if is_folder:
        # Click on folder (but not delete button) toggles it
        item["is_open"] = not item.get("is_open", False)
        save_todos()
        return True
    else:
        # It's a to-do, check for checkbox click
        checkbox_rect = pygame.Rect(item_rect.x + 8, item_rect.centery - CHECKBOX_SIZE // 2, CHECKBOX_SIZE, CHECKBOX_SIZE)
        if checkbox_rect.collidepoint(x, my):
            item["done"] = not item.get("done", False)
            if "id" in item:
                for event_list in all_events.values():
                    for ev in event_list:
                        if ev.get("todo_id") == item["id"]:
                            ev["done"] = item["done"]
            if item["done"]:
                trigger_motivational_quote(active_quotes, WIDTH, HEIGHT, get_font_wrapper(22))
            save_todos()
            return True

    return False

def show_todo_context_menu(todo_index, pos, scroll_offset=0):
    menu_w, menu_h = 180, 130
    menu_x, menu_y = pos

    options = ["Schedule for Today", "Schedule for Tomorrow", "Someday"]
    option_rects = []

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    while True:
        screen.blit(overlay, (0, 0))  # Transparent overlay to catch clicks
        pygame.draw.rect(
            screen,
            THEME["settings_bg"],
            (menu_x, menu_y, menu_w, menu_h),
            border_radius=10,
        )
        pygame.draw.rect(
            screen,
            (150, 150, 150),
            (menu_x, menu_y, menu_w, menu_h),
            1,
            border_radius=10,
        )

        option_rects.clear()
        for i, option in enumerate(options):
            rect = pygame.Rect(menu_x + 5, menu_y + 5 + i * 40, menu_w - 10, 35)
            option_rects.append(rect)

            mx, my = pygame.mouse.get_pos()
            if rect.collidepoint(mx, my):
                pygame.draw.rect(screen, (0, 150, 255, 100), rect, border_radius=8)

            text = get_font_wrapper(16).render(option, True, THEME["text"])
            screen.blit(text, (rect.x + 10, rect.centery - text.get_height() // 2))

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = e.pos
                if not pygame.Rect(menu_x, menu_y, menu_w, menu_h).collidepoint(mx, my):
                    return  # Clicked outside, close menu

                for i, rect in enumerate(option_rects):
                    if rect.collidepoint(mx, my):
                        todo = todos[todo_index]
                        if i == 0:  # Today
                            # Add the "today" tag as requested
                            todo["date"] = datetime.date.today().strftime("%Y-%m-%d")
                            todo["tag"] = "today"
                        elif i == 1:  # Tomorrow
                            todo["date"] = (
                                datetime.date.today() + datetime.timedelta(days=1)
                            ).strftime("%Y-%m-%d")
                            todo["tag"] = "tmr"
                            if "tag" in todo:
                                del todo["tag"]
                        elif i == 2:  # Someday
                            if "date" in todo:
                                del todo["date"]
                            if "tag" in todo:
                                # Remove all tags as requested
                                del todo["tag"]
                        save_todos()
                        return
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return


def edit_or_delete_event_at_pos(pos, current_scroll, queue):
    x, y = pos
    # Prevent clicks if the mouse is over the top UI bar area.
    if y < TOP_Y:
        return False

    event_layout = calculate_event_layout(events, WIDTH - EVENT_X - EVENT_RIGHT_MARGIN)

    for event in events:
        event_id = get_event_id(event)
        layout = event_layout.get(
            event_id, {"x": EVENT_X, "width": WIDTH - EVENT_X - EVENT_RIGHT_MARGIN}
        )
        event_x, event_width = layout["x"], layout["width"]

        start_minutes = event["hour"] * 60 + event.get("minute", 0)
        event_start_y = (
            TOP_Y
            + (start_minutes - START_HOUR * 60) * (HOUR_HEIGHT / 60)
            - current_scroll
        )
        event_rect = pygame.Rect(
            event_x,
            event_start_y + 5,
            event_width,
            (event.get("duration", 60) * (HOUR_HEIGHT / 60)) - 10,
        )

        edit_btn_rect = pygame.Rect(event_rect.right - 80, event_rect.y + 5, 32, 32)
        delete_btn_rect = pygame.Rect(event_rect.right - 40, event_rect.y + 5, 32, 32)
        if delete_btn_rect.collidepoint(x, y):
            events.remove(event)
            save_events()
            return True
        if edit_btn_rect.collidepoint(x, y):
            details = event_add_window(
                pos=(event["hour"], event.get("minute", 0)), edit_event=event
            )
            if details:
                # If date is different, move the event
                if details["date"] != selected_date.strftime("%Y-%m-%d"):
                    events.remove(event) # Remove from current day's list
                    date_str = details["date"]
                    if date_str not in all_events:
                        all_events[date_str] = []
                    # Create a new event object for the new date
                    new_event_on_new_date = {
                        "title": details["title"],
                        "hour": details["hour"],
                        "minute": details["minute"],
                        "duration": details["duration"],
                        "color": details["color"],
                        "icon": details["icon"],
                        "done": details["done"]
                    }
                    all_events[date_str].append(new_event_on_new_date)
                else: # Date is the same, just update
                    event.update({
                        "title": details["title"],
                        "duration": details["duration"],
                        "color": details["color"],
                        "icon": details["icon"]
                    })
                save_events()
            return True
        
        is_current_event = selected_date == datetime.date.today() and start_minutes <= (datetime.datetime.now().hour * 60 + datetime.datetime.now().minute) < (start_minutes + event.get("duration", 60))
        play_btn_rect = pygame.Rect(event_rect.right - 120, event_rect.y + 5, 32, 32)
        if is_current_event and play_btn_rect.collidepoint(x, y):
            show_focus_timer(event)
            return True
    return False


def event_add_window(pos=None, edit_event=None):
    # --- Animation & Style Setup ---
    start_time = time.time() # noqa


def show_coin_counter_popup(event):
    """Displays a small 200x200 popup showing coins earned per minute."""
    win_w, win_h = 200, 200
    try:
        # Attempt to create a borderless window
        win = pygame.display.set_mode((win_w, win_h), pygame.NOFRAME, vsync=1)
    except pygame.error:
        # Fallback for systems that don't support NOFRAME
        win = pygame.display.set_mode((win_w, win_h), vsync=1)
    
    pygame.display.set_caption("Coin Counter")
    clock = pygame.time.Clock()

    # --- Style ---
    BG_COLOR = (35, 40, 55)
    TEXT_COLOR = (230, 230, 255)
    font_large = get_font_wrapper(28)
    font_small = get_font_wrapper(16)

    coins_per_minute = 1 / 5 * 20 # 20 coins per 5 minutes

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN or (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1):
                running = False

        # --- Drawing ---
        win.fill(BG_COLOR)
        
        # Draw a subtle border
        pygame.draw.rect(win, (60, 70, 90), (0, 0, win_w, win_h), 2, border_radius=12)

        # --- Animated Coin Sprite ---
        if coin_sprite_sheet:
            # Update animation frame
            now = pygame.time.get_ticks()
            if now - coin_animation["last_update"] > coin_animation["frame_rate"]:
                coin_animation["last_update"] = now
                coin_animation["current_frame"] = (coin_animation["current_frame"] + 1) % coin_animation["frames_per_row"]

            frame_rect = pygame.Rect(
                coin_animation["current_frame"] * coin_animation["frame_width"],
                coin_animation["current_coin_type"] * coin_animation["frame_height"],
                coin_animation["frame_width"],
                coin_animation["frame_height"]
            )
            frame_image = coin_sprite_sheet.subsurface(frame_rect)
            # Scale it up for the popup
            scaled_coin = pygame.transform.smoothscale(frame_image, (80, 80))
            win.blit(scaled_coin, (win_w // 2 - 40, 30))
        else:
            # Fallback if sprite is missing
            pygame.draw.circle(win, (255, 215, 0), (win_w // 2, 70), 40)

        # --- Text ---
        coins_text = font_large.render(f"+{coins_per_minute:.1f}", True, TEXT_COLOR)
        win.blit(coins_text, (win_w // 2 - coins_text.get_width() // 2, 120))

        per_minute_text = font_small.render("coins/min", True, (150, 160, 180))
        win.blit(per_minute_text, (win_w // 2 - per_minute_text.get_width() // 2, 155))

        pygame.display.flip()
        clock.tick(60)

    # Restore main window display mode
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE, vsync=1)


def show_focus_timer(event):
    """Displays an interactive focus timer for the given event."""
    win_w, win_h = 300, 280
    try:
        win = pygame.display.set_mode((win_w, win_h), pygame.NOFRAME, vsync=1)
    except pygame.error:
        win = pygame.display.set_mode((win_w, win_h), vsync=1)
    
    pygame.display.set_caption("Focus Timer")
    clock = pygame.time.Clock()

    # --- Style & Fonts ---
    BG_COLOR = (35, 40, 55)
    TEXT_COLOR = (230, 230, 255)
    BAR_BG = (50, 60, 80)
    BAR_FG = (0, 255, 150)
    font_title = get_font_wrapper(24)
    font_timer = get_font_wrapper(64)
    font_small = get_font_wrapper(16)

    # --- Timer State ---
    total_seconds = event.get("duration", 60) * 60
    remaining_seconds = total_seconds
    is_paused = True
    last_tick = pygame.time.get_ticks()

    # --- Button Rects ---
    play_pause_btn = pygame.Rect(win_w // 2 - 30, win_h - 80, 60, 60)

    running = True
    while running:
        dt_ms = clock.tick(60)
        mx, my = pygame.mouse.get_pos()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                if e.key == pygame.K_SPACE:
                    is_paused = not is_paused
                    last_tick = pygame.time.get_ticks() # Reset tick to prevent jump
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if play_pause_btn.collidepoint(mx, my):
                    is_paused = not is_paused
                    last_tick = pygame.time.get_ticks() # Reset tick
                # Allow clicking anywhere else to close
                elif not play_pause_btn.collidepoint(mx, my):
                    # Check if click is outside the main button area
                    if not pygame.Rect(0, 0, win_w, win_h).collidepoint(mx,my):
                         running = False

        # --- Timer Logic ---
        if not is_paused and remaining_seconds > 0:
            now = pygame.time.get_ticks()
            delta_seconds = (now - last_tick) / 1000.0
            remaining_seconds -= delta_seconds
            last_tick = now
        
        remaining_seconds = max(0, remaining_seconds)
        if remaining_seconds == 0:
            is_paused = True

        # --- Drawing ---
        win.fill(BG_COLOR)
        pygame.draw.rect(win, (60, 70, 90), (0, 0, win_w, win_h), 2, border_radius=12)

        # Title
        title_surf = font_title.render(truncate_text(event['title'], font_title, win_w - 40), True, TEXT_COLOR)
        win.blit(title_surf, (win_w // 2 - title_surf.get_width() // 2, 20))

        # Timer Text
        time_str = format_time(remaining_seconds)
        timer_surf = font_timer.render(time_str, True, TEXT_COLOR)
        win.blit(timer_surf, (win_w // 2 - timer_surf.get_width() // 2, 70))

        # Progress Bar
        progress = 1.0 - (remaining_seconds / total_seconds) if total_seconds > 0 else 0
        bar_rect = pygame.Rect(30, 160, win_w - 60, 15)
        pygame.draw.rect(win, BAR_BG, bar_rect, border_radius=8)
        fill_w = bar_rect.width * progress
        pygame.draw.rect(win, BAR_FG, (bar_rect.x, bar_rect.y, fill_w, bar_rect.height), border_radius=8)

        # Play/Pause Button
        pygame.draw.circle(win, BAR_FG, play_pause_btn.center, play_pause_btn.width // 2)
        if is_paused: # Draw Play Icon
            pygame.draw.polygon(win, BG_COLOR, [
                (play_pause_btn.centerx - 8, play_pause_btn.centery - 12),
                (play_pause_btn.centerx - 8, play_pause_btn.centery + 12),
                (play_pause_btn.centerx + 12, play_pause_btn.centery)
            ])
        else: # Draw Pause Icon
            pygame.draw.rect(win, BG_COLOR, (play_pause_btn.centerx - 10, play_pause_btn.centery - 10, 8, 20), border_radius=2)
            pygame.draw.rect(win, BG_COLOR, (play_pause_btn.centerx + 2, play_pause_btn.centery - 10, 8, 20), border_radius=2)

        pygame.display.flip()

    # Restore main window display mode
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE, vsync=1)


def event_add_window(pos=None, edit_event=None):
    # --- Animation & Style Setup ---
    start_time = time.time()
    anim_duration = 0.5

    # Colors
    BG_COLOR = (45, 50, 65) if current_theme == "dark" else (250, 250, 255)
    BORDER_COLOR = (60, 70, 90) if current_theme == "dark" else (220, 220, 220)
    TEXT_COLOR = (230, 230, 255) if current_theme == "dark" else (30, 30, 30)
    LABEL_COLOR = (180, 180, 200) if current_theme == "dark" else (100, 100, 100)
    INPUT_BG = (30, 35, 45) if current_theme == "dark" else (235, 235, 240)
    HIGHLIGHT_COLOR = (0, 255, 198)  # Mint
    SHADOW_COLOR = (15, 20, 30, 150)

    # Fonts
    font_title = get_font_wrapper(32)
    font_label = get_font_wrapper(18)
    font_input = get_font_wrapper(20)

    # Window setup
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))

    win_w, win_h = 480, 580
    win_x, win_y = WIDTH // 2 - win_w // 2, HEIGHT // 2 - win_h // 2

    # --- Initial State ---
    title_text = edit_event.get("title", "") if edit_event else ""
    duration = edit_event.get("duration", 60) if edit_event else 60
    # Use a color from the theme's choices, or a default if not found
    color = edit_event.get("color", (255, 220, 120)) if edit_event else (255, 220, 120)
    icon_idx = edit_event.get("icon", 0) if edit_event else 0
    event_date = selected_date
    input_active = "title"
    input_str = title_text
    
    # --- New state for editable start time ---
    start_hour = edit_event["hour"] if edit_event else pos[0]
    start_minute = edit_event.get("minute", 0) if edit_event else pos[1]
    # --- New state for scrolling ---
    scroll_offset = 0
    scroll_velocity = 0

    dragging_duration = False

    color_choices = THEME.get("color_choices", [(255, 220, 120)])
    color_idx = color_choices.index(color) if color in color_choices else 0

    done = False

    # --- Icon picker grid geometry (shared by hit-test and drawing) ---
    ICON_COLS = 6
    ICON_STEP_Y = 48
    ICON_ROWS = max(1, (len(EVENT_ICONS) + ICON_COLS - 1) // ICON_COLS)
    ICON_BLOCK_H = ICON_ROWS * ICON_STEP_Y + 24

    # --- Calculate total content height for scrolling physics ---
    # This is a pre-calculation of the final y_offset to determine scroll bounds early.
    content_height = 0
    content_height += 100 # Date
    content_height += 110 # Time
    content_height += 90  # Title
    content_height += 90  # Duration
    content_height += 90  # Color
    content_height += ICON_BLOCK_H  # Icon grid
    content_height += 100 # Buttons
    content_height += 20  # Padding
    
    while not done:
        # --- Scrolling Physics ---
        visible_height = (win_h - 150) # Corresponds to content_clip_rect height
        max_scroll = max(0, content_height - visible_height + 20) # Add some padding

        scroll_offset += scroll_velocity # Apply velocity
        scroll_velocity *= 0.90 # Apply friction

        mx, my = pygame.mouse.get_pos()
        # Convert mouse y to be relative to the scrollable content area
        content_my = my + scroll_offset

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif e.type == pygame.KEYDOWN:
                if input_active == "title":
                    if e.key == pygame.K_BACKSPACE:
                        input_str = input_str[:-1]
                    elif e.key == pygame.K_RETURN:
                        if input_str.strip():
                            done = True  # OK on enter
                    elif len(input_str) < 64 and e.unicode.isprintable():
                        input_str += e.unicode

            elif e.type == pygame.MOUSEWHEEL:
                # Use the more modern MOUSEWHEEL event for smoother scrolling
                scroll_velocity -= e.y * 5 # Adjust multiplier for sensitivity

            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button != 1:
                    continue
                
                # --- Event handling based on y_offset positions ---
                y_pos = win_y + 90 # Use a separate variable for position tracking
                
                # Use the mouse y-coordinate relative to the scrollable content
                relative_my = my + scroll_offset

                # Date Selection
                date_prev_btn = pygame.Rect(win_x + 40, y_pos + 25 - scroll_offset, 40, 40)
                date_next_btn = pygame.Rect(win_x + win_w - 80, y_pos + 25 - scroll_offset, 40, 40)
                if date_prev_btn.collidepoint(mx, my):
                    event_date -= datetime.timedelta(days=1)
                if date_next_btn.collidepoint(mx, my):
                    event_date += datetime.timedelta(days=1)
                y_pos += 100

                # --- Handle Time Edit Buttons ---
                hour_up_btn = pygame.Rect(win_x + 40, y_pos + 25 - scroll_offset, 40, 20)
                hour_down_btn = pygame.Rect(win_x + 40, y_pos + 45 - scroll_offset, 40, 20)
                minute_up_btn = pygame.Rect(win_x + 120, y_pos + 25 - scroll_offset, 40, 20)
                minute_down_btn = pygame.Rect(win_x + 120, y_pos + 45 - scroll_offset, 40, 20)
                if hour_up_btn.collidepoint(mx, my):
                    start_hour = (start_hour + 1) % 24
                if hour_down_btn.collidepoint(mx, my):
                    start_hour = (start_hour - 1 + 24) % 24
                if minute_up_btn.collidepoint(mx, my):
                    start_minute = (start_minute + 15) % 60
                    if start_minute == 0 and mx > minute_up_btn.x: # If it wrapped around
                        start_hour = (start_hour + 1) % 24
                if minute_down_btn.collidepoint(mx, my):
                    start_minute = (start_minute - 15 + 60) % 60
                    if start_minute == 45 and mx > minute_down_btn.x: # If it wrapped around
                        start_hour = (start_hour - 1 + 24) % 24
                y_pos += 110

                # Title Input
                title_input_rect = pygame.Rect(win_x + 40, y_pos + 25 - scroll_offset, win_w - 80, 40)
                if title_input_rect.collidepoint(mx, my):
                    input_active = "title"
                else:
                    input_active = None
                y_pos += 90

                # Duration Slider
                duration_slider_rect = pygame.Rect(win_x + 40, y_pos + 35 - scroll_offset, win_w - 80, 12)
                if duration_slider_rect.collidepoint(mx, my):
                    dragging_duration = True
                y_pos += 90
                y_pos += 10 # space between title colour and options

                # Color Picker
                for i, c in enumerate(color_choices):
                    radius = 18
                    cx = win_x + 60 + i * ((win_w - 120) / 5) # noqa
                    cy = y_pos + 30 - scroll_offset
                    if (mx - cx) ** 2 + (relative_my - cy) ** 2 < (radius + 5) ** 2:
                        color_idx = i
                        color = color_choices[i]
                y_pos += 90

                for i, icon in enumerate(EVENT_ICONS):
                    col = i % ICON_COLS
                    row = i // ICON_COLS
                    bx = win_x + 60 + col * ((win_w - 120) / (ICON_COLS - 1))
                    by = y_pos + 30 + row * ICON_STEP_Y - scroll_offset
                    if pygame.Rect(bx - 20, by - 20, 40, 40).collidepoint(mx, my):
                        icon_idx = i

                ok_rect = pygame.Rect(
                    win_x + win_w // 2 - 130, win_y + win_h - 65, 120, 40
                )
                cancel_rect = pygame.Rect(
                    win_x + win_w // 2 + 10, win_y + win_h - 65, 120, 40
                )
                if ok_rect.collidepoint(mx, my):
                    if input_str.strip():
                        done = True
                if cancel_rect.collidepoint(mx, my):
                    return None

            elif e.type == pygame.MOUSEBUTTONUP:
                if e.button != 1:
                    continue
                dragging_duration = False

            elif e.type == pygame.MOUSEMOTION:
                if dragging_duration:
                    # Recalculate y for duration slider relative to scroll
                    y_pos = win_y + 90 # date
                    y_pos += 100 # time
                    y_pos += 110 # title
                    y_pos += 90 # to duration section

                    # Correctly calculate slider rect based on its scrolled position
                    slider_rect = pygame.Rect(win_x + 40, y_pos + 35 - scroll_offset, win_w - 80, 12)
                    progress = (mx - slider_rect.x) / slider_rect.width
                    progress = clamp(progress, 0, 1)
                    # Snap to 15-minute intervals from 15 to 240
                    new_duration = 15 + progress * (240 - 15)
                    duration = int(round(new_duration / 15.0)) * 15

        # --- Drawing ---
        screen.blit(overlay, (0, 0))

        # Animation progress
        elapsed = time.time() - start_time
        anim_progress = min(1.0, elapsed / anim_duration)
        ease_out = 1 - pow(1 - anim_progress, 4)

        # Parallax effect
        parallax_x = (mx - (win_x + win_w / 2)) / (win_w / 2)
        parallax_y = (my - (win_y + win_h / 2)) / (win_h / 2)

        # Draw window with animation
        current_w, current_h = win_w * ease_out, win_h * ease_out
        current_x, current_y = (
            win_x + (win_w - current_w) / 2,
            win_y + (win_h - current_h) / 2,
        )
        win_rect = pygame.Rect(current_x, current_y, current_w, current_h)

        # Shadow and main window background
        shadow_surf = pygame.Surface((win_w + 20, win_h + 20), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surf, SHADOW_COLOR, (10, 10, win_w, win_h), border_radius=24
        )
        screen.blit(
            pygame.transform.smoothscale(shadow_surf, (current_w + 20, current_h + 20)),
            (current_x - 10, current_y - 10),
        )
        pygame.draw.rect(screen, BG_COLOR, win_rect, border_radius=20)
        pygame.draw.rect(screen, BORDER_COLOR, win_rect, 1, border_radius=20)

        # --- Content (with fade-in and parallax) ---
        content_alpha = int(255 * ease_out)

        # Title
        title_text_str = "Add Event" if not edit_event else "Edit Event"
        title_surf = font_title.render(title_text_str, True, TEXT_COLOR)
        title_surf.set_alpha(content_alpha)
        screen.blit(
            title_surf,
            # Parallax effect for the title
            (
                win_rect.centerx - title_surf.get_width() / 2 + parallax_x * -2,
                win_rect.y + 30 + parallax_y * -4,
            ),
        )

        # --- Clipping area for scrollable content ---
        content_clip_rect = pygame.Rect(win_x, win_y  + 80, win_w, win_h - 150)
        screen.set_clip(content_clip_rect)

        # --- Date Selection ---
        date_label_surf = font_label.render("Date", True, LABEL_COLOR) # noqa
        date_label_surf.set_alpha(content_alpha)
        screen.blit(date_label_surf, (win_rect.x + 40, y_offset - scroll_offset))
        date_prev_btn = pygame.Rect(win_rect.x + 40, y_offset + 25 - scroll_offset, 40, 40)
        date_next_btn = pygame.Rect(win_rect.right - 80, y_offset + 25 - scroll_offset, 40, 40)
        pygame.draw.rect(screen, INPUT_BG, date_prev_btn, border_radius=8)
        pygame.draw.rect(screen, INPUT_BG, date_next_btn, border_radius=8)
        pygame.draw.polygon(screen, TEXT_COLOR, [(date_prev_btn.centerx - 3, date_prev_btn.centery), (date_prev_btn.centerx + 5, date_prev_btn.centery - 8), (date_prev_btn.centerx + 5, date_prev_btn.centery + 8)])
        pygame.draw.polygon(screen, TEXT_COLOR, [(date_next_btn.centerx + 3, date_next_btn.centery), (date_next_btn.centerx - 5, date_next_btn.centery - 8), (date_next_btn.centerx - 5, date_next_btn.centery + 8)])
        date_str = event_date.strftime("%a, %d %b %Y")
        date_text_surf = font_input.render(date_str, True, TEXT_COLOR)
        date_text_surf.set_alpha(content_alpha)
        screen.blit(date_text_surf, (win_rect.centerx - date_text_surf.get_width() // 2, y_offset + 33 - scroll_offset))
        y_offset += 100
        pygame.draw.line(screen, BORDER_COLOR, (win_x + 30, y_offset - 10 - scroll_offset), (win_x + win_w - 30, y_offset - 10 - scroll_offset), 1)

        # --- Time Display ---
        start_dt = datetime.datetime(2000, 1, 1, start_hour, start_minute)
        end_dt = start_dt + datetime.timedelta(minutes=duration)
        
        start_time_str = start_dt.strftime("%I:%M %p")
        end_time_str = end_dt.strftime("%I:%M %p")

        time_label_surf = font_label.render("Start Time", True, LABEL_COLOR) # noqa
        time_label_surf.set_alpha(content_alpha)
        # screen.blit(time_label_surf, (win_rect.x + 40, win_rect.y + 135 + y_offset + scroll_offset ))

        screen.blit(time_label_surf, (win_rect.x + 40, y_offset - scroll_offset))
        # Hour Control
        hour_up_btn = pygame.Rect(win_rect.x + 40, y_offset + 25 - scroll_offset, 40, 20)
        hour_down_btn = pygame.Rect(win_rect.x + 40, y_offset + 45 - scroll_offset, 40, 20)
        pygame.draw.rect(screen, INPUT_BG, hour_up_btn, border_top_left_radius=8, border_top_right_radius=8)
        pygame.draw.rect(screen, INPUT_BG, hour_down_btn, border_bottom_left_radius=8, border_bottom_right_radius=8)
        pygame.draw.polygon(screen, TEXT_COLOR, [(hour_up_btn.centerx, hour_up_btn.centery - 4), (hour_up_btn.centerx - 5, hour_up_btn.centery + 4), (hour_up_btn.centerx + 5, hour_up_btn.centery + 4)])
        pygame.draw.polygon(screen, TEXT_COLOR, [(hour_down_btn.centerx, hour_down_btn.centery + 4), (hour_down_btn.centerx - 5, hour_down_btn.centery - 4), (hour_down_btn.centerx + 5, hour_down_btn.centery - 4)])
        hour_text_surf = font_input.render(f"{start_dt.strftime('%I')}", True, TEXT_COLOR)
        # screen.blit(hour_text_surf, (win_rect.x + 85, win_rect.y + 162 - scroll_offset))
        screen.blit(hour_text_surf, (win_rect.x + 85, y_offset + 32 - scroll_offset))
        # Minute Control
        minute_up_btn = pygame.Rect(win_rect.x + 120, y_offset + 25 - scroll_offset, 40, 20)
        minute_down_btn = pygame.Rect(win_rect.x + 120, y_offset + 45 - scroll_offset, 40, 20)
        pygame.draw.rect(screen, INPUT_BG, minute_up_btn, border_top_left_radius=8, border_top_right_radius=8)
        pygame.draw.rect(screen, INPUT_BG, minute_down_btn, border_bottom_left_radius=8, border_bottom_right_radius=8)
        pygame.draw.polygon(screen, TEXT_COLOR, [(minute_up_btn.centerx, minute_up_btn.centery - 4), (minute_up_btn.centerx - 5, minute_up_btn.centery + 4), (minute_up_btn.centerx + 5, minute_up_btn.centery + 4)])
        pygame.draw.polygon(screen, TEXT_COLOR, [(minute_down_btn.centerx, minute_down_btn.centery + 4), (minute_down_btn.centerx - 5, minute_down_btn.centery - 4), (minute_down_btn.centerx + 5, minute_down_btn.centery - 4)])
        minute_text_surf = font_input.render(f":{start_dt.strftime('%M')}", True, TEXT_COLOR)
        # screen.blit(minute_text_surf, (win_rect.x + 165, win_rect.y + 162))
        screen.blit(minute_text_surf, (win_rect.x + 165, y_offset + 32 - scroll_offset))
        # AM/PM Display
        ampm_text_surf = font_input.render(f"{start_dt.strftime('%p')}", True, TEXT_COLOR)
        # screen.blit(ampm_text_surf, (win_rect.x + 210, win_rect.y + 162))
        screen.blit(ampm_text_surf, (win_rect.x + 210, y_offset + 32 - scroll_offset))
        # End Time Display
        end_time_label_surf = font_label.render("End Time", True, LABEL_COLOR) # noqa
        end_time_label_surf.set_alpha(content_alpha)
        # screen.blit(end_time_label_surf, (win_rect.x + win_rect.width - 160, win_rect.y + 135))
        screen.blit(end_time_label_surf, (win_rect.x + win_rect.width - 160, y_offset - scroll_offset))
        end_time_text_surf = font_input.render(end_time_str, True, TEXT_COLOR)
        end_time_text_surf.set_alpha(content_alpha)
        end_time_box_rect = pygame.Rect(win_rect.x + win_rect.width - 160, y_offset + 25 - scroll_offset, 120, 40)
        pygame.draw.rect(screen, INPUT_BG, end_time_box_rect, border_radius=8)
        screen.blit(
            end_time_text_surf,
            (end_time_box_rect.centerx - end_time_text_surf.get_width() // 2,
             end_time_box_rect.centery - end_time_text_surf.get_height() // 2)
        )
        y_offset += 110
        pygame.draw.line(screen, BORDER_COLOR, (win_x + 30, y_offset - 10 - scroll_offset), (win_x + win_w - 30, y_offset - 10 - scroll_offset), 1)

        # Event Title Input
        label_surf = font_label.render("Title", True, LABEL_COLOR)
        label_surf.set_alpha(content_alpha)
        screen.blit(label_surf, (win_rect.x + 40, y_offset - scroll_offset))
        input_rect = pygame.Rect(win_rect.x + 40, y_offset + 25 - scroll_offset, win_rect.width - 80, 40)
        pygame.draw.rect(screen, INPUT_BG, input_rect, border_radius=8)
        if input_active == "title":
            pygame.draw.rect(screen, HIGHLIGHT_COLOR, input_rect, 2, border_radius=8)

        input_text_surf = font_input.render(
            input_str
            + (
                "|" if input_active == "title" and int(time.time() * 2) % 2 == 0 else ""
            ),
            True,
            TEXT_COLOR,
        )
        input_text_surf.set_alpha(content_alpha)
        screen.blit(
            input_text_surf,
            (input_rect.x + 12, input_rect.y + 5),
        )
        screen.blit(input_text_surf, (input_rect.x + 12, input_rect.y + 5))
        y_offset += 90
        pygame.draw.line(screen, BORDER_COLOR, (win_x + 30, y_offset - 10 - scroll_offset), (win_x + win_w - 30, y_offset - 10 - scroll_offset), 1)

        # Duration Slider
        dur_label_surf = font_label.render(
            f"Duration: {duration} min", True, LABEL_COLOR
        )
        dur_label_surf.set_alpha(content_alpha)
        screen.blit(dur_label_surf, (win_rect.x + 40, y_offset - scroll_offset))
        slider_rect = pygame.Rect(win_rect.x + 40, y_offset + 35 - scroll_offset, win_rect.width - 80, 12)
        pygame.draw.rect(screen, INPUT_BG, slider_rect, border_radius=6)

        progress = (duration - 15) / (240 - 15)
        fill_w = int(slider_rect.width * progress)
        pygame.draw.rect(
            screen,
            HIGHLIGHT_COLOR,
            (slider_rect.x, slider_rect.y, fill_w, slider_rect.height),
            border_radius=6,
        )

        knob_x = slider_rect.x + fill_w
        pygame.draw.circle(screen, (255, 255, 255), (knob_x, slider_rect.centery), 10)
        pygame.draw.circle(
            screen, HIGHLIGHT_COLOR, (knob_x, slider_rect.centery), 10, 2
        )
        y_offset += 90
        pygame.draw.line(screen, BORDER_COLOR, (win_x + 30, y_offset - 10 - scroll_offset), (win_x + win_w - 30, y_offset - 10 - scroll_offset), 1)

        # Color Picker
        color_label_surf = font_label.render("Color", True, LABEL_COLOR)
        color_label_surf.set_alpha(content_alpha)
        screen.blit(color_label_surf, (win_rect.x + 40, y_offset - scroll_offset))
        y_offset += 10 # space between title colour and options
        for i, c in enumerate(color_choices):
            cx = win_rect.x + 60 + i * ((win_rect.width - 120) / 5)
            cy = y_offset + 30 - scroll_offset
            radius = 18
            is_hovered = (mx - cx) ** 2 + (my - cy) ** 2 < (radius + 5) ** 2
            current_radius = radius + 3 * ease_out if is_hovered else radius
            pygame.draw.circle(screen, c, (cx, cy), current_radius)
            if i == color_idx:
                pygame.draw.circle(
                    screen, HIGHLIGHT_COLOR, (cx, cy), current_radius + 2, 3
                )
        y_offset += 90
        pygame.draw.line(screen, BORDER_COLOR, (win_x + 30, y_offset - 10 - scroll_offset), (win_x + win_w - 30, y_offset - 10 - scroll_offset), 1)

        # Icon Picker
        icon_label_surf = font_label.render("Icon", True, LABEL_COLOR)
        icon_label_surf.set_alpha(content_alpha)
        screen.blit(icon_label_surf, (win_rect.x + 40, y_offset - scroll_offset))
        for i, icon in enumerate(EVENT_ICONS):
            col = i % ICON_COLS
            row = i // ICON_COLS
            cx = win_rect.x + 60 + col * ((win_rect.width - 120) / (ICON_COLS - 1))
            cy = y_offset + 30 + row * ICON_STEP_Y - scroll_offset
            is_hovered = pygame.Rect(cx - 20, cy - 20, 40, 40).collidepoint(mx, my)

            bg_color = (
                tuple(min(c + 20, 255) for c in INPUT_BG) if is_hovered else INPUT_BG
            )
            pygame.draw.rect(
                screen, bg_color, (cx - 20, cy - 20, 40, 40), border_radius=10
            )
            if icon:
                icon_size = 32
                icon_surf = pygame.transform.smoothscale(icon, (icon_size, icon_size))
                icon_surf.set_alpha(content_alpha)
                screen.blit(icon_surf, (cx - icon_size / 2, cy - icon_size / 2))
            if i == icon_idx:
                pygame.draw.rect(
                    screen,
                    HIGHLIGHT_COLOR,
                    (cx - 22, cy - 22, 44, 44),
                    2,
                    border_radius=12,
                )
        y_offset += ICON_BLOCK_H

        # --- Bounce-back logic ---
        if scroll_offset < 0:
            # If overscrolled at the top, apply a force pulling it back down
            scroll_offset *= 0.85 # Dampen the overscroll
            scroll_velocity += (-scroll_offset) * 0.1 # Apply restoring force
        elif scroll_offset > max_scroll:
            # If overscrolled at the bottom, pull it back up
            scroll_offset = (scroll_offset - max_scroll) * 0.85 + max_scroll # Dampen
            scroll_velocity += (max_scroll - scroll_offset) * 0.1 # Apply restoring force


        # --- Reset clipping to draw fixed elements ---
        screen.set_clip(None)

        # Draw visual scrollbar
        if max_scroll > 0:
            scrollbar_h = visible_height * (visible_height / content_height)
            scrollbar_y = content_clip_rect.y + (scroll_offset / max_scroll) * (visible_height - scrollbar_h)
            pygame.draw.rect(screen, (100,100,100,100), (win_x + win_w - 15, scrollbar_y, 8, scrollbar_h), border_radius=4)
        
        # Buttons
        ok_rect = pygame.Rect(win_rect.centerx - 130, win_rect.bottom - 60, 120, 40)
        cancel_rect = pygame.Rect(win_rect.centerx + 10, win_rect.bottom - 60, 120, 40)

        ok_color = (0, 200, 150) if ok_rect.collidepoint(mx, my) else (0, 180, 130)
        cancel_color = (
            (255, 120, 120) if cancel_rect.collidepoint(mx, my) else (255, 100, 100)
        )
        pygame.draw.rect(screen, ok_color, ok_rect, border_radius=12)
        pygame.draw.rect(screen, cancel_color, cancel_rect, border_radius=12)

        ok_txt = get_font_wrapper(22).render("Save", True, (255, 255, 255))
        cancel_txt = get_font_wrapper(22).render("Cancel", True, (255, 255, 255))
        ok_txt.set_alpha(content_alpha)
        cancel_txt.set_alpha(content_alpha)
        screen.blit(ok_txt, (ok_rect.centerx - ok_txt.get_width() / 2, ok_rect.centery - ok_txt.get_height() / 2))
        screen.blit(
            cancel_txt,
            (
                cancel_rect.centerx - cancel_txt.get_width() / 2,
                cancel_rect.centery - cancel_txt.get_height() / 2,
            ),
        )

        pygame.display.flip()
        pygame.time.wait(16)

    return {
        "title": input_str.strip(),
        "duration": duration,
        "color": color,
        "icon": icon_idx,
        "date": event_date.strftime("%Y-%m-%d"),
        "done": edit_event["done"] if edit_event else False,
        "hour": start_hour,
        "minute": start_minute,
    }

def todo_add_window_v2():
    """A modern, animated window to add a to-do item with folder selection."""
    start_time = time.time()
    anim_duration = 0.4

    # --- Style ---
    BG_COLOR = (45, 50, 65) if "Dark" in current_theme else (250, 250, 255)
    BORDER_COLOR = (60, 70, 90) if "Dark" in current_theme else (220, 220, 220)
    TEXT_COLOR = (230, 230, 255) if "Dark" in current_theme else (30, 30, 30)
    LABEL_COLOR = (180, 180, 200) if "Dark" in current_theme else (100, 100, 100)
    INPUT_BG = (30, 35, 45) if "Dark" in current_theme else (235, 235, 240)
    HIGHLIGHT_COLOR = (0, 255, 198)

    # --- Fonts ---
    font_title = get_font_wrapper(28)
    font_label = get_font_wrapper(18)
    font_input = get_font_wrapper(22)

    # --- Window Setup ---
    win_w, win_h = 450, 300
    target_x, target_y = WIDTH // 2 - win_w // 2, HEIGHT // 2 - win_h // 2

    # --- State ---
    input_str = ""
    selected_parent = todos  # Default to root
    dropdown_open = False

    def get_folder_options(items, level=0):
        """Recursively get a flat list of folder options for the dropdown."""
        options = []
        for item in items:
            if item.get("type") == "folder":
                options.append({"name": "  " * level + item.get("name", "Untitled"), "item_list": item.get("children", [])})
                options.extend(get_folder_options(item.get("children", []), level + 1))
        return options

    folder_options = [{"name": "Root Level", "item_list": todos}] + get_folder_options(todos)

    while True:
        # --- Animation ---
        elapsed = time.time() - start_time
        anim_progress = min(1.0, elapsed / anim_duration)
        ease_out = 1 - pow(1 - anim_progress, 4)

        current_w = win_w * ease_out
        current_h = win_h * ease_out
        current_x = target_x + (win_w - current_w) / 2
        current_y = target_y + (win_h - current_h) / 2
        win_rect = pygame.Rect(current_x, current_y, current_w, current_h)

        # --- Event Handling ---
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(), sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    if input_str.strip():
                        new_todo = {"title": input_str.strip(), "done": False, "type": "todo"}
                        selected_parent.append(new_todo)
                        save_todos()
                        return
                elif e.key == pygame.K_ESCAPE:
                    return
                elif e.key == pygame.K_BACKSPACE:
                    input_str = input_str[:-1]
                elif len(input_str) < 64 and e.unicode.isprintable():
                    input_str += e.unicode
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                dropdown_rect = pygame.Rect(win_rect.x + 40, win_rect.y + 150, win_rect.width - 80, 40)
                if dropdown_rect.collidepoint(mx, my):
                    dropdown_open = not dropdown_open
                    continue
                elif dropdown_open:
                    option_clicked = False
                    for i, option in enumerate(folder_options):
                        option_rect = pygame.Rect(dropdown_rect.x, dropdown_rect.bottom + i * 35, dropdown_rect.width, 35)
                        if option_rect.collidepoint(mx, my):
                            selected_parent = option["item_list"]
                            dropdown_open = False
                            option_clicked = True
                            break
                    if option_clicked:
                        continue
                    else: # Clicked outside dropdown
                        dropdown_open = False
                        # We don't continue here, so the click can also trigger buttons if clicked outside
                
                # Check buttons only if dropdown was not open (or just closed by clicking outside, though we might want to prevent that too)
                if dropdown_open:
                    continue

                ok_rect = pygame.Rect(win_rect.centerx - 130, win_rect.bottom - 60, 120, 40)
                cancel_rect = pygame.Rect(win_rect.centerx + 10, win_rect.bottom - 60, 120, 40)
                if ok_rect.collidepoint(mx, my) and input_str.strip():
                    new_todo = {"title": input_str.strip(), "done": False, "type": "todo"}
                    selected_parent.append(new_todo)
                    save_todos()
                    return
                if cancel_rect.collidepoint(mx, my):
                    return

        # --- Drawing ---
        screen.blit(screen.copy(), (0,0)) # Redraw main screen underneath
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0,0))

        pygame.draw.rect(screen, BG_COLOR, win_rect, border_radius=18)
        pygame.draw.rect(screen, BORDER_COLOR, win_rect, 1, border_radius=18)

        content_alpha = int(255 * ease_out)
        
        # Title
        title_surf = font_title.render("Add New To-Do", True, TEXT_COLOR)
        title_surf.set_alpha(content_alpha)
        screen.blit(title_surf, (win_rect.centerx - title_surf.get_width() / 2, win_rect.y + 20))

        # Input Box
        input_rect = pygame.Rect(win_rect.x + 40, win_rect.y + 80, win_rect.width - 80, 40)
        pygame.draw.rect(screen, INPUT_BG, input_rect, border_radius=8)
        pygame.draw.rect(screen, HIGHLIGHT_COLOR, input_rect, 2, border_radius=8)
        cursor = "|" if int(time.time() * 2) % 2 == 0 else ""
        txt_surf = font_input.render(input_str + cursor, True, TEXT_COLOR)
        txt_surf.set_alpha(content_alpha)
        screen.blit(txt_surf, (input_rect.x + 12, input_rect.y + 6))

        # Folder Dropdown
        dropdown_rect = pygame.Rect(win_rect.x + 40, win_rect.y + 150, win_rect.width - 80, 40)
        pygame.draw.rect(screen, INPUT_BG, dropdown_rect, border_radius=8)
        selected_folder_name = next((opt['name'] for opt in folder_options if opt['item_list'] is selected_parent), "Select Folder")
        folder_txt = font_input.render(selected_folder_name.strip(), True, TEXT_COLOR)
        screen.blit(folder_txt, (dropdown_rect.x + 12, dropdown_rect.centery - folder_txt.get_height()//2))
        
        # Buttons
        ok_rect = pygame.Rect(win_rect.centerx - 130, win_rect.bottom - 60, 120, 40)
        cancel_rect = pygame.Rect(win_rect.centerx + 10, win_rect.bottom - 60, 120, 40)
        
        # Dim buttons if dropdown is open
        btn_alpha = 100 if dropdown_open else 255
        
        ok_btn_surf = pygame.Surface(ok_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(ok_btn_surf, (0, 180, 130, btn_alpha), ok_btn_surf.get_rect(), border_radius=12)
        screen.blit(ok_btn_surf, ok_rect.topleft)
        
        cancel_btn_surf = pygame.Surface(cancel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(cancel_btn_surf, (255, 100, 100, btn_alpha), cancel_btn_surf.get_rect(), border_radius=12)
        screen.blit(cancel_btn_surf, cancel_rect.topleft)

        ok_txt = get_font_wrapper(22).render("Save", True, (255, 255, 255))
        ok_txt.set_alpha(btn_alpha)
        cancel_txt = get_font_wrapper(22).render("Cancel", True, (255, 255, 255))
        cancel_txt.set_alpha(btn_alpha)
        
        screen.blit(ok_txt, (ok_rect.centerx - ok_txt.get_width() / 2, ok_rect.centery - ok_txt.get_height() / 2))
        screen.blit(cancel_txt, (cancel_rect.centerx - cancel_txt.get_width() / 2, cancel_rect.centery - cancel_txt.get_height() / 2))

        # Dropdown options if open (drawn last to be on top)
        if dropdown_open:
            for i, option in enumerate(folder_options):
                option_rect = pygame.Rect(dropdown_rect.x, dropdown_rect.bottom + i * 35, dropdown_rect.width, 35)
                pygame.draw.rect(screen, INPUT_BG, option_rect)
                option_text = font_input.render(option['name'], True, TEXT_COLOR)
                screen.blit(option_text, (option_rect.x + 10, option_rect.y + 5))

        pygame.display.flip()
        pygame.time.wait(16)



def todo_add_window():
    """A simple window to get text input for a new or edited todo item."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    win_w, win_h = 400, 200
    win_x, win_y = WIDTH // 2 - win_w // 2, HEIGHT // 2 - win_h // 2
    pygame.draw.rect(
        screen, THEME["settings_bg"], (win_x, win_y, win_w, win_h), border_radius=18
    )
    pygame.draw.rect(
        screen, (200, 200, 200), (win_x, win_y, win_w, win_h), 4, border_radius=18
    )

    font_title = get_font_wrapper(28)
    title = font_title.render("Add To-Do Item", True, THEME["text"])
    screen.blit(title, (win_x + win_w // 2 - title.get_width() // 2, win_y + 18))

    input_rect = pygame.Rect(win_x + 40, win_y + 70, 320, 36)
    input_str = ""
    font_input = get_font_wrapper(22)

    # Keep drawing the main view underneath
    draw_day_view({})  # No drag state here
    draw_todo_list(pygame.mouse.get_pos(), -1)

    done = False
    while not done:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(), sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    if input_str.strip():
                        return {"title": input_str.strip()}
                    else:
                        return None
                elif e.key == pygame.K_ESCAPE:
                    return None
                elif e.key == pygame.K_BACKSPACE:
                    input_str = input_str[:-1]
                elif len(input_str) < 40:
                    input_str += e.unicode

        # Redraw input box and text
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(
            screen, THEME["settings_bg"], (win_x, win_y, win_w, win_h), border_radius=18
        )
        pygame.draw.rect(
            screen, (200, 200, 200), (win_x, win_y, win_w, win_h), 4, border_radius=18
        )
        screen.blit(title, (win_x + win_w // 2 - title.get_width() // 2, win_y + 18))
        pygame.draw.rect(screen, (230, 230, 230), input_rect, border_radius=8)
        txt_surf = font_input.render(input_str + "|", True, THEME["text"])
        screen.blit(txt_surf, (input_rect.x + 8, input_rect.y + 5))

        # Instructions
        font_instr = get_font_wrapper(16)
        instr_surf = font_instr.render(
            "Press Enter to save, Esc to cancel", True, (100, 100, 100)
        )
        screen.blit(
            instr_surf, (win_x + win_w // 2 - instr_surf.get_width() // 2, win_y + 140)
        )

        pygame.display.flip()
        pygame.time.wait(16)


def todo_edit_window(todo_text):
    """A modern, animated, glass-like window to edit a todo item."""
    start_time = time.time()

    # Capture the screen for the glass effect
    background_capture = screen.copy()

    anim_duration = 0.4

    # --- Window & Style ---
    win_w, win_h = 400, 200
    target_x, target_y = WIDTH // 2 - win_w // 2, HEIGHT // 2 - win_h // 2

    # --- Fonts & Colors ---
    BG_COLOR = (45, 50, 65, 200) if current_theme == "dark" else (250, 250, 255, 200)
    BORDER_COLOR = (60, 70, 90) if current_theme == "dark" else (220, 220, 220)
    TEXT_COLOR = (230, 230, 255) if current_theme == "dark" else (30, 30, 30)
    INPUT_BG = (30, 35, 45) if current_theme == "dark" else (235, 235, 240)
    HIGHLIGHT_COLOR = (0, 255, 198)
    
    font_title = get_font_wrapper(28)
    font_input = get_font_wrapper(22)
    title_surf = font_title.render("Edit To-Do Item", True, TEXT_COLOR)

    # --- State ---
    input_str = todo_text

    while True:
        # --- Animation ---
        elapsed = time.time() - start_time
        anim_progress = min(1.0, elapsed / anim_duration)
        ease_out = 1 - pow(1 - anim_progress, 4)

        # Animate window position and size
        current_w = win_w * ease_out
        current_h = win_h * ease_out
        current_x = target_x + (win_w - current_w) / 2
        current_y = target_y + (win_h - current_h) / 2
        win_rect = pygame.Rect(current_x, current_y, current_w, current_h)

        # --- Event Handling ---
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(), sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    return input_str.strip() if input_str.strip() else None
                elif e.key == pygame.K_ESCAPE:
                    return None
                elif e.key == pygame.K_BACKSPACE:
                    input_str = input_str[:-1]
                elif len(input_str) < 40 and e.unicode.isprintable():
                    input_str += e.unicode

        # --- Drawing ---
        # 1. Capture the background for the glass effect
        glass_area = screen.subsurface(win_rect).copy()
        glass_area = pygame.transform.smoothscale(glass_area, (win_rect.width // 8, win_rect.height // 8))
        glass_area = pygame.transform.smoothscale(glass_area, win_rect.size)

        # 2. Draw the blurred background and the semi-transparent overlay
        screen.blit(glass_area, win_rect.topleft)
        pygame.draw.rect(screen, BG_COLOR, win_rect, border_radius=18)
        pygame.draw.rect(screen, BORDER_COLOR, win_rect, 1, border_radius=18)

        # 3. Draw content (fades in with animation)
        content_alpha = int(255 * ease_out)
        title_surf.set_alpha(content_alpha)
        screen.blit(
            title_surf,
            (
                win_rect.centerx - title_surf.get_width() / 2,
                win_rect.y + 18,
            ),
        )

        # Input box
        input_rect = pygame.Rect(win_rect.x + 40, win_rect.y + 70, win_rect.width - 80, 40)
        pygame.draw.rect(screen, INPUT_BG, input_rect, border_radius=8)
        pygame.draw.rect(screen, HIGHLIGHT_COLOR, input_rect, 2, border_radius=8)

        # Input text with cursor
        cursor = "|" if int(time.time() * 2) % 2 == 0 else ""
        txt_surf = font_input.render(input_str + cursor, True, TEXT_COLOR)
        txt_surf.set_alpha(content_alpha)
        screen.blit(txt_surf, (input_rect.x + 12, input_rect.y + 6))

        pygame.display.flip()
        pygame.time.wait(16)


# --- COUNTDOWN WINDOW (PYGAME) ---
def show_countdown(event):
    win = pygame.display.set_mode((400, 200), pygame.NOFRAME)
    pygame.display.set_caption("Event Countdown")
    start = datetime.datetime.now().replace(
        hour=event["hour"], minute=event["minute"], second=0, microsecond=0
    )
    end_time = start + datetime.timedelta(minutes=event["duration"])
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN or (
                e.type == pygame.MOUSEBUTTONDOWN and e.button == 1
            ):
                running = False
        win.fill((30, 40, 30))
        now = datetime.datetime.now() # noqa
        remaining = end_time - now
        total_sec = event["duration"] * 60
        left_sec = max(0, int(remaining.total_seconds()))
        progress = 1 - left_sec / total_sec if total_sec else 1
        pygame.draw.rect(
            win, (60, 180, 60), (40, 120, int(320 * progress), 24), border_radius=12
        )
        pygame.draw.rect(win, (200, 200, 200), (40, 120, 320, 24), 2, border_radius=12)
        font = get_font_wrapper(36)
        if left_sec > 0:
            txt = font.render(str(remaining).split(".")[0], True, (255, 255, 255))
        else:
            txt = font.render("Done!", True, (120, 255, 120))
        win.blit(txt, (200 - txt.get_width() // 2, 60))
        pygame.display.flip()
        pygame.time.wait(100)
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)


# def toggle_checkbox_at_pos(pos):
#     """
#     Hit-test the checkbox for each event using the exact same layout math
#     as draw_day_view(). Returns True if a checkbox was toggled.
#     """
#     x, y = pos

#     # Iterate events and compute their on-screen rects (same math as draw_day_view)
#     for ev in events:
#         start_minutes = ev["hour"] * 60 + ev.get("minute", 0)
#         event_start_y = TOP_Y + (start_minutes - START_HOUR * 60) * (HOUR_HEIGHT / 60)
#         event_height = max(24, (ev.get("duration", 60)) * (HOUR_HEIGHT / 60))

#         # EXACT same layout constants used in draw_day_view
#         ICON_MAX = 40
#         icon_size = max(0, min(int(event_height - 16), ICON_MAX))
#         icon_x = EVENT_X + 12
#         # checkbox placed after icon + gap
#         # checkbox_x = icon_x + icon_size + 8
#         checkbox_x = EVENT_X + 28 + 20  # fixed position after icon area
#         # checkbox_y = int(event_start_y + (event_height - CHECKBOX_SIZE) / 2)
#         checkbox_y = int(event_start_y + 10)

#         checkbox_rect = pygame.Rect(
#             checkbox_x, checkbox_y, CHECKBOX_SIZE, CHECKBOX_SIZE
#         )
#
#         if checkbox_rect.collidepoint(x, y):
#             # toggle done state and trigger confetti/sound when marking done
#             new_state = not ev.get("done", False)
#             ev["done"] = new_state
#             if new_state:

#                 spawn_confetti(
#                     checkbox_x + CHECKBOX_SIZE // 2, checkbox_y + CHECKBOX_SIZE // 2
#                 )
#                 if DING_SOUND:
#                     try:
#                         DING_SOUND.play()
#                     except Exception:
#                         pass
#             save_events()
#             return True

#     return False


# --- NEW ADVANCED TIMER FUNCTIONS (from progress.py) ---

class Particle:
    def __init__(self, pos, vel, life, color, size):
        self.pos = list(pos)
        self.vel = list(vel)
        self.life = life
        self.maxlife = life
        self.color = color
        self.size = size

    def update(self, dt):
        self.life -= dt
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.vel[0] *= 0.995
        self.vel[1] *= 0.995

    def draw(self, surf):
        a = max(0, min(255, int(255 * (self.life / self.maxlife))))
        col = (*self.color[:3], a)
        r = max(1, int(self.size * (self.life / self.maxlife)))
        if r < 1:
            return

        s = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        gfxdraw.filled_circle(s, r * 2, r * 2, r, col)
        gfxdraw.aacircle(s, r * 2, r * 2, r, col)
        surf.blit(
            s,
            (self.pos[0] - r * 2, self.pos[1] - r * 2),
            special_flags=pygame.BLEND_PREMULTIPLIED,
        )


# def timer_process_target(event_dict, result_queue):
#     """Target function for the advanced multiprocessing timer window."""
#     pygame.init()
#     pygame.font.init()

#     # --- Window Dragging & Resizing Setup ---
#     try:
#         import ctypes
#         from ctypes import wintypes

#         ctypes.windll.user32.SetProcessDPIAware()
#     except (ImportError, AttributeError):
#         ctypes = None  # Not on Windows

#     # Config
#     W, H = 350, 350  # Start with a smaller default size
#     CENTER = (W // 2, H // 2)
#     FPS = 120 # noqa
#     RADIUS = 250

#     # Colors
#     BG_TOP = (12, 14, 20)
#     BG_BOTTOM = (18, 24, 36)
#     ACCENT = (84, 210, 255)
#     ACCENT2 = (150, 90, 255)
#     WHITE = (240, 242, 245)

#     screen = pygame.display.set_mode((W, H), pygame.RESIZABLE | pygame.NOFRAME, vsync=1)
#     pygame.display.set_caption(f"Focus Timer - {event_dict['title']}")

#     clock = pygame.time.Clock()
#     font_large = pygame.font.SysFont("Segoe UI", 64, bold=True)
#     font_medium = pygame.font.SysFont("Segoe UI", 28)
#     font_small = pygame.font.SysFont("Segoe UI", 18)

#     particles = []

#     def draw_ring(surface, radius, width, phase, colors=(ACCENT, ACCENT2)):
#         steps = 180
#         for i in range(steps):
#             a0 = (i / steps) * math.tau + phase
#             a1 = ((i + 1) / steps) * math.tau + phase
#             x0 = CENTER[0] + math.cos(a0) * radius
#             y0 = CENTER[1] + math.sin(a0) * radius
#             x1 = CENTER[0] + math.cos(a1) * (radius - width)
#             y1 = CENTER[1] + math.sin(a1) * (radius - width)
#             t = i / steps
#             col = (
#                 int(colors[0][0] * (1 - t) + colors[1][0] * t),
#                 int(colors[0][1] * (1 - t) + colors[1][1] * t),
#                 int(colors[0][2] * (1 - t) + colors[1][2] * t),
#                 16,
#             )
#             gfxdraw.filled_trigon(
#                 surface,
#                 int(x0),
#                 int(y0),
#                 int(x1),
#                 int(y1),
#                 int(CENTER[0] + math.cos(a0) * (radius - width / 2)),
#                 int(CENTER[1] + math.sin(a0) * (radius - width / 2)),
#                 col,
#             )

#     def draw_ticks(surface, radius, thickness, progress):
#         count = 60
#         for i in range(count):
#             a = (i / count) * math.tau - math.pi / 2
#             x = CENTER[0] + math.cos(a) * (radius)
#             y = CENTER[1] + math.sin(a) * (radius)
#             inner = CENTER[0] + math.cos(a) * (radius - thickness)
#             inner_y = CENTER[1] + math.sin(a) * (radius - thickness)
#             edge = progress * math.tau - math.pi / 2
#             diff = abs(((a - edge + math.pi) % math.tau) - math.pi)
#             brightness = max(0, 1 - diff * 2.5)
#             alpha = int(80 * (0.4 + 0.6 * brightness))
#             col = (*WHITE[:3], alpha)
#             pygame.draw.aaline(surface, col, (inner, inner_y), (x, y))

#     def draw_center_glass(surface, radius):
#         g = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
#         for r in range(radius, 0, -6):
#             t = r / radius
#             c = (20, 26, 36, int(160 * t))
#             pygame.draw.circle(g, c, (radius, radius), r)
#         pygame.draw.circle(
#             g, (255, 255, 255, 16), (radius, radius), int(radius * 0.88), width=4
#         )
#         pygame.draw.circle(
#             g, (0, 0, 0, 80), (radius, radius), int(radius * 0.88), width=1
#         )
#         surface.blit(
#             g,
#             (CENTER[0] - radius, CENTER[1] - radius),
#             special_flags=pygame.BLEND_PREMULTIPLIED,
#         )

#     # Timer state
#     total_seconds = event_dict["duration"] * 60
#     running = False
#     elapsed = 0.0

#     # Adjust for events already in progress
#     event_start_dt = datetime.datetime.now().replace(
#         hour=event_dict["hour"],
#         minute=event_dict.get("minute", 0),
#         second=0,
#         microsecond=0,
#     )
#     now = datetime.datetime.now()
#     if event_start_dt < now:
#         elapsed = (now - event_start_dt).total_seconds()

#     remaining = max(0.0, total_seconds - elapsed)

#     # Animation state
#     ring_phase = 0.0
#     spawn_cooldown = 0.0
#     is_dragging_window = False
#     drag_offset = (0, 0)
#     is_resizing = False
#     resize_side = None
#     resize_margin = 10

#     # Pre-generate noise surface to avoid creating it every frame
#     noise_surf = pygame.Surface((W, H), pygame.SRCALPHA)
#     for i in range(1800):
#         x = random.randrange(0, W)
#         y = random.randrange(0, H)
#         a = random.randrange(8, 18)
#         noise_surf.set_at((x, y), (255, 255, 255, a))
#     noise_surf.set_alpha(36)


#     # Main loop
#     while True:
#         dt = clock.tick(FPS) / 1000.0
#         mx, my = pygame.mouse.get_pos()

#         for e in pygame.event.get():
#             if e.type == pygame.QUIT:
#                 # Send results back to the main process before quitting
#                 result_queue.put({
#                     "event_id": get_event_id(event_dict),
#                     "elapsed_seconds": elapsed,
#                     "total_seconds": total_seconds,
#                     "title": event_dict["title"]
#                 })
#                 return
#             elif e.type == pygame.KEYDOWN:
#                 if e.key == pygame.K_ESCAPE:
#                     return
#                 elif e.key == pygame.K_SPACE:
#                     running = not running
#                 elif e.key == pygame.K_r:
#                     remaining = total_seconds
#                     running = False
#                     elapsed = 0.0
#                 elif e.key in (pygame.K_PLUS, pygame.K_KP_PLUS):
#                     total_seconds = max(10, total_seconds + 30)
#                     if not running:
#                         remaining = total_seconds
#                         elapsed = 0.0
#                 elif e.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
#                     total_seconds = max(10, total_seconds - 30)
#                     if not running:
#                         remaining = total_seconds
#                         elapsed = 0.0
#             elif e.type == pygame.MOUSEBUTTONDOWN:
#                 if e.button == 1:
#                     if my < 40:  # Top 40px is draggable
#                         is_dragging_window = True # noqa
#                         drag_offset = (mx, my)
#                     # Check for resize start
#                     if mx < resize_margin:
#                         resize_side = "left"
#                     elif mx > W - resize_margin:
#                         resize_side = "right"
#                     if my < resize_margin:
#                         resize_side = (resize_side or "") + "top"
#                     elif my > H - resize_margin:
#                         resize_side = (resize_side or "") + "bottom"

#                     if resize_side:
#                         is_resizing = True
#                         if ctypes:
#                             hwnd = pygame.display.get_wm_info()["window"]
#                             rect = wintypes.RECT()
#                             ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
#                             drag_offset = (rect.left, rect.top)
#                         drag_offset = (mx, my) # noqa
#             elif e.type == pygame.MOUSEBUTTONUP:
#                 if e.button == 1:
#                     is_dragging_window = False
#                     is_resizing = False
#                     resize_side = None
#             elif e.type == pygame.MOUSEMOTION:
#                 if is_dragging_window and ctypes:
#                     hwnd = pygame.display.get_wm_info()["window"]
#                     rect = wintypes.RECT()
#                     ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
#                     new_x = rect.left + (mx - drag_offset[0])
#                     new_y = rect.top + (my - drag_offset[1])
#                     ctypes.windll.user32.MoveWindow(hwnd, new_x, new_y, W, H, True)
#                 elif is_resizing and ctypes:
#                     hwnd = pygame.display.get_wm_info()["window"]
#                     rect = wintypes.RECT()
#                     ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))

#                     new_w, new_h = W, H
#                     new_x, new_y = rect.left, rect.top

#                     if "right" in resize_side:
#                         new_w = W + e.rel[0]
#                     if "bottom" in resize_side:
#                         new_h = H + e.rel[1]
#                     if "left" in resize_side:
#                         new_w = W - e.rel[0]
#                         new_x = rect.left + e.rel[0]
#                     if "top" in resize_side:
#                         new_h = H - e.rel[1]
#                         new_y = rect.top + e.rel[1]

#                     new_w = max(150, new_w)  # Lower min width
#                     new_h = max(40, new_h)  # Lower min height

#                     ctypes.windll.user32.MoveWindow(
#                         hwnd, new_x, new_y, new_w, new_h, True
#                     )
#                     W, H = new_w, new_h
#                     screen = pygame.display.set_mode(
#                         (W, H), pygame.RESIZABLE | pygame.NOFRAME, vsync=1
#                     )
                    
#                 # Update cursor for resizing
#                 if not is_resizing and not is_dragging_window:
#                     if (mx < resize_margin and my < resize_margin) or (
#                         mx > W - resize_margin and my > H - resize_margin
#                     ):
#                         pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENWSE)
#                     elif (mx > W - resize_margin and my < resize_margin) or (
#                         mx < resize_margin and my > H - resize_margin
#                     ):
#                         pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENESW)
#                     elif mx < resize_margin or mx > W - resize_margin:
#                         pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEWE)
#                     elif my < resize_margin or my > H - resize_margin:
#                         pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENS)
#                     else:
#                         pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
#             elif e.type == pygame.VIDEORESIZE:
#                 W, H = max(150, e.w), max(40, e.h)
#                 screen = pygame.display.set_mode(
#                     (W, H), pygame.RESIZABLE | pygame.NOFRAME, vsync=1
#                 )

#         if running:
#             elapsed += dt
#             remaining = max(0.0, total_seconds - elapsed)
#             if remaining <= 0:
#                 running = False

#         progress = 1.0 - (remaining / total_seconds) if total_seconds > 0 else 0.0

#         is_bar_mode = H < 150  # Condition for switching to progress bar mode

#         if is_bar_mode:
#             # This mode is not part of the new design, so we'll just draw the background.
#             # A more advanced implementation could create a horizontal bar version of the ring.
#             screen.fill((30, 30, 30))
#             msg = font_small.render("Resize window to see timer", True, WHITE)
#             screen.blit(msg, msg.get_rect(center=(W/2, H/2)))

#         else:
#             # --- Redesigned Circular UI (based on draw_current_event_widget) ---
#             screen.fill((30, 30, 30)) # Dark background

#             CENTER = (W // 2, H // 2)
#             radius = min(W, H) // 2 - 40 # Leave some margin
#             thickness = max(12, int(radius * 0.15))

#             # 1. Background Track
#             track_color = (45, 45, 45)
#             pygame.draw.circle(screen, track_color, CENTER, radius, thickness)

#             # 2. Progress Arc
#             if progress > 0.005:
#                 progress_color = (0, 255, 150)  # Bright green
#                 padding = 20
#                 arc_rect = pygame.Rect(CENTER[0] - radius - padding, CENTER[1] - radius - padding, (radius + padding) * 2, (radius + padding) * 2)
#                 start_angle = math.pi / 2
#                 end_angle = start_angle - (progress * 2 * math.pi)

#                 arc_surf = pygame.Surface(arc_rect.size, pygame.SRCALPHA)
#                 for i in range(thickness):
#                     aa_radius = radius - (thickness // 2) + i
#                     pygame.draw.arc(
#                         arc_surf, progress_color,
#                         (padding + radius - aa_radius, padding + radius - aa_radius, aa_radius * 2, aa_radius * 2),
#                         end_angle, start_angle, 1
#                     )
#                 screen.blit(arc_surf, arc_rect.topleft)

#                 # 3. "Translucent Bean" Knob
#                 knob_angle = end_angle
#                 knob_x = CENTER[0] + radius * math.cos(knob_angle)
#                 knob_y = CENTER[1] - radius * math.sin(knob_angle)

#                 bean_w, bean_h = 30, 14
#                 bean_surf = pygame.Surface((bean_w, bean_h), pygame.SRCALPHA)
#                 pygame.draw.rect(bean_surf, (255, 255, 255, 180), (0, 0, bean_w, bean_h), border_radius=7)
#                 pygame.draw.rect(bean_surf, (255, 255, 255, 220), (0, 0, bean_w, bean_h), 1, border_radius=7)

#                 rotated_bean = pygame.transform.rotate(bean_surf, math.degrees(knob_angle))
#                 bean_rect = rotated_bean.get_rect(center=(knob_x, knob_y))
#                 screen.blit(rotated_bean, bean_rect)

#             # 4. Central Glass Button & Time
#             button_radius = radius - thickness - 5
#             button_center = CENTER
            
#             # Draw a subtle glass effect for the center
#             pygame.draw.circle(screen, (255, 255, 255, 15), button_center, button_radius)
#             pygame.draw.circle(screen, (255, 255, 255, 40), button_center, button_radius, 1)

#             # Display remaining time
#             time_text = format_time(remaining)
#             time_font_size = max(20, int(radius * 0.4))
#             time_font = pygame.font.SysFont("Segoe UI", time_font_size, bold=True)
#             time_surf = time_font.render(time_text, True, WHITE)
            
#             # Draw with a shadow for better visibility
#             time_shadow = time_font.render(time_text, True, (10,10,10))
#             screen.blit(time_shadow, time_shadow.get_rect(center=(CENTER[0]+2, CENTER[1]+2)))
#             screen.blit(time_surf, time_surf.get_rect(center=CENTER))

#             # 5. Instructions
#             help_font_size = max(12, int(radius * 0.1))
#             help_font = pygame.font.SysFont("Segoe UI", help_font_size)
#             help_text = "SPACE: Start/Pause | R: Reset | +/-: Change Time | ESC: Close"
#             help_surf = help_font.render(help_text, True, (150, 150, 170))
#             screen.blit(help_surf, help_surf.get_rect(center=(W/2, H - 25)))
            
#             # Status text (Running/Paused)
#             status = (
#                 "Running" if running else "Paused"
#             ) + f" • Total {int(total_seconds/60)} min"  # noqa
#             status_surf = help_font.render(status, True, (150, 150, 170))
#             screen.blit(status_surf, (15, 15))

#         pygame.display.flip()


# def run_focus_timer(event, queue):
#     """Starts a separate process for the aesthetic timer window."""
#     # Ensure we don't open multiple timers for the same event
#     if any(p.name == f"Timer-{get_event_id(event)}" for p in multiprocessing.active_children()):
#         return
#     p = multiprocessing.Process(target=timer_process_target, args=(event, queue), name=f"Timer-{get_event_id(event)}", daemon=True)
#     p.start()


# def green_ring_timer_process(event_dict):
#     """A separate process to show the green ring timer in its own window."""
#     pygame.init()
#     pygame.font.init()

#     W, H = 350, 350
#     screen = pygame.display.set_mode((W, H), pygame.NOFRAME, vsync=1)
#     pygame.display.set_caption(f"Focus: {event_dict['title']}")
#     clock = pygame.time.Clock()

#     # --- Re-implement helper functions needed in this process ---
#     def get_font_local(size):
#         try:
#             return pygame.font.Font(event_dict.get("font_path"), int(size))
#         except:
#             return pygame.font.SysFont("Arial", int(size))

#     def clamp_local(val, lo, hi):
#         return max(lo, min(val, hi))

#     def format_time_local(seconds):
#         td = datetime.timedelta(seconds=int(max(0, seconds)))
#         m, s = divmod(td.seconds, 60)
#         return f"{m:02d}:{s:02d}"

#     # --- Main Loop for the timer window ---
#     running = True
#     while running:
#         for e in pygame.event.get():
#             if e.type == pygame.QUIT or e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
#                 running = False

#         screen.fill((30, 30, 30)) # Dark background for the window

#         # --- Drawing logic adapted from draw_current_event_widget ---
#         now = datetime.datetime.now()
#         start_time = now.replace(
#             hour=event_dict["hour"], minute=event_dict.get("minute", 0), second=0, microsecond=0
#         )
#         duration_minutes = event_dict.get("duration", 60)
#         end_time = start_time + datetime.timedelta(minutes=duration_minutes)

#         elapsed_seconds = (now - start_time).total_seconds()
#         total_seconds = duration_minutes * 60
#         progress = clamp_local(elapsed_seconds / total_seconds, 0, 1)
#         remaining_seconds = total_seconds - elapsed_seconds

#         center_x, center_y = W // 2, H // 2
#         radius = min(W, H) // 2 - 30
#         thickness = 16

#         # Background Track
#         pygame.draw.circle(screen, (40, 40, 40), (center_x, center_y), radius, thickness)

#         # Progress Arc
#         if progress > 0.005:
#             progress_color = (0, 255, 150)
#             padding = 20
#             arc_rect = pygame.Rect(center_x - radius - padding, center_y - radius - padding, (radius + padding) * 2, (radius + padding) * 2)
#             start_angle = math.pi / 2
#             end_angle = start_angle - (progress * 2 * math.pi)

#             arc_surf = pygame.Surface(arc_rect.size, pygame.SRCALPHA)
#             for i in range(thickness):
#                 aa_radius = radius - (thickness // 2) + i
#                 pygame.draw.arc(
#                     arc_surf, progress_color,
#                     (padding + radius - aa_radius, padding + radius - aa_radius, aa_radius * 2, aa_radius * 2),
#                     end_angle, start_angle, 1
#                 )
#             screen.blit(arc_surf, arc_rect.topleft)

#             # Knob
#             knob_angle = end_angle
#             knob_x = center_x + radius * math.cos(knob_angle)
#             knob_y = center_y - radius * math.sin(knob_angle)
#             bean_w, bean_h = 30, 14
#             bean_surf = pygame.Surface((bean_w, bean_h), pygame.SRCALPHA)
#             # Make the bean more visible against a dark background
#             pygame.draw.rect(bean_surf, (255, 255, 255, 200), (0, 0, bean_w, bean_h), border_radius=7)
#             pygame.draw.rect(bean_surf, (255, 255, 255, 255), (0, 0, bean_w, bean_h), 1, border_radius=7)
#             rotated_bean = pygame.transform.rotate(bean_surf, math.degrees(knob_angle))
#             screen.blit(rotated_bean, rotated_bean.get_rect(center=(knob_x, knob_y)))

#         # Central Glass Button
#         button_radius = radius - thickness - 5
#         pygame.draw.circle(screen, (255, 255, 255, 20), (center_x, center_y), button_radius)
#         pygame.draw.circle(screen, (255, 255, 255, 60), (center_x, center_y), button_radius, 1)

#         # Time Text
#         remaining_time_str = format_time_local(remaining_seconds)
#         time_font = get_font_local(int(radius * 0.5))
#         # Draw with a shadow for better visibility
#         time_shadow = time_font.render(remaining_time_str, True, (10,10,10))
#         time_surf = time_font.render(remaining_time_str, True, (240, 240, 250))
#         screen.blit(time_shadow, time_shadow.get_rect(center=(center_x+2, center_y+2)))
#         screen.blit(time_surf, time_surf.get_rect(center=(center_x, center_y)))

#         pygame.display.flip()
#         clock.tick(30)

#     pygame.quit()


# def run_green_ring_focus_timer(event):
#     """Starts a separate process for the green ring timer window."""
#     # Pass font path to the new process
#     event['font_path'] = settings.get("font_path")
#     p = multiprocessing.Process(target=green_ring_timer_process, args=(event,), daemon=True)
#     p.start()


load_settings()
load_events()
clock = pygame.time.Clock()

# Drag/resize state
dragging_event = None
drag_offset_y = 0
resizing_event = None
resize_initial_duration = 0
dragging_divider = False

weekly_view = False

def main_loop():
    global weekly_view, current_week_start, selected_date, scroll_offset, scrolling, scroll_drag_start, scroll_start_offset, dragging_event, drag_offset_y, resizing_event, resize_initial_duration, lofi_on, events, WIDTH, HEIGHT, screen, BACKGROUND_IMAGE, todos, todo_scroll_offset, HOUR_HEIGHT, timer_state, TODO_WIDTH, dragging_divider
    global currently_playing_index, minute_offset, START_HOUR, END_HOUR
    global coin_animation, user_coins # Add to globals to modify it

    load_settings()
    load_events()
    load_todos()
    clock = pygame.time.Clock()

    # Drag/resize state
    load_coin_animation()
    dragging_event = None
    drag_offset_y = 0
    drag_offset_x = 0
    resizing_event = None
    dragging_todo = None
    dragging_todo_index = -1
    dragging_item_path = None
    is_dragging_over_todo = False
    focus_result_queue = multiprocessing.Queue()
    # --- New state for smooth scrolling ---
    scroll_velocity = 0
    todo_scroll_velocity = 0

    last_click_time = 0
    timer_state = {} # Reset timer state
    todo_drop_indicator_y = -1

    current_event = None
    weekly_view = False
    current_week_start = selected_date - datetime.timedelta(
        days=selected_date.weekday()
    )
    global lofi_on
    resize_initial_duration = 0

    # Initialized before the loop so the bounce-back physics (which runs at the
    # top of the loop) has a valid value on the very first frame.
    max_todo_scroll = 0

    while True:
        # --- Smooth Scrolling Update ---
        scroll_offset += scroll_velocity
        scroll_velocity *= 0.94  # Even softer friction for a smoother glide
        if abs(scroll_velocity) < 0.1: scroll_velocity = 0

        todo_scroll_offset += todo_scroll_velocity
        todo_scroll_velocity *= 0.94 # Even softer friction for a smoother glide
        if abs(todo_scroll_velocity) < 0.1: todo_scroll_velocity = 0

        # --- Bounce-back logic for scrolling ---
        if not scrolling:
            if scroll_offset < SCROLL_MIN:
                scroll_offset += (SCROLL_MIN - scroll_offset) * 0.15
            elif scroll_offset > SCROLL_MAX:
                scroll_offset += (SCROLL_MAX - scroll_offset) * 0.15

            if todo_scroll_offset < 0:
                todo_scroll_offset += (0 - todo_scroll_offset) * 0.15
            elif todo_scroll_offset > max_todo_scroll:
                todo_scroll_offset += (max_todo_scroll - todo_scroll_offset) * 0.15

        # --- Update Coin Animation ---
        now = pygame.time.get_ticks()
        if coin_sprite_sheet and now - coin_animation["last_update"] > coin_animation["frame_rate"]:
            coin_animation["last_update"] = now
            coin_animation["current_frame"] = (coin_animation["current_frame"] + 1) % coin_animation["frames_per_row"]


        # --- Check for results from focus sessions ---
        while not focus_result_queue.empty():
            try:
                result = focus_result_queue.get_nowait()
                event_id = result["event_id"]
                elapsed_seconds = result["elapsed_seconds"]

                # Check if it's the global focus session
                if event_id == "global_focus":
                    coins_earned = int(elapsed_seconds / 60) # 1 coin per minute
                    user_coins += coins_earned
                    with open(resource_path(os.path.join(ASSETS_DIR, "player_data.json")), "w") as f:
                        json.dump({"coins": user_coins}, f)
                    continue # Skip the rest of the logic for global timer

                # Find the event this result belongs to
                for ev in events:
                    if get_event_id(ev) == event_id:
                        original_duration_minutes = ev.get("duration", 60)
                        
                        # 2. Check for extension
                        if elapsed_seconds > original_duration_minutes * 60:
                            # Round up to the nearest 15 minutes
                            new_duration = math.ceil(elapsed_seconds / (15 * 60)) * 15
                            ev["duration"] = new_duration
                        save_events()
                        break
            except Exception: # Catch queue.Empty and other potential errors
                break

        if weekly_view:
            week_btns = draw_weekly_view(current_week_start)
            # Draw buttons over the view
            pygame.draw.rect(
                screen, THEME["button_bg"], week_btns["back"], border_radius=8
            ) # noqa
            back_txt = get_font_wrapper(20).render("Day View", True, THEME["text"])
            screen.blit(
                back_txt,
                (
                    week_btns["back"].centerx - back_txt.get_width() // 2,
                    week_btns["back"].centery - back_txt.get_height() // 2,
                ),
            )
            pygame.draw.rect(
                screen, THEME["button_bg"], week_btns["prev"], border_radius=8
            ) # noqa
            prev_txt = get_font_wrapper(20).render("Prev Week", True, THEME["text"])
            screen.blit(
                prev_txt,
                (
                    week_btns["prev"].centerx - prev_txt.get_width() // 2,
                    week_btns["prev"].centery - prev_txt.get_height() // 2,
                ),
            )
            pygame.draw.rect(
                screen, THEME["button_bg"], week_btns["next"], border_radius=8
            ) # noqa
            next_txt = get_font_wrapper(20).render("Next Week", True, THEME["text"])
            screen.blit(
                next_txt,
                (
                    week_btns["next"].centerx - next_txt.get_width() // 2,
                    week_btns["next"].centery - next_txt.get_height() // 2,
                ),
            )

            pygame.display.flip()
            for pe in pygame.event.get():
                if pe.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif pe.type == pygame.MOUSEBUTTONDOWN and pe.button == 1:
                    if week_btns["back"].collidepoint(pe.pos):
                        weekly_view = False
                    elif week_btns["prev"].collidepoint(pe.pos):
                        current_week_start -= datetime.timedelta(weeks=1)
                    elif week_btns["next"].collidepoint(pe.pos):
                        current_week_start += datetime.timedelta(weeks=1)
                    for day, rect in week_btns["days"]:
                        if rect.collidepoint(pe.pos):
                            selected_date = day
                            load_events()
                            weekly_view = False
                            break
            clock.tick(60)
            continue

        # Update drag-over state for visual feedback
        mouse_pos = pygame.mouse.get_pos()
        is_dragging_over_todo = dragging_event is not None and mouse_pos[0] < TODO_WIDTH

        # Update todo drop indicator
        if dragging_todo is not None and mouse_pos[0] < TODO_WIDTH:
            # Calculate which slot the mouse is over
            slot_index = clamp((mouse_pos[1] - 70 + 25) // 50, 0, len(todos))
            todo_drop_indicator_y = 70 + slot_index * 50 - 5
        else:
            todo_drop_indicator_y = -1

        # Normal day view
        mouse_pos = pygame.mouse.get_pos()
        event_layout = calculate_event_layout(
            events, WIDTH - EVENT_X - EVENT_RIGHT_MARGIN
        )
        btns = draw_day_view(event_layout, dragging_event, is_dragging_over_todo)

        current_event = get_current_event() # Get the event first
        todo_btns = draw_todo_list(
            mouse_pos,
            dragging_item_path,
            is_event_widget_active=bool(current_event),
            scroll_offset=todo_scroll_offset,
        )
        
        widget_btns = draw_current_event_widget(current_event)

        # --- Draw Coin Counter (after main views, before event loop) ---
        if coin_sprite_sheet:
            # Get the current frame of the animation
            frame_rect = pygame.Rect(
                coin_animation["current_frame"] * coin_animation["frame_width"],
                coin_animation["current_coin_type"] * coin_animation["frame_height"],
                coin_animation["frame_width"],
                coin_animation["frame_height"]
            )
            frame_image = coin_sprite_sheet.subsurface(frame_rect)
            scaled_coin = pygame.transform.smoothscale(frame_image, (32, 32))
            screen.blit(scaled_coin, (WIDTH - 280, 70))
        else:
            # Fallback to a simple circle if the sprite is not loaded
            pygame.draw.circle(screen, (255, 215, 0), (WIDTH - 280 + 16, 70 + 16), 16)
        coin_text = get_font_wrapper(22).render(f"{user_coins}", True, THEME["text"])
        screen.blit(coin_text, (WIDTH - 320, 75))

        # Clamp todo scroll offset removed from here to allow bounce in the main loop
        max_todo_scroll = todo_btns.get("max_scroll", 0)

        for pe in pygame.event.get():
            if pe.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif pe.type == pygame.VIDEORESIZE:
                w, h = pe.w, pe.h
                w = max(w, MIN_WIDTH)
                h = max(h, MIN_HEIGHT)
                WIDTH, HEIGHT = w, h
                screen = pygame.display.set_mode(
                    (WIDTH, HEIGHT), pygame.RESIZABLE, vsync=1
                )
                try:
                    BACKGROUND_IMAGE = pygame.transform.scale(
                        BACKGROUND_IMAGE, (WIDTH, HEIGHT)
                    )
                except:
                    pass
                
            elif pe.type == pygame.MOUSEWHEEL:
                # This event handles both modern touchpads (pe.y != 0) and
                # traditional mouse wheels (pe.y == 0, but pe.x is used for up/down).
                # We use pe.y for vertical scrolling. It's negative for up, positive for down.
                scroll_y = pe.y
                # For older mice, pe.y is 0, and up/down is in pe.x.
                # if scroll_y == 0:
                #     scroll_y = pe.x # This can cause issues with horizontal scrolling on some touchpads

                scroll_multiplier = 15  # Adjust this value to control scroll sensitivity
                if pygame.mouse.get_pos()[0] < TODO_WIDTH:
                    todo_scroll_velocity -= scroll_y * scroll_multiplier
                else:
                    scroll_velocity -= scroll_y * scroll_multiplier
                continue # Don't process as MOUSEBUTTONDOWN

            elif pe.type == pygame.MOUSEBUTTONDOWN:
                if pe.button == 4:
                    if pe.pos[0] < TODO_WIDTH:
                        todo_scroll_velocity -= 10 # Slower, gentler acceleration
                    else:
                        scroll_velocity -= 5 # Slower, gentler acceleration
                elif pe.button == 5:
                    if pe.pos[0] < TODO_WIDTH:
                        todo_scroll_velocity += 10
                    else:
                        scroll_velocity += 5
                elif pe.button == 2:
                    scrolling = True
                    scroll_drag_start = pe.pos[1]
                    scroll_start_offset = scroll_offset
                elif pe.button == 1:
                    # If a drag is already in progress, don't re-evaluate for a new one.
                    if dragging_event or resizing_event or dragging_todo:
                        continue

                    # Check for divider drag
                    if TODO_WIDTH - 5 < pe.pos[0] < TODO_WIDTH + 5:
                        dragging_divider = True
                        continue
                    # --- Check for click on an active quote to dismiss it ---
                    clicked_on_quote = False
                    for quote in active_quotes:
                        # Re-calculate the quote's current position for hit-testing
                        elapsed = time.time() - quote["start_time"]
                        slide_progress = min(1.0, elapsed / quote["slide_in_duration"]) # noqa
                        ease_out_slide = 1 - pow(1 - slide_progress, 4)
                        text_surf = get_font_wrapper(22).render(quote["text"], True, (0,0,0))
                        box_w, box_h = text_surf.get_width() + 60, 60
                        start_y, end_y = HEIGHT + 20, HEIGHT - box_h - 20
                        current_y = start_y + (end_y - start_y) * ease_out_slide
                        quote_rect = pygame.Rect(WIDTH // 2 - box_w // 2, current_y, box_w, box_h)
                        if quote_rect.collidepoint(pe.pos):
                            # Dismiss by setting its start time way in the past
                            quote["start_time"] = 0 
                            clicked_on_quote = True
                    if clicked_on_quote: continue

                    mx, my = pe.pos
                    clicked_on_event = False
                    if check_or_delete_todo_at_pos(pe.pos, todo_scroll_offset):
                        continue

                    # Handle clicks on the to-do panel buttons FIRST, before the
                    # todo-item hit-test. Otherwise a click on "Add To-do" (or the
                    # delete-completed button) also grabs whatever todo happens to
                    # sit behind the button, selecting/dragging it by mistake.
                    if todo_btns and todo_btns["add_todo_btn"].collidepoint(pe.pos):
                        new_todo_details = todo_add_window_v2()
                        if new_todo_details:
                            todos.append(new_todo_details)
                            save_todos()
                        continue
                    if todo_btns and todo_btns["delete_completed_btn"].collidepoint(pe.pos):
                        if any(t.get("done") for t in todos):
                            if show_confirmation_dialog("Delete all completed tasks?"):
                                todos = [t for t in todos if not t.get("done")]
                                save_todos()
                        continue

                    # Check for dragging a todo
                    clicked_item, _, clicked_path = find_item_at_pos_recursive(todos, pe.pos, 70 - todo_scroll_offset, 0, todo_scroll_offset)
                    if clicked_item:
                        dragging_todo = clicked_item # This can be a folder or a todo
                        dragging_item_path = clicked_path
                        # dragging_todo_rect is handled in the drawing loop now

                    # Check for double-click on a todo
                    current_time = time.time()
                    if current_time - last_click_time < 0.3: # 300ms threshold for double-click
                        clicked_item, _, _ = find_item_at_pos_recursive(todos, pe.pos, 70 - todo_scroll_offset, 0, todo_scroll_offset)
                        if clicked_item and not clicked_item.get("type") == "folder":
                            dragging_todo = None # Cancel drag on double click
                            dragging_item_path = None
                            
                            new_text = todo_edit_window(clicked_item['title'])
                            if new_text is not None:
                                clicked_item['title'] = new_text
                                save_todos()
                                break # Stop checking other todos

                    last_click_time = current_time
                    if dragging_todo or clicked_on_event:
                        continue

                    full_event_width = WIDTH - EVENT_X - EVENT_RIGHT_MARGIN
                    for ev in events:
                        event_id = get_event_id(ev)
                        layout = event_layout.get(
                            event_id, {"x": EVENT_X, "width": full_event_width}
                        )
                        event_x, event_width = layout["x"], layout["width"]

                        start_minutes = ev["hour"] * 60 + ev.get("minute", 0)
                        ev_start_y = (
                            TOP_Y
                            + (start_minutes - START_HOUR * 60) * (HOUR_HEIGHT / 60)
                            - scroll_offset
                        )
                        ev_height = ev.get("duration", 60) * (HOUR_HEIGHT / 60)
                        ev_rect = pygame.Rect(
                            event_x, ev_start_y + 5, event_width, ev_height - 10
                        )
                        resize_rect = pygame.Rect(
                            event_x, ev_start_y + ev_height - 5, event_width, 10
                        )

                        if resize_rect.collidepoint(mx, my):
                            resizing_event = ev
                            resize_initial_duration = ev.get("duration", 60)
                            clicked_on_event = True
                            break
                        elif ev_rect.collidepoint(mx, my):
                            dragging_event = ev
                            drag_offset_y = my - ev_start_y
                            drag_offset_x = mx - event_x
                            clicked_on_event = True
                            break

                    if my < TOP_Y and mx > TODO_WIDTH:
                        if btns["left_btn"].collidepoint(pe.pos):
                            selected_date -= datetime.timedelta(days=1)
                            load_events()
                            continue
                        if btns["right_btn"].collidepoint(pe.pos):
                            selected_date += datetime.timedelta(days=1)
                            load_events()
                            continue
                        if btns["settings_rect"].collidepoint(pe.pos):
                            show_settings()
                            START_HOUR = settings["start_hour"]
                            END_HOUR = settings["end_hour"]
                            continue
                        if btns["stats_btn"].collidepoint(pe.pos):
                            show_stats_popup(events, screen, font_cache , settings.get("font_path") , WIDTH , HEIGHT)
                            continue
                        if btns["credits_btn"].collidepoint(pe.pos):
                            show_credits()
                            continue
                        if btns["lofi_btn"].collidepoint(pe.pos):
                            run_music_player() # noqa
                            continue
                        if btns["week_btn"].collidepoint(pe.pos):
                            weekly_view = True
                            current_week_start = selected_date - datetime.timedelta(
                                days=selected_date.weekday()
                            )
                            continue


                    if not (dragging_event or resizing_event or dragging_todo):
                        pass # This block is now handled above for the header area

                    if edit_or_delete_event_at_pos(pe.pos, scroll_offset , focus_result_queue):
                        continue
                    if toggle_checkbox_at_pos(pe.pos, scroll_offset):
                        continue
                    

                    # If we handled a button click, don't also start a drag.
                    if clicked_on_event:
                        continue
                    if clicked_on_event:
                        continue

                    if (
                        mx > TODO_WIDTH
                    ):  # Only add event if clicking in the calendar area
                        minute_offset = int(
                            (pe.pos[1] + scroll_offset - TOP_Y) / (HOUR_HEIGHT / 60)
                        )
                        hour = START_HOUR + minute_offset // 60
                        minute = (minute_offset % 60) // 15 * 15
                        if hour < START_HOUR or hour > END_HOUR:
                            continue
                        details = event_add_window(pos=(hour, minute))
                        if details:
                            new_event = {
                                "title": details["title"], "hour": hour, "minute": minute,
                                "duration": details["duration"], 
                                "color": details["color"], # Use the selected color
                                "icon": details["icon"], "done": False
                            }
                            events.append(new_event)
                            save_events()
                            break # Exit loop after adding event

                elif pe.button == 3:  # Right-click
                    # This is a simplified hit-test. A more robust solution would mirror the drawing logic.
                    if pe.pos[0] < TODO_WIDTH:
                        # Account for scroll offset to find correct index
                        clicked_index = (pe.pos[1] - 70 + todo_scroll_offset) // 50
                        if 0 <= clicked_index < len(todos):
                            show_todo_context_menu(
                                clicked_index, pe.pos, todo_scroll_offset
                            )

                    minute_offset = int(
                        (pe.pos[1] + scroll_offset - TOP_Y) / (HOUR_HEIGHT / 60)
                    )
                    hour = START_HOUR + minute_offset // 60
                    minute = (minute_offset % 60) // 15 * 15
                    # if hour < START_HOUR or hour > END_HOUR:

            elif pe.type == pygame.MOUSEBUTTONUP:
                if pe.button == 2:
                    scrolling = False
                if pe.button == 1:
                    dragging_divider = False
                    mx, my = pe.pos
                    if dragging_event is not None:
                        # Prevent dropping event behind header
                        if my < TOP_Y:
                            # Snap back to original position or a safe spot
                            pass # The drag logic already handles this by not updating
                        # Check if dropped on the todo list area
                        if mx < TODO_WIDTH:
                            # Convert event to todo
                            new_todo = {
                                "title": dragging_event["title"],
                                "done": dragging_event.get("done", False),
                                "color": dragging_event.get("color")
                            }
                            todos.append(new_todo)
                            save_todos()
                            # Remove event from calendar
                            events.remove(dragging_event)
                            save_events()
                        else:
                            save_events()
                        dragging_event = None
                        drag_offset_y = 0
                        drag_offset_x = 0
                    if resizing_event is not None:
                        # This logic is now part of the timer widget state
                        save_events()
                        resizing_event = None
                        resize_initial_duration = 0
                    if dragging_todo is not None:
                        # Check if dropped on the calendar area
                        if mx > EVENT_X:
                            minute_offset = int(
                                (my + scroll_offset - TOP_Y) / (HOUR_HEIGHT / 60)
                            )
                            hour = START_HOUR + minute_offset // 60
                            minute = (minute_offset % 60) // 15 * 15

                            if START_HOUR <= hour <= END_HOUR:
                                # Ensure the dragged item has a unique ID
                                if "id" not in dragging_todo:
                                    dragging_todo["id"] = f"todo_{int(time.time() * 1000)}"
                                
                                parent_name = get_parent_folder_name(dragging_item_path, todos)
                                # Use the todo's color if it exists, otherwise pick a random one
                                event_color = dragging_todo.get("color")
                                if not event_color:
                                    # Fallback to a random color from the current theme's choices
                                    event_color = random.choice(THEME.get("color_choices", [(189, 224, 254)]))

                                new_event = {
                                    "title": f"{parent_name}: {dragging_todo['title']}" if parent_name else dragging_todo["title"],
                                    "hour": hour,
                                    "minute": minute,
                                    "duration": 60,
                                    "done": dragging_todo.get("done", False),
                                    "color": event_color,
                                    "icon": 0,
                                    "todo_id": dragging_todo["id"], # Link to the original to-do
                                }
                                events.append(new_event)
                                save_events()
                                find_and_remove_item(dragging_item_path, todos)
                                save_todos()
                        elif mx < TODO_WIDTH:
                            # --- New, robust reordering logic ---
                            today_str = datetime.date.today().strftime("%Y-%m-%d")
                            regular_todos = [t for t in todos if not t.get("date") or t["date"] >= today_str or t.get("done")]
                            
                            # Calculate y offset where regular todos start
                            y_offset = 70
                            if any(t.get("date") and t["date"] < today_str and not t.get("done") for t in todos):
                                num_overdue = sum(1 for t in todos if t.get("date") and t["date"] < today_str and not t.get("done"))
                                y_offset += 30 + (num_overdue * 50) + 10

                            # Calculate the visual slot index within the regular list
                            relative_y = my - y_offset + todo_scroll_offset
                            target_visual_index = clamp((relative_y + 25) // 50, 0, len(regular_todos))

                            if 0 <= target_visual_index < len(regular_todos):
                                # Find the actual item at that visual slot
                                target_item = regular_todos[target_visual_index]
                                target_actual_index = todos.index(target_item)
                                
                                # This logic is now too simple for nested structures.
                                # A full implementation would need to find the item by path and move it.
                                # Deferring this complex logic for now.
                                print("TODO: Implement nested drag-and-drop reordering.")
                        dragging_todo = None
                        dragging_item_path = None
                        

            elif pe.type == pygame.MOUSEMOTION:
                if dragging_divider:
                    TODO_WIDTH = clamp(pe.pos[0], 200, 500)
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEWE)
                    continue

                mx, my = pe.pos
                if scrolling:
                    dy = pe.pos[1] - scroll_drag_start
                    raw_offset = scroll_start_offset - dy
                    # Rubber-band past the limits while dragging (with resistance)
                    # so the timeline AND the events overscroll together; the
                    # spring-back in the main loop then pulls everything home.
                    if raw_offset < SCROLL_MIN:
                        scroll_offset = SCROLL_MIN + (raw_offset - SCROLL_MIN) * 0.35
                    elif raw_offset > SCROLL_MAX:
                        scroll_offset = SCROLL_MAX + (raw_offset - SCROLL_MAX) * 0.35
                    else:
                        scroll_offset = raw_offset

                # --- Cursor Change Logic ---
                cursor_set = False # noqa
                
                # If mouse is over header, don't change cursor for events
                if my < TOP_Y and mx > TODO_WIDTH:
                    pass

                if not (dragging_event or resizing_event or dragging_todo):
                    for ev in events:
                        event_id = get_event_id(ev)
                        layout = event_layout.get(event_id, {"x": EVENT_X, "width": WIDTH - EVENT_X - EVENT_RIGHT_MARGIN})
                        event_x, event_width = layout['x'], layout['width']
                        start_minutes = ev["hour"] * 60 + ev.get("minute", 0)
                        ev_start_y = TOP_Y + (start_minutes - START_HOUR * 60) * (HOUR_HEIGHT / 60) - scroll_offset
                        ev_height = ev.get("duration", 60) * (HOUR_HEIGHT / 60)
                        resize_handle_rect = pygame.Rect(event_x, ev_start_y + ev_height - 5, event_width, 10)
                        if resize_handle_rect.collidepoint(mx, my):
                            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENS)
                            cursor_set = True
                            break
                    # Divider cursor
                    if TODO_WIDTH - 5 < mx < TODO_WIDTH + 5:
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEWE)
                    elif not cursor_set:
                        # Reset to arrow if no other cursor is set
                        current_cursor = pygame.mouse.get_cursor()
                        # Only reset if it's not already the arrow to avoid flicker
                        # Pygame doesn't expose the current cursor type easily, so we check the tuple
                        # The default arrow cursor is a specific tuple of size, hotspot, and data.
                        # This is a heuristic, but works for default cursors.
                        # A simpler check is just to set it, but this avoids potential flicker.
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

                is_dragging_over_todo = (
                    dragging_event is not None and pe.pos[0] < TODO_WIDTH
                )

                if dragging_todo is not None:
                    # The dragged item is now drawn directly in the main loop,
                    # so we just need to update its temporary position for drawing.
                    pass

                if dragging_event is not None and not is_dragging_over_todo:
                    # Only update position if dragging within the calendar area
                    if mx > EVENT_X:
                        new_top_y = my - drag_offset_y + scroll_offset
                        min_top = TOP_Y
                        max_top = (
                            TOP_Y
                            + (END_HOUR - START_HOUR + 1) * HOUR_HEIGHT
                            - (dragging_event.get("duration", 60) * (HOUR_HEIGHT / 60))
                        )
                        new_top_y = max(min_top, min(new_top_y, max_top))
                        rel_minutes = round((new_top_y - TOP_Y) / (HOUR_HEIGHT / 60))
                        snapped = int(round(rel_minutes / 15.0) * 15)
                        new_hour = START_HOUR + snapped // 60
                        new_minute = snapped % 60
                        if new_hour < START_HOUR:
                            new_hour = START_HOUR
                            new_minute = 0
                        if new_hour > END_HOUR:
                            new_hour = END_HOUR
                            new_minute = 0
                        dragging_event["hour"] = int(new_hour)
                        dragging_event["minute"] = int(new_minute)

                if resizing_event is not None:
                    start_minutes = resizing_event["hour"] * 60 + resizing_event.get(
                        "minute", 0
                    )
                    ev_start_y = (
                        TOP_Y
                        + (start_minutes - START_HOUR * 60) * (HOUR_HEIGHT / 60)
                        - scroll_offset
                    )
                    new_height_pixels = max(15, my - ev_start_y)
                    new_minutes = max(
                        15,
                        int(round(new_height_pixels / (HOUR_HEIGHT / 60) / 15.0) * 15),
                    )
                    if start_minutes + new_minutes > (END_HOUR + 1) * 60:
                        new_minutes = (END_HOUR + 1) * 60 - start_minutes
                    resizing_event["duration"] = int(new_minutes)

            elif pe.type == pygame.KEYDOWN:
                if pe.key == pygame.K_s:
                    show_stats_popup(events, screen , font_cache , font_path , WIDTH , HEIGHT)
                elif pe.key == pygame.K_t:
                    keys = list(THEMES.keys())
                    idx = keys.index(current_theme)
                    set_theme(keys[(idx + 1) % len(keys)])
                elif pe.key == pygame.K_c:
                    curr = get_current_event()
                    # if curr: 
                        # run_green_ring_focus_timer(curr)

        # --- Update and Draw Animations ---
        current_time = time.time()
        done_animating = []
        for item_id, anim in animating_out.items():
            elapsed = current_time - anim["start_time"]
            progress = min(1.0, elapsed / anim["duration"])
            ease_in_quad = progress * progress  # Makes it accelerate

            if progress >= 1.0:
                done_animating.append(item_id)
                continue

            # Calculate scale and alpha
            scale = 1.0 - ease_in_quad
            alpha = 255 * (1.0 - progress)

            # Create scaled and faded surface
            orig_rect = anim["rect"]
            new_w, new_h = int(orig_rect.width * scale), int(orig_rect.height * scale)
            scaled_surf = pygame.transform.smoothscale(anim["surface"], (new_w, new_h))
            scaled_surf.set_alpha(alpha)

            # Blit it centered on the original position
            new_rect = scaled_surf.get_rect(center=orig_rect.center)
            screen.blit(scaled_surf, new_rect)

        # Draw highlight for dropping event on todo list
        if is_dragging_over_todo:
            pygame.draw.rect(screen, (0, 150, 255, 100), (0, 0, TODO_WIDTH, HEIGHT), 5)
            # Draw the event as a small, todo-like block following the cursor
            if dragging_event:
                dragged_rect = pygame.Rect(0, 0, TODO_WIDTH - 20, 44)
                dragged_rect.center = mouse_pos
                pygame.draw.rect(screen, (255, 255, 255), dragged_rect, border_radius=8)
                pygame.draw.rect(screen, (0, 0, 0), dragged_rect, 2, border_radius=8) # noqa
                event_title_txt = get_font_wrapper(16).render(
                    dragging_event["title"], True, (0, 0, 0)
                )
                screen.blit(
                    event_title_txt,
                    (dragged_rect.x + 10, dragged_rect.y + 10),
                )

        # Draw the drop indicator for reordering todos
        if todo_drop_indicator_y != -1:
            pygame.draw.line(
                screen,
                (0, 100, 255),
                (10, todo_drop_indicator_y),
                (TODO_WIDTH - 10, todo_drop_indicator_y),
                3,
            )

        if dragging_todo:
            # Draw the dragged item (folder or todo) at the mouse cursor
            item_text = dragging_todo.get("name") or dragging_todo.get("title", "...")
            drag_surf = get_font_wrapper(16).render(item_text, True, THEME["text"])
            drag_rect = pygame.Rect(mouse_pos[0] - 20, mouse_pos[1] - 20, drag_surf.get_width() + 40, 40)
            pygame.draw.rect(
                screen, THEME["todo_item_hover"], drag_rect, border_radius=8
            )
            pygame.draw.rect(screen, THEME["text"], drag_rect, 1, border_radius=8)
            screen.blit(
                drag_surf, (drag_rect.x + 20, drag_rect.centery - drag_surf.get_height() // 2)
            )

        # Clean up finished animations
        for item_id in done_animating:
            del animating_out[item_id]
        
        # Draw confetti on top of everything else
        update_confetti()
        draw_confetti()

        # Draw non-blocking quotes on top of everything
        update_and_draw_quotes(active_quotes, screen, WIDTH, HEIGHT, get_font_wrapper(22))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    dragging_divider = False
    # This is important for multiprocessing to work correctly on all platforms
    main_loop()