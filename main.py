import pygame
import random
import os
import math
import sys

pygame.init()

WIDTH = 800
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rain Drop - Journey to the Ocean")

clock = pygame.time.Clock()
FPS = 60

# ==================== COLORS ====================
WHITE = (255, 255, 255)
OCEAN_BLUE = (0, 105, 148)
DARK_BLUE = (0, 60, 100)
LIGHT_BLUE = (135, 206, 235)
SKY_TOP = (135, 206, 250)
SKY_BOTTOM = (25, 25, 112)
GOLD = (255, 215, 0)
GREEN = (50, 255, 100)
RED = (255, 80, 80)
BLACK = (0, 0, 0)

# ==================== PRE-RENDER GRADIENT BACKGROUND ====================
bg_surface = pygame.Surface((WIDTH, HEIGHT))
for y in range(HEIGHT):
    ratio = y / HEIGHT
    r = int(SKY_TOP[0] * (1 - ratio) + SKY_BOTTOM[0] * ratio)
    g = int(SKY_TOP[1] * (1 - ratio) + SKY_BOTTOM[1] * ratio)
    b = int(SKY_TOP[2] * (1 - ratio) + SKY_BOTTOM[2] * ratio)
    pygame.draw.line(bg_surface, (r, g, b), (0, y), (WIDTH, y))
bg_surface = bg_surface.convert()

# Victory background
victory_bg = pygame.Surface((WIDTH, HEIGHT))
for y in range(HEIGHT):
    ratio = y / HEIGHT
    r = int(26 * (1 - ratio) + 10 * ratio)
    g = int(58 * (1 - ratio) + 22 * ratio)
    b = int(92 * (1 - ratio) + 40 * ratio)
    pygame.draw.line(victory_bg, (r, g, b), (0, y), (WIDTH, y))
victory_bg = victory_bg.convert()

# ==================== FONT CACHE ====================
font_cache = {}


def get_font(size):
    if size not in font_cache:
        font_cache[size] = pygame.font.SysFont("Arial", size, bold=True)
    return font_cache[size]


