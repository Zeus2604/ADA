import streamlit as st
import ollama
import sqlite3
import pandas as pd
import subprocess
import time
import csv
import os
import re
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

def generar_sql(pregunta, contexto, correccion=None):
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

def es_seguro(sql, nombre_tabla):
    sql_minusculas = sql.lower()
    return (
        f'from {nombre_tabla.lower()}' in sql_minusculas and
        sql_minusculas.startswith('select') and
        'drop' not in sql_minusculas and
        'delete' not in sql_minusculas and
        'update' not in sql_minusculas and
        'insert' not in sql_minusculas
    )

def corregir_group_by(sql):
    match = re.search(r'group by\s+([a-zA-Z_][a-zA-Z0-9_]*)', sql, re.IGNORECASE)
    if match:
        columna_group = match.group(1)
        select_match = re.search(r'select\s+(.*?)\s+from', sql, re.IGNORECASE)
        if select_match:
            select_clause = select_match.group(1)
            if columna_group.lower() not in select_clause.lower():
                nuevo_select = f"{columna_group}, {select_clause}"
                sql = sql.replace(f"SELECT {select_clause}", f"SELECT {nuevo_select}", 1)
                sql = sql.replace(f"select {select_clause}", f"select {nuevo_select}", 1)
    return sql
contexto_clientes = """Eres un generador de SQL. Tu única función es convertir preguntas en español a consultas SQL.

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

Ejemplo:
Pregunta: Dame los 5 clientes con mayor saldo
Respuesta: SELECT * FROM clientes ORDER BY saldo DESC LIMIT 5;

Ejemplo:
Pregunta: Cuáles son los 3 clientes con menor saldo
Respuesta: SELECT * FROM clientes ORDER BY saldo ASC LIMIT 3;

Ejemplo:
Pregunta: Muéstrame los 10 clientes más antiguos
Respuesta: SELECT * FROM clientes ORDER BY fecha_vinculacion ASC LIMIT 10;
"""
def construir_contexto_universal(df, nombre_tabla):
    columnas_info = []
    columna_texto_ejemplo = None
    columna_numero_ejemplo = None

    for col in df.columns:
        tipo = str(df[col].dtype)
        if tipo.startswith('int') or tipo.startswith('float'):
            tipo_legible = "número"
            if columna_numero_ejemplo is None:
                columna_numero_ejemplo = col
        else:
            tipo_legible = "texto"
            if columna_texto_ejemplo is None:
                columna_texto_ejemplo = col
        columnas_info.append(f"- {col} ({tipo_legible})")

    columnas_texto = "\n".join(columnas_info)

    ejemplos_dinamicos = ""
    if columna_texto_ejemplo and columna_numero_ejemplo:
        ejemplos_dinamicos = f"""
Ejemplo:
Pregunta: Cuál es el promedio de {columna_numero_ejemplo} por {columna_texto_ejemplo}
Respuesta: SELECT {columna_texto_ejemplo}, AVG({columna_numero_ejemplo}) FROM {nombre_tabla} GROUP BY {columna_texto_ejemplo};

Ejemplo:
Pregunta: Cuántos registros hay por {columna_texto_ejemplo}
Respuesta: SELECT {columna_texto_ejemplo}, COUNT(*) FROM {nombre_tabla} GROUP BY {columna_texto_ejemplo};

Ejemplo:
Pregunta: Cuál es el total de {columna_numero_ejemplo} agrupado por {columna_texto_ejemplo}
Respuesta: SELECT {columna_texto_ejemplo}, SUM({columna_numero_ejemplo}) FROM {nombre_tabla} GROUP BY {columna_texto_ejemplo};
"""

    contexto = f"""Eres un generador de SQL. Tu única función es convertir preguntas en español a consultas SQL.

Tabla disponible: {nombre_tabla}
Columnas:
{columnas_texto}

Reglas:
- Responde SOLO con la consulta SQL, en una sola línea.
- No agregues explicaciones, ni texto antes o después.
- No agregues comillas ni la palabra "sql".
- Siempre incluye la cláusula FROM {nombre_tabla}.
- Si la pregunta menciona "por" alguna categoría (ej. "por ciudad", "por área"), usa GROUP BY con esa columna, nunca WHERE.
- Cuando uses GROUP BY, SIEMPRE incluye esa misma columna en el SELECT, para que el resultado sea legible.
- Si la pregunta pide "el/la [algo] con mayor/menor [valor]", usa SELECT * (todas las columnas), no solo una columna.

Ejemplo:
Pregunta: Cuántos registros hay
Respuesta: SELECT COUNT(*) FROM {nombre_tabla};

Ejemplo:
Pregunta: Ordena de mayor a menor por la primera columna numérica
Respuesta: SELECT * FROM {nombre_tabla} ORDER BY 1 DESC;
{ejemplos_dinamicos}"""
    return contexto
