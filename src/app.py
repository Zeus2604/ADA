import streamlit as st
import ollama
import sqlite3
import pandas as pd
import subprocess
import time
import csv
import os
from datetime import datetime

def asegurar_ollama_activo():
    try:
        ollama.list()
    except Exception:
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for segundos in range(15):
            time.sleep(1)
            try:
                ollama.list()
                return
            except Exception:
                continue

asegurar_ollama_activo()

def guardar_historial(pregunta, sql, exitoso):
    archivo_historial = 'notebooks/historial.csv'
    existe = os.path.exists(archivo_historial)
    with open(archivo_historial, mode='a', newline='', encoding='utf-8') as archivo:
        escritor = csv.writer(archivo)
        if not existe:
            escritor.writerow(['fecha_hora', 'pregunta', 'sql_generado', 'exitoso'])
        escritor.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), pregunta, sql, exitoso])

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

Ejemplo:
Pregunta: Cuántos clientes tiene cada estado de mora
Respuesta: SELECT estado_mora, COUNT(*) FROM clientes GROUP BY estado_mora;

Ejemplo:
Pregunta: Cuántos clientes están al día
Respuesta: SELECT COUNT(*) FROM clientes WHERE estado_mora = 'Al día';

Ejemplo:
Pregunta: Muéstrame la distribución de clientes por estado de mora
Respuesta: SELECT estado_mora, COUNT(*) FROM clientes GROUP BY estado_mora;
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

# ===== INTERFAZ VISUAL =====

st.set_page_config(page_title="ADA - Almar Data Analysis", page_icon="📊")
st.title("📊 ADA - Almar Data Analysis")
st.write("Escribe tu pregunta sobre los clientes en lenguaje natural.")

pregunta = st.text_input("Tu pregunta:")

if st.button("Consultar") and pregunta:
    intentos = 0
    max_intentos = 2
    sql = generar_sql(pregunta)
    resultado_final = None

    with st.spinner("ADA está pensando..."):
        while intentos < max_intentos:
            if not es_seguro(sql):
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
                sql = generar_sql(pregunta, correccion={'sql_fallido': sql, 'error': str(e)})
                intentos += 1

    st.code(sql, language="sql")

    if resultado_final:
        resultados, columnas = resultado_final
        tabla_resultado = pd.DataFrame(resultados, columns=columnas)
        st.success("Resultado:")
        st.dataframe(tabla_resultado, use_container_width=True)
        guardar_historial(pregunta, sql, True)
    else:
        st.error(f"No se pudo generar una consulta válida después de {max_intentos} intentos.")
        guardar_historial(pregunta, sql, False)