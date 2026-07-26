import sqlite3
import pandas as pd

# Conectar a la base de datos
conexion = sqlite3.connect('notebooks/ejemplo.db')

# Traer todos los clientes como una tabla (DataFrame)
tabla = pd.read_sql_query("SELECT * FROM clientes", conexion)

conexion.close()

# Mostrar la tabla en pantalla
print(tabla)

# Exportar a un archivo Excel real
tabla.to_excel('notebooks/clientes.xlsx', index=False)

print("Archivo Excel creado correctamente.")