import pygame, sys
from collections import deque

pygame.init()
WIDTH, HEIGHT = 900, 700
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🎨 Smart Map Coloring")

# Load and scale map
MAP_IMAGE = pygame.image.load("sketch.png").convert()
MAP_IMAGE = pygame.transform.scale(MAP_IMAGE, (WIDTH, HEIGHT))
DRAW_SURFACE = MAP_IMAGE.copy()

# Colors palette
COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 0), (255, 165, 0), (128, 0, 128),
    (0, 255, 255), (255, 192, 203), (139, 69, 19),
    (210, 180, 140), (0, 0, 0), (255, 255, 255)
]

FONT = pygame.font.SysFont("Comic Sans MS", 26, bold=True)
selected_color_index = 0
warning_message = ""

regions = []
next_region_id = 1

def color_close(c1, c2, tolerance=30):
    return all(abs(c1[i] - c2[i]) < tolerance for i in range(3))

def get_region_pixels(surface, x, y, tol=30):
    target = surface.get_at((x, y))[:3]
    q = deque([(x, y)])
    visited = set()
    while q:
        cx, cy = q.popleft()
        if (cx, cy) in visited:
            continue
        if cx < 0 or cy < 0 or cx >= WIDTH or cy >= HEIGHT:
            continue
        cur = surface.get_at((cx, cy))[:3]
        if not color_close(cur, target, tol):
            continue
        visited.add((cx, cy))
        q.extend([(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)])
    return visited

def fill_pixels(surface, pixels, fill_color):
    for (px, py) in pixels:
        surface.set_at((px, py), fill_color)

def get_centroid(pixels):
    if not pixels:
        return (0, 0)
    sx = sum(p[0] for p in pixels)
    sy = sum(p[1] for p in pixels)
    return (sx // len(pixels), sy // len(pixels))

def regions_touch(pixels_a, pixels_b):
    bset = set(pixels_b)
    for (x, y) in pixels_a:
        if ((x+1, y) in bset) or ((x-1, y) in bset) or ((x, y+1) in bset) or ((x, y-1) in bset):
            return True
    return False

def palette_rects():
    rects = []
    cols_per_row = 8
    swatch_size = 50
    padding = 10
    start_x = 50
    start_y = HEIGHT - 150
    for i in range(len(COLORS)):
        row = i // cols_per_row
        col = i % cols_per_row
        x = start_x + col * (swatch_size + padding)
        y = start_y + row * (swatch_size + padding)
        rects.append((i, pygame.Rect(x, y, swatch_size, swatch_size)))
    return rects

def draw_palette():
    for i, rect in palette_rects():
        pygame.draw.rect(WIN, COLORS[i], rect)
        if i == selected_color_index:
            pygame.draw.rect(WIN, (0, 0, 0), rect, 3)

def reset_map():
    global DRAW_SURFACE, warning_message, regions, next_region_id
    DRAW_SURFACE = MAP_IMAGE.copy()
    warning_message = ""
    regions = []
    next_region_id = 1

def draw_screen():
    WIN.blit(DRAW_SURFACE, (0, 0))
    title = FONT.render("🎨 Click to color | Click palette to choose | R to reset | ESC to exit", True, (0, 0, 0))
    WIN.blit(title, (40, 20))
    draw_palette()
    if warning_message:
        warn = FONT.render(warning_message, True, (255, 0, 0))
        WIN.blit(warn, (40, 60))
    pygame.display.update()

# ---------------- Main Loop ----------------
clock = pygame.time.Clock()

while True:
    clock.tick(30)
    draw_screen()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            elif event.key == pygame.K_r:
                reset_map()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            clicked_palette = None
            for i, rect in palette_rects():
                if rect.collidepoint(pos):
                    clicked_palette = i
                    break
            if clicked_palette is not None:
                selected_color_index = clicked_palette
                warning_message = ""
                continue

            if pos[0] < 0 or pos[1] < 0 or pos[0] >= WIDTH or pos[1] >= HEIGHT:
                continue

            new_region_pixels = get_region_pixels(MAP_IMAGE, pos[0], pos[1])  # region from original map
            if not new_region_pixels or len(new_region_pixels) < 5:
                warning_message = "Click inside a valid region!"
                continue

            new_color = COLORS[selected_color_index]
            violates = False

            # Check adjacency first before coloring
            for reg in regions:
                if reg['color'] == new_color:
                    if regions_touch(new_region_pixels, reg['pixels']):
                        violates = True
                        break

            if violates:
                warning_message = "❌ Adjacent region already has this color!"
            else:
                fill_pixels(DRAW_SURFACE, new_region_pixels, new_color)
                centroid = get_centroid(new_region_pixels)
                regions.append({
                    'id': next_region_id,
                    'color': new_color,
                    'pixels': new_region_pixels,
                    'centroid': centroid
                })
                next_region_id += 1
                warning_message = ""

