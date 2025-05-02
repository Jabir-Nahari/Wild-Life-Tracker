import pygame
import sys
import random
import agent as ag
import Environment as en
import asyncio

# Initialize Pygame
pygame.init()

# Constants
N = 20
TILE_SIZE = 30
GRID_WIDTH, GRID_HEIGHT = N, N
TOP_LAYER_HEIGHT_RATIO = 0.70
WIDTH, HEIGHT = TILE_SIZE * GRID_WIDTH, GRID_HEIGHT * TILE_SIZE
TOP_LAYER_HEIGHT = HEIGHT
BOTTOM_LAYER_OFFSET = 150
BOTTOM_LAYER_HEIGHT = HEIGHT+BOTTOM_LAYER_OFFSET

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GREEN = (0, 50, 0)
VISION_COLOR = (255, 255, 0, 80)

# Actions
ACTIONS = ['turn-left', 'turn-right', 'move-forward', 'throw-needle', 'pick', 'stay']

# Setup screen
screen = pygame.display.set_mode((WIDTH, BOTTOM_LAYER_HEIGHT))
pygame.display.set_caption("Wild-Life-Tracker")

# Font setup for bottom layer
FONT = pygame.font.SysFont('arial', 12)
animal_status = ""
animal_pos = ()
trees = set()
agent = ""
env = ""

amb, ori, needles = (0,0), "right", 5
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
    


# Helper: Wrap and draw text inside a rectangle
def draw_text_wrapped(text, rect, font, color=pygame.Color('white'), wrap_on=None):
    """
    Draws text inside a pygame.Rect, splitting lines when 'wrap_on' is found.
    
    Parameters:
        text (str): The text to render
        rect (pygame.Rect): Area to render inside
        font (pygame.font.Font): Font to use
        color (tuple): Color of the text
        wrap_on (str): String or character(s) to split on for wrapping (e.g., ".WRAP.")
    """
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

    # Draw each line
    for line in lines:
        text_surface = font.render(line, True, color)
        if y + text_surface.get_height() < rect.bottom:
            surface.blit(text_surface, (x, y))
            y += text_surface.get_height() + line_spacing

    return y
    
# Load assets
def load_image(name, size=TILE_SIZE):
    path = f"game_assets/{name}"
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, (size+20, size))
    except FileNotFoundError:
        print(f"Missing asset: {path}")
        return pygame.Surface((size, size))

tile_grass = load_image("Grass.jpg")
tile_tree = load_image("Tree.png")
tile_ambulance = load_image("Ambulance.png", size=TILE_SIZE)
player_img = load_image("Drone.png", size=TILE_SIZE)
animal_img = load_image("Shed.png", size=TILE_SIZE + 40)

