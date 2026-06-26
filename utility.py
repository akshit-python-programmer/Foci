import pygame
import sys
import os
import datetime
import math
import time
import random
# --- Path & Resource Helpers ---

def resource_path(relative_path):
    """Get absolute path to resource (works for dev and .exe)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_icon_safe(name, size=(28, 28)):
    """Loads an image with a fallback to a blank surface."""
    try:
        img = pygame.image.load(name).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    except Exception as e:
        print(f"Warning: Could not load icon {name}: {e}")
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        return surf

def find_fonts(assets_dir):
    """Scans a directory for .ttf and .otf files and returns a dictionary."""
    found_fonts = {}
    for root, _, files in os.walk(assets_dir):
        for file in files:
            if file.lower().endswith((".ttf", ".otf")):
                base_name = os.path.splitext(file)[0]
                font_family_name = base_name.split('-')[0].title()
                is_preferred = 'regular' in base_name.lower() or 'variable' in base_name.lower()
                if font_family_name not in found_fonts or is_preferred:
                    found_fonts[font_family_name] = os.path.join(root, file)
    return found_fonts

# --- Math & Data Helpers ---

def clamp(val, lo, hi):
    """Restricts a value to be within a specified range."""
    return max(lo, min(val, hi))

def get_event_id(ev):
    """Creates a unique-ish string identifier for an event."""
    return f"{ev['hour']}-{ev.get('minute',0)}-{ev['title']}"

def format_time(seconds):
    """Formats seconds into a MM:SS string."""
    td = datetime.timedelta(seconds=int(max(0, seconds)))
    m, s = divmod(td.seconds, 60)
    return f"{m:02d}:{s:02d}"

def eased_progress(t):
    """An easing function for smooth animations (ease-in-out)."""
    if t < 0: return 0.0
    if t > 1: return 1.0
    return (3 - 2 * t) * t * t

# --- Text & Font Helpers ---

def get_font(font_cache, font_path, size):
    """
    Retrieves a font from a cache or loads it.
    Now accepts cache and path as arguments.
    """
    key = (font_path, size)
    if key in font_cache and font_cache[key] is not None:
        return font_cache[key]
    try:
        font = pygame.font.Font(key[0], int(size))
        font_cache[key] = font
        return font
    except Exception:
        # Fallback to a system font if the custom one fails
        return pygame.font.SysFont("Arial", int(size))

def get_font_wrapper(font_cache, path , size):
    return get_font(font_cache, path, size)

def truncate_text(text, font, max_width):
    """Truncates a string to fit within a given width, adding '...'."""
    if font.size(text)[0] <= max_width:
        return text
    while len(text) > 0 and font.size(text + "...")[0] > max_width:
        text = text[:-1]
    return text + "..."

# --- Drawing & Color Helpers ---

def lerp_color(c1, c2, t):
    """Linearly interpolates between two colors."""
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )

def desaturate(color, amount=0.5):
    """Reduces the saturation of a color."""
    c = pygame.Color(*color)
    h, s, v, a = c.hsva
    c.hsva = (h, int(s * amount), v, a)
    return c

def draw_vertical_gradient(surface, c1, c2, rect=None):
    """Draws a vertical color gradient on a surface."""
    if rect is None:
        rect = surface.get_rect()
    for y in range(rect.height):
        t = y / rect.height
        color = lerp_color(c1, c2, t)
        pygame.draw.line(
            surface, color, (rect.left, rect.top + y), (rect.right, rect.top + y)
        )

def draw_radial_gradient(surface, inner_color, outer_color):
    """Draws a radial color gradient on a surface."""
    cx, cy = surface.get_width() // 2, surface.get_height() // 2
    max_radius = int(math.hypot(cx, cy))
    for r in range(max_radius, 0, -8):
        t = r / max_radius
        c = (
            int(outer_color[0] * (1 - t) + inner_color[0] * t),
            int(outer_color[1] * (1 - t) + inner_color[1] * t),
            int(outer_color[2] * (1 - t) + inner_color[2] * t),
        )
        pygame.draw.circle(surface, c, (cx, cy), r)

def round_image(image, radius):
    """Returns a copy of an image surface with rounded corners."""
    size = image.get_size()
    mask = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
    rounded = image.copy()
    rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return rounded

def make_blur(surface, passes=3, scale_factor=0.5):
    """Applies a simple and fast blur effect to a surface."""
    w, h = surface.get_size()
    tmp = surface.copy()
    for i in range(passes):
        s = pygame.transform.smoothscale(
            tmp, (max(1, int(w * scale_factor)), max(1, int(h * scale_factor)))
        )
        tmp = pygame.transform.smoothscale(s, (w, h))
    return tmp


def trigger_motivational_quote(active_quotes, WIDTH, HEIGHT, font):
    """Adds a new quote to the active_quotes list to be displayed."""
    quotes = [
        # steve jobs focus and discipline related quotes
        "The people who are crazy enough to think they can change the world are the ones who do.",
        "Focus is about saying no.",
        "I'm convinced that about half of what separates successful entrepreneurs from the non-successful ones is pure perseverance.",
        "Stay hungry, stay foolish.",
        # elon musk focus and productivity related quotes
        "When something is important enough, you do it even if the odds are not in your favor.",
        "Work like hell. I mean you just have to put in 80 to 100 hour weeks every week. This improves the odds of success.",
        "Focus on signal over noise. Don't waste time on stuff that doesn't actually make things better.",
        # discipline related quotes
        "Discipline is the bridge between goals and accomplishment." ,
        "Success is nothing more than a few simple disciplines, practiced every day.",
        "The pain of discipline is far less than the pain of regret.",
        

        "Great job! Keep going!", "Every step counts. Well done!", "You're crushing it!",
        "Small wins lead to big victories.", "Focus brings results!", "You did it! 🎉",
        "Keep up the momentum!", "Progress, not perfection.", "Another task bites the dust!",
        "You're unstoppable!"
    ]

    # --- New logic to ensure the quote fits on screen ---
    # font object is passed as an argument now
    # Filter quotes to find ones that fit within the screen width (with padding)
    permissible_quotes = [q for q in quotes if font.size(q)[0] < WIDTH - 80]

    if not permissible_quotes:
        # If no quotes fit (very small window), default to a short one
        quote_text = "You did it! 🎉"
    else:
        quote_text = random.choice(permissible_quotes)

    # Calculate duration based on text length: 5s base + 0.05s per character
    duration = 5.0 + len(quote_text) * 0.05

    new_quote = {
        "text": quote_text,
        "start_time": time.time(),
        "duration": duration,
        "slide_in_duration": 0.6,
        "fade_out_duration": 1.5,
    }
    active_quotes.append(new_quote)

def update_and_draw_quotes(active_quotes, screen, WIDTH, HEIGHT, font):
    """Manages the animation and drawing of non-blocking motivational quotes."""
    if not active_quotes:
        return

    current_time = time.time()
    
    # Remove old quotes
    active_quotes[:] = [q for q in active_quotes if current_time - q["start_time"] < q["duration"]]

    for i, quote in enumerate(active_quotes):
        elapsed = current_time - quote["start_time"]
        
        # --- Animation ---
        # Slide-in
        slide_progress = min(1.0, elapsed / quote["slide_in_duration"])
        ease_out_slide = 1 - pow(1 - slide_progress, 4)

        # Fade-out
        time_left = quote["duration"] - elapsed
        fade_progress = 0.0
        if time_left < quote["fade_out_duration"]:
            fade_progress = 1.0 - (time_left / quote["fade_out_duration"])
        
        alpha = 255 * (1.0 - fade_progress)

        # --- Drawing ---
        text_surf = font.render(quote["text"], True, (255, 255, 255))
        box_w = text_surf.get_width() + 60
        box_h = 60
        
        start_y = HEIGHT + 20
        end_y = HEIGHT - box_h - 20
        current_y = start_y + (end_y - start_y) * ease_out_slide

        box_rect = pygame.Rect(WIDTH // 2 - box_w // 2, current_y, box_w, box_h)

        # --- Glassmorphism Effect (with clipping to prevent ValueError) ---
        # 1. Find the visible part of the box
        visible_rect = box_rect.clip(screen.get_rect())

        if visible_rect.width > 0 and visible_rect.height > 0:
            # 2. Capture the visible area behind the box
            glass_area = screen.subsurface(visible_rect).copy()
            # 2. Blur it by scaling down and up
            glass_area = pygame.transform.smoothscale(glass_area, (visible_rect.width // 8, visible_rect.height // 8))
            glass_area = pygame.transform.smoothscale(glass_area, visible_rect.size)
            # 3. Blit the blurred background
            screen.blit(glass_area, visible_rect.topleft)

        # 4. Draw a semi-transparent overlay and shadow
        shadow_color = (0, 0, 0, int(70 * (1 - fade_progress)))
        bg_color = (40, 45, 60, int(200 * (1 - fade_progress)))
        pygame.draw.rect(screen, shadow_color, box_rect.move(0, 4), border_radius=12)
        pygame.draw.rect(screen, bg_color, box_rect, border_radius=12)
        
        # 5. Draw the text on top
        text_surf.set_alpha(alpha)
        screen.blit(text_surf, text_surf.get_rect(center=box_rect.center))


def show_stats_popup(events, screen ,font_cache , font_path , WIDTH , HEIGHT):
    total = len(events)
    completed = sum(1 for e in events if e.get("done"))
    total_minutes = sum(e.get("duration", 60) for e in events)
    completed_minutes = sum(e.get("duration", 60) for e in events if e.get("done"))
    percent_tasks = (completed / total) if total else 0
    percent_time = (completed_minutes / total_minutes) if total_minutes else 0

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))

    win_w, win_h = 600, 400
    win_x, win_y = WIDTH // 2 - win_w // 2, HEIGHT // 2 - win_h // 2

    # Animation state
    anim_progress = 0.0
    start_time = time.time()
    anim_duration = 0.6  # seconds

    # Fonts
    font_title = get_font_wrapper(font_cache, font_path, 32)
    font_percent = get_font_wrapper(font_cache, font_path, 40)
    font_label = get_font_wrapper(font_cache, font_path, 18)
    font_sublabel = get_font_wrapper(font_cache, font_path, 16)

    # Colors
    BG_COLOR = (245, 248, 250)
    SHADOW_COLOR = (210, 215, 220)
    TEXT_COLOR = (50, 50, 70)
    CHART_BG = (225, 230, 235)
    TASKS_COLOR = (0, 191, 255)
    TIME_COLOR = (138, 43, 226)

    def draw_donut_chart(center_x, center_y, radius, progress, color, label, sub_label):
        # Draw shadow
        pygame.draw.circle(
            screen, SHADOW_COLOR, (center_x, center_y + 4), radius + 2, 18
        )
        # Draw background track
        pygame.draw.circle(screen, CHART_BG, (center_x, center_y), radius, 16)

        # Draw progress arc
        if progress > 0:
            arc_rect = pygame.Rect(
                center_x - radius, center_y - radius, radius * 2, radius * 2
            )
            end_angle = math.pi / 2 - (progress * 2 * math.pi)
            pygame.draw.arc(screen, color, arc_rect, math.pi / 2, end_angle, 16)

        # Text inside
        percent_text = font_percent.render(f"{int(progress * 100)}%", True, TEXT_COLOR)
        screen.blit(
            percent_text,
            (
                center_x - percent_text.get_width() // 2,
                center_y - percent_text.get_height() // 2,
            ),
        )

        # Labels below
        label_text = font_label.render(label, True, TEXT_COLOR)
        screen.blit(
            label_text, (center_x - label_text.get_width() // 2, center_y + radius + 15)
        )
        sub_label_text = font_sublabel.render(sub_label, True, (150, 150, 160))
        screen.blit(
            sub_label_text,
            (center_x - sub_label_text.get_width() // 2, center_y + radius + 40),
        )

    while True:
        # Redraw the underlying screen to create the overlay effect
        screen.blit(overlay, (0, 0))

        # Draw main window
        pygame.draw.rect(
            screen, BG_COLOR, (win_x, win_y, win_w, win_h), border_radius=24
        )
        pygame.draw.rect(
            screen, (220, 225, 230), (win_x, win_y, win_w, win_h), 1, border_radius=24
        )

        # Title
        title = font_title.render("Today's Progress", True, TEXT_COLOR)
        screen.blit(title, (win_x + win_w // 2 - title.get_width() // 2, win_y + 30))

        # Animation logic
        elapsed = time.time() - start_time
        if elapsed < anim_duration:
            # Ease-out cubic easing function
            t = elapsed / anim_duration
            anim_progress = 1 - pow(1 - t, 3)
        else:
            anim_progress = 1.0

        # Draw charts
        chart_y = win_y + win_h // 2
        radius = 70

        # Tasks Chart
        tasks_x = win_x + win_w // 4
        draw_donut_chart(
            tasks_x,
            chart_y,
            radius,
            percent_tasks * anim_progress,
            TASKS_COLOR,
            "Tasks Completed",
            f"{completed} of {total}",
        )

        # Time Chart
        time_x = win_x + (win_w // 4) * 3
        draw_donut_chart(
            time_x,
            chart_y,
            radius,
            percent_time * anim_progress,
            TIME_COLOR,
            "Time Focused",
            f"{completed_minutes} of {total_minutes} min",
        )

        # Close button
        close_btn = pygame.Rect(win_x + win_w // 2 - 50, win_y + win_h - 60, 100, 40)
        pygame.draw.rect(screen, (255, 200, 200), close_btn, border_radius=12)
        close_txt = get_font_wrapper(font_cache, font_path, 22).render("Close", True, (100, 50, 50))
        screen.blit(
            close_txt,
            (
                close_btn.centerx - close_txt.get_width() // 2,
                close_btn.centery - close_txt.get_height() // 2,
            ),
        )

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                if close_btn.collidepoint(mx, my):
                    return

