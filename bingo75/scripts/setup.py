import os
import sys
import subprocess
import logging
from pathlib import Path

def setup_logging():
    """Configure logging for setup process."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "setup.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def check_python_version():
    """Check if Python version meets requirements."""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        raise RuntimeError(
            f"Python {required_version[0]}.{required_version[1]} or higher is required"
        )

def install_dependencies():
    """Install required Python packages."""
    requirements_file = Path(__file__).parent.parent / "requirements.txt"
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install dependencies: {e}")
        return False

def create_desktop_shortcut():
    """Create desktop shortcut for the application."""
    try:
        # Get home directory
        home = Path.home()
        desktop = home / "Desktop"
        
        # Get project root
        project_root = Path(__file__).parent.parent.absolute()
        
        if sys.platform == "win32":
            # Windows shortcut
            shortcut_path = desktop / "Bingo75.bat"
            with open(shortcut_path, "w") as f:
                f.write(f"""@echo off
cd /d "{project_root}"
"{sys.executable}" src/main.py
pause
""")
            
        elif sys.platform == "darwin":
            # macOS shortcut
            shortcut_path = desktop / "Bingo75.command"
            with open(shortcut_path, "w") as f:
                f.write(f"""#!/bin/bash
cd "{project_root}"
"{sys.executable}" src/main.py
""")
            # Make executable
            os.chmod(shortcut_path, 0o755)
            
        else:
            # Linux desktop entry
            shortcut_path = desktop / "Bingo75.desktop"
            with open(shortcut_path, "w") as f:
                f.write(f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Bingo75
Comment=Bingo Game Management System
Exec="{sys.executable}" "{project_root}/src/main.py"
Terminal=false
Categories=Game;
""")
            # Make executable
            os.chmod(shortcut_path, 0o755)
        
        return True
    except Exception as e:
        logging.error(f"Failed to create desktop shortcut: {e}")
        return False

def create_data_directories():
    """Create necessary data directories."""
    project_root = Path(__file__).parent.parent
    
    directories = [
        "data",    # Database and other data files
        "logs",    # Log files
        "backup"   # Backup files
    ]
    
    for directory in directories:
        (project_root / directory).mkdir(exist_ok=True)

def main():
    """Main setup function."""
    logger = setup_logging()
    logger.info("Starting Bingo75 setup")
    
    try:
        # Check Python version
        logger.info("Checking Python version...")
        check_python_version()
        logger.info("Python version check passed")
        
        # Create directories
        logger.info("Creating data directories...")
        create_data_directories()
        logger.info("Data directories created")
        
        # Install dependencies
        logger.info("Installing dependencies...")
        if not install_dependencies():
            logger.error("Failed to install dependencies")
            sys.exit(1)
        logger.info("Dependencies installed successfully")
        
        # Initialize database
        logger.info("Initializing database...")
        init_script = Path(__file__).parent / "init_db.py"
        result = subprocess.run(
            [sys.executable, str(init_script)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Database initialization failed: {result.stderr}")
            sys.exit(1)
        logger.info("Database initialized successfully")
        
        # Create desktop shortcut
        logger.info("Creating desktop shortcut...")
        if create_desktop_shortcut():
            logger.info("Desktop shortcut created")
        else:
            logger.warning("Failed to create desktop shortcut")
        
        logger.info("Setup completed successfully")
        
        print("""
Bingo75 has been set up successfully!

Default admin credentials:
Username: admin
Password: admin123

Please change these credentials after first login.

You can start the application by:
1. Running 'python src/main.py' from the project directory
2. Using the desktop shortcut (if created successfully)

For more information, please refer to the README.md file.
""")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
