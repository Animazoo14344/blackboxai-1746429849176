import json
import random
from typing import List, Optional, Tuple
import pandas as pd
from .database import Database

class Card:
    """Bingo card management system."""
    
    # Constants for card validation
    ROWS = 5
    COLS = 5
    FREE_SPACE = (2, 2)  # Center position (row, col)
    
    # Column ranges for numbers (B: 1-15, I: 16-30, etc.)
    COLUMN_RANGES = [
        (1, 15),    # B
        (16, 30),   # I
        (31, 45),   # N
        (46, 60),   # G
        (61, 75)    # O
    ]
    
    def __init__(self, db: Database):
        """Initialize card manager.
        
        Args:
            db (Database): Database connection manager
        """
        self.db = db
    
    def generate_card_numbers(self) -> List[List[Optional[int]]]:
        """Generate a valid set of numbers for a bingo card.
        
        Returns:
            List[List[Optional[int]]]: 5x5 grid of numbers with None at FREE space
        """
        card = [[None for _ in range(self.COLS)] for _ in range(self.ROWS)]
        
        # Generate numbers for each column
        for col in range(self.COLS):
            min_num, max_num = self.COLUMN_RANGES[col]
            numbers = random.sample(range(min_num, max_num + 1), self.ROWS)
            
            for row in range(self.ROWS):
                # Skip FREE space
                if (row, col) == self.FREE_SPACE:
                    continue
                card[row][col] = numbers[row]
        
        return card
    
    def validate_card_numbers(self, numbers: List[List[Optional[int]]]) -> bool:
        """Validate a set of card numbers.
        
        Args:
            numbers (List[List[Optional[int]]]): 5x5 grid of numbers
            
        Returns:
            bool: True if card numbers are valid
        """
        if len(numbers) != self.ROWS or any(len(row) != self.COLS for row in numbers):
            return False
            
        # Check FREE space
        if numbers[self.FREE_SPACE[0]][self.FREE_SPACE[1]] is not None:
            return False
            
        # Check each column
        for col in range(self.COLS):
            min_num, max_num = self.COLUMN_RANGES[col]
            col_numbers = [
                numbers[row][col] 
                for row in range(self.ROWS) 
                if (row, col) != self.FREE_SPACE
            ]
            
            # Check range and uniqueness
            if not all(min_num <= num <= max_num for num in col_numbers):
                return False
            if len(set(col_numbers)) != len(col_numbers):
                return False
        
        return True
    
    def create_card(self, serial_number: str, batch_number: str,
                   numbers: Optional[List[List[Optional[int]]]] = None) -> Tuple[bool, str]:
        """Create a new bingo card.
        
        Args:
            serial_number (str): Unique card identifier
            batch_number (str): Batch identifier
            numbers (List[List[Optional[int]]], optional): Card numbers.
                                                         If None, generates new numbers.
        
        Returns:
            tuple: (success (bool), message (str))
        """
        try:
            if numbers is None:
                numbers = self.generate_card_numbers()
            
            if not self.validate_card_numbers(numbers):
                return False, "Invalid card numbers"
            
            # Convert numbers to JSON string for storage
            numbers_json = json.dumps(numbers)
            
            query = """
                INSERT INTO cards (serial_number, batch_number, numbers)
                VALUES (?, ?, ?)
            """
            self.db.execute(query, (serial_number, batch_number, numbers_json))
            self.db.commit()
            
            return True, "Card created successfully"
        except Exception as e:
            self.db.rollback()
            return False, str(e)
    
    def import_cards_from_csv(self, file_path: str) -> Tuple[int, List[str]]:
        """Import cards from CSV file.
        
        Args:
            file_path (str): Path to CSV file
            
        Returns:
            tuple: (number of cards imported, list of error messages)
        """
        errors = []
        imported = 0
        
        try:
            df = pd.read_csv(file_path)
            required_columns = ['serial_number', 'batch_number']
            
            # Validate columns
            if not all(col in df.columns for col in required_columns):
                return 0, ["CSV file missing required columns"]
            
            # Process each row
            for _, row in df.iterrows():
                serial_number = str(row['serial_number'])
                batch_number = str(row['batch_number'])
                
                # Generate new card numbers
                success, message = self.create_card(serial_number, batch_number)
                
                if success:
                    imported += 1
                else:
                    errors.append(f"Error importing card {serial_number}: {message}")
            
            return imported, errors
        except Exception as e:
            return 0, [f"Import error: {str(e)}"]
    
    def update_card_status(self, serial_number: str, status: str) -> Tuple[bool, str]:
        """Update card status.
        
        Args:
            serial_number (str): Card serial number
            status (str): New status ('available', 'in_play', 'won')
            
        Returns:
            tuple: (success (bool), message (str))
        """
        valid_statuses = ['available', 'in_play', 'won']
        if status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        
        try:
            query = "UPDATE cards SET status = ? WHERE serial_number = ?"
            self.db.execute(query, (status, serial_number))
            self.db.commit()
            
            return True, f"Card status updated to {status}"
        except Exception as e:
            self.db.rollback()
            return False, str(e)
    
    def get_card(self, serial_number: str) -> Optional[dict]:
        """Get card information.
        
        Args:
            serial_number (str): Card serial number
            
        Returns:
            dict: Card information or None if not found
        """
        query = """
            SELECT serial_number, batch_number, numbers, status
            FROM cards WHERE serial_number = ?
        """
        result = self.db.execute(query, (serial_number,)).fetchone()
        
        if not result:
            return None
            
        return {
            'serial_number': result[0],
            'batch_number': result[1],
            'numbers': json.loads(result[2]),
            'status': result[3]
        }
    
    def search_cards(self, batch_number: Optional[str] = None,
                    status: Optional[str] = None) -> List[dict]:
        """Search cards based on criteria.
        
        Args:
            batch_number (str, optional): Filter by batch number
            status (str, optional): Filter by status
            
        Returns:
            List[dict]: List of matching cards
        """
        query = "SELECT serial_number, batch_number, numbers, status FROM cards WHERE 1=1"
        params = []
        
        if batch_number:
            query += " AND batch_number = ?"
            params.append(batch_number)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        results = self.db.execute(query, tuple(params)).fetchall()
        
        return [{
            'serial_number': row[0],
            'batch_number': row[1],
            'numbers': json.loads(row[2]),
            'status': row[3]
        } for row in results]
    
    def get_card_grid_string(self, numbers: List[List[Optional[int]]]) -> str:
        """Convert card numbers to formatted string representation.
        
        Args:
            numbers (List[List[Optional[int]]]): Card numbers
            
        Returns:
            str: Formatted string representation of card
        """
        result = "B  I  N  G  O\n"
        result += "-" * 15 + "\n"
        
        for row in range(self.ROWS):
            row_str = []
            for col in range(self.COLS):
                num = numbers[row][col]
                if num is None:
                    row_str.append("FR")
                else:
                    row_str.append(f"{num:2d}")
            result += " ".join(row_str) + "\n"
        
        return result
