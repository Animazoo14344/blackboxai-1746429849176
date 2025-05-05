import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from models.database import Database
from views.main_window import MainWindow
from controllers.app_controller import AppController

def setup_logging():
    """Configure logging for the application."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "bingo75.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def init_database():
    """Initialize the database connection and create tables."""
    db = Database()
    with db:
        db.create_tables()
    return db

def main():
    """Main application entry point."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Bingo 75 application")
    
    try:
        # Initialize database
        db = init_database()
        logger.info("Database initialized successfully")
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Use Fusion style for consistent look across platforms
        
        # Set application-wide attributes
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
        
        # Create MVC components
        controller = AppController(db)
        main_window = MainWindow(controller)
        
        # Show main window
        main_window.show()
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Application shutdown complete")

if __name__ == '__main__':
    main()
