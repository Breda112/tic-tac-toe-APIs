import math
import random

X = "X"
O = "O"
EMPTY = None
def initial_state():
    """
    Returns starting state of the board.
    """
    return [[EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY]]

def player(board):
    """
    Returns the player who has the next turn on the board.
    """
    countX = sum(row.count(X) for row in board)
    countO = sum(row.count(O) for row in board)
    
    return X if countO >= countX else O


def actions(board):
    """
    Returns a set of all possible actions (i, j) available on the board, shuffled randomly.
    """
    # Generate the list of possible actions
    action_list = [(i, j) for i in range(len(board)) for j in range(len(board[i])) if board[i][j] == '']
    
    # Shuffle the list
    random.shuffle(action_list)
    # return
    return action_list


def result(board, action):
    """
    Returns the board that results from making move (i, j) on the board.
    """
    if action not in actions(board):
        raise Exception("not valid action")
    
    i, j = action
    board_copy = [row[:] for row in board]  # Shallow copy of the board
    board_copy[i][j] = player(board)
    
    return board_copy

# Precomputed winning patterns
winning_patterns = [
    {(0, 0), (0, 1), (0, 2)},  # Row 0
    {(1, 0), (1, 1), (1, 2)},  # Row 1
    {(2, 0), (2, 1), (2, 2)},  # Row 2
    {(0, 0), (1, 0), (2, 0)},  # Column 0
    {(0, 1), (1, 1), (2, 1)},  # Column 1
    {(0, 2), (1, 2), (2, 2)},  # Column 2
    {(0, 0), (1, 1), (2, 2)},  # Diagonal 0
    {(0, 2), (1, 1), (2, 0)},  # Diagonal 1
]

def checkwinner(board, p):
    # Get all positions occupied by the player
    player_positions = {(i, j) for i in range(3) for j in range(3) if board[i][j] == p}
    
    # Check if any of the winning patterns is completely contained within the player's positions
    return any(pattern <= player_positions for pattern in winning_patterns)


def winner(board):
    """
    Returns the winner of the game, if there is one.
    """
    if checkwinner(board, X):
        return X
    elif checkwinner(board, O):
        return O
    else:
        return None

def terminal(board):
    """
    Returns True if game is over, False otherwise.
    """
    return winner(board) is not None or not actions(board)

def utility(board):
    """
    Returns 1 if X has won the game, -1 if O has won, 0 otherwise.
    """
    t = winner(board)
    if t == X:
        return 1
    elif t == O:
        return -1
    else:
        return 0

# Cache to store the results of previously computed board states
cache = {}

def minimax(board):
    """
    Returns the optimal action for the current player on the board using alpha-beta pruning,
    with caching to avoid redundant calculations.
    """
    # Convert the board to a hashable tuple of tuples
    board_tuple = tuple(map(tuple, board))
    
        # Check if the board is empty
    if all(cell == EMPTY for row in board for cell in row):
        random_action = random.choice(list(actions(board)))
        cache[board_tuple] = random_action
        return random_action
    
    # Check if the result for this board state is already cached
    if board_tuple in cache:
        return cache[board_tuple]

    # If the game is over, return None
    if terminal(board):
        return None

    current_player = player(board)
    if current_player == X:
        _, action = max_value(board, -math.inf, math.inf)
    else:
        _, action = min_value(board, -math.inf, math.inf)
    
    # Cache the result (action) for the current board state
    cache[board_tuple] = action
    return action

def max_value(board, alpha, beta):
    if terminal(board):
        return utility(board), None

    v = -math.inf
    best_action = None

    for action in actions(board):
        min_val, _ = min_value(result(board, action), alpha, beta)
        if min_val > v:
            v = min_val
            best_action = action

        alpha = max(alpha, v)
        if alpha >= beta:
            break

    return v, best_action

def min_value(board, alpha, beta):
    if terminal(board):
        return utility(board), None

    v = math.inf
    best_action = None

    for action in actions(board):
        max_val, _ = max_value(result(board, action), alpha, beta)
        if max_val < v:
            v = max_val
            best_action = action

        beta = min(beta, v)
        if alpha >= beta:
            break

    return v, best_action
