import pygame
import sys
import random

# =========================
# CONFIG
# =========================
ROOM_ORIGINAL = 800
ROOM_SCALE = 0.5
ROOM_DRAW = int(ROOM_ORIGINAL * ROOM_SCALE)  # 512
FPS = 60
PLAYER_SPEED = 5
DEBUG = False
CARD_WIDTH  = 90
CARD_HEIGHT = 160   # 180 × 16 / 9 ≈ 320

CAN_PASS_DOOR = False

FRAME_SIZE = 64
FRAMES_PER_ROW = 4

# =========================
# STORE SYSTEM
# =========================
STORE_MAX_USES = 3
store_uses_left = STORE_MAX_USES

store_selected_indices = set()
store_target_type = None




DIR_ROW = {
    "bottom": 0,
    "left": 1,
    "top": 2,
    "right": 3
}

selected_card_index = None
show_swap_ui = False

explored_rooms = set()



GRID_W = 10
GRID_H = 10

visited_rooms = set()


# =========================
# UI / LAYOUT (IMPORTANT)
# =========================
SIDEBAR_W = 450            # LEFT UI ONLY
PREVIEW_MARGIN = ROOM_DRAW // 2     # space for half rooms

SCREEN_WIDTH  = SIDEBAR_W + ROOM_DRAW + PREVIEW_MARGIN * 2
SCREEN_HEIGHT = ROOM_DRAW + PREVIEW_MARGIN * 2

# =========================
# STORE UI CONSTANTS
# =========================
STORE_BASE_Y = SCREEN_HEIGHT - 140
STORE_BTN_RECT = pygame.Rect(20, STORE_BASE_Y + 65, 160, 38)


CARD_TYPES = ["Jungle", "Desert", "Ice", "Volcanic", "Arcane"]
CARD_MIN_POWER = 1
CARD_MAX_POWER = 9
MAX_CARDS = 10

selected_card_indices = set()
gate_message = ""
gate_message_timer = 0


# One card per gate (fixed once generated)
gate_cards = {
    "top":    {"rewards": [], "power": None},
    "bottom": {"rewards": [], "power": None},
    "left":   {"rewards": [], "power": None},
    "right":  {"rewards": [], "power": None},
}


def create_random_card():
    return {
        "type": random.choice(CARD_TYPES),
        "power": random.randint(CARD_MIN_POWER, CARD_MAX_POWER)
    }
cards = []
for _ in range(MAX_CARDS):
    c = create_random_card()
    c["power"] = random.randint(6, CARD_MAX_POWER)  # stronger start
    cards.append(c)

def init_gate_cards():
    for d in gate_cards:
        power = random.randint(CARD_MIN_POWER, CARD_MAX_POWER)
        gate_cards[d]["power"] = power

        gate_cards[d]["rewards"] = []

        for _ in range(2):
            r = create_random_card()
            r["power"] = power
            gate_cards[d]["rewards"].append(r)




selected_reward_index = None


# =========================
# INIT
# =========================
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
idle_sheet = pygame.image.load("assets/player_idle.png").convert_alpha()
walk_sheet = pygame.image.load("assets/player_walk.png").convert_alpha()

pygame.display.set_caption("Tower Puzzle — Rooms (10x10)")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 36)
map_font = pygame.font.SysFont(None, 14)
retro_font = pygame.font.Font("assets/retro.ttf", 26)
retro_small = pygame.font.Font("assets/retro.ttf", 16)
retro_power = pygame.font.Font("assets/retro.ttf", 48)  # ← change 48


player_dir = "bottom"   # default facing
player_frame = 0
anim_timer = 0
moving = False


def get_player_frame(direction, frame, moving):
    row = DIR_ROW[direction]
    sheet = walk_sheet if moving else idle_sheet

    x = frame * FRAME_SIZE
    y = row * FRAME_SIZE

    return sheet.subsurface((x, y, FRAME_SIZE, FRAME_SIZE))

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

