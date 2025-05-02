# test.py - focused A* agent with improved targeting strategy
import sys, random
from Environment import Jungle_Environment
from search_algorithim import astar_search, get_path_actions, get_path_states
import asyncio
# ───── make Windows console UTF-8 so emojis don't crash ─────
if sys.platform.startswith("win") and (sys.stdout.encoding or "").lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

class AStarAgent:
    def __init__(self, env):
        self.env = env
        self.current_state = env.initial_state
        self.phase = "exploration"
        self.knowledge = {}
        self.shed_last_seen = None
        self.update_knowledge(env.perceive(self.current_state))
        
    def update_knowledge(self, vis):
        self.knowledge.update(vis)
        for pos, obj in vis.items():
            if obj == 'shed':
                self.shed_last_seen = pos
                self.phase = "exploitation"

    
    def is_free(self, pos):
        return self.knowledge.get(pos) in ("empty", "shed")
    
    def reachable_frontier(self):
        from collections import deque
        N = self.env.N
        seen, front = set(), set()
        start = self.current_state[0]
        
        if not self.is_free(start): 
            return front
            
        dq = deque([start])
        seen.add(start)
        
        while dq:
            r, c = dq.popleft()
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r+dr, c+dc
                if not (0 <= nr < N and 0 <= nc < N): 
                    continue
                p = (nr, nc)
                if p in self.knowledge:
                    if self.is_free(p) and p not in seen:
                        seen.add(p)
                        dq.append(p)
                else:
                    front.add(p)
        return front
    
    def h_exp(self, node):
        (r, c), *_ = node.state
        F = self._front
        
        if not F:
            return 0
            
        if self.shed_last_seen:
            sr, sc = self.shed_last_seen
            min_dist = float('inf')
            for fr, fc in F:
                dist = abs(r-fr) + abs(c-fc) + 0.1 * (abs(fr-sr) + abs(fc-sc))
                min_dist = min(min_dist, dist)
            return min_dist
        return min(abs(r-fr) + abs(c-fc) for fr, fc in F)
    
    # ------------------------------------------------------------
#  HEURISTIC  h_expl_fast  (admissible)
# ------------------------------------------------------------
    def h_expl_fast(self, node):
        (r, c), orient, needles, caught, status, (sr, sc) = node.state
        ar, ac = self.env.ambulance          #  const for the whole problem

        # --------------------------------------------------------
        # 1.  AFTER THE SHED HAS BEEN PICKED  (caught == True)
        # --------------------------------------------------------
        if caught:
            # Only have to walk to the ambulance.
            # Manhattan distance  is a lower bound because turning
            # and obstacles can only increase the cost.
            return abs(r - ar) + abs(c - ac)

        # --------------------------------------------------------
        # 2.  SHED IS TRANQUILISED BUT NOT YET PICKED  (status == 3)
        # --------------------------------------------------------
        if status == 3:
            # Need to walk to the shed, pick, then walk to ambulance.
            #            walk-to-shed   + pick(0.1) + walk-home
            return (abs(r - sr) + abs(c - sc)
                    + 0.1
                    + abs(sr - ar) + abs(sc - ac))

        # --------------------------------------------------------
        # 3.  SHED IS STILL RUNNING  (status == 2)
        # --------------------------------------------------------
        # We must:
        #   a) reach the *shooting line*  (same row OR same column)
        #   b) face toward the shed       (≤ one turn -- see below)
        #   c) throw the needle           (0.1)
        #   d) walk to the shed + pick    (dist + 0.1)
        #   e) walk to the ambulance
        #
        # Any real plan will cost at least the sum of the five terms
        # below, so the heuristic is admissible.
        # --------------------------------------------------------

        # a+b)  cost **until** the needle leaves the gun
        # ------------------------------------------------
        #  distance to *first* aligned square
        to_line = min(abs(r - sr), abs(c - sc))

        #  minimal extra turn to face the shed *once aligned*
        #  (a real plan sometimes needs two turns; counting only
        #   one keeps the estimate admissible)
        one_turn = 0
        if r == sr:                                 # already on same row
            need = 'right' if c <  sc else 'left'
            one_turn = 0 if orient == need else 1
        elif c == sc:                               # already on same col
            need = 'down'  if r <  sr else 'up'
            one_turn = 0 if orient == need else 1
        # if not yet aligned --> we may need a turn later; we ignore it

        # c)  shoot
        shoot_cost = 0.1

        # d)  walk from shooting spot to the shed  (necessarily
        #      |r-sr| + |c-sc| after alignment)  +  pick(0.1)
        to_shed  = abs(r - sr) + abs(c - sc)
        pick_cost = 0.1

        # e)  walk from shed to ambulance
        to_home = abs(sr - ar) + abs(sc - ac)

        return to_line + one_turn + shoot_cost + to_shed + pick_cost + to_home

    
    def actions(self, s):
        avail = self.env.actions(s)
        (r, c), orient, needles, caught, status, (sr, sc) = s
        
        if 'throw-needle' in avail and needles > 0 and status == 2:
            if self.env._clear_line((r, c), (sr, sc), orient):
                return ['throw-needle']
        
        if 'pick' in avail and (r, c) == (sr, sc) and status == 3:
            return ['pick']
        
        dr, dc = self.env._FWD_DELTA[orient]
        ahead = (r+dr, c+dc)
        
        if self.phase == "exploitation" and self.shed_last_seen:
            if 'move-forward' in avail:
                if caught:
                    ar, ac = self.env.ambulance
                    curr_dist = abs(r-ar) + abs(c-ac)
                    new_dist = abs(r+dr-ar) + abs(c+dc-ac)
                    if new_dist < curr_dist:
                        return ['move-forward']
                elif status == 3:
                    curr_dist = abs(r-sr) + abs(c-sc)
                    new_dist = abs(r+dr-sr) + abs(c+dc-sc)
                    if new_dist < curr_dist:
                        return ['move-forward']
                elif status == 2:
                    if r+dr == sr or c+dc == sc:
                        return ['move-forward']
        
        return avail
    
    def result(self, s, a):
        return self.env.result(s, a)
    
    def action_cost(self, s, a, s1):
        (r, c), orient, needles, caught, status, (sr, sc) = s
        
        if a == 'throw-needle' and self.env._clear_line((r, c), (sr, sc), orient) and status == 2:
            return 0.1
        if a == 'pick' and (r, c) == (sr, sc) and status == 3:
            return 0.1
        if a == 'move-forward':
            dr, dc = self.env._FWD_DELTA[orient]
            if caught:
                ar, ac = self.env.ambulance
                if abs(r+dr-ar) + abs(c+dc-ac) < abs(r-ar) + abs(c-ac):
                    return 0.5
            elif status == 3:
                if abs(r+dr-sr) + abs(c+dc-sc) < abs(r-sr) + abs(c-sc):
                    return 0.5
            return 1
        if a in ('turn-left', 'turn-right'):
            return 1.5
        return 2
    
    def is_goal(self, s):
        return self.env.is_goal(s)
    
    def plan(self):
        if self.phase == "exploration":
            F = self.reachable_frontier()
            if not F:
                self.phase = "exploitation"
                return self.plan()
                
            self._front = F
            agent = self
            
            class P:
                def __init__(self): self.initial_state = agent.current_state
                def actions(self, s): return agent.actions(s)
                def result(self, s, a): return agent.result(s, a)
                def action_cost(self, s, a, s1): return agent.action_cost(s, a, s1)
                def is_goal(self, s): return s[0] in F
                
            node = astar_search(P(), self.h_exp)
        
        else:
                self.env.initial_state = self.current_state
                node = astar_search(self.env, self.h_expl_fast)

        
        if not node:
            return False
        
        self.plan_actions = get_path_actions(node)
        self.plan_states = get_path_states(node)
        return bool(self.plan_actions)
    
    async def run(self, max_steps=1000):
        self.step = 0
        self.max_steps = max_steps
        while not self.is_goal(self.current_state):
            if self.step >= max_steps or not self.plan():
                print(f"❌  Agent failed after {self.step} steps.")
                return
            
            self.action = self.plan_actions.pop(0)
            agent_pos, orient, needles, caught, status, shed_pos = self.current_state
            print(f"Step {self.step:6}: {self.action} | Agent: {agent_pos} | Shed: {shed_pos} | Status: {status} | Caught: {caught}")
            
            self.current_state = self.result(self.current_state, self.action)
            self.update_knowledge(self.env.perceive(self.current_state))
            
            *_, status, (sr, sc) = self.current_state
            if status != 1 or (sr, sc) in self.knowledge:
                self.phase = "exploitation"
            
            self.step += 1
            await asyncio.sleep(0) 
        print(f"\n✅  Mission complete in {self.step} steps!")

# ───────────── driver ─────────────
# if __name__ == "__main__":
#     N, amb, ori, needles = 50, (0,0), "right", 5
#     shed = (30,20)
#     trees = set()
#     while len(trees) < 50:
#         trees.add((random.randint(5,N-1), random.randint(5,N-1)))
    
#     for r in range(min(amb[0], shed[0]), max(amb[0], shed[0])+1):
#         for c in range(min(amb[1], shed[1]), max(amb[1], shed[1])+1):
#             if (r,c) in trees and (r,c) != amb and (r,c) != shed:
#                 trees.remove((r,c))
    
#     env = Jungle_Environment(N, amb, ori, needles, shed, trees)
#     agent = AStarAgent(env)
#     agent.run()
