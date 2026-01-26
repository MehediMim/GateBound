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
DEBUG = False 

GRID_W = 10
GRID_H = 10

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
screen = pygame.display.set_mode((SCREEN, SCREEN))
pygame.display.set_caption("Tower Puzzle — Rooms (10x10)")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
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
# LAYOUT
# =========================
SIDEBAR_W = 200
GAME_W = SCREEN - SIDEBAR_W
GAME_H = SCREEN

# =========================
# CENTER ROOM RECT (SCREEN SPACE)
# =========================
ROOM_RECT = pygame.Rect(
    SIDEBAR_W + (GAME_W - ROOM_DRAW) // 2,
    (GAME_H - ROOM_DRAW) // 2,
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
# FIXED 10x10 WORLD (PERSISTENT)
# =========================
rooms = {}

def room_id(x, y):
    return y * GRID_W + x

def id_to_xy(rid):
    return (rid % GRID_W, rid // GRID_W)

def create_world():
    for y in range(GRID_H):
        for x in range(GRID_W):
            rid = room_id(x, y)

            links = {}
            if y > 0:              links["top"] = room_id(x, y - 1)
            if y < GRID_H - 1:     links["bottom"] = room_id(x, y + 1)
            if x > 0:              links["left"] = room_id(x - 1, y)
            if x < GRID_W - 1:     links["right"] = room_id(x + 1, y)

            rooms[rid] = {
                "id": rid,
                "pos": (x, y),
                "type": random.choice(ROOM_TYPES),  # random ONCE
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



def print_cards():
    print("---- CARDS ----")
    for i, c in enumerate(cards):
        print(f"{i}: {c['type']} ({c['power']})")
    print("---------------")

init_cards()
print_cards()
print("CARDS AT START:", cards)




# =========================
# MOVEMENT + ROOM CHANGE
# =========================
def move(dx, dy):
    player.x += dx
    player.y += dy
    player.clamp_ip(WALK_RECT)

def print_room_list():
    print("====== ROOM LIST (10x10) ======")
    for rid in range(GRID_W * GRID_H):
        print(f"Room {rid:02d} @ {rooms[rid]['pos']}: {rooms[rid]['type']}")
    print("===============================")

def change_room(direction):
    global current
    if direction in rooms[current]["links"]:
        current = rooms[current]["links"][direction]
        player.center = SPAWN

        r = rooms[current]
        print("---- ROOM CHANGE ----")
        print("Current:", current, "Grid:", r["pos"], "Type:", r["type"])
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
        t = map_font.render(name, True, (255, 0, 0))
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

    line(f"Room ID: {current}  Grid: {room['pos']}  Type: {room['type']}")
    line(f"Top: {room['links'].get('top')}")
    line(f"Left: {room['links'].get('left')}")
    line(f"Right: {room['links'].get('right')}")
    line(f"Bottom: {room['links'].get('bottom')}")

# =========================
# MINIMAP (CROSS: MAX 5 EACH SIDE)
# =========================
def draw_minimap():
    panel_size = 200
    panel_x = 10
    panel_y = SCREEN - panel_size - 10


    node = 16
    gap = 4
    step = node + gap

    center_x = panel_x + panel_size // 2 - node // 2
    center_y = panel_y + panel_size // 2 - node // 2

    pygame.draw.rect(screen, (20, 20, 20), (panel_x, panel_y, panel_size, panel_size))
    pygame.draw.rect(screen, (200, 200, 200), (panel_x, panel_y, panel_size, panel_size), 2)

    # center
    pygame.draw.rect(screen, (0, 200, 255), (center_x, center_y, node, node))
    screen.blit(map_font.render(str(current), True, (0, 0, 0)), (center_x + 3, center_y + 2))

    for d, (dx, dy) in {
        "top": (0, -1),
        "bottom": (0, 1),
        "left": (-1, 0),
        "right": (1, 0),
    }.items():
        rid = current
        cx, cy = center_x, center_y

        for _ in range(5):
            nxt = rooms[rid]["links"].get(d)
            if nxt is None:
                break

            cx += dx * step
            cy += dy * step

            pygame.draw.line(
                screen, (120, 120, 120),
                (cx + node // 2 - dx * step, cy + node // 2 - dy * step),
                (cx + node // 2, cy + node // 2),
                2
            )

            pygame.draw.rect(screen, (170, 170, 170), (cx, cy, node, node))
            screen.blit(map_font.render(str(nxt), True, (0, 0, 0)), (cx + 3, cy + 2))

            rid = nxt
def draw_cards():
    x = 10
    y = 60
    w = SIDEBAR_W - 20
    h = 60
    gap = 10

    for i, c in enumerate(cards):
        color = {
            "Jungle": (50, 160, 80),
            "Desert": (200, 180, 80),
            "Ice": (150, 200, 255),
            "Volcanic": (200, 80, 60),
            "Arcane": (160, 100, 200)
        }[c["type"]]

        rect = pygame.Rect(x, y + i * (h + gap), w, h)

        pygame.draw.rect(screen, color, rect, border_radius=6)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2, border_radius=6)

        t1 = map_font.render(c["type"], True, (0, 0, 0))
        t2 = map_font.render(f"Power: {c['power']}", True, (0, 0, 0))

        screen.blit(t1, (rect.x + 8, rect.y + 8))
        screen.blit(t2, (rect.x + 8, rect.y + 32))


# =========================
# LOOP
# =========================
while True:
    clock.tick(FPS)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_p:   # print whole list on demand
                print_room_list()

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


    # Game box background
    pygame.draw.rect(
        screen,
        (30, 30, 30),
        (SIDEBAR_W, 0, GAME_W, GAME_H)
    )
    pygame.draw.rect(
        screen,
        (180, 180, 180),
        (SIDEBAR_W, 0, GAME_W, GAME_H),
        2
    )

    # =====================
    # DRAW (HALF PREVIEWS)
    # =====================
    screen.fill((0, 0, 0))

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
    label = font.render(f"{room['type']} Room  (ID {current}, {room['pos']})", True, (255, 255, 255))
    screen.blit(label, (SCREEN // 2 - label.get_width() // 2, 18))

    if DEBUG:
        draw_debug()
        draw_debug_info()
        draw_minimap()

    draw_cards()

    pygame.display.flip()
