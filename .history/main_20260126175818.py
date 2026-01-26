import pygame
import sys
import random

# =========================
# CONFIG
# =========================
SCREEN = 720
ROOM_ORIGINAL = 1024
ROOM_SCALE = 0.5
ROOM_DRAW = int(ROOM_ORIGINAL * ROOM_SCALE)  # 512
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
# CENTER ROOM RECT (SCREEN SPACE)
# =========================
ROOM_RECT = pygame.Rect(
    SCREEN // 2 - ROOM_DRAW // 2,
    SCREEN // 2 - ROOM_DRAW // 2,
    ROOM_DRAW,
    ROOM_DRAW
)

# Door hitboxes around the center room (screen space)
DOORS = {
    "top":    pygame.Rect(ROOM_RECT.centerx - 56, ROOM_RECT.top - 112, 112, 112),
    "bottom": pygame.Rect(ROOM_RECT.centerx - 56, ROOM_RECT.bottom,     112, 112),
    "left":   pygame.Rect(ROOM_RECT.left - 112,   ROOM_RECT.centery - 56, 112, 112),
    "right":  pygame.Rect(ROOM_RECT.right,        ROOM_RECT.centery - 56, 112, 112),
}

# Allow player to reach doors
WALK_RECT = ROOM_RECT.copy()
for r in DOORS.values():
    WALK_RECT.union_ip(r)

SPAWN = ROOM_RECT.center

# =========================
# ROOM GRAPH (PERSISTENT, BIDIRECTIONAL)
# =========================
rooms = {}
rid = 0

OPPOSITE = {
    "top": "bottom",
    "bottom": "top",
    "left": "right",
    "right": "left"
}

def new_room():
    global rid
    rooms[rid] = {
        "id": rid,
        "type": random.choice(ROOM_TYPES),
        "links": {}  # direction -> room_id (bidirectional)
    }
    rid += 1
    return rid - 1

def connect_rooms(a, direction, b):
    rooms[a]["links"][direction] = b
    rooms[b]["links"][OPPOSITE[direction]] = a

def ensure_neighbors(room_id):
    room = rooms[room_id]
    for d in ("top", "left", "right"):
        if d not in room["links"]:
            child = new_room()
            connect_rooms(room_id, d, child)

# Start game
current = new_room()
ensure_neighbors(current)

# =========================
# PLAYER
# =========================
player = pygame.Rect(0, 0, 16, 16)
player.center = SPAWN

# =========================
# MOVEMENT + ROOM CHANGE
# =========================
def move(dx, dy):
    player.x += dx
    player.y += dy
    player.clamp_ip(WALK_RECT)

def change_room(direction):
    global current
    ensure_neighbors(current)

    if direction in rooms[current]["links"]:
        current = rooms[current]["links"][direction]
        ensure_neighbors(current)
        player.center = SPAWN

        # DEBUG PRINT
        r = rooms[current]
        print("---- ROOM CHANGE ----")
        print("Current:", current)
        for k in ("top", "left", "right", "bottom"):
            print(f"  {k} ->", r["links"].get(k))
        print("---------------------")

def handle_doors():
    for direction, rect in DOORS.items():
        if player.colliderect(rect):
            change_room(direction)
            break

# =========================
# DEBUG DRAW
# =========================
def draw_debug():
    pygame.draw.rect(screen, (0, 255, 0), ROOM_RECT, 2)
    pygame.draw.rect(screen, (255, 255, 0), WALK_RECT, 2)
    for name, r in DOORS.items():
        pygame.draw.rect(screen, (255, 0, 0), r, 2)
        t = font.render(name, True, (255, 0, 0))
        screen.blit(t, (r.x + 5, r.y + 5))
    pygame.draw.rect(screen, (0, 150, 255), player, 2)

def draw_debug_info():
    y = 60
    line_h = 20
    room = rooms[current]

    def line(text):
        nonlocal y
        screen.blit(font.render(text, True, (255, 255, 0)), (10, y))
        y += line_h

    line(f"Current room: {current}")
    line(f"Top: {room['links'].get('top')}")
    line(f"Left: {room['links'].get('left')}")
    line(f"Right: {room['links'].get('right')}")
    line(f"Bottom: {room['links'].get('bottom')}")
    
def print_room_list():
    print("====== ROOM LIST ======")
    for rid, room in rooms.items():
        print(f"Room {rid}: {room['type']}")
    print("=======================")


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
    if k[pygame.K_a] or k[pygame.K_LEFT]:
        dx -= PLAYER_SPEED
    if k[pygame.K_d] or k[pygame.K_RIGHT]:
        dx += PLAYER_SPEED
    if k[pygame.K_w] or k[pygame.K_UP]:
        dy -= PLAYER_SPEED
    if k[pygame.K_s] or k[pygame.K_DOWN]:
        dy += PLAYER_SPEED

    move(dx, dy)
    handle_doors()

    # =====================
    # DRAW (HALF PREVIEWS)
    # =====================
    screen.fill((0, 0, 0))

    ensure_neighbors(current)
    room = rooms[current]
    cx, cy = ROOM_RECT.topleft
    w = h = ROOM_DRAW
    half = w // 2

    # Center room (full)
    screen.blit(BG[room["type"]], (cx, cy))

    # Top room (show bottom half)
    top_id = room["links"].get("top")
    if top_id is not None:
        top_room = rooms[top_id]
        top_img = BG[top_room["type"]].subsurface(pygame.Rect(0, half, w, half))
        screen.blit(top_img, (cx, cy - half))

    # Bottom room (show top half)
    bottom_id = room["links"].get("bottom")
    if bottom_id is not None:
        bottom_room = rooms[bottom_id]
        bottom_img = BG[bottom_room["type"]].subsurface(pygame.Rect(0, 0, w, half))
        screen.blit(bottom_img, (cx, cy + w))

    # Left room (show right half)
    left_id = room["links"].get("left")
    if left_id is not None:
        left_room = rooms[left_id]
        left_img = BG[left_room["type"]].subsurface(pygame.Rect(half, 0, half, h))
        screen.blit(left_img, (cx - half, cy))

    # Right room (show left half)
    right_id = room["links"].get("right")
    if right_id is not None:
        right_room = rooms[right_id]
        right_img = BG[right_room["type"]].subsurface(pygame.Rect(0, 0, half, h))
        screen.blit(right_img, (cx + w, cy))

    # Player
    pygame.draw.rect(screen, (255, 255, 255), player)

    # Label
    label = font.render(f"{room['type']} Room", True, (255, 255, 255))
    screen.blit(label, (SCREEN // 2 - label.get_width() // 2, 18))

    if DEBUG:
        draw_debug()
        draw_debug_info()

    pygame.display.flip()