# Create map
map_data = [["grass" for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

# Randomly add trees
run_env_agent()

def create_trees():
    global trees
    global N
    while len(trees) < 50:
        trees.add((random.randint(5,N-1), random.randint(5,N-1)))
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
        self.direction = agent.current_state[1]  # 0: up, 1: right, 2: down, 3: left

    def draw(self, surface):
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
        
        

    def perform_action(self, action):
        if action == "turn-left":
            self.direction = (self.direction - 1) % 4
        elif action == "turn-right":
            self.direction = (self.direction + 1) % 4
        elif action == "move-forward":
            dx, dy = [(0, -1), (1, 0), (0, 1), (-1, 0)][self.direction]
            new_x, new_y = self.x + dx, self.y + dy
            if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT:
                if map_data[new_y][new_x] not in ["tree"]:  # Can't move into trees
                    self.x, self.y = new_x, new_y
        elif action == "throw-needle":
            print("Throwing needle...")
        elif action == "pick":
            print("Picking up...")
        elif action == "stay":
            pass

# Animal class
class Animal:
    def __init__(self):
        self.x, self.y = animal_pos

    def draw(self, surface):
        surface.blit(animal_img, (self.x * TILE_SIZE, self.y * TILE_SIZE))
        
    def update_animal_position(self, surface):
        self.x, self.y = animal_pos
# Placeholder for future logic
    def get_animal_position(self):
        return self.x, self.y

# Create agent
agent_sprite = Agent()

# Animal state
current_animal = Animal()

# Main loop
clock = pygame.time.Clock()
running = True
timestep = 0




async def run_ui():
    global running
    global timestep
    global clock
    global current_animal
    global agent_sprite
    global agent
    global animal_pos
    global animal_status
    while running:
        clock.tick(5)  # Slow sim for demo
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
                    screen.blit(tile_grass, rect.topleft)
                elif map_data[y][x] == "tree":
                    screen.blit(tile_grass, rect.topleft)
                    screen.blit(tile_tree, rect.topleft)
                elif map_data[y][x] == "ambulance":
                    screen.blit(tile_grass, rect.topleft)
                    screen.blit(tile_ambulance, rect.topleft)

        vision_rects = agent_sprite.get_vision_area()  # Now using vision_range instead of radius
        vision_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        vision_surface.fill(VISION_COLOR)  # This is your semi-transparent yellow

        for vx, vy in vision_rects:
            screen.blit(vision_surface, (vx * TILE_SIZE, vy * TILE_SIZE))
        agent_sprite.draw(screen)
        
        animal_pos = env.state[5]
        animal_status = env.state[4]
        if current_animal:
            current_animal.update_animal_position(screen)
            current_animal.draw(screen)

        if((env.state[3] == True or timestep >= agent.max_steps) and current_animal):
                screen.blit(tile_grass, (current_animal.x * TILE_SIZE, current_animal.y * TILE_SIZE))
                current_animal = None
                
                
                
        # DRAW BOTTOM LAYER (INFO PANELS)
        bottom_background = pygame.Rect(0, TOP_LAYER_HEIGHT, WIDTH, BOTTOM_LAYER_HEIGHT)
        pygame.draw.rect(screen, DARK_GREEN, bottom_background)

        # Info boxes
        box_a_top = TOP_LAYER_HEIGHT
        box_a_height = BOTTOM_LAYER_OFFSET // 2
        box_b_top = box_a_top + box_a_height
        box_b_height = BOTTOM_LAYER_OFFSET // 2

        box_a_left = pygame.Rect(0, box_a_top, WIDTH // 2, box_a_height)
        box_a_right = pygame.Rect(WIDTH // 2, box_a_top, WIDTH // 2, box_a_height)
        box_b_left = pygame.Rect(0, box_b_top, WIDTH // 2, box_b_height)
        box_b_right = pygame.Rect(WIDTH // 2, box_b_top, WIDTH // 2, box_b_height)

        # Fill and border
        for r in [box_a_left, box_a_right, box_b_left, box_b_right]:
            pygame.draw.rect(screen, DARK_GREEN, r)
            pygame.draw.rect(screen, BLACK, r, 2)

        # Add wrapped text
        draw_text_wrapped("Agent Actions: Move: Up, Down, Left, Right|Inject: On same tile as Shed|Pick: When Shed is asleep|Throw Needle: Straight line", box_a_left, FONT, wrap_on="|")
        draw_text_wrapped("Environment Rules:|Shed escapes when spotted|Movement: 2 away from agent, 2 left|Trees block movement/vision|Vision: 5x5 area", box_a_right, FONT, wrap_on="|")

        animal_status = "Present" if env.state[3] else "None"
        draw_text_wrapped(f"Resources: Needles: {agent.current_state[2]}|Time Remaining: 120 time units", box_b_left, FONT, wrap_on="|")

        draw_text_wrapped("Mission Status: Shed: Active|Carrying: No", box_b_right, FONT, wrap_on="|")

        # Update display
        pygame.display.flip()
        await asyncio.sleep(0)  

    pygame.quit()
    sys.exit()

async def main():
    # Run both coroutines concurrently
    await asyncio.gather(
        agent.run(),
        run_ui()
    )

if __name__ == "__main__":
    asyncio.run(main())