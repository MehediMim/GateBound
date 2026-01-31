import pygame
import sys
import random

# =========================
# CONFIG
# =========================
HOWTO_TEXT = """
HOW TO PLAY (MANDATORY)

1. OVERALL GAME STRUCTURE
The game takes place in a 10 × 10 grid of rooms.
Each room is connected to neighboring rooms through gates on the top, bottom, left, or right side.

At the start:
- The player spawns in a random room.
- One room in the grid is randomly selected as the escape room.
- The player does NOT know the full map initially.

Your goal is to:
- Explore rooms
- Open gates using cards
- Reach the escape room before your points run out

There is no combat in the game.

2. POINTS SYSTEM (TIME PRESSURE)
- You start the game with 1000 points.
- Points decrease automatically every second.
- This creates constant pressure to make decisions efficiently.

If:
- Points reach 0 → GAME OVER
- You reach the escape room → YOU WIN

Points do NOT regenerate. There is no way to gain extra points.

3. PLAYER MOVEMENT
Movement:
- W / A / S / D or Arrow Keys
- Movement is free inside the room
- Walls block movement
- Doors allow movement between rooms (only if unlocked)

The player always spawns at the center of a room when entering it.

4. ROOMS
Each room:
- Has a visual theme (Jungle, Desert, Ice, Volcanic, Arcane)
- May contain up to four gates
- Is part of the larger grid

Room states:
- CURRENT: the room you are in now
- VISITED: rooms you have entered before
- EXPLORED: rooms adjacent to visited rooms (seen but not entered)
- UNKNOWN: rooms you have not discovered yet

5. GATES (CORE MECHANIC)
Each gate has:
- A required card type
- A required total power value

Rules:
- You can use multiple cards to open a gate
- All used cards are consumed permanently
- Once opened, a gate stays open forever
- Opening a gate unlocks it from BOTH sides

6. CARD SYSTEM
Each card has:
- TYPE: Jungle / Desert / Ice / Volcanic / Arcane
- POWER: 1 to 9

Only cards matching the gate’s required type can be used.
Power values from selected cards are added together.
If total power ≥ required power → gate can be opened

7. SELECTING CARDS FOR A GATE
- LEFT CLICK on cards to select them
- Selected cards are highlighted
- You can select more than one card

8. GATE REWARDS
- Two reward cards are shown
- Choose one reward (LEFT CLICK)
- Then click SWAP

9. STORE SYSTEM
- Limited uses
1) RIGHT CLICK to select exactly 2 cards
2) The two cards MUST be same type
3) Choose a target type
4) Click TRADE

10. MINIMAP SYSTEM
- Circular visibility radius
- Only rooms inside the circle are fully visible
- Red outline = Escape room (always visible)

11. STRATEGY
Key decisions:
- Which gate to open first
- When to use store
- Which reward to take

12. WIN CONDITION
You win immediately when you enter the Escape Room.

13. LOSE CONDITION
You lose when points reach zero.

14. IMPORTANT NOTES
- No combat, no enemies
- Difficulty comes from planning + time pressure
- Each run differs due to random layout and rewards
""".strip()


last_printed_room = None

ROOM_ORIGINAL = 800
ROOM_SCALE = 0.5
ROOM_DRAW = int(ROOM_ORIGINAL * ROOM_SCALE)  # 512
FPS = 60
PLAYER_SPEED = 5
DEBUG = True
CARD_WIDTH  = 90
CARD_HEIGHT = 160   # 180 × 16 / 9 ≈ 320
footstep_timer = 0
MAX_POINTS = 1000
POINT_DECAY_PER_SEC = 1
points = MAX_POINTS
time_accumulator = 0
GAME_OVER = False
GAME_WIN = False
GAME_ENDED = False

prev_show_gate_popup = False
CAN_PASS_DOOR = False
CONFIRM_BTN_OFFSET_X = 0   # try 0 → adjust ±10 if needed

# Back to menu button
show_menu_confirmation = False

FRAME_SIZE = 64
FRAMES_PER_ROW = 4


STATE_MENU = "menu"
STATE_DIFFICULTY = "difficulty"
STATE_HOWTO = "howto"
STATE_GAME = "game"
STATE_QUIT = "quit"

game_state = STATE_MENU

# =========================
# DIFFICULTY LEVELS
# =========================
DIFFICULTY_EASY = "easy"
DIFFICULTY_MEDIUM = "medium"
DIFFICULTY_HARD = "hard"

current_difficulty = DIFFICULTY_EASY

# Difficulty settings
difficulty_settings = {
    DIFFICULTY_EASY: {
        "max_points": 1000,
        "point_decay": 1,
        "minimap_radius": 5,
        "store_uses": 3,
        "score_multiplier": 1
    },
    DIFFICULTY_MEDIUM: {
        "max_points": 500,
        "point_decay": 1,
        "minimap_radius": 3,
        "store_uses": 2,
        "score_multiplier": 3
    },
    DIFFICULTY_HARD: {
        "max_points": 300,
        "point_decay": 1,
        "minimap_radius": 2,
        "store_uses": 1,
        "score_multiplier": 5
    }
}

CARDS_START_X = 20
CARDS_GAP_X = 15
CARDS_ROW_OVERLAP = 28
CARDS_PER_ROW = 4




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


def get_random_room_id():
    x = random.randint(0, GRID_W - 1)
    y = random.randint(0, GRID_H - 1)
    return room_id(x, y)



# =========================
# UI / LAYOUT (IMPORTANT)
# =========================
SIDEBAR_W = 450            # LEFT UI ONLY
PREVIEW_MARGIN = ROOM_DRAW // 2     # space for half rooms

SCREEN_WIDTH  = SIDEBAR_W + ROOM_DRAW + PREVIEW_MARGIN * 2
SCREEN_HEIGHT = ROOM_DRAW + PREVIEW_MARGIN * 2
MENU_CONFIRM_YES_RECT = pygame.Rect(0, 0, 0, 0)
MENU_CONFIRM_NO_RECT  = pygame.Rect(0, 0, 0, 0)


# =========================
# STORE UI CONSTANTS
# =========================


CARD_TYPES = ["Jungle", "Desert", "Ice", "Volcanic", "Arcane"]
CARD_MIN_POWER = 1
CARD_MAX_POWER = 9
MAX_CARDS = 10

selected_card_indices = set()
gate_message = ""
gate_message_timer = 0


# Gate cards are now stored per room per direction
# Format: gate_cards[room_id][direction] = {"power": X, "rewards": [...]}
gate_cards = {}


def get_or_create_gate_card(room_id, direction):
    """Get existing gate card or create a new one for this specific room+direction"""
    if room_id not in gate_cards:
        gate_cards[room_id] = {}
    
    if direction not in gate_cards[room_id]:
        # Create new gate card for this specific gate
        power = random.randint(CARD_MIN_POWER, CARD_MAX_POWER)
        rewards = []
        for _ in range(2):
            r = create_random_card()
            r["power"] = power
            rewards.append(r)
        
        gate_cards[room_id][direction] = {
            "power": power,
            "rewards": rewards
        }
    
    return gate_cards[room_id][direction]






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


selected_reward_index = None


howto_scroll = 0  # global

def wrap_text(text, font, max_w):
    """Returns a list of wrapped lines."""
    lines_out = []
    for raw in text.splitlines():
        raw = raw.rstrip()
        if raw == "":
            lines_out.append("")
            continue

        words = raw.split(" ")
        cur = ""
        for w in words:
            test = w if cur == "" else (cur + " " + w)
            if font.size(test)[0] <= max_w:
                cur = test
            else:
                lines_out.append(cur)
                cur = w
        if cur != "":
            lines_out.append(cur)
    return lines_out