def try_store_swap():
    global store_uses_left
    global cards
    global store_selected_indices
    global store_target_type
    global gate_message, gate_message_timer

    # ===== USE LIMIT =====
    if store_uses_left <= 0:
        gate_message = "STORE EMPTY!"
        gate_message_timer = 90
        return False

    # ===== EXACTLY 2 CARDS =====
    if len(store_selected_indices) != 2:
        gate_message = "SELECT 2 CARDS!"
        gate_message_timer = 90
        return False

    i1, i2 = list(store_selected_indices)
    c1 = cards[i1]
    c2 = cards[i2]

    # ===== SAME TYPE REQUIRED =====
    if c1["type"] != c2["type"]:
        gate_message = "CARDS MUST BE SAME TYPE!"
        gate_message_timer = 90
        return False

    # ===== TARGET TYPE REQUIRED =====
    if store_target_type is None:
        gate_message = "CHOOSE TARGET TYPE!"
        gate_message_timer = 90
        return False

    # ===== POWER SUM (CAPPED) =====
    new_power = c1["power"] + c2["power"]
    if new_power > CARD_MAX_POWER:
        new_power = CARD_MAX_POWER

    # ===== REMOVE OLD CARDS =====
    for i in sorted(store_selected_indices, reverse=True):
        cards.pop(i)

    # ===== ADD NEW CARD =====
    cards.append({
        "type": store_target_type,
        "power": new_power
    })

    # ===== RESET =====
    store_selected_indices.clear()
    store_target_type = None
    store_uses_left -= 1

    gate_message = f"TRADE SUCCESS! POWER {new_power}"
    gate_message_timer = 90
    return True


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
    global selected_reward_index
    global cards

    required_type = get_next_room_type(d)
    required_power = gate_cards[d]["power"]

    chosen = [cards[i] for i in selected_indices]

    # TYPE CHECK
    if any(c["type"] != required_type for c in chosen):
        global gate_message, gate_message_timer
        gate_message = "WRONG CARD TYPE!"
        gate_message_timer = 90
        return False

    # POWER SUM CHECK
    if sum(c["power"] for c in chosen) < required_power:
        gate_message = "NOT ENOUGH POWER!"
        gate_message_timer = 90
        return False

    # REMOVE GIVEN CARDS
    for i in sorted(selected_indices, reverse=True):
        cards.pop(i)

    # ADD REWARD CARD
    # MUST SELECT A REWARD

    if selected_reward_index is None:
        gate_message = "CHOOSE A REWARD!"
        gate_message_timer = 90
        return False

    reward = gate_cards[d]["rewards"][selected_reward_index]
    cards.append(reward)
    selected_reward_index = None


    cur = current
    nxt = rooms[current]["links"][d]

    # open gate both sides
    rooms[cur]["open_gates"][d] = True

    opposite = {"top":"bottom", "bottom":"top", "left":"right", "right":"left"}
    rooms[nxt]["open_gates"][opposite[d]] = True

    change_room(d)
    gate_message = "GATE OPENED!"
    gate_message_timer = 90
    selected_reward_index = None
    return True

