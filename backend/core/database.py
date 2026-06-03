import sqlite3
import os
from core.config import sqliteDbPath, kernelLogger

def inicializarBaseDatos():
    kernelLogger.info(f"💾 Inicializando base de datos SQLite en: {sqliteDbPath}")
    dbDirectory = os.path.dirname(sqliteDbPath)
    if dbDirectory:
        os.makedirs(dbDirectory, exist_ok=True)
        
    connection = sqlite3.connect(sqliteDbPath)
    cursor = connection.cursor()
    
    # Tabla de historial de chat
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chatHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userId TEXT,
            terminalId TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de preferencias del sistema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS systemPreferences (
            prefKey TEXT PRIMARY KEY,
            prefValue TEXT
        )
    """)
    
    connection.commit()
    connection.close()

def guardarMensajeChat(userId: str, terminalId: str, role: str, content: str):
    connection = sqlite3.connect(sqliteDbPath)
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO chatHistory (userId, terminalId, role, content)
        VALUES (?, ?, ?, ?)
    """, (userId, terminalId, role, content))
    connection.commit()
    connection.close()

def obtenerMensajesChat(userId: str, terminalId: str, limit: int = 20) -> list[dict]:
    connection = sqlite3.connect(sqliteDbPath)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT role, content, timestamp FROM chatHistory
        WHERE userId = ? AND terminalId = ?
        ORDER BY id DESC LIMIT ?
    """, (userId, terminalId, limit))
    rows = cursor.fetchall()
    connection.close()
    
    # Retornamos en orden cronológico
    messages = []
    for row in reversed(rows):
        messages.append({
            "role": row[0],
            "content": row[1],
            "timestamp": row[2]
        })
    return messages

def guardarPreferencia(prefKey: str, prefValue: str):
    connection = sqlite3.connect(sqliteDbPath)
    cursor = connection.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO systemPreferences (prefKey, prefValue)
        VALUES (?, ?)
    """, (prefKey, prefValue))
    connection.commit()
    connection.close()

def obtenerPreferencia(prefKey: str, defaultValue: str = "") -> str:
    connection = sqlite3.connect(sqliteDbPath)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT prefValue FROM systemPreferences
        WHERE prefKey = ?
    """, (prefKey,))
    row = cursor.fetchone()
    connection.close()
    if row:
        return row[0]
    return defaultValue