def draw_howto_screen():
    global howto_scroll
    screen.blit(menu_bg, (0, 0))
    # --- dark overlay for readability ---
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))  # alpha: 120–180 is ideal
    screen.blit(overlay, (0, 0))
    
    # Background only

    # ===== TITLE =====
    title = retro_font.render("HOW TO PLAY", True, (255, 255, 255))
    screen.blit(
        title,
        (SCREEN_WIDTH // 2 - title.get_width() // 2, 30)
    )

    # ===== CONTENT AREA (FULL SCREEN) =====
    top_margin = 90
    bottom_margin = 60
    side_margin = 80

    content_x = side_margin
    content_y = top_margin
    content_w = SCREEN_WIDTH - side_margin * 2
    content_h = SCREEN_HEIGHT - top_margin - bottom_margin

    # Columns
    col_gap = 60
    col_w = (content_w - col_gap) // 2

    left_x = content_x
    right_x = content_x + col_w + col_gap

    # ===== TEXT =====
    lines = wrap_text(HOWTO_TEXT, retro_small, col_w)
    line_h = retro_small.get_height() + 6

    # split evenly into columns
    half = (len(lines) + 1) // 2
    left_lines = lines[:half]
    right_lines = lines[half:]

    content_total_h = max(len(left_lines), len(right_lines)) * line_h
    max_scroll = max(0, content_total_h - content_h)
    howto_scroll = max(0, min(howto_scroll, max_scroll))

    clip = pygame.Rect(content_x, content_y, content_w, content_h)
    old_clip = screen.get_clip()
    screen.set_clip(clip)

    # LEFT COLUMN
    y = content_y - howto_scroll
    for ln in left_lines:
        screen.blit(render_howto_line(ln), (left_x, y))
        y += line_h

    # RIGHT COLUMN
    y = content_y - howto_scroll
    for ln in right_lines:
        screen.blit(render_howto_line(ln), (right_x, y))
        y += line_h

    screen.set_clip(old_clip)

    # ===== FOOTER =====
    hint = retro_small.render(
        "ESC - Back   |   Mouse Wheel / ↑ ↓ to Scroll",
        True, (180, 180, 180)
    )
    screen.blit(
        hint,
        (SCREEN_WIDTH // 2 - hint.get_width() // 2,
         SCREEN_HEIGHT - 30)
    )


# =========================
# INIT
# =========================
pygame.init()
pygame.mixer.init(
    frequency=44100,
    size=-16,
    channels=2,
    buffer=512
)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
idle_sheet = pygame.image.load("assets/player_idle.png").convert_alpha()
walk_sheet = pygame.image.load("assets/player_walk.png").convert_alpha()


menu_confirm_bg = pygame.image.load("assets/buttons/Asset 6.png").convert_alpha()
menu_confirm_bg = pygame.transform.smoothscale(menu_confirm_bg, (400, 200))


pygame.display.set_caption("Tower Puzzle — Rooms (10x10)")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 36)
map_font = pygame.font.SysFont(None, 14)
retro_font = pygame.font.Font("assets/retro.ttf", 26)
retro_small = pygame.font.Font("assets/retro.ttf", 16)
retro_power = pygame.font.Font("assets/retro.ttf", 48)  # ← change 48
menu_font = pygame.font.Font("assets/retro.ttf", 26)
# =========================
# AUDIO
# =========================

# --- Music ---
MUSIC_MENU = "assets/audio/music/menu.mp3"
MUSIC_GAME = "assets/audio/music/gameplay.mp3"
MUSIC_WIN  = "assets/audio/music/victory.mp3"

# --- Sound Effects ---
SFX_CLICK       = pygame.mixer.Sound("assets/audio/sfx/click.wav")
SFX_GATE_OPEN   = pygame.mixer.Sound("assets/audio/sfx/gate_open.mp3")
SFX_CARD_SELECT = pygame.mixer.Sound("assets/audio/sfx/card_select.mp3")
SFX_SWAP        = pygame.mixer.Sound("assets/audio/sfx/swap.mp3")
SFX_FOOTSTEP    = pygame.mixer.Sound("assets/audio/sfx/footstep.mp3")

# Volumes
pygame.mixer.music.set_volume(0.4)
for s in [SFX_CLICK, SFX_GATE_OPEN, SFX_CARD_SELECT, SFX_SWAP, SFX_FOOTSTEP]:
    s.set_volume(0.6)

def play_music(track, loop=True):
    pygame.mixer.music.stop()
    pygame.mixer.music.load(track)
    pygame.mixer.music.play(-1 if loop else 0)

def stop_music():
    pygame.mixer.music.stop()

