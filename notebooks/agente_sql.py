import ollama
import sqlite3
import pandas as pd

contexto = """Eres un generador de SQL. Tu única función es convertir preguntas en español a consultas SQL.

Tabla disponible: clientes
Columnas:
- id (número)
- nombre (texto)
- ciudad (texto)
- saldo (número decimal)
- producto (texto: Cuenta Ahorros, Cuenta Corriente, CDT, Crédito de Consumo, Crédito Hipotecario)
- fecha_vinculacion (fecha en formato YYYY-MM-DD)
- estado_mora (texto: Al día, Mora temprana, Mora avanzada)
- segmento (texto: Persona Natural, Pyme, Empresarial)

Reglas:
- Responde SOLO con la consulta SQL, en una sola línea.
- No agregues explicaciones, ni texto antes o después.
- No agregues comillas ni la palabra "sql".
- Siempre incluye la cláusula FROM clientes.

Ejemplo:
Pregunta: Dame los clientes de Bogotá
Respuesta: SELECT * FROM clientes WHERE ciudad = 'Bogotá';

Ejemplo:
Pregunta: Cuántos clientes hay
Respuesta: SELECT COUNT(*) FROM clientes;

Ejemplo:
Pregunta: Cuál es el promedio de saldo
Respuesta: SELECT AVG(saldo) FROM clientes;

Ejemplo:
Pregunta: Ordena los clientes de mayor a menor saldo
Respuesta: SELECT * FROM clientes ORDER BY saldo DESC;

Ejemplo:
Pregunta: Cuál es el cliente con el saldo más alto
Respuesta: SELECT * FROM clientes ORDER BY saldo DESC LIMIT 1;

Ejemplo:
Pregunta: Cuántos clientes hay por ciudad
Respuesta: SELECT ciudad, COUNT(*) FROM clientes GROUP BY ciudad;

Ejemplo:
Pregunta: Cuál es el saldo total por ciudad
Respuesta: SELECT ciudad, SUM(saldo) FROM clientes GROUP BY ciudad;

Ejemplo:
Pregunta: Cuántos clientes están en mora avanzada
Respuesta: SELECT COUNT(*) FROM clientes WHERE estado_mora = 'Mora avanzada';

Ejemplo:
Pregunta: Cuántos clientes tiene cada producto
Respuesta: SELECT producto, COUNT(*) FROM clientes GROUP BY producto;

Ejemplo:
Pregunta: Cuál es el saldo promedio por segmento
Respuesta: SELECT segmento, AVG(saldo) FROM clientes GROUP BY segmento;

Ejemplo:
Pregunta: Dame los clientes vinculados después de 2022
Respuesta: SELECT * FROM clientes WHERE fecha_vinculacion > '2022-01-01';
"""

def generar_sql(pregunta, correccion=None):
    mensajes = [{'role': 'system', 'content': contexto}]
    if correccion:
        mensajes.append({'role': 'user', 'content': pregunta})
        mensajes.append({'role': 'assistant', 'content': correccion['sql_fallido']})
        mensajes.append({'role': 'user', 'content': f"Ese SQL tuvo un error: {correccion['error']}. Corrígelo y responde solo con el SQL correcto."})
    else:
        mensajes.append({'role': 'user', 'content': pregunta})

    respuesta = ollama.chat(model='qwen2:1.5b', messages=mensajes)
    sql = respuesta['message']['content'].strip()
    sql = sql.replace('Respuesta:', '').replace('respuesta:', '').strip()
    return sql

def es_seguro(sql):
    sql_minusculas = sql.lower()
    return (
        'from clientes' in sql_minusculas and
        sql_minusculas.startswith('select') and
        'drop' not in sql_minusculas and
        'delete' not in sql_minusculas and
        'update' not in sql_minusculas and
        'insert' not in sql_minusculas
    )

print("=== ADA - Agente de consultas ===")
print("Escribe tu pregunta sobre los clientes (o 'salir' para terminar)\n")

while True:
    pregunta = input("Tu pregunta: ")

    if pregunta.lower() in ['salir', 'exit', 'salir()']:
        print("¡Hasta luego!")
        break

    intentos = 0
    max_intentos = 2
    sql = generar_sql(pregunta)
    resultado_final = None

    while intentos < max_intentos:
        print(f"\nIntento {intentos + 1} — SQL generado: {sql}")

        if not es_seguro(sql):
            print("⚠️ No pasó la validación de seguridad. Pidiendo corrección al modelo...")
            sql = generar_sql(pregunta, correccion={'sql_fallido': sql, 'error': 'la consulta no es un SELECT seguro sobre la tabla clientes'})
            intentos += 1
            continue

        try:
            conexion = sqlite3.connect('notebooks/ejemplo.db')
            cursor = conexion.cursor()
            cursor.execute(sql)
            resultados = cursor.fetchall()
            columnas = [descripcion[0] for descripcion in cursor.description]
            conexion.close()
            resultado_final = (resultados, columnas)
            break
        except sqlite3.OperationalError as e:
            print(f"⚠️ Error al ejecutar: {e}. Pidiendo corrección al modelo...")
            sql = generar_sql(pregunta, correccion={'sql_fallido': sql, 'error': str(e)})
            intentos += 1

    if resultado_final:
        resultados, columnas = resultado_final
        print("\n✅ Resultado real de la base de datos:")
        for fila in resultados:
            print(fila)

        tabla_resultado = pd.DataFrame(resultados, columns=columnas)
        tabla_resultado.to_excel('notebooks/resultado_pregunta.xlsx', index=False)
        print("✅ Resultado exportado a: notebooks/resultado_pregunta.xlsx\n")
    else:
        print(f"❌ No se pudo generar una consulta válida después de {max_intentos} intentos. Intenta reformular.\n")