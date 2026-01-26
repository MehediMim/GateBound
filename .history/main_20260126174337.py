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
HALF = ROOM_DRAW // 2                        # 256 (overlap so "half" is visible)
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

BG = {
    k: pygame.transform.smoothscale(v, (ROOM_DRAW, ROOM_DRAW))
    for k, v in BG_RAW.items()
}

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

SPAWN = ROOM_RECT.center

# =========================
# ROOM GRAPH (PERSISTENT)
# =========================
rooms = {}
rid = 0

def new_room(frm=None):
    """Create a room node only. Does NOT generate its neighbors."""
    global rid
    rooms[rid] = {
        "id": rid,
        "type": random.choice(ROOM_TYPES),
        "from": frm,              # back link (bottom)
        "next": {},               # top/left/right -> room_id
        "generated": False        # neighbors not generated yet
    }
    rid += 1
    return rid - 1

def ensure_neighbors(room_id):
    """Generate top/left/right neighbors ONCE for this room, then save."""
    room = rooms[room_id]
    if room["generated"]:
        return

    for d in ("top", "left", "right"):
        if d not in room["next"]:
            child = new_room(frm=room_id)
            room["next"][d] = child

    room["generated"] = True

current = new_room(frm=None)
ensure_neighbors(current)

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
                    ensure_neighbors(current)
            else:
                ensure_neighbors(current)
                current = rooms[current]["next"][d]
                ensure_neighbors(current)

            player.center = SPAWN
            break

def draw_debug():
    pygame.draw.rect(screen, (0, 255, 0), ROOM_RECT, 2)
    for name, r in DOORS.items():
        pygame.draw.rect(screen, (255, 0, 0), r, 2)
        t = font.render(name, True, (255, 0, 0))
        screen.blit(t, (r.x + 5, r.y + 5))
    pygame.draw.rect(screen, (0, 150, 255), player, 2)

# =========================
# DRAW HELPERS
# =========================
def blit_center(img):
    screen.blit(img, ROOM_RECT.topleft)

def blit_half(img, dx, dy):
    # dx/dy are shifts relative to center room position
    cx, cy = ROOM_RECT.topleft
    screen.blit(img, (cx + dx, cy + dy))

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
    if k[pygame.K_a] or k[pygame.K_LEFT]:  dx -= PLAYER_SPEED
    if k[pygame.K_d] or k[pygame.K_RIGHT]: dx += PLAYER_SPEED
    if k[pygame.K_w] or k[pygame.K_UP]:    dy -= PLAYER_SPEED
    if k[pygame.K_s] or k[pygame.K_DOWN]:  dy += PLAYER_SPEED

    move(dx, dy)
    handle_doors()

# =====================
# DRAW
# =====================
screen.fill((0, 0, 0))

room = rooms[current]
cx, cy = ROOM_RECT.topleft
w, h = ROOM_DRAW, ROOM_DRAW
half = w // 2

# -------- CENTER ROOM (full) --------
screen.blit(BG[room["type"]], (cx, cy))

# -------- TOP ROOM (show bottom half) --------
top_room = rooms[room["next"]["top"]]
top_img = BG[top_room["type"]].subsurface(
    pygame.Rect(0, half, w, half)
)
screen.blit(top_img, (cx, cy - half))

# -------- BOTTOM ROOM (show top half) --------
if room["from"] is not None:
    bottom_room = rooms[room["from"]]
    bottom_img = BG[bottom_room["type"]].subsurface(
        pygame.Rect(0, 0, w, half)
    )
    screen.blit(bottom_img, (cx, cy + w))

# -------- LEFT ROOM (show right half) --------
left_room = rooms[room["next"]["left"]]
left_img = BG[left_room["type"]].subsurface(
    pygame.Rect(half, 0, half, h)
)
screen.blit(left_img, (cx - half, cy))

# -------- RIGHT ROOM (show left half) --------
right_room = rooms[room["next"]["right"]]
right_img = BG[right_room["type"]].subsurface(
    pygame.Rect(0, 0, half, h)
)
screen.blit(right_img, (cx + w, cy))

# -------- PLAYER --------
pygame.draw.rect(screen, (255, 255, 255), player)

# -------- LABEL --------
label = font.render(f"{room['type']} Room", True, (255, 255, 255))
screen.blit(label, (SCREEN // 2 - label.get_width() // 2, 18))

if DEBUG:
    draw_debug()

pygame.display.flip()
