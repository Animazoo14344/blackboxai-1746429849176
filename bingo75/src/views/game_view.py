from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame, QSpacerItem,
    QSizePolicy, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from controllers.app_controller import AppController

class BallDisplay(QFrame):
    """Widget for displaying called balls."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Set up the ball display UI."""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #2c3e50;
                border-radius: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Header with column labels (B-I-N-G-O)
        header_layout = QHBoxLayout()
        labels = ['B', 'I', 'N', 'G', 'O']
        for label in labels:
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("""
                QLabel {
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 5px;
                }
            """)
            header_layout.addWidget(lbl)
        layout.addLayout(header_layout)
        
        # Grid for ball numbers
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(5)
        
        # Create ball labels (1-75)
        self.ball_labels = {}
        for i in range(75):
            number = i + 1
            label = QLabel(str(number))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("""
                QLabel {
                    background-color: #ecf0f1;
                    border: 1px solid #bdc3c7;
                    border-radius: 15px;
                    padding: 5px;
                    font-size: 16px;
                    min-width: 30px;
                    min-height: 30px;
                }
            """)
            
            # Calculate grid position
            col = (number - 1) // 15
            row = (number - 1) % 15
            self.grid_layout.addWidget(label, row, col)
            self.ball_labels[number] = label
            
        layout.addLayout(self.grid_layout)
    
    def highlight_ball(self, number: int):
        """Highlight a called ball.
        
        Args:
            number (int): Ball number to highlight
        """
        if number in self.ball_labels:
            self.ball_labels[number].setStyleSheet("""
                QLabel {
                    background-color: #3498db;
                    color: white;
                    border: 1px solid #2980b9;
                    border-radius: 15px;
                    padding: 5px;
                    font-size: 16px;
                    font-weight: bold;
                    min-width: 30px;
                    min-height: 30px;
                }
            """)
    
    def reset_display(self):
        """Reset all balls to uncalled state."""
        for label in self.ball_labels.values():
            label.setStyleSheet("""
                QLabel {
                    background-color: #ecf0f1;
                    border: 1px solid #bdc3c7;
                    border-radius: 15px;
                    padding: 5px;
                    font-size: 16px;
                    min-width: 30px;
                    min-height: 30px;
                }
            """)

