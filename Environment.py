class Jungle_Environment:
    _ORIENT_LEFT  = {'up':'left',  'left':'down', 'down':'right', 'right':'up'}  # given up (for example) - if i turn left what is my orient
    _ORIENT_RIGHT = {v:k for k,v in _ORIENT_LEFT.items()} # given up (for example) - if i turn left what is my orient
    _FWD_DELTA    = {'up':(-1,0), 'down':(1,0), 'left':(0,-1), 'right':(0,1)}
    
    def __init__(self, N, ambulance, F_orientation, Needle_num,Trees_location,Shed_init_locaiton, Timer):
        self.N = N
        self.ambulance = ambulance
        self.F_orientation = F_orientation
        self.Needle_num = Needle_num
        self.Trees_location = Trees_location
        # Shed status (3 -> drugged sleep), (2 -> awake), (1 -> initial sleep), (0 -> dead)
        self.Shed_init_location = Shed_init_locaiton
        self.Timer = Timer

        self.initial_state = (self.ambulance, self.F_orientation, self.Needle_num, False, 1, self.Shed_init_location, self.Timer)

    def action(self, state):
        available_actions = ['move-forward', 'turn-left', 'turn-right', 'throw-needle', 'pick', 'stay']
        '''dealing with (move-forward) action'''
        s = list(state)
        dr, dc = Jungle_Environment._FWD_DELTA[s[1]]
        new_location = tuple(s[0][0]+dr, s[0][1]+dc)
        if new_location in self.Trees_location:
            available_actions.remove('move-forward')
        elif new_location[0] >= self.N or new_location[0] < 0:
            available_actions.remove('move-forward')
        elif new_location[1] >= self.N or new_location[1] < 0:
            available_actions.remove('move-forward')
        '''dealing with (pick) action'''
        if s[0] != s[5]:
            available_actions.remove('pick')
        '''dealing with (throw-needle)'''
        if s[2] <= 0:
            available_actions.remove('throw-needle')
        '''return the set of actions available'''
        return available_actions

    
    def result(self, state, action):
        # 1) Unpack
        (row, col), orient, needles, caught, status, (sr, sc), timer = state
        
        """
        state = (agent_loc, orient, needles, caught, shed_status, shed_loc, timer)
        
        agent_loc   = (row, col)
        orient      = 'up'|'down'|'left'|'right'
        needles     = int
        caught      = bool
        shed_status = 0|1|2
        shed_loc    = (sr, sc)
        timer       = int

        action ∈ {'turn-left','turn-right',
              'move-forward','throw-needle','pick','stay'}
        """

        # 2) Apply the agent’s action
        if action == 'turn-left':
            orient = Jungle_Environment._ORIENT_LEFT[orient]
        elif action == 'turn-right':
            orient = Jungle_Environment._ORIENT_RIGHT[orient]
        elif action == 'move-forward':
            dr, dc = Jungle_Environment._FWD_DELTA[orient]
            nr, nc = row+dr, col+dc
            # only move if the cell is in‑bounds and not a tree
            if 0 <= (nr, nc) < self.N and (nr, nc) not in self.Trees_location:
                (row, col) = (nr, nc)
        elif action == 'throw-needle':
            needles -= 1
            # if Shed is in line‑of‑sight, put it into drugged sleep mode
            if self._clear_line((row, col), (sr, sc)):
                status = 3
        elif action == 'pick':
            # can pick only if on the same cell, Shed is asleep, and not already caught
            if not caught and (row, col) == (sr, sc) and status == 3:
                caught = True
        # 'stay' does nothing

        # 3) Environment dynamics
        # if Shed is in initial sleeping (1) and just came into the 5×5 window: (the status becomes awake (2))
        if status == 1 and max(abs(row - sr), abs(col - sc)) <= 2:
            status = 2

        # —— shed’s movement (only if awake & not caught) ———————
        if status == 2 and not caught:
            sr, sc = self._shed_next((sr, sc), (row, col), timer)
        
        timer -= 1
        if timer <=0:
            status = 0
        return tuple((row, col), orient, needles, caught, status, (sr, sc), timer)
    
    def _shed_next(self, pos, agent_pos, t):
        """
        Implements the pattern:
        even step  -> 2 tiles directly away from agent
        odd step   -> 2 tiles left (relative to agent)
        If a step is blocked by a tree or boundary, Shed skips it.
        """
        sr, sc = pos
        ar, ac = agent_pos
        phase  = (self.timer0 - t) % 2          # toggles 0 / 1 each turn
        moves  = []
        if phase == 0:
            dr = 1 if sr > ar else -1 if sr < ar else 0
            dc = 1 if sc > ac else -1 if sc < ac else 0
            moves = [(sr + dr, sc + dc), (sr + 2*dr, sc + 2*dc)]
        else:                                   # two steps to the agent's left
            # 'Left' vector depends on agent‑to‑shed direction
            lr, lc = -(ac - sc), ar - sr        # (dx,dy) rotated left
            moves = [(sr + lr, sc + lc), (sr + 2*lr, sc + 2*lc)]

        for r, c in moves:
            if 0 <= r < self.N and 0 <= c < self.N and (r, c) not in self.trees:
                sr, sc = r, c
        return sr, sc
    
    def _clear_line(self, A, B):
        """True iff A and B share row/col and no tree between them."""
        r1, c1 = A
        r2, c2 = B
        if r1 == r2:
            for c in range(min(c1,c2)+1, max(c1,c2)):
                if (r1,c) in self.Trees_location:
                    return False
            return True
        if c1 == c2:
            for r in range(min(r1,r2)+1, max(r1,r2)):
                if (r, c1) in self.Trees_location:
                    return False
                return True
        return False
    
    def action_cost(self, state, action, next_state):
        s = list(state)
        normal_actions = ['move-forward', 'turn-left', 'turn-right', 'pick']
        n = list(next_state)
        if n[6]<=0:
            return -1000
        if action in normal_actions:
            return -2 # -1 for the action and -1 for the timer
        if action == 'stay':
            return -3 # To discourage halts
        
    def is_goal(self, state):
        s = list(state)
        if s[5] == s.ambulance and s[4] == 1 and s[3] == True and s[6] > 0:
            return True
        else:
            False
    def h(self, node):
        pass
    