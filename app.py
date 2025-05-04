import pygame
import sys
import random
import agent as ag
import Environment as en
import asyncio
# === Performance Logging Setup ===
import os
import json

STATS_FILE = "stats/performance_log.json"
if not os.path.exists("stats"):
    os.makedirs("stats")
if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, "w") as f:
        json.dump([], f)

def log_run_statistics(success, steps, needles_left):
    with open(STATS_FILE, "r") as f:
        data = json.load(f)

    new_entry = {
        "success": success,
        "steps": steps,
        "needles_left": needles_left
    }
    data.append(new_entry)

    with open(STATS_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return data

def calculate_and_display_stats(data, current_entry):
    total_runs = len(data)
    successes = sum(1 for d in data if d["success"])
    avg_steps = sum(d["steps"] for d in data) / total_runs
    avg_needles = sum(d["needles_left"] for d in data) / total_runs

    print("\n----- Agent Performance Statistics -----")
    print(f"Total Runs: {total_runs}")
    print(f"Success Rate: {successes / total_runs:.2%}")
    print(f"Average Steps: {avg_steps:.2f}")
    print(f"Average Needles Left: {avg_needles:.2f}")
    print("\n-- Current Run --")
    print(f"Success: {current_entry['success']}")
    print(f"Steps Taken: {current_entry['steps']}")
    print(f"Needles Left: {current_entry['needles_left']}")
    print("----------------------------------------\n")


# === Game Setup ===

pygame.init()
N = random.randint(20,25)
TILE_SIZE = 20
GRID_WIDTH, GRID_HEIGHT = N, N
TOP_LAYER_HEIGHT_RATIO = 0.70
WIDTH, HEIGHT = TILE_SIZE * GRID_WIDTH, GRID_HEIGHT * TILE_SIZE
TOP_LAYER_HEIGHT = HEIGHT
BOTTOM_LAYER_OFFSET = 150
BOTTOM_LAYER_HEIGHT = HEIGHT+BOTTOM_LAYER_OFFSET

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GREEN = (0, 50, 0)
VISION_COLOR = (255, 255, 0, 80)
ACTIONS = ['turn-left', 'turn-right', 'move-forward', 'throw-needle', 'pick', 'stay']
screen = pygame.display.set_mode((WIDTH, BOTTOM_LAYER_HEIGHT))
pygame.display.set_caption("Wild-Life-Tracker")

FONT = pygame.font.SysFont('arial', 12)
animal_status = ""
animal_pos = ()
trees = set()
agent = ""
env = ""

if N < 27:
    amb = (0, random.randint(0,GRID_HEIGHT))
else:
    amb = (random.randint(0, GRID_WIDTH), 0)
ori, needles = "right", 5
ax, ay = amb

def run_env_agent():
    shed = (12,13)
    for r in range(min(amb[0], shed[0]), max(amb[0], shed[0])+1):
        for c in range(min(amb[1], shed[1]), max(amb[1], shed[1])+1):
            if (r,c) in trees and (r,c) != amb and (r,c) != shed:
                trees.remove((r,c))

    global env
    global agent
    global animal_pos
    global animal_status
    env = en.Jungle_Environment(N, amb, ori, needles, shed, trees)
    agent = ag.AStarAgent(env)
    animal_pos = env.state[5]
    animal_status = env.state[4]

def draw_text_wrapped(text, rect, font, color=pygame.Color('white'), wrap_on=None):
    surface = pygame.display.get_surface()
    padding = 5
    line_spacing = -2
    x = rect.x + padding
    y = rect.y + padding

    if wrap_on and wrap_on in text:
        lines = text.split(wrap_on)
    else:
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            w = font.size(' '.join(current_line + ['...']))[0]
            if w > rect.width - 2 * padding:
                if len(current_line) > 1:
                    last_word = current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [last_word]
        if current_line:
            lines.append(' '.join(current_line))

    for line in lines:
        text_surface = font.render(line, True, color)
        if y + text_surface.get_height() < rect.bottom:
            surface.blit(text_surface, (x, y))
            y += text_surface.get_height() + line_spacing

    return y

def load_image(name, size=TILE_SIZE):
    path = f"game_assets/{name}"
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, (size, size))
    except FileNotFoundError:
        print(f"Missing asset: {path}")
        return pygame.Surface((size, size))

tile_grass = load_image("Grass.jpg")
tile_tree = load_image("Tree.png", size=TILE_SIZE+5)
tile_ambulance = load_image("ambulance-car.png", size=TILE_SIZE)
player_img = load_image("Drone.png", size=TILE_SIZE)
animal_img = load_image("Shed2.png", size=TILE_SIZE+30)

