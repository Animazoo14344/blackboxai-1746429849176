import bcrypt
import pyotp
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from .database import Database

class User:
    """User model for authentication and management."""
    
    MAX_LOGIN_ATTEMPTS = 3
    LOCKOUT_DURATION = timedelta(minutes=15)
    
    def __init__(self, db: Database):
        """Initialize user model.
        
        Args:
            db (Database): Database connection manager
        """
        self.db = db
        
    def create_user(self, username: str, password: str, is_admin: bool = False,
                   enable_2fa: bool = False) -> Tuple[bool, str]:
        """Create a new user.
        
        Args:
            username (str): Username
            password (str): Plain text password
            is_admin (bool): Whether user has admin privileges
            enable_2fa (bool): Whether to enable 2FA
            
        Returns:
            tuple: (success (bool), message (str))
        """
        try:
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Generate TOTP secret if 2FA is enabled
            totp_secret = pyotp.random_base32() if enable_2fa else None
            
            query = """
                INSERT INTO users (username, password_hash, is_admin, totp_secret)
                VALUES (?, ?, ?, ?)
            """
            self.db.execute(query, (username, password_hash, is_admin, totp_secret))
            self.db.commit()
            
            return True, "User created successfully"
        except Exception as e:
            self.db.rollback()
            logging.error(f"User creation error: {e}")
            return False, str(e)
    
    def verify_password(self, username: str, password: str) -> bool:
        """Verify user password.
        
        Args:
            username (str): Username
            password (str): Plain text password
            
        Returns:
            bool: True if password matches
        """
        query = "SELECT password_hash FROM users WHERE username = ?"
        result = self.db.execute(query, (username,)).fetchone()
        
        if not result:
            return False
            
        stored_hash = result[0]
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
    
    def verify_2fa(self, username: str, token: str) -> bool:
        """Verify 2FA token.
        
        Args:
            username (str): Username
            token (str): 2FA token
            
        Returns:
            bool: True if token is valid
        """
        query = "SELECT totp_secret FROM users WHERE username = ?"
        result = self.db.execute(query, (username,)).fetchone()
        
        if not result or not result[0]:
            return False
            
        totp = pyotp.TOTP(result[0])
        return totp.verify(token)
    
    def check_login_attempts(self, username: str) -> Tuple[bool, str]:
        """Check if user is allowed to attempt login.
        
        Args:
            username (str): Username
            
        Returns:
            tuple: (allowed (bool), message (str))
        """
        query = """
            SELECT failed_attempts, last_failed_attempt
            FROM users WHERE username = ?
        """
        result = self.db.execute(query, (username,)).fetchone()
        
        if not result:
            return True, ""
            
        attempts, last_attempt = result
        
        if attempts >= self.MAX_LOGIN_ATTEMPTS:
            if last_attempt:
                last_attempt = datetime.fromisoformat(last_attempt)
                if datetime.now() - last_attempt < self.LOCKOUT_DURATION:
                    return False, "Account temporarily locked. Please try again later."
                else:
                    # Reset attempts after lockout period
                    self.reset_login_attempts(username)
                    
        return True, ""
    
    def record_failed_attempt(self, username: str):
        """Record a failed login attempt.
        
        Args:
            username (str): Username
        """
        query = """
            UPDATE users 
            SET failed_attempts = failed_attempts + 1,
                last_failed_attempt = CURRENT_TIMESTAMP
            WHERE username = ?
        """
        self.db.execute(query, (username,))
        self.db.commit()
    
    def reset_login_attempts(self, username: str):
        """Reset failed login attempts counter.
        
        Args:
            username (str): Username
        """
        query = """
            UPDATE users 
            SET failed_attempts = 0,
                last_failed_attempt = NULL
            WHERE username = ?
        """
        self.db.execute(query, (username,))
        self.db.commit()
    
    def get_user_info(self, username: str) -> Optional[dict]:
        """Get user information.
        
        Args:
            username (str): Username
            
        Returns:
            dict: User information or None if not found
        """
        query = """
            SELECT id, username, is_admin, totp_secret IS NOT NULL as has_2fa
            FROM users WHERE username = ?
        """
        result = self.db.execute(query, (username,)).fetchone()
        
        if not result:
            return None
            
        return {
            'id': result[0],
            'username': result[1],
            'is_admin': bool(result[2]),
            'has_2fa': bool(result[3])
        }
    
    def update_password(self, username: str, new_password: str) -> Tuple[bool, str]:
        """Update user password.
        
        Args:
            username (str): Username
            new_password (str): New plain text password
            
        Returns:
            tuple: (success (bool), message (str))
        """
        try:
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            query = """
                UPDATE users 
                SET password_hash = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE username = ?
            """
            self.db.execute(query, (password_hash, username))
            self.db.commit()
            
            return True, "Password updated successfully"
        except Exception as e:
            self.db.rollback()
            logging.error(f"Password update error: {e}")
            return False, str(e)
    
    def toggle_2fa(self, username: str, enable: bool) -> Tuple[bool, str, Optional[str]]:
        """Enable or disable 2FA for user.
        
        Args:
            username (str): Username
            enable (bool): Whether to enable or disable 2FA
            
        Returns:
            tuple: (success (bool), message (str), new_secret (str) if enabled)
        """
        try:
            if enable:
                secret = pyotp.random_base32()
                query = """
                    UPDATE users 
                    SET totp_secret = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE username = ?
                """
                self.db.execute(query, (secret, username))
            else:
                query = """
                    UPDATE users 
                    SET totp_secret = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE username = ?
                """
                self.db.execute(query, (username,))
                secret = None
            
            self.db.commit()
            status = "enabled" if enable else "disabled"
            return True, f"2FA {status} successfully", secret
        except Exception as e:
            self.db.rollback()
            logging.error(f"2FA toggle error: {e}")
            return False, str(e), None
