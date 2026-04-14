import copy

OBJECT_EMPTY = None
OBJECT_HOUSE = "🏠"
OBJECT_HOSPITAL = "🏥"


MOVE_UP = (0, -1)
MOVE_DOWN = (0, 1)
MOVE_LEFT = (-1, 0)
MOVE_RIGHT = (1, 0)


def is_free_to_move(map, move):
    x,y = move
    return map[y][x] == OBJECT_EMPTY 


def is_valid_move(map, move):
    x,y = move
    rowsCount = len(map)
    columnsCount = len(map[0])
    return x >=0 and y>=0 and x < columnsCount and y < rowsCount
        
        
def find_objects(map, target_object_symbol):        
    res = []
    rowsCount = len(map)
    columnsCount = len(map[0])
    for y in range(rowsCount):
        for x in range(columnsCount):
            pos = map[y][x]
            if pos is target_object_symbol:
                res.append((x,y))
                
    return res

def result(map, hospital_coordinates, target_move):
    newMap = copy.deepcopy(map)
    oldX, oldY = hospital_coordinates
    newX, newY = target_move
    newMap[newY][newX] = OBJECT_HOSPITAL
    newMap[oldY][oldX] = OBJECT_EMPTY
    return newMap
    


def manhattan(pos, pos_2):
    x1,y1 = pos
    x2,y2 = pos_2 
    return abs(y2-y1) + abs(x2-x1)


def cost(map):
    """
    Compute total cost as the sum of distances from each hospital to each house.

    Args:
        map: Matrix (list of lists) representing the board.

    Returns:
        int: Total Manhattan-distance cost.
    """
    hospitals = find_objects(map, OBJECT_HOSPITAL)
    houses = find_objects(map, OBJECT_HOUSE)
    total_cost = 0
    
    for hospital in hospitals:
        for house in houses:
            total_cost += manhattan(hospital, house)
    
    return total_cost
    


def move(pos, pos_2):
    """
    Add two coordinates component-wise.

    Args:
        pos: First coordinate as (x, y).
        pos_2: Second coordinate as (x, y).

    Returns:
        tuple[int, int]: New coordinate as (x1 + x2, y1 + y2).
    """

    x1,y1 = pos
    x2,y2 = pos_2
    return (x1 + x2, y1 + y2)


def actions(map, hospital_position):
    """
    Return all valid adjacent moves for a hospital in up, down, left, right order.

    Args:
        map: Matrix (list of lists) representing the board.
        hospital_position: Hospital coordinate as (x, y).

    Returns:
        list[tuple[int, int]]: Valid neighboring positions that are in bounds and free.
    """
    res = []
    up = move(hospital_position, MOVE_UP)
    down = move(hospital_position, MOVE_DOWN)
    left = move(hospital_position, MOVE_LEFT)
    right = move(hospital_position, MOVE_RIGHT)
    for movement in [up, down, left, right]:
        if is_valid_move(map,movement) and is_free_to_move(map, movement) :
            res.append(movement)
    return res
        
def movable_hospitals(map):
    res = []
    hospitals = find_objects(map, OBJECT_HOSPITAL)
    for hospital in hospitals:
        if len(actions(map, hospital)) > 0:
            res.append(hospital)
    return res
