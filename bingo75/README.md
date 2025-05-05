# Bingo 75-Ball Game System

A comprehensive Python-based bingo game management system with secure login, card management, pattern editor, and game controls.

## Features

- Secure login system with admin privileges and 2FA
- SQLite database backend
- PyQt6-based GUI
- Card management with batch import
- Pattern editor with moving patterns support
- Game preparation and control interface
- Winner verification system
- Comprehensive reporting

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Initialize the database:
```bash
python scripts/init_db.py
```

## Project Structure

```
bingo75/
├── src/
│   ├── models/         # Database models
│   ├── views/          # GUI components
│   ├── controllers/    # Business logic
│   ├── utils/         # Helper functions
│   └── resources/     # Images, sounds, etc.
├── tests/            # Unit tests
├── scripts/          # Setup and maintenance scripts
├── docs/            # Documentation
└── requirements.txt  # Project dependencies
```

## Usage

Run the application:
```bash
python src/main.py
```

## License

MIT License