# =========================
# MENU ASSETS
# =========================
menu_bg = pygame.image.load("assets/bg.png").convert()
menu_bg = pygame.transform.smoothscale(menu_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

logo_img = pygame.image.load("assets/logo.png").convert_alpha()

# optional scale
LOGO_W = 520
LOGO_H = int(logo_img.get_height() * (LOGO_W / logo_img.get_width()))
logo_img = pygame.transform.smoothscale(logo_img, (LOGO_W, LOGO_H))


btn_1= pygame.image.load("assets/buttons/Asset 5.png").convert_alpha()
# btn_start_hover = pygame.image.load("assets/btn_start_hover.png").convert_alpha()

btn_2= pygame.image.load("assets/buttons/Asset 2.png").convert_alpha()
# btn_howto_hover = pygame.image.load("assets/btn_howto_hover.png").convert_alpha()

btn_3= pygame.image.load("assets/buttons/Asset 4.png").convert_alpha()
# btn_quit_hover = pygame.image.load("assets/btn_quit_hover.png").convert_alpha()

msg_bg = pygame.image.load("assets/buttons/Asset 6.png").convert_alpha()
msg_bg = pygame.transform.smoothscale(msg_bg, (420, 90))

cursor_img = pygame.image.load("assets/buttons/mouse.png").convert_alpha()
pygame.mouse.set_visible(False)

hud_bg = pygame.image.load("assets/buttons/Asset 7.png").convert_alpha()
HUD_W = 280
HUD_H = 140
hud_bg = pygame.transform.smoothscale(hud_bg, (HUD_W, HUD_H))
HUD_FONT_BIG = pygame.font.Font("assets/retro.ttf", 28)   # POINTS
HUD_FONT_NORMAL = pygame.font.Font("assets/retro.ttf", 22)


sidebar_bg = pygame.image.load("assets/leftbg.png").convert_alpha()
sidebar_bg = pygame.transform.smoothscale(
    sidebar_bg,
    (SIDEBAR_W, SCREEN_HEIGHT)
)
bg_world = pygame.image.load("assets/rightbg.png").convert()
bg_world = pygame.transform.smoothscale(
    bg_world,
    (ROOM_DRAW + PREVIEW_MARGIN * 2,
     ROOM_DRAW + PREVIEW_MARGIN * 2)
)
STORE_BASE_Y = SCREEN_HEIGHT - 140
STORE_BTN_RECT = pygame.Rect(20, STORE_BASE_Y + 65,btn_1.get_width(),btn_1.get_height())

world_border_img = pygame.image.load("assets/buttons/border.png").convert_alpha()
world_border_img = pygame.transform.smoothscale(
    world_border_img,
    (ROOM_DRAW + PREVIEW_MARGIN * 2, ROOM_DRAW + PREVIEW_MARGIN * 2)
)

minimap_bg = pygame.image.load("assets/minimap.png").convert_alpha()
MINIMAP_SIZE = 160
minimap_bg = pygame.transform.smoothscale(
    minimap_bg,
    (MINIMAP_SIZE, MINIMAP_SIZE)
)



MENU_BTN_W = 260
MENU_BTN_H = 70

SIDEBAR_HUD_W = 300
SIDEBAR_HUD_H = 140

LOGO_TOP_Y = -40
LOGO_GAP = -40


hud_bg_sidebar = pygame.transform.smoothscale(
    hud_bg,
    (SIDEBAR_HUD_W, SIDEBAR_HUD_H)
)


menu_buttons = {
    "start": pygame.Rect(SCREEN_WIDTH//2 - 130, 280, MENU_BTN_W, MENU_BTN_H),
    "howto": pygame.Rect(SCREEN_WIDTH//2 - 130, 370, MENU_BTN_W, MENU_BTN_H),
    "quit":  pygame.Rect(SCREEN_WIDTH//2 - 130, 460, MENU_BTN_W, MENU_BTN_H),
}



player_dir = "bottom"   # default facing
player_frame = 0
anim_timer = 0
moving = False

btn_w, btn_h = btn_1.get_size()

menu_buttons = {
    "start": pygame.Rect(SCREEN_WIDTH//2 - btn_w//2, 280, btn_w, btn_h),
    "howto": pygame.Rect(SCREEN_WIDTH//2 - btn_w//2, 370, btn_w, btn_h),
    "quit":  pygame.Rect(SCREEN_WIDTH//2 - btn_w//2, 460, btn_w, btn_h),
}


def get_visual_rect(img):
    mask = pygame.mask.from_surface(img)
    return mask.get_bounding_rects()[0]

def draw_button(img, rect, text, font, text_color=(255,255,255)):
    img_x = rect.centerx - img.get_width() // 2
    img_y = rect.centery - img.get_height() // 2
    screen.blit(img, (img_x, img_y))


    shadow = font.render(text, True, (0,0,0))
    main   = font.render(text, True, text_color)

    screen.blit(shadow, (rect.centerx - shadow.get_width()//2 + 2,
                          rect.centery - shadow.get_height()//2 + 2))
    screen.blit(main,   (rect.centerx - main.get_width()//2,
                          rect.centery - main.get_height()//2))


def get_player_frame(direction, frame, moving):
    row = DIR_ROW[direction]
    sheet = walk_sheet if moving else idle_sheet

    x = frame * FRAME_SIZE
    y = row * FRAME_SIZE

    return sheet.subsurface((x, y, FRAME_SIZE, FRAME_SIZE))


show_store_popup = False

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
store_popup_img = pygame.image.load("assets/buttons/menubg.png").convert_alpha()
store_popup_img = pygame.transform.smoothscale(store_popup_img, (420, 420))

btn_easy   = pygame.image.load("assets/buttons/Asset 5.png").convert_alpha()
btn_medium = pygame.image.load("assets/buttons/Asset 5.png").convert_alpha()
btn_hard   = pygame.image.load("assets/buttons/Asset 5.png").convert_alpha()

# optional hover versions (if you want)
btn_easy_h   = btn_3
btn_medium_h = btn_3
btn_hard_h   = btn_3
DIFF_BTN_TEXT_OFFSET_X = -14
 
def draw_difficulty_button(img, rect, title, desc):
    visual = pygame.mask.from_surface(img).get_bounding_rects()[0]

    draw_x = rect.centerx - (visual.x + visual.width // 2)
    draw_y = rect.centery - (visual.y + visual.height // 2)

    screen.blit(img, (draw_x, draw_y))


    title_main = menu_font.render(title, True, (255,255,255))
    title_outline = menu_font.render(title, True, (0,0,0))
    desc_txt = retro_small.render(desc, True, (235,235,235))

    spacing = 6
    block_h = title_main.get_height() + spacing + desc_txt.get_height()
    start_y = rect.centery - block_h // 2

    # 🔥 OPTICAL CENTER FIX HERE
    cx = rect.centerx + DIFF_BTN_TEXT_OFFSET_X

    # TITLE
    tx = cx - title_main.get_width() // 2
    ty = start_y
    for ox, oy in [(-2,0),(2,0),(0,-2),(0,2)]:
        screen.blit(title_outline, (tx+ox, ty+oy))
    screen.blit(title_main, (tx, ty))

    # DESCRIPTION
    dx = cx - desc_txt.get_width() // 2
    dy = ty + title_main.get_height() + spacing
    screen.blit(desc_txt, (dx, dy))


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

HUD_X = GAME_BOX_RECT.centerx - HUD_W // 2
HUD_Y = GAME_BOX_RECT.top - HUD_H - 16   # slight gap above room



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

CARDS_TITLE_Y = 10
CARDS_TITLE_H = int(btn_1.get_height() * 0.50) + 6

show_gate_popup = False
SIDEBAR_HUD_Y = 20
SIDEBAR_HUD_H = HUD_H
CARDS_TOP_PADDING = 20

HUD_FONT_SIZE = 22
hud_font = pygame.font.Font("assets/retro.ttf", HUD_FONT_SIZE)


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

close_btn_img = pygame.image.load("assets/buttons/Asset 10.png").convert_alpha()
close_btn_img = pygame.transform.smoothscale(close_btn_img, (32, 32))
STORE_CLOSE_BTN_RECT = pygame.Rect(0, 0, 32, 32)

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
    SFX_SWAP.play()

    gate_message = f"TRADE SUCCESS! POWER {new_power}"
    gate_message_timer = 90
    return True


create_world()
def print_world_grid():
    print("\n=== WORLD GRID (row, col → room_id) ===")
    for y in range(GRID_H):
        row = []
        for x in range(GRID_W):
            rid = room_id(x, y)
            row.append(f"{rid:02d}")
        print(f"Row {y}: " + "  ".join(row))
    print("=====================================\n")

print_world_grid()

current = get_random_room_id()
visited_rooms.add(current)
explored_rooms.add(current)

START_ROOM = current 
# =========================
# PLAYER
# =========================
player = pygame.Rect(0, 0, 16, 16)
player.center = SPAWN


finish_room = get_random_room_id()
while abs(rooms[finish_room]["pos"][0] - rooms[current]["pos"][0]) < 4:
    finish_room = get_random_room_id()

# =========================
# CARDS
# =========================

popup_w = 420
popup_h = 300
popup_x = SCREEN_WIDTH // 2 - popup_w // 2
popup_y = SCREEN_HEIGHT // 2 - popup_h // 2

# =========================
# MOVEMENT
# =========================
def move(dx, dy):
    global footstep_timer
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
    gate_card = get_or_create_gate_card(current, d)
    required_power = gate_card["power"]

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

    reward = gate_card["rewards"][selected_reward_index]
    cards.append(reward)
    selected_reward_index = None


    cur = current
    nxt = rooms[current]["links"][d]

    # open gate both sides
    rooms[cur]["open_gates"][d] = True
    SFX_GATE_OPEN.play()

    opposite = {"top":"bottom", "bottom":"top", "left":"right", "right":"left"}
    rooms[nxt]["open_gates"][opposite[d]] = True

    change_room(d)
    
    
    global last_printed_room

    if current != last_printed_room:
        print(f"[ROOM CHANGE]")
        print(f"START ROOM : {START_ROOM}")
        print(f"END ROOM   : {finish_room}")
        print(f"CURRENT    : {current}")
        print("-" * 30)
        last_printed_room = current
    check_finish()
    gate_message = "GATE OPENED!"
    gate_message_timer = 90
    selected_reward_index = None
    return True
def draw_button_with_text(img, rect, text):
    # draw image
    screen.blit(img, rect.topleft)

    text_main = menu_font.render(text, True, (255, 255, 255))
    text_outline = menu_font.render(text, True, (0, 0, 0))

    tx = rect.x + (rect.width  - text_main.get_width())  // 2
    ty = rect.y + (rect.height - text_main.get_height()) // 2 - 3  # small lift

    for ox, oy in [(-2,0),(2,0),(0,-2),(0,2)]:
        screen.blit(text_outline, (tx+ox, ty+oy))

    screen.blit(text_main, (tx, ty))


def draw_points():
    txt = retro_font.render(f"POINTS: {points}", True, (255, 255, 255))
    screen.blit(txt, (SIDEBAR_W + 20, 10))

def draw_start_end_rooms():
    y_base = 40  # below POINTS

    start_txt = retro_small.render(
        f"START ROOM: #{START_ROOM}", True, (180, 180, 180)
    )
    end_txt = retro_small.render(
        f"END ROOM: #{finish_room}", True, (255, 120, 120)
    )

    screen.blit(start_txt, (SIDEBAR_W + 20, y_base))
    screen.blit(end_txt, (SIDEBAR_W + 20, y_base + 20))


TRADE_BTN_RECT = pygame.Rect(0, 0, btn_1.get_width(), btn_1.get_height())
STORE_TRADE_BTN_RECT = pygame.Rect(0, 0, btn_1.get_width(), btn_1.get_height())
BACK_TO_MENU_BTN_RECT = pygame.Rect(0, 0, 50, 50)
STORE_CARD_RECTS = []
STORE_TYPE_RECTS = []

def get_gate_card_positions(popup_x, popup_y):
    cx = popup_x + 420 // 2
    cards_y = popup_y + 120

    gap_inner = 16
    gap_group = 40

    total_width = CARD_WIDTH * 3 + gap_group + gap_inner
    group_left = cx - total_width // 2

    give_x    = group_left
    reward_x1 = give_x + CARD_WIDTH + gap_group
    reward_x2 = reward_x1 + CARD_WIDTH + gap_inner

    return give_x, reward_x1, reward_x2, cards_y

def handle_events(cards_start_y):
    global pressed_e
    global selected_card_indices
    global selected_reward_index
    global store_selected_indices
    global store_target_type
    global show_store_popup
    global show_gate_popup
    global show_menu_confirmation
    global game_state

    pressed_e = False

    start_x = CARDS_START_X
    gap_x   = CARDS_GAP_X
    gap_y   = CARD_HEIGHT - CARDS_ROW_OVERLAP
    cards_per_row = CARDS_PER_ROW

    for e in pygame.event.get():

        # ===============================
        # QUIT
        # ===============================
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # ===============================
        # KEYBOARD
        # ===============================
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_e:
                pressed_e = True

            if e.key == pygame.K_ESCAPE:
                # Close menu confirmation if open
                if show_menu_confirmation:
                    show_menu_confirmation = False
                    return
                # Otherwise close popups
                show_store_popup = False
                show_gate_popup = False
                selected_reward_index = None
                return

        # ===============================
        # MOUSE EVENTS ONLY
        # ===============================
        if e.type != pygame.MOUSEBUTTONDOWN:
            continue

        mx, my = e.pos
        # ===============================
        # MENU CONFIRMATION DIALOG (HIGHEST PRIORITY)
        # ===============================
        if show_menu_confirmation:
            if MENU_CONFIRM_YES_RECT.collidepoint(mx, my):
                game_state = STATE_MENU
                show_menu_confirmation = False
                return
        
            if MENU_CONFIRM_NO_RECT.collidepoint(mx, my):
                show_menu_confirmation = False
                return
        
            return
        

        # ===============================
        # BACK TO MENU BUTTON (if no popups)
        # ===============================
        if not show_store_popup and not show_gate_popup:
            if BACK_TO_MENU_BTN_RECT.collidepoint(mx, my):
                show_menu_confirmation = True
                return

        # ===============================
        # TRADE BUTTON (LEFT SIDEBAR)
        # ===============================
        if e.button == 1 and TRADE_BTN_RECT.collidepoint(mx, my):
            show_store_popup = True
            show_gate_popup = False
            return

        # ==================================================
        # GATE SWAP POPUP
        # ==================================================
        if show_gate_popup:
            popup_x = SCREEN_WIDTH // 2 - 420 // 2 + 120
            popup_y = SCREEN_HEIGHT // 2 - 420 // 2

            # ---- SWAP BUTTON ----
            if STORE_TRADE_BTN_RECT.collidepoint(mx, my):
                d = can_interact_gate()
                if d and selected_reward_index is not None:
                    if try_swap_with_gate(d, selected_card_indices):
                        selected_card_indices.clear()
                        show_gate_popup = False
                return

            # ---- REWARD SELECTION ----
            popup_rect = pygame.Rect(popup_x, popup_y, 420, 420)
            if popup_rect.collidepoint(mx, my):
                d = can_interact_gate()
                if d:
                    gate_card = get_or_create_gate_card(current, d)
                    rewards = gate_card["rewards"]

                    # 🔥 SINGLE SOURCE OF TRUTH
                    give_x, reward_x1, reward_x2, cards_y = get_gate_card_positions(
                        popup_x, popup_y
                    )

                    reward_positions = [reward_x1, reward_x2]

                    for i, rx in enumerate(reward_positions):
                        if pygame.Rect(rx, cards_y, CARD_WIDTH, CARD_HEIGHT).collidepoint(mx, my):
                            selected_reward_index = i
                            SFX_CARD_SELECT.play()
                            return
                return

        # ==================================================
        # STORE POPUP
        # ==================================================
        if show_store_popup:
            popup_w = 420
            popup_h = 520
            popup_x = SCREEN_WIDTH // 2 - popup_w // 2
            popup_y = SCREEN_HEIGHT // 2 - popup_h // 2

            STORE_CLOSE_BTN_RECT.topleft = (
                popup_x + popup_w - 36,
                popup_y + 12
            )

            if STORE_CLOSE_BTN_RECT.collidepoint(mx, my):
                show_store_popup = False
                store_selected_indices.clear()
                store_target_type = None
                return

            if e.button in (1, 3):
                for i, rect in STORE_CARD_RECTS:
                    if rect.collidepoint(mx, my):
                        if i in store_selected_indices:
                            store_selected_indices.remove(i)
                        elif len(store_selected_indices) < 2:
                            store_selected_indices.add(i)
                            SFX_CARD_SELECT.play()
                        return

            if e.button == 1:
                for t, rect in STORE_TYPE_RECTS:
                    if rect.collidepoint(mx, my):
                        store_target_type = t
                        return

                if STORE_TRADE_BTN_RECT.collidepoint(mx, my):
                    try_store_swap()
                    return

            return

        # ==================================================
        # LEFT SIDEBAR CARD SELECTION
        # ==================================================
        if e.button == 1:
            for i, c in enumerate(cards):
                row = i // cards_per_row
                col = i % cards_per_row

                x = start_x + col * (CARD_WIDTH + gap_x)
                y = cards_start_y + row * gap_y

                if pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT).collidepoint(mx, my):
                    if i in selected_card_indices:
                        selected_card_indices.remove(i)
                    else:
                        selected_card_indices.add(i)
                        SFX_CARD_SELECT.play()
                    return

howto_scroll = 0  # global


def wrap_text(text, font, max_w):
    lines_out = []
    for raw in text.splitlines():
        raw = raw.rstrip()
        if raw == "":
            lines_out.append("")
            continue

        words = raw.split(" ")
        cur = ""
        for w in words:
            test = w if cur == "" else cur + " " + w
            if font.size(test)[0] <= max_w:
                cur = test
            else:
                lines_out.append(cur)
                cur = w
        if cur:
            lines_out.append(cur)
    return lines_out


def render_howto_line(line):
    if line.startswith(tuple(str(i) + "." for i in range(1, 20))):
        return retro_small.render(line, True, (255, 220, 120))
    elif line.strip().isupper() and len(line.strip()) > 4:
        return retro_small.render(line, True, (220, 220, 220))
    elif line.startswith("-"):
        return retro_small.render(line, True, (210, 210, 210))
    else:
        return retro_small.render(line, True, (190, 190, 190))


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

def draw_back_to_menu_button():
    """Draw back-to-menu button using CLOSE icon as background"""
    # Top-right corner
    BACK_TO_MENU_BTN_RECT.size = close_btn_img.get_size()
    BACK_TO_MENU_BTN_RECT.x = SCREEN_WIDTH - BACK_TO_MENU_BTN_RECT.width - 20
    BACK_TO_MENU_BTN_RECT.y = 20

    mx, my = pygame.mouse.get_pos()
    hover = BACK_TO_MENU_BTN_RECT.collidepoint(mx, my)

    # Slight hover glow
    if hover:
        glow = pygame.Surface(
            (BACK_TO_MENU_BTN_RECT.width + 6, BACK_TO_MENU_BTN_RECT.height + 6),
            pygame.SRCALPHA
        )
        glow.fill((255, 255, 255, 40))
        screen.blit(glow, (BACK_TO_MENU_BTN_RECT.x - 3, BACK_TO_MENU_BTN_RECT.y - 3))

    # Draw close button image
    screen.blit(close_btn_img, BACK_TO_MENU_BTN_RECT.topleft)
def draw_menu_confirmation_dialog():
    global MENU_CONFIRM_YES_RECT, MENU_CONFIRM_NO_RECT

    # ---- overlay ----
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    # ---- dialog ----
    dialog_w, dialog_h = menu_confirm_bg.get_size()
    dialog_x = SCREEN_WIDTH // 2 - dialog_w // 2
    dialog_y = SCREEN_HEIGHT // 2 - dialog_h // 2

    screen.blit(menu_confirm_bg, (dialog_x, dialog_y))

    # ---- text ----
    title = retro_font.render("RETURN TO MENU?", True, (255, 200, 80))
    warning = retro_small.render("Progress will be lost!", True, (100, 100, 100))

    screen.blit(title, (dialog_x + dialog_w//2 - title.get_width()//2, dialog_y + 60))
    screen.blit(warning, (dialog_x + dialog_w//2 - warning.get_width()//2, dialog_y + 86))

    # ---- buttons (OPTICAL CENTER) ----
    # NEW (match rect to image size)
    button_w, button_h = btn_1.get_size()

    button_gap = 30
    button_y = dialog_y + dialog_h - 62

    center_x = dialog_x + dialog_w // 2

    MENU_CONFIRM_YES_RECT = pygame.Rect(
        center_x - button_gap//2 - button_w,
        button_y,
        button_w,
        button_h
    )

    MENU_CONFIRM_NO_RECT = pygame.Rect(
        center_x + button_gap//2,
        button_y,
        button_w,
        button_h
    )

    # ---- draw buttons ----
    mx, my = pygame.mouse.get_pos()
    draw_image_button(MENU_CONFIRM_YES_RECT, "YES",
                      MENU_CONFIRM_YES_RECT.collidepoint(mx, my))
    draw_image_button(MENU_CONFIRM_NO_RECT, "NO",
                      MENU_CONFIRM_NO_RECT.collidepoint(mx, my))


def can_use_card_for_gate(card, d):
    if d is None:
        return False

    required_type = get_next_room_type(d)
    gate_card = get_or_create_gate_card(current, d)
    required_power = gate_card["power"]

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
def draw_banner_title(text, center_x, y, scale=1):
    bw, bh = btn_1.get_size()

    sw = int(bw * scale)
    sh = int(bh * scale)

    banner = pygame.transform.smoothscale(btn_1, (sw, sh))
    x = center_x - sw // 2

    screen.blit(banner, (x, y))

    text_main = menu_font.render(text, True, (255, 255, 255))
    text_outline = menu_font.render(text, True, (0, 0, 0))

    tx = center_x - text_main.get_width() // 2
    ty = y + sh // 2 - text_main.get_height() // 2 - 2

    for ox, oy in [(-2,0),(2,0),(0,-2),(0,2)]:
        screen.blit(text_outline, (tx + ox, ty + oy))

    screen.blit(text_main, (tx, ty))
    return sh


def draw_cards_title():
    center_x = SIDEBAR_W // 2
    y = SIDEBAR_HUD_Y + SIDEBAR_HUD_H + 12

    banner_h = draw_banner_title("CURRENT CARDS", center_x, y)
    return y + banner_h

def draw_cards(start_y):

    start_x = CARDS_START_X
    gap_x = CARDS_GAP_X
    gap_y = CARD_HEIGHT - CARDS_ROW_OVERLAP
    cards_per_row = CARDS_PER_ROW


    for i, c in enumerate(cards):
        key = CARD_IMAGE_KEY[c["type"]]

        row = i // cards_per_row
        col = i % cards_per_row

        x = start_x + col * (CARD_WIDTH + gap_x)
        y = start_y + row * gap_y
        if row > 0:
            shadow = pygame.Surface((CARD_WIDTH, 20), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 60))
            screen.blit(shadow, (x, y))

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
                border_radius=0
            )

        # pygame.draw.rect(
        #     screen,
        #     (220, 220, 220),
        #     (x, y, CARD_WIDTH, CARD_HEIGHT),
        #     2,
        #     border_radius=0
        # )
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


# CARDS_START_Y = draw_cards_title() + 12

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
    # pygame.draw.rect(
    #     screen,
    #     (220, 220, 220),
    #     (x, y, CARD_WIDTH, CARD_HEIGHT),
    #     2,
    #     border_radius=8
    # )

    draw_card_power(x, y, card["power"])

def draw_gate_message():
    if gate_message_timer <= 0 or not gate_message:
        return

    bg_w, bg_h = msg_bg.get_size()

    # Position: bottom-center of room area
    cx = ROOM_RECT.centerx
    y  = ROOM_RECT.bottom + 20

    bg_x = cx - bg_w // 2
    bg_y = y

    # Draw background
    screen.blit(msg_bg, (bg_x, bg_y))

    # Draw text
    txt = retro_font.render(gate_message, True, (255, 220, 120))
    screen.blit(
        txt,
        (
            cx - txt.get_width() // 2,
            bg_y + bg_h // 2 - txt.get_height() // 2
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
def draw_store_ui(base_x, base_y):
    popup_w = 420
    center_x = base_x + popup_w // 2

    # ---- TITLE ----
    title_h = draw_banner_title("STORE", center_x, base_y + 20)

    # ---- USES LEFT ----
    uses = retro_small.render(f"USES LEFT: {store_uses_left}", True, (200,200,200))
    screen.blit(uses, (center_x - uses.get_width()//2, base_y + 20 + title_h + 10))

    # ---- YOUR CARDS ----
    # next_y = draw_store_cards(base_x, base_y)

    # ---- RULE TEXT ----
    hint = retro_small.render("GIVE 2 SAME - GET 1", True, (170,170,170))
    screen.blit(hint, (center_x - hint.get_width()//2, next_y + 10))

    # ---- TARGET TYPE ----
    type_y = next_y + 40
    type_gap = 75
    start_x = center_x - (len(CARD_TYPES)*type_gap)//2

    for i, t in enumerate(CARD_TYPES):
        rect = pygame.Rect(start_x + i*type_gap, type_y, 70, 22)

        if t == store_target_type:
            pygame.draw.rect(screen, (255,255,120), rect, 2)
            col = (255,255,120)
        else:
            pygame.draw.rect(screen, (90,90,90), rect, 1)
            col = (170,170,170)

        txt = retro_small.render(t, True, col)
        screen.blit(txt, (rect.centerx - txt.get_width()//2,
                          rect.centery - txt.get_height()//2))

    # ---- TRADE BUTTON ----
    btn_rect = pygame.Rect(
        center_x - btn_1.get_width()//2,
        type_y + 45,
        btn_1.get_width(),
        btn_1.get_height()
    )

    mx, my = pygame.mouse.get_pos()
    hover = btn_rect.collidepoint(mx, my)
    draw_image_button(btn_rect, "TRADE", hover)

    return btn_rect


def draw_trade_button_center(cards_end_y):
    # CENTER INSIDE LEFT SIDEBAR
    TRADE_BTN_RECT.x = SIDEBAR_W // 2 - btn_1.get_width() // 2
    TRADE_BTN_RECT.y = cards_end_y + 40

    mx, my = pygame.mouse.get_pos()
    hover = TRADE_BTN_RECT.collidepoint(mx, my)

    draw_image_button(TRADE_BTN_RECT, "TRADE", hover)
    return TRADE_BTN_RECT


def draw_image_button(rect, text, hover=False):
    img = btn_3 if hover else btn_1
    draw_button_with_text(img, rect, text)

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


def draw_cursor():
    mx, my = pygame.mouse.get_pos()
    screen.blit(
        cursor_img,
        (mx - cursor_img.get_width() // 2,
         my - cursor_img.get_height() // 2)
    )
    


def get_next_room_type(d):
    nxt = rooms[current]["links"].get(d)
    if nxt is None:
        return None
    return rooms[nxt]["type"]
def draw_minimap():
    panel_size = MINIMAP_SIZE
    panel_x = SCREEN_WIDTH - panel_size - 30
    panel_y = SCREEN_HEIGHT - panel_size - 30
    screen.blit(minimap_bg, (panel_x, panel_y))
    center = (
        panel_x + panel_size // 2,
        panel_y + panel_size // 2
    )
    radius_px = panel_size // 2 - 2

    node = 14
    gap = 4
    step = node + gap
    radius = difficulty_settings[current_difficulty]["minimap_radius"]

    # background circle
    # pygame.draw.circle(screen, (20, 20, 20), center, radius_px)
    # pygame.draw.circle(screen, (180, 180, 180), center, radius_px, 2)

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

            rx = x + node // 2
            ry = y + node // 2

            inside_circle = (rx - center[0])**2 + (ry - center[1])**2 <= radius_px**2

            # ==================================================
            # 1️⃣ ALWAYS draw GOAL OUTLINE (even outside circle)
            # ==================================================
            if rid == finish_room:
                pygame.draw.rect(
                    screen,
                    (255, 80, 80),
                    (x - 2, y - 2, node + 4, node + 4),
                    2,
                    border_radius=3
                )

            # ==================================================
            # 2️⃣ Draw filled cells ONLY if inside circle
            # ==================================================
            if not inside_circle:
                continue

            # decide fill color
            if rid == current:
                color = (255, 255, 255)
            elif rid == finish_room:
                color = (255, 80, 80)
            elif rid in visited_rooms:
                color = (245, 245, 245)
            elif rid in explored_rooms:
                color = ROOM_COLORS[rooms[rid]["type"]]
            else:
                continue  # unknown stays hidden

            pygame.draw.rect(screen, color, (x, y, node, node))

            # ==================================================
            # 3️⃣ CURRENT ROOM GLOW
            # ==================================================
            if rid == current:
                pygame.draw.rect(
                    screen,
                    (255, 255, 120),
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
    
    
def draw_main_menu():
    screen.blit(menu_bg, (0, 0))
    mx, my = pygame.mouse.get_pos()

    # ---- LOGO ----
    logo_x = SCREEN_WIDTH // 2 - logo_img.get_width() // 2
    logo_y = LOGO_TOP_Y
    screen.blit(logo_img, (logo_x, logo_y))

    # ---- BUTTON START Y (BASED ON LOGO HEIGHT) ----
    buttons_start_y = logo_y + logo_img.get_height() + LOGO_GAP
    btn_gap = 75

    menu_buttons["start"].y = buttons_start_y
    menu_buttons["howto"].y = buttons_start_y + btn_gap
    menu_buttons["quit"].y  = buttons_start_y + btn_gap * 2

    # ---- DRAW BUTTONS ----
    img = btn_3 if menu_buttons["start"].collidepoint(mx, my) else btn_1
    draw_button_with_text(img, menu_buttons["start"], "START GAME")

    img = btn_3 if menu_buttons["howto"].collidepoint(mx, my) else btn_1
    draw_button_with_text(img, menu_buttons["howto"], "HOW TO PLAY")

    img = btn_3 if menu_buttons["quit"].collidepoint(mx, my) else btn_1
    draw_button_with_text(img, menu_buttons["quit"], "QUIT")


    
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
    
    
def draw_howto():
    screen.fill((0, 0, 0))

    title = retro_font.render("HOW TO PLAY", True, (255, 255, 255))
    screen.blit(title, (80, 60))

    lines = [
        "• Move using WASD or Arrow keys",
        "• Reach gates to unlock rooms",
        "• Give cards of SAME TYPE",
        "• Total power must meet gate requirement",
        "• Choose ONE reward card",
        "• Use STORE to merge cards",
        "• Reach the RED goal room to win",
        "",
        "Press ESC to go back"
    ]

    y = 140
    for line in lines:
        txt = retro_small.render(line, True, (200, 200, 200))
        screen.blit(txt, (80, y))
        y += 28
        
def draw_hud_line(text, cx, y, font, color=(255,255,255)):
    outline = font.render(text, True, (0,0,0))
    main    = font.render(text, True, color)

    x = cx - main.get_width() // 2

    for ox, oy in [(-1,0),(1,0),(0,-1),(0,1)]:
        screen.blit(outline, (x + ox, y + oy))

    screen.blit(main, (x, y))

def draw_game_hud():
    cx = HUD_X + HUD_W // 2

    # ---- shadow ----
    shadow = pygame.Surface((HUD_W, HUD_H), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 90))
    screen.blit(shadow, (HUD_X + 4, HUD_Y + 4))

    # ---- background ----
    screen.blit(hud_bg, (HUD_X, HUD_Y))

    y0 = HUD_Y + 26
    gap = 26

    # LINE 1 — POINTS (BIGGER)
    draw_hud_line(
        f"POINTS: {points}",
        cx,
        y0,
        HUD_FONT_BIG
    )

    # LINE 2 — START
    draw_hud_line(
        f"START ROOM: #{START_ROOM}",
        cx,
        y0 + gap + 6,
        HUD_FONT_NORMAL
    )

    # LINE 3 — END
    draw_hud_line(
        f"END ROOM: #{finish_room}",
        cx,
        y0 + gap * 2 + 6,
        HUD_FONT_NORMAL,
        (255, 80, 80)
    )

    # LINE 4 — CURRENT ROOM
    draw_hud_line(
        f"{rooms[current]['type'].upper()} CHAMBER  -  #{current}",
        cx,
        y0 + gap * 3 + 6,
        HUD_FONT_NORMAL
    )


def handle_menu_events():
    global game_state

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            SFX_CLICK.play()
            mx, my = e.pos

            if menu_buttons["start"].collidepoint(mx, my):
                game_state = STATE_DIFFICULTY

            elif menu_buttons["howto"].collidepoint(mx, my):
                game_state = STATE_HOWTO

            elif menu_buttons["quit"].collidepoint(mx, my):
                pygame.quit()
                sys.exit()

def handle_howto_events():
    global game_state, howto_scroll

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                game_state = STATE_MENU
            elif e.key == pygame.K_DOWN:
                howto_scroll += 30
            elif e.key == pygame.K_UP:
                howto_scroll -= 30
            elif e.key == pygame.K_PAGEDOWN:
                howto_scroll += 300
            elif e.key == pygame.K_PAGEUP:
                howto_scroll -= 300

        if e.type == pygame.MOUSEWHEEL:
            howto_scroll -= e.y * 40

def handle_difficulty_events():
    global game_state, current_difficulty, MAX_POINTS, POINT_DECAY_PER_SEC, store_uses_left

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            game_state = STATE_MENU
            return

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            SFX_CLICK.play()
            mx, my = e.pos

            # Create button rects
            center_x = SCREEN_WIDTH // 2
            start_y = SCREEN_HEIGHT // 2 - 100
            button_gap = 80
            button_w, button_h = btn_easy.get_size()


            easy_rect = pygame.Rect(center_x - button_w // 2, start_y, button_w, button_h)
            medium_rect = pygame.Rect(center_x - button_w // 2, start_y + button_gap, button_w, button_h)
            hard_rect = pygame.Rect(center_x - button_w // 2, start_y + button_gap * 2, button_w, button_h)

            if easy_rect.collidepoint(mx, my):
                current_difficulty = DIFFICULTY_EASY
                apply_difficulty_settings()
                play_music(MUSIC_GAME)
                reset_game()
                game_state = STATE_GAME

            elif medium_rect.collidepoint(mx, my):
                current_difficulty = DIFFICULTY_MEDIUM
                apply_difficulty_settings()
                play_music(MUSIC_GAME)
                reset_game()
                game_state = STATE_GAME

            elif hard_rect.collidepoint(mx, my):
                current_difficulty = DIFFICULTY_HARD
                apply_difficulty_settings()
                play_music(MUSIC_GAME)
                reset_game()
                game_state = STATE_GAME


def apply_difficulty_settings():
    global MAX_POINTS, POINT_DECAY_PER_SEC, store_uses_left, STORE_MAX_USES
    
    settings = difficulty_settings[current_difficulty]
    MAX_POINTS = settings["max_points"]
    POINT_DECAY_PER_SEC = settings["point_decay"]
    STORE_MAX_USES = settings["store_uses"]
    store_uses_left = STORE_MAX_USES


def draw_difficulty_screen():
    screen.blit(menu_bg, (0, 0))
    
    # Title
    title = retro_font.render("SELECT DIFFICULTY", True, (255, 255, 255))
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))
    
    # Create button rects
    center_x = SCREEN_WIDTH // 2
    start_y = SCREEN_HEIGHT // 2 - 100
    button_gap = 80
    button_w = 300
    button_h = 60
    
    mx, my = pygame.mouse.get_pos()
    
    easy_rect = pygame.Rect(center_x - button_w // 2, start_y, button_w, button_h)
    medium_rect = pygame.Rect(center_x - button_w // 2, start_y + button_gap, button_w, button_h)
    hard_rect = pygame.Rect(center_x - button_w // 2, start_y + button_gap * 2, button_w, button_h)
    
    # Easy
    easy_img = btn_easy_h if easy_rect.collidepoint(mx, my) else btn_easy
    draw_difficulty_button(
        easy_img,
        easy_rect,
        "EASY",
        "Time: 1000 | Trades: 3"
    )

    # Medium
    medium_img = btn_medium_h if medium_rect.collidepoint(mx, my) else btn_medium
    draw_difficulty_button(
        medium_img,
        medium_rect,
        "MEDIUM",
        "Time: 500 | Trades: 2"
    )

    # Hard
    hard_img = btn_hard_h if hard_rect.collidepoint(mx, my) else btn_hard
    draw_difficulty_button(
        hard_img,
        hard_rect,
        "HARD",
        "Time: 300 | Trades: 1"
    )

    
    # Back hint
    hint = retro_small.render("Press ESC to go back", True, (180, 180, 180))
    screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 80))


def handle_howto_events():
    global game_state

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            game_state = STATE_MENU



def reset_game():
    global current, visited_rooms, explored_rooms
    global cards, points, GAME_OVER, GAME_WIN, GAME_ENDED
    global gate_cards

    points = MAX_POINTS
    GAME_OVER = False
    GAME_WIN = False
    GAME_ENDED = False

    visited_rooms.clear()
    explored_rooms.clear()
    gate_cards.clear()  # Clear all gate cards for fresh start

    cards.clear()
    for _ in range(MAX_CARDS):
        c = create_random_card()
        c["power"] = random.randint(6, CARD_MAX_POWER)
        cards.append(c)

    current = get_random_room_id()
    visited_rooms.add(current)
    explored_rooms.add(current)

    player.center = SPAWN


def draw_gate_card_popup():
    d = can_interact_gate()
    if d is None:
        return

    give_type = get_next_room_type(d)
    gate_card = get_or_create_gate_card(current, d)
    power = gate_card["power"]
    rewards = gate_card["rewards"]

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
        ROOM_RECT.centerx - btn_1.get_width() // 2,
        ROOM_RECT.centery + CARD_HEIGHT // 2 + 30,
        btn_1.get_width(),
        btn_1.get_height()
    )

    mx, my = pygame.mouse.get_pos()
    hover = rect.collidepoint(mx, my)

    draw_image_button(rect, "SWAP", hover)
    return rect

def check_finish():
    global GAME_WIN, GAME_ENDED
    if current == finish_room:
        GAME_WIN = True
        GAME_ENDED = True
        play_music(MUSIC_WIN, loop=False)


def draw_sidebar_hud():
    # center HUD inside sidebar
    x = (SIDEBAR_W - SIDEBAR_HUD_W) // 2
    y = 18

    # soft shadow ONLY under parchment
    shadow = pygame.Surface((SIDEBAR_HUD_W, SIDEBAR_HUD_H), pygame.SRCALPHA)
    # shadow.fill((0, 100, 100, 70))
    screen.blit(shadow, (x + 4, y + 4))

    # parchment background
    screen.blit(hud_bg_sidebar, (x, y))

    cx = x + SIDEBAR_HUD_W // 2
    y0 = y + 30
    gap = 30

    # Difficulty level colors
    diff_colors = {
        DIFFICULTY_EASY: (120, 255, 120),
        DIFFICULTY_MEDIUM: (255, 200, 80),
        DIFFICULTY_HARD: (255, 80, 80)
    }
    diff_color = diff_colors.get(current_difficulty, (255, 255, 255))
    
    
    # LINE 0 — DIFFICULTY LEVEL
    draw_hud_line(
        f"LEVEL: {current_difficulty.upper()}", 
        cx, 
        y0+15, 
        HUD_FONT_NORMAL,
        diff_color
    )
    
    # LINE 1 — POINTS (BIGGER)
    draw_hud_line(f"POINTS: {points}", cx, y0 + gap+15, HUD_FONT_BIG, (255, 80, 80))
    
def draw_store_popup():
    global STORE_CARD_RECTS, STORE_TYPE_RECTS

    STORE_CARD_RECTS.clear()
    STORE_TYPE_RECTS.clear()

    popup_w, popup_h = 420, 520



    popup_x = SCREEN_WIDTH//2 - popup_w//2
    popup_y = SCREEN_HEIGHT//2 - popup_h//2
    # preview_y = popup_y + 160   # DEFAULT SAFE VALUE

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0,0,0,140))
    screen.blit(overlay, (0,0))

    screen.blit(store_popup_img, (popup_x, popup_y))


    draw_banner_title("STORE", popup_x + popup_w//2, popup_y + 15)
    y_cursor = popup_y + 80

    # ---- STORE CARD LIST (TEXT ONLY) ----
    list_x = popup_x + PAD_X
    list_y = popup_y + 90


    row_h  = 24

    for i, c in enumerate(cards):
        y = list_y + i * row_h

        rect = pygame.Rect(list_x, y, popup_w - 90, row_h - 4)

        STORE_CARD_RECTS.append((i, rect))

        # background
        if i in store_selected_indices:
            pygame.draw.rect(screen, (80,120,160), rect, border_radius=4)
        else:
            pygame.draw.rect(screen, (40,40,40), rect, border_radius=4)

        pygame.draw.rect(screen, (160,160,160), rect, 1, border_radius=4)

        txt = retro_small.render(
            f"{i+1}. {c['type']}  |  Power: {c['power']}",
            True,
            (255,255,255)
        )
        screen.blit(txt, (rect.x + 8, rect.y + 4))
    
    # ---- TARGET TYPE SELECTION (AFTER CARD LIST) ----
    type_y = list_y + len(cards) * row_h + 15
    type_gap = 75
    start_x = popup_x + popup_w//2 - (len(CARD_TYPES)*type_gap)//2

    for i, t in enumerate(CARD_TYPES):
        rect = pygame.Rect(start_x + i*type_gap, type_y, 70, 24)
        STORE_TYPE_RECTS.append((t, rect))

        if t == store_target_type:
            bg = (80, 120, 160)        # selected bg
            border = (255, 255, 120)
            text_col = (255, 255, 255)
        else:
            bg = (40, 40, 40)          # 🔥 DARK bg (key fix)
            border = (160, 160, 160)
            text_col = (220, 220, 220)

        # background fill (THIS FIXES VISIBILITY)
        pygame.draw.rect(screen, bg, rect, border_radius=6)

        # border
        pygame.draw.rect(screen, border, rect, 2, border_radius=6)

        txt = retro_small.render(t, True, text_col)
        screen.blit(
            txt,
            (rect.centerx - txt.get_width()//2,
             rect.centery - txt.get_height()//2)
        )


    # ---- RESULT PREVIEW ----
    preview_y = type_y + 35


    preview_text = "SELECT 2 SAME TYPE CARDS"
    preview_color = (170,170,170)

    if len(store_selected_indices) == 2:
        i1, i2 = list(store_selected_indices)
        c1, c2 = cards[i1], cards[i2]

        if c1["type"] == c2["type"] and store_target_type:
            new_power = min(c1["power"] + c2["power"], CARD_MAX_POWER)
            preview_text = f"RESULT → {store_target_type} | POWER {new_power}"
            preview_color = (255,255,120)
        elif c1["type"] != c2["type"]:
            preview_text = "CARDS MUST BE SAME TYPE"
            preview_color = (255,120,120)

    txt = retro_small.render(preview_text, True, preview_color)
    screen.blit(txt, (popup_x + popup_w//2 - txt.get_width()//2, preview_y))
    
    # ---- TRADE BUTTON ----
    STORE_TRADE_BTN_RECT.center = (
        popup_x + popup_w//2,
        preview_y + 35
    )
    # ---- CLOSE BUTTON (TOP-RIGHT) ----
    STORE_CLOSE_BTN_RECT.topleft = (
        popup_x + popup_w - 36,
        popup_y + 12
    )

    screen.blit(close_btn_img, STORE_CLOSE_BTN_RECT.topleft)


    draw_image_button(
        STORE_TRADE_BTN_RECT,
        "TRADE",
        STORE_TRADE_BTN_RECT.collidepoint(pygame.mouse.get_pos())
    )
def draw_gate_popup():
    global selected_reward_index

    popup_w, popup_h = 420, 420
    popup_x = SCREEN_WIDTH // 2 - popup_w // 2 + 120
    popup_y = SCREEN_HEIGHT // 2 - popup_h // 2

    # ---- overlay (world side only) ----
    overlay = pygame.Surface(
        (SCREEN_WIDTH - SIDEBAR_W, SCREEN_HEIGHT),
        pygame.SRCALPHA
    )
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (SIDEBAR_W, 0))

    # ---- popup background ----
    screen.blit(store_popup_img, (popup_x, popup_y))

    d = can_interact_gate()
    if d is None:
        return

    give_type = get_next_room_type(d)
    # give_type = get_next_room_type(d)
    if give_type is None:
        return   # 🔥 DO NOT DRAW POPUP

    gate_card = get_or_create_gate_card(current, d)
    need_power = gate_card["power"]
    rewards = gate_card["rewards"]

    cx = popup_x + popup_w // 2
    cards_y = popup_y + 120   # unified baseline

    # ==================================================
    # TITLE
    # ==================================================
    draw_banner_title("GATE TRADE", cx, popup_y + 18)

    # ==================================================
    # CARD POSITIONS (INTENTIONAL, NOT CLEVER)
    # ==================================================
    gap_inner = 16        # gap between reward cards
    gap_group = 40        # 🔥 gap between GIVE and GET groups

    # total width = 1 give + gap_group + 2 rewards + inner gap
    total_width = CARD_WIDTH * 3 + gap_group + gap_inner

    group_left = cx - total_width // 2

    # YOU GIVE
    give_x, reward_x1, reward_x2, cards_y = get_gate_card_positions(popup_x, popup_y)

    # ==================================================
    # LABELS
    # ==================================================
    give_lbl = retro_small.render("YOU GIVE", True, (180, 180, 180))
    get_lbl  = retro_small.render("YOU GET (CHOOSE ONE)", True, (180, 180, 180))

    screen.blit(
        give_lbl,
        (give_x + CARD_WIDTH // 2 - give_lbl.get_width() // 2,
         cards_y - 24)
    )

    screen.blit(
        get_lbl,
        ((reward_x1 + reward_x2 + CARD_WIDTH) // 2 - get_lbl.get_width() // 2,
         cards_y - 24)
    )

    # ==================================================
    # YOU GIVE (REQUIRED CARD)
    # ==================================================
    draw_full_card(
        {"type": give_type, "power": need_power},
        give_x,
        cards_y
    )

    # ==================================================
    # YOU GET (REWARD CARDS)
    # ==================================================
    draw_full_card(rewards[0], reward_x1, cards_y)
    draw_full_card(rewards[1], reward_x2, cards_y)

    # ---- selected highlight ----
    if selected_reward_index is not None:
        rx = reward_x1 if selected_reward_index == 0 else reward_x2
        pygame.draw.rect(
            screen,
            (255, 255, 120),
            (rx - 4, cards_y - 4, CARD_WIDTH + 8, CARD_HEIGHT + 8),
            3
        )

    # ==================================================
    # SWAP BUTTON
    # ==================================================
    STORE_TRADE_BTN_RECT.center = (
        cx,
        cards_y + CARD_HEIGHT + 62
    )
    draw_image_button(
        STORE_TRADE_BTN_RECT,
        "SWAP",
        STORE_TRADE_BTN_RECT.collidepoint(pygame.mouse.get_pos())
    )

    # ==================================================
    # CANCEL HINT
    # ==================================================
    hint = retro_small.render(
        "MOVE AWAY TO CANCEL SWAP",
        True,
        (180, 180, 180)
    )
    screen.blit(
        hint,
        (cx - hint.get_width() // 2,
         popup_y + popup_h - 36)
    )

def draw_room_debug_info():
    if not DEBUG:
        return

    lines = [
        f"START ROOM : {START_ROOM}",
        f"END ROOM   : {finish_room}",
        f"CURRENT    : {current}",
    ]

    x = SIDEBAR_W + 20
    y = 20
    gap = 18

    for i, line in enumerate(lines):
        txt = retro_small.render(line, True, (255, 120, 120))
        screen.blit(txt, (x, y + i * gap))


# =========================
# LOOP
# =========================
while True:
    clock.tick(FPS)
    
    
    if game_state == STATE_MENU:
        if not pygame.mixer.music.get_busy():
            play_music(MUSIC_MENU)
        handle_menu_events()
        draw_main_menu()
        draw_cursor()
        pygame.display.flip()
        continue


    if game_state == STATE_HOWTO:
        handle_howto_events()
        draw_howto_screen()
        draw_cursor()
        pygame.display.flip()
        continue

    if game_state == STATE_DIFFICULTY:
        handle_difficulty_events()
        draw_difficulty_screen()
        draw_cursor()
        pygame.display.flip()
        continue
    
    if game_state == STATE_GAME:
        
        
        if GAME_ENDED:
            # Handle events for game ended screen
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Return to main menu on ESC or SPACE or ENTER
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE or e.key == pygame.K_SPACE or e.key == pygame.K_RETURN:
                        game_state = STATE_MENU
                        # Reset game will be called when starting new game
                        continue
                
                # Also allow mouse click to return to menu
                if e.type == pygame.MOUSEBUTTONDOWN:
                    game_state = STATE_MENU
                    continue
            
            screen.fill((0, 0, 0))

            if GAME_OVER:
                txt = retro_font.render("GAME OVER", True, (255, 80, 80))
                screen.blit(
                    txt,
                    (SCREEN_WIDTH // 2 - txt.get_width() // 2,
                     SCREEN_HEIGHT // 2 - txt.get_height() // 2)
                )
            else:
                # Calculate final score
                score_multiplier = difficulty_settings[current_difficulty]["score_multiplier"]
                final_score = points * score_multiplier
                
                # "YOU ESCAPED!" title
                txt = retro_font.render("YOU ESCAPED!", True, (80, 255, 120))
                screen.blit(
                    txt,
                    (SCREEN_WIDTH // 2 - txt.get_width() // 2,
                     SCREEN_HEIGHT // 2 - 60)
                )
                
                # "FINAL SCORE:" label
                score_label = retro_small.render("FINAL SCORE:", True, (200, 200, 200))
                screen.blit(
                    score_label,
                    (SCREEN_WIDTH // 2 - score_label.get_width() // 2,
                     SCREEN_HEIGHT // 2)
                )
                
                # Score number in large golden text
                score_text = retro_font.render(str(final_score), True, (255, 215, 0))
                screen.blit(
                    score_text,
                    (SCREEN_WIDTH // 2 - score_text.get_width() // 2,
                     SCREEN_HEIGHT // 2 + 30)
                )
                
                # Show calculation breakdown
                breakdown = retro_small.render(f"({points} points × {score_multiplier})", True, (150, 150, 150))
                screen.blit(
                    breakdown,
                    (SCREEN_WIDTH // 2 - breakdown.get_width() // 2,
                     SCREEN_HEIGHT // 2 + 75)
                )

            hint = retro_small.render("Press ESC or click to return to menu", True, (180, 180, 180))
            screen.blit(
                hint,
                (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                 SCREEN_HEIGHT // 2 + 120)
            )
            
            draw_cursor()
            pygame.display.flip()
            continue   # 🔴 THIS STOPS ALL GAME LOGIC
        
        
        
        
        if gate_message_timer > 0:
            gate_message_timer -= 1

        dt = clock.get_time() / 1000  # seconds
        time_accumulator += dt

        if not GAME_OVER and not GAME_WIN:
            if time_accumulator >= 1:
                points -= POINT_DECAY_PER_SEC
                time_accumulator = 0

                if points <= 0:
                    points = 0
                    GAME_OVER = True
                    GAME_ENDED = True





    


    
    
    
    
    
    
    
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
    
    # =========================
    # FOOTSTEP SOUND (FIXED)
    # =========================
    if moving:
        footstep_timer += 1
        if footstep_timer >= 15:   # adjust for speed (10–20)
            SFX_FOOTSTEP.play()
            footstep_timer = 0
    else:
        footstep_timer = 0
    
            
            

    
    handle_doors()
    
    update_free_gate()
    
    gate_dir = can_interact_gate()
    show_swap_ui = False
    show_gate_popup = gate_dir is not None



    # 🔥 RESET SELECTION ONLY WHEN POPUP JUST OPENED
    if show_gate_popup and not prev_show_gate_popup:
        selected_reward_index = None

    prev_show_gate_popup = show_gate_popup
    # screen.fill((0,0,0))

    # Sidebar
    screen.blit(sidebar_bg, (0, 0))
    cards_top = draw_cards_title()
    cards_start_y = cards_top + 12
    handle_events(cards_start_y)
    # Game box border
    
    # ===== WORLD BACKGROUND (MAIN ROOM + PREVIEWS) =====
    # world_x = SIDEBAR_W
    world_x = SIDEBAR_W
    world_y = 0
    screen.blit(bg_world, (world_x, world_y))
    # screen.blit(world_border_img, (world_x, world_y))

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
    
    rows = (len(cards) - 1) // CARDS_PER_ROW + 1
    cards_end_y = cards_start_y + rows * (CARD_HEIGHT - CARDS_ROW_OVERLAP)

    trade_button_rect = draw_trade_button_center(cards_end_y)

    # cards_top = draw_cards_title()
    # CARDS_START_Y = cards_top + 12
    draw_press_e_hint()
    draw_sidebar_hud()
    # LEFT SIDEBAR & CARDS ARE ALWAYS DRAWN
    draw_cards(cards_start_y)
    draw_minimap()
    # draw_gate_message()

    # POPUPS DRAW ON TOP
    if show_store_popup:
        PAD_X = 40
        PAD_Y = 80
        draw_store_popup()
    elif show_gate_popup:
        draw_gate_popup()

    # BACK TO MENU BUTTON (always visible during gameplay)
    draw_back_to_menu_button()
    
    # MENU CONFIRMATION DIALOG (top layer)
    if show_menu_confirmation:
        draw_menu_confirmation_dialog()




    
    if GAME_OVER:
        txt = retro_font.render("GAME OVER", True, (255, 80, 80))
        screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2,
                          SCREEN_HEIGHT//2 - 20))
        pygame.display.flip()
        continue
    if GAME_WIN:
        txt = retro_font.render("YOU ESCAPED!", True, (80, 255, 120))
        screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2,
                          SCREEN_HEIGHT//2 - 20))
        pygame.display.flip()
        continue






    # title_text = f"{room['type']} CHAMBER  -  #{current}"
    # title = retro_font.render(title_text, True, (240, 240, 240))

    # title_x = GAME_BOX_RECT.centerx - title.get_width() // 2
    # title_y = GAME_BOX_RECT.top - 34

    # screen.blit(title, (title_x, title_y))

    
    
    if DEBUG:
        draw_debug_borders()


    mx, my = pygame.mouse.get_pos()

    # hotspot adjustment (see below)
    cursor_x = mx
    cursor_y = my

    screen.blit(cursor_img, (cursor_x, cursor_y))
    
    if not show_store_popup and not show_gate_popup and not show_menu_confirmation:
        world_x = SIDEBAR_W
        world_y = 0
        screen.blit(world_border_img, (world_x, world_y))

    draw_room_debug_info()
    draw_gate_message()
    pygame.display.flip()
