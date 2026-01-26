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
