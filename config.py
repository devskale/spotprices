# config.py
from pathlib import Path

CONFIG = {
    'db_file': 'spotprices.db',
    'db_path': Path(__file__).parent / 'data'
}