def handle_events():
    global pressed_e
    global selected_card_indices
    global selected_reward_index
    global store_selected_indices
    global store_target_type

    pressed_e = False

    start_x = 20
    start_y = 60
    gap_x = 15
    gap_y = 20
    cards_per_row = 4

    for e in pygame.event.get():

        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_e:
                pressed_e = True

        if e.type != pygame.MOUSEBUTTONDOWN:
            continue

        mx, my = e.pos

        # =====================================
        # LEFT CLICK
        # =====================================
        if e.button == 1:

            # -------- GATE CARD SELECTION --------
            if show_swap_ui:
                for i, c in enumerate(cards):
                    row = i // cards_per_row
                    col = i % cards_per_row
                    x = start_x + col * (CARD_WIDTH + gap_x)
                    y = start_y + row * (CARD_HEIGHT + gap_y)

                    if pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT).collidepoint(mx, my):
                        if i in selected_card_indices:
                            selected_card_indices.remove(i)
                        else:
                            selected_card_indices.add(i)
                        break

                # -------- GATE REWARD SELECTION --------
                d = can_interact_gate()
                if d:
                    rewards = gate_cards[d]["rewards"]
                    cx = ROOM_RECT.centerx
                    cy = ROOM_RECT.centery

                    for i, r in enumerate(rewards):
                        rx = cx + 30 + i * (CARD_WIDTH + 20)
                        ry = cy - 110
                        if pygame.Rect(rx, ry, CARD_WIDTH, CARD_HEIGHT).collidepoint(mx, my):
                            selected_reward_index = i
                            break

                # -------- GATE SWAP BUTTON --------
                btn = draw_swap_button()
                if btn and btn.collidepoint(mx, my):
                    if d and selected_card_indices:
                        if try_swap_with_gate(d, selected_card_indices):
                            selected_card_indices.clear()

            # -------- STORE TARGET TYPE --------
            type_y = STORE_BASE_Y + 28
            for i, t in enumerate(CARD_TYPES):
                r = pygame.Rect(20 + i * 80, type_y, 70, 22)
                if r.collidepoint(mx, my):
                    store_target_type = t

                if r.collidepoint(mx, my):
                    store_target_type = t

            # -------- STORE TRADE BUTTON --------
            if STORE_BTN_RECT.collidepoint(mx, my):
                try_store_swap()

        # =====================================
        # RIGHT CLICK — STORE CARD SELECTION
        # =====================================
        if e.button == 3:
            for i, c in enumerate(cards):
                row = i // cards_per_row
                col = i % cards_per_row
                x = start_x + col * (CARD_WIDTH + gap_x)
                y = start_y + row * (CARD_HEIGHT + gap_y)

                if pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT).collidepoint(mx, my):
                    if i in store_selected_indices:
                        store_selected_indices.remove(i)
                    else:
                        if len(store_selected_indices) < 2:
                            store_selected_indices.add(i)
                    break



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
    txt = retro_small.render("Wanna Pass??", True, (255, 255, 255))
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
    cards_per_row = 4

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
        if i in store_selected_indices:
            pygame.draw.rect(
                screen,
                (120,200,255),
                (x-3, y-3, CARD_WIDTH+6, CARD_HEIGHT+6),
                3,
                border_radius=10
            )



        # BIG POWER IN CENTER
        power_str = str(c["power"])

        # outline (black border)
        power_outline = retro_power.render(power_str, True, (0, 0, 0))
        power_text    = retro_power.render(power_str, True, (255, 255, 255))

        px = x + CARD_WIDTH // 2 - power_text.get_width() // 2
        py = y + CARD_HEIGHT // 2 - power_text.get_height() // 2

        # draw outline (4 directions)
        screen.blit(power_outline, (px - 2, py))
        screen.blit(power_outline, (px + 2, py))
        screen.blit(power_outline, (px, py - 2))
        screen.blit(power_outline, (px, py + 2))

        # draw main text
        screen.blit(power_text, (px, py))



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

    draw_card_power(x, y, card["power"])


