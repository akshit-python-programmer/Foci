# focus_timer.py
# Modern circular focus timer with visual effects (pygame)
# Controls: Space=start/pause, R=reset, +/- adjust duration, Esc=quit

import pygame
import sys
import math
import random
from pygame import gfxdraw
from datetime import timedelta

pygame.init()

# Config
W, H = 880, 880
CENTER = (W // 2, H // 2)
FPS = 120
FOCUS_SECONDS = 60  # default demo length; change to 1500 for 25 minutes
RADIUS = 250

# Colors
BG_TOP = (12, 14, 20)
BG_BOTTOM = (18, 24, 36)
ACCENT = (84, 210, 255)
ACCENT2 = (150, 90, 255)
WHITE = (240, 242, 245)

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Circular Focus Timer — Visual Demo")

clock = pygame.time.Clock()
font_large = pygame.font.SysFont("Segoe UI", 64, bold=True)
font_medium = pygame.font.SysFont("Segoe UI", 28)
font_small = pygame.font.SysFont("Segoe UI", 18)


def draw_radial_gradient(surface, inner_color, outer_color):
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


def eased_progress(t):
    if t < 0:
        return 0.0
    if t > 1:
        return 1.0
    return (3 - 2 * t) * t * t


def make_blur(surface, passes=3, scale_factor=0.5):
    w, h = surface.get_size()
    tmp = surface.copy()
    for i in range(passes):
        s = pygame.transform.smoothscale(
            tmp, (max(1, int(w * scale_factor)), max(1, int(h * scale_factor)))
        )
        tmp = pygame.transform.smoothscale(s, (w, h))
    return tmp


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
        if self.life <= 0:
            return
        a = max(0, min(255, int(255 * (self.life / self.maxlife))))
        col = (*self.color[:3], a)
        r = max(1, int(self.size * (self.life / self.maxlife)))
        s = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(s, r * 2, r * 2, r, col)
        pygame.gfxdraw.aacircle(s, r * 2, r * 2, r, col)
        surf.blit(
            s,
            (self.pos[0] - r * 2, self.pos[1] - r * 2),
            special_flags=pygame.BLEND_PREMULTIPLIED,
        )


particles = []


def spawn_particles_on_arc(angle_rad, radius, count=8):
    for i in range(count):
        a = angle_rad + random.uniform(-0.12, 0.12)
        r = radius + random.uniform(-6, 6)
        x = CENTER[0] + math.cos(a) * r
        y = CENTER[1] + math.sin(a) * r
        speed = random.uniform(30, 180)
        vel = [
            math.cos(a) * speed * random.uniform(0.25, 0.9),
            math.sin(a) * speed * random.uniform(0.25, 0.9),
        ]
        life = random.uniform(0.5, 1.6)
        col = (
            random.randint(200, 255),
            random.randint(200, 255),
            random.randint(240, 255),
        )
        size = random.uniform(1.6, 4.2)
        particles.append(Particle((x, y), vel, life, col, size))


def draw_ring(surface, radius, width, phase, colors=(ACCENT, ACCENT2)):
    steps = 180
    for i in range(steps):
        a0 = (i / steps) * math.tau + phase
        a1 = ((i + 1) / steps) * math.tau + phase
        x0 = CENTER[0] + math.cos(a0) * radius
        y0 = CENTER[1] + math.sin(a0) * radius
        x1 = CENTER[0] + math.cos(a1) * (radius - width)
        y1 = CENTER[1] + math.sin(a1) * (radius - width)
        t = i / steps
        col = (
            int(colors[0][0] * (1 - t) + colors[1][0] * t),
            int(colors[0][1] * (1 - t) + colors[1][1] * t),
            int(colors[0][2] * (1 - t) + colors[1][2] * t),
            16,
        )
        pygame.gfxdraw.filled_trigon(
            surface,
            int(x0),
            int(y0),
            int(x1),
            int(y1),
            int(CENTER[0] + math.cos(a0) * (radius - width / 2)),
            int(CENTER[1] + math.sin(a0) * (radius - width / 2)),
            col,
        )


def draw_ticks(surface, radius, thickness, progress):
    count = 60
    for i in range(count):
        a = (i / count) * math.tau - math.pi / 2
        x = CENTER[0] + math.cos(a) * (radius)
        y = CENTER[1] + math.sin(a) * (radius)
        inner = CENTER[0] + math.cos(a) * (radius - thickness)
        inner_y = CENTER[1] + math.sin(a) * (radius - thickness)
        edge = progress * math.tau - math.pi / 2
        diff = abs(((a - edge + math.pi) % math.tau) - math.pi)
        brightness = max(0, 1 - diff * 2.5)
        alpha = int(80 * (0.4 + 0.6 * brightness))
        col = (*WHITE[:3], alpha)
        pygame.draw.aaline(surface, col, (inner, inner_y), (x, y))


def draw_center_glass(surface, radius):
    g = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -6):
        t = r / radius
        c = (20, 26, 36, int(160 * t))
        pygame.draw.circle(g, c, (radius, radius), r)
    pygame.draw.circle(
        g, (255, 255, 255, 16), (radius, radius), int(radius * 0.88), width=4
    )
    pygame.draw.circle(g, (0, 0, 0, 80), (radius, radius), int(radius * 0.88), width=1)
    surface.blit(
        g,
        (CENTER[0] - radius, CENTER[1] - radius),
        special_flags=pygame.BLEND_PREMULTIPLIED,
    )


def format_time(seconds):
    td = timedelta(seconds=int(max(0, seconds)))
    m, s = divmod(td.seconds, 60)
    return f"{m:02d}:{s:02d}"