# ===== INTERFAZ VISUAL =====

st.set_page_config(page_title="ADA - Almar Data Analysis", page_icon="📊", layout="wide")
st.title("📊 ADA - Almar Data Analysis")

tab1, tab2 = st.tabs(["🏠 Clientes (base fija)", "📁 Subir archivo nuevo"])

with tab1:
    st.write("Pregunta sobre la base de datos de clientes ya cargada.")
    pregunta1 = st.text_input("Tu pregunta:", key="pregunta_clientes")

    if st.button("Consultar", key="boton_clientes") and pregunta1:
        intentos = 0
        max_intentos = 2
        sql = generar_sql(pregunta1, contexto_clientes)
        resultado_final = None

        with st.spinner("ADA está pensando..."):
            while intentos < max_intentos:
                if not es_seguro(sql, "clientes"):
                    sql = generar_sql(pregunta1, contexto_clientes, correccion={'sql_fallido': sql, 'error': 'la consulta no es un SELECT seguro sobre la tabla clientes'})
                    intentos += 1
                    continue

                sql = corregir_group_by(sql)
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
                    sql = generar_sql(pregunta1, contexto_clientes, correccion={'sql_fallido': sql, 'error': str(e)})
                    intentos += 1

        st.code(sql, language="sql")

        if resultado_final:
            resultados, columnas = resultado_final
            tabla_resultado = pd.DataFrame(resultados, columns=columnas)
            st.success("Resultado:")
            st.dataframe(tabla_resultado, use_container_width=True)
            guardar_historial(pregunta1, sql, True)
        else:
            st.error(f"No se pudo generar una consulta válida después de {max_intentos} intentos.")
            guardar_historial(pregunta1, sql, False)

with tab2:
    st.write("Sube un archivo CSV o Excel y pregúntale lo que quieras.")
    archivo_subido = st.file_uploader("Sube tu archivo", type=["csv", "xlsx"])

    if archivo_subido is not None:
        if archivo_subido.name.endswith('.csv'):
            df = pd.read_csv(archivo_subido)
        else:
            df = pd.read_excel(archivo_subido)

        st.write("Vista previa de los datos:")
        st.dataframe(df.head(), use_container_width=True)

        nombre_tabla = "datos_usuario"
        conexion_universal = sqlite3.connect(':memory:')
        df.to_sql(nombre_tabla, conexion_universal, index=False, if_exists='replace')

        contexto_universal = construir_contexto_universal(df, nombre_tabla)

        pregunta2 = st.text_input("Tu pregunta sobre este archivo:", key="pregunta_universal")

        if st.button("Consultar", key="boton_universal") and pregunta2:
            intentos = 0
            max_intentos = 2
            sql = generar_sql(pregunta2, contexto_universal)
            resultado_final = None

            with st.spinner("ADA está pensando..."):
                while intentos < max_intentos:
                    if not es_seguro(sql, nombre_tabla):
                        sql = generar_sql(pregunta2, contexto_universal, correccion={'sql_fallido': sql, 'error': f'la consulta no es un SELECT seguro sobre la tabla {nombre_tabla}'})
                        intentos += 1
                        continue

                    sql = corregir_group_by(sql)
                    try:
                        cursor = conexion_universal.cursor()
                        cursor.execute(sql)
                        resultados = cursor.fetchall()
                        columnas = [descripcion[0] for descripcion in cursor.description]
                        resultado_final = (resultados, columnas)
                        break
                    except sqlite3.OperationalError as e:
                        sql = generar_sql(pregunta2, contexto_universal, correccion={'sql_fallido': sql, 'error': str(e)})
                        intentos += 1

            st.code(sql, language="sql")

            if resultado_final:
                resultados, columnas = resultado_final
                tabla_resultado = pd.DataFrame(resultados, columns=columnas)
                st.success("Resultado:")
                st.dataframe(tabla_resultado, use_container_width=True)
            else:
                st.error(f"No se pudo generar una consulta válida después de {max_intentos} intentos.")
    else:
        st.info("Sube un archivo para comenzar.")