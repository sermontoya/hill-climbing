import math
import random

import utils


def simulated_annealing(grid, T_min, T_initial, cooling_rate):
    """
    Optimize hospital positions using simulated annealing by exploring random moves
    and occasionally accepting worse states to escape local optima.

    Args:
        grid: Matrix (list of lists) representing the board.
        T_min: Minimum temperature at which the search stops.
        T_initial: Starting temperature for the annealing process.
        cooling_rate: Multiplicative factor used to cool the temperature each step.

    Returns:
        list[list]: A grid configuration produced by the annealing search.
    """
    current_grid = grid
    current_cost = utils.cost(current_grid)
    temperature = T_initial
    while temperature > T_min:
        movable_hospitals = utils.movable_hospitals(current_grid)
        if len(movable_hospitals) == 0:
            break
        selected_hospital = random.choice(movable_hospitals)
        posible_moves = utils.actions(current_grid, selected_hospital)
        selected_move = random.choice(posible_moves)
        neighbor_solution = utils.result(current_grid, selected_hospital, selected_move)
        neighbor_cost = utils.cost(neighbor_solution)
        cost_difference = neighbor_cost - current_cost
        if cost_difference < 0:
            current_grid = neighbor_solution
            current_cost = neighbor_cost
        else:
            acceptance_probability = math.exp(-cost_difference / temperature)
            random_value = random.random()
            if random_value < acceptance_probability:
                current_grid = neighbor_solution
                current_cost = neighbor_cost
        temperature *= cooling_rate
    return current_grid



def hill_climbing(map):
    """
    Optimize a board by repeatedly choosing the best local move.


    This function should implement classic hill climbing: on each iteration,
    evaluate every one-step move for every hospital, choose the neighbor with
    the lowest cost, and move there only if it strictly improves the current
    cost. Stop when no improving neighbor exists.
    Args:
        map: Matrix (list of lists) representing the board.

    Returns:
        list[list]: A map configuration with locally minimized cost.
    """


    current_map = map
    current_cost = utils.cost(current_map)

    while True:
        best_map = current_map
        best_cost = current_cost

        for hospital in utils.find_objects(current_map, utils.OBJECT_HOSPITAL):
            for candidate_move in utils.actions(current_map, hospital):
                candidate_map = utils.result(current_map, hospital, candidate_move)
                candidate_cost = utils.cost(candidate_map)

                if candidate_cost < best_cost:
                    best_map = candidate_map
                    best_cost = candidate_cost

        if best_cost < current_cost:
            current_map = best_map
            current_cost = best_cost
        else:
            break

    return current_map
