from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from controllers.app_controller import AppController

class LoginView(QWidget):
    """Login screen for user authentication."""
    
    # Signal emitted on successful login
    login_successful = pyqtSignal()
    
    def __init__(self, controller: AppController):
        """Initialize login view.
        
        Args:
            controller (AppController): Application controller
        """
        super().__init__()
        self.controller = controller
        self.init_ui()
    
    def init_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create form layout for inputs
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        
        # Style for form labels
        label_style = """
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
            }
        """
        
        # Style for input fields
        input_style = """
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
                min-width: 250px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """
        
        # Username input
        username_label = QLabel("Username:")
        username_label.setStyleSheet(label_style)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setStyleSheet(input_style)
        form_layout.addRow(username_label, self.username_input)
        
        # Password input
        password_label = QLabel("Password:")
        password_label.setStyleSheet(label_style)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(input_style)
        form_layout.addRow(password_label, self.password_input)
        
        # 2FA input (initially hidden)
        self.totp_label = QLabel("2FA Code:")
        self.totp_label.setStyleSheet(label_style)
        self.totp_input = QLineEdit()
        self.totp_input.setPlaceholderText("Enter 2FA code")
        self.totp_input.setStyleSheet(input_style)
        self.totp_input.setMaxLength(6)
        self.totp_input.setVisible(False)
        self.totp_label.setVisible(False)
        form_layout.addRow(self.totp_label, self.totp_input)
        
        # Add form to main layout
        layout.addWidget(form_widget)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(10)
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #219a52;
            }
        """)
        self.login_button.clicked.connect(self.attempt_login)
        button_layout.addWidget(self.login_button)
        
        # Clear button
        clear_button = QPushButton("Clear")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        clear_button.clicked.connect(self.clear_inputs)
        button_layout.addWidget(clear_button)
        
        # Add buttons to main layout
        layout.addLayout(button_layout)
        
        # Set up event handlers
        self.username_input.returnPressed.connect(self.focus_password)
        self.password_input.returnPressed.connect(self.handle_password_return)
        self.totp_input.returnPressed.connect(self.attempt_login)
    
    def focus_password(self):
        """Move focus to password input."""
        self.password_input.setFocus()
    
    def handle_password_return(self):
        """Handle return press in password field."""
        if self.totp_input.isVisible():
            self.totp_input.setFocus()
        else:
            self.attempt_login()
    
    def clear_inputs(self):
        """Clear all input fields."""
        self.username_input.clear()
        self.password_input.clear()
        self.totp_input.clear()
        self.username_input.setFocus()
    
    def show_error(self, message: str):
        """Show error message dialog.
        
        Args:
            message (str): Error message to display
        """
        QMessageBox.critical(
            self,
            "Login Error",
            message,
            QMessageBox.StandardButton.Ok
        )
    
    def attempt_login(self):
        """Attempt to log in with provided credentials."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        totp_code = self.totp_input.text().strip() if self.totp_input.isVisible() else None
        
        if not username or not password:
            self.show_error("Please enter both username and password")
            return
        
        # Attempt login
        success, message = self.controller.login(username, password, totp_code)
        
        if success:
            self.clear_inputs()
            self.login_successful.emit()
        else:
            # Check if 2FA is required
            if "2FA token required" in message:
                self.totp_label.setVisible(True)
                self.totp_input.setVisible(True)
                self.totp_input.setFocus()
            else:
                self.show_error(message)
    
    def showEvent(self, event):
        """Handle widget show event."""
        super().showEvent(event)
        # Reset view state
        self.clear_inputs()
        self.totp_label.setVisible(False)
        self.totp_input.setVisible(False)
