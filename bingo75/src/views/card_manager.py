from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QFrame, QScrollArea, QMessageBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import List, Dict, Optional
from controllers.app_controller import AppController

class CardPreview(QFrame):
    """Widget for displaying a bingo card preview."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Set up the card preview UI."""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #2c3e50;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Card header
        header_layout = QHBoxLayout()
        
        self.serial_label = QLabel()
        self.serial_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.serial_label)
        
        self.batch_label = QLabel()
        header_layout.addWidget(self.batch_label)
        
        layout.addLayout(header_layout)
        
        # Card grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)
        
        # Column headers (B-I-N-G-O)
        headers = ['B', 'I', 'N', 'G', 'O']
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-weight: bold;")
            grid_layout.addWidget(label, 0, col)
        
        # Create number cells
        self.number_labels = []
        for row in range(5):
            row_labels = []
            for col in range(5):
                label = QLabel()
                label.setFixedSize(40, 40)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setStyleSheet("""
                    QLabel {
                        background-color: #ecf0f1;
                        border: 1px solid #bdc3c7;
                        border-radius: 5px;
                    }
                """)
                grid_layout.addWidget(label, row + 1, col)
                row_labels.append(label)
            self.number_labels.append(row_labels)
        
        layout.addLayout(grid_layout)
        
        # Card status
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
    
    def update_card(self, card_data: Dict):
        """Update card preview with new data.
        
        Args:
            card_data (dict): Card information
        """
        self.serial_label.setText(f"Serial: {card_data['serial_number']}")
        self.batch_label.setText(f"Batch: {card_data['batch_number']}")
        
        # Update numbers
        numbers = card_data['numbers']
        for row in range(5):
            for col in range(5):
                number = numbers[row][col]
                label = self.number_labels[row][col]
                if number is None:
                    label.setText("FREE")
                    label.setStyleSheet("""
                        QLabel {
                            background-color: #f1c40f;
                            border: 1px solid #f39c12;
                            border-radius: 5px;
                            font-weight: bold;
                        }
                    """)
                else:
                    label.setText(str(number))
                    label.setStyleSheet("""
                        QLabel {
                            background-color: #ecf0f1;
                            border: 1px solid #bdc3c7;
                            border-radius: 5px;
                        }
                    """)
        
        # Update status with color coding
        status = card_data['status']
        status_styles = {
            'available': ('Available', '#2ecc71'),
            'in_play': ('In Play', '#f1c40f'),
            'won': ('Won', '#e74c3c')
        }
        status_text, color = status_styles.get(status, ('Unknown', '#95a5a6'))
        self.status_label.setText(f"Status: {status_text}")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-weight: bold;
                padding: 5px;
            }}
        """)

class CardManager(QWidget):
    """Card management interface."""
    
    # Signal emitted when back button is clicked
    back_requested = pyqtSignal()
    
    def __init__(self, controller: AppController):
        """Initialize card manager.
        
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
        
        import_btn = QPushButton("Import Cards")
        import_btn.clicked.connect(self.import_cards)
        top_bar.addWidget(import_btn)
        
        layout.addLayout(top_bar)
        
        # Search controls
        search_group = QGroupBox("Search Cards")
        search_layout = QHBoxLayout(search_group)
        
        # Batch number search
        search_layout.addWidget(QLabel("Batch:"))
        self.batch_input = QLineEdit()
        search_layout.addWidget(self.batch_input)
        
        # Status filter
        search_layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(['All', 'Available', 'In Play', 'Won'])
        search_layout.addWidget(self.status_combo)
        
        # Search button
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.search_cards)
        search_layout.addWidget(search_btn)
        
        layout.addWidget(search_group)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Card list
        list_layout = QVBoxLayout()
        
        self.card_table = QTableWidget()
        self.card_table.setColumnCount(3)
        self.card_table.setHorizontalHeaderLabels(['Serial', 'Batch', 'Status'])
        self.card_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.card_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.card_table.itemSelectionChanged.connect(self.on_card_selected)
        list_layout.addWidget(self.card_table)
        
        content_layout.addLayout(list_layout)
        
        # Card preview
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(QLabel("Card Preview"))
        
        self.card_preview = CardPreview()
        preview_layout.addWidget(self.card_preview)
        
        content_layout.addLayout(preview_layout)
        
        # Add content area to main layout
        layout.addLayout(content_layout)
    
    def import_cards(self):
        """Import cards from CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Cards",
            "",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            imported, errors = self.controller.import_cards(file_path)
            
            if errors:
                QMessageBox.warning(
                    self,
                    "Import Errors",
                    f"Imported {imported} cards with {len(errors)} errors:\n\n" +
                    "\n".join(errors)
                )
            else:
                QMessageBox.information(
                    self,
                    "Import Success",
                    f"Successfully imported {imported} cards"
                )
            
            # Refresh card list
            self.search_cards()
    
    def search_cards(self):
        """Search cards based on current filters."""
        batch = self.batch_input.text().strip()
        status = self.status_combo.currentText().lower()
        if status == 'all':
            status = None
        
        cards = self.controller.card_model.search_cards(batch, status)
        
        # Update table
        self.card_table.setRowCount(len(cards))
        for row, card in enumerate(cards):
            self.card_table.setItem(
                row, 0, QTableWidgetItem(card['serial_number'])
            )
            self.card_table.setItem(
                row, 1, QTableWidgetItem(card['batch_number'])
            )
            self.card_table.setItem(
                row, 2, QTableWidgetItem(card['status'])
            )
        
        self.card_table.resizeColumnsToContents()
    
    def on_card_selected(self):
        """Handle card selection in table."""
        selected = self.card_table.selectedItems()
        if not selected:
            return
            
        serial = self.card_table.item(selected[0].row(), 0).text()
        card = self.controller.card_model.get_card(serial)
        if card:
            self.card_preview.update_card(card)
