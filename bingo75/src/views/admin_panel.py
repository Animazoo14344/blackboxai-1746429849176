from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QCheckBox, QGroupBox, QFormLayout, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from controllers.app_controller import AppController

class UserManagementTab(QWidget):
    """Tab for managing system users."""
    
    def __init__(self, controller: AppController):
        """Initialize user management tab.
        
        Args:
            controller (AppController): Application controller
        """
        super().__init__()
        self.controller = controller
        self.init_ui()
    
    def init_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # User creation form
        create_group = QGroupBox("Create User")
        form_layout = QFormLayout(create_group)
        
        self.username_input = QLineEdit()
        form_layout.addRow("Username:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_input)
        
        self.admin_check = QCheckBox("Admin privileges")
        form_layout.addRow("", self.admin_check)
        
        self.enable_2fa = QCheckBox("Enable 2FA")
        form_layout.addRow("", self.enable_2fa)
        
        create_btn = QPushButton("Create User")
        create_btn.clicked.connect(self.create_user)
        form_layout.addRow("", create_btn)
        
        layout.addWidget(create_group)
        
        # User list
        list_group = QGroupBox("User List")
        list_layout = QVBoxLayout(list_group)
        
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels([
            'Username', 'Admin', '2FA Enabled', 'Actions'
        ])
        list_layout.addWidget(self.user_table)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_users)
        list_layout.addWidget(refresh_btn)
        
        layout.addWidget(list_group)
        
        # Initial load
        self.refresh_users()
    
    def create_user(self):
        """Create a new user."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        is_admin = self.admin_check.isChecked()
        enable_2fa = self.enable_2fa.isChecked()
        
        if not username or not password:
            QMessageBox.warning(
                self,
                "Error",
                "Please enter both username and password"
            )
            return
        
        success, message = self.controller.user_model.create_user(
            username, password, is_admin, enable_2fa
        )
        
        if success:
            QMessageBox.information(
                self,
                "Success",
                "User created successfully"
            )
            self.username_input.clear()
            self.password_input.clear()
            self.admin_check.setChecked(False)
            self.enable_2fa.setChecked(False)
            self.refresh_users()
        else:
            QMessageBox.warning(self, "Error", message)
    
    def refresh_users(self):
        """Refresh the user list."""
        # Get all users from database
        query = """
            SELECT username, is_admin, totp_secret IS NOT NULL as has_2fa
            FROM users
            ORDER BY username
        """
        with self.controller.db:
            results = self.controller.db.execute(query).fetchall()
        
        self.user_table.setRowCount(len(results))
        for row, (username, is_admin, has_2fa) in enumerate(results):
            # Username
            self.user_table.setItem(
                row, 0, QTableWidgetItem(username)
            )
            
            # Admin status
            admin_item = QTableWidgetItem()
            admin_item.setCheckState(
                Qt.CheckState.Checked if is_admin else Qt.CheckState.Unchecked
            )
            self.user_table.setItem(row, 1, admin_item)
            
            # 2FA status
            twofa_item = QTableWidgetItem()
            twofa_item.setCheckState(
                Qt.CheckState.Checked if has_2fa else Qt.CheckState.Unchecked
            )
            self.user_table.setItem(row, 2, twofa_item)
            
            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            reset_btn = QPushButton("Reset Password")
            reset_btn.clicked.connect(
                lambda u=username: self.reset_password(u)
            )
            action_layout.addWidget(reset_btn)
            
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(
                lambda u=username: self.delete_user(u)
            )
            action_layout.addWidget(delete_btn)
            
            self.user_table.setCellWidget(row, 3, action_widget)
        
        self.user_table.resizeColumnsToContents()
    
    def reset_password(self, username: str):
        """Reset user password.
        
        Args:
            username (str): Username
        """
        # Simple password reset - in production, would email reset link
        new_password, ok = QInputDialog.getText(
            self,
            "Reset Password",
            f"Enter new password for {username}:",
            QLineEdit.EchoMode.Password
        )
        
        if ok and new_password:
            success, message = self.controller.user_model.update_password(
                username, new_password
            )
            
            if success:
                QMessageBox.information(
                    self,
                    "Success",
                    "Password reset successfully"
                )
            else:
                QMessageBox.warning(self, "Error", message)
    
    def delete_user(self, username: str):
        """Delete a user.
        
        Args:
            username (str): Username
        """
        response = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete user {username}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if response == QMessageBox.StandardButton.Yes:
            # Delete user from database
            try:
                with self.controller.db:
                    self.controller.db.execute(
                        "DELETE FROM users WHERE username = ?",
                        (username,)
                    )
                QMessageBox.information(
                    self,
                    "Success",
                    "User deleted successfully"
                )
                self.refresh_users()
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to delete user: {str(e)}"
                )

class SystemConfigTab(QWidget):
    """Tab for system configuration settings."""
    
    def __init__(self, controller: AppController):
        """Initialize system config tab.
        
        Args:
            controller (AppController): Application controller
        """
        super().__init__()
        self.controller = controller
        self.init_ui()
    
    def init_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Security settings
        security_group = QGroupBox("Security Settings")
        security_layout = QFormLayout(security_group)
        
        self.max_attempts = QSpinBox()
        self.max_attempts.setRange(1, 10)
        self.max_attempts.setValue(3)
        security_layout.addRow("Max Login Attempts:", self.max_attempts)
        
        self.lockout_time = QSpinBox()
        self.lockout_time.setRange(1, 60)
        self.lockout_time.setValue(15)
        security_layout.addRow("Lockout Time (minutes):", self.lockout_time)
        
        self.require_2fa = QCheckBox("Require 2FA for Admin Users")
        security_layout.addRow("", self.require_2fa)
        
        layout.addWidget(security_group)
        
        # Game settings
        game_group = QGroupBox("Game Settings")
        game_layout = QFormLayout(game_group)
        
        self.auto_verify = QCheckBox("Auto-verify Winners")
        game_layout.addRow("", self.auto_verify)
        
        self.sound_effects = QCheckBox("Enable Sound Effects")
        game_layout.addRow("", self.sound_effects)
        
        layout.addWidget(game_group)
        
        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
        # Load current settings
        self.load_settings()
    
    def load_settings(self):
        """Load current system settings."""
        # Load settings from database
        query = "SELECT key, value FROM system_settings"
        with self.controller.db:
            results = self.controller.db.execute(query).fetchall()
        
        settings = dict(results)
        
        # Apply settings to UI
        self.max_attempts.setValue(int(settings.get('max_login_attempts', 3)))
        self.lockout_time.setValue(int(settings.get('lockout_time', 15)))
        self.require_2fa.setChecked(settings.get('require_admin_2fa', '0') == '1')
        self.auto_verify.setChecked(settings.get('auto_verify', '0') == '1')
        self.sound_effects.setChecked(settings.get('sound_effects', '1') == '1')
    
    def save_settings(self):
        """Save system settings."""
        settings = {
            'max_login_attempts': str(self.max_attempts.value()),
            'lockout_time': str(self.lockout_time.value()),
            'require_admin_2fa': '1' if self.require_2fa.isChecked() else '0',
            'auto_verify': '1' if self.auto_verify.isChecked() else '0',
            'sound_effects': '1' if self.sound_effects.isChecked() else '0'
        }
        
        try:
            with self.controller.db:
                # Clear existing settings
                self.controller.db.execute("DELETE FROM system_settings")
                
                # Insert new settings
                for key, value in settings.items():
                    self.controller.db.execute(
                        "INSERT INTO system_settings (key, value) VALUES (?, ?)",
                        (key, value)
                    )
            
            QMessageBox.information(
                self,
                "Success",
                "Settings saved successfully"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to save settings: {str(e)}"
            )

class AdminPanel(QWidget):
    """Administrative control panel."""
    
    # Signal emitted when back button is clicked
    back_requested = pyqtSignal()
    
    def __init__(self, controller: AppController):
        """Initialize admin panel.
        
        Args:
            controller (AppController): Application controller
        """
        super().__init__()
        self.controller = controller
        self.init_ui()
    
    def init_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Top bar
        top_bar = QHBoxLayout()
        
        back_btn = QPushButton("Back to Game")
        back_btn.clicked.connect(self.back_requested.emit)
        top_bar.addWidget(back_btn)
        
        layout.addLayout(top_bar)
        
        # Tab widget
        tabs = QTabWidget()
        
        # Add tabs
        tabs.addTab(UserManagementTab(self.controller), "User Management")
        tabs.addTab(SystemConfigTab(self.controller), "System Configuration")
        
        layout.addWidget(tabs)
