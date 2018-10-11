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
class Sides:
    LEFT = 1
    RIGHT = 2

class Army:
    def __init__(self):
        self.IsAttackRecommended = True
        self.RammingPings = 0
        self.AttackingPings = 0
        self.AttackingEMPs = 0
    
    def Strategize(self, defendingCoords, bitsToSpend):

        return self.IsAttackRecommended


class AlgoStrategy(gamelib.AlgoCore):
    
    def __init__(self):
        super().__init__()
        random.seed()

        self.readyToAttack = False
        self.useShockTroops = True
        self.attackedLastTurn = False
        self.lastEnemyHealth = 30
        self.troopDeploymentCoord = [13,0]
        self.rammingTroopsDeploymentCoord = [14,0]
        self.firstTurnTroopCoord = [13,0]
        self.predictedNewAttackers = 0
        # ramming troops are only needed if there is no short path
        self.useRammingTroops = False

        self.sideToAttack = Sides.RIGHT
        self.reinforceRight = False
        self.reinforceLeft = False

        # left corner
        self.enemy_left_corner_area = [[0,14], [1,14], [2,14], [3,14], [4,14], [5,14], [6,14]]
        self.enemy_right_corner_area = [[27,14], [26,14], [25,14], [24,14], [23,14], [22,14], [21,14]]
        # main 'V' shape
        self.filter_left_leg_coords = [[2,13], [3,12], [4,11], [5,10], [6,9], [7,8], [8,7], [9,6], [10,5], [11, 4]] 
        self.filter_right_leg_coords = [[25,13], [24,12], [23,11], [22,10], [21,9], [20,8], [19,7], [18,6], [17,5], [16, 4]]
        # pick one corridoor
        self.overlapping_cooridoor_coords = [[14, 2], [13, 2]]
        self.filter_left_corridoor_coords = [[12,3], [15,2], [26,13], [27,13]]
        self.filter_right_corridoor_coords = [[15, 3], [12,2], [0,13], [1,13]]

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
        game_state = gamelib.AdvancedGameState(self.config, turn_state)
        p1UnitCount = len(self.jsonState.get('p1Units')[0])
        p2UnitCount = len(self.jsonState.get('p2Units')[0])
        #gamelib.debug_write('p1 has {} units. p2 has {} units'.format(p1UnitCount, p2UnitCount))

        if game_state.turn_number == 0:
            while game_state.can_spawn(PING, self.firstTurnTroopCoord):
                game_state.attempt_spawn(PING, self.firstTurnTroopCoord)
            # no building this turn
        else:
            left_corner_stats = game_state.get_area_stats(self.enemy_left_corner_area)
            gamelib.debug_write('left_corner_stats = {}'.format(left_corner_stats))
            right_corner_stats = game_state.get_area_stats(self.enemy_right_corner_area)
            gamelib.debug_write('right_corner_stats = {}'.format(right_corner_stats))

            if game_state.get_resource(game_state.BITS) >= 8:
                self.readyToAttack = True
            else:
                self.readyToAttack = False

            # determine which side is more vulnerable
            if left_corner_stats.destructor_count < right_corner_stats.destructor_count:
                self.SetSideToAttack(Sides.LEFT, game_state)
            else:
                self.SetSideToAttack(Sides.RIGHT, game_state)

            if self.readyToAttack:
                if self.useRammingTroops:
                    self.deployRammingTroops(game_state)
                self.deployTroops(game_state)

            self.buildWalls(game_state)
            self.markForRefund(game_state)

        game_state.submit_turn()

    def SetSideToAttack(self, newSide, game_state):
        if not self.sideToAttack == newSide:
            gamelib.debug_write('Attack the other side!')
            self.readyToAttack = False
            self.sideToAttack = newSide
            self.SwitchAttackCooridoor(game_state)
            if self.sideToAttack == Sides.LEFT:
                self.troopDeploymentCoord = [14,0]
                self.rammingTroopsDeploymentCoord = [13,0]
            else:
                self.troopDeploymentCoord = [13,0]
                self.rammingTroopsDeploymentCoord = [14,0]
    
    def SwitchAttackCooridoor(self, game_state):
        if self.sideToAttack == Sides.LEFT:
            coordsToRemove = self.filter_right_corridoor_coords
        else:
            coordsToRemove = self.filter_left_leg_coords

        for location in coordsToRemove:
            game_state.attempt_remove(location)

    def deployRammingTroops(self, game_state):
        gamelib.debug_write('Sending Ramming Troops!')
        for x in range(4):
            game_state.attempt_spawn(PING, self.rammingTroopsDeploymentCoord)

    def deployTroops(self, game_state):
        gamelib.debug_write('Sending Troops!')
        while game_state.can_spawn(PING, self.troopDeploymentCoord):
            game_state.attempt_spawn(PING, self.troopDeploymentCoord)
        # it's bad to prioritize this over other walls, this should be moved!
        if (game_state.get_resource(game_state.BITS) >= 7 and game_state.can_spawn(ENCRYPTOR, self.encrypt_right_leg_coord)):
                game_state.attempt_spawn(ENCRYPTOR, self.encrypt_right_leg_coord)

    def markForRefund(self, game_state):
        # if any firewalls have less than half stability, mark for removal
        for location in self.all_the_walls:
            x, y = location
            if (game_state.game_map.in_arena_bounds(location)):
                for unit in game_state.game_map[x,y]:
                    if unit.stability < 35:
                        game_state.attempt_remove(location)

    def buildWalls(self, game_state):
        if self.reinforceLeft:
            for location in self.destroyer_left_leg_coords:
                if (game_state.can_spawn(DESTRUCTOR, location)):
                    game_state.attempt_spawn(DESTRUCTOR, location)

        if self.reinforceRight:
            for location in self.destroyer_right_leg_coords:
                if (game_state.can_spawn(DESTRUCTOR, location)):
                    game_state.attempt_spawn(DESTRUCTOR, location)

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

        for location in self.overlapping_cooridoor_coords:
            if (game_state.can_spawn(FILTER, location)):
                    game_state.attempt_spawn(FILTER, location)

        if self.sideToAttack == Sides.RIGHT:
            for location in self.filter_right_corridoor_coords:
                if (game_state.can_spawn(FILTER, location)):
                    game_state.attempt_spawn(FILTER, location)
        else:
            for location in self.filter_left_corridoor_coords:
                if (game_state.can_spawn(FILTER, location)):
                    game_state.attempt_spawn(FILTER, location)
        
        for location in self.destroyer_funnel_coords:
            if (game_state.can_spawn(DESTRUCTOR, location)):
                game_state.attempt_spawn(DESTRUCTOR, location)


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
