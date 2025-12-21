import sqlite3
from pathlib import Path
from datetime import datetime
from src.config import paths

DB_PATH = paths/"logs_estimations.db"


def init_db():
    """Crée la table si elle n'existe pas"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            adresse TEXT,
            arrondissement INTEGER,
            surface REAL,
            pieces INTEGER,
            annee INTEGER,
            prix_estime REAL,
            classification TEXT,
            confiance REAL,
            ip_client TEXT
        )
    ''')
    conn.commit()
    conn.close()


def log_request(data: dict, result: dict, client_ip: str = "127.0.0.1"):
    """Enregistre une requête et son résultat"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        INSERT INTO logs (
            timestamp, adresse, arrondissement, surface, pieces, annee, 
            prix_estime, classification, confiance, ip_client
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        data.get('adresse'),
        result['geo_info']['arrondissement'],
        data.get('surface'),
        data.get('pieces'),
        data.get('annee'),
        result.get('prix_m2_estime'),
        result.get('classification'),
        result.get('confiance'),
        client_ip
    ))

    conn.commit()
    conn.close()