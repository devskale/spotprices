# config.py
from pathlib import Path

CONFIG = {
    'db_file': 'spotprices.db',
    'db_path': Path(__file__).parent / 'data'
}

TARIF_CONFIG = {
    'Tarifueberblick': [
        {
            "url": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQzXH8w3XpQT-DKUNf-6rDV3X1j6n-s5BRKkkTkbcvym-VbMgPBj1NbaE0rcfoU04hslJXKDd13AdcI/pub?gid=1603076999&single=true&output=csv",
            "Beschreibung": "Liste mit Tarifüberblicksseiten"
        }
    ]
}

CRAWL_CONFIG = {
    'w3m': [
        {
            "PREFIX": "https://amd1.mooo.com/api/w3m?url=",
            "Bearer": "test23",
            "Format": "txt"
        }
    ],
    'lynx': [
        {
            "PREFIX": "https://amd1.mooo.com/api/lynx?url=",
            "Bearer": "test23",
            "Format": "txt"
        }
    ],
    'markdowner': [
        {
            "PREFIX": "https://md.dhr.wtf/?url=",
            "Bearer": "",
            "format": "md"
        }
    ],
}