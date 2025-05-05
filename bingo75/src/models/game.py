import json
from datetime import datetime
from typing import List, Optional, Tuple, Set
from .database import Database
from .pattern import Pattern
from .card import Card

class Game:
    """Bingo game management system."""
    
    def __init__(self, db: Database):
        """Initialize game manager.
        
        Args:
            db (Database): Database connection manager
        """
        self.db = db
        self.pattern_manager = Pattern(db)
        self.card_manager = Card(db)
    
    def create_game(self, pattern_id: int) -> Tuple[bool, str, Optional[int]]:
        """Create a new game.
        
        Args:
            pattern_id (int): Pattern ID to use for the game
            
        Returns:
            tuple: (success (bool), message (str), game_id (int))
        """
        try:
            # Verify pattern exists
            pattern = self.pattern_manager.get_pattern(pattern_id)
            if not pattern:
                return False, "Pattern not found", None
            
            query = """
                INSERT INTO games (pattern_id, status)
                VALUES (?, 'pending')
            """
            cursor = self.db.execute(query, (pattern_id,))
            game_id = cursor.lastrowid
            self.db.commit()
            
            return True, "Game created successfully", game_id
        except Exception as e:
            self.db.rollback()
            return False, str(e), None
    
    def add_cards_to_game(self, game_id: int,
                         serial_numbers: List[str]) -> Tuple[bool, str]:
        """Add cards to a game.
        
        Args:
            game_id (int): Game ID
            serial_numbers (List[str]): List of card serial numbers
            
        Returns:
            tuple: (success (bool), message (str))
        """
        try:
            # Verify game exists and is pending
            game = self.get_game(game_id)
            if not game:
                return False, "Game not found"
            if game['status'] != 'pending':
                return False, "Can only add cards to pending games"
            
            # Add cards and update their status
            for serial in serial_numbers:
                # Verify card exists and is available
                card = self.card_manager.get_card(serial)
                if not card:
                    return False, f"Card {serial} not found"
                if card['status'] != 'available':
                    return False, f"Card {serial} is not available"
                
                # Add card to game
                query = "INSERT INTO game_cards (game_id, card_id) VALUES (?, ?)"
                self.db.execute(query, (game_id, serial))
                
                # Update card status
                self.card_manager.update_card_status(serial, 'in_play')
            
            self.db.commit()
            return True, "Cards added successfully"
        except Exception as e:
            self.db.rollback()
            return False, str(e)
    
    def start_game(self, game_id: int) -> Tuple[bool, str]:
        """Start a game.
        
        Args:
            game_id (int): Game ID
            
        Returns:
            tuple: (success (bool), message (str))
        """
        try:
            # Verify game exists and is pending
            game = self.get_game(game_id)
            if not game:
                return False, "Game not found"
            if game['status'] != 'pending':
                return False, "Game is not in pending status"
            
            # Update game status
            query = """
                UPDATE games 
                SET status = 'in_progress',
                    start_time = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            self.db.execute(query, (game_id,))
            self.db.commit()
            
            return True, "Game started successfully"
        except Exception as e:
            self.db.rollback()
            return False, str(e)
    
    def call_number(self, game_id: int, number: int) -> Tuple[bool, str]:
        """Call a number in the game.
        
        Args:
            game_id (int): Game ID
            number (int): Called number (1-75)
            
        Returns:
            tuple: (success (bool), message (str))
        """
        if not 1 <= number <= 75:
            return False, "Invalid number (must be 1-75)"
            
        try:
            # Verify game is in progress
            game = self.get_game(game_id)
            if not game:
                return False, "Game not found"
            if game['status'] != 'in_progress':
                return False, "Game is not in progress"
            
            # Check if number was already called
            query = "SELECT COUNT(*) FROM ball_calls WHERE game_id = ? AND number = ?"
            count = self.db.execute(query, (game_id, number)).fetchone()[0]
            if count > 0:
                return False, "Number already called"
            
            # Get next call order
            query = """
                SELECT COALESCE(MAX(call_order), 0) + 1
                FROM ball_calls WHERE game_id = ?
            """
            next_order = self.db.execute(query, (game_id,)).fetchone()[0]
            
            # Record the call
            query = """
                INSERT INTO ball_calls (game_id, number, call_order)
                VALUES (?, ?, ?)
            """
            self.db.execute(query, (game_id, number, next_order))
            self.db.commit()
            
            return True, "Number called successfully"
        except Exception as e:
            self.db.rollback()
            return False, str(e)
    
    def verify_winner(self, game_id: int,
                     serial_number: str) -> Tuple[bool, str, bool]:
        """Verify if a card has won the game.
        
        Args:
            game_id (int): Game ID
            serial_number (str): Card serial number
            
        Returns:
            tuple: (success (bool), message (str), is_winner (bool))
        """
        try:
            # Verify game is in progress
            game = self.get_game(game_id)
            if not game:
                return False, "Game not found", False
            if game['status'] != 'in_progress':
                return False, "Game is not in progress", False
            
            # Verify card is in the game
            query = """
                SELECT COUNT(*) FROM game_cards
                WHERE game_id = ? AND card_id = ?
            """
            count = self.db.execute(query, (game_id, serial_number)).fetchone()[0]
            if count == 0:
                return False, "Card is not in this game", False
            
            # Get called numbers
            query = "SELECT number FROM ball_calls WHERE game_id = ? ORDER BY call_order"
            called_numbers = {row[0] for row in self.db.execute(query, (game_id,))}
            
            # Get card numbers and pattern
            card = self.card_manager.get_card(serial_number)
            pattern = self.pattern_manager.get_pattern(game['pattern_id'])
            
            if not card or not pattern:
                return False, "Failed to get card or pattern data", False
            
            # Check if pattern is satisfied
            is_winner = self._check_pattern_match(
                card['numbers'],
                pattern['grid'],
                called_numbers,
                pattern['is_moving'],
                pattern['movement_rules'],
                len(called_numbers)
            )
            
            return True, "Verification completed", is_winner
        except Exception as e:
            return False, str(e), False
    
    def _check_pattern_match(self, card_numbers: List[List[Optional[int]]],
                           pattern_grid: List[List[bool]], called_numbers: Set[int],
                           is_moving: bool, movement_rules: Optional[dict],
                           call_count: int) -> bool:
        """Check if card matches pattern with called numbers.
        
        Args:
            card_numbers (List[List[Optional[int]]]): Card numbers
            pattern_grid (List[List[bool]]): Pattern grid
            called_numbers (Set[int]): Called numbers
            is_moving (bool): Whether pattern is moving
            movement_rules (dict): Movement rules
            call_count (int): Number of calls made
            
        Returns:
            bool: True if card matches pattern
        """
        if is_moving and movement_rules:
            # Get current pattern state based on movement rules
            pattern_grid = self.pattern_manager.apply_movement_rule(
                pattern_grid, movement_rules, call_count
            )
        
        # Check each cell in the pattern
        for row in range(5):
            for col in range(5):
                if pattern_grid[row][col]:
                    number = card_numbers[row][col]
                    # FREE space always matches
                    if number is None:
                        continue
                    # Number must be called
                    if number not in called_numbers:
                        return False
        
        return True
    
    def end_game(self, game_id: int, winner_card: Optional[str] = None,
                 cancelled: bool = False) -> Tuple[bool, str]:
        """End a game.
        
        Args:
            game_id (int): Game ID
            winner_card (str, optional): Winning card serial number
            cancelled (bool): Whether game was cancelled
            
        Returns:
            tuple: (success (bool), message (str))
        """
        try:
            # Verify game is in progress
            game = self.get_game(game_id)
            if not game:
                return False, "Game not found"
            if game['status'] != 'in_progress':
                return False, "Game is not in progress"
            
            # Update game status
            status = 'cancelled' if cancelled else 'completed'
            query = """
                UPDATE games 
                SET status = ?,
                    end_time = CURRENT_TIMESTAMP,
                    winner_card_id = ?
                WHERE id = ?
            """
            self.db.execute(query, (status, winner_card, game_id))
            
            # Update card statuses
            query = """
                SELECT card_id FROM game_cards WHERE game_id = ?
            """
            for row in self.db.execute(query, (game_id,)):
                card_id = row[0]
                new_status = 'won' if card_id == winner_card else 'available'
                self.card_manager.update_card_status(card_id, new_status)
            
            self.db.commit()
            return True, f"Game {status} successfully"
        except Exception as e:
            self.db.rollback()
            return False, str(e)
    
    def get_game(self, game_id: int) -> Optional[dict]:
        """Get game information.
        
        Args:
            game_id (int): Game ID
            
        Returns:
            dict: Game information or None if not found
        """
        query = """
            SELECT id, pattern_id, status, start_time, end_time, winner_card_id
            FROM games WHERE id = ?
        """
        result = self.db.execute(query, (game_id,)).fetchone()
        
        if not result:
            return None
            
        return {
            'id': result[0],
            'pattern_id': result[1],
            'status': result[2],
            'start_time': result[3],
            'end_time': result[4],
            'winner_card_id': result[5]
        }
    
    def get_called_numbers(self, game_id: int) -> List[Tuple[int, int]]:
        """Get list of called numbers for a game.
        
        Args:
            game_id (int): Game ID
            
        Returns:
            List[Tuple[int, int]]: List of (number, call_order) tuples
        """
        query = """
            SELECT number, call_order
            FROM ball_calls
            WHERE game_id = ?
            ORDER BY call_order
        """
        return [(row[0], row[1]) 
                for row in self.db.execute(query, (game_id,))]
    
    def get_game_cards(self, game_id: int) -> List[str]:
        """Get list of cards in a game.
        
        Args:
            game_id (int): Game ID
            
        Returns:
            List[str]: List of card serial numbers
        """
        query = "SELECT card_id FROM game_cards WHERE game_id = ?"
        return [row[0] for row in self.db.execute(query, (game_id,))]
