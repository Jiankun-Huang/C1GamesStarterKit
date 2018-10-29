import gamelib
import random
import math
import warnings
import copy
from sys import maxsize
from enum import Enum

DefenseStrategy = Enum('DefenseStrategy', 'DefendAttacksFromLeft DefendAttacksFromRight DefendBoth')
OffenseStrategy = Enum('OffenseStrategy', 'AssaultLeft AssaultRight')

class AlgoStrategy(gamelib.AlgoCore):
    
    def __init__(self):
        super().__init__()
        random.seed()
        # state variables
        self.attackedWithScramblers = True
        self.attackedLastTurn = False
        self.lastEnemyHealth = 30
        self.lastEnemyArmyDict = {}
        self.troopDeploymentCoords = [13,0]
        self.reservedCoords = [
        ]
        for x in range(14):
            self.reservedCoords.append([13 + x, x])
            self.reservedCoords.append([14 + x, x])
        self.reservedCoordsForThisTurn = []
        self.betterAsFilter = []
        for x in range(12):
            self.betterAsFilter.append([8 + x, 9])
        self.totalCoresSpent = 0
        self.spawnBlacklist = [
        ]
        self.coresToSpendOnRebuilding = 0
        
        
        self.rightAssaultTowerCoords = [
            [24, 13],[23, 12],[22, 11],[21, 10]
        ]
        self.rightAssaultTowerFilterCoords = [
            [23, 13], [25, 13], [22, 12], [21, 11], [20, 10]
        ] 
        self.rightAssaultEncryptorCoords = [
            [24, 12],[23, 11],[22, 10]
        ]

        self.leftAssaultTowerCoords = [
            [3, 13],[4, 12],[5, 11],[6, 10]
        ]
        self.leftAssaultTowerFilterCoords = [
            [2, 13], [4, 13], [5, 12], [6, 11], [7, 10]
        ] 
        self.leftAssaultEncryptorCoords = [
            [3, 12],[4, 11],[5, 10]
        ]

        self.nineWall = []
        for x in range(15):
            self.nineWall.append([5 + x, 9])

        self.rightCornerTowers = [
            [0, 13],[1, 12],[2, 11]
        ]
        self.rightCornerFilters = [
            [1, 13],[2, 13],[2, 12]
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
        
        self.totalCoresSpent = 0
        self.reservedCoordsForThisTurn = []

        for coord in self.reservedCoords:
            self.reservedCoordsForThisTurn.append(coord)

        if game_state.can_spawn(FILTER, [25, 13]):
            game_state.attempt_spawn(FILTER, [25, 13])

        path = game_state.find_path_to_edge([13, 0], game_state.game_map.TOP_RIGHT)
        reinforcementCoords = game_state.game_map.get_locations_in_range([23, 11], 3)
        if not any((True for c in reinforcementCoords if c in path)):
            gamelib.debug_write('we are outside the path!')
            self.buildFirewalls(game_state, self.nineWall, FILTER, False)
        
        cornerCoords = [[0, 13],[1, 12],[2, 11]]
        if game_state.my_health <= 15 and any((True for c in cornerCoords if c in self.breach_list)):
            self.buildFirewalls(game_state, self.rightCornerTowers, DESTRUCTOR, False, 1)
            self.buildFirewalls(game_state, self.rightCornerFilters, FILTER, False, 1)

        self.buildFirewalls(game_state, self.rightAssaultTowerCoords, DESTRUCTOR, False, 1)
        self.buildFirewalls(game_state, self.rightAssaultTowerFilterCoords, FILTER, False, 2)
        self.buildFirewalls(game_state, self.rightAssaultEncryptorCoords, ENCRYPTOR, False, 1)
        self.reinforceLocationsEvenly(game_state, self.enemy_spawn_coords)

        shouldAttack = True
        path = game_state.find_path_to_edge([13, 0], game_state.game_map.TOP_RIGHT)
        if not any((True for c in reinforcementCoords if c in path)):
            gamelib.debug_write('we are outside the path!')
            shouldAttack = False

        gamelib.debug_write('{} - attack path={}'.format(game_state.turn_number, len(path)))
        if len(path) > 30:
            shouldAttack = False

        defendingDestructors = len(game_state.get_attackers([26, 13], 0))
        defendingFilters = game_state.get_enemy_filter_count_for_locations([[26, 14], [27, 14]])
        if game_state.number_affordable(PING) < defendingDestructors + defendingFilters + 1:
            shouldAttack = False


        if shouldAttack:
            x, y = path[-1]
            gamelib.debug_write('Final step: {}'.format(path[-1]))
            if [26, 13] in path and game_state.turn_number > 0:
                if self.attackedWithScramblers and self.lastEnemyHealth >= game_state.enemy_health - 4:
                    if game_state.number_affordable(EMP) >= 3 + 1 * game_state.turn_number // 12:
                        game_state.attempt_spawn(EMP, [13, 0], game_state.number_affordable(EMP))
                        self.attackedWithScramblers = False
                        self.attackedLastTurn = True
                        shouldAttack = False
                    else:
                        shouldAttack = False
                elif y == 13 or self.attackedLastTurn and self.lastEnemyHealth >= game_state.enemy_health - 4:
                    game_state.attempt_spawn(SCRAMBLER, [24, 10], defendingDestructors + defendingFilters + 1)
                    self.attackedWithScramblers = True
                    self.attackedLastTurn = True

            if shouldAttack and game_state.number_affordable(PING) > 2:
                game_state.attempt_spawn(PING, [13, 0], game_state.number_affordable(PING))
                self.attackedLastTurn = True
        else:
            self.attackedLastTurn = False
        
        self.lastEnemyHealth = game_state.enemy_health
        game_state.submit_turn()

    def reinforceLocation(self, game_state, location, number_to_add):
        added = 0
        gamelib.debug_write('reinforcing {} with {} towers. {} to spend'.format(location, number_to_add, game_state.get_resource(game_state.CORES)))
        for n in range(4):
            if added < number_to_add:
                for coord in game_state.game_map.get_locations_in_range(location, n):
                    if coord in self.betterAsFilter:
                        if self.totalCoresSpent < 8 and game_state.can_spawn(FILTER, coord) and coord not in self.reservedCoordsForThisTurn:
                            game_state.attempt_spawn(FILTER, coord)
                            self.totalCoresSpent += 1
                    elif self.totalCoresSpent < 8 and game_state.can_spawn(DESTRUCTOR, coord) and coord not in self.reservedCoordsForThisTurn:
                        game_state.attempt_spawn(DESTRUCTOR, coord)
                        self.totalCoresSpent += 3
                        added += 1

    def reinforceLocationsEvenly(self, game_state, locations):
        gamelib.debug_write('Reinforcement planning {}'.format(locations))
        dictOfDefense = {}
        coordsToReinforce = []
        for startCoord in reversed(locations):
            if startCoord in game_state.game_map.get_edge_locations(game_state.game_map.TOP_LEFT):
                path = game_state.find_path_to_edge(startCoord, game_state.game_map.BOTTOM_RIGHT)
                if path:
                    for step in path:
                        x, y = step
                        # avoid the first few rows
                        if y < 9 and y > 7:
                            dictOfDefense[tuple(step)] = len(game_state.get_attackers(step, 1))
                            gamelib.debug_write('DictOfDefense adding {}, attackers={}'.format(step, dictOfDefense[tuple(step)]))

            elif startCoord in game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT):
                path = game_state.find_path_to_edge(startCoord, game_state.game_map.BOTTOM_LEFT)
                if path:
                    for step in path:
                        x, y = step
                        if y < 9 and y > 7:
                            dictOfDefense[tuple(step)] = len(game_state.get_attackers(step, 1))
                            gamelib.debug_write('DictOfDefense2 adding {}, attackers={}'.format(step, dictOfDefense[tuple(step)]))
        
        for coord, attackers in sorted(dictOfDefense.items(), key=lambda x: x[1]):
            coordsToReinforce.append(list(coord))
            if attackers < 3:
                self.reinforceLocation(game_state, list(coord), 1)

        return coordsToReinforce

    def threatenSpawn(self, game_state):
        for spawn in self.enemy_spawn_coords:
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
                    self.enemy_spawn_coords.clear()
                    return
    
    def buildFirewalls(self, game_state, locations, unit_type, rebuildAsNeeded, maxToBuild = 100):
        numberBuilt = 0
        for location in locations:
            if location not in self.reservedCoords:
                if rebuildAsNeeded:
                    self.checkForRefund(game_state, location)
                if game_state.can_spawn(unit_type, location):
                    x, y = location
                    if (x, y) in self.death_dict:
                        if self.death_dict[(x, y)] > 1:
                            unit_type = FILTER
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
        deployLocation = [13, 0]
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
