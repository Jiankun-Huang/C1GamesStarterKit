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
        self.troopDeploymentCoords = [13,0]

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
        
        if game_state.turn_number < 6:
            self.buildLeftTowers(game_state)
            self.buildRightTowers(game_state)
        else:
            self.sellRightTowers(game_state)
        
        game_state.submit_turn()

    def sellRightTowers(self, game_state):
        coordsToRemove = [[25, 13], [26, 13], [27, 13], [26, 12]]
        for location in coordsToRemove:
            game_state.attempt_remove(location)

    def buildRightTowers(self, game_state):
        # right-side towers
        right_side_towers = [[25, 13], [26, 13], [27, 13], [26, 12]]

        for location in right_side_towers:
            if game_state.can_spawn(DESTRUCTOR, location):
                game_state.attempt_spawn(DESTRUCTOR, location)

    def buildLeftTowers(self, game_state):    
        # left-side towers
        left_side_towers = [[0, 13], [1, 13], [2, 13], [1, 12]]
        
        for location in left_side_towers:
            if game_state.can_spawn(DESTRUCTOR, location):
                game_state.attempt_spawn(DESTRUCTOR, location)
    

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
