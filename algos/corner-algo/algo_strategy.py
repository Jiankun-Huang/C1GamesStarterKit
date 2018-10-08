import gamelib
import random
import math
import warnings
from sys import maxsize

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

Additional functions are made available by importing the AdvancedGameState 
class from gamelib/advanced.py as a replcement for the regular GameState class 
in game.py.

You can analyze action frames by modifying algocore.py.

The GameState.map object can be manually manipulated to create hypothetical 
board states. Though, we recommended making a copy of the map to preserve 
the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    
    def __init__(self):
        super().__init__()
        random.seed()
        # state variables
        self.useShockTroops = True
        self.attackedLastTurn = False
        self.lastEnemyHealth = 30
        self.troopDeploymentCoord = [13,0]
        self.rammingTroopsDeploymentCoord = [14,0]
        self.firstTurnTroopCoord = [25,11]

        self.attackRight = True
        self.reinforceRight = False
        self.reinforceLeft = False

        # main 'V' shape
        self.filter_left_leg_coords = [[2,13], [3,12], [4,11], [5,10], [6,9], [7,8], [8,7], [9,6], [10,5], [11, 4]] 
        self.filter_right_leg_coords = [[25,13], [24,12], [23,11], [22,10], [21,9], [20,8], [19,7], [18,6], [17,5], [16, 4]]
        # pick one corridoor
        self.filter_left_corridoor_coords = [[12,3], [13,2], [14,2], [15,2], [26,13], [27,13]]
        self.filter_right_corridoor_coords = [[15, 3], [14,2], [13,2], [12,2], [0,13], [1,13]]

        # build one per turn
        self.destroyer_funnel_coords = [[12,4], [15,4], [11,5], [16,5], [10,6], [17,6]]

        # reinforce when needed
        self.destroyer_left_leg_coords = [[3,13], [5, 11]]
        self.destroyer_right_leg_coords = [[24, 13], [22, 11]]

        # there has got to be a better way ...
        self.all_the_walls = [[2,13], [3,12], [4,11], [5,10], [6,9], [7,8], [8,7], [9,6], [10,5], [11, 4],
                              [25,13], [24,12], [23,11], [22,10], [21,9], [20,8], [19,7], [18,6], [17,5], [16, 4],
                              [12,3], [13,2], [14,2], [15,2],
                              [15, 3], [14,2], [13,2], [12,2],
                              [12,4], [15,4], [11,5], [16,5], [10,6], [17,6],
                              [3,13], [5, 11],
                              [24, 13], [22, 11]]

        # encryptor on offense
        self.encrypt_left_leg_coord = [4, 12]
        self.encrypt_right_leg_coord = [23, 12]
        

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]


    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        if game_state.turn_number == 0:
            while game_state.can_spawn(PING, self.firstTurnTroopCoord):
                game_state.attempt_spawn(PING, self.firstTurnTroopCoord)
            # no building this turn
        else:
            #if shock troops aren't successful, go with the bruisers
            if game_state.get_resource(game_state.BITS) >= 8:
                self.attackedLastTurn = True
                #while (len(gamelib.advanced_game_state.AdvancedGameState.get_attackers(game_state, self.troopDeploymentCoords, 0)) > 0):
                #    self.moveDeploymentAway()

                self.deployRammingTroops(game_state)
                self.deployTroops(game_state)
            self.buildWalls(game_state)
            # this doesn't work yet!
            #self.markForRefund(game_state)

        game_state.submit_turn()

    def deployRammingTroops(self, game_state):
        gamelib.debug_write('Sending Ramming Troops!')
        for x in range(4):
            game_state.attempt_spawn(PING, self.rammingTroopsDeploymentCoord)

    def deployTroops(self, game_state):
        gamelib.debug_write('Sending Troops!')
        while game_state.can_spawn(PING, self.troopDeploymentCoord):
            game_state.attempt_spawn(PING, self.troopDeploymentCoord)

    def markForRefund(self, game_state):
        # if any firewalls have less than half stability, mark for removal
        for location in self.all_the_walls:
            x = location[0]
            y = location[1]
            if (game_state.game_map.in_arena_bounds(location)):
                unit = game_state.game_map[x,y][0]
                if unit.stability < 35:
                    game_state.attempt_remove(location)
            else:
                gamelib.debug_write('Out of bounds? {}', location)

    def buildWalls(self, game_state):
        # always want leg walls built
        for location in self.filter_left_leg_coords:
            if (game_state.can_spawn(FILTER, location)):
                game_state.attempt_spawn(FILTER, location)
                if game_state.turn_number != 1:
                    self.reinforceLeft = True
        for location in self.filter_right_leg_coords:
            if (game_state.can_spawn(FILTER, location)):
                game_state.attempt_spawn(FILTER, location)
                if game_state.turn_number != 1:
                    self.reinforceRight = True

        if self.attackRight:
            for location in self.filter_right_corridoor_coords:
                if (game_state.can_spawn(FILTER, location)):
                    game_state.attempt_spawn(FILTER, location)
        else:
            for location in self.filter_left_corridoor_coords:
                if (game_state.can_spawn(FILTER, location)):
                    game_state.attempt_spawn(FILTER, location)
        
        if self.reinforceLeft:
            for location in self.destroyer_left_leg_coords:
                if (game_state.can_spawn(DESTRUCTOR, location)):
                    game_state.attempt_spawn(DESTRUCTOR, location)

        if self.reinforceRight:
            for location in self.destroyer_right_leg_coords:
                if (game_state.can_spawn(DESTRUCTOR, location)):
                    game_state.attempt_spawn(DESTRUCTOR, location)

        for location in self.destroyer_funnel_coords:
            if (game_state.can_spawn(DESTRUCTOR, location)):
                game_state.attempt_spawn(DESTRUCTOR, location)


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
