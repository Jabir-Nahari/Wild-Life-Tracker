class Jungle_Environment:
    _ORIENT_LEFT  = {'up':'left',  'left':'down', 'down':'right', 'right':'up'}  # given up (for example) - if i turn left what is my orient
    _ORIENT_RIGHT = {v:k for k,v in _ORIENT_LEFT.items()} # given up (for example) - if i turn left what is my orient
    _FWD_DELTA    = {'up':(-1,0), 'down':(1,0), 'left':(0,-1), 'right':(0,1)}

    def __init__(self, N, ambulance, F_orientation, Needle_num,Shed_init_locaiton, Trees_location):
        self.N = N
        self.ambulance = ambulance
        self.F_orientation = F_orientation
        self.Needle_num = Needle_num
        # Caught (True -> Shed is Caught), (False -> Shed is not Caught yet)
        # Shed status (3 -> drugged sleep), (2 -> awake), (1 -> initial sleep)
        self.Shed_init_location = Shed_init_locaiton
        self.Trees_location = Trees_location
        self.phase_toggle = 0  # start with even phase
        self.initial_state = (self.ambulance, self.F_orientation, self.Needle_num, False, 1, self.Shed_init_location)

    def actions(self, state):
        available_actions = ['move-forward', 'turn-left', 'turn-right', 'throw-needle', 'pick', 'stay']
        '''dealing with (move-forward) action'''
        (row, col), orient, needles, caught, status, (sr, sc) = state
        dr, dc = Jungle_Environment._FWD_DELTA[orient]
        new_location = (row+dr, col+dc)
        if new_location in self.Trees_location:
            available_actions.remove('move-forward')
        elif new_location[0] >= self.N or new_location[0] < 0:
            available_actions.remove('move-forward')
        elif new_location[1] >= self.N or new_location[1] < 0:
            available_actions.remove('move-forward')
        '''dealing with (pick) action'''
        if (row, col) != (sr, sc) or caught:
            available_actions.remove('pick')
        '''dealing with (throw-needle)'''
        if needles <= 0:
            available_actions.remove('throw-needle')
        '''return the set of actions available'''
        return available_actions

    
    def result(self, state, action):
        # 1) Unpack
        (row, col), orient, needles, caught, status, (sr, sc) = state
        
        """
        state = (agent_loc, orient, needles, caught, shed_status, shed_loc)
        
        agent_loc   = (row, col)
        orient      = 'up'|'down'|'left'|'right'
        needles     = int
        caught      = bool
        shed_status = 1|2|3
        shed_loc    = (sr, sc)

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
            if 0 <= nr < self.N and 0 <= nc < self.N and (nr, nc) not in self.Trees_location:
                (row, col) = (nr, nc)
                # if Shed is caught by the agent, then when the agent moves, Shed also moves along with him
                if caught:
                    sr, sc = row, col
        elif action == 'throw-needle':
            needles -= 1
            # if Shed is in line‑of‑sight, put it into drugged sleep mode
            if self._clear_line((row, col), (sr, sc), orient):
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

        # shed’s movement (only if awake & not caught)
        if status == 2 and not caught:
            sr, sc = self._shed_next((sr, sc), (row, col), self.phase_toggle)

        self.phase_toggle = 1 - self.phase_toggle
        return (row, col), orient, needles, caught, status, (sr, sc)
    
    def _shed_next(self, pos, agent_pos, phase):
        """
        Implements the pattern:
        even step  -> 2 tiles directly away from agent
        odd step   -> 2 tiles left (relative to agent)
        If a step is blocked by a tree or boundary, Shed skips it.
        """
        sr, sc = pos
        ar, ac = agent_pos
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
            if 0 <= r < self.N and 0 <= c < self.N and (r, c) not in self.Trees_location:
                sr, sc = r, c
        return sr, sc
    
    def _clear_line(self, A, B, orient):
        """True iff A and B share row/col and no tree between them and A is looking toward B."""
        ra, ca = A
        rb, cb = B
        if ra == rb and ca == cb:
            return True
        if ra == rb:
            expected_orient = 'right' if ca<cb else 'left'
            for c in range(min(ca,cb)+1, max(ca,cb)):
                if (ra,c) in self.Trees_location:
                    return False
            return orient == expected_orient
        if ca == cb:
            expected_orient = 'down' if ra<rb else 'up'
            for r in range(min(ra,rb)+1, max(ra,rb)):
                if (r, ca) in self.Trees_location:
                    return False
            return orient == expected_orient
        return False
    
    def action_cost(self, state, action, next_state):
        """
        Assigns a cost to each action based on its utility.
        Encourages efficient, purposeful moves and punishes ineffective ones.
        """
        (row, col), orient, needles, caught, status, (sr, sc) = state

        # Valid needle throw if Shed is in line of sight and awake
        is_valid_throw = (
            action == 'throw-needle' and
            status != 3 and
            needles > 0 and
            self._clear_line((row, col), (sr, sc), orient)
        )

        # Attempted pickup when on top of tranquilized Shed
        is_valid_pick = (
            action == 'pick' and
            (row, col) == (sr, sc) and
            not caught and
            status == 3
        )

        # Action costs
        if action == 'move-forward':
            return 1  # Basic movement
        elif action in ('turn-left', 'turn-right'):
            return 2  # Slightly discouraged turning
        elif action == 'throw-needle':
            if is_valid_throw:
                return 2  # Reasonable cost for a good throw
            else:
                return 100  # Bad throw: penalty for wasting a needle
        elif action == 'pick':
            if is_valid_pick:
                return 1  # Efficient and successful pickup
            else:
                return 50  # Penalize useless or invalid pickup
        elif action == 'stay':
            return 10  # Discourage idle actions

        return 5  # Default for any other custom/unknown actions

        
    def is_goal(self, state):
        (row, col), _, _, caught, _, _ = state
        return caught and (row, col) == self.ambulance

    def h(self, node):
        (row, col), _, _, caught, status, (srow, scol) = node.state

        if self.is_goal(node.state):
            return 0
        if caught:
            # Need to walk home
            return abs(row - self.ambulance[0]) + abs(col - self.ambulance[1])
        elif status == 3:
            # Need to walk to Shed and pick up
            return abs(row - srow) + abs(col - scol) + abs(srow - self.ambulance[0]) + abs(scol - self.ambulance[1])
        else:
            # Need to tranquilize and then return
            return abs(row - srow) + abs(col - scol) + 2 + abs(srow - self.ambulance[0]) + abs(scol - self.ambulance[1])


            

            

        

        
        
        
    