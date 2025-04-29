import heapq

class PriorityQueue:
    def __init__(self, items=(), priority_function=(lambda x: x)):
        self.priority_function = priority_function
        self.pqueue = []
        self.counter = 0  # Unique counter to avoid tie errors
        for item in items:
            self.add(item)

    def add(self, item):
        priority = self.priority_function(item)
        heapq.heappush(self.pqueue, (priority, self.counter, item))
        self.counter += 1

    def pop(self):
        return heapq.heappop(self.pqueue)[2]  # return the Node

    def __len__(self):
        return len(self.pqueue)



class Node:
    def __init__(self, state, parent=None, action_from_parent=None, path_cost=0):
        self.state = state
        self.parent = parent
        self.action_from_parent = action_from_parent
        self.path_cost = path_cost

        if self.parent == None:
            self.depth = 0
        else:
            self.depth = self.parent.depth + 1

def expand(problem, node):
    s = node.state
    for action in problem.actions(s):
        s1 = problem.result(s, action)
        cost = node.path_cost + problem.action_cost(s, action, s1)
        yield Node(s1, node, action, cost)

def best_first_search(problem, f, max_depth = None):
    node = Node(problem.initial_state)
    frontier = PriorityQueue([node], f)
    reached = {problem.initial_state: node}
    best_node = node   # ← Keep track of best effort
    while len(frontier) > 0:
        n = frontier.pop()
        if problem.is_goal(n.state):
            return n
        best_node = n  # Always update best seen so far
        if max_depth is None or n.depth < max_depth:
            for child in expand(problem, n):
                s = child.state
                if s not in reached or reached[s].path_cost > child.path_cost:
                    reached[s] = child
                    frontier.add(child)
    
    # If no goal found, return best node
    return best_node


def best_first_search_treelike(problem, f, max_depth = None):
    node = Node(problem.initial_state)
    frontier = PriorityQueue([node], f)
    while len(frontier) > 0:
        n = frontier.pop()
        if problem.is_goal(n.state):
            return n
        best_node = n  # Always update best seen so far
        if max_depth is None or n.depth < max_depth:
            for child in expand(problem, n):
                frontier.add(child)
    return best_node

def get_path_actions(node):
    if node == None or node.parent == None:
        return []
    return get_path_actions(node.parent) + [node.action_from_parent]

def get_path_states(node):
    if node == None:
        return []
    return get_path_states(node.parent) + [node.state]

def astar_search(problem, h, treelike=False, max_depth = None):
    if treelike:
        if max_depth is not None:
            return best_first_search_treelike(problem, (lambda node: node.path_cost + h(node)), max_depth)
        return best_first_search_treelike(problem, (lambda node: node.path_cost + h(node)))
    else:
        if max_depth is not None:
            return best_first_search(problem, (lambda node: node.path_cost + h(node)), max_depth)
        return best_first_search(problem, (lambda node: node.path_cost + h(node)))

def depth_first_search(problem, treelike=False):
    if treelike:
        return best_first_search_treelike(problem, (lambda node: -node.depth))
    else:
        return best_first_search(problem, (lambda node: -node.depth))

def bredth_first_search(problem, treelike=False):
    if treelike:
        return best_first_search_treelike(problem, (lambda node: node.depth))
    else:
        return best_first_search(problem, (lambda node: node.depth))


def greedy_search(problem, h, treelike=False):
    if treelike:
        return best_first_search_treelike(problem, f=h)
    else:
        return best_first_search(problem, f=h)






