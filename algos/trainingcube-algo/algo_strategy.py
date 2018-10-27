import gamelib
import random
import math
import warnings
import copy
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
        self.lastEnemyArmyDict = {}
        self.troopDeploymentCoords = [13,0]
        # maybe this magical cooridoor is suicide, but we'll see!
        self.reservedCoords = [
            [22,10],[23,10]
        ]
        self.useRightDoor = True
        self.coresToSpendOnRebuilding = 0
        self.castleWallRow = 0
        self.turnZeroScramblerCoord = [7, 6]
        self.turnZeroEMPCoord = [20, 6]
        
        self.turnZeroTowers = [
            [3, 11],[24, 11]
        ]
        self.filterCorners = [
            [0, 13],[1, 12],[2, 11],[27, 13],[26, 12],[25, 11]
        ]
        self.leftDoorTowers = [
            [5, 11],[20, 11],[16, 11],[12, 11],[8, 11]
        ]
        self.leftDoorFilters = [
            [23, 11],[22, 11],[21, 11],[19, 11],[18, 11],[17, 11],[15, 11],[14, 11],[13, 11],
            [11, 11],[10, 11],[9, 11],[7, 11],[6, 11]
        ]
        self.leftExtraCornerTower = [
            [2, 12]
        ]
        self.leftRearHallway = [
            [3, 10],[4, 9],[5, 9],[6, 9],[7, 9],[8, 9]
        ]
        self.leftFrontWall = []
        for x in range(24):
            self.leftFrontWall.append([1 + x, 13])
        self.leftEncryptors = [
            [21, 9],[5, 8],[9, 9],[15, 9],[11, 9],[13, 9],[17, 9],[19, 9],[23, 9]
        ]

        self.rightDoorTowers = [
            [22, 11],[7, 11],[11, 11],[15, 11],[19, 11]
        ]
        self.rightDoorFilters = [
            [4, 11],[5, 11],[6, 11],[8, 11],[9, 11],[10, 11],[12, 11],[13, 11],[14, 11],
            [16, 11],[17, 11],[18, 11],[20, 11],[21, 11]
        ]
        self.rightRearHallway = [
            [24, 10],[23, 9],[22, 9],[21, 9],[20, 9],[19, 9]
        ]
        self.rightExtraCornerTower = [
            [25, 12]
        ]
        self.rightFrontWall = []
        for x in range(24):
            self.rightFrontWall.append([26 - x,13])
        self.rightEncryptors = [
            [22, 8],[6, 9],[18, 9],[12, 9],[16, 9],[14, 9],[10, 9],[8, 9],[4, 9]
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
        p1UnitCount = len(self.jsonState.get('p1Units')[0]) + len(self.jsonState.get('p1Units')[1]) + len(self.jsonState.get('p1Units')[2])
        p2UnitCount = len(self.jsonState.get('p2Units')[0]) + len(self.jsonState.get('p2Units')[1]) + len(self.jsonState.get('p2Units')[2])
        gamelib.debug_write('p2 has {} units'.format(p2UnitCount))
        gamelib.debug_write('p2 army cost last turn = {}'.format(self.enemy_army_cost))
        
        if self.army_dict.get('total_cost', 0) > 0:
            self.lastEnemyArmyDict = self.army_dict.copy()
        
        if 'total_cost' in self.lastEnemyArmyDict and game_state.get_resource(game_state.BITS, 1) >= self.lastEnemyArmyDict['total_cost']:
            gamelib.debug_write('I predict that p2 will spawn an army this turn!')
        
        encryptorCount = len(self.jsonState.get('p1Units')[1])
        #if game_state.turn_number % 4 == 0:
        #    if game_state.can_spawn(ENCRYPTOR, [2 + 2 * encryptorCount, 11]):
        #        game_state.attempt_spawn(ENCRYPTOR, [2 + 2 * encryptorCount, 11])

        for x in range(26):
            self.checkForRefund(game_state, [x, 13])
            if x % 3 == 0:
                if game_state.can_spawn(DESTRUCTOR, [x, 13]):
                    game_state.attempt_spawn(DESTRUCTOR, [x, 13])
            else:
                if game_state.can_spawn(FILTER, [x, 13]):
                    game_state.attempt_spawn(FILTER, [x, 13])

        spawnCoord = [3, 10]
        if game_state.turn_number == 0:
            spawnCoord = [1, 12]
        
        while game_state.can_spawn(EMP, spawnCoord):
            game_state.attempt_spawn(EMP, spawnCoord)

        # reset the dictionary for the next analysis
        self.army_dict['total_count'] = 0
        self.army_dict['total_cost'] = 0
        self.army_dict['ping_count'] = 0
        self.army_dict['EMP_count'] = 0
        self.army_dict['scrambler_count'] = 0
        self.enemy_spawns.clear()
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
    
    def buildFirewalls(self, game_state, locations, unit_type, rebuildAsNeeded, maxToBuild = 100):
        numberBuilt = 0
        for location in locations:
            if location not in self.reservedCoords:
                if rebuildAsNeeded:
                    self.checkForRefund(game_state, location)
                if game_state.can_spawn(unit_type, location):
                    game_state.attempt_spawn(unit_type, location)
                    numberBuilt += 1
                    if numberBuilt >= maxToBuild:
                        return

    def checkForRefund(self, game_state, location):
        x, y = location
        for unit in game_state.game_map[x,y]:
            if unit.stability < 35 and self.coresToSpendOnRebuilding >= unit.cost:
                game_state.attempt_remove(location)
                self.coresToSpendOnRebuilding -= unit.cost

    
 
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
        lowestPathRisk = 1000
        
        for startLocation in game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT):
            #if game_state.can_spawn(PING, startLocation) and len(game_state.get_attackers(startLocation, 0)) == 0:
            if game_state.can_spawn(PING, startLocation):
                path = game_state.find_path_to_edge(startLocation, game_state.game_map.TOP_RIGHT)
                lastX, lastY = path[-1]
                # need to make it at least to the edge of our map to be considered!
                if lastY >= 13:
                    pathRisk = 0
                    #gamelib.debug_write('STARTING FROM {}'.format(path[0]))
                    for step in path:
                        attackers = len(game_state.get_attackers(step, 0))
                        #gamelib.debug_write('{} - attackers={}'.format(step, attackers))
                        pathRisk += attackers
                    
                    if pathRisk < lowestPathRisk:
                        lowestPathRisk = pathRisk
                        deployLocation = startLocation

        for startLocation in game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT):
            #if game_state.can_spawn(PING, startLocation) and len(game_state.get_attackers(startLocation, 0)) == 0:
            if game_state.can_spawn(PING, startLocation):
                path = game_state.find_path_to_edge(startLocation, game_state.game_map.TOP_LEFT)
                lastX, lastY = path[-1]
                # need to make it at least to the edge of our map to be considered!
                if lastY >= 13:
                    pathRisk = 0
                    #gamelib.debug_write('STARTING FROM {}'.format(path[0]))
                    for step in path:
                        attackers = len(game_state.get_attackers(step, 0))
                        #gamelib.debug_write('{} - attackers={}'.format(step, attackers))
                        pathRisk += attackers
                    
                    if pathRisk < lowestPathRisk:
                        lowestPathRisk = pathRisk
                        deployLocation = startLocation

        gamelib.debug_write('Lowest risk path value = {}'.format(lowestPathRisk))

        while game_state.can_spawn(PING, deployLocation):
            game_state.attempt_spawn(PING, deployLocation)

        return lowestPathRisk

    def attackForMaxTargets(self, game_state):
        if self.useRightDoor:
            deployLocation = [3, 10]
        else:
            deployLocation = [24, 10]
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
        
        path = game_state.find_path_to_edge(deployLocation, targetEdge)
        x, y = path[len(path) - 1] 
        if y >= 13:
            while game_state.can_spawn(EMP, deployLocation):
                game_state.attempt_spawn(EMP, deployLocation)
        else:
            gamelib.debug_write('No path outside our territory, NOT DEPLOYING TROOPS')
        
        return bestPathValue

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
