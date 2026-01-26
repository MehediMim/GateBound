import pygame
import sys
import random

# =========================================================
# CONFIG
# =========================================================
SCREEN_SIZE = 720
ROOM_SIZE = 1024          # actual room image size
FPS = 60
PLAYER_SPEED = 5
DEBUG = True

# =========================================================
# INIT
# =========================================================
pygame.init()
screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
pygame.display.set_caption("Tower Puzzle — Rooms")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# =========================================================
# ROOM TYPES
# =========================================================
ROOM_TYPES = ["Jungle", "Desert", "Ice", "Volcanic", "Arcane"]

BG_IMAGES = {
    "Jungle":   pygame.image.load("assets/bg_jungle.png").convert(),
    "Desert":   pygame.image.load("assets/bg_desert.png").convert(),
    "Ice":      pygame.image.load("assets/bg_ice.png").convert(),
    "Volcanic": pygame.image.load("assets/bg_volcanic.png").convert(),
    "Arcane":   pygame.image.load("assets/bg_arcane.png").convert(),
}

# =========================================================
# GEOMETRY (1024 layout, world space)
# =========================================================
ROOM_RECT = pygame.Rect(312, 312, 400, 400)

DOORS = {
    "top":    pygame.Rect(400,  88, 224, 224),
    "bottom": pygame.Rect(400, 712, 224, 224),
    "left":   pygame.Rect( 88, 400, 224, 224),
    "right":  pygame.Rect(712, 400, 224, 224),
}

SPAWN_POINT = (512, 512)

# Camera origin so CENTER room is centered,
# and ADJACENT rooms are HALF visible
CAMERA_ORIGIN = (
    SCREEN_SIZE // 2 - ROOM_SIZE // 2,
    SCREEN_SIZE // 2 - ROOM_SIZE // 2
)

HALF_OFFSET = ROOM_SIZE // 2

# =========================================================
# ROOM GRAPH
# =========================================================
rooms = {}
room_id_counter = 0

def create_room(from_room=None):
    global room_id_counter
    room = {
        "id": room_id_counter,
        "type": random.choice(ROOM_TYPES),
        "from": from_room,
        "connections": {}
    }
    rooms[room_id_counter] = room
    room_id_counter += 1
    return room["id"]

current_room = create_room()

# =========================================================
# PLAYER (world space)
# =========================================================
player = pygame.Rect(0, 0, 24, 24)
player.center = SPAWN_POINT

# =========================================================
# LOGIC
# =========================================================
def move_player(dx, dy):
    player.x += dx
    player.y += dy

    if player.left < ROOM_RECT.left:
        player.left = ROOM_RECT.left
    if player.right > ROOM_RECT.right:
        player.right = ROOM_RECT.right
    if player.top < ROOM_RECT.top:
        player.top = ROOM_RECT.top
    if player.bottom > ROOM_RECT.bottom:
        player.bottom = ROOM_RECT.bottom

def handle_doors():
    global current_room
    for name, rect in DOORS.items():
        if player.colliderect(rect):
            if name == "bottom":
                if rooms[current_room]["from"] is not None:
                    current_room = rooms[current_room]["from"]
            else:
                if name not in rooms[current_room]["connections"]:
                    new_room = create_room(from_room=current_room)
                    rooms[current_room]["connections"][name] = new_room
                current_room = rooms[current_room]["connections"][name]
            player.center = SPAWN_POINT
            break

def draw_debug():
    pygame.draw.rect(
        screen, (0, 255, 0),
        ROOM_RECT.move(CAMERA_ORIGIN), 2
    )
    for rect in DOORS.values():
        pygame.draw.rect(
            screen, (255, 0, 0),
            rect.move(CAMERA_ORIGIN), 2
        )
    pygame.draw.rect(
        screen, (0, 150, 255),
        player.move(CAMERA_ORIGIN), 2
    )

# =========================================================
# GAME LOOP
# =========================================================
while True:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    dx = dy = 0
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= PLAYER_SPEED
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += PLAYER_SPEED
    if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= PLAYER_SPEED
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += PLAYER_SPEED

    move_player(dx, dy)
    handle_doors()

    # =====================================================
    # DRAW
    # =====================================================
    screen.fill((0, 0, 0))
    cx, cy = CAMERA_ORIGIN
    room = rooms[current_room]

    # CENTER room
    screen.blit(BG_IMAGES[room["type"]], (cx, cy))

    # BOTTOM (previous) — half visible
    if room["from"] is not None:
        prev_room = rooms[room["from"]]
        screen.blit(
            BG_IMAGES[prev_room["type"]],
            (cx, cy + HALF_OFFSET)
        )

    # FORWARD rooms — half visible
    offsets = {
        "top":    (0, -HALF_OFFSET),
        "left":   (-HALF_OFFSET, 0),
        "right":  (HALF_OFFSET, 0),
    }

    for d, (ox, oy) in offsets.items():
        if d in room["connections"]:
            r = rooms[room["connections"][d]]
            screen.blit(
                BG_IMAGES[r["type"]],
                (cx + ox, cy + oy)
            )

    # Player
    pygame.draw.rect(
        screen, (255, 255, 255),
        player.move(CAMERA_ORIGIN)
    )

    # Room label
    label = font.render(f"{room['type']} Room", True, (255, 255, 255))
    screen.blit(label, (SCREEN_SIZE // 2 - label.get_width() // 2, 20))

    if DEBUG:
        draw_debug()

    pygame.display.flip()
