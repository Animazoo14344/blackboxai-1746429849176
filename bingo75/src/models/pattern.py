import json
from typing import List, Optional, Tuple, Dict
from .database import Database

class Pattern:
    """Bingo pattern management system."""
    
    GRID_SIZE = 5
    
    def __init__(self, db: Database):
        """Initialize pattern manager.
        
        Args:
            db (Database): Database connection manager
        """
        self.db = db
    
    def create_pattern(self, name: str, category: str, grid: List[List[bool]],
                      is_moving: bool = False,
                      movement_rules: Optional[Dict] = None) -> Tuple[bool, str]:
        """Create a new bingo pattern.
        
        Args:
            name (str): Pattern name
            category (str): Pattern category
            grid (List[List[bool]]): 5x5 grid of boolean values
            is_moving (bool): Whether pattern changes during game
            movement_rules (dict, optional): Rules for pattern movement
            
        Returns:
            tuple: (success (bool), message (str))
        """
        if not self.validate_grid(grid):
            return False, "Invalid grid format"
            
        try:
            grid_json = json.dumps(grid)
            rules_json = json.dumps(movement_rules) if movement_rules else None
            
            query = """
                INSERT INTO patterns (name, category, grid, is_moving, movement_rules)
                VALUES (?, ?, ?, ?, ?)
            """
            self.db.execute(query, (name, category, grid_json, is_moving, rules_json))
            self.db.commit()
            
            return True, "Pattern created successfully"
        except Exception as e:
            self.db.rollback()
            return False, str(e)
    
    def validate_grid(self, grid: List[List[bool]]) -> bool:
        """Validate pattern grid format.
        
        Args:
            grid (List[List[bool]]): Pattern grid
            
        Returns:
            bool: True if grid is valid
        """
        if len(grid) != self.GRID_SIZE:
            return False
            
        return all(
            len(row) == self.GRID_SIZE and all(isinstance(cell, bool) for cell in row)
            for row in grid
        )
    
    def get_pattern(self, pattern_id: int) -> Optional[dict]:
        """Get pattern information.
        
        Args:
            pattern_id (int): Pattern ID
            
        Returns:
            dict: Pattern information or None if not found
        """
        query = """
            SELECT id, name, category, grid, is_moving, movement_rules
            FROM patterns WHERE id = ?
        """
        result = self.db.execute(query, (pattern_id,)).fetchone()
        
        if not result:
            return None
            
        return {
            'id': result[0],
            'name': result[1],
            'category': result[2],
            'grid': json.loads(result[3]),
            'is_moving': bool(result[4]),
            'movement_rules': json.loads(result[5]) if result[5] else None
        }
    
    def update_pattern(self, pattern_id: int, name: Optional[str] = None,
                      category: Optional[str] = None,
                      grid: Optional[List[List[bool]]] = None,
                      is_moving: Optional[bool] = None,
                      movement_rules: Optional[Dict] = None) -> Tuple[bool, str]:
        """Update pattern information.
        
        Args:
            pattern_id (int): Pattern ID
            name (str, optional): New pattern name
            category (str, optional): New pattern category
            grid (List[List[bool]], optional): New pattern grid
            is_moving (bool, optional): New moving status
            movement_rules (dict, optional): New movement rules
            
        Returns:
            tuple: (success (bool), message (str))
        """
        try:
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            
            if category is not None:
                updates.append("category = ?")
                params.append(category)
            
            if grid is not None:
                if not self.validate_grid(grid):
                    return False, "Invalid grid format"
                updates.append("grid = ?")
                params.append(json.dumps(grid))
            
            if is_moving is not None:
                updates.append("is_moving = ?")
                params.append(is_moving)
            
            if movement_rules is not None:
                updates.append("movement_rules = ?")
                params.append(json.dumps(movement_rules))
            
            if not updates:
                return False, "No updates provided"
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            query = f"""
                UPDATE patterns 
                SET {', '.join(updates)}
                WHERE id = ?
            """
            params.append(pattern_id)
            
            self.db.execute(query, tuple(params))
            self.db.commit()
            
            return True, "Pattern updated successfully"
        except Exception as e:
            self.db.rollback()
            return False, str(e)
    
    def delete_pattern(self, pattern_id: int) -> Tuple[bool, str]:
        """Delete a pattern.
        
        Args:
            pattern_id (int): Pattern ID
            
        Returns:
            tuple: (success (bool), message (str))
        """
        try:
            # Check if pattern is used in any games
            query = "SELECT COUNT(*) FROM games WHERE pattern_id = ?"
            count = self.db.execute(query, (pattern_id,)).fetchone()[0]
            
            if count > 0:
                return False, "Pattern is used in games and cannot be deleted"
            
            query = "DELETE FROM patterns WHERE id = ?"
            self.db.execute(query, (pattern_id,))
            self.db.commit()
            
            return True, "Pattern deleted successfully"
        except Exception as e:
            self.db.rollback()
            return False, str(e)
    
    def search_patterns(self, category: Optional[str] = None,
                       is_moving: Optional[bool] = None) -> List[dict]:
        """Search patterns based on criteria.
        
        Args:
            category (str, optional): Filter by category
            is_moving (bool, optional): Filter by moving status
            
        Returns:
            List[dict]: List of matching patterns
        """
        query = """
            SELECT id, name, category, grid, is_moving, movement_rules
            FROM patterns WHERE 1=1
        """
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if is_moving is not None:
            query += " AND is_moving = ?"
            params.append(is_moving)
        
        results = self.db.execute(query, tuple(params)).fetchall()
        
        return [{
            'id': row[0],
            'name': row[1],
            'category': row[2],
            'grid': json.loads(row[3]),
            'is_moving': bool(row[4]),
            'movement_rules': json.loads(row[5]) if row[5] else None
        } for row in results]
    
    def apply_movement_rule(self, grid: List[List[bool]], rules: Dict,
                          call_count: int) -> List[List[bool]]:
        """Apply movement rules to pattern grid.
        
        Args:
            grid (List[List[bool]]): Current pattern grid
            rules (dict): Movement rules
            call_count (int): Number of balls called
            
        Returns:
            List[List[bool]]: Updated grid after applying movement rules
        """
        # Example movement rule format:
        # {
        #     "type": "shift",
        #     "direction": "right",
        #     "trigger": {
        #         "type": "call_count",
        #         "value": 5
        #     }
        # }
        
        if not rules or 'type' not in rules:
            return grid
            
        # Check if movement should be triggered
        trigger = rules.get('trigger', {})
        trigger_type = trigger.get('type')
        trigger_value = trigger.get('value')
        
        if trigger_type == 'call_count' and call_count < trigger_value:
            return grid
            
        # Apply movement based on rule type
        rule_type = rules['type']
        new_grid = [row[:] for row in grid]  # Create a copy
        
        if rule_type == 'shift':
            direction = rules.get('direction', 'right')
            
            if direction == 'right':
                for row in range(self.GRID_SIZE):
                    new_grid[row] = new_grid[row][-1:] + new_grid[row][:-1]
            elif direction == 'left':
                for row in range(self.GRID_SIZE):
                    new_grid[row] = new_grid[row][1:] + new_grid[row][:1]
            elif direction == 'up':
                new_grid = new_grid[1:] + [new_grid[0]]
            elif direction == 'down':
                new_grid = [new_grid[-1]] + new_grid[:-1]
        
        elif rule_type == 'rotate':
            # Rotate 90 degrees clockwise
            new_grid = [[grid[self.GRID_SIZE-1-j][i] 
                        for j in range(self.GRID_SIZE)]
                       for i in range(self.GRID_SIZE)]
        
        return new_grid
    
    def get_pattern_display(self, grid: List[List[bool]]) -> str:
        """Convert pattern grid to string representation.
        
        Args:
            grid (List[List[bool]]): Pattern grid
            
        Returns:
            str: String representation of pattern
        """
        result = ""
        for row in grid:
            result += " ".join("X" if cell else "." for cell in row) + "\n"
        return result
