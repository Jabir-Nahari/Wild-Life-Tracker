import time
import random
from Environment import Jungle_Environment
from search_algorithim import (
    astar_search,
    get_path_actions,
    get_path_states
)

class AStarAgent:
    def __init__(self, environment):
        self.env = environment
        self.solution_node = None
        self.actions_taken = []
        self.states_visited = []

    def plan(self):
        self.solution_node = astar_search(self.env, self.env.h)
        if self.solution_node:
            self.actions_taken = get_path_actions(self.solution_node)
            self.states_visited = get_path_states(self.solution_node)
            return True
        return False

    def get_actions(self):
        return self.actions_taken

    def get_states(self):
        return self.states_visited

    def print_plan(self):
        print("Actions to reach goal:")
        for action in self.actions_taken:
            print(" -", action)
        print("\nFinal State:")
        print(self.solution_node.state if self.solution_node else "No final state")


if __name__ == "__main__":
    # Define test environment parameters
    N = 30
    ambulance = (0, 0)
    orientation = 'right'
    needles = 2 
    shed_location = (3, 25)
    existing_trees = {(1, 1), (1, 2), (2, 1), (3, 3), (21, 1)}

    restricted_positions = {ambulance, shed_location}
    restricted_positions.update(existing_trees)

    # Generate ~100 trees
    target_tree_count = 100
    trees = set(existing_trees)

    while len(trees) < target_tree_count:
        x = random.randint(0, N - 1)
        y = random.randint(0, N - 1)
        new_pos = (x, y)
        if new_pos not in restricted_positions:
            trees.add(new_pos)

    # Create environment
    env = Jungle_Environment(N, ambulance, orientation, needles, shed_location, trees)

    # Create and run agent
    agent = AStarAgent(env)
    success = agent.plan()

    if success:
        print(" Agent reached the goal!")
        agent.print_plan()
    else:
        print(" Agent failed to reach the goal.")
