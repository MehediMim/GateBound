import pygame
import sys
import random

# =========================
# CONFIG (DO NOT TOUCH IMAGE SIZE)
# =========================
ROOM_ORIGINAL = 1024
ROOM_SCALE = 0.5
ROOM_DRAW = int(ROOM_ORIGINAL * ROOM_SCALE)  # 512
FPS = 60
PLAYER_SPEED = 5
DEBUG = False

GRID_W = 10
GRID_H = 10

# =========================
# LAYOUT (EXTEND WINDOW)
# =========================
SIDEBAR_W = 200
PADDING = 20

SCREEN_WIDTH  = SIDEBAR_W + ROOM_DRAW + PADDING * 2
SCREEN_HEIGHT = ROOM_DRAW + PADDING * 2

# =========================
# CARD CONFIG
# =========================
CARD_TYPES = ["Jungle", "Desert", "Ice", "Volcanic", "Arcane"]
CARD_MIN_POWER = 1
CARD_MAX_POWER = 9
MAX_CARDS = 5

# =========================
# INIT
# =========================
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tower Puzzle — Rooms (10x10)")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)
map_font = pygame.font.SysFont(None, 14)

# =========================
# ROOM TYPES + BG
# =========================
ROOM_TYPES = ["Jungle", "Desert", "Ice", "Volcanic", "Arcane"]

BG_RAW = {
    "Jungle": pygame.image.load("assets/bg_jungle.png").convert(),
    "Desert": pygame.image.load("assets/bg_desert.png").convert(),
    "Ice": pygame.image.load("assets/bg_ice.png").convert(),
    "Volcanic": pygame.image.load("assets/bg_volcanic.png").convert(),
    "Arcane": pygame.image.load("assets/bg_arcane.png").convert(),
}

BG = {k: pygame.transform.smoothscale(v, (ROOM_DRAW, ROOM_DRAW)) for k, v in BG_RAW.items()}

# =========================
# GAME BOX (SQUARE)
# =========================
GAME_BOX_RECT = pygame.Rect(
    SIDEBAR_W + PADDING,
    PADDING,
    ROOM_DRAW,
    ROOM_DRAW
)

ROOM_RECT = GAME_BOX_RECT.copy()

# =========================
# DOORS + WALK AREA
# =========================
DOORS = {
    "top":    pygame.Rect(ROOM_RECT.centerx - 56, ROOM_RECT.top - 112, 112, 112),
    "bottom": pygame.Rect(ROOM_RECT.centerx - 56, ROOM_RECT.bottom,     112, 112),
    "left":   pygame.Rect(ROOM_RECT.left - 112,   ROOM_RECT.centery - 56, 112, 112),
    "right":  pygame.Rect(ROOM_RECT.right,        ROOM_RECT.centery - 56, 112, 112),
}

WALK_RECT = ROOM_RECT.copy()
for r in DOORS.values():
    WALK_RECT.union_ip(r)

SPAWN = ROOM_RECT.center

# =========================
# WORLD (FIXED 10x10)
# =========================
rooms = {}

def room_id(x, y):
    return y * GRID_W + x

def create_world():
    for y in range(GRID_H):
        for x in range(GRID_W):
            rid = room_id(x, y)
            links = {}
            if y > 0: links["top"] = room_id(x, y - 1)
            if y < GRID_H - 1: links["bottom"] = room_id(x, y + 1)
            if x > 0: links["left"] = room_id(x - 1, y)
            if x < GRID_W - 1: links["right"] = room_id(x + 1, y)

            rooms[rid] = {
                "id": rid,
                "pos": (x, y),
                "type": random.choice(ROOM_TYPES),
                "links": links
            }

create_world()
current = room_id(GRID_W // 2, GRID_H // 2)

# =========================
# PLAYER
# =========================
player = pygame.Rect(0, 0, 16, 16)
player.center = SPAWN

# =========================
# CARDS
# =========================
cards = []

def create_random_card():
    return {
        "type": random.choice(CARD_TYPES),
        "power": random.randint(CARD_MIN_POWER, CARD_MAX_POWER)
    }

def init_cards():
    cards.clear()
    for _ in range(MAX_CARDS):
        cards.append(create_random_card())

init_cards()

# =========================
# MOVEMENT
# =========================
def move(dx, dy):
    player.x += dx
    player.y += dy
    player.clamp_ip(WALK_RECT)

def change_room(direction):
    global current
    if direction in rooms[current]["links"]:
        current = rooms[current]["links"][direction]
        player.center = SPAWN

def handle_doors():
    for d, r in DOORS.items():
        if player.colliderect(r):
            change_room(d)
            break

# =========================
# MINIMAP
# =========================
def draw_minimap():
    panel = pygame.Rect(10, SCREEN_HEIGHT - 210, 200, 200)
    pygame.draw.rect(screen, (20, 20, 20), panel)
    pygame.draw.rect(screen, (180, 180, 180), panel, 2)

    node = 14
    gap = 4
    step = node + gap

    cx = panel.centerx - node // 2
    cy = panel.centery - node // 2

    pygame.draw.rect(screen, (0, 200, 255), (cx, cy, node, node))
    screen.blit(map_font.render(str(current), True, (0, 0, 0)), (cx + 2, cy + 1))

    for d, (dx, dy) in {"top":(0,-1),"bottom":(0,1),"left":(-1,0),"right":(1,0)}.items():
        rid = current
        px, py = cx, cy
        for _ in range(5):
            nxt = rooms[rid]["links"].get(d)
            if nxt is None:
                break
            px += dx * step
            py += dy * step
            pygame.draw.rect(screen, (160,160,160), (px, py, node, node))
            screen.blit(map_font.render(str(nxt), True, (0,0,0)), (px+2, py+1))
            rid = nxt

# =========================
# CARDS UI
# =========================
def draw_cards():
    x, y = 10, 20
    w, h = SIDEBAR_W - 20, 55
    gap = 10

    colors = {
        "Jungle": (60,160,90),
        "Desert": (200,180,80),
        "Ice": (150,200,255),
        "Volcanic": (200,80,60),
        "Arcane": (160,100,200)
    }

    for i, c in enumerate(cards):
        rect = pygame.Rect(x, y + i*(h+gap), w, h)
        pygame.draw.rect(screen, colors[c["type"]], rect, border_radius=6)
        pygame.draw.rect(screen, (0,0,0), rect, 2, border_radius=6)
        screen.blit(map_font.render(c["type"], True, (0,0,0)), (rect.x+8, rect.y+8))
        screen.blit(map_font.render(f"Power {c['power']}", True, (0,0,0)), (rect.x+8, rect.y+30))

# =========================
# LOOP
# =========================
while True:
    clock.tick(FPS)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    k = pygame.key.get_pressed()
    dx = dy = 0
    if k[pygame.K_a] or k[pygame.K_LEFT]: dx -= PLAYER_SPEED
    if k[pygame.K_d] or k[pygame.K_RIGHT]: dx += PLAYER_SPEED
    if k[pygame.K_w] or k[pygame.K_UP]: dy -= PLAYER_SPEED
    if k[pygame.K_s] or k[pygame.K_DOWN]: dy += PLAYER_SPEED

    move(dx, dy)
    handle_doors()

    # ---------- DRAW ----------
    screen.fill((0,0,0))

    # Sidebar
    pygame.draw.rect(screen, (15,15,15), (0,0,SIDEBAR_W,SCREEN_HEIGHT))
    pygame.draw.rect(screen, (180,180,180), (0,0,SIDEBAR_W,SCREEN_HEIGHT), 2)

    # Game box
    pygame.draw.rect(screen, (30,30,30), GAME_BOX_RECT)
    pygame.draw.rect(screen, (180,180,180), GAME_BOX_RECT, 2)

    room = rooms[current]
    cx, cy = ROOM_RECT.topleft
    w = h = ROOM_DRAW
    half = w // 2

    screen.blit(BG[room["type"]], (cx, cy))

    for d, (dx, dy, sx, sy) in {
        "top":    (0, -half, 0, half),
        "bottom": (0,  w,    0, 0),
        "left":   (-half, 0, half, 0),
        "right":  (w, 0, 0, 0),
    }.items():
        nid = room["links"].get(d)
        if nid is not None:
            img = BG[rooms[nid]["type"]].subsurface((sx, sy, half if dx else w, half if dy else h))
            screen.blit(img, (cx+dx, cy+dy))

    pygame.draw.rect(screen, (255,255,255), player)

    draw_cards()
    draw_minimap()

    title = font.render(f"{room['type']} Room (ID {current})", True, (255,255,255))
    screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 5))

    pygame.display.flip()
