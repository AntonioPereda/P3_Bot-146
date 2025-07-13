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


strongAlly = 1
nearbyAlly = 2
globalStrongest = 3
selfDestruct = 4

def fleetSize(state, fromPlanet, toPlanet, case):

    if strongAlly:
        #target has faster growth rate, dont need to send as many ships
        if toPlanet.growth_rate > fromPlanet.growth_rate:
            return fromPlanet.num_ships//5
        
        #we can make up the extra ships we sent in a few turns
        else: 
            return (fromPlanet.num_ships//5) + toPlanet.growth_rate * state.distance(fromPlanet.ID, toPlanet.ID)
    
    #same logic as above, just smaller amount
    elif nearbyAlly:
        if toPlanet.growth_rate > fromPlanet.growth_rate:
            return fromPlanet.num_ships//7
        
        #we can make up the extra ships we sent in a few turns
        else: 
            return (fromPlanet.num_ships//7) + toPlanet.growth_rate * state.distance(fromPlanet.ID, toPlanet.ID)//2

    elif globalStrongest:
        distance = state.distance(fromPlanet.ID, toPlanet.ID)

        return (fromPlanet.growth_rate * distance) + fromPlanet.num_ships//5

    #for selfDestruct, pass len(alliesToSave) -1 in toPlanet
    elif selfDestruct:
        return fromPlanet.num_ships// toPlanet

    else:
        raise ValueError("Unknown <case> Input. Must be strongAlly, nearbyAlly, globalStrongest or selfDestruct")



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

    planetToAttacker = {}
    
    for enemyFleet in activeEnemyFleets:
        if enemyFleet.destination_planet in myAlliesByID:
            alliesUnderAttackByID.append(enemyFleet.destination_planet)
            planetToAttacker[enemyFleet.destination_planet] = enemyFleet
    
    #DST IMPLIMENTATION
    alliesToSave = [grabPlanetByID(ID, allyPlanets) for ID in alliesUnderAttackByID]

    #send help to allies under threat
    for planetToDefend in range(len(alliesToSave)):
        
        try: #ensuring that we have they key-value pair set up
            planetsWithinRange[planetToDefend]
        except KeyError:
            discoverClosestAllies(state, planetToDefend, allyPlanets)

        #who is the strongest ally within range?
        closeStrongestAlly = max(planetsWithinRange[planetToDefend], key=lambda p: p.num_ships, default=None)
            
        #if no strong ally within range, different protocol
        if closeStrongestAlly == None:
            
            attacker = planetToAttacker[planetToDefend.ID]

            #is it predicted to likely to lose?
            estSizeByTouchdown = planetToDefend.num_ships + (attacker.turns_remaining 
            * planetToDefend.growth_rate)
            
            if attacker.num_ships > estSizeByTouchdown:
                pass

                #if we send OP backup, will we instantly reclaim or win?
                strongestAllyPlanet = max(state.my_planets(), key=lambda p: p.num_ships, default=None)
                takeoverGrowthConsideration = 1.25 #~25% consideration for growth rate & time/distance

                                                        #est size of planet after enemy takes over and few turns pass
                if (strongestAllyPlanet.num_ships/5) > int((attacker.num_ships-estSizeByTouchdown)*takeoverGrowthConsideration):
                    if planetToDefend.ID not in myActiveFleetsByDST:
                        issue_order(state, strongestAllyPlanet.ID, planetToDefend.ID, 
                                    fleetSize(state, strongestAllyPlanet, planetToDefend, strongestAllyPlanet))

                #its going to lose anyways, sac itself equally amongst weaker planets
                else:
                    for ally in alliesToSave:
                        if ally != planetToDefend:
                            issue_order(state, planetToDefend.ID, ally.ID, 
                                        fleetSize(state, planetToDefend, len(alliesToSave)-1, selfDestruct))


            #its going to win anyways, move on...
            continue

        #dont send duplicate ships
        if planetToDefend.ID not in myActiveFleetsByDST:
            
            #all ships send help if weak ally under attack
            for ally in planetsWithinRange[planetToDefend]:

                #for closeStrongestAlly, it contributes more ships to help
                if closeStrongestAlly == ally:
                    issue_order(state, closeStrongestAlly.ID, planetToDefend.ID, 
                                fleetSize(state, closeStrongestAlly, planetToDefend, strongAlly))

                #all allies (excl any under attack) send tiny help as well
                elif closeStrongestAlly != ally and ally not in alliesToSave:
                    issue_order(state, ally.ID, planetToDefend.ID, 
                                fleetSize(state, strongestAllyPlanet, planetToDefend, nearbyAlly))

    return True