map_data = [["grass" for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
run_env_agent()

def create_trees():
    global trees
    global N
    max_trees = 50
    min_distance = 2
    attempts = 0
    max_attempts = 500

    while len(trees) < max_trees and attempts < max_attempts:
        x = random.randint(0, N - 1)
        y = random.randint(0, N - 1)
        too_close = False
        for tx, ty in trees:
            if abs(tx - x) < min_distance and abs(ty - y) < min_distance:
                too_close = True
                break
        if not too_close:
            trees.add((x, y))
        attempts += 1

    env.Trees_location = trees

create_trees()
for tree in trees:
    x, y = tree
    map_data[y][x] = "tree"

while True:
    if map_data[ay][ax] == "grass":
        map_data[ay][ax] = "ambulance"
        break

class Agent:
    def __init__(self):
        self.x, self.y = agent.current_state[0]
        self.direction = agent.current_state[1]

    def draw(self, surface):
        center = (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.circle(surface, (255, 0, 0), center, 3)
        surface.blit(player_img, (self.x * TILE_SIZE, self.y * TILE_SIZE))

    def get_vision_area(self):
        vision_tiles = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                    vision_tiles.append((nx, ny))
        return vision_tiles

    def update_agent(self):
        self.x, self.y = agent.current_state[0]
        self.direction = agent.current_state[1]

class Animal:
    def __init__(self):
        self.x, self.y = animal_pos

    def draw(self, surface):
        center = (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.circle(surface, (0, 0, 255), center, 3)
        surface.blit(animal_img, (self.x * TILE_SIZE, self.y * TILE_SIZE))

    def update_animal_position(self, surface):
        self.x, self.y = animal_pos

    def get_animal_position(self):
        return self.x, self.y

agent_sprite = Agent()
current_animal = Animal()
clock = pygame.time.Clock()
running = True
timestep = 0

async def run_ui():
    global running, timestep, clock, current_animal, agent_sprite, agent, animal_pos, animal_status
    while running:
        clock.tick(5)
        if not env.state[3] and timestep < agent.max_steps:
            timestep += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        agent_sprite.update_agent()
        screen.fill(WHITE)

        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if map_data[y][x] == "grass":
                    color = (0, 100, 0) if (x + y) % 2 == 0 else (34, 139, 34)
                    pygame.draw.rect(screen, color, rect)
                elif map_data[y][x] == "tree":
                    pygame.draw.rect(screen, (34, 139, 34), rect)
                    screen.blit(tile_tree, rect.topleft)
                elif map_data[y][x] == "ambulance":
                    pygame.draw.rect(screen, (0, 100, 0), rect)
                    screen.blit(tile_ambulance, rect.topleft)

        vision_rects = agent_sprite.get_vision_area()
        vision_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        vision_surface.fill(VISION_COLOR)
        for vx, vy in vision_rects:
            screen.blit(vision_surface, (vx * TILE_SIZE, vy * TILE_SIZE))

        agent_sprite.draw(screen)
        animal_pos = env.state[5]
        animal_status = env.state[4]

        if current_animal:
            current_animal.update_animal_position(screen)
            current_animal.draw(screen)

        if ((env.state[3] == True or timestep >= agent.max_steps) and current_animal):
            screen.blit(tile_grass, (current_animal.x * TILE_SIZE, current_animal.y * TILE_SIZE))
            current_animal = None

        bottom_background = pygame.Rect(0, TOP_LAYER_HEIGHT, WIDTH, BOTTOM_LAYER_HEIGHT)
        pygame.draw.rect(screen, DARK_GREEN, bottom_background)

        box_a_top = TOP_LAYER_HEIGHT
        box_a_height = BOTTOM_LAYER_OFFSET // 2
        box_b_top = box_a_top + box_a_height
        box_b_height = BOTTOM_LAYER_OFFSET // 2

        box_a_left = pygame.Rect(0, box_a_top, WIDTH // 2, box_a_height)
        box_a_right = pygame.Rect(WIDTH // 2, box_a_top, WIDTH // 2, box_a_height)
        box_b_left = pygame.Rect(0, box_b_top, WIDTH // 2, box_b_height)
        box_b_right = pygame.Rect(WIDTH // 2, box_b_top, WIDTH // 2, box_b_height)

        for r in [box_a_left, box_a_right, box_b_left, box_b_right]:
            pygame.draw.rect(screen, DARK_GREEN, r)
            pygame.draw.rect(screen, BLACK, r, 2)

        draw_text_wrapped("Agent Actions: Move: Up, Down, Left, Right|Inject: On same tile as Shed|Pick: When Shed is asleep|Throw Needle: Straight line", box_a_left, FONT, wrap_on="|")
        draw_text_wrapped("Environment Rules:|Shed escapes when spotted|Movement: 2 away from agent, 2 left|Trees block movement/vision|Vision: 5x5 area", box_a_right, FONT, wrap_on="|")
        animal_status = "Present" if env.state[3] else "None"
        draw_text_wrapped(f"Resources: Needles: {agent.current_state[2]}|Time Remaining: 120 time units", box_b_left, FONT, wrap_on="|")
        draw_text_wrapped("Mission Status: Shed: Active|Carrying: No", box_b_right, FONT, wrap_on="|")

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()

    # Log and display stats
    current_entry = {
        "success": env.state[3],
        "steps": timestep,
        "needles_left": agent.current_state[2]
    }

    stats_data = log_run_statistics(**current_entry)
    calculate_and_display_stats(stats_data, current_entry)
    sys.exit()


async def main():
    await asyncio.gather(
        agent.run(),
        run_ui()
    )

if __name__ == "__main__":
    asyncio.run(main())
