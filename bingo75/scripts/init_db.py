import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.models.database import Database
from src.models.user import User

def init_database():
    """Initialize the database and create default admin user."""
    # Set up logging
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "init_db.log"),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting database initialization")
    
    try:
        # Initialize database
        db = Database()
        with db:
            # Create tables
            db.create_tables()
            logger.info("Database tables created successfully")
            
            # Create system settings table
            db.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default settings
            default_settings = {
                'max_login_attempts': '3',
                'lockout_time': '15',
                'require_admin_2fa': '0',
                'auto_verify': '0',
                'sound_effects': '1'
            }
            
            for key, value in default_settings.items():
                db.execute(
                    """
                    INSERT OR REPLACE INTO system_settings (key, value)
                    VALUES (?, ?)
                    """,
                    (key, value)
                )
            
            logger.info("System settings initialized")
            
            # Create default admin user if none exists
            result = db.execute(
                "SELECT COUNT(*) FROM users WHERE is_admin = 1"
            ).fetchone()
            
            if result[0] == 0:
                user_model = User(db)
                success, message = user_model.create_user(
                    username="admin",
                    password="admin123",  # Should be changed on first login
                    is_admin=True
                )
                
                if success:
                    logger.info("Default admin user created")
                else:
                    logger.error(f"Failed to create admin user: {message}")
            
            db.commit()
            logger.info("Database initialization completed successfully")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    init_database()