class PatternDisplay(QFrame):
    """Widget for displaying current bingo pattern."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Set up the pattern display UI."""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #2c3e50;
                border-radius: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Pattern title
        self.title_label = QLabel("Current Pattern")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Grid for pattern display
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(2)
        
        # Create pattern cells
        self.cells = []
        for row in range(5):
            row_cells = []
            for col in range(5):
                cell = QLabel()
                cell.setFixedSize(30, 30)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setStyleSheet("""
                    QLabel {
                        background-color: #ecf0f1;
                        border: 1px solid #bdc3c7;
                    }
                """)
                self.grid_layout.addWidget(cell, row, col)
                row_cells.append(cell)
            self.cells.append(row_cells)
        
        layout.addLayout(self.grid_layout)
        
        # Pattern name
        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #2c3e50;
                padding: 5px;
            }
        """)
        layout.addWidget(self.name_label)
    
    def update_pattern(self, pattern_grid: list, pattern_name: str):
        """Update the pattern display.
        
        Args:
            pattern_grid (list): 5x5 grid of boolean values
            pattern_name (str): Pattern name
        """
        for row in range(5):
            for col in range(5):
                cell = self.cells[row][col]
                if pattern_grid[row][col]:
                    cell.setStyleSheet("""
                        QLabel {
                            background-color: #3498db;
                            border: 1px solid #2980b9;
                        }
                    """)
                else:
                    cell.setStyleSheet("""
                        QLabel {
                            background-color: #ecf0f1;
                            border: 1px solid #bdc3c7;
                        }
                    """)
        
        self.name_label.setText(pattern_name)

class GameView(QWidget):
    """Main game interface view."""
    
    # Signal emitted when logout is requested
    logout_requested = pyqtSignal()
    
    def __init__(self, controller: AppController):
        """Initialize game view.
        
        Args:
            controller (AppController): Application controller
        """
        super().__init__()
        self.controller = controller
        self.init_ui()
        
        # Set up game state
        self.game_in_progress = False
        self.last_called_number = None
        
        # Timer for auto-advance
        self.auto_advance_timer = QTimer()
        self.auto_advance_timer.timeout.connect(self.auto_advance_timeout)
        self.auto_advance_active = False
    
    def init_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Top bar with controls
        top_bar = QHBoxLayout()
        
        # Game controls
        self.new_game_btn = QPushButton("New Game")
        self.new_game_btn.clicked.connect(self.start_new_game)
        top_bar.addWidget(self.new_game_btn)
        
        self.verify_btn = QPushButton("Verify Winner")
        self.verify_btn.clicked.connect(self.verify_winner)
        self.verify_btn.setEnabled(False)
        top_bar.addWidget(self.verify_btn)
        
        top_bar.addStretch()
        
        # Navigation buttons
        self.pattern_btn = QPushButton("Pattern Editor")
        self.pattern_btn.clicked.connect(
            lambda: self.parent().parent().show_pattern_editor()
        )
        top_bar.addWidget(self.pattern_btn)
        
        self.cards_btn = QPushButton("Card Manager")
        self.cards_btn.clicked.connect(
            lambda: self.parent().parent().show_card_manager()
        )
        top_bar.addWidget(self.cards_btn)
        
        self.admin_btn = QPushButton("Admin Panel")
        self.admin_btn.clicked.connect(
            lambda: self.parent().parent().show_admin_panel()
        )
        self.admin_btn.setVisible(False)
        top_bar.addWidget(self.admin_btn)
        
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout_requested.emit)
        top_bar.addWidget(logout_btn)
        
        layout.addLayout(top_bar)
        
        # Main game area
        game_layout = QHBoxLayout()
        
        # Ball display
        self.ball_display = BallDisplay()
        game_layout.addWidget(self.ball_display, stretch=2)
        
        # Right side panel
        right_panel = QVBoxLayout()
        
        # Pattern display
        self.pattern_display = PatternDisplay()
        right_panel.addWidget(self.pattern_display)
        
        # Ball call controls
        call_controls = QVBoxLayout()
        
        self.last_call_label = QLabel("Last Call: None")
        self.last_call_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.last_call_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        call_controls.addWidget(self.last_call_label)
        
        # Ball call buttons
        ball_buttons = QHBoxLayout()
        
        self.call_btn = QPushButton("Call Ball")
        self.call_btn.clicked.connect(self.call_ball)
        self.call_btn.setEnabled(False)
        ball_buttons.addWidget(self.call_btn)
        
        self.auto_btn = QPushButton("Auto Call")
        self.auto_btn.clicked.connect(self.toggle_auto_call)
        self.auto_btn.setEnabled(False)
        ball_buttons.addWidget(self.auto_btn)
        
        call_controls.addLayout(ball_buttons)
        right_panel.addLayout(call_controls)
        
        # Add right panel to game layout
        game_layout.addLayout(right_panel, stretch=1)
        
        # Add game area to main layout
        layout.addLayout(game_layout)
    
    def update_permissions(self, is_admin: bool):
        """Update UI based on user permissions.
        
        Args:
            is_admin (bool): Whether current user is admin
        """
        self.admin_btn.setVisible(is_admin)
    
    def start_new_game(self):
        """Start a new game."""
        # TODO: Implement game setup dialog
        pass
    
    def call_ball(self):
        """Call a new ball."""
        if not self.game_in_progress:
            return
            
        number, ok = QInputDialog.getInt(
            self,
            "Call Ball",
            "Enter ball number (1-75):",
            min=1,
            max=75
        )
        
        if ok:
            success, message = self.controller.call_number(number)
            if success:
                self.ball_display.highlight_ball(number)
                self.last_called_number = number
                self.last_call_label.setText(f"Last Call: {number}")
            else:
                QMessageBox.warning(self, "Error", message)
    
    def toggle_auto_call(self):
        """Toggle automatic ball calling."""
        if self.auto_advance_active:
            self.auto_advance_timer.stop()
            self.auto_advance_active = False
            self.auto_btn.setText("Auto Call")
        else:
            interval, ok = QInputDialog.getInt(
                self,
                "Auto Call",
                "Enter interval in seconds:",
                value=30,
                min=5,
                max=120
            )
            if ok:
                self.auto_advance_timer.start(interval * 1000)
                self.auto_advance_active = True
                self.auto_btn.setText("Stop Auto")
    
    def auto_advance_timeout(self):
        """Handle auto-advance timer timeout."""
        self.call_ball()
    
    def verify_winner(self):
        """Verify a winning card."""
        if not self.game_in_progress:
            return
            
        serial, ok = QInputDialog.getText(
            self,
            "Verify Winner",
            "Enter card serial number:"
        )
        
        if ok and serial:
            success, message, is_winner = self.controller.verify_winner(serial)
            if success:
                if is_winner:
                    response = QMessageBox.question(
                        self,
                        "Winner Verified",
                        "Card is a winner! End game?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if response == QMessageBox.StandardButton.Yes:
                        self.end_game(serial)
                else:
                    QMessageBox.information(
                        self,
                        "Not a Winner",
                        "Card is not a winner."
                    )
            else:
                QMessageBox.warning(self, "Error", message)
    
    def end_game(self, winner_card: str = None):
        """End the current game.
        
        Args:
            winner_card (str, optional): Winning card serial number
        """
        success, message = self.controller.end_game(winner_card)
        if success:
            self.game_in_progress = False
            self.call_btn.setEnabled(False)
            self.auto_btn.setEnabled(False)
            self.verify_btn.setEnabled(False)
            self.ball_display.reset_display()
            self.last_call_label.setText("Last Call: None")
            self.last_called_number = None
            
            if self.auto_advance_active:
                self.toggle_auto_call()
            
            QMessageBox.information(self, "Game Over", "Game has ended.")
        else:
            QMessageBox.warning(self, "Error", message)