# ==================== LOAD ASSETS ====================
def create_drop_surface(w, h, color_top, color_bottom):
    """Create a teardrop shape procedurally."""
    surf = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
    cx = w // 2 + 2
    # Draw body (ellipse at bottom)
    body_rect = pygame.Rect(2, h // 3, w, h * 2 // 3)
    pygame.draw.ellipse(surf, color_bottom, body_rect)
    # Draw top triangle
    pygame.draw.polygon(surf, color_top, [
        (cx, 2),
        (2 + 4, h // 3 + h // 6),
        (w - 2, h // 3 + h // 6)
    ])
    # Blend with another ellipse
    inner_rect = pygame.Rect(6, h // 3 + 4, w - 8, h * 2 // 3 - 8)
    pygame.draw.ellipse(surf, color_top, inner_rect)
    # Shine highlight
    pygame.draw.ellipse(surf, (255, 255, 255, 120),
                        pygame.Rect(cx - w // 6, h // 3 + 2, w // 4, h // 5))
    return surf


def create_cloud_surface(w, h, brightness=240):
    """Create a cloud shape procedurally."""
    surf = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
    b = brightness
    color = (b, b, b, 220)
    shadow = (b - 40, b - 40, b - 30, 180)

    # Shadow blobs
    pygame.draw.ellipse(surf, shadow,
                        (5 + 3, h * 0.25 + 5, w * 0.55, h * 0.6))
    pygame.draw.ellipse(surf, shadow,
                        (w * 0.35 + 3, h * 0.1 + 5, w * 0.45, h * 0.65))

    # Main blobs
    pygame.draw.ellipse(surf, color,
                        (5, h * 0.25, w * 0.55, h * 0.6))
    pygame.draw.ellipse(surf, color,
                        (w * 0.2, h * 0.05, w * 0.5, h * 0.7))
    pygame.draw.ellipse(surf, color,
                        (w * 0.35, h * 0.25, w * 0.55, h * 0.55))
    # Bottom fill
    pygame.draw.ellipse(surf, color,
                        (w * 0.1, h * 0.35, w * 0.7, h * 0.45))

    # Highlight
    highlight = (min(255, b + 15), min(255, b + 15), min(255, b + 10), 100)
    pygame.draw.ellipse(surf, highlight,
                        (w * 0.25, h * 0.1, w * 0.3, h * 0.25))
    return surf


# Try loading images, fall back to procedural
try:
    rain_img = pygame.transform.scale(
        pygame.image.load("rain_drop.png").convert_alpha(), (50, 70)
    )
    cloud_img_base = pygame.image.load("cloud.png").convert_alpha()
    power_img_base = pygame.transform.scale(
        pygame.image.load("rain_drop.png").convert_alpha(), (28, 40)
    )
    IMAGES_LOADED = True
except Exception:
    rain_img = create_drop_surface(46, 66, (168, 216, 255), (34, 102, 204))
    cloud_img_base = create_cloud_surface(160, 90, 240)
    power_img_base = create_drop_surface(24, 36, (200, 255, 200), (50, 180, 80))
    IMAGES_LOADED = False

# Pre-scale cloud variants
if IMAGES_LOADED:
    cloud_normal = pygame.transform.scale(cloud_img_base, (165, 95))
    cloud_fast = pygame.transform.scale(cloud_img_base, (130, 75))
    cloud_fast.fill((180, 180, 200), special_flags=pygame.BLEND_RGB_MULT)
    cloud_big = pygame.transform.scale(cloud_img_base, (230, 130))
else:
    cloud_normal = create_cloud_surface(165, 95, 240)
    cloud_fast = create_cloud_surface(130, 75, 190)
    cloud_big = create_cloud_surface(230, 130, 235)

# Pre-create tinted power-up images
def tint_surface(surf, color):
    """Create a tinted copy of a surface."""
    tinted = surf.copy()
    overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
    overlay.fill((*color, 100))
    tinted.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return tinted


power_green = tint_surface(power_img_base, (0, 200, 50))
power_blue = tint_surface(power_img_base, (50, 150, 255))
power_gold = tint_surface(power_img_base, (255, 200, 0))

# ==================== GAME SETTINGS ====================
LANES = [100, 220, 340, 460, 580, 700]
WIN_SCORE = 30


# ==================== HIGH SCORE ====================
def get_high_score():
    try:
        if os.path.exists("high_score.txt"):
            with open("high_score.txt", "r") as f:
                return int(f.read().strip())
    except Exception:
        pass
    return 0


def save_high_score(score):
    try:
        with open("high_score.txt", "w") as f:
            f.write(str(score))
    except Exception:
        pass


# ==================== RAIN PARTICLES ====================
class RainParticle:
    def __init__(self, randomize_y=True):
        self.reset()
        if randomize_y:
            self.y = random.uniform(0, HEIGHT)

    def reset(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(-60, -5)
        self.speed = random.uniform(280, 520)
        self.length = random.randint(8, 18)
        self.alpha = random.randint(60, 140)

    def update(self, dt):
        self.y += self.speed * dt
        if self.y > HEIGHT + 10:
            self.reset()

    def draw(self, surface):
        end_y = min(self.y + self.length, HEIGHT)
        pygame.draw.line(surface, (200, 220, 255),
                         (int(self.x), int(self.y)),
                         (int(self.x) - 1, int(end_y)), 1)


# ==================== SPARKLE ====================
class Sparkle:
    def __init__(self, x, y, color):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.life = 1.0
        self.vx = random.uniform(-180, 180)
        self.vy = random.uniform(-300, -60)
        self.size = random.uniform(2, 4)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 400 * dt
        self.life -= 2.0 * dt
        return self.life > 0

    def draw(self, surface):
        s = max(1, int(self.size * self.life))
        pygame.draw.circle(surface, self.color,
                           (int(self.x), int(self.y)), s)


# ==================== PLAYER ====================
class Player:
    def __init__(self):
        self.image = rain_img
        self.w = self.image.get_width()
        self.h = self.image.get_height()
        self.x = float(WIDTH // 2 - self.w // 2)
        self.y = 90.0
        self.fall_speed = 50.0
        self.move_speed = 320.0
        self.shield = False
        self.shield_timer = 0.0
        self.invincible = False
        self.inv_timer = 0.0
        self.wobble_t = random.uniform(0, 6.28)

    def update(self, dt, keys_pressed):
        self.wobble_t += dt * 2.5

        # Natural falling
        self.y += self.fall_speed * dt
        self.x += math.sin(self.wobble_t) * 0.4

        # Movement
        spd = self.move_speed * dt
        if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.x -= spd
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.x += spd
        if keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            self.y -= spd * 0.5
        if keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            self.y += spd * 0.35

        # Boundaries
        self.x = max(5, min(self.x, WIDTH - self.w - 5))
        self.y = max(30, min(self.y, HEIGHT - self.h - 65))

        # Timers
        if self.shield:
            self.shield_timer -= dt
            if self.shield_timer <= 0:
                self.shield = False

        if self.invincible:
            self.inv_timer -= dt
            if self.inv_timer <= 0:
                self.invincible = False

    def activate_shield(self, duration=3.0):
        self.shield = True
        self.shield_timer = duration

    @property
    def center_x(self):
        return self.x + self.w / 2

    @property
    def center_y(self):
        return self.y + self.h / 2

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def get_hitbox(self):
        """Smaller hitbox for fair collisions."""
        return pygame.Rect(int(self.x + 10), int(self.y + 8),
                           self.w - 20, self.h - 12)

    def draw(self, surface, frame_count):
        # Shield glow
        if self.shield:
            pulse = math.sin(frame_count * 0.08) * 0.3 + 0.7
            radius = int((self.w * 0.7 + 20) * pulse)
            shield_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (100, 200, 255, 70),
                               (radius, radius), radius)
            pygame.draw.circle(shield_surf, (150, 220, 255, 120),
                               (radius, radius), radius, 3)
            surface.blit(shield_surf,
                         (int(self.center_x - radius),
                          int(self.center_y - radius)))

        # Invincibility flash
        if self.invincible and int(frame_count * 0.5) % 2 == 0:
            return  # Skip drawing every other frame for flash

        surface.blit(self.image, (int(self.x), int(self.y)))


# ==================== CLOUD ====================
class Cloud:
    CLOUD_IMAGES = {
        "normal": cloud_normal,
        "fast": cloud_fast,
        "big": cloud_big,
    }

    def __init__(self, speed, cloud_type="normal"):
        self.cloud_type = cloud_type
        self.image = self.CLOUD_IMAGES.get(cloud_type, cloud_normal)
        self.w = self.image.get_width()
        self.h = self.image.get_height()

        lane = random.choice(LANES)
        self.x = float(lane - self.w / 2)
        self.y = float(HEIGHT + 100)

        speed_mult = 1.5 if cloud_type == "fast" else (0.85 if cloud_type == "big" else 1.0)
        self.speed = speed * speed_mult * 60
        self.passed = False
        self.h_speed = random.uniform(-30, 30)
        self.alive = True

    def update(self, dt):
        self.y -= self.speed * dt
        self.x += self.h_speed * dt

        if self.x < -10 or self.x + self.w > WIDTH + 10:
            self.h_speed *= -1

        if self.y + self.h < -60:
            self.alive = False

    def get_hitbox(self):
        """Inset hitbox for fair collisions."""
        return pygame.Rect(int(self.x + 15), int(self.y + 15),
                           self.w - 30, self.h - 25)

    def draw(self, surface):
        surface.blit(self.image, (int(self.x), int(self.y)))


# ==================== POWER-UP ====================
class PowerUp:
    IMAGES = {
        "slow": power_green,
        "shield": power_blue,
        "score": power_gold,
    }
    TINTS = {
        "slow": GREEN,
        "shield": (100, 200, 255),
        "score": GOLD,
    }

    def __init__(self, power_type="slow"):
        self.power_type = power_type
        self.image = self.IMAGES.get(power_type, power_green)
        self.tint = self.TINTS.get(power_type, GREEN)
        self.w = self.image.get_width()
        self.h = self.image.get_height()
        self.x = random.uniform(50, WIDTH - 50)
        self.y = float(HEIGHT + 40)
        self.speed = 150.0
        self.wobble_t = random.uniform(0, 6.28)
        self.glow_t = random.uniform(0, 6.28)
        self.alive = True

    def update(self, dt):
        self.y -= self.speed * dt
        self.wobble_t += dt * 3
        self.x += math.sin(self.wobble_t) * 1.2
        self.glow_t += dt * 4

        if self.y + self.h < -30:
            self.alive = False

    def get_hitbox(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def draw(self, surface):
        # Glow
        glow_size = int(22 + math.sin(self.glow_t) * 5)
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.tint, 60),
                           (glow_size, glow_size), glow_size)
        surface.blit(glow_surf,
                     (int(self.x + self.w / 2 - glow_size),
                      int(self.y + self.h / 2 - glow_size)))

        surface.blit(self.image, (int(self.x), int(self.y)))


# ==================== DRAWING HELPERS ====================
def draw_ocean(surface, frame_count):
    """Draw animated ocean at bottom."""
    ocean_rect = pygame.Rect(0, HEIGHT - 55, WIDTH, 55)
    pygame.draw.rect(surface, DARK_BLUE, ocean_rect)

    # Two wave layers
    for layer in range(2):
        points = [(0, HEIGHT)]
        for x in range(0, WIDTH + 4, 4):
            wy = (HEIGHT - 50 + layer * 18
                  + math.sin(frame_count * 0.04 + x * 0.015 + layer * 2) * 8
                  + math.sin(frame_count * 0.025 + x * 0.008) * 4)
            points.append((x, int(wy)))
        points.append((WIDTH, HEIGHT))

        colors = [OCEAN_BLUE, (0, 140, 180)]
        pygame.draw.polygon(surface, colors[layer], points)


def draw_text(surface, text, x, y, size=40, color=WHITE, center=False):
    """Draw text with shadow, using cached fonts."""
    font = get_font(size)
    # Shadow
    shadow_surf = font.render(text, True, (0, 0, 0))
    text_surf = font.render(text, True, color)

    if center:
        rect = text_surf.get_rect(center=(x, y))
        shadow_rect = shadow_surf.get_rect(center=(x + 2, y + 2))
    else:
        rect = text_surf.get_rect(topleft=(x, y))
        shadow_rect = shadow_surf.get_rect(topleft=(x + 2, y + 2))

    surface.blit(shadow_surf, shadow_rect)
    surface.blit(text_surf, rect)


def draw_progress_bar(surface, score, target):
    """Journey progress indicator."""
    bw, bh = 180, 22
    bx = WIDTH - bw - 20
    by = 22
    progress = min(score / target, 1.0)

    # Background
    pygame.draw.rect(surface, (30, 30, 60),
                     (bx - 2, by - 2, bw + 4, bh + 4), border_radius=12)
    pygame.draw.rect(surface, DARK_BLUE,
                     (bx, by, bw, bh), border_radius=10)

    # Fill
    if progress > 0:
        fw = max(4, int(bw * progress))
        fill_rect = pygame.Rect(bx, by + 2, fw, bh - 4)
        for i in range(fw):
            ratio = i / bw
            c = (int(100 * (1 - ratio) + 50 * ratio),
                 int(200 * (1 - ratio) + 255 * ratio),
                 100)
            pygame.draw.line(surface, c,
                             (bx + i, by + 2), (bx + i, by + bh - 2))

    # Border
    pygame.draw.rect(surface, WHITE,
                     (bx, by, bw, bh), 2, border_radius=10)

    # Label
    draw_text(surface, "Ocean", bx + bw // 2, by + bh // 2, 15, WHITE, center=True)


def draw_hud(surface, score, high_score, lives, player, frame_count):
    """Draw game HUD."""
    draw_text(surface, f"Score: {score}", 20, 22, 30, WHITE)
    draw_text(surface, f"Best: {high_score}", 20, 55, 22, GOLD)

    # Lives as hearts
    lives_color = RED if lives == 1 else WHITE
    hearts = " ".join(["<3"] * lives)
    draw_text(surface, f"Lives: {hearts}", 20, 85, 20, lives_color)

    # Shield status
    if player.shield:
        remaining = max(0, int(math.ceil(player.shield_timer)))
        draw_text(surface, f"Shield: {remaining}s",
                  WIDTH // 2, 18, 22, (100, 200, 255), center=True)


def hsl_to_rgb(h, s, l):
    """Convert HSL to RGB."""
    import colorsys
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return (int(r * 255), int(g * 255), int(b * 255))


# ==================== WELCOME SCREEN ====================
def welcome_screen():
    particles = [RainParticle() for _ in range(30)]
    frame_count = 0

    while True:
        dt = clock.tick(FPS) / 1000.0
        frame_count += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return
            if event.type == pygame.MOUSEBUTTONDOWN:
                return

        # Draw
        screen.blit(bg_surface, (0, 0))

        for p in particles:
            p.update(dt)
            p.draw(screen)

        draw_ocean(screen, frame_count)

        # Animated title
        title_y = 130 + math.sin(frame_count * 0.03) * 12

        # Title glow effect
        draw_text(screen, "RAIN DROP", WIDTH // 2, title_y, 62, WHITE, center=True)
        draw_text(screen, "Journey to the Ocean",
                  WIDTH // 2, title_y + 48, 28, LIGHT_BLUE, center=True)

        # Draw demo raindrop
        screen.blit(rain_img, (WIDTH // 2 - rain_img.get_width() // 2, title_y - 80))

        # Instructions
        ys = 270
        draw_text(screen, "Controls:", WIDTH // 2, ys, 26, GOLD, center=True)
        draw_text(screen, "Arrow Keys / WASD to move",
                  WIDTH // 2, ys + 35, 20, WHITE, center=True)
        draw_text(screen, "Avoid the clouds!",
                  WIDTH // 2, ys + 80, 22, (255, 200, 200), center=True)
        draw_text(screen, "Collect power-ups!",
                  WIDTH // 2, ys + 110, 22, GOLD, center=True)
        draw_text(screen, f"Reach score {WIN_SCORE} to win!",
                  WIDTH // 2, ys + 140, 22, GREEN, center=True)

        # Pulsing start text
        pulse = 0.85 + math.sin(frame_count * 0.08) * 0.15
        sz = int(36 * pulse)
        draw_text(screen, "Press ENTER to Start",
                  WIDTH // 2, 530, sz, WHITE, center=True)

        pygame.display.flip()


# ==================== GAME LOOP ====================
def game_loop():
    player = Player()
    clouds = []
    powerups = []
    sparkles = []
    particles = [RainParticle() for _ in range(25)]

    spawn_timer = 0.0
    power_timer = 0.0
    cloud_speed = 3.2
    score = 0
    lives = 3
    frame_count = 0
    high_score = get_high_score()

    while True:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)  # Cap to prevent spiral
        frame_count += 1

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return score, False

        keys_pressed = pygame.key.get_pressed()

        # ---- UPDATE ----
        for p in particles:
            p.update(dt)

        player.update(dt, keys_pressed)

        # Spawn clouds
        spawn_timer += dt
        spawn_rate = max(0.5, 1.2 - score * 0.03)
        if spawn_timer >= spawn_rate:
            roll = random.random()
            if roll > 0.9:
                ctype = "big"
            elif roll > 0.7:
                ctype = "fast"
            else:
                ctype = "normal"
            clouds.append(Cloud(cloud_speed, ctype))
            spawn_timer = 0

        # Spawn powerups
        power_timer += dt
        if power_timer >= 4.0:
            roll = random.random()
            if roll > 0.7:
                ptype = "shield"
            elif roll > 0.4:
                ptype = "score"
            else:
                ptype = "slow"
            powerups.append(PowerUp(ptype))
            power_timer = 0

        # Difficulty scaling
        cloud_speed = min(6.5, 3.2 + score * 0.07)

        # Update clouds
        for c in clouds:
            c.update(dt)
        clouds = [c for c in clouds if c.alive]

        # Update powerups
        for p in powerups:
            p.update(dt)
        powerups = [p for p in powerups if p.alive]

        # Update sparkles
        sparkles = [s for s in sparkles if s.update(dt)]

        # Scoring
        player_hb = player.get_hitbox()
        for c in clouds:
            if not c.passed and c.y + c.h < player.y:
                score += 1
                c.passed = True

        # Win condition
        if score >= WIN_SCORE:
            if score > high_score:
                save_high_score(score)
            return score, True

        # Cloud collision
        if not player.shield and not player.invincible:
            for c in clouds:
                if player_hb.colliderect(c.get_hitbox()):
                    lives -= 1
                    player.invincible = True
                    player.inv_timer = 1.5
                    for _ in range(12):
                        sparkles.append(Sparkle(player.center_x,
                                                player.center_y, RED))
                    if lives <= 0:
                        if score > high_score:
                            save_high_score(score)
                        return score, False
                    break

        # Shield absorbs hit
        if player.shield:
            for c in clouds:
                if player_hb.colliderect(c.get_hitbox()):
                    for _ in range(8):
                        sparkles.append(Sparkle(player.center_x,
                                                player.center_y,
                                                (100, 200, 255)))
                    c.alive = False
                    player.shield = False
                    break

        # Powerup collection
        for p in powerups[:]:
            if player_hb.colliderect(p.get_hitbox()):
                for _ in range(8):
                    sparkles.append(Sparkle(
                        p.x + p.w / 2, p.y + p.h / 2, p.tint))
                if p.power_type == "slow":
                    cloud_speed = max(2, cloud_speed - 0.8)
                elif p.power_type == "shield":
                    player.activate_shield(3.0)
                elif p.power_type == "score":
                    score += 3
                p.alive = False

        powerups = [p for p in powerups if p.alive]

        # High score tracking
        if score > high_score:
            high_score = score

        # ---- DRAW ----
        screen.blit(bg_surface, (0, 0))

        for p in particles:
            p.draw(screen)

        draw_ocean(screen, frame_count)

        for c in clouds:
            c.draw(screen)
        for p in powerups:
            p.draw(screen)

        player.draw(screen, frame_count)

        for s in sparkles:
            s.draw(screen)

        # HUD
        draw_hud(screen, score, high_score, lives, player, frame_count)
        draw_progress_bar(screen, score, WIN_SCORE)

        pygame.display.flip()

    return score, False


# ==================== GAME OVER SCREEN ====================
def game_over_screen(final_score):
    particles = [RainParticle() for _ in range(25)]
    frame_count = 0
    high_score = get_high_score()

    while True:
        dt = clock.tick(FPS) / 1000.0
        frame_count += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return
            if event.type == pygame.MOUSEBUTTONDOWN:
                return

        for p in particles:
            p.update(dt)

        # Draw
        screen.blit(bg_surface, (0, 0))
        for p in particles:
            p.draw(screen)
        draw_ocean(screen, frame_count)

        dy = 130 + math.sin(frame_count * 0.04) * 8

        draw_text(screen, "GAME OVER", WIDTH // 2, dy, 56, RED, center=True)
        draw_text(screen, "The clouds caught you!",
                  WIDTH // 2, dy + 55, 26, WHITE, center=True)
        draw_text(screen, f"Final Score: {final_score}",
                  WIDTH // 2, 290, 44, GOLD, center=True)

        if final_score >= high_score and final_score > 0:
            hue = (frame_count * 3) % 360
            rainbow = hsl_to_rgb(hue, 100, 60)
            draw_text(screen, "NEW HIGH SCORE!",
                      WIDTH // 2, 355, 36, rainbow, center=True)
        else:
            draw_text(screen, f"High Score: {high_score}",
                      WIDTH // 2, 355, 30, WHITE, center=True)

        draw_text(screen, "Don't give up! Try again!",
                  WIDTH // 2, 420, 24, LIGHT_BLUE, center=True)

        pulse = 0.85 + math.sin(frame_count * 0.08) * 0.15
        draw_text(screen, "Press ENTER to Retry",
                  WIDTH // 2, 530, int(32 * pulse), WHITE, center=True)

        pygame.display.flip()


# ==================== VICTORY SCREEN ====================
def victory_screen(final_score):
    particles = [RainParticle() for _ in range(15)]
    frame_count = 0
    high_score = get_high_score()

    # Create confetti data
    confetti_colors = [GOLD, GREEN, WHITE, LIGHT_BLUE, (255, 150, 150), (255, 200, 100)]
    confetti = []
    for _ in range(100):
        confetti.append({
            "x": random.uniform(0, WIDTH),
            "y": random.uniform(-HEIGHT * 1.5, 0),
            "speed": random.uniform(100, 350),
            "color": random.choice(confetti_colors),
            "size": random.randint(3, 8),
            "rot": random.uniform(0, 360),
            "rot_spd": random.uniform(-300, 300),
            "wobble": random.uniform(0, 10),
        })

    while True:
        dt = clock.tick(FPS) / 1000.0
        frame_count += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return
            if event.type == pygame.MOUSEBUTTONDOWN:
                return

        for p in particles:
            p.update(dt)

        # Update confetti
        for c in confetti:
            c["y"] += c["speed"] * dt
            c["x"] += math.sin(frame_count * 0.02 + c["wobble"]) * 1.5
            c["rot"] += c["rot_spd"] * dt
            if c["y"] > HEIGHT + 30:
                c["y"] = random.uniform(-40, -10)
                c["x"] = random.uniform(0, WIDTH)

        # Draw
        screen.blit(victory_bg, (0, 0))

        for p in particles:
            p.draw(screen)

        # Celebration ocean
        for layer in range(3):
            points = [(0, HEIGHT)]
            for x in range(0, WIDTH + 5, 5):
                wy = (HEIGHT - 75 + layer * 22
                      + math.sin(frame_count * 0.06 + x * 0.012 + layer * 1.5) * 14)
                points.append((x, int(wy)))
            points.append((WIDTH, HEIGHT))
            blues = [OCEAN_BLUE, (0, 140, 180), (0, 160, 200)]
            pygame.draw.polygon(screen, blues[layer], points)

        # Confetti
        for c in confetti:
            size = c["size"]
            surf = pygame.Surface((size, max(1, int(size * 0.6))), pygame.SRCALPHA)
            surf.fill(c["color"])
            rotated = pygame.transform.rotate(surf, c["rot"])
            screen.blit(rotated, (int(c["x"]), int(c["y"])))

        # Victory text
        ty = 95 + math.sin(frame_count * 0.04) * 12

        draw_text(screen, "VICTORY!", WIDTH // 2, ty, 70, GOLD, center=True)
        draw_text(screen, "You reached the Ocean!",
                  WIDTH // 2, ty + 58, 32, WHITE, center=True)

        # Animated raindrop
        drop_y = 230 + math.sin(frame_count * 0.06) * 8
        screen.blit(rain_img,
                    (WIDTH // 2 - rain_img.get_width() // 2, int(drop_y)))

        # Ripple effect
        for i in range(3):
            r = 15 + i * 12 + math.sin(frame_count * 0.05 + i) * 5
            alpha = max(0, 180 - i * 50)
            ripple_surf = pygame.Surface((int(r * 2 + 4), int(r * 0.6 + 4)), pygame.SRCALPHA)
            pygame.draw.ellipse(ripple_surf, (100, 200, 255, alpha),
                                (2, 2, int(r * 2), int(r * 0.6)), 2)
            screen.blit(ripple_surf,
                        (int(WIDTH // 2 - r), int(drop_y + 72 - r * 0.15)))

        draw_text(screen, f"Final Score: {final_score}",
                  WIDTH // 2, 375, 44, WHITE, center=True)

        if final_score >= high_score:
            hue = (frame_count * 4) % 360
            rainbow = hsl_to_rgb(hue, 100, 60)
            draw_text(screen, "NEW HIGH SCORE!",
                      WIDTH // 2, 435, 40, rainbow, center=True)
        else:
            draw_text(screen, f"High Score: {high_score}",
                      WIDTH // 2, 435, 32, WHITE, center=True)

        draw_text(screen, "The raindrop completed its journey!",
                  WIDTH // 2, 490, 22, LIGHT_BLUE, center=True)

        pulse = 0.85 + math.sin(frame_count * 0.1) * 0.15
        draw_text(screen, "Press ENTER to Play Again",
                  WIDTH // 2, 555, int(30 * pulse), WHITE, center=True)

        pygame.display.flip()


# ==================== MAIN ====================
if __name__ == "__main__":
    while True:
        welcome_screen()
        final_score, won = game_loop()
        if won:
            victory_screen(final_score)
        else:
            game_over_screen(final_score)