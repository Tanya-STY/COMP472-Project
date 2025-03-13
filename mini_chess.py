import math
import copy
import time
import argparse
import os
from collections import defaultdict

class MiniChess:
    """
        Initialize MiniChess game instance

        Args:
            - playmode: string | Play mode: H-H (for now, only Human vs. Human is supported)
            - maxturns: int | Maximum number of turns
    """
    def __init__(self, playmode='H-H', maxturns=100, timeout=5, alpha_beta=True, heuristic_white='e0', heuristic_black='e0'):
        
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
        self.heuristics = {'white': heuristic_white, 'black': heuristic_black}
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

    # def display_board(self, game_state):
    #     print("\n                  A     B    C    D    E")
    #     print("                +----+----+----+----+----+")
    #     for i, row in enumerate(game_state["board"], start=1):
    #         row_str = f"              {6 - i} | " + " | ".join(piece if piece != '.' else '  ' for piece in row) + " | " + f"{6 - i}"
    #         print(row_str)
    #         print("                +----+----+----+----+----+")
            
    #     print("                  A     B    C    D    E")
    #     print()

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
    def make_move(self, game_state, move):
        # start = move[0]
        # end = move[1]
        start, end = move
        start_row, start_col = start
        end_row, end_col = end
        piece = game_state["board"][start_row][start_col]
        game_state["board"][start_row][start_col] = '.'
        game_state["board"][end_row][end_col] = piece

        # check king capture
        opponent = 'b' if game_state["turn"] == 'white' else 'w'
        king_piece = any(cell == opponent + 'K' for row in game_state["board"] for cell in row)
        if not king_piece:
            self.game_over = True
            self.result = f"{game_state['turn'].capitalize()} wins by capturing the king in {self.turn_count + 1} turns."
        
        # pawn promotion
        if piece[1] == 'p':
            if (piece[0] == 'w' and end_row == 0) or (piece[0] == 'b' and end_row == 4):
                game_state["board"][end_row][end_col] = piece[0] + 'Q'
        
        # toggle turn and check for full turn completion
        game_state["turn"] = 'black' if game_state["turn"] == 'white' else 'white'
        if game_state["turn"] == 'white':  # Black just moved
            self.turn_count += 1
            current_count = self.count_pieces(game_state["board"])
            self.piece_count_history.append(current_count)
            # Check max turns
            if self.turn_count >= self.maxturns:
                self.game_over = True
                self.result = "Draw by reaching max turns"
            # Check 10-turn draw
            if len(self.piece_count_history) >= 10:
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

    # def convert_to_notation(self, pos):
    #     row, col = pos
    #     return f"{chr(col + ord('A')) + str(5 - row)}"

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

    # def get_next_filename(self):
    #     # Save in the same folder as this script
    #     base_dir = os.path.dirname(os.path.abspath(__file__))
    #     base_name = os.path.join(base_dir, "gameTrace-HH")
    #     index = 1
    #     while True:
    #         filename = f"{base_name}-{index}.txt"
    #         if not os.path.exists(filename):
    #             print(f"\nCreating file...")
    #             return filename
    #         index += 1

    def get_next_filename(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        base_name = os.path.join(base_dir, "gameTrace")
        index = 1
        while True:
            filename = f"{base_name}-{index}.txt"
            if not os.path.exists(filename):
                self.log(f"Creating game trace file: {filename}")
                return filename
            index += 1


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
            f"Playmode: {self.playmode}",
            f"Max turns: {self.maxturns}",
            f"Timeout: {self.timeout}",
            f"Alpha-beta: {self.alpha_beta}",
            f"Heuristic (White): {self.heuristics['white']}",
            f"Heuristic (Black): {self.heuristics['black']}",
            "\nInitial Board Configuration:",
            self.display_board(self.current_game_state) 
        ]
        self.log("\n".join(params))

        self.log("\nWelcome to Mini Chess! Enter moves as 'B2 B3'. Type 'exit' to quit.")
        while not self.game_over:
            current_player = self.current_game_state['turn']
            is_ai_turn = (current_player == 'white' and white_is_ai) or (current_player == 'black' and black_is_ai)

            # self.log(self.display_board(self.current_game_state))

            if is_ai_turn:
                move = ((0, 0), (0, 0))
                move_str = "A1 A1"
                self.log(f"AI plays: {move_str}")
            
            # else:
            #     move_str = input(f"                   {current_player.capitalize()} to move: ").strip()
            
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
            self.log(f"\n-------------------------------------------------\n                  | Player: {current_player}    |\n                  | Turn #: {turn_number}        |\n                  | Action: {start_notation} to {end_notation} |\n") 

            self.make_move(self.current_game_state, move)
            self.move_count += 1

            self.log("New board configuration:")
            self.log(self.display_board(self.current_game_state))
        
        if self.game_over:
            self.log(f"\nGame over! {self.result}")
        
        
        with open(self.filename, 'w') as f:
            f.write("\n".join(self.output_buffer))
        print(f"Game trace written to file: {self.filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mini Chess Game')
    parser.add_argument('--playmode', type=str, default='H-H', help='H-H, H-AI, AI-H, AI-AI')
    parser.add_argument('--maxturns', type=int, default=100, help='Maximum number of turns')
    parser.add_argument('--timeout', type=int, default=5, help='AI move timeout in seconds')
    parser.add_argument('--alpha_beta', type=bool, default=True, help='Use alpha-beta pruning')
    parser.add_argument('--heuristic_white', type=str, default='e0', help='Heuristic for white player')
    parser.add_argument('--heuristic_black', type=str, default='e0', help='Heuristic for black player')
    args = parser.parse_args()

    game = MiniChess(
        playmode=args.playmode,
        maxturns=args.maxturns,
        timeout=args.timeout,
        alpha_beta=args.alpha_beta,
        heuristic_white=args.heuristic_white,
        heuristic_black=args.heuristic_black
    )
    game.play()