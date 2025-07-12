import random
from math import sqrt

averagePlanetDist = None

def distanceOfPlanets(source, destination):
    x1 = source.x
    y1 = source.y
    x2 = destination.x 
    y2 = destination.y

    return sqrt( (x2-x1)**2 + (y2-y1)**2 )

def calcAverageDistance(state):
    listOfPlanets = [planet for planet in state.planets]
    averageDistance = 0
    for planet in listOfPlanets:
        minPlanet = random.choice(listOfPlanets)
        maxPlanet = planet

        for comparedPlanet in listOfPlanets:
            if comparedPlanet == planet:
                pass
            elif distanceOfPlanets(planet, comparedPlanet) > distanceOfPlanets(planet, maxPlanet):
                maxPlanet = comparedPlanet
            elif distanceOfPlanets(planet, comparedPlanet) < distanceOfPlanets(planet, minPlanet):
                minPlanet = comparedPlanet

        averageDistance += (distanceOfPlanets(planet, minPlanet) + distanceOfPlanets(planet, maxPlanet)) // 2
        
    return averageDistance // len(listOfPlanets)

def isWithinDistance(state, fromPlanet, targetPlanet):
    global averagePlanetDist
    if averagePlanetDist == None: #if first run, calc avgDist from planets & store 4 l8r uses
        averagePlanetDist = int(calcAverageDistance(state))

    return distanceOfPlanets(fromPlanet, targetPlanet) <= averagePlanetDist

def if_neutral_planet_available(state):
    return any(state.neutral_planets())


def have_largest_fleet(state):
    return sum(planet.num_ships for planet in state.my_planets()) \
             + sum(fleet.num_ships for fleet in state.my_fleets()) \
           > sum(planet.num_ships for planet in state.enemy_planets()) \
             + sum(fleet.num_ships for fleet in state.enemy_fleets())


def is_ally_under_attack(state):
    
    myAllies = [planet.ID for planet in state.my_planets()]
    activeEnemyFleets = [fleet for fleet in state.enemy_fleets()]
    
    for enemyFleet in activeEnemyFleets:
        if enemyFleet.destination_planet in myAllies:
            return True
        
        
    return False