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
        self.stats = {"states_explored": 0, "depth_counts": defaultdict(int)}
        
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

        # Check if the move captures the opponent's king (only during actual gameplay, not AI evaluation)
        if not is_ai_evaluation and target_piece != '.':  # Target square is not empty
            if target_piece[1] == 'K':  # Target piece is a king
                opponent_color = 'b' if game_state["turn"] == 'white' else 'w'
                if target_piece[0] == opponent_color:  # Target piece is the opponent's king
                    self.log(f"Game over! {game_state['turn'].capitalize()} wins by capturing the king.")
                    self.game_over = True
                    self.result = f"{game_state['turn'].capitalize()} wins by capturing the king in {self.turn_count + 1} turns."
                    return game_state

        # Make the move
        game_state["board"][start_row][start_col] = '.'
        game_state["board"][end_row][end_col] = piece

        # Pawn promotion
        if piece[1] == 'p':
            if (piece[0] == 'w' and end_row == 0) or (piece[0] == 'b' and end_row == 4):
                game_state["board"][end_row][end_col] = piece[0] + 'Q'

        # Toggle turn
        game_state["turn"] = 'black' if game_state["turn"] == 'white' else 'white'

        # Increment turn count and update piece count history after Black's move (only during actual game progression)
        if not is_ai_evaluation and game_state["turn"] == 'white':  # Black just moved
            self.turn_count += 1
            current_count = self.count_pieces(game_state["board"])
            self.piece_count_history.append(current_count)

            # Debugging: Print turn count and piece count history
            self.log(f"Turn Count: {self.turn_count}, Piece Count History: {self.piece_count_history}")

            # Check max turns
            if self.turn_count >= self.maxturns:
                self.game_over = True
                self.result = "Draw by reaching max turns"
                return game_state

            # Check 10-turn draw (only after 10 full turns)
            if self.turn_count >= 10:
                last_ten = self.piece_count_history[-10:]
                if all(x == last_ten[0] for x in last_ten):
                    self.game_over = True
                    self.result = "Draw by 10 turns with no captures"
                    return game_state

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
    Write the board state to a file

    Args:
        - file: file object | File object to write to
        - game_state: dictionary | Dictionary representing the current game state
    Returns:
        - None
    """
    def write_board_to_file(self, file, game_state):
        file.write("\n                  A     B    C    D    E\n")
        file.write("                +----+----+----+----+----+\n")
        for i, row in enumerate(game_state["board"], start=1):
            row_str = f"              {6 - i} | " + " | ".join(piece if piece != '.' else '  ' for piece in row) + " | " + f"{6 - i}\n"
            file.write(row_str)
            file.write("                +----+----+----+----+----+\n")
        file.write("                  A     B    C    D    E\n")


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
            filename = f"{base_name}-{index}.txt"
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
        # Implement heuristic e1
        pass

    def evaluate_state_e2(self, state):
        # Implement heuristic e2
        pass

    def order_moves(self, state, moves):
        """Prioritize capturing moves."""
        def move_value(move):
            _, end_pos = move
            end_piece = state["board"][end_pos[0]][end_pos[1]]
            return 10 if end_piece != '.' else 0  
        return sorted(moves, key=move_value, reverse=True)

    # Minimax with Alpha-Beta pruning
    def minimax(self, state, depth, maximizing, alpha, beta, start_time, time_limit):
        if time.time() - start_time >= time_limit:
            return self.evaluate_state(state), alpha, beta
        
        if depth == 0 or self.game_over:
            return self.evaluate_state(state), alpha, beta

        moves = self.order_moves(state, self.valid_moves(state))
        
        if not moves:
            return self.evaluate_state(state), alpha, beta

        if maximizing:
            value = -math.inf
            for move in moves:
                new_state = copy.deepcopy(state)
                self.make_move(new_state, move, is_ai_evaluation=True)
                eval_score, new_alpha, new_beta = self.minimax(new_state, depth - 1, False, alpha, beta, start_time, time_limit)
                value = max(value, eval_score)
                
                # Alpha-Beta pruning
                if self.alpha_beta:
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break  # Beta cutoff
            return value, alpha, beta
        else:
            value = math.inf
            for move in moves:
                new_state = copy.deepcopy(state)
                self.make_move(new_state, move, is_ai_evaluation=True)
                eval_score, new_alpha, new_beta = self.minimax(new_state, depth - 1, True, alpha, beta, start_time, time_limit)
                value = min(value, eval_score)
                
                # Alpha-Beta pruning
                if self.alpha_beta:
                    beta = min(beta, value)
                    if beta <= alpha:
                        break  # Alpha cutoff
            return value, alpha, beta

    def get_best_move(self, state, max_depth, time_limit):
        start_time = time.time()
        best_move = None
        best_value = -math.inf if state["turn"] == "white" else math.inf

        moves = self.order_moves(state, self.valid_moves(state))

        for move in moves:
            if time.time() - start_time > time_limit:
                break
            new_state = copy.deepcopy(state)
            self.make_move(new_state, move, is_ai_evaluation=True)
            
            # Call minimax with alpha and beta for Alpha-Beta pruning
            value, alpha, beta = self.minimax(new_state, max_depth - 1, state["turn"] == "black", -math.inf, math.inf, start_time, time_limit)

            if state["turn"] == "white" and value > best_value:
                best_value = value
                best_move = move
            elif state["turn"] == "black" and value < best_value:
                best_value = value
                best_move = move

        # Log the final move chosen by the AI
        if best_move:
            time_taken = time.time() - start_time
            self.log(f"AI chooses: {self.convert_to_notation(best_move[0])} to {self.convert_to_notation(best_move[1])}")
            self.log(f"Time taken: {time_taken:.2f} seconds")
            self.log(f"Final Heuristic Score: {self.evaluate_state(state)}")
            
            # Log Alpha-Beta score if Alpha-Beta pruning is enabled
            if self.alpha_beta:
                self.log(f"Final Alpha-Beta Score: Alpha={alpha}, Beta={beta}")
            else:
                self.log(f"Final Minimax Score: {best_value}")

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

        ai_depth = 4

        while not self.game_over:
            current_player = self.current_game_state['turn']
            is_ai_turn = (current_player == 'white' and white_is_ai) or (current_player == 'black' and black_is_ai)

            if is_ai_turn:
                move_start_time = time.time()
                move = self.get_best_move(self.current_game_state, ai_depth, self.timeout)
                move_time_taken = time.time() - move_start_time

                if not move:
                    self.log("No valid moves found. Game over.")
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