# MiniChess Game
#### Tanya So Tin Yan (40208954) - Section NN

## Description
MiniChess is a simplified chess variant implemented in Python. It features a 5x5 board with a reduced set of pieces and rules. The game supports human vs. human gameplay and includes standard chess mechanics like piece movement, captures, pawn promotion, and king capture. Additionally, it implements draw conditions based on maximum turns or no captures in 10 consecutive turns.

The game logs all moves and board states to a trace file for review and analysis.

## Features
- **5x5 Chess Board**: Smaller board with simplified piece setup.
- **Piece Movement**: Supports King, Queen, Bishop, Knight, and Pawn movements.
- **Win Conditions**: King capture results in an immediate win.
- **Draw Conditions**:
  - Maximum turns reached (configurable).
  - No captures in 10 consecutive turns.
- **Logging**: Saves game trace to a file for review.
- **Human vs. Human**: Two-player gameplay with alternating turns.


## How to Run the Project

### Prerequisites
- Python 3.x installed on your system.

### Steps to Run
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Tanya-STY/COMP472-Project.git
   cd COMP472-Project
   ```

2. **Run the Game**:
   ```bash
   python mini_chess.py
   ```

3. **Command-Line Arguments**:
   - `--playmode`: Specify the play mode (default: `H-H` for human vs. human).
     - Supported modes: `H-H` (Human vs. Human).
     ```bash
     python mini_chess.py --playmode H-H 
     ```

4. **Gameplay**:
   - Enter moves in the format `A1 B2` (start and end positions).
   - Type `exit` to quit the game at any time.
   - The game will display the board and prompt players for their moves.

5. **Game Trace**:
   - The game saves a trace file named `gameTrace-HH-{n}.txt` in the same directory.
   - The file contains:
     - Initial board setup.
     - Move-by-move details (player, turn number, action).
     - Final board state and game result.

## Key Classes and Functions

### Classes
1. **`MiniChess`**:
   - Main class that handles game initialization, gameplay, and logging.
   - Manages game state, valid moves, and win/draw conditions.

### Key Methods
1. **`init_board`**:
   - Initializes the 5x5 board with starting piece positions.

2. **`display_board`**:
   - Prints the current board state to the console with coordinates.

3. **`valid_moves`**:
   - Generates all legal moves for the current player.

4. **`make_move`**:
   - Executes a move and updates the game state.
   - Handles pawn promotion, king capture, and draw conditions.

5. **`parse_input`**:
   - Converts user input (e.g., `A1 B2`) into board coordinates.

6. **`count_pieces`**:
   - Counts the number of pieces on the board for draw condition checks.

7. **`write_board_to_file`**:
   - Writes the current board state to the game trace file.

8. **`play`**:
   - Main game loop that handles player input and game progression.

## Example Gameplay
![image](https://github.com/user-attachments/assets/e63ca7b8-f7b5-49f5-a8fb-ffd6611ae8aa)

## Notes
- The game is designed for simplicity and does not include advanced chess rules.
- Only human vs. human mode is currently implemented.

---

Enjoy playing MiniChess! 🎉
