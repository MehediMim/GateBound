import pygame
import sys
import random

# =========================
# CONFIG
# =========================
SCREEN = 720
ROOM_SIZE = 1024
FPS = 60
PLAYER_SPEED = 5
DEBUG = True

# =========================
# INIT
# =========================
pygame.init()
screen = pygame.display.set_mode((SCREEN, SCREEN))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# =========================
# ROOM TYPES
# =========================
ROOM_TYPES = ["Jungle", "Desert", "Ice", "Volcanic", "Arcane"]

BG = {
    "Jungle": pygame.image.load("assets/bg_jungle.png").convert(),
    "Desert": pygame.image.load("assets/bg_desert.png").convert(),
    "Ice": pygame.image.load("assets/bg_ice.png").convert(),
    "Volcanic": pygame.image.load("assets/bg_volcanic.png").convert(),
    "Arcane": pygame.image.load("assets/bg_arcane.png").convert(),
}

# =========================
# GEOMETRY (WORLD SPACE)
# =========================
ROOM_RECT = pygame.Rect(312, 312, 400, 400)

DOORS = {
    "top": pygame.Rect(400, 88, 224, 224),
    "bottom": pygame.Rect(400, 712, 224, 224),
    "left": pygame.Rect(88, 400, 224, 224),
    "right": pygame.Rect(712, 400, 224, 224),
}

SPAWN = (512, 512)

# =========================
# CAMERA (THIS WAS THE BUG)
# =========================
CAMERA_X = ROOM_SIZE // 2 - SCREEN // 2
CAMERA_Y = ROOM_SIZE // 2 - SCREEN // 2

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
# PLAYER (WORLD SPACE)
# =========================
player = pygame.Rect(0, 0, 24, 24)
player.center = SPAWN

# =========================
# LOGIC
# =========================
def move(dx, dy):
    player.x += dx
    player.y += dy
    player.clamp_ip(ROOM_RECT)

def doors():
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

def debug():
    pygame.draw.rect(screen, (0,255,0),
        ROOM_RECT.move(-CAMERA_X, -CAMERA_Y), 2)
    for r in DOORS.values():
        pygame.draw.rect(screen, (255,0,0),
            r.move(-CAMERA_X, -CAMERA_Y), 2)
    pygame.draw.rect(screen, (0,150,255),
        player.move(-CAMERA_X, -CAMERA_Y), 2)

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
    doors()

    # =====================
    # DRAW (CORRECT)
    # =====================
    screen.fill((0,0,0))
    room = rooms[current]

    # CENTER
    screen.blit(BG[room["type"]],
        (-CAMERA_X, -CAMERA_Y))

    # BOTTOM
    if room["from"] is not None:
        screen.blit(BG[rooms[room["from"]]["type"]],
            (-CAMERA_X, ROOM_SIZE - CAMERA_Y))

    # FORWARD
    for d,(ox,oy) in {
        "top":(0,-ROOM_SIZE),
        "left":(-ROOM_SIZE,0),
        "right":(ROOM_SIZE,0)
    }.items():
        if d in room["next"]:
            screen.blit(
                BG[rooms[room["next"][d]]["type"]],
                (ox - CAMERA_X, oy - CAMERA_Y)
            )

    pygame.draw.rect(screen,(255,255,255),
        player.move(-CAMERA_X, -CAMERA_Y))

    label = font.render(room["type"]+" Room", True,(255,255,255))
    screen.blit(label,(SCREEN//2-label.get_width()//2,15))

    if DEBUG:
        debug()

    pygame.display.flip()
