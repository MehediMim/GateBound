import pygame
import sys
import random

# =========================
# CONFIG
# =========================
SCREEN = 720
ROOM_ORIGINAL = 1024
ROOM_SCALE = 0.5            # <<< THIS IS THE KEY
ROOM_DRAW = int(ROOM_ORIGINAL * ROOM_SCALE)
FPS = 60
PLAYER_SPEED = 5
DEBUG = True

# =========================
# INIT
# =========================
pygame.init()
screen = pygame.display.set_mode((SCREEN, SCREEN))
pygame.display.set_caption("Tower Puzzle — Rooms")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# =========================
# ROOM TYPES
# =========================
ROOM_TYPES = ["Jungle", "Desert", "Ice", "Volcanic", "Arcane"]

BG_RAW = {
    "Jungle": pygame.image.load("assets/bg_jungle.png").convert(),
    "Desert": pygame.image.load("assets/bg_desert.png").convert(),
    "Ice": pygame.image.load("assets/bg_ice.png").convert(),
    "Volcanic": pygame.image.load("assets/bg_volcanic.png").convert(),
    "Arcane": pygame.image.load("assets/bg_arcane.png").convert(),
}

BG = {
    k: pygame.transform.smoothscale(v, (ROOM_DRAW, ROOM_DRAW))
    for k, v in BG_RAW.items()
}

# =========================
# ROOM GEOMETRY (SCALED)
# =========================
ROOM_RECT = pygame.Rect(
    SCREEN//2 - ROOM_DRAW//2,
    SCREEN//2 - ROOM_DRAW//2,
    ROOM_DRAW,
    ROOM_DRAW
)

# Doors (relative to scaled room)
DOORS = {
    "top": pygame.Rect(
        ROOM_RECT.centerx - 56, ROOM_RECT.top - 112, 112, 112),
    "bottom": pygame.Rect(
        ROOM_RECT.centerx - 56, ROOM_RECT.bottom, 112, 112),
    "left": pygame.Rect(
        ROOM_RECT.left - 112, ROOM_RECT.centery - 56, 112, 112),
    "right": pygame.Rect(
        ROOM_RECT.right, ROOM_RECT.centery - 56, 112, 112),
}

SPAWN = ROOM_RECT.center

# =========================
# ROOM GRAPH
# =========================
rooms = {}
rid = 0

def new_room(frm=None):
    global rid
    rooms[rid] = {
        "type": random.choice(ROOM_TYPES),
        "from": frm,
        "next": {}
    }
    rid += 1
    return rid - 1

current = new_room()

# =========================
# PLAYER
# =========================
player = pygame.Rect(0, 0, 16, 16)
player.center = SPAWN

# =========================
# LOGIC
# =========================
def move(dx, dy):
    player.x += dx
    player.y += dy
    player.clamp_ip(ROOM_RECT)

def handle_doors():
    global current
    for d, r in DOORS.items():
        if player.colliderect(r):
            if d == "bottom":
                if rooms[current]["from"] is not None:
                    current = rooms[current]["from"]
            else:
                if d not in rooms[current]["next"]:
                    rooms[current]["next"][d] = new_room(current)
                current = rooms[current]["next"][d]
            player.center = SPAWN
            break

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
    if k[pygame.K_a]: dx -= PLAYER_SPEED
    if k[pygame.K_d]: dx += PLAYER_SPEED
    if k[pygame.K_w]: dy -= PLAYER_SPEED
    if k[pygame.K_s]: dy += PLAYER_SPEED

    move(dx, dy)
    handle_doors()

    # =====================
    # DRAW
    # =====================
    screen.fill((0, 0, 0))
    room = rooms[current]

    cx, cy = ROOM_RECT.topleft

    # Center
    screen.blit(BG[room["type"]], (cx, cy))

    # Adjacent rooms
    if room["from"] is not None:
        screen.blit(BG[rooms[room["from"]]["type"]],
                    (cx, cy + ROOM_DRAW))

    for d, (ox, oy) in {
        "top": (0, -ROOM_DRAW),
        "left": (-ROOM_DRAW, 0),
        "right": (ROOM_DRAW, 0),
    }.items():
        if d in room["next"]:
            screen.blit(
                BG[rooms[room["next"][d]]["type"]],
                (cx + ox, cy + oy)
            )

    # Player
    pygame.draw.rect(screen, (255,255,255), player)

    # Label
    label = font.render(room["type"]+" Room", True, (255,255,255))
    screen.blit(label, (SCREEN//2 - label.get_width()//2, 20))

    if DEBUG:
        pygame.draw.rect(screen, (0,255,0), ROOM_RECT, 2)
        for r in DOORS.values():
            pygame.draw.rect(screen, (255,0,0), r, 2)
        pygame.draw.rect(screen, (0,150,255), player, 2)

    pygame.display.flip()
