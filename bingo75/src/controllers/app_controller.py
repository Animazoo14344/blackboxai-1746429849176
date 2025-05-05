import logging
from typing import Optional, Tuple, List, Dict
from models.database import Database
from models.user import User
from models.card import Card
from models.pattern import Pattern
from models.game import Game

class AppController:
    """Main application controller coordinating models and views."""
    
    def __init__(self, db: Database):
        """Initialize application controller.
        
        Args:
            db (Database): Database connection manager
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Initialize models
        self.user_model = User(db)
        self.card_model = Card(db)
        self.pattern_model = Pattern(db)
        self.game_model = Game(db)
        
        # Current session state
        self.current_user = None
        self.current_game_id = None
        
    def login(self, username: str, password: str,
             totp_token: Optional[str] = None) -> Tuple[bool, str]:
        """Handle user login.
        
        Args:
            username (str): Username
            password (str): Password
            totp_token (str, optional): 2FA token if enabled
            
        Returns:
            tuple: (success (bool), message (str))
        """
        try:
            # Check login attempts
            allowed, message = self.user_model.check_login_attempts(username)
            if not allowed:
                return False, message
            
            # Verify password
            if not self.user_model.verify_password(username, password):
                self.user_model.record_failed_attempt(username)
                return False, "Invalid username or password"
            
            # Get user info
            user_info = self.user_model.get_user_info(username)
            if not user_info:
                return False, "User not found"
            
            # Check 2FA if enabled
            if user_info['has_2fa']:
                if not totp_token:
                    return False, "2FA token required"
                if not self.user_model.verify_2fa(username, totp_token):
                    return False, "Invalid 2FA token"
            
            # Reset failed attempts and set current user
            self.user_model.reset_login_attempts(username)
            self.current_user = user_info
            
            self.logger.info(f"User {username} logged in successfully")
            return True, "Login successful"
            
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False, "Login failed"
    
    def logout(self):
        """Handle user logout."""
        if self.current_user:
            self.logger.info(f"User {self.current_user['username']} logged out")
            self.current_user = None
    
    def is_admin(self) -> bool:
        """Check if current user is admin.
        
        Returns:
            bool: True if current user is admin
        """
        return bool(self.current_user and self.current_user['is_admin'])
    
    def create_game(self, pattern_id: int,
                   card_serials: List[str]) -> Tuple[bool, str]:
        """Create and set up a new game.
        
        Args:
            pattern_id (int): Pattern ID to use
            card_serials (List[str]): Cards to include in game
            
        Returns:
            tuple: (success (bool), message (str))
        """
        try:
            # Create game
            success, message, game_id = self.game_model.create_game(pattern_id)
            if not success:
                return False, message
            
            # Add cards
            success, message = self.game_model.add_cards_to_game(game_id, card_serials)
            if not success:
                return False, message
            
            self.current_game_id = game_id
            self.logger.info(f"Game {game_id} created successfully")
            return True, "Game created successfully"
            
        except Exception as e:
            self.logger.error(f"Game creation error: {e}")
            return False, "Failed to create game"
    
    def start_game(self) -> Tuple[bool, str]:
        """Start the current game.
        
        Returns:
            tuple: (success (bool), message (str))
        """
        if not self.current_game_id:
            return False, "No game selected"
            
        try:
            success, message = self.game_model.start_game(self.current_game_id)
            if success:
                self.logger.info(f"Game {self.current_game_id} started")
            return success, message
            
        except Exception as e:
            self.logger.error(f"Game start error: {e}")
            return False, "Failed to start game"
    
    def call_number(self, number: int) -> Tuple[bool, str]:
        """Call a number in the current game.
        
        Args:
            number (int): Number to call
            
        Returns:
            tuple: (success (bool), message (str))
        """
        if not self.current_game_id:
            return False, "No game in progress"
            
        try:
            success, message = self.game_model.call_number(self.current_game_id, number)
            if success:
                self.logger.info(f"Number {number} called in game {self.current_game_id}")
            return success, message
            
        except Exception as e:
            self.logger.error(f"Number call error: {e}")
            return False, "Failed to call number"
    
    def verify_winner(self, serial_number: str) -> Tuple[bool, str, bool]:
        """Verify if a card has won the current game.
        
        Args:
            serial_number (str): Card serial number
            
        Returns:
            tuple: (success (bool), message (str), is_winner (bool))
        """
        if not self.current_game_id:
            return False, "No game in progress", False
            
        try:
            return self.game_model.verify_winner(self.current_game_id, serial_number)
            
        except Exception as e:
            self.logger.error(f"Winner verification error: {e}")
            return False, "Failed to verify winner", False
    
    def end_game(self, winner_card: Optional[str] = None,
                cancelled: bool = False) -> Tuple[bool, str]:
        """End the current game.
        
        Args:
            winner_card (str, optional): Winning card serial number
            cancelled (bool): Whether game was cancelled
            
        Returns:
            tuple: (success (bool), message (str))
        """
        if not self.current_game_id:
            return False, "No game in progress"
            
        try:
            success, message = self.game_model.end_game(
                self.current_game_id, winner_card, cancelled
            )
            if success:
                self.logger.info(f"Game {self.current_game_id} ended")
                self.current_game_id = None
            return success, message
            
        except Exception as e:
            self.logger.error(f"Game end error: {e}")
            return False, "Failed to end game"
    
    def get_game_state(self) -> Optional[Dict]:
        """Get current game state.
        
        Returns:
            dict: Game state information or None if no game
        """
        if not self.current_game_id:
            return None
            
        try:
            game_info = self.game_model.get_game(self.current_game_id)
            if not game_info:
                return None
                
            # Add called numbers
            called_numbers = self.game_model.get_called_numbers(self.current_game_id)
            game_info['called_numbers'] = called_numbers
            
            # Add pattern information
            pattern = self.pattern_model.get_pattern(game_info['pattern_id'])
            if pattern:
                game_info['pattern'] = pattern
            
            return game_info
            
        except Exception as e:
            self.logger.error(f"Game state error: {e}")
            return None
    
    def import_cards(self, file_path: str) -> Tuple[int, List[str]]:
        """Import cards from file.
        
        Args:
            file_path (str): Path to import file
            
        Returns:
            tuple: (number of cards imported, list of error messages)
        """
        try:
            return self.card_model.import_cards_from_csv(file_path)
        except Exception as e:
            self.logger.error(f"Card import error: {e}")
            return 0, [str(e)]
    
    def create_pattern(self, name: str, category: str,
                      grid: List[List[bool]], is_moving: bool = False,
                      movement_rules: Optional[Dict] = None) -> Tuple[bool, str]:
        """Create a new pattern.
        
        Args:
            name (str): Pattern name
            category (str): Pattern category
            grid (List[List[bool]]): Pattern grid
            is_moving (bool): Whether pattern changes during game
            movement_rules (dict, optional): Rules for pattern movement
            
        Returns:
            tuple: (success (bool), message (str))
        """
        try:
            return self.pattern_model.create_pattern(
                name, category, grid, is_moving, movement_rules
            )
        except Exception as e:
            self.logger.error(f"Pattern creation error: {e}")
            return False, str(e)
