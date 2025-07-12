import sys
sys.path.insert(0, '../')
from planet_wars import issue_order
from checks import averagePlanetDist, distanceOfPlanets, isWithinDistance

""" planetsWihtinRange = dict of planets (pseudo-cache)
Planet -> [Planets]
Value = list of Planets within averagePlanetDist of KeyPlanet
"""

planetsWithinRange = {}

def discoverClosestAllies(state, planet, myAllies):
    planetsWithinRange[planet] = []

    for ally in myAllies:
        if isWithinDistance(state, planet, ally):
            planetsWithinRange[planet].append(ally)



def grabPlanetByID(planetID, possiblePlanets):
    for planet in possiblePlanets:
        if planetID == planet.ID:
            return planet


### ORDERS ###
def attack_weakest_enemy_planet(state):
    # (1) If we currently have a fleet in flight, abort plan.
    if len(state.my_fleets()) >= 1:
        return False

    # (2) Find my strongest planet.
    strongest_planet = max(state.my_planets(), key=lambda t: t.num_ships, default=None)

    # (3) Find the weakest enemy planet.
    weakest_planet = min(state.enemy_planets(), key=lambda t: t.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        # No legal source or destination
        return False
    else:
        # (4) Send half the ships from my strongest planet to the weakest enemy planet.
        return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships / 2)


def spread_to_weakest_neutral_planet(state):
    # (1) If we currently have a fleet in flight, just do nothing.
    if len(state.my_fleets()) >= 1:
        return False

    # (2) Find my strongest planet.
    strongest_planet = max(state.my_planets(), key=lambda p: p.num_ships, default=None)

    # (3) Find the weakest neutral planet.
    weakest_planet = min(state.neutral_planets(), key=lambda p: p.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        # No legal source or destination
        return False
    else:
        # (4) Send half the ships from my strongest planet to the weakest enemy planet.
        return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships / 2)
 
def protect_ally(state):

    alliesUnderAttackByID = []
    myAlliesByID = [planet.ID for planet in state.my_planets()]
    allyPlanets = [planet for planet in state.my_planets()]

    myActiveFleetsByDST = [fleet.destination_planet for fleet in state.my_fleets()]

    activeEnemyFleets = [fleet for fleet in state.enemy_fleets()]
    
    for enemyFleet in activeEnemyFleets:
        if enemyFleet.destination_planet in myAlliesByID:
            alliesUnderAttackByID.append(enemyFleet.destination_planet)
    
    #DST IMPLIMENTATION
    alliesToSave = [grabPlanetByID(ID, allyPlanets) for ID in alliesUnderAttackByID]

    #send help to allies not already under threat
    for _ in range(len(alliesToSave)):

        #!!!logic for sending closest ally planet
        planetToDefend = min(alliesToSave, key=lambda p: p.num_ships, default=None)
        
        try: #ensuring that we have they key-value pair set up
            planetsWithinRange[planetToDefend]
        except KeyError:
            discoverClosestAllies(state, planetToDefend, allyPlanets)

        #who is the strongest ally within range?
        closestStrongestAlly = max(planetsWithinRange[planetToDefend], key=lambda p: p.num_ships, default=None)

        #if no strong ally within range, not worth protecting - skip
        if closestStrongestAlly == None:
            continue
            #keep as is, or, send closest one globally if under attack?
        
        #dont send multiple ships at once
        if planetToDefend.ID not in myActiveFleetsByDST:
            issue_order(state, closestStrongestAlly.ID, planetToDefend.ID, closestStrongestAlly.num_ships / 4)

    return True
