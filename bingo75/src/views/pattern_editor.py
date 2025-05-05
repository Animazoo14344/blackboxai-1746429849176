from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QFrame, QScrollArea, QMessageBox, QCheckBox,
    QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import List, Dict
from controllers.app_controller import AppController

class PatternCell(QPushButton):
    """Interactive cell for pattern grid."""
    
    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        self.setFixedSize(50, 50)
        self.update_style()
        self.toggled.connect(self.update_style)
    
    def update_style(self):
        """Update cell appearance based on state."""
        if self.isChecked():
            self.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    border: 2px solid #2980b9;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #ecf0f1;
                    border: 2px solid #bdc3c7;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #bdc3c7;
                }
            """)

class PatternGrid(QFrame):
    """5x5 grid for pattern editing."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Set up the pattern grid UI."""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #2c3e50;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout = QGridLayout(self)
        layout.setSpacing(5)
        
        # Create grid cells
        self.cells = []
        for row in range(5):
            row_cells = []
            for col in range(5):
                cell = PatternCell()
                # Center cell is always checked (FREE space)
                if row == 2 and col == 2:
                    cell.setChecked(True)
                    cell.setEnabled(False)
                layout.addWidget(cell, row, col)
                row_cells.append(cell)
            self.cells.append(row_cells)
    
    def get_pattern(self) -> List[List[bool]]:
        """Get current pattern as 2D boolean array.
        
        Returns:
            List[List[bool]]: Pattern grid
        """
        return [[cell.isChecked() for cell in row] for row in self.cells]
    
    def set_pattern(self, pattern: List[List[bool]]):
        """Set pattern from 2D boolean array.
        
        Args:
            pattern (List[List[bool]]): Pattern grid
        """
        for row in range(5):
            for col in range(5):
                if row == 2 and col == 2:  # FREE space
                    continue
                self.cells[row][col].setChecked(pattern[row][col])
    
    def clear_pattern(self):
        """Clear pattern (except FREE space)."""
        for row in range(5):
            for col in range(5):
                if row == 2 and col == 2:  # FREE space
                    continue
                self.cells[row][col].setChecked(False)

class MovementRulesEditor(QGroupBox):
    """Editor for pattern movement rules."""
    
    def __init__(self):
        super().__init__("Movement Rules")
        self.init_ui()
    
    def init_ui(self):
        """Set up the movement rules editor UI."""
        layout = QVBoxLayout(self)
        
        # Movement type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Shift", "Rotate"])
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Direction (for shift)
        direction_layout = QHBoxLayout()
        direction_layout.addWidget(QLabel("Direction:"))
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["Right", "Left", "Up", "Down"])
        direction_layout.addWidget(self.direction_combo)
        layout.addLayout(direction_layout)
        
        # Trigger settings
        trigger_group = QGroupBox("Trigger")
        trigger_layout = QVBoxLayout(trigger_group)
        
        # Trigger type
        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems(["Call Count"])
        trigger_layout.addWidget(self.trigger_combo)
        
        # Trigger value
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Value:"))
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("e.g., 5 for every 5 calls")
        value_layout.addWidget(self.value_input)
        trigger_layout.addLayout(value_layout)
        
        layout.addWidget(trigger_group)
    
    def get_rules(self) -> Dict:
        """Get current movement rules configuration.
        
        Returns:
            dict: Movement rules
        """
        return {
            "type": self.type_combo.currentText().lower(),
            "direction": self.direction_combo.currentText().lower(),
            "trigger": {
                "type": "call_count",
                "value": int(self.value_input.text() or 0)
            }
        }
    
    def set_rules(self, rules: Dict):
        """Set movement rules configuration.
        
        Args:
            rules (dict): Movement rules
        """
        if not rules:
            return
            
        self.type_combo.setCurrentText(rules["type"].capitalize())
        self.direction_combo.setCurrentText(rules["direction"].capitalize())
        if "trigger" in rules:
            self.value_input.setText(str(rules["trigger"].get("value", "")))

class PatternEditor(QWidget):
    """Pattern editor interface."""
    
    # Signal emitted when back button is clicked
    back_requested = pyqtSignal()
    
    def __init__(self, controller: AppController):
        """Initialize pattern editor.
        
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
        
        top_bar.addStretch()
        
        self.save_btn = QPushButton("Save Pattern")
        self.save_btn.clicked.connect(self.save_pattern)
        top_bar.addWidget(self.save_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_pattern)
        top_bar.addWidget(clear_btn)
        
        layout.addLayout(top_bar)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Left side - Pattern grid
        left_panel = QVBoxLayout()
        
        # Pattern details
        details_group = QGroupBox("Pattern Details")
        details_layout = QVBoxLayout(details_group)
        
        # Pattern name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        details_layout.addLayout(name_layout)
        
        # Pattern category
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Standard", "Four Corners", "Letter X", "Blackout",
            "Custom"
        ])
        category_layout.addWidget(self.category_combo)
        details_layout.addLayout(category_layout)
        
        left_panel.addWidget(details_group)
        
        # Pattern grid
        self.pattern_grid = PatternGrid()
        left_panel.addWidget(self.pattern_grid)
        
        content_layout.addLayout(left_panel)
        
        # Right side - Movement rules
        right_panel = QVBoxLayout()
        
        # Moving pattern toggle
        self.moving_check = QCheckBox("Moving Pattern")
        self.moving_check.toggled.connect(self.toggle_movement_rules)
        right_panel.addWidget(self.moving_check)
        
        # Movement rules editor
        self.movement_editor = MovementRulesEditor()
        self.movement_editor.setEnabled(False)
        right_panel.addWidget(self.movement_editor)
        
        right_panel.addStretch()
        
        content_layout.addLayout(right_panel)
        
        # Add content area to main layout
        layout.addLayout(content_layout)
    
    def toggle_movement_rules(self, enabled: bool):
        """Enable/disable movement rules editor.
        
        Args:
            enabled (bool): Whether to enable movement rules
        """
        self.movement_editor.setEnabled(enabled)
    
    def clear_pattern(self):
        """Clear the current pattern."""
        self.pattern_grid.clear_pattern()
        self.name_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.moving_check.setChecked(False)
    
    def save_pattern(self):
        """Save the current pattern."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a pattern name")
            return
        
        category = self.category_combo.currentText()
        grid = self.pattern_grid.get_pattern()
        is_moving = self.moving_check.isChecked()
        movement_rules = self.movement_editor.get_rules() if is_moving else None
        
        success, message = self.controller.create_pattern(
            name, category, grid, is_moving, movement_rules
        )
        
        if success:
            QMessageBox.information(self, "Success", "Pattern saved successfully")
            self.clear_pattern()
        else:
            QMessageBox.warning(self, "Error", message)