# Timer state
total_seconds = FOCUS_SECONDS
remaining = total_seconds
running = False
elapsed = 0.0

# Animation state
ring_phase = 0.0
spawn_cooldown = 0.0

# Main loop
running_main = True
while running_main:
    dt = clock.tick(FPS) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running_main = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running_main = False
            elif event.key == pygame.K_SPACE:
                running = not running
            elif event.key == pygame.K_r:
                remaining = total_seconds
                running = False
                elapsed = 0.0
            elif event.key in (pygame.K_PLUS, pygame.K_KP_PLUS):
                total_seconds = max(10, total_seconds + 30)
                remaining = total_seconds
                elapsed = 0.0
                running = False
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                total_seconds = max(10, total_seconds - 30)
                remaining = total_seconds
                elapsed = 0.0
                running = False

    if running:
        elapsed += dt
        remaining = max(0.0, total_seconds - elapsed)
        if remaining <= 0:
            running = False

    # background
    bg = pygame.Surface((W, H))
    draw_radial_gradient(bg, BG_TOP, BG_BOTTOM)
    screen.blit(bg, (0, 0))

    # rings
    ring_surf = pygame.Surface((W, H), pygame.SRCALPHA)
    ring_phase += dt * 0.25
    draw_ring(ring_surf, RADIUS + 24, 36, ring_phase, colors=(ACCENT2, ACCENT))
    draw_ring(ring_surf, RADIUS + 72, 18, -ring_phase * 0.5, colors=(ACCENT, ACCENT2))
    screen.blit(ring_surf, (0, 0), special_flags=pygame.BLEND_ADD)

    # progress arc
    progress = 1.0 - (remaining / total_seconds) if total_seconds > 0 else 0.0
    eased = eased_progress(progress)
    angle = eased * math.tau
    arc_surf = pygame.Surface((W, H), pygame.SRCALPHA)

    thickness = 28
    start_angle = -math.pi / 2
    end_angle = start_angle + angle
    rect = pygame.Rect(CENTER[0] - RADIUS, CENTER[1] - RADIUS, RADIUS * 2, RADIUS * 2)
    pygame.draw.arc(arc_surf, (40, 44, 52, 150), rect, 0, math.tau, width=thickness)
    segs = max(48, int(120 * progress) + 6)
    for i in range(segs):
        a0 = start_angle + (i / segs) * angle
        a1 = start_angle + ((i + 1) / segs) * angle
        t = i / max(1, segs - 1)
        col = (
            int(ACCENT[0] * (1 - t) + ACCENT2[0] * t),
            int(ACCENT[1] * (1 - t) + ACCENT2[1] * t),
            int(ACCENT[2] * (1 - t) + ACCENT2[2] * t),
            int(220 * (0.6 + 0.4 * math.sin(math.pi * t))),
        )
        pygame.draw.arc(arc_surf, col, rect, a0, a1, width=thickness)

    tip_angle = end_angle
    tip_x = CENTER[0] + math.cos(tip_angle) * RADIUS
    tip_y = CENTER[1] + math.sin(tip_angle) * RADIUS
    pygame.gfxdraw.filled_circle(
        arc_surf, int(tip_x), int(tip_y), 10, (*WHITE[:3], 180)
    )
    pygame.gfxdraw.aacircle(arc_surf, int(tip_x), int(tip_y), 10, (*WHITE[:3], 220))

    spawn_cooldown -= dt
    if running and spawn_cooldown <= 0:
        spawn_particles_on_arc(tip_angle, RADIUS, count=6 + int(6 * progress))
        spawn_cooldown = 0.04

    draw_ticks(arc_surf, RADIUS + thickness / 2 + 8, 12, progress)

    screen.blit(arc_surf, (0, 0))

    # particle layer
    particle_surf = pygame.Surface((W, H), pygame.SRCALPHA)
    for p in particles[:]:
        p.update(dt)
        p.draw(particle_surf)
        if p.life <= 0:
            particles.remove(p)
    bloom = make_blur(particle_surf, passes=2, scale_factor=0.35)
    screen.blit(bloom, (0, 0), special_flags=pygame.BLEND_ADD)
    screen.blit(particle_surf, (0, 0), special_flags=pygame.BLEND_PREMULTIPLIED)

    # center glass
    draw_center_glass(screen, int(RADIUS * 0.78))

    # noise overlay
    noise = pygame.Surface((W, H), pygame.SRCALPHA)
    for i in range(1800):
        x = random.randrange(0, W)
        y = random.randrange(0, H)
        a = random.randrange(8, 18)
        noise.set_at((x, y), (255, 255, 255, a))
    noise.set_alpha(36)
    screen.blit(noise, (0, 0))

    # time text
    time_text = format_time(remaining)
    txt = font_large.render(time_text, True, WHITE)
    txt_rect = txt.get_rect(center=CENTER)
    screen.blit(txt, txt_rect)

    sub = font_medium.render(
        "Press SPACE to Start / Pause • R to Reset • +/- to change time",
        True,
        (200, 204, 210),
    )
    screen.blit(sub, (CENTER[0] - sub.get_width() // 2, CENTER[1] + 68))

    status = ("Running" if running else "Paused") + f" • Total {int(total_seconds)}s"
    st2 = font_small.render(status, True, (170, 170, 180))
    screen.blit(st2, (18, H - 28))

    # vignette
    vign = pygame.Surface((W, H), pygame.SRCALPHA)
    for r in range(int(max(W, H) / 2), 0, -12):
        t = r / (max(W, H) / 2)
        a = int(55 * (1 - t))
        pygame.draw.circle(vign, (0, 0, 0, a), CENTER, r)
    screen.blit(vign, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    pygame.display.flip()

pygame.quit()
sys.exit()
