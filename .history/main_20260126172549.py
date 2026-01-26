import pygame
import sys
import random

# =========================================================
# CONFIG
# =========================================================
SCREEN_SIZE = 720
FPS = 60
PLAYER_SPEED = 5
DEBUG = True   # set to False to hide debug overlay
CENTER_SCALE = 0.6      # center room uses 60% of screen
PREVIEW_SCALE = 0.25    # previews are smaller



# =========================================================
# INIT
# =========================================================
pygame.init()
screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
pygame.display.set_caption("Tower Puzzle — Rooms")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# =========================================================
# ROOM TYPES (FINAL)
# =========================================================
ROOM_TYPES = ["Jungle", "Desert", "Ice", "Volcanic", "Arcane"]

BG_IMAGES = {
    "Jungle":   pygame.image.load("assets/bg_jungle.png").convert(),
    "Desert":   pygame.image.load("assets/bg_desert.png").convert(),
    "Ice":      pygame.image.load("assets/bg_ice.png").convert(),
    "Volcanic": pygame.image.load("assets/bg_volcanic.png").convert(),
    "Arcane":   pygame.image.load("assets/bg_arcane.png").convert(),
}

def scale_image(img, scale):
    w, h = img.get_size()
    return pygame.transform.smoothscale(
        img, (int(w * scale), int(h * scale))
    )

SCALED_CENTER = {
    k: scale_image(v, CENTER_SCALE) for k, v in BG_IMAGES.items()
}

SCALED_PREVIEW = {
    k: scale_image(v, PREVIEW_SCALE) for k, v in BG_IMAGES.items()
}

CENTER_IMG_SIZE = SCALED_CENTER["Jungle"].get_size()
CENTER_POS = (
    SCREEN_SIZE//2 - CENTER_IMG_SIZE[0]//2,
    SCREEN_SIZE//2 - CENTER_IMG_SIZE[1]//2
)

PREVIEW_OFFSET = 20

# =========================================================
# PIXEL-PERFECT GEOMETRY (FROM YOUR IMAGE)
# =========================================================
ROOM_RECT = pygame.Rect(312, 312, 400, 400)

DOORS = {
    "top":    pygame.Rect(400,  88, 224, 224),
    "bottom": pygame.Rect(400, 712, 224, 224),
    "left":   pygame.Rect( 88, 400, 224, 224),
    "right":  pygame.Rect(712, 400, 224, 224),
}

SPAWN_POINT = (512, 512)

# =========================================================
# ROOM GRAPH (PERSISTENT)
# =========================================================
rooms = {}
room_id_counter = 0

def create_room(from_room=None):
    global room_id_counter

    room = {
        "id": room_id_counter,
        "type": random.choice(ROOM_TYPES),
        "from": from_room,          # back link
        "connections": {}           # top/left/right
    }

    rooms[room_id_counter] = room
    room_id_counter += 1
    return room["id"]

current_room = create_room()

# =========================================================
# PLAYER
# =========================================================
player = pygame.Rect(0, 0, 24, 24)
player.center = SPAWN_POINT

# =========================================================
# MOVEMENT
# =========================================================
def move_player(dx, dy):
    player.x += dx
    player.y += dy

    # Clamp inside room interior
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

            # BACK DOOR
            if name == "bottom":
                if rooms[current_room]["from"] is not None:
                    current_room = rooms[current_room]["from"]

            # FORWARD DOORS
            else:
                if name not in rooms[current_room]["connections"]:
                    new_room = create_room(from_room=current_room)
                    rooms[current_room]["connections"][name] = new_room

                current_room = rooms[current_room]["connections"][name]

            player.center = SPAWN_POINT
            break
        
        
def draw_debug():
    # Room interior
    pygame.draw.rect(screen, (0, 255, 0), ROOM_RECT, 2)

    # Doors
    for name, rect in DOORS.items():
        pygame.draw.rect(screen, (255, 0, 0), rect, 2)

        label = font.render(name, True, (255, 0, 0))
        screen.blit(label, (rect.x + 5, rect.y + 5))

    # Player hitbox
    pygame.draw.rect(screen, (0, 150, 255), player, 2)


# =========================================================
# GAME LOOP
# =========================================================
while True:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Input
    keys = pygame.key.get_pressed()
    dx = dy = 0

    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        dx -= PLAYER_SPEED
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        dx += PLAYER_SPEED
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        dy -= PLAYER_SPEED
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        dy += PLAYER_SPEED

    move_player(dx, dy)
    handle_doors()

    # =====================================================
    # DRAW
    # =====================================================
        room = rooms[current_room]

    screen.fill((0, 0, 0))  # background

    # -----------------------------
    # Draw PREVIEW rooms
    # -----------------------------
    cx, cy = CENTER_POS
    cw, ch = CENTER_IMG_SIZE

    # Bottom (previous)
    if room["from"] is not None:
        prev_room = rooms[room["from"]]
        img = SCALED_PREVIEW[prev_room["type"]]
        screen.blit(
            img,
            (cx + cw//2 - img.get_width()//2, cy + ch + PREVIEW_OFFSET)
        )

    # Forward rooms
    for dir_name, offset in {
        "top":    (0, -PREVIEW_OFFSET),
        "left":   (-PREVIEW_OFFSET, 0),
        "right":  (PREVIEW_OFFSET, 0),
    }.items():

        if dir_name in room["connections"]:
            r = rooms[room["connections"][dir_name]]
            img = SCALED_PREVIEW[r["type"]]

            px = cx + cw//2 - img.get_width()//2
            py = cy + ch//2 - img.get_height()//2

            if dir_name == "top":
                py -= ch//2 + img.get_height()
            elif dir_name == "left":
                px -= cw//2 + img.get_width()
            elif dir_name == "right":
                px += cw//2 + img.get_width()

            screen.blit(img, (px, py))

    # -----------------------------
    # Draw CENTER room
    # -----------------------------
    screen.blit(SCALED_CENTER[room["type"]], CENTER_POS)

    # Player (still drawn in absolute coords)
    pygame.draw.rect(screen, (255, 255, 255), player)

    # Room Type Text
    label = font.render(f"{room['type']} Room", True, (255, 255, 255))
    screen.blit(label, (SCREEN_SIZE//2 - label.get_width()//2, 30))

    if DEBUG:
        draw_debug()
        
        
    pygame.display.flip()
