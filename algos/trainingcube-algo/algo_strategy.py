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
        self.reservedCoords = [
        ]
        self.spawnBlacklist = [
        ]
        self.useRightDoor = True
        self.coresToSpendOnRebuilding = 0
        self.castleWallRow = 0
        self.turnZeroScramblerCoord = [7, 6]
        self.turnZeroEMPCoord = [20, 6]
        self.earlyEncryptorBuilt = False
        
        self.possibleRightSpawnCoords = [
        ]
        self.possibleLeftSpawnCoords = [
        ]

        self.leftSidePartOneCoords = [

        ]
        self.leftSidePartTwoCoords = [

        ]
        self.mainFilterSideCoords = [
            [1, 13],[3, 13],[4, 13],[5, 13],[22, 13],[23, 13],[24, 13],[26, 13],[3, 12],[24, 12]
        ]
        self.mainTowerSideCoords = [
            [6, 11],[21, 11],[2, 13],[25, 13]
        ]
        self.middleTowerCoords = [
            [12, 10], [15, 10]
        ]
        self.leftEncryptorCoords = [

        ]
        self.rightEncryptorCoords = [

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
        
        shouldRebuild = game_state.turn_number > 3
        shouldRebuildWall = p1UnitCount >= 27 #only reinforce if the full wall is in place
        needsStrongerCorners = game_state.turn_number > 3      
        towersToBuild = 1   
        self.coresToSpendOnRebuilding = 4

        if game_state.turn_number == 0:
            self.buildFirewalls(game_state, [[1, 13], [3, 13], [24, 13], [26, 13]], FILTER, False)
            self.buildFirewalls(game_state, [[2, 13], [6, 11], [21, 11], [25, 13]], DESTRUCTOR, False)
            game_state.attempt_spawn(SCRAMBLER, [22, 8])
            game_state.attempt_spawn(SCRAMBLER, [5, 8])
        elif game_state.turn_number == 1:
            if game_state.get_enemy_destructor_count_for_locations([[ 0, 14],[ 1, 14],[ 2, 14],[ 3, 14],[ 4, 14],[ 5, 14]]) > 0:
                self.buildFirewalls(game_state,[[3, 11],[5, 11]], FILTER, False)
                self.buildFirewalls(game_state,[[4, 11]], ENCRYPTOR, False)
                self.possibleLeftSpawnCoords = [[3, 10]]
            elif game_state.get_enemy_destructor_count_for_locations([[ 1, 15],[ 2, 15],[ 3, 15],[ 4, 15],[ 5, 15]]) > 0:
                self.buildFirewalls(game_state,[[3, 12],[5, 12]], FILTER, False)
                self.buildFirewalls(game_state,[[4, 12]], ENCRYPTOR, False)
                self.possibleLeftSpawnCoords = [[2, 11]]
            else:
                self.buildFirewalls(game_state,[[4, 13],[5,13]], FILTER, False)
                self.buildFirewalls(game_state,[[4, 11]], ENCRYPTOR, False)
                self.possibleLeftSpawnCoords = [[1, 12]]

            if game_state.get_enemy_destructor_count_for_locations([[ 22, 14],[ 23, 14],[ 24, 14],[ 25, 14],[ 26, 14],[ 27, 14]]) > 0:
                self.buildFirewalls(game_state,[[22, 11],[24, 11]], FILTER, False)
                self.buildFirewalls(game_state,[[23, 11]], ENCRYPTOR, False)
                self.possibleRightSpawnCoords = [[24, 10]]
            elif game_state.get_enemy_destructor_count_for_locations([[ 22, 15],[ 23, 15],[ 24, 15],[ 25, 15],[ 26, 15]]) > 0:
                self.buildFirewalls(game_state,[[22, 12],[24, 12]], FILTER, False)
                self.buildFirewalls(game_state,[[23, 12]], ENCRYPTOR, False)
                self.possibleRightSpawnCoords = [[25, 11]]
            else:
                self.buildFirewalls(game_state,[[22, 13],[23,13]], FILTER, False)
                self.buildFirewalls(game_state,[[23, 11]], ENCRYPTOR, False)
                self.possibleRightSpawnCoords = [[26, 12]]

            game_state.attempt_spawn(EMP, self.possibleLeftSpawnCoords[0])
            game_state.attempt_spawn(EMP, self.possibleRightSpawnCoords[0])
        else:
            game_state.attempt_spawn(EMP, self.possibleLeftSpawnCoords[0])
            game_state.attempt_spawn(EMP, self.possibleRightSpawnCoords[0])


            # EMPs will be neutralized by my own encrypted EMPs.  Check if I need more encryptors
            if len(self.enemy_EMP_spawn_coords) > 0:
                leftEMPSpawnCoords = []
                rightEMPSpawnCoords = []
                for c in self.enemy_EMP_spawn_coords:
                    x, y = c
                    if x < 14:
                        leftEMPSpawnCoords.append(c)
                    else:
                        rightEMPSpawnCoords.append(c)
                leftEncryptorStrength = 0
                rightEncryptorStrenth = 0
                for c in self.jsonState.get('p2Units')[1]:
                    x = c[0]
                    if x < 14:
                        leftEncryptorStrength += 1
                    else:
                        rightEncryptorStrenth += 1
                enemyEMPsAffordable = game_state.get_resource(game_state.BITS, 1) // 3

                # we want to build EMP army size + encryptor strength in encryptors
                if len(leftEMPSpawnCoords) > 0:
                    if game_state.count_units_in_locations(self.leftEncryptorCoords) < enemyEMPsAffordable + leftEncryptorStrength:
                        self.buildFirewalls(game_state, self.leftEncryptorCoords, ENCRYPTOR, False, 1)
                if len(rightEMPSpawnCoords) > 0:
                    if game_state.count_units_in_locations(self.rightEncryptorCoords) < enemyEMPsAffordable + rightEncryptorStrenth:
                        self.buildFirewalls(game_state, self.rightEncryptorCoords, ENCRYPTOR, False, 1)


            # towers will be the way to neutralize pings
            if len(self.enemy_ping_spawn_coords) > 0:
                self.buildFirewalls(game_state, self.middleTowerCoords, DESTRUCTOR, False)

            # towers will be the way to neutralize scramblers
            if len(self.enemy_scrambler_spawn_cords) > 0:
                self.buildFirewalls(game_state, self.middleTowerCoords, DESTRUCTOR, False)

        # reset the dictionary for the next analysis
        self.army_dict['total_count'] = 0
        self.army_dict['total_cost'] = 0
        self.army_dict['ping_count'] = 0
        self.army_dict['EMP_count'] = 0
        self.army_dict['scrambler_count'] = 0
        self.enemy_spawns.clear()
        self.my_EMP_ids.clear()
        game_state.submit_turn()

    def threatenSpawn(self, game_state):
        for spawn in self.enemy_EMP_spawn_coords:
            path = []
            offset = 0
            if spawn in game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT):
                path = game_state.find_path_to_edge(spawn, game_state.game_map.BOTTOM_LEFT)
                offset = -1
            else:
                path = game_state.find_path_to_edge(spawn, game_state.game_map.BOTTOM_RIGHT)
                offset = 1

            stepCount = 0
            for step in path:
                stepCount += 1
                if stepCount > 3:
                    return
                x, y = step
                if y <= 16 and [x, 13] not in self.reservedCoords and [x + offset, 13] not in self.reservedCoords:
                    self.buildFirewalls(game_state, [[x, 13]], FILTER, True)
                    self.buildFirewalls(game_state, [[x + offset, 13]], DESTRUCTOR, True)
                    self.enemy_EMP_spawn_coords.clear()
                    return
    
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
                        return numberBuilt
        return numberBuilt

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
            if game_state.can_spawn(PING, startLocation) and startLocation not in self.spawnBlacklist:
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
            if game_state.can_spawn(PING, startLocation) and startLocation not in self.spawnBlacklist:
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
            if game_state.can_spawn(EMP, startLocation) and startLocation not in self.spawnBlacklist and len(game_state.get_attackers(startLocation, 0)) == 0:
                path = game_state.find_path_to_edge(startLocation, game_state.game_map.TOP_RIGHT)
                pathValue = game_state.get_target_count_for_EMP_locations(path)
                if pathValue > bestPathValue:
                    bestPathValue = pathValue
                    deployLocation = startLocation
                    targetEdge = game_state.game_map.TOP_RIGHT
        for startLocation in game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT):
            if game_state.can_spawn(EMP, startLocation) and startLocation not in self.spawnBlacklist and len(game_state.get_attackers(startLocation, 0)) == 0:
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
            if game_state.can_spawn(EMP, startLocation) and startLocation not in self.spawnBlacklist and len(game_state.get_attackers(startLocation, 0)) == 0:
                path = game_state.find_path_to_edge(startLocation, game_state.game_map.TOP_RIGHT)
                #pathValue = game_state.get_target_count_for_EMP_locations(path) - game_state.get_attacker_count_for_locations(path)
                pathValue = game_state.get_free_target_count_for_EMP_locations(path)
                if pathValue > bestPathValue:
                    bestPathValue = pathValue
                    deployLocation = startLocation
                    targetEdge = game_state.game_map.TOP_RIGHT
        for startLocation in game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT):
            if game_state.can_spawn(EMP, startLocation) and startLocation not in self.spawnBlacklist and len(game_state.get_attackers(startLocation, 0)) == 0:
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
