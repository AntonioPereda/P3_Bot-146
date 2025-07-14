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
    """Populate planetsWithinRange[planet] with nearby ally planets."""
    planetsWithinRange[planet] = []

    for ally in myAllies:
        if isWithinDistance(state, planet, ally):
            planetsWithinRange[planet].append(ally)


def grabPlanetByID(planetID, possiblePlanets):
    """Return the Planet object with the given ID from a list."""
    for planet in possiblePlanets:
        if planetID == planet.ID:
            return planet


### ORDERS ###

def attack_weakest_enemy_planet(state):
    """Send just enough ships from nearby planets to capture the weakest enemy planet."""

    my_planets = state.my_planets()
    enemy_planets = state.enemy_planets()

    if not my_planets or not enemy_planets:
        return False

    action_taken = False

    # Get the list of destination IDs our fleets are already heading toward
    my_fleets = [fleet.destination_planet for fleet in state.my_fleets()]

    # Sort enemy planets by projected strength after accounting for growth over distance
    enemy_planets = sorted(enemy_planets, key=lambda enemy: (
        enemy.num_ships + min(
            (state.distance(p.ID, enemy.ID) for p in my_planets),
            default=0
        ) * enemy.growth_rate
    ))

    for target in enemy_planets:

        if target.ID in my_fleets:
            continue  # Skip if already sending a fleet there

        # Calculate distance from each planet to the target
        source_distances = [(planet, state.distance(planet.ID, target.ID)) for planet in my_planets]

        # Estimate how many ships are needed to capture this planet
        min_distance = min(dist for _, dist in source_distances)
        projected_ships_needed = int(target.num_ships + min_distance * target.growth_rate) + 1

        # Sort our planets by how close they are to the target
        source_distances.sort(key=lambda pair: pair[1])

        total_sent = 0

        for source, dist in source_distances:

            if source.num_ships <= 5:
                continue  # Skip weak planets

            if total_sent >= projected_ships_needed:
                break

            remaining = projected_ships_needed - total_sent
            ships_to_send = min(source.num_ships // 2, remaining)

            if ships_to_send > 0:
                issue_order(state, source.ID, target.ID, ships_to_send)
                total_sent += ships_to_send
                action_taken = True

        if total_sent >= projected_ships_needed:
            break  # We captured a planet, stop attacking more this turn

    return action_taken


def spread_to_weakest_neutral_planet(state):
    """Send just enough ships to take over the weakest neutral planets."""

    if len(state.my_fleets()) >= 1:
        return False  # Avoid spamming too many fleets

    my_planets = state.my_planets()
    neutral_planets = sorted(state.neutral_planets(), key=lambda p: p.num_ships)

    if not my_planets or not neutral_planets:
        return False

    # Select the strongest planet as the source
    source = max(my_planets, key=lambda p: p.num_ships)
    available_ships = source.num_ships
    action_taken = False

    for target in neutral_planets:
        required_ships = target.num_ships + 1

        if available_ships > required_ships:
            issue_order(state, source.ID, target.ID, required_ships)
            available_ships -= required_ships
            action_taken = True
        else:
            break  # Not enough ships left to conquer another planet

    return action_taken


def protect_ally(state):
    """Send reinforcements to ally planets under attack, using nearby strong planets."""

    # Get all ally planets
    my_allies = [planet for planet in state.my_planets()]
    my_allies_by_id = [planet.ID for planet in my_allies]

    # track where our fleets are already going
    my_active_fleet_targets = [fleet.destination_planet for fleet in state.my_fleets()]
    active_enemy_fleets = state.enemy_fleets()

    #list of planet IDs being targeted by enemy fleets
    threats = {}
    for fleet in active_enemy_fleets:
        if fleet.destination_planet in my_allies_by_id:
            threats.setdefault(fleet.destination_planet, 0)
            threats[fleet.destination_planet] += fleet.num_ships

    if not threats:
        return False  # No threats, nothing to defend

    action_taken = False

    for threatened_id, enemy_ships in threats.items():
        # DST IMPLEMENTATION
        target_ally = grabPlanetByID(threatened_id, my_allies)
        if target_ally is None:
            continue

        # Ensuring that we have the key-value pair set up (pseudo-cache for nearby allies)
        try:
            nearby_planets = planetsWithinRange[target_ally]
        except KeyError:
            discoverClosestAllies(state, target_ally, my_allies)
            nearby_planets = planetsWithinRange[target_ally]

        # Sort allies by distance with closest first
        nearby_planets = sorted(nearby_planets, key=lambda p: state.distance(p.ID, target_ally.ID))

        # target total support needed (enemy ships + buffer)
        total_needed = enemy_ships + 10
        total_sent = 0

        for ally in nearby_planets:
            # Skip weak planets
            if ally.num_ships <= 5:
                continue

            remaining_needed = total_needed - total_sent
            ships_to_send = min(remaining_needed, ally.num_ships // 2)

            # Don't send multiple ships at once (from same ally to same destination)
            if ships_to_send > 0 and target_ally.ID not in my_active_fleet_targets:
                issue_order(state, ally.ID, target_ally.ID, ships_to_send)
                total_sent += ships_to_send
                action_taken = True

            if total_sent >= total_needed:
                break  # Covered, move on to next threatened planet

        # if no strong ally within range, not worth protecting - skip
        
    return action_taken


