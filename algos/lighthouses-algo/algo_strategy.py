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
        self.attackWithPings = True
        self.attackedLastTurn = False
        self.lastEnemyHealth = 30
        self.troopDeploymentCoords = [13,0]
        # maybe this magical cooridoor is suicide, but we'll see!
        self.reservedCoords = [
            [22,10],[23,10]
        ]
        self.buildCastleWall = False
        self.castleWallRow = 0
        self.scramblerCoords = [[4,9], [8,5], [13,0], [17, 3], [21,7]]
        self.pingCoord = [3, 10]
        self.cornerTowers = [
            [2, 11],[25, 11]
        ]
        self.cornerFilters = [
            [0, 13],[1, 12],[2, 12],[25, 12],[26, 12],[27, 13]
        ]
        self.lightHouseTowers = [
            [9, 10],[19, 10],[11, 10],[17, 10],[7, 10]
        ]
        self.filterWall = [
            [3, 11],[4, 11],[5, 11],[13, 11],[14, 11],[15, 11]
        ]
        self.tunnelTowers = [
            [24, 10],[23, 9],[22, 8]
        ]
        self.cornerPhaseTwo = [
            [25, 13],[26, 13],[1, 13],[2, 13]
        ]
        self.encryptorPhaseOne = [
            [21, 8],[21, 7]
        ]
        self.row_ten = []
        for x in range(22):
            self.row_ten.append([24 - x, 10])
        self.encryptorPhaseTwo = [
            [20, 8],[20, 7],[20, 6],
            [19, 8],[19, 7],[19, 6],
            [18, 8],[18, 7],[18, 6]
        ]
        
        
        

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        super().on_game_start(config)
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
        game_state = gamelib.AdvancedGameState(self.config, turn_state)
        #p1UnitCount = len(self.jsonState.get('p1Units')[0])
        p2UnitCount = len(self.jsonState.get('p2Units')[0]) + len(self.jsonState.get('p2Units')[1]) + len(self.jsonState.get('p2Units')[2])
        gamelib.debug_write('p2 has {} units'.format(p2UnitCount))
        
        shouldRebuild = game_state.turn_number > 7
        needsStrongerCorners = game_state.turn_number > 3            

        self.buildFirewalls(game_state, self.cornerTowers, DESTRUCTOR, shouldRebuild)
        if needsStrongerCorners:
            self.buildFirewalls(game_state, self.cornerFilters, DESTRUCTOR, shouldRebuild)
        else:
            self.buildFirewalls(game_state, self.cornerFilters, FILTER, shouldRebuild)
        self.buildFirewalls(game_state, self.lightHouseTowers, DESTRUCTOR, shouldRebuild)
        self.reinforceDestructors(game_state, self.lightHouseTowers, shouldRebuild)
        self.buildFirewalls(game_state, self.filterWall, FILTER, shouldRebuild)
        self.buildFirewalls(game_state, self.tunnelTowers, DESTRUCTOR, shouldRebuild)
        self.buildFirewalls(game_state, self.cornerPhaseTwo, FILTER, shouldRebuild)
        self.buildFirewalls(game_state, self.encryptorPhaseOne, ENCRYPTOR, False)
        self.buildFirewalls(game_state, self.row_ten, DESTRUCTOR, False)
        self.buildFirewalls(game_state, self.encryptorPhaseTwo, ENCRYPTOR, False)


        if self.attackWithPings:
            if game_state.number_affordable(PING) >= 8 + (game_state.turn_number // 10):
                self.attackForMaxPain(game_state)
                if game_state.turn_number > 4:
                    self.attackWithPings = False
        else:
            if game_state.number_affordable(EMP) > 2 + (game_state.turn_number // 18):
                self.attackForMaxDestruction(game_state)
                self.attackWithPings = True

        game_state.submit_turn()

    def reinforceDestructors(self, game_state, locations, rebuildAsNeeded):
        for location in locations:
            x, y = location
            oneForward = [x, y + 1]
            if rebuildAsNeeded:
                self.checkForRefund(game_state, oneForward)
            if oneForward not in self.reservedCoords:
                if game_state.can_spawn(FILTER, oneForward):
                    game_state.attempt_spawn(FILTER, oneForward)
        
        for location in locations:
            x, y = location
            oneRight = [x + 1, y]
            if rebuildAsNeeded:
                self.checkForRefund(game_state, oneRight)
            if oneRight not in self.reservedCoords:
                if game_state.can_spawn(FILTER, oneRight):
                    game_state.attempt_spawn(FILTER, oneRight)

        for location in locations:
            x, y = location
            oneLeft = [x - 1, y]
            if rebuildAsNeeded:
                self.checkForRefund(game_state, oneLeft)
            if oneLeft not in self.reservedCoords:
                if game_state.can_spawn(FILTER, oneLeft):
                    game_state.attempt_spawn(FILTER, oneLeft)
    
    def buildFirewalls(self, game_state, locations, unit_type, rebuildAsNeeded):
        for location in locations:
            if location not in self.reservedCoords:
                if rebuildAsNeeded:
                    self.checkForRefund(game_state, location)
                if game_state.can_spawn(unit_type, location):
                    game_state.attempt_spawn(unit_type, location)

    def checkForRefund(self, game_state, location):
        x, y = location
        for unit in game_state.game_map[x,y]:
            if unit.stability < 35:
                game_state.attempt_remove(location)

    
 
    def reinforceBreachLocation(self, game_state):
        # I don't know if I want this reversed or not
        for breach in reversed(self.breach_list):
            for x in range(3):
                for location in game_state.game_map.get_locations_in_range(breach, x):
                    x, y = location
                    for unit in game_state.game_map[x,y]:
                        if unit.stability < 35:
                            game_state.attempt_remove(location)
                    #gamelib.debug_write('Want to build DEST at {}'.format(location))
                    if game_state.can_spawn(DESTRUCTOR, location) and location not in self.reservedCoords:
                        game_state.attempt_spawn(DESTRUCTOR, location)

    def attackForMaxPain(self, game_state):
        deployLocation = [13, 0]
        lowestPathRisk = 10
        
        for startLocation in game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT):
            if game_state.can_spawn(PING, startLocation) and len(game_state.get_attackers(startLocation, 0)) == 0:
                path = game_state.find_path_to_edge(startLocation, game_state.game_map.TOP_RIGHT)
                pathRisk = 0
                for step in path:
                    pathRisk += len(game_state.get_attackers(step, 0))
                
                if pathRisk < lowestPathRisk:
                    lowestPathRisk = pathRisk
                    deployLocation = startLocation

        for startLocation in game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT):
            if game_state.can_spawn(PING, startLocation) and len(game_state.get_attackers(startLocation, 0)) == 0:
                path = game_state.find_path_to_edge(startLocation, game_state.game_map.TOP_LEFT)
                pathRisk = 0
                for step in path:
                    pathRisk += len(game_state.get_attackers(step, 0))
                
                if pathRisk < lowestPathRisk:
                    lowestPathRisk = pathRisk
                    deployLocation = startLocation

        gamelib.debug_write('Lowest risk path value = {}'.format(lowestPathRisk))

        while game_state.can_spawn(PING, deployLocation):
            game_state.attempt_spawn(PING, deployLocation)

    def attackForMaxTargets(self, game_state):
        deployLocation = [13, 0]
        bestPathValue = 0
        targetEdge = game_state.game_map.TOP_RIGHT

        # don't want to start in range of a destructor
        for startLocation in game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT):
            if game_state.can_spawn(EMP, startLocation) and len(game_state.get_attackers(startLocation, 0)) == 0:
                path = game_state.find_path_to_edge(startLocation, game_state.game_map.TOP_RIGHT)
                pathValue = game_state.get_target_count_for_EMP_locations(path)
                if pathValue > bestPathValue:
                    bestPathValue = pathValue
                    deployLocation = startLocation
                    targetEdge = game_state.game_map.TOP_RIGHT
        for startLocation in game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT):
            if game_state.can_spawn(EMP, startLocation) and len(game_state.get_attackers(startLocation, 0)) == 0:
                path = game_state.find_path_to_edge(startLocation, game_state.game_map.TOP_LEFT)
                pathValue = game_state.get_target_count_for_EMP_locations(path)
                if pathValue > bestPathValue:
                    bestPathValue = pathValue
                    deployLocation = startLocation
                    targetEdge = game_state.game_map.TOP_LEFT

        gamelib.debug_write('Best path value = {}'.format(bestPathValue))
        while game_state.can_spawn(EMP, deployLocation):
            game_state.attempt_spawn(EMP, deployLocation)

    def attackForMaxDestruction(self, game_state):
        deployLocation = [13, 0]
        bestPathValue = 0
        targetEdge = game_state.game_map.TOP_RIGHT

        # don't want to start in range of a destructor
        for startLocation in game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT):
            if game_state.can_spawn(EMP, startLocation) and len(game_state.get_attackers(startLocation, 0)) == 0:
                path = game_state.find_path_to_edge(startLocation, game_state.game_map.TOP_RIGHT)
                #pathValue = game_state.get_target_count_for_EMP_locations(path) - game_state.get_attacker_count_for_locations(path)
                pathValue = game_state.get_free_target_count_for_EMP_locations(path)
                if pathValue > bestPathValue:
                    bestPathValue = pathValue
                    deployLocation = startLocation
                    targetEdge = game_state.game_map.TOP_RIGHT
        for startLocation in game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT):
            if game_state.can_spawn(EMP, startLocation) and len(game_state.get_attackers(startLocation, 0)) == 0:
                path = game_state.find_path_to_edge(startLocation, game_state.game_map.TOP_LEFT)
                #pathValue = game_state.get_target_count_for_EMP_locations(path) - game_state.get_attacker_count_for_locations(path)
                pathValue = game_state.get_free_target_count_for_EMP_locations(path)
                if pathValue > bestPathValue:
                    bestPathValue = pathValue
                    deployLocation = startLocation
                    targetEdge = game_state.game_map.TOP_LEFT

        gamelib.debug_write('Best path value = {}'.format(bestPathValue))

        
        if game_state.number_affordable(EMP) > 2:
            path = game_state.find_path_to_edge(deployLocation, targetEdge)
            x, y = path[len(path) - 1] 
            if y >= 13:
                ''' # ENCRYPTORs have not been useful yet
                if game_state.number_affordable(ENCRYPTOR) > 0:
                    # find a good place to put it!
                    encryptorPlaced = False
                    for step in game_state.find_path_to_edge(deployLocation, targetEdge):
                        x, y = step
                        if y == 13 and not encryptorPlaced:
                            if game_state.can_spawn(ENCRYPTOR, [x-1,y]):
                                game_state.attempt_spawn(ENCRYPTOR, [x-1,y])
                                encryptorPlaced = True
                            elif game_state.can_spawn(ENCRYPTOR, [x+1,y]):
                                game_state.attempt_spawn(ENCRYPTOR, [x+1,y])
                                encryptorPlaced = True
                            else:
                                gamelib.debug_write('Wanted to spawn encryptor but could not find suitable location!')
                '''

                while game_state.can_spawn(EMP, deployLocation):
                    game_state.attempt_spawn(EMP, deployLocation)
            else:
                gamelib.debug_write('No path outside our territory, NOT DEPLOYING TROOPS')
                for x in range(4):
                    game_state.attempt_remove([20, 13 - x])

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
