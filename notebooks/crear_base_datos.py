import sqlite3

# Crear (o conectar a) la base de datos
conexion = sqlite3.connect('notebooks/ejemplo.db')
cursor = conexion.cursor()

# Crear una tabla de ejemplo: clientes ficticios
cursor.execute('''
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY,
    nombre TEXT,
    ciudad TEXT,
    saldo REAL
)
''')

# Insertar datos ficticios de ejemplo
cursor.executemany('''
INSERT INTO clientes (nombre, ciudad, saldo) VALUES (?, ?, ?)
''', [
    ('Cliente Ficticio 1', 'Bogotá', 1500000),
    ('Cliente Ficticio 2', 'Medellín', 2300000),
    ('Cliente Ficticio 3', 'Cali', 980000),
])

conexion.commit()
conexion.close()

print("Base de datos de ejemplo creada correctamente.")