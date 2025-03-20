import math
import copy
import time
import os
from collections import defaultdict

class MiniChess:
    """
        Initialize MiniChess game instance

        Args:
            - playmode: string | Play mode: H-H (for now, only Human vs. Human is supported)
            - maxturns: int | Maximum number of turns
    """
    def __init__(self, playmode='H-H', maxturns=10, timeout=5, alpha_beta=False, heuristic_white='e0', heuristic_black='e0'):
        self.current_game_state = self.init_board()
        self.playmode = playmode
        self.maxturns = maxturns
        self.turn_count = 0
        self.piece_count_history = []
        self.game_over = False
        self.result = None
        self.move_count = 1

        # AI parameter
        self.timeout = timeout 
        self.alpha_beta = alpha_beta
        self.heuristics = {'white': heuristic_white, 'black': heuristic_black}  # Initialize heuristics
        self.stats = {"states_explored": 0, "depth_counts": defaultdict(int), "total_branches": 0, "total_parent_nodes": 0}  
        
        self.output_buffer = []
        self.filename = self.get_next_filename()

    def log(self, message, end='\n'):
        self.output_buffer.append(message + end)
        print(message, end=end)

    """
    Initialize the board configuration

    Args:
        - None

    Returns:
        - state: A dictionary representing the state of the game
    """
    def init_board(self):
        state = {
                "board": 
                [['bK', 'bQ', 'bB', 'bN', '.'],
                ['.', '.', 'bp', 'bp', '.'],
                ['.', '.', '.', '.', '.'],
                ['.', 'wp', 'wp', '.', '.'],
                ['.', 'wN', 'wB', 'wQ', 'wK']],
                "turn": 'white',
                }
        return state

    """
    Prints the board state to the console
    
    Args:
        - game_state: Dictionary representing the current game state
    Returns:
        - None
    """
    def display_board(self, game_state):
        board_str = []
        board_str.append("\n                  A     B    C    D    E")
        board_str.append("                +----+----+----+----+----+")
        for i, row in enumerate(game_state["board"], start=1):
            row_str = f"              {6 - i} | " + " | ".join(piece if piece != '.' else '  ' for piece in row) + " | " + f"{6 - i}"
            board_str.append(row_str)
            board_str.append("                +----+----+----+----+----+")
        board_str.append("                  A     B    C    D    E\n")
        return '\n'.join(board_str)

    """
    Check if the move is valid    
    
    Args: 
        - game_state:   dictionary | Dictionary representing the current game state
        - move          tuple | the move which we check the validity of ((start_row, start_col),(end_row, end_col))
    Returns:
        - boolean representing the validity of the move
    """
    def is_valid_move(self, game_state, move):
        # Check if move is in list of valid moves
        return move in self.valid_moves(game_state)

    """
    Returns a list of valid moves

    Args:
        - game_state:   dictionary | Dictionary representing the current game state
    Returns:
        - valid moves:   list | A list of nested tuples corresponding to valid moves [((start_row, start_col),(end_row, end_col)),((start_row, start_col),(end_row, end_col))]
    """
    def valid_moves(self, game_state):
        # Return a list of all the valid moves.
        # Implement basic move validation
        # Check for out-of-bounds, correct turn, move legality, etc

        valid_moves = []
        current_player = game_state['turn']
        opponent_color = 'b' if current_player == 'white' else 'w'
        board = game_state["board"]
        rows, cols = 5, 5

        # Nested loop to iterate through the board to find all valid moves
        for row in range(rows):
            for col in range(cols):
                piece = board[row][col]
                if piece == '.' or piece[0] != ('w' if current_player == 'white' else 'b'):
                    continue
                piece_type = piece[1]
 
                if piece_type == 'K': # King
                    # King can move one square in any direction
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]
                    for dir_row, dir_col in directions:
                        new_row, new_col = row + dir_row, col + dir_col
                        if 0 <= new_row < rows and 0 <= new_col < cols:
                            target = board[new_row][new_col]
                            if target == '.' or target[0] == opponent_color:
                                valid_moves.append(((row, col), (new_row, new_col)))
                
                elif piece_type == 'Q': # Queen
                    # Queen can move any number of squares in any direction
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
                    for dir_row, dir_col in directions:
                        step = 1
                        while True:
                            new_row, new_col = row + step * dir_row, col + step * dir_col
                            if not (0 <= new_row < rows and 0 <= new_col < cols):
                                break
                            target = board[new_row][new_col]
                            if target == '.':
                                valid_moves.append(((row, col), (new_row, new_col)))
                            elif target[0] == opponent_color:
                                valid_moves.append(((row, col), (new_row, new_col)))
                                break
                            else:
                                break
                            step += 1

                elif piece_type == 'B': # Bishop
                    # Bishop can move any number of squares diagonally
                    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                    for dir_row, dir_col in directions:
                        step = 1
                        while True:
                            new_row, new_col = row + step * dir_row, col + step * dir_col
                            
                            # Check if new position is out of bounds
                            if not (0 <= new_row < rows and 0 <= new_col < cols):
                                break
                            target = board[new_row][new_col]
                            
                            # Check if new position is empty
                            if target == '.':
                                valid_moves.append(((row, col), (new_row, new_col)))
                            
                            # Check if new position has opponent piece
                            elif target[0] == opponent_color:
                                valid_moves.append(((row, col), (new_row, new_col)))
                                break
                            
                            # If new position has same color piece, break
                            else:
                                break
                            step += 1

                elif piece_type == 'N': # Knight
                    # Knight can move in an L-shape (2 squares in one direction, 1 square perpendicular)
                    directions = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2)]
                    for dir_row, dir_col in directions:
                        new_row, new_col = row + dir_row, col + dir_col
                        if 0 <= new_row < rows and 0 <= new_col < cols:
                            target = board[new_row][new_col]
                            if target == '.' or target[0] == opponent_color:
                                valid_moves.append(((row, col), (new_row, new_col)))

                elif piece_type == 'p': # Pawn   
                    # Pawn can move one square forward
                    if current_player == 'white':
                        # white pawn moves up the board
                        if row - 1 >= 0 and board[row - 1][col] == '.':
                            valid_moves.append(((row, col), (row-1, col)))
                        
                        # white pawn captures diagonally
                        for dir_col in [-1, 1]:
                            if col + dir_col < 0 or col + dir_col >= cols:
                                continue
                            if row - 1 >= 0 and board[row-1][col+dir_col][0] != '.' and board[row - 1][col + dir_col][0] == 'b':
                                valid_moves.append(((row, col), (row - 1, col + dir_col)))
                    
                    else:
                    # Black pawn moves forward (down the board)
                        if row + 1 < rows and board[row + 1][col] == '.':
                            valid_moves.append(((row, col), (row + 1, col)))
                        # Black pawn captures diagonally
                        for dc in [-1, 1]:
                            if col + dc < 0 or col + dc >= cols:
                                continue
                            if row + 1 < rows and board[row + 1][col + dc] != '.' and board[row + 1][col + dc][0] == 'w':
                                valid_moves.append(((row, col), (row + 1, col + dc)))

        return valid_moves
    
    """
    Count the number of pieces on the board

    Args:
        - board: list | List of lists representing the board state

    Returns:
        - int | Number of non-empty squares on the board
    """
    
    def count_pieces(self, board):
        return sum(cell != '.' for row in board for cell in row)

    """
    Execute the move on the board and update the game state

    Args: 
        - game_state:   dictionary | Dictionary representing the current game state
        - move          tuple | the move to perform ((start_row, start_col),(end_row, end_col))
    Returns:
        - game_state:   dictionary | Dictionary representing the modified game state
    """
    def make_move(self, game_state, move, is_ai_evaluation=False):
        start, end = move
        start_row, start_col = start
        end_row, end_col = end
        piece = game_state["board"][start_row][start_col]
        target_piece = game_state["board"][end_row][end_col]

        # Log the move and target piece only during actual gameplay
        if not is_ai_evaluation:
            self.log(f"Moving {piece} from {self.convert_to_notation(start)} to {self.convert_to_notation(end)}")
            if target_piece != '.':
                self.log(f"Capturing {target_piece} at {self.convert_to_notation(end)}")

        # Make the move FIRST
        game_state["board"][start_row][start_col] = '.'
        game_state["board"][end_row][end_col] = piece

        # Check if the move captured the opponent's king
        if not is_ai_evaluation and target_piece != '.':
            if target_piece[1] == 'K':
                opponent_color = 'b' if game_state["turn"] == 'white' else 'w'
                if target_piece[0] == opponent_color:
                    self.log(f"Game over! {game_state['turn'].capitalize()} wins by capturing the king.")
                    self.game_over = True
                    self.result = f"{game_state['turn'].capitalize()} wins by capturing the king in {self.turn_count + 1} turns."
                    
                    # Still process promotions and turn toggle for accurate board state
                    if piece[1] == 'p':
                        if (piece[0] == 'w' and end_row == 0) or (piece[0] == 'b' and end_row == 4):
                            game_state["board"][end_row][end_col] = piece[0] + 'Q'
                    
                    game_state["turn"] = 'black' if game_state["turn"] == 'white' else 'white'
                    return game_state

        # Pawn promotion
        if piece[1] == 'p':
            if (piece[0] == 'w' and end_row == 0) or (piece[0] == 'b' and end_row == 4):
                game_state["board"][end_row][end_col] = piece[0] + 'Q'

        # Toggle turn
        game_state["turn"] = 'black' if game_state["turn"] == 'white' else 'white'

        # Update turn count after Black's move
        if not is_ai_evaluation and game_state["turn"] == 'white':
            self.turn_count += 1
            current_count = self.count_pieces(game_state["board"])
            self.piece_count_history.append(current_count)

            if self.turn_count >= self.maxturns:
                self.game_over = True
                self.result = "Draw by reaching max turns"
            
            elif self.turn_count >= 10:
                last_ten = self.piece_count_history[-10:]
                if all(x == last_ten[0] for x in last_ten):
                    self.game_over = True
                    self.result = "Draw by 10 turns with no captures"

        return game_state
        
    """
    Parse the input string and modify it into board coordinates

    Args:
        - move: string representing a move "B2 B3"
    Returns:
        - (start, end)  tuple | the move to perform ((start_row, start_col),(end_row, end_col))
    """
    def parse_input(self, move):
        try:
            start, end = move.split()
            start_row = 5 - int(start[1])
            start_col = ord(start[0].upper()) - ord('A')
            end_row = 5 - int(end[1])
            end_col = ord(end[0].upper()) - ord('A')

            if 0 <= start_row < 5 and 0 <= end_row < 5 and 0 <= start_col < 5 and 0 <= end_col < 5:
                return ((start_row, start_col), (end_row, end_col))
        except:
            return None

    """
    Convert board coordinates to chess notation

    Args:
        - pos: tuple representing the board coordinates (row, col)
    Returns:
        - string representing the chess notation "B2"
    """

    def convert_to_notation(self, pos):
        row, col = pos
        return f"{chr(col + ord('A'))}{5 - row}"
    


    """
    Generate the next filename for the game trace

    Args:
        - None
    Returns:
        - string representing the filename
    """
    def get_next_filename(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        base_name = os.path.join(base_dir, "gameTrace")
        index = 1
        while True:
            filename = f"{base_name}{index}-{alpha_beta}-{timeout}-{maxturns}.txt"
            if not os.path.exists(filename):
                self.log(f"\nCreating game trace file: {filename}\n")
                return filename
            index += 1

    # AI functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`
    
    """
        Evaluate board using heuristic e0:
        (#wp + 3*#wB + 3*#wN + 9*#wQ + 999*wK) − (#bp + 3*#bB + 3*#bN + 9*#bQ + 999*bK)
        """
    def evaluate_state(self, state):
        current_player = state['turn']
        heuristic = self.heuristics[current_player]
        
        if heuristic == 'e0':
            return self.evaluate_state_e0(state)
        elif heuristic == 'e1':
            return self.evaluate_state_e1(state)
        elif heuristic == 'e2':
            return self.evaluate_state_e2(state)
        else:
            return 0  # Default heuristic

    def evaluate_state_e0(self, state):
        piece_values = {'p': 1, 'B': 3, 'N': 3, 'Q': 9, 'K': 999}
        white_score = 0
        black_score = 0
        
        for row in state["board"]:
            for cell in row:
                if cell == '.':
                    continue
                color = cell[0]
                piece_type = cell[1]
                value = piece_values.get(piece_type, 0)
                if color == 'w':
                    white_score += value
                elif color == 'b':
                    black_score += value
        
        return white_score - black_score

    def evaluate_state_e1(self, state):
        # Material score from e0
        material_score = self.evaluate_state_e0(state)
        
        positional_score = 0
        
        # Positional tables
        pawn_white_pos = [
            [5, 5, 5, 5, 5],  # Promotion row (row 0)
            [4, 4, 4, 4, 4],
            [3, 3, 3, 3, 3],
            [2, 2, 2, 2, 2],  # Initial position (row 3)
            [1, 1, 1, 1, 1],
        ]
        
        pawn_black_pos = [
            [1, 1, 1, 1, 1],
            [2, 2, 2, 2, 2],  # Initial position (row 1)
            [3, 3, 3, 3, 3],
            [4, 4, 4, 4, 4],
            [5, 5, 5, 5, 5],  # Promotion row (row 4)
        ]
        
        central_scores = [
            [1, 1, 2, 1, 1],
            [1, 2, 3, 2, 1],
            [2, 3, 4, 3, 2],
            [1, 2, 3, 2, 1],
            [1, 1, 2, 1, 1],
        ]
        
        for row_idx in range(5):
            for col_idx in range(5):
                piece = state["board"][row_idx][col_idx]
                if piece == '.':
                    continue
                color, piece_type = piece[0], piece[1]
                
                if piece_type == 'p':
                    if color == 'w':
                        positional_score += pawn_white_pos[row_idx][col_idx]
                    else:
                        positional_score += pawn_black_pos[row_idx][col_idx]
                else:
                    # Apply central score for non-pawn pieces
                    positional_score += central_scores[row_idx][col_idx]
        
        # Weight positional score to balance with material
        return material_score + positional_score * 0.5

    def evaluate_state_e2(self, state):
        # Material score from e0
        material_score = self.evaluate_state_e0(state)
        
        # Temporarily calculate mobility for both players
        original_turn = state['turn']
        
        # Calculate white's mobility
        state['turn'] = 'white'
        white_moves = len(self.valid_moves(state))
        
        # Calculate black's mobility
        state['turn'] = 'black'
        black_moves = len(self.valid_moves(state))
        
        # Restore original turn
        state['turn'] = original_turn
        
        # Mobility score with scaling factor
        mobility_score = white_moves - black_moves
        return material_score + 0.2 * mobility_score

    def order_moves(self, state, moves):
        """Prioritize capturing moves based on piece values."""
        piece_values = {'p': 1, 'B': 3, 'N': 3, 'Q': 9, 'K': 999}
        def move_value(move):
            _, end_pos = move
            end_piece = state["board"][end_pos[0]][end_pos[1]]
            if end_piece == '.':
                return 0
            return piece_values.get(end_piece[1], 0)
        return sorted(moves, key=move_value, reverse=True)

    # Minimax with Alpha-Beta pruning
    def minimax(self, state, current_depth, max_depth, maximizing, alpha, beta, start_time, time_limit):
        # Increment the states explored counter and depth counts
        self.stats["states_explored"] += 1
        self.stats["depth_counts"][current_depth] += 1

        if time.time() - start_time >= time_limit:
            return self.evaluate_state(state), alpha, beta
        
        if current_depth == max_depth or self.game_over:
            return self.evaluate_state(state), alpha, beta

        moves = self.order_moves(state, self.valid_moves(state))
        
        if not moves:
            return self.evaluate_state(state), alpha, beta

        # Track branching factor
        num_branches = len(moves)
        self.stats["total_branches"] += num_branches
        self.stats["total_parent_nodes"] += 1

        if maximizing:
            value = -math.inf
            for move in moves:
                new_state = self.make_move(copy.deepcopy(state), move, is_ai_evaluation=True)
                eval_score, _, _ = self.minimax(new_state, current_depth + 1, max_depth, False, alpha, beta, start_time, time_limit)
                value = max(value, eval_score)
                if self.alpha_beta:
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break
            return value, alpha, beta
        else:
            value = math.inf
            for move in moves:
                new_state = copy.deepcopy(state)
                self.make_move(new_state, move, is_ai_evaluation=True)
                eval_score, new_alpha, new_beta = self.minimax(new_state, current_depth + 1, max_depth, True, alpha, beta, start_time, time_limit)
                value = min(value, eval_score)
                if self.alpha_beta:
                    beta = min(beta, value)
                    if beta <= alpha:
                        break
            return value, alpha, beta

    def get_best_move(self, state, time_limit):
        # Reset counters for this move
        self.stats["states_explored"] = 0
        self.stats["depth_counts"] = defaultdict(int)
        self.stats["total_branches"] = 0
        self.stats["total_parent_nodes"] = 0

        start_time = time.time()
        best_move = None
        best_value = -math.inf if state["turn"] == "white" else math.inf
        moves = self.order_moves(state, self.valid_moves(state))
        if not moves:
            return None

        max_depth = 3  # Maximum allowed depth
        current_max_depth = 1  # Start with depth 1
        time_remaining = time_limit

        while time_remaining > 0 and current_max_depth <= max_depth:
            depth_start_time = time.time()
            self.log(f"Searching at depth {current_max_depth}...")
            current_best_move = None
            current_best_value = -math.inf if state["turn"] == "white" else math.inf

            for move in moves:
                if time.time() - start_time > time_limit:
                    break

                new_state = copy.deepcopy(state)
                self.make_move(new_state, move, is_ai_evaluation=True)
                eval_score, alpha, beta = self.minimax(
                    new_state,
                    current_depth=0,
                    max_depth=current_max_depth,
                    maximizing=(state["turn"] == "black"),
                    alpha=-math.inf,
                    beta=math.inf,
                    start_time=start_time,
                    time_limit=time_limit
                )

                # Update best move for current depth
                if (state["turn"] == "white" and eval_score > current_best_value) or \
                (state["turn"] == "black" and eval_score < current_best_value):
                    current_best_value = eval_score
                    current_best_move = move

            # Update global best move if depth completed
            if current_best_move:
                best_move = current_best_move
                best_value = current_best_value
                self.log(f"Reached search depth: {current_max_depth}")
                current_max_depth += 1
            else:
                break

            # Update remaining time
            elapsed = time.time() - start_time
            time_remaining = time_limit - elapsed

        # Final time check
        total_time = time.time() - start_time
        if total_time > time_limit:
            self.log("AI exceeded timeout! Forfeiting turn.")
            return None

        # Log results
        if best_move:
            self.log(f"AI chooses: {self.convert_to_notation(best_move[0])} to {self.convert_to_notation(best_move[1])}")
            self.log(f"Minimax/Alpha-Beta Search Score: {best_value}")
            self.log(f"Time taken: {total_time:.2f} seconds")

            # Cumulative states explored
            self.log(f"Cumulative states explored: {self.stats['states_explored']}")

            # States explored by depth
            self.log("Cumulative states explored by depth:")
            max_depth_reached = max(self.stats["depth_counts"].keys(), default=0)
            for d in range(max_depth_reached + 1):
                count = self.stats["depth_counts"].get(d, 0)
                self.log(f"  Depth {d}: {count}")

            # Percentage of states explored by depth
            total_states = self.stats["states_explored"]
            self.log("Cumulative % states explored by depth:")
            for d in range(max_depth_reached + 1):
                count = self.stats["depth_counts"].get(d, 0)
                percentage = (count / total_states) * 100 if total_states else 0
                self.log(f"  Depth {d}: {percentage:.1f}%")

            # Average branching factor
            if self.stats["total_parent_nodes"] > 0:
                avg_branch = self.stats["total_branches"] / self.stats["total_parent_nodes"]
            else:
                avg_branch = 0
            self.log(f"Average branching factor: {avg_branch:.1f}")

        return best_move

    """
    Main game loop handling player input and game progression

    Args:
        - None
    Returns:
        - None
    """

    def play(self):
        white_is_ai = 'AI' in self.playmode.split('-')[0].upper()
        black_is_ai = 'AI' in self.playmode.split('-')[1].upper()

        params = [
            f"                **************************",
            f"                   Playmode: {self.playmode}",
            f"                   Max turns: {self.maxturns}",
            f"                   Timeout: {self.timeout}",
            f"                   Alpha-beta: {self.alpha_beta}",
            f"                   Heuristic (White): {self.heuristics['white']}",
            f"                   Heuristic (Black): {self.heuristics['black']}",
            f"                **************************",
            "\n               Initial Board Configuration:",
            "              ______________________________",
            self.display_board(self.current_game_state) 
        ]
        self.log("\n".join(params))

        self.log("\nWelcome to Mini Chess! Enter moves as 'B2 B3'. Type 'exit' to quit.")


        while not self.game_over:
            current_player = self.current_game_state['turn']
            is_ai_turn = (current_player == 'white' and white_is_ai) or (current_player == 'black' and black_is_ai)

            if is_ai_turn:
                move_start_time = time.time()
                move = self.get_best_move(self.current_game_state, self.timeout)
                move_time_taken = time.time() - move_start_time

                if not move:
                    self.log(f"{current_player} AI exceeded timeout! Automatic loss.")
                    self.game_over = True
                    self.result = f"{current_player} AI lost by timeout."
                    break

                move_str = f"{self.convert_to_notation(move[0])} {self.convert_to_notation(move[1])}"
                self.log(f"                      AI plays: {move_str}")
                self.log(f"                      Time taken: {move_time_taken:.2f} seconds")

                # Log heuristic score of the resulting board
                new_state = copy.deepcopy(self.current_game_state)
                self.make_move(new_state, move, is_ai_evaluation=True)
                heuristic_score = self.evaluate_state(new_state)
                self.log(f"                      Heuristic Score of Resulting Board: {heuristic_score}")
            
            else:
                move_str = input(f"                   {current_player.capitalize()} to move: ").strip()
                self.output_buffer.append(f"                   {current_player.capitalize()} to move: {move_str}")

            if move_str.lower() == 'exit':
                self.log("\nGame exited by user.")
                break

            move = self.parse_input(move_str)
            if not move or not self.is_valid_move(self.current_game_state, move):
                self.log("      * * * * * * Invalid move. Try again. * * * * * *")
                continue

            start_notation = self.convert_to_notation(move[0])
            end_notation = self.convert_to_notation(move[1])
            turn_number = (self.move_count + 1) // 2
            self.log(f"\n     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n                  | Player: {current_player}    |\n                  | Turn #: {turn_number}        |\n                  | Action: {start_notation} to {end_notation} |\n") 

            self.make_move(self.current_game_state, move)
            self.move_count += 1

            self.log("                  New board configuration:")
            self.log(self.display_board(self.current_game_state))
        
        if self.game_over:
            self.log(f"\n     ++++++++++++++++++++++++++++++++++++++++++++++++++++++\n     Game over! {self.result} \n     ++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")

        with open(self.filename, 'w') as f:
            f.write("\n".join(self.output_buffer))
        print(f"Game trace written to file: {self.filename}")

        exit()


if __name__ == "__main__":
    # Prompt for parameters interactively.
    p1 = input("\nEnter Player 1 mode (H for Human or AI for AI): ").strip().upper()
    p2 = input("Enter Player 2 mode (H for Human or AI for AI): ").strip().upper()
    playmode = f"{p1}-{p2}"
    
    # Prompt for max turns for all playmodes
    try:
        maxturns = int(input("Enter maximum number of turns: ").strip())
    except ValueError:
        maxturns = 100

    # Initialize AI-specific parameters
    timeout = "N/A"  # Default timeout for human players
    alpha_beta = False
    heuristic_white = "N/A"  # Default heuristic for human players
    heuristic_black = "N/A"  # Default heuristic for human players

    # Determine if there are one or two AI players
    ai_count = (1 if p1 == "AI" else 0) + (1 if p2 == "AI" else 0)

    # Prompt for AI parameters only if at least one player is AI.
    if ai_count > 0:
        # Prompt for timeout only if at least one player is AI
        try:
            timeout = float(input(f"Enter AI move timeout (in seconds) for the {'AI player' if ai_count == 1 else 'AI players'}: ").strip())
        except ValueError:
            timeout = 5  # Default timeout if invalid input
        
        # Prompt for alpha-beta pruning once (applies to both players if they are AI)
        alpha_beta = input(f"Force alpha-beta pruning for the {'AI player' if ai_count == 1 else 'AI players'}? (true/false): ").strip().lower() in ['true', 't', 'yes', '1']
        
        # Prompt for heuristic for each AI player
        if p1 == "AI":
            heuristic_white = input(f"Enter heuristic for White AI [e0, e1, e2]: ").strip().lower()
            if heuristic_white not in ['e0', 'e1', 'e2']:
                heuristic_white = 'e0'
        if p2 == "AI":
            heuristic_black = input(f"Enter heuristic for Black AI [e0, e1, e2]: ").strip().lower()
            if heuristic_black not in ['e0', 'e1', 'e2']:
                heuristic_black = 'e0'
    
    # Initialize the game with the correct heuristics
    game = MiniChess(
        playmode=playmode,
        maxturns=maxturns,
        timeout=timeout,
        alpha_beta=alpha_beta,
        heuristic_white=heuristic_white,
        heuristic_black=heuristic_black
    )
    game.play()