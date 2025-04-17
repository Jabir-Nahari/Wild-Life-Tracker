class Jungle_Environment:
    def __init__(self, N, ambulance, F_orientation, Trees_location, Shed_init_locaiton, Shed_status, Needle_num):
        self.N = N
        self.ambulance = ambulance
        self.Trees_location = Trees_location
        self.Shed_init_location = Shed_init_locaiton
        self.Shed_status = Shed_status
        self.Needle_num = Needle_num
        self.F_orientation = F_orientation
        self.state = (self.ambulance, self.F_orientation, self.Needle_num, False, 2, self.Shed_init_location)

    def action(self, state):
        available_actions = ['move-forward', 'turn-left', 'turn-right', 'throw-needle', 'pick', 'stay']
        '''dealing with (move-forward) action'''
        s = list(state)
        actions = {
            'up': lambda x: (x[0]+1, x[1]),
            'down': lambda x: (x[0]-1, x[1]),
            'right': lambda x: (x[0], x[1]+1),
            'left': lambda x: (x[0], x[1]-1)
        }
        new_location = actions.get(s[1])(s[0])
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
        pass
    def action_cost(self, state, action, next_state):
        pass
    def is_goal(self, state):
        pass
    def h(self, node):
        pass
    