import pygame
import os
import random
import math
import sys

# --------------------------------------------------------------
# INITIAL SETUP
# --------------------------------------------------------------
os.chdir(os.path.dirname(os.path.abspath(__file__)))
pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("SPACE")
clock = pygame.time.Clock()

# --------------------------------------------------------------
# FONTS
# --------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(BASE_DIR, "imagefont.ttf")
if not os.path.exists(font_path):
    raise FileNotFoundError(f"Font file not found: {font_path}")

title_font = pygame.font.Font(font_path, 120)
instruction_font = pygame.font.Font(font_path, 30)

# --------------------------------------------------------------
# SAFE IMAGE LOADER
# --------------------------------------------------------------
def load_image_safe(path, width=None, height=None, fallback_color=(200, 200, 200)):
    try:
        img = pygame.image.load(path).convert_alpha()
        if width and height:
            img = pygame.transform.scale(img, (width, height))
        return img
    except:
        surf = pygame.Surface((width or 50, height or 50), pygame.SRCALPHA)
        surf.fill(fallback_color)
        return surf

# --------------------------------------------------------------
# BUTTON CLASS
# --------------------------------------------------------------
class Button:
    def __init__(self, x, y, image, w, h):
        self.image = pygame.transform.scale(image, (w, h))
        self.rect = self.image.get_rect(center=(x, y))
        self.clicked = False

    def draw(self):
        action = False
        mouse_pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(mouse_pos):
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                self.clicked = True
                action = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        screen.blit(self.image, self.rect)
        return action

# --------------------------------------------------------------
# LOAD IMAGES
# --------------------------------------------------------------
start_img   = load_image_safe("playimg2.jpg", 350, 100)
option_img  = load_image_safe("options1.jfif", 350, 100)
credit_img  = load_image_safe("aboutimg.jfif", 350, 100)
back_img    = load_image_safe("back1.png", 150, 60)

player_img      = load_image_safe("Sprite2.png", 50, 50)
asteroid_img    = load_image_safe("asteroid.png", 80, 80)
background_img  = load_image_safe("BACKGROUND.png", SCREEN_WIDTH, SCREEN_HEIGHT)

# --------------------------------------------------------------
# STAR BACKGROUND
# --------------------------------------------------------------
def create_stars(n):
    stars = []
    for _ in range(n):
        stars.append({
            "x": random.randint(0, SCREEN_WIDTH),
            "y": random.randint(0, SCREEN_HEIGHT),
            "size": random.randint(1, 3),
            "brightness": random.randint(120, 255),
            "twinkle_speed": random.uniform(0.5, 1.5),
            "direction": random.choice([-1, 1]),
        })
    return stars

def draw_stars(stars):
    for star in stars:
        star["brightness"] += star["twinkle_speed"] * star["direction"]
        if star["brightness"] > 255 or star["brightness"] < 120:
            star["direction"] *= -1
        b = max(120, min(255, int(star["brightness"])))
        pygame.draw.circle(screen, (b, b, b), (star["x"], star["y"]), star["size"])

# --------------------------------------------------------------
# TEXT HELPER
# --------------------------------------------------------------
def draw_text_centered(text, font, color, y):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(SCREEN_WIDTH//2, y))
    screen.blit(surface, rect)

# --------------------------------------------------------------
# PLAYER CLASS
# --------------------------------------------------------------
class Player:
    def __init__(self):
        self.img = player_img
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.angle = 0
        self.rotation_speed = 4
        self.vel_x = 0
        self.vel_y = 0
        self.acceleration = 0.25
        self.friction = 0.99
        self.max_speed = 8

    def rotate(self, direction):
        if direction == "LEFT":
            self.angle += self.rotation_speed
        elif direction == "RIGHT":
            self.angle -= self.rotation_speed
        self.angle %= 360

    def thrust(self):
        rad = math.radians(self.angle)
        self.vel_x += -math.sin(rad) * self.acceleration
        self.vel_y += -math.cos(rad) * self.acceleration
        speed = math.hypot(self.vel_x, self.vel_y)
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.vel_x *= scale
            self.vel_y *= scale

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_x *= self.friction
        self.vel_y *= self.friction
        if self.x < 0: self.x = SCREEN_WIDTH
        if self.x > SCREEN_WIDTH: self.x = 0
        if self.y < 0: self.y = SCREEN_HEIGHT
        if self.y > SCREEN_HEIGHT: self.y = 0

    def draw(self):
        rotated = pygame.transform.rotate(self.img, self.angle)
        rect = rotated.get_rect(center=(self.x, self.y))
        screen.blit(rotated, rect)

# --------------------------------------------------------------
# BULLET CLASS
# --------------------------------------------------------------
class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.speed = 12
        rad = math.radians(angle)
        self.vel_x = -math.sin(rad) * self.speed
        self.vel_y = -math.cos(rad) * self.speed
        self.radius = 4

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        return (0 < self.x < SCREEN_WIDTH) and (0 < self.y < SCREEN_HEIGHT)

    def draw(self):
        pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), self.radius)

# --------------------------------------------------------------
# ASTEROID CLASS
# --------------------------------------------------------------
class Asteroid:
    def __init__(self):
        self.img = asteroid_img
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = -80
        self.speed = random.uniform(1, 3)
        self.angle = random.uniform(0, 360)
        rad = math.radians(self.angle)
        self.vel_x = math.cos(rad) * self.speed
        self.vel_y = math.sin(rad) * self.speed

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        return self.y <= SCREEN_HEIGHT + 100

    def draw(self):
        screen.blit(self.img, (self.x, self.y))

    def rect(self):
        return pygame.Rect(self.x, self.y, 80, 80)

# --------------------------------------------------------------
# GAME OVER SCREEN
# --------------------------------------------------------------
def game_over_screen():
    timer = 120  # 2 seconds at 60 FPS
    while timer > 0:
        screen.fill((0, 0, 0))
        draw_text_centered("GAME OVER", title_font, (255, 0, 0), SCREEN_HEIGHT//2)
        pygame.display.update()
        clock.tick(60)
        timer -= 1

# --------------------------------------------------------------
# GAME LOOP
# --------------------------------------------------------------
def game_loop():
    player = Player()
    bullets = []
    asteroids = []
    asteroid_timer = 0

    while True:
        screen.blit(background_img, (0, 0))
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if event.key == pygame.K_SPACE:
                    bullets.append(Bullet(player.x, player.y, player.angle))

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player.rotate("LEFT")
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player.rotate("RIGHT")
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            player.thrust()

        asteroid_timer += 1
        if asteroid_timer > 60:
            asteroids.append(Asteroid())
            asteroid_timer = 0

        asteroids = [a for a in asteroids if a.update()]
        bullets = [b for b in bullets if b.update()]

        # Player collision
        for a in asteroids:
            if a.rect().collidepoint(player.x, player.y):
                game_over_screen()
                return

        # Bullet collision
        for b in bullets:
            for a in asteroids:
                if a.rect().collidepoint(b.x, b.y):
                    bullets.remove(b)
                    asteroids.remove(a)
                    break

        # Draw
        player.update()
        player.draw()
        for b in bullets: b.draw()
        for a in asteroids: a.draw()

        pygame.display.update()

# --------------------------------------------------------------
# BUTTONS
# --------------------------------------------------------------
center_x = SCREEN_WIDTH // 2
start_button   = Button(center_x, 250, start_img, 350, 100)
option_button  = Button(center_x, 370, option_img, 350, 100)
credit_button  = Button(center_x, 490, credit_img, 350, 100)
back_button    = Button(SCREEN_WIDTH - 100, SCREEN_HEIGHT - 50, back_img, 150, 60)

# --------------------------------------------------------------
# ABOUT & OPTIONS
# --------------------------------------------------------------
def options_loop():
    while True:
        screen.fill((0, 0, 0))
        draw_text_centered("OPTIONS COMING SOON!", instruction_font, (255, 255, 255), SCREEN_HEIGHT // 2)
        if back_button.draw(): return
        pygame.display.update()

def about_loop():
    lines = ["Made by Alec", "Thanks for playing!"]
    h = instruction_font.get_height()
    start_y = SCREEN_HEIGHT//2 - (len(lines)*h)//2
    while True:
        screen.fill((0, 0, 0))
        for i, text in enumerate(lines):
            draw_text_centered(text, instruction_font, (255, 255, 255), start_y + i*h)
        if back_button.draw(): return
        pygame.display.update()

# --------------------------------------------------------------
# MAIN MENU
# --------------------------------------------------------------
def main_menu():
    stars = create_stars(150)
    while True:
        screen.fill((0, 0, 20))
        draw_stars(stars)
        draw_text_centered("SPACE", title_font, (255, 255, 255), 150)

        if start_button.draw(): game_loop()
        if option_button.draw(): options_loop()
        if credit_button.draw(): about_loop()

        pygame.display.update()

# --------------------------------------------------------------
# RUN GAME
# --------------------------------------------------------------
if __name__ == "__main__":
    main_menu()
