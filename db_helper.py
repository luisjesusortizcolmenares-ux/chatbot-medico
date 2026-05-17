import psycopg2
import os

# Jala la URL de tu base de datos de Render de forma oculta y segura
DATABASE_URL = os.environ.get("DATABASE_URL")

def obtener_conexion():
    """Establece la conexión con la base de datos PostgreSQL de Render."""
    return psycopg2.connect(DATABASE_URL)

def inicializar_db():
    """Crea las tablas si no existen en PostgreSQL."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # Tabla de pacientes (Perfil básico) - Sintaxis Postgres
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
            id SERIAL PRIMARY KEY,
            telefono TEXT,
            fecha DATE DEFAULT CURRENT_DATE,
            comidas TEXT,
            ejercicio TEXT,
            sintomas TEXT,
            alertas TEXT
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

def obtener_paciente(telefono):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pacientes WHERE telefono = %s", (telefono,))
    paciente = cursor.fetchone()
    cursor.close()
    conn.close()
    return paciente

def registrar_paciente(telefono, nombre, edad, condiciones):
    conn = obtener_conexion()
    cursor = conn.cursor()
    # Usamos la sintaxis oficial de Postgres para el "INSERT OR REPLACE"
    cursor.execute('''
        INSERT INTO pacientes (telefono, nombre, edad, condiciones, estado_registro)
        VALUES (%s, %s, %s, %s, 'COMPLETO')
        ON CONFLICT (telefono) 
        DO UPDATE SET nombre = EXCLUDED.nombre, edad = EXCLUDED.edad, condiciones = EXCLUDED.condiciones, estado_registro = 'COMPLETO'
    ''', (telefono, nombre, edad, condiciones))
    conn.commit()
    cursor.close()
    conn.close()

def guardar_registro_diario(telefono, comidas, ejercicio, sintomas, alertas):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO registros_diarios (telefono, comidas, ejercicio, sintomas, alertas)
        VALUES (%s, %s, %s, %s, %s)
    ''', (telefono, comidas, ejercicio, sintomas, alertas))
    conn.commit()
    cursor.close()
    conn.close()

# Inicializamos las tablas en la nube automáticamente
if DATABASE_URL:
    inicializar_db()
    print("¡Base de datos y tablas sincronizadas con éxito en PostgreSQL de Render!")
else:
    print("[ERROR] No se encontró la variable DATABASE_URL.")