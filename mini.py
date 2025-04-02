import math
import copy
import time
import os
import re
import random
from collections import defaultdict

def clean_text(text):
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

class MiniChess:
    def __init__(self, playmode='H-H', maxturns=10, timeout=2, 
                 alpha_beta=False, heuristic_white='e0', heuristic_black='e0'):
        self.current_game_state = self.init_board()
        self.playmode = playmode
        self.maxturns = maxturns
        self.turn_count = 0
        self.piece_count_history = []
        self.game_over = False
        self.result = None
        self.move_count = 1
        self.timeout = timeout
        self.alpha_beta = alpha_beta
        self.heuristics = {'white': heuristic_white, 'black': heuristic_black}
        self.stats = {"states_explored": 0, "depth_counts": defaultdict(int), 
                      "total_branches": 0, "total_parent_nodes": 0}
        self.output_buffer = []
        self.filename = self.get_next_filename()

    def init_board(self):
        """Initialize the board configuration with validation"""
        board = [
            ['bK', 'bQ', 'bB', 'bN', '.'],
            ['.', '.', 'bp', 'bp', '.'],
            ['.', '.', '.', '.', '.'],
            ['.', 'wp', 'wp', '.', '.'],
            ['.', 'wN', 'wB', 'wQ', 'wK']
        ]
        # Validate all pieces
        for row in board:
            for i, piece in enumerate(row):
                if not self.is_valid_piece(piece):
                    row[i] = '.'  # Reset invalid pieces
        return {"board": board, "turn": 'white'}

    def display_board(self, game_state):
        """Print the board state."""
        board_str = ["\n                  A     B    C    D    E",
                    "                +----+----+----+----+----+"]
        for i, row in enumerate(game_state["board"], 1):
            row_display = f"              {6 - i} | " + " | ".join(piece if piece != '.' else '  ' for piece in row) + " | " + f"{6 - i}"
            board_str.append(row_display)
            board_str.append("                +----+----+----+----+----+")
        board_str.append("                  A     B    C    D    E\n")
        return '\n'.join(board_str)

    def make_move(self, game_state, move, is_ai_evaluation=False):
        """Execute a move and check for game completion."""
        start, end = move
        start_row, start_col = start
        end_row, end_col = end

        piece = game_state["board"][start_row][start_col]
        target_piece = game_state["board"][end_row][end_col]

        # Move the piece
        game_state["board"][start_row][start_col] = '.'
        game_state["board"][end_row][end_col] = piece

        # Check for king capture
        if target_piece and target_piece[1] == 'K':
            self.game_over = True
            self.result = f"{game_state['turn'].capitalize()} wins by capturing the king"
            return

        # Check for pawn promotion
        if piece[1] == 'p' and ((piece[0] == 'w' and end_row == 0) or (piece[0] == 'b' and end_row == 4)):
            game_state["board"][end_row][end_col] = piece[0] + 'Q'

        # Switch turns
        game_state["turn"] = 'black' if game_state["turn"] == 'white' else 'white'

        # Update turn count
        if not is_ai_evaluation and game_state["turn"] == 'white':
            self.turn_count += 1
            if self.turn_count >= self.maxturns:
                self.game_over = True
                self.result = "Draw by max turns"

        return game_state

    def run_tournament(self, rounds=3):
        """Run a stable tournament between heuristics with better error handling"""
        results = {
            'e0': {'wins': 0, 'losses': 0, 'draws': 0},
            'e1': {'wins': 0, 'losses': 0, 'draws': 0},
            'e2': {'wins': 0, 'losses': 0, 'draws': 0}
        }
        
        matchups = [('e0', 'e1'), ('e1', 'e2'), ('e2', 'e0')]
        
        for idx, (white, black) in enumerate(matchups, 1):
            print(f"\nGame {idx}: {white} vs {black}")
            try:
                # Reset game with new heuristics
                self.__init__(playmode='AI-AI', timeout=1, maxturns=10,
                            heuristic_white=white, heuristic_black=black)
                
                # Validate initial board
                for row in self.current_game_state["board"]:
                    for piece in row:
                        if not self.is_valid_piece(piece):
                            raise ValueError(f"Invalid piece '{piece}' in initial board")
                
                start_time = time.time()
                move_count = 0
                winner = None
                
                while not self.game_over and move_count < 10:
                    # Check kings manually with validation
                    wk_present = any('wK' in row for row in self.current_game_state["board"])
                    bk_present = any('bK' in row for row in self.current_game_state["board"])
                    
                    if not wk_present:
                        winner = 'black'
                        break
                    if not bk_present:
                        winner = 'white'
                        break
                    
                    # Get AI move with timeout protection
                    try:
                        move = self.get_best_move(self.current_game_state, 0.5)
                        if not move:
                            break
                            
                        self.make_move(self.current_game_state, move)
                        move_count += 1
                    except Exception as e:
                        print(f"Move error: {str(e)}")
                        break
                    
                # Record results
                if winner:
                    results[white if winner == 'white' else black]['wins'] += 1
                    results[black if winner == 'white' else white]['losses'] += 1
                else:
                    results[white]['draws'] += 1
                    results[black]['draws'] += 1
                    
                print(f"  Completed in {time.time()-start_time:.1f}s - {winner if winner else 'Draw'}")
                
            except Exception as e:
                print(f"  Game failed: {str(e)}")
                # Count the failure as a loss for both to avoid skewing results
                results[white]['losses'] += 1
                results[black]['losses'] += 1
                continue
    # Add other necessary methods (valid_moves, get_best_move, evaluate_state, etc.)
    # [Include all other methods from previous implementations]
    # Move Validation and Execution
    def is_valid_move(self, game_state, move):
        """Check if the move is valid."""
        return move in self.valid_moves(game_state)

    def is_valid_piece(self, piece):
        """Check if a piece representation is valid"""
        if piece == '.':
            return True
        return (len(piece) == 2 and 
                piece[0] in ('w', 'b') and 
                piece[1] in ('p', 'B', 'N', 'Q', 'K'))

    def valid_moves(self, game_state):
        """Returns a list of valid moves."""
        valid_moves = []
        current_player = game_state['turn']
        opponent_color = 'b' if current_player == 'white' else 'w'
        board = game_state["board"]
        rows, cols = 5, 5

        # Iterate over the board to find valid moves
        for row in range(rows):
            for col in range(cols):
                piece = board[row][col]
                if piece == '.' or piece[0] != ('w' if current_player == 'white' else 'b'):
                    continue # Skip empty cells or opponent pieces
                piece_type = piece[1]

                # King moves
                if piece_type == 'K':  
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]
                    for dir_row, dir_col in directions:
                        new_row, new_col = row + dir_row, col + dir_col
                        if 0 <= new_row < rows and 0 <= new_col < cols:
                            target = board[new_row][new_col]
                            if target == '.' or target[0] == opponent_color:
                                valid_moves.append(((row, col), (new_row, new_col)))

                # Queen moves
                elif piece_type == 'Q':  
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

                # Bishop moves
                elif piece_type == 'B': 
                    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
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

                # Knight moves
                elif piece_type == 'N': 
                    directions = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2)]
                    for dir_row, dir_col in directions:
                        new_row, new_col = row + dir_row, col + dir_col
                        if 0 <= new_row < rows and 0 <= new_col < cols:
                            target = board[new_row][new_col]
                            if target == '.' or target[0] == opponent_color:
                                valid_moves.append(((row, col), (new_row, new_col)))

                # Pawn moves
                elif piece_type == 'p':  
                    # White pawn moves
                    if current_player == 'white':
                        if row - 1 >= 0 and board[row - 1][col] == '.':
                            valid_moves.append(((row, col), (row-1, col)))
                        for dir_col in [-1, 1]:
                            if col + dir_col < 0 or col + dir_col >= cols:
                                continue
                            if row - 1 >= 0 and board[row-1][col+dir_col][0] != '.' and board[row - 1][col + dir_col][0] == 'b':
                                valid_moves.append(((row, col), (row - 1, col + dir_col)))
                    
                    # Black pawn moves
                    else:
                        if row + 1 < rows and board[row + 1][col] == '.':
                            valid_moves.append(((row, col), (row + 1, col)))
                        for dc in [-1, 1]:
                            if col + dc < 0 or col + dc >= cols:
                                continue
                            if row + 1 < rows and board[row + 1][col + dc] != '.' and board[row + 1][col + dc][0] == 'w':
                                valid_moves.append(((row, col), (row + 1, col + dc)))

        return valid_moves


    def count_pieces(self, board):
        """Count the number of pieces on the board."""
        return sum(cell != '.' for row in board for cell in row)

    def parse_input(self, move):
        """Parse the input string and modify it into board coordinates."""
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

    def convert_to_notation(self, pos):
        """Convert board coordinates to chess notation."""
        row, col = pos
        return f"{chr(col + ord('A'))}{5 - row}"

    

    def get_next_filename(self):
        """Generate the next filename for the game trace."""
        base_dir = os.path.dirname(os.path.abspath(__file__))  # Get script directory
        trace_dir = os.path.join(base_dir, "game_traces")  # Ensure all traces go here

        # Ensure the directory exists
        os.makedirs(trace_dir, exist_ok=True)

        # Sanitize parameters (replace invalid characters)
        safe_alpha_beta = str(self.alpha_beta).replace("/", "_").replace("\\", "_")
        safe_timeout = str(self.timeout).replace("/", "_").replace("\\", "_")
        safe_maxturns = str(self.maxturns).replace("/", "_").replace("\\", "_")

        # Ensure 'N/A' is replaced with a safe character (underscore or empty string)
        safe_timeout = safe_timeout.replace("N/A", "NA")  # Change 'N/A' to 'NA'

        base_name = os.path.join(trace_dir, "gameTrace")
        index = 1

        while True:
            filename = f"{base_name}{index}-{safe_alpha_beta}-{safe_timeout}-{safe_maxturns}.txt"
            if not os.path.exists(filename):
                self.log(f"\nCreating game trace file: {filename}\n")

                # Clean and write the message to ensure no ANSI codes
                with open(filename, 'w') as f:
                    f.write(clean_text(f"\nCreating game trace file: {filename}\n"))

                return filename
            index += 1


    # AI Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~``
    def evaluate_state_e0(self, state):
        start_time = time.perf_counter()
        piece_values = {'p': 1, 'B': 3, 'N': 3, 'Q': 9, 'K': 999}
        white_score = 0
        black_score = 0
        
        for row in state["board"]:
            for cell in row:
                if cell == '.':
                    continue
                try:
                    color = cell[0]
                    piece_type = cell[1]
                    value = piece_values.get(piece_type, 0)
                    
                    print(f"Piece: {cell}, Value: {value}")  # Debug print
                    
                    if color == 'w':
                        white_score += value
                    elif color == 'b':
                        black_score += value
                except IndexError:
                    print(f"Warning: Invalid piece representation '{cell}'")
                    continue
            
        print(f"White total: {white_score}, Black total: {black_score}")  # Debug
        elapsed = (time.perf_counter() - start_time) * 1000
        return white_score - black_score, elapsed

    def evaluate_state_e0(self, state):
        start_time = time.perf_counter()
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
                
                print(f"Piece: {cell}, Value: {value}")  # Debug print
                
                if color == 'w':
                    white_score += value
                elif color == 'b':
                    black_score += value
        
        print(f"White total: {white_score}, Black total: {black_score}")  # Debug
        elapsed = (time.perf_counter() - start_time) * 1000
        return white_score - black_score, elapsed

    def evaluate_state_e1(self, state):
        """
        Evaluate the board using heuristic e1, which is a combination of material score 
        (based on the piece values) and positional score. The positional score considers 
        the positioning of pawns and pieces on the board.

        Parameters:
        - state (dict): The current game state, which includes the board configuration.

        Returns:
        - int: The evaluation score for the board. Positive values favor white, and 
        negative values favor black. The score is a weighted sum of material and positional scores.
        """
        start_time = time.perf_counter()

        # Evaluate material score using heuristic e0 (based on piece values)
        material_score, _ = self.evaluate_state_e0(state)  # Extract only the score
        
        # Initialize positional score, which will be modified based on piece positions
        positional_score = 0
        
        # Position values for white pawns based on their row and column (higher values are more favorable)
        pawn_white_pos = [
            [5, 5, 5, 5, 5],
            [4, 4, 4, 4, 4],
            [3, 3, 3, 3, 3],
            [2, 2, 2, 2, 2],
            [1, 1, 1, 1, 1],
        ]
        
        # Position values for black pawns (reverse of white pawn values)
        pawn_black_pos = [
            [1, 1, 1, 1, 1],
            [2, 2, 2, 2, 2],
            [3, 3, 3, 3, 3],
            [4, 4, 4, 4, 4],
            [5, 5, 5, 5, 5],
        ]
        
        # Central control values for pieces (central squares are more valuable)
        central_scores = [
            [1, 1, 2, 1, 1],
            [1, 2, 3, 2, 1],
            [2, 3, 4, 3, 2],
            [1, 2, 3, 2, 1],
            [1, 1, 2, 1, 1],
        ]
        
        # Loop through each cell on the board to evaluate piece positions
        for row_idx in range(5):
            for col_idx in range(5):
                piece = state["board"][row_idx][col_idx]
                
                # Skip empty cells
                if piece == '.':
                    continue
                
                # Extract the color and type of the piece
                color, piece_type = piece[0], piece[1]
                
                # If the piece is a pawn, evaluate its position
                if piece_type == 'p':
                    if color == 'w':
                        positional_score += pawn_white_pos[row_idx][col_idx]  # White pawn's position value
                    else:
                        positional_score += pawn_black_pos[row_idx][col_idx]  # Black pawn's position value
                else:
                    # For other pieces, add their position value based on central control
                    positional_score += central_scores[row_idx][col_idx]
        elapsed = (time.perf_counter() - start_time) * 1000

        # Return the total score, combining material and positional scores.
        # The positional score is weighted by a factor of 0.5.
        return material_score + positional_score * 0.5, elapsed

    def evaluate_state_e2(self, state):
        """
        Evaluate the board using heuristic e2, which combines material score 
        and mobility score. The mobility score is based on the number of valid 
        moves available for each player.

        Parameters:
        - state (dict): The current game state, which includes the board configuration.

        Returns:
        - float: The evaluation score for the board. Positive values favor white, 
        and negative values favor black. The score is a combination of material 
        and mobility scores.
        """
        start_time = time.perf_counter()

        # Evaluate material score using heuristic e0 (based on piece values)
        material_score, _ = self.evaluate_state_e0(state)  # Extract only the score
        
        # Save the original turn to restore after calculating mobility
        original_turn = state['turn']
        
        # Calculate the number of valid moves for white
        state['turn'] = 'white'
        white_moves = len(self.valid_moves(state))
        
        # Calculate the number of valid moves for black
        state['turn'] = 'black'
        black_moves = len(self.valid_moves(state))
        
        # Restore the original turn
        state['turn'] = original_turn
        
        # Calculate mobility score (white's valid moves minus black's valid moves)
        mobility_score = white_moves - black_moves
        
        elapsed = (time.perf_counter() - start_time) * 1000

        # Return the combined score, with mobility weighted by 0.2
        return material_score + 0.2 * mobility_score, elapsed

    def generate_random_board(self):
        """Generate more balanced random boards"""
        pieces = ['p', 'p', 'p', 'B', 'N', 'Q', 'K']  # Higher probability for pawns
        colors = ['w', 'b']
        board = []
        
        # Ensure at least one king per side
        white_king = False
        black_king = False
        
        for _ in range(5):
            row = []
            for _ in range(5):
                if random.random() < 0.5:  # 50% chance of piece
                    color = random.choice(colors)
                    piece = random.choice(pieces)
                    if piece == 'K':
                        if color == 'w' and not white_king:
                            white_king = True
                        elif color == 'b' and not black_king:
                            black_king = True
                        else:
                            piece = random.choice(['Q', 'B', 'N'])  # Don't add extra kings
                    row.append(color + piece)
                else:
                    row.append('.')
            board.append(row)
        
        # Add kings if missing
        if not white_king:
            board[random.randint(0,4)][random.randint(0,4)] = 'wK'
        if not black_king:
            board[random.randint(0,4)][random.randint(0,4)] = 'bK'
        
        return {"board": board, "turn": random.choice(['white', 'black'])}

    def batch_test_heuristics(self, heuristic, num_tests=10000, trace_file=None):
        """
        Run comprehensive testing of a heuristic on random board states.
        
        Args:
            heuristic (str): Heuristic to test ('e0', 'e1', or 'e2')
            num_tests (int): Number of test cases to run
            trace_file (str): File path to log results
            
        Returns:
            tuple: (avg_score, avg_time_ms)
        """
        total_score = 0.0
        total_time_ns = 0
        min_score = float('inf')
        max_score = -float('inf')
        scores = []  # Store all scores for variance calculation
        
        # Set the heuristic for both players for consistent evaluation
        self.heuristics = {'white': heuristic, 'black': heuristic}
        
        for i in range(num_tests):
            # Generate and evaluate random board
            state = self.generate_random_board()
            
            # Time the evaluation precisely
            start_time = time.perf_counter_ns()
            score, elapsed = self.evaluate_state(state)
            elapsed_ns = time.perf_counter_ns() - start_time
            
            # Validate return type
            if not isinstance(score, (int, float)):
                raise TypeError(f"Heuristic {heuristic} returned invalid score type: {type(score)}")
            
            # Update statistics
            scores.append(score)  # Store the score for variance calculation
            total_score += score
            total_time_ns += elapsed_ns
            min_score = min(min_score, score)
            max_score = max(max_score, score)
            
            # Progress reporting
            if (i+1) % 1000 == 0:
                print(f"Completed {i+1}/{num_tests} tests...")
        
        # Calculate averages
        avg_score = total_score / num_tests
        avg_time_ms = (total_time_ns / num_tests) / 1_000_000  # Convert ns → ms
        
        # Calculate standard deviation
        variance = sum((s - avg_score)**2 for s in scores) / num_tests
        std_dev = math.sqrt(variance)
        
        # Log results
        results = (
            f"\nHeuristic {heuristic} Test Results (N={num_tests}):\n"
            f"  Average Score: {avg_score:.4f} ± {std_dev:.4f}\n"
            f"  Score Range: [{min_score:.2f}, {max_score:.2f}]\n"
            f"  Average Time: {avg_time_ms:.6f} ms\n"
            f"  Total Test Duration: {total_time_ns/1_000_000_000:.2f} seconds\n"
        )
        
        print(results)
        
        if trace_file:
            with open(trace_file, 'a') as f:
                f.write(results)
                f.write("="*60 + "\n")
        
        return avg_score, avg_time_ms

    def order_moves(self, state, moves):
        """
        Prioritize capturing moves based on piece values.

        This function sorts a list of moves by the value of the piece being captured 
        at the destination square. The idea is to prioritize moves that capture 
        higher-valued pieces (e.g., Queens, Knights) over moves that don't capture 
        any pieces.

        Parameters:
        - state (dict): The current game state, including the board configuration.
        - moves (list): A list of moves to be ordered. Each move is represented as 
        a tuple of (start position, end position).

        Returns:
        - list: The moves sorted by the value of the piece being captured (if any).
        """
        
        # Piece values based on common chess piece values
        piece_values = {'p': 1, 'B': 3, 'N': 3, 'Q': 9, 'K': 999}

        # Define a helper function to get the value of the piece at the end position
        def move_value(move):
            # Extract the destination position from the move
            _, end_pos = move
            # Get the piece at the end position on the board
            end_piece = state["board"][end_pos[0]][end_pos[1]]
            
            # If the end position is empty, return a value of 0 (no piece captured)
            if end_piece == '.':
                return 0
            
            # Otherwise, return the value of the captured piece (based on the piece type)
            return piece_values.get(end_piece[1], 0)

        # Sort the moves by the value of the piece being captured, in descending order
        return sorted(moves, key=move_value, reverse=True)


    def minimax(self, state, current_depth, max_depth, maximizing, alpha, beta, start_time, time_limit):
        """
        Minimax algorithm with Alpha-Beta pruning for game decision-making.
        """
        # Increment the count for states explored and depth-specific node counts
        self.stats["states_explored"] += 1
        self.stats["depth_counts"][current_depth] += 1

        # Check if time limit has been exceeded; if so, return the current evaluation
        if time.time() - start_time >= time_limit:
            score, _ = self.evaluate_state(state)  # Extract only the score
            return score, alpha, beta

        # If we've reached the maximum depth or the game is over, evaluate the board state
        if current_depth == max_depth or self.game_over:
            score, _ = self.evaluate_state(state)  # Extract only the score
            return score, alpha, beta

        # Get the list of valid moves and order them based on their value
        moves = self.order_moves(state, self.valid_moves(state))
        
        # If there are no moves, evaluate the state (in case of a stalemate or no moves left)
        if not moves:
            score, _ = self.evaluate_state(state)  # Extract only the score
            return score, alpha, beta

        # Track the number of branches at this depth for statistics
        num_branches = len(moves)
        self.stats["total_branches"] += num_branches
        self.stats["total_parent_nodes"] += 1

        # Maximizing player
        if maximizing:
            value = -math.inf  # Start with a very low value for maximizer
            for move in moves:
                # Make the move and evaluate the new state recursively
                new_state = self.make_move(copy.deepcopy(state), move, is_ai_evaluation=True)
                eval_score, _, _ = self.minimax(new_state, current_depth + 1, max_depth, False, alpha, beta, start_time, time_limit)
                value = max(value, eval_score)  # Update value with the better score
                if self.alpha_beta:  # Apply Alpha-Beta pruning
                    alpha = max(alpha, value)
                    if alpha >= beta:  # Prune the search if alpha >= beta
                        break
            return value, alpha, beta

        # Minimizing player
        else:
            value = math.inf  # Start with a very high value for minimizer
            for move in moves:
                # Make the move and evaluate the new state recursively
                new_state = copy.deepcopy(state)
                self.make_move(new_state, move, is_ai_evaluation=True)
                eval_score, _, _ = self.minimax(new_state, current_depth + 1, max_depth, True, alpha, beta, start_time, time_limit)
                value = min(value, eval_score)  # Update value with the worse score
                if self.alpha_beta:  # Apply Alpha-Beta pruning
                    beta = min(beta, value)
                    if beta <= alpha:  # Prune the search if beta <= alpha
                        break
            return value, alpha, beta


    def get_best_move(self, state, time_limit):
        """
        Get the best move using Minimax with Alpha-Beta pruning.
        
        This function iteratively searches deeper into the game tree using the Minimax
        algorithm with Alpha-Beta pruning. It aims to find the best move while respecting
        the time limit. The function explores increasing depths of the game tree until
        the time limit is exhausted or the maximum depth is reached.

        Parameters:
        - state (dict): The current game state, including board and turn information.
        - time_limit (float): The maximum time allowed for the move search in seconds.
        
        Returns:
        - best_move (tuple): The best move for the AI, or None if no valid move is found.
        """
        
        # Initialize statistics for the search
        self.stats["states_explored"] = 0
        self.stats["depth_counts"] = defaultdict(int)
        self.stats["total_branches"] = 0
        self.stats["total_parent_nodes"] = 0

        # Start the timer for the search process
        start_time = time.time()
        best_move = None
        best_value = -math.inf if state["turn"] == "white" else math.inf
        
        # Get all possible valid moves and order them based on their value
        moves = self.order_moves(state, self.valid_moves(state))
        if not moves:
            return None  # If no valid moves, return None

        # Set maximum depth based on whether Alpha-Beta pruning is enabled
        max_depth = 4 if self.alpha_beta else 3
        current_max_depth = 1  # Start at depth 1
        time_remaining = time_limit  # Set the initial remaining time

        # Iteratively increase the depth until time limit is reached or max depth is exceeded
        while time_remaining > 0 and current_max_depth <= max_depth:
            depth_start_time = time.time()
            self.log(f"      Searching at depth {current_max_depth}...", color="blue")

            # Variables to track the best move and its value for the current depth
            current_best_move = None
            current_best_value = -math.inf if state["turn"] == "white" else math.inf

            # Evaluate each possible move at the current depth
            for move in moves:
                # Check if time limit has been exceeded during evaluation
                if time.time() - start_time > time_limit:
                    break

                # Make the move and create a new state to evaluate
                new_state = copy.deepcopy(state)
                self.make_move(new_state, move, is_ai_evaluation=True)

                # Perform Minimax with Alpha-Beta pruning for the current move
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

                # Update best move for the current depth based on evaluation score
                if (state["turn"] == "white" and eval_score > current_best_value) or \
                (state["turn"] == "black" and eval_score < current_best_value):
                    current_best_value = eval_score
                    current_best_move = move

            # If a best move was found at this depth, update the global best
            if current_best_move:
                best_move = current_best_move
                best_value = current_best_value
                self.log(f"                             Reached search depth: {current_max_depth}", color="blue")
                current_max_depth += 1  # Move to the next depth level
            else:
                break  # If no move is found, stop the search

            # Update the remaining time for the next iteration
            elapsed = time.time() - start_time
            time_remaining = time_limit - elapsed

        # Check if the total time taken exceeds the time limit
        total_time = time.time() - start_time
        if total_time > time_limit:
            self.log("AI exceeded timeout! Forfeiting turn.", color="red", bold=True)
            return None  # If the time limit is exceeded, return None

        # If a best move is found, log detailed search statistics
        if best_move:
            self.log(f"\n                  AI chooses: {self.convert_to_notation(best_move[0])} to {self.convert_to_notation(best_move[1])}", color="green", bold=True)
            self.log(f"\n          Minimax/Alpha-Beta Search Score: {best_value}", color="cyan")
            self.log(f"                  Time taken: {total_time:.2f} seconds", color="cyan")

            # Log cumulative states explored and depth statistics
            self.log(f"\n            Cumulative states explored: {self.stats['states_explored']}", color="cyan")
            self.log("\n          Cumulative states explored by depth:", color="cyan")
            max_depth_reached = max(self.stats["depth_counts"].keys(), default=0)
            for d in range(max_depth_reached + 1):
                count = self.stats["depth_counts"].get(d, 0)
                self.log(f"                     Depth {d}: {count}", color="cyan")

            # Log the percentage of states explored at each depth
            total_states = self.stats["states_explored"]
            self.log("\n          Cumulative % states explored by depth:", color="cyan")
            for d in range(max_depth_reached + 1):
                count = self.stats["depth_counts"].get(d, 0)
                percentage = (count / total_states) * 100 if total_states else 0
                self.log(f"                     Depth {d}: {percentage:.1f}%", color="cyan")

            # Log the average branching factor
            if self.stats["total_parent_nodes"] > 0:
                avg_branch = self.stats["total_branches"] / self.stats["total_parent_nodes"]
            else:
                avg_branch = 0
            self.log(f"\n             Average branching factor: {avg_branch:.1f}\n", color="cyan")

        return best_move  # Return the best move found
    def play(self):
        """
        Main game loop handling player input and game progression.
        
        This function drives the entire game process, from initializing the game 
        settings, handling player or AI moves, to displaying the board, checking 
        for game termination conditions, and saving the game trace to a file.
        It alternates between players and AIs, ensuring the game is played step 
        by step until completion or timeout.

        Parameters:
        - None
        
        Returns:
        - None
        """
        
        # Determine if white and black players are AI based on playmode settings
        white_is_ai = 'AI' in self.playmode.split('-')[0].upper()
        black_is_ai = 'AI' in self.playmode.split('-')[1].upper()

        # Log the game configuration and initial board setup
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
        self.log("\n".join(params), color="magenta")

        # Welcome message to users
        self.log("\nWelcome to Mini Chess! Enter moves as 'B2 B3'. Type 'exit' to quit.", color="green", bold=True)

        # Main game loop: continues until the game is over
        while not self.game_over:
            current_player = self.current_game_state['turn']  # Get current player's turn
            is_ai_turn = (current_player == 'white' and white_is_ai) or (current_player == 'black' and black_is_ai)

            if is_ai_turn:
                # If it's the AI's turn, make the move and evaluate
                move_start_time = time.time()  # Record start time of AI's move
                move = self.get_best_move(self.current_game_state, self.timeout)  # Get AI's best move
                move_time_taken = time.time() - move_start_time  # Calculate the time AI took

                # If no move is found or the AI exceeds the time limit, end the game
                if not move:
                    self.log(f"{current_player} AI exceeded timeout! Automatic loss.", color="red", bold=True)
                    self.game_over = True
                    self.result = f"{current_player} AI lost by timeout."
                    break

                # Log the AI's move and time taken
                move_str = f"{self.convert_to_notation(move[0])} {self.convert_to_notation(move[1])}"
                self.log(f"                    AI plays: {move_str}", color="green")
                self.log(f"               Time taken: {move_time_taken:.2f} seconds", color="cyan")

                # Update game state after AI move
                new_state = copy.deepcopy(self.current_game_state)
                self.make_move(new_state, move, is_ai_evaluation=True)
                heuristic_score = self.evaluate_state(new_state)
                self.log(f"        Heuristic Score of Resulting Board: {heuristic_score}", color="cyan")
            
            else:
                # If it's the player's turn, prompt for move input
                move_str = input(f"                   {current_player.capitalize()} to move: ").strip()
                self.output_buffer.append(f"                   {current_player.capitalize()} to move: {move_str}")

            # If the user types 'exit', end the game
            if move_str.lower() == 'exit':
                self.log("\nGame exited by user.", color="red", bold=True)
                break

            # Parse the input move and validate it
            move = self.parse_input(move_str)
            if not move or not self.is_valid_move(self.current_game_state, move):
                self.log("      * * * * * * Invalid move. Try again. * * * * * *", color="red", bold=True)
                continue  # If move is invalid, prompt again

            # Log details about the move being made
            start_notation = self.convert_to_notation(move[0])
            end_notation = self.convert_to_notation(move[1])
            turn_number = (self.move_count + 1) // 2  # Calculate the current turn number
            if turn_number < 10:
                self.log(f"\n     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n                |      Player: {current_player}      |\n                |      Turn #: {turn_number}          |\n                |      Action: {start_notation} to {end_notation}   |", color="magenta") 
            else:
                self.log(f"\n     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n                |      Player: {current_player}      |\n                |      Turn #: {turn_number}         |\n                |      Action: {start_notation} to {end_notation}   |", color="magenta")

            # Apply the move to the game state and increment the move count
            self.make_move(self.current_game_state, move)
            self.move_count += 1

            # Log the new board configuration after the move
            self.log("                  New board configuration:", color="cyan")
            self.log(self.display_board(self.current_game_state))
        
        # If the game is over, log the result
        if self.game_over:
            self.log(f"\n     ++++++++++++++++++++++++++++++++++++++++++++++++++++++\n     Game over! {self.result} \n     ++++++++++++++++++++++++++++++++++++++++++++++++++++++\n", color="green", bold=True)

        # Ensure the directory for game trace files exists
        trace_dir = os.path.dirname(self.filename)
        os.makedirs(trace_dir, exist_ok=True)  # Create directory if it doesn't exist

        # Write the game trace to a file, cleaning the output buffer first
        with open(self.filename, 'w') as f:
            cleaned_output = clean_text("".join(self.output_buffer))
            f.write(cleaned_output)
        print(f"Game trace written to file: {self.filename}")

        # Exit the game
        exit()
    def log(self, message, end='\n', color=None, bold=False):
        """Log a message with optional color and bold formatting."""
        colors = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "magenta": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "reset": "\033[0m",
        }
        bold_code = "\033[1m" if bold else ""
        color_code = colors.get(color, "")
        formatted_message = f"{bold_code}{color_code}{message}{colors['reset']}"
        self.output_buffer.append(formatted_message + end)
        print(formatted_message, end=end)

if __name__ == "__main__":
    print("MiniChess Tournament Runner")
    print("===========================")
    
    try:
        game = MiniChess(playmode='AI-AI', timeout=2)
        results = game.run_tournament()
        
        # Save results
        filename = f"tournament_results_{int(time.time())}.txt"
        with open(filename, 'w') as f:
            f.write("Heuristic | Wins | Losses | Draws\n")
            f.write("---------------------------------\n")
            for h in results:
                f.write(f"{h:<9} | {results[h]['wins']:^4} | {results[h]['losses']:^6} | {results[h]['draws']:^5}\n")
                
        print(f"\nResults saved to {filename}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        with open("chess_error.log", "w") as f:
            f.write(f"Error at {time.ctime()}:\n{str(e)}")