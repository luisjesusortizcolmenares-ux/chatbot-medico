import sqlite3

DB_NAME = "clinica_preventiva.db"

def inicializar_db():
    """Crea las tablas si no existen al arrancar el programa."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla de pacientes (Perfil básico)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            telefono TEXT PRIMARY KEY,
            nombre TEXT,
            edad INTEGER,
            condiciones TEXT,
            estado_registro TEXT DEFAULT 'NUEVO'
        )
    ''')
    
    # Tabla de registros diarios (Lo que come, hace, etc.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros_diarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telefono TEXT,
            fecha TEXT DEFAULT CURRENT_DATE,
            comidas TEXT,
            ejercicio TEXT,
            sintomas TEXT,
            alertas TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def obtener_paciente(telefono):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pacientes WHERE telefono = ?", (telefono,))
    paciente = cursor.fetchone()
    conn.close()
    return paciente

def registrar_paciente(telefono, nombre, edad, condiciones):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO pacientes (telefono, nombre, edad, condiciones, estado_registro)
        VALUES (?, ?, ?, ?, 'COMPLETO')
    ''', (telefono, nombre, edad, condiciones))
    conn.commit()
    conn.close()

def guardar_registro_diario(telefono, comidas, ejercicio, sintomas, alertas):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO registros_diarios (telefono, comidas, ejercicio, sintomas, alertas)
        VALUES (?, ?, ?, ?, ?)
    ''', (telefono, comidas, ejercicio, sintomas, alertas))
    conn.commit()
    conn.close()

# Inicializamos la base de datos automáticamente al importar o correr este archivo
inicializar_db()
print("¡Base de datos y tablas creadas con éxito en Windows 11!")