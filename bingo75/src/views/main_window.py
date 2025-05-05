from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget,
    QMessageBox, QLabel
)
from PyQt6.QtCore import Qt
from .login_view import LoginView
from .game_view import GameView
from .pattern_editor import PatternEditor
from .card_manager import CardManager
from .admin_panel import AdminPanel
from controllers.app_controller import AppController

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, controller: AppController):
        """Initialize main window.
        
        Args:
            controller (AppController): Application controller
        """
        super().__init__()
        self.controller = controller
        
        self.setWindowTitle("Bingo 75")
        self.setMinimumSize(1024, 768)
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Create header
        self.header = QLabel()
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                color: white;
                padding: 10px;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        self.layout.addWidget(self.header)
        
        # Create stacked widget for different views
        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)
        
        # Initialize views
        self.init_views()
        
        # Show login view initially
        self.show_login()
    
    def init_views(self):
        """Initialize all application views."""
        # Create views
        self.login_view = LoginView(self.controller)
        self.game_view = GameView(self.controller)
        self.pattern_editor = PatternEditor(self.controller)
        self.card_manager = CardManager(self.controller)
        self.admin_panel = AdminPanel(self.controller)
        
        # Add views to stacked widget
        self.stacked_widget.addWidget(self.login_view)
        self.stacked_widget.addWidget(self.game_view)
        self.stacked_widget.addWidget(self.pattern_editor)
        self.stacked_widget.addWidget(self.card_manager)
        self.stacked_widget.addWidget(self.admin_panel)
        
        # Connect signals
        self.login_view.login_successful.connect(self.on_login_success)
        self.game_view.logout_requested.connect(self.show_login)
        self.pattern_editor.back_requested.connect(self.show_game)
        self.card_manager.back_requested.connect(self.show_game)
        self.admin_panel.back_requested.connect(self.show_game)
    
    def show_login(self):
        """Switch to login view."""
        self.header.setText("Bingo 75 - Login")
        self.stacked_widget.setCurrentWidget(self.login_view)
        self.controller.logout()
    
    def show_game(self):
        """Switch to game view."""
        self.header.setText("Bingo 75 - Game")
        self.stacked_widget.setCurrentWidget(self.game_view)
    
    def show_pattern_editor(self):
        """Switch to pattern editor view."""
        self.header.setText("Bingo 75 - Pattern Editor")
        self.stacked_widget.setCurrentWidget(self.pattern_editor)
    
    def show_card_manager(self):
        """Switch to card manager view."""
        self.header.setText("Bingo 75 - Card Manager")
        self.stacked_widget.setCurrentWidget(self.card_manager)
    
    def show_admin_panel(self):
        """Switch to admin panel view."""
        self.header.setText("Bingo 75 - Admin Panel")
        self.stacked_widget.setCurrentWidget(self.admin_panel)
    
    def on_login_success(self):
        """Handle successful login."""
        self.show_game()
        
        # Update game view with user permissions
        self.game_view.update_permissions(self.controller.is_admin())
        
        # Show welcome message
        username = self.controller.current_user['username']
        QMessageBox.information(
            self,
            "Welcome",
            f"Welcome, {username}!",
            QMessageBox.StandardButton.Ok
        )
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Perform cleanup
        self.controller.logout()
        event.accept()
