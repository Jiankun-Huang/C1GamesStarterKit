import gamelib
import random
import math
import warnings
from sys import maxsize

class AlgoStrategy(gamelib.AlgoCore):
    
    def __init__(self):
        super().__init__()
        random.seed()
        # state variables
        self.attackForPain = True
        self.attackedLastTurn = False
        self.lastEnemyHealth = 30
        self.lastEnemyUnitCount = 0
        self.doesEnemyHorde = False
        self.lastTurnGameState = None
        self.totalCoresSpent = 0
        self.troopDeploymentCoords = [13,0]
        # maybe this magical cooridoor is suicide, but we'll see!
        self.reservedCoords = [
            [20,13],[20,12],[20,11],[20,10],[13,0],[13,1],[13,2],[13,3],[13,4],[13,5],
            # Reserving this helps shape the corner defense
            [1,13],[26,13]
        ]
        self.reservedCoordsForThisTurn = []
        self.betterAsFilter = []
        
        self.buildCastleWall = False
        self.castleWallRow = 0
        self.scramblerCoords = [[4,9], [8,5], [13,0], [17, 3], [21,7]]
        self.pingCoord = [3, 10]
        self.turnZeroBuild = [
            [0,13],[1,12],[4,11],[23,11],[26,12],[27,13]
        ]

    def on_game_start(self, config):
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
        
        self.totalCoresSpent = 0
        self.reservedCoordsForThisTurn = []
        for coord in self.reservedCoords:
            self.reservedCoordsForThisTurn.append(coord)

        self.buildTurnZeroTowers(game_state)

        # consider front line being FILTERS? Does it matter if they use EMPs? YES!! PINGS need these to be towers
        # NEED TO COUNTER HEAVY EMP DESTRUCTION, we can't afford to build enough defense when EMPs wreck havok
        if self.enemy_EMP_spawn_count > self.enemy_ping_spawn_count:
            gamelib.debug_write('p2 likes to spawn EMPs. {} > {}'.format(self.enemy_EMP_spawn_count, self.enemy_ping_spawn_count))
            for x in range(28):
                if [x,13] not in self.betterAsFilter:
                    self.betterAsFilter.append([x,13])
        else:
            gamelib.debug_write('p2 likes to spawn Pings. {} < {}'.format(self.enemy_EMP_spawn_count, self.enemy_ping_spawn_count))
            self.betterAsFilter = []


        if not self.doesEnemyHorde and game_state.turn_number > 4 and game_state.get_resource(game_state.CORES, 1) >= 10:
            gamelib.debug_write('p2 is a HORDER! CORES:{}'.format(game_state.get_resource(game_state.CORES, 1)))
            # once a horder, always a horder
            self.doesEnemyHorde = True
            self.attackForPain = True

        if self.attackedLastTurn:
            if self.attackForPain and game_state.enemy_health == self.lastEnemyHealth:
                gamelib.debug_write('Tried to hurt them and failed! Changing strategies.')
                if not self.doesEnemyHorde:
                    self.attackForPain = False
            elif p2UnitCount >= self.lastEnemyUnitCount + 4:
                # TODO # This is not good enough, we lose some games where switching to PINGS might have made the difference
                gamelib.debug_write('Tried to damage them and failed! Changing strategies.')
                self.attackForPain = True
        
        self.attackedLastTurn = False

        # we need to be careful overbuilding on any one turn, so pretend we never have more than 26 cores #
        # TODO # DONE

        if game_state.turn_number == 0:
            self.spawnScramblerJammers(game_state)
        else:
            # if we haven't seen an enemy spawn yet (and it's still early)
            if game_state.turn_number < 3 and len(self.enemy_spawn_coords) == 0:
                self.spawnScramblerJammers(game_state)
            
            self.markForRefund(game_state)
            # NEED TO CONSIDER ALGOs THAT HORDE CORES AND WHAT HAPPENS AFTER MASSIVE DESTRUCTION
            # more complex comparisson would be if they can afford to replace all that was destroyed ...
            if self.lastEnemyUnitCount > p2UnitCount and game_state.get_resource(game_state.CORES, 1) > 6:
                coordsToReinforce = self.reinforceLocationsEvenly(self.lastTurnGameState, self.enemy_spawn_coords)
                for location in coordsToReinforce:
                    attackers = len(game_state.get_attackers(location, 1))
                    if attackers < 5:
                        self.reinforceLocation(game_state, location, 5 - attackers)
            else:
                self.reinforceLocationsEvenly(game_state, self.enemy_spawn_coords)

            if self.attackForPain:
                if game_state.number_affordable(PING) >= 12 + game_state.turn_number // 5:
                    self.attackForMaxPain(game_state)
                    self.attackedLastTurn = True
                else:
                    self.attackedLastTurn = False
            else:
                if game_state.number_affordable(EMP) >= 3 + game_state.turn_number // 15:
                    self.attackForMaxDestruction(game_state)
                    self.attackedLastTurn = True
                else:
                    self.attackedLastTurn = False


        gamelib.debug_write('SUMBITTING TURN {}'.format(game_state.turn_number))
        self.lastEnemyHealth = game_state.enemy_health
        self.lastEnemyUnitCount = p2UnitCount
        self.lastTurnGameState = game_state
        game_state.submit_turn()

    def buildTurnZeroTowers(self, game_state):
        for location in self.turnZeroBuild:
            if self.totalCoresSpent < 23 and game_state.can_spawn(DESTRUCTOR, location):
                game_state.attempt_spawn(DESTRUCTOR, location)
                self.totalCoresSpent += 3

    def spawnScramblerJammers(self, game_state):
        for location in self.scramblerCoords:
            if game_state.can_spawn(SCRAMBLER, location):
                game_state.attempt_spawn(SCRAMBLER, location)

    def markForRefund(self, game_state):
        for location in game_state.friendly_firewall_locations:
            x, y = location
            for unit in game_state.game_map[x,y]:
                if unit.stability < 35:
                    game_state.attempt_remove(location)

    def buildWall(self, game_state):
        # always start from the left for now
        for x in range(28):
            wallLocation = [x, self.castleWallRow]
            attackLocation = [x, self.castleWallRow - 1]
            if game_state.game_map.in_arena_bounds(attackLocation):
                if attackLocation not in self.reservedCoords:
                    self.reservedCoords.append(attackLocation)
            
            if game_state.game_map.in_arena_bounds(wallLocation):
                x, y = wallLocation
                for unit in game_state.game_map[x,y]:
                    if unit.stability < 35:
                        game_state.attempt_remove(wallLocation)
                if self.totalCoresSpent < 23 and game_state.can_spawn(DESTRUCTOR, wallLocation) and wallLocation not in self.reservedCoords:
                    game_state.attempt_spawn(DESTRUCTOR, wallLocation)
                    self.totalCoresSpent += 3
 
    def reinforceLocation(self, game_state, location, number_to_add):
        added = 0
        gamelib.debug_write('reinforcing {} with {} towers. {} to spend'.format(location, number_to_add, game_state.get_resource(game_state.CORES)))
        for n in range(4):
            if added < number_to_add:
                for coord in game_state.game_map.get_locations_in_range(location, n):
                    if coord in self.betterAsFilter:
                        if self.totalCoresSpent < 25 and game_state.can_spawn(FILTER, coord) and coord not in self.reservedCoordsForThisTurn:
                            game_state.attempt_spawn(FILTER, coord)
                            self.totalCoresSpent += 1
                    elif self.totalCoresSpent < 23 and game_state.can_spawn(DESTRUCTOR, coord) and coord not in self.reservedCoordsForThisTurn:
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
                
                # we want to allow the path through our defenses, just defend it!
                if path:
                    for step in path:
                        x, y = step
                        # let's focus our towers on the first few rows of our base
                        # TODO # Consider a 'v' shape! To minimize needless destruction from sweeping Algos 
                        if y < 16 and y > 9:
                            if step not in self.reservedCoordsForThisTurn:
                                self.reservedCoordsForThisTurn.append(step)
                            dictOfDefense[tuple(step)] = len(game_state.get_attackers(step, 1))
                            gamelib.debug_write('DictOfDefense adding {}, attackers={}'.format(step, dictOfDefense[tuple(step)]))

            elif startCoord in game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT):
                path = game_state.find_path_to_edge(startCoord, game_state.game_map.BOTTOM_LEFT)
                if path:
                    # we want to allow the path through our defenses, just defend it!
                    for step in path:
                        x, y = step
                        # avoid the first few rows
                        if y < 9 and y > 6:
                            if step not in self.reservedCoordsForThisTurn:
                                self.reservedCoordsForThisTurn.append(step)
                            dictOfDefense[tuple(step)] = len(game_state.get_attackers(step, 1))
                            gamelib.debug_write('DictOfDefense2 adding {}, attackers={}'.format(step, dictOfDefense[tuple(step)]))
        
        for coord, attackers in sorted(dictOfDefense.items(), key=lambda x: x[1]):
            coordsToReinforce.append(list(coord))
            if attackers < 5:
                self.reinforceLocation(game_state, list(coord), 5 - attackers)

        return coordsToReinforce

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