def draw_gate_message():
    if gate_message_timer <= 0:
        return

    txt = retro_font.render(gate_message, True, (255, 200, 120))
    screen.blit(
        txt,
        (ROOM_RECT.centerx - txt.get_width() // 2,
         ROOM_RECT.centery + CARD_HEIGHT + 80)
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
    cards_per_row = 4

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
def draw_store_ui():
    center_x = SIDEBAR_W // 2

    title = retro_font.render("STORE", True, (255, 220, 160))
    screen.blit(title, (center_x - title.get_width() // 2, STORE_BASE_Y - 50))

    uses = retro_small.render(f"USES LEFT: {store_uses_left}", True, (200, 200, 200))
    screen.blit(uses, (20, STORE_BASE_Y - 20))

    hint = retro_small.render("GIVE 2 SAME - GET 1", True, (170, 170, 170))
    screen.blit(hint, (20, STORE_BASE_Y))

    # ---- TARGET TYPE ----
    type_y = STORE_BASE_Y + 28
    type_gap = 80

    for i, t in enumerate(CARD_TYPES):
        x = 20 + i * type_gap
        rect = pygame.Rect(x, type_y, 70, 22)

        if t == store_target_type:
            pygame.draw.rect(screen, (255, 255, 120), rect, 2)
            col = (255, 255, 120)
        else:
            pygame.draw.rect(screen, (90, 90, 90), rect, 1)
            col = (170, 170, 170)

        txt = retro_small.render(t, True, col)
        screen.blit(txt, (rect.centerx - txt.get_width() // 2,
                          rect.centery - txt.get_height() // 2))

    # ---- TRADE BUTTON ----
    pygame.draw.rect(screen, (120, 160, 120), STORE_BTN_RECT, border_radius=6)
    pygame.draw.rect(screen, (0, 0, 0), STORE_BTN_RECT, 2)

    txt = retro_small.render("TRADE", True, (0, 0, 0))
    screen.blit(txt, (STORE_BTN_RECT.centerx - txt.get_width() // 2,
                      STORE_BTN_RECT.centery - txt.get_height() // 2))



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
    panel_x = SCREEN_WIDTH - panel_size - 30
    panel_y = SCREEN_HEIGHT - panel_size - 30

    center = (
        panel_x + panel_size // 2,
        panel_y + panel_size // 2
    )
    radius_px = panel_size // 2 - 2


    node = 14
    gap = 4
    step = node + gap
    radius = 5  # how many rooms around current

    center = (panel_x + panel_size // 2, panel_y + panel_size // 2)
    radius_px = panel_size // 2 -2

    pygame.draw.circle(screen, (20, 20, 20), center, radius_px)
    pygame.draw.circle(screen, (180, 180, 180), center, radius_px, 2)

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

            rx = x + node // 2
            ry = y + node // 2

            
            # draw cell (inside circular mask check)
            if (rx - center[0])**2 + (ry - center[1])**2 <= radius_px**2:
                pygame.draw.rect(screen, color, (x, y, node, node))

                # 🔥 CURRENT ROOM GLOW
                if rid == current:
                    pygame.draw.rect(
                        screen,
                        (255, 255, 120),           # glow color
                        (x - 2, y - 2, node + 4, node + 4),
                        2,
                        border_radius=3
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
    
def draw_card_power(x, y, power):
    text = str(power)

    outline = retro_power.render(text, True, (0, 0, 0))
    main    = retro_power.render(text, True, (255, 255, 255))

    cx = x + CARD_WIDTH // 2
    cy = y + CARD_HEIGHT // 2

    for ox, oy in [(-2,0),(2,0),(0,-2),(0,2)]:
        screen.blit(outline, (cx - outline.get_width()//2 + ox,
                               cy - outline.get_height()//2 + oy))

    screen.blit(main, (cx - main.get_width()//2,
                       cy - main.get_height()//2))


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
    rewards = gate_cards[d]["rewards"]

    cx = ROOM_RECT.centerx
    cy = ROOM_RECT.centery

    # GIVE
    txt1 = retro_small.render("YOU GIVE", True, (255,255,255))
    screen.blit(txt1, (cx-120, cy-140))
    draw_full_card({"type": give_type, "power": power}, cx-150, cy-110)

    # GET
    txt2 = retro_small.render("YOU GET ANY OF", True, (255,255,255))
    screen.blit(txt2, (cx+30, cy-140))
    for i, r in enumerate(rewards):
        rx = cx + 30 + i * (CARD_WIDTH + 20)
        ry = cy - 110
    
        draw_full_card(r, rx, ry)
    
        # highlight selected
        if selected_reward_index == i:
            pygame.draw.rect(
                screen,
                (255,255,120),
                (rx-4, ry-4, CARD_WIDTH+8, CARD_HEIGHT+8),
                3,
                border_radius=8
            )

    
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
    if gate_message_timer > 0:
        gate_message_timer -= 1

    handle_events()


    
    
    
    
    
    
    
    k = pygame.key.get_pressed()
    dx = dy = 0
    if k[pygame.K_a] or k[pygame.K_LEFT]: dx -= PLAYER_SPEED
    if k[pygame.K_d] or k[pygame.K_RIGHT]: dx += PLAYER_SPEED
    if k[pygame.K_w] or k[pygame.K_UP]: dy -= PLAYER_SPEED
    if k[pygame.K_s] or k[pygame.K_DOWN]: dy += PLAYER_SPEED

    move(dx, dy)
        # === STEP 4: animation update ===
    if dx != 0 or dy != 0:
        moving = True

        if dy > 0: player_dir = "bottom"
        elif dy < 0: player_dir = "top"
        elif dx < 0: player_dir = "left"
        elif dx > 0: player_dir = "right"

        anim_timer += 1
        if anim_timer >= 8:        # animation speed
            anim_timer = 0
            player_frame = (player_frame + 1) % 4
    else:
        moving = False
        player_frame = 0
        
            
            

    
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

    # === STEP 5: draw animated player ===
    img = get_player_frame(player_dir, player_frame, moving)
    screen.blit(img, player.topleft)

    draw_press_e_hint()
    draw_cards_title()
    # draw_cards()
    # draw_gate_card_popup()


    draw_cards()
    # draw_cards()
    draw_minimap()
    draw_gate_card_popup()
    draw_gate_message()

    draw_swap_button()
    draw_store_ui()




    title_text = f"{room['type']} CHAMBER  -  #{current}"
    title = retro_font.render(title_text, True, (240, 240, 240))

    title_x = GAME_BOX_RECT.centerx - title.get_width() // 2
    title_y = GAME_BOX_RECT.top - 34

    screen.blit(title, (title_x, title_y))

    
    
    if DEBUG:
        draw_debug_borders()


    pygame.display.flip()
