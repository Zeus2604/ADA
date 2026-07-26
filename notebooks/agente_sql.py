import ollama
import sqlite3

contexto = """Eres un generador de SQL. Tu única función es convertir preguntas en español a consultas SQL.

Tabla disponible: clientes
Columnas: id, nombre, ciudad, saldo

Reglas:
- Responde SOLO con la consulta SQL, en una sola línea.
- No agregues explicaciones, ni texto antes o después.
- No agregues comillas ni la palabra "sql".

Ejemplo:
Pregunta: Dame los clientes de Bogotá
Respuesta: SELECT * FROM clientes WHERE ciudad = 'Bogotá';

Ejemplo:
Pregunta: Cuántos clientes hay
Respuesta: SELECT COUNT(*) FROM clientes;
"""

pregunta = "Dame los clientes con saldo mayor a 1000000"

# Paso 1: el modelo genera el SQL
respuesta = ollama.chat(model='qwen2:0.5b', messages=[
    {'role': 'system', 'content': contexto},
    {'role': 'user', 'content': pregunta}
])

sql_generado = respuesta['message']['content'].strip()
print("Pregunta:", pregunta)
print("SQL generado:", sql_generado)

# Paso 2: ejecutamos ese SQL contra la base de datos real
conexion = sqlite3.connect('notebooks/ejemplo.db')
cursor = conexion.cursor()

cursor.execute(sql_generado)
resultados = cursor.fetchall()

conexion.close()

print("\nResultado real de la base de datos:")
for fila in resultados:
    print(fila)