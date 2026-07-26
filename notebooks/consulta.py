import sqlite3

# Conectar a la base de datos que ya creamos
conexion = sqlite3.connect('notebooks/ejemplo.db')
cursor = conexion.cursor()

# Consulta SQL: traer todos los clientes con saldo mayor a 1,000,000
cursor.execute('''
SELECT nombre, ciudad, saldo
FROM clientes
WHERE saldo > 1000000
''')

resultados = cursor.fetchall()

print("Clientes con saldo mayor a 1,000,000:")
for fila in resultados:
    print(fila)

conexion.close()