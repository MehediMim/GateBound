import pygame
import sys
import random

# =========================
# CONFIG
# =========================
ROOM_ORIGINAL = 720
ROOM_SCALE = 0.5
ROOM_DRAW = int(ROOM_ORIGINAL * ROOM_SCALE)  # 512
FPS = 60
PLAYER_SPEED = 5
DEBUG = False
CARD_WIDTH  = 90
CARD_HEIGHT = 160   # 180 × 16 / 9 ≈ 320

CAN_PASS_DOOR = False

selected_card_index = None
show_swap_ui = False

explored_rooms = set()



GRID_W = 10
GRID_H = 10

visited_rooms = set()


# =========================
# UI / LAYOUT (IMPORTANT)
# =========================
SIDEBAR_W = 360            # LEFT UI ONLY
PREVIEW_MARGIN = ROOM_DRAW // 2     # space for half rooms

SCREEN_WIDTH  = SIDEBAR_W + ROOM_DRAW + PREVIEW_MARGIN * 2
SCREEN_HEIGHT = ROOM_DRAW + PREVIEW_MARGIN * 2

CARD_TYPES = ["Jungle", "Desert", "Ice", "Volcanic", "Arcane"]
CARD_MIN_POWER = 1
CARD_MAX_POWER = 9
MAX_CARDS = 5

selected_card_indices = set()


# One card per gate (fixed once generated)
gate_cards = {
    "top":    {"reward": None, "power": None},
    "bottom": {"reward": None, "power": None},
    "left":   {"reward": None, "power": None},
    "right":  {"reward": None, "power": None},
}

def create_random_card():
    return {
        "type": random.choice(CARD_TYPES),
        "power": random.randint(CARD_MIN_POWER, CARD_MAX_POWER)
    }
cards = [create_random_card() for _ in range(MAX_CARDS)]


def init_gate_cards():
    for d in gate_cards:
        power = random.randint(CARD_MIN_POWER, CARD_MAX_POWER)
        gate_cards[d]["power"] = power

        reward = create_random_card()
        reward["power"] = power   # SAME POWER
        gate_cards[d]["reward"] = reward





# =========================
# INIT
# =========================
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tower Puzzle — Rooms (10x10)")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 36)
map_font = pygame.font.SysFont(None, 14)
retro_font = pygame.font.Font("assets/retro.ttf", 26)
retro_small = pygame.font.Font("assets/retro.ttf", 16)


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
card_images = {
    "jungle": pygame.image.load("assets/card_jungle.jpeg").convert_alpha(),
    "desert": pygame.image.load("assets/card_desert.jpeg").convert_alpha(),
    "ice": pygame.image.load("assets/card_ice.jpeg").convert_alpha(),
    "volcanic": pygame.image.load("assets/card_volcanic.jpeg").convert_alpha(),
    "arcane": pygame.image.load("assets/card_arcane.jpeg").convert_alpha(),
}
CARD_IMAGE_KEY = {
    "Jungle": "jungle",
    "Desert": "desert",
    "Ice": "ice",
    "Volcanic": "volcanic",
    "Arcane": "arcane",
}

ROOM_COLORS = {
    "Jungle":   (60, 160, 90),
    "Desert":   (210, 190, 90),
    "Ice":      (140, 200, 255),
    "Volcanic": (200, 80, 60),
    "Arcane":   (160, 110, 210),
}

passed_free_gate = {
    "top": False,
    "bottom": False,
    "left": False,
    "right": False,
}

def update_free_gate():
    for d, g in FREE_GATES.items():
        if player.colliderect(g):
            passed_free_gate[d] = True


BG = {
    k: pygame.transform.smoothscale(v, (ROOM_DRAW, ROOM_DRAW))
    for k, v in BG_RAW.items()
}

for key in card_images:
    card_images[key] = pygame.transform.smoothscale(
        card_images[key],
        (CARD_WIDTH, CARD_HEIGHT)
    )

# =========================
# GAME BOX (UNCHANGED LOGIC)
# =========================
GAME_BOX_RECT = pygame.Rect(
    SIDEBAR_W + PREVIEW_MARGIN,
    PREVIEW_MARGIN,
    ROOM_DRAW,
    ROOM_DRAW
)

ROOM_RECT = GAME_BOX_RECT.copy()

GATE_THICK = 6

# FREE gate is closer to room center (hit first)
FREE_GATES = {
    "top":    pygame.Rect(ROOM_RECT.centerx - 56, ROOM_RECT.top + 28, 112, GATE_THICK),
    "bottom": pygame.Rect(ROOM_RECT.centerx - 56, ROOM_RECT.bottom - 28 - GATE_THICK, 112, GATE_THICK),
    "left":   pygame.Rect(ROOM_RECT.left + 28, ROOM_RECT.centery - 56, GATE_THICK, 112),
    "right":  pygame.Rect(ROOM_RECT.right - 28 - GATE_THICK, ROOM_RECT.centery - 56, GATE_THICK, 112),
}

# LOCKED gate is closer to the edge (hit second)
LOCKED_GATES = {
    "top":    pygame.Rect(ROOM_RECT.centerx - 56, ROOM_RECT.top + 12, 112, GATE_THICK),
    "bottom": pygame.Rect(ROOM_RECT.centerx - 56, ROOM_RECT.bottom - 12 - GATE_THICK, 112, GATE_THICK),
    "left":   pygame.Rect(ROOM_RECT.left + 12, ROOM_RECT.centery - 56, GATE_THICK, 112),
    "right":  pygame.Rect(ROOM_RECT.right - 12 - GATE_THICK, ROOM_RECT.centery - 56, GATE_THICK, 112),
}


# =========================
# DOORS
# =========================
DOORS = {
    "top":    pygame.Rect(ROOM_RECT.centerx - 56, ROOM_RECT.top - 112, 112, 112),
    "bottom": pygame.Rect(ROOM_RECT.centerx - 56, ROOM_RECT.bottom,     112, 112),
    "left":   pygame.Rect(ROOM_RECT.left - 112,   ROOM_RECT.centery - 56, 112, 112),
    "right":  pygame.Rect(ROOM_RECT.right,        ROOM_RECT.centery - 56, 112, 112),
}

WALL_THICK = 32

WALLS = {
    "top": pygame.Rect(
        ROOM_RECT.left, ROOM_RECT.top,
        ROOM_DRAW, WALL_THICK
    ),
    "bottom": pygame.Rect(
        ROOM_RECT.left, ROOM_RECT.bottom - WALL_THICK,
        ROOM_DRAW, WALL_THICK
    ),
    "left": pygame.Rect(
        ROOM_RECT.left, ROOM_RECT.top,
        WALL_THICK, ROOM_DRAW
    ),
    "right": pygame.Rect(
        ROOM_RECT.right - WALL_THICK, ROOM_RECT.top,
        WALL_THICK, ROOM_DRAW
    ),
}


WALK_RECT = ROOM_RECT.copy()
for r in DOORS.values():
    WALK_RECT.union_ip(r)

SPAWN = ROOM_RECT.center

# =========================
# WORLD (10x10 FIXED)
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
                "links": links,
                "open_gates": {d: False for d in links}   # 👈 ADD THIS
            }


create_world()
current = room_id(GRID_W // 2, GRID_H // 2)
init_gate_cards()
visited_rooms.add(current)



# =========================
# PLAYER
# =========================
player = pygame.Rect(0, 0, 16, 16)
player.center = SPAWN

# =========================
# CARDS
# =========================


# =========================
# MOVEMENT
# =========================
def move(dx, dy):
    # X
    player.x += dx
    for w in get_blocking_walls():
        if player.colliderect(w):
            if dx > 0: player.right = w.left
            if dx < 0: player.left = w.right



    # Y
    player.y += dy
    for w in get_blocking_walls():
        if player.colliderect(w):
            if dy > 0: player.bottom = w.top
            if dy < 0: player.top = w.bottom

    for d, g in LOCKED_GATES.items():
        if rooms[current]["open_gates"].get(d, False):
            continue

        if not passed_free_gate[d]:
            continue
        if player.colliderect(g):
            if dx > 0: player.right = g.left
            if dx < 0: player.left = g.right
            if dy > 0: player.bottom = g.top
            if dy < 0: player.top = g.bottom

def can_interact_gate():
    d = get_free_gate_dir()
    if d is None:
        return None

    # gate already permanently open → no interaction
    if rooms[current]["open_gates"].get(d, False):
        return None

    return d



def try_swap_with_gate(d, selected_indices):
    global cards

    required_type = get_next_room_type(d)
    required_power = gate_cards[d]["power"]

    chosen = [cards[i] for i in selected_indices]

    # TYPE CHECK
    if any(c["type"] != required_type for c in chosen):
        return False

    # POWER SUM CHECK
    if sum(c["power"] for c in chosen) < required_power:
        return False


    # REMOVE GIVEN CARDS
    for i in sorted(selected_indices, reverse=True):
        cards.pop(i)

    # ADD REWARD CARD
    cards.append(gate_cards[d]["reward"])

    cur = current
    nxt = rooms[current]["links"][d]

    # open gate both sides
    rooms[cur]["open_gates"][d] = True

    opposite = {"top":"bottom", "bottom":"top", "left":"right", "right":"left"}
    rooms[nxt]["open_gates"][opposite[d]] = True

    change_room(d)

    return True



def change_room(direction):
    global current, passed_free_gate

    # mark neighbors as explored
    for nxt in rooms[current]["links"].values():
        explored_rooms.add(nxt)

    if direction in rooms[current]["links"]:
        current = rooms[current]["links"][direction]
        visited_rooms.add(current)
        explored_rooms.add(current)

        player.center = SPAWN
        passed_free_gate = {k: False for k in passed_free_gate}


def can_use_card_for_gate(card, d):
    if d is None:
        return False

    required_type = get_next_room_type(d)
    required_power = gate_cards[d]["power"]

    if card["type"] != required_type:
        return False

    # total power of ALL SAME-TYPE cards (including this one)
    total = sum(
        c["power"] for c in cards
        if c["type"] == required_type
    )

    # glow ONLY if reaching the requirement is possible
    return total >= required_power



def handle_doors():
    global current

    for d, r in DOORS.items():
        if not rooms[current]["open_gates"].get(d, False):
            continue

        if player.colliderect(r):
            prev = current
            current = rooms[current]["links"].get(d, current)
            player.center = SPAWN

            # clear transient states ONLY
            for k in passed_free_gate:
                passed_free_gate[k] = False

            # ensure gate is open from BOTH sides
            opposite = {
                "top": "bottom",
                "bottom": "top",
                "left": "right",
                "right": "left"
            }[d]

            rooms[current].setdefault("open_gates", {})
            rooms[current]["open_gates"][opposite] = True

            init_gate_cards()
            break

def draw_press_e_hint():
    d = get_free_gate_dir()

    if d is None:
        return
    txt = retro_small.render("PRESS E", True, (255, 255, 255))
    screen.blit(txt, (player.centerx - txt.get_width() // 2, player.top - 20))


# =========================
# DRAW UI
# =========================

def draw_cards_title():
    text = retro_font.render("CURRENT CARDS", True, (240, 240, 240))
    x = (SIDEBAR_W - text.get_width()) // 2
    y = 10
    screen.blit(text, (x, y))
    
    
def draw_cards():
    start_x = 20
    start_y = 60
    gap_x = 15
    gap_y = 20
    cards_per_row = 3

    for i, c in enumerate(cards):
        key = CARD_IMAGE_KEY[c["type"]]

        row = i // cards_per_row
        col = i % cards_per_row

        x = start_x + col * (CARD_WIDTH + gap_x)
        y = start_y + row * (CARD_HEIGHT + gap_y)

        # card image
        screen.blit(card_images[key], (x, y))

        # GLOW IF CARD CAN BE USED FOR CURRENT GATE
        d = can_interact_gate()
        if d and can_use_card_for_gate(c, d):
            glow = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
            glow.fill((255, 255, 255, 50))
            screen.blit(glow, (x, y))


        # border
        if i in selected_card_indices:
            # glow border
            pygame.draw.rect(
                screen,
                (255, 255, 120),   # glow color
                (x-3, y-3, CARD_WIDTH+6, CARD_HEIGHT+6),
                3,
                border_radius=10
            )

        pygame.draw.rect(
            screen,
            (220, 220, 220),
            (x, y, CARD_WIDTH, CARD_HEIGHT),
            2,
            border_radius=8
        )


        # 🔥 POWER BADGE (BOTTOM-RIGHT)
        power_text = retro_small.render(str(c["power"]), True, (0, 0, 0))
        badge_size = 30
        badge_x = x + CARD_WIDTH - badge_size - 6
        badge_y = y + CARD_HEIGHT - badge_size - 6

        pygame.draw.rect(
            screen,
            (240, 240, 240),
            (badge_x, badge_y, badge_size, badge_size),
            border_radius=4
        )
        pygame.draw.rect(
            screen,
            (0, 0, 0),
            (badge_x, badge_y, badge_size, badge_size),
            2,
            border_radius=4
        )

        screen.blit(
            power_text,
            (
                badge_x + (badge_size - power_text.get_width()) // 2,
                badge_y + (badge_size - power_text.get_height()) // 2
            )
        )


def get_free_gate_dir():
    for d, g in FREE_GATES.items():
        if player.colliderect(g):
            return d
    return None

def draw_full_card(card, x, y):
    key = CARD_IMAGE_KEY[card["type"]]

    # image
    screen.blit(card_images[key], (x, y))

    # border
    pygame.draw.rect(
        screen,
        (220, 220, 220),
        (x, y, CARD_WIDTH, CARD_HEIGHT),
        2,
        border_radius=8
    )

    # power badge
    badge_size = 30
    badge_x = x + CARD_WIDTH - badge_size - 6
    badge_y = y + CARD_HEIGHT - badge_size - 6

    pygame.draw.rect(
        screen,
        (240, 240, 240),
        (badge_x, badge_y, badge_size, badge_size),
        border_radius=4
    )
    pygame.draw.rect(
        screen,
        (0, 0, 0),
        (badge_x, badge_y, badge_size, badge_size),
        2,
        border_radius=4
    )

    power_text = retro_small.render(str(card["power"]), True, (0, 0, 0))
    screen.blit(
        power_text,
        (
            badge_x + (badge_size - power_text.get_width()) // 2,
            badge_y + (badge_size - power_text.get_height()) // 2
        )
    )



def draw_debug_borders():
    # Sidebar
    pygame.draw.rect(screen, (255, 0, 0), (0, 0, SIDEBAR_W, SCREEN_HEIGHT), 2)

    # Main room
    pygame.draw.rect(screen, (0, 255, 0), ROOM_RECT, 2)

    # Doors
    for w in get_blocking_walls():
        pygame.draw.rect(screen, (255, 0, 0), w, 2)
        
    for g in FREE_GATES.values():
        pygame.draw.rect(screen, (0, 255, 0), g, 2)   # first = free

    for g in LOCKED_GATES.values():
        pygame.draw.rect(screen, (255, 255, 0), g, 2) # second = needs E


    # Walkable area
    pygame.draw.rect(screen, (0, 200, 255), WALK_RECT, 2)

    # Card slots
    start_x = 20
    start_y = 60
    gap_x = 15
    gap_y = 20
    cards_per_row = 3

    for i in range(MAX_CARDS):
        row = i // cards_per_row
        col = i % cards_per_row

        x = start_x + col * (CARD_WIDTH + gap_x)
        y = start_y + row * (CARD_HEIGHT + gap_y)

        pygame.draw.rect(
            screen,
            (255, 0, 255),
            (x, y, CARD_WIDTH, CARD_HEIGHT),
            1
        )


def get_blocking_walls():
    blocks = []

    for side, wall in WALLS.items():
        door = DOORS[side]
        left_part = wall.clip(
            pygame.Rect(wall.left, wall.top, door.left - wall.left, wall.height)
        )
        right_part = wall.clip(
            pygame.Rect(door.right, wall.top, wall.right - door.right, wall.height)
        )

        if wall.width > wall.height:  # horizontal wall
            blocks.append(pygame.Rect(wall.left, wall.top, door.left - wall.left, wall.height))
            blocks.append(pygame.Rect(door.right, wall.top, wall.right - door.right, wall.height))
        else:  # vertical wall
            blocks.append(pygame.Rect(wall.left, wall.top, wall.width, door.top - wall.top))
            blocks.append(pygame.Rect(wall.left, door.bottom, wall.width, wall.bottom - door.bottom))

    return blocks

def get_next_room_type(d):
    nxt = rooms[current]["links"].get(d)
    if nxt is None:
        return None
    return rooms[nxt]["type"]

def draw_minimap():
    panel_size = 160
    panel_x = 40
    panel_y = SCREEN_HEIGHT - panel_size - 40

    node = 14
    gap = 4
    step = node + gap
    radius = 5  # how many rooms around current

    pygame.draw.rect(screen, (20, 20, 20), (panel_x, panel_y, panel_size, panel_size))
    pygame.draw.rect(screen, (180, 180, 180), (panel_x, panel_y, panel_size, panel_size), 2)

    cx0, cy0 = rooms[current]["pos"]

    center_x = panel_x + panel_size // 2 - node // 2
    center_y = panel_y + panel_size // 2 - node // 2

    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            nx = cx0 + dx
            ny = cy0 + dy

            if nx < 0 or ny < 0 or nx >= GRID_W or ny >= GRID_H:
                continue

            rid = room_id(nx, ny)

            x = center_x + dx * step
            y = center_y + dy * step

            if rid == current:
                color = (255, 255, 255)  # CURRENT
            elif rid in visited_rooms:
                color = (245, 245, 245)  # VISITED
            elif rid in explored_rooms:
                color = ROOM_COLORS[rooms[rid]["type"]]  # EXPLORED
            else:
                color = (0, 0, 0)  # UNKNOWN

            pygame.draw.rect(screen, color, (x, y, node, node))

            if rid in visited_rooms:
                screen.blit(
                    map_font.render(str(rid), True, (0, 0, 0)),
                    (x + 2, y + 1)
                )

def draw_card(screen, card_type, x, y):
    draw_full_card(card_type, x, y)


def draw_card_with_border(screen, card_type, x, y):
    screen.blit(card_images[card_type], (x, y))
    pygame.draw.rect(
        screen,
        (220, 220, 220),  # light border
        (x, y, CARD_WIDTH, CARD_HEIGHT),
        2
    )

def draw_selected_card(screen, card_type, x, y):
    screen.blit(card_images[card_type], (x, y))
    glow_rect = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
    glow_rect.fill((255, 255, 255, 40))  # soft white glow
    screen.blit(glow_rect, (x, y))

def draw_gate_card_popup():
    d = can_interact_gate()
    if d is None:
        return

    give_type = get_next_room_type(d)
    power = gate_cards[d]["power"]
    reward = gate_cards[d]["reward"]

    cx = ROOM_RECT.centerx
    cy = ROOM_RECT.centery

    # GIVE
    txt1 = retro_small.render("YOU GIVE", True, (255,255,255))
    screen.blit(txt1, (cx-120, cy-140))
    draw_full_card({"type": give_type, "power": power}, cx-150, cy-110)

    # GET
    txt2 = retro_small.render("YOU GET", True, (255,255,255))
    screen.blit(txt2, (cx+30, cy-140))
    draw_full_card(reward, cx+30, cy-110)

    
def draw_swap_button():
    if not show_swap_ui or not selected_card_indices:
        return None


    rect = pygame.Rect(
        ROOM_RECT.centerx - 60,
        ROOM_RECT.centery + CARD_HEIGHT//2 + 20,
        120, 40
    )

    pygame.draw.rect(screen, (80,180,80), rect, border_radius=6)
    pygame.draw.rect(screen, (0,0,0), rect, 2)

    txt = retro_small.render("SWAP", True, (0,0,0))
    screen.blit(txt, (rect.centerx - txt.get_width()//2,
                      rect.centery - txt.get_height()//2))
    return rect


# =========================
# LOOP
# =========================
while True:
    clock.tick(FPS)
    pressed_e = False
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if e.type == pygame.KEYDOWN and e.key == pygame.K_e:
            pressed_e = True
    
    if show_swap_ui and e.type == pygame.MOUSEBUTTONDOWN:
        mx, my = e.pos
        start_x = 20
        start_y = 60
        gap_x = 15
        gap_y = 20
        cards_per_row = 3
        for i, c in enumerate(cards):
            row = i // cards_per_row
            col = i % cards_per_row
            x = start_x + col * (CARD_WIDTH + gap_x)
            y = start_y + row * (CARD_HEIGHT + gap_y)

            card_rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(mx, my):
                if i in selected_card_indices:
                    selected_card_indices.remove(i)
                else:
                    selected_card_indices.add(i)
                break
    

    
    if show_swap_ui and e.type == pygame.MOUSEBUTTONDOWN:
        btn = draw_swap_button()
        if btn and btn.collidepoint(e.pos):
            d = can_interact_gate()
            if d and selected_card_indices:
                if try_swap_with_gate(d, selected_card_indices):
                    selected_card_indices.clear()


    
    
    
    k = pygame.key.get_pressed()
    dx = dy = 0
    if k[pygame.K_a] or k[pygame.K_LEFT]: dx -= PLAYER_SPEED
    if k[pygame.K_d] or k[pygame.K_RIGHT]: dx += PLAYER_SPEED
    if k[pygame.K_w] or k[pygame.K_UP]: dy -= PLAYER_SPEED
    if k[pygame.K_s] or k[pygame.K_DOWN]: dy += PLAYER_SPEED

    move(dx, dy)
    handle_doors()
    
    update_free_gate()
    
    gate_dir = can_interact_gate()
    show_swap_ui = gate_dir is not None



    screen.fill((0,0,0))

    # Sidebar
    pygame.draw.rect(screen, (20,20,20), (0,0,SIDEBAR_W,SCREEN_HEIGHT))
    pygame.draw.rect(screen, (180,180,180), (0,0,SIDEBAR_W,SCREEN_HEIGHT), 2)

    # Game box border
    pygame.draw.rect(screen, (30,30,30), GAME_BOX_RECT)
    pygame.draw.rect(screen, (180,180,180), GAME_BOX_RECT, 2)

    room = rooms[current]
    cx, cy = ROOM_RECT.topleft
    w = h = ROOM_DRAW
    half = w // 2

    # Center
    screen.blit(BG[room["type"]], (cx, cy))

    # Neighbors (VISIBLE, NOT CLIPPED)
    if "top" in room["links"]:
        t = rooms[room["links"]["top"]]
        screen.blit(BG[t["type"]].subsurface((0, half, w, half)), (cx, cy-half))
    if "bottom" in room["links"]:
        b = rooms[room["links"]["bottom"]]
        screen.blit(BG[b["type"]].subsurface((0, 0, w, half)), (cx, cy+w))
    if "left" in room["links"]:
        l = rooms[room["links"]["left"]]
        screen.blit(BG[l["type"]].subsurface((half, 0, half, h)), (cx-half, cy))
    if "right" in room["links"]:
        r = rooms[room["links"]["right"]]
        screen.blit(BG[r["type"]].subsurface((0, 0, half, h)), (cx+w, cy))

    pygame.draw.rect(screen, (255,255,255), player)
    draw_press_e_hint()
    draw_cards_title()
    # draw_cards()
    # draw_gate_card_popup()


    draw_cards()
    # draw_cards()
    draw_minimap()
    draw_gate_card_popup()
    draw_swap_button()



    label = font.render(f"{room['type']} Room (ID {current})", True, (255,255,255))
    screen.blit(label, (SCREEN_WIDTH//2 - label.get_width()//2, 10))
    
    
    if DEBUG:
        draw_debug_borders()


    pygame.display.flip()
