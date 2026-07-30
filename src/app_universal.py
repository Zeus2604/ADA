import streamlit as st
import ollama
import sqlite3
import pandas as pd
import subprocess
import time
import os
import re

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

def construir_contexto(df, nombre_tabla):
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
- Cuando uses GROUP BY, SIEMPRE incluye esa misma columna en el SELECT, para que el resultado sea legible (nunca hagas SELECT COUNT(*) solo, sin la columna de agrupación).
- Si la pregunta pide "el/la [algo] con mayor/menor [valor]" (ej. "el empleado con más experiencia"), usa SELECT * (todas las columnas), no solo una columna.

Ejemplo:
Pregunta: Cuántos registros hay
Respuesta: SELECT COUNT(*) FROM {nombre_tabla};

Ejemplo:
Pregunta: Ordena de mayor a menor por la primera columna numérica
Respuesta: SELECT * FROM {nombre_tabla} ORDER BY 1 DESC;
{ejemplos_dinamicos}"""
    return contexto

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

# ===== INTERFAZ VISUAL =====

st.set_page_config(page_title="ADA - Análisis Universal", page_icon="📁")
st.title("📁 ADA - Análisis Universal de Archivos")
st.write("Sube un archivo CSV o Excel y pregúntale lo que quieras, en lenguaje natural.")

archivo_subido = st.file_uploader("Sube tu archivo", type=["csv", "xlsx"])

if archivo_subido is not None:
    if archivo_subido.name.endswith('.csv'):
        df = pd.read_csv(archivo_subido)
    else:
        df = pd.read_excel(archivo_subido)

    st.write("Vista previa de los datos:")
    st.dataframe(df.head(), use_container_width=True)

    nombre_tabla = "datos_usuario"
    conexion = sqlite3.connect(':memory:')
    df.to_sql(nombre_tabla, conexion, index=False, if_exists='replace')

    contexto = construir_contexto(df, nombre_tabla)

    pregunta = st.text_input("Tu pregunta sobre este archivo:")

    if st.button("Consultar") and pregunta:
        intentos = 0
        max_intentos = 2
        sql = generar_sql(pregunta, contexto)
        resultado_final = None

        with st.spinner("ADA está pensando..."):
            while intentos < max_intentos:
                if not es_seguro(sql, nombre_tabla):
                    sql = generar_sql(pregunta, contexto, correccion={'sql_fallido': sql, 'error': f'la consulta no es un SELECT seguro sobre la tabla {nombre_tabla}'})
                    intentos += 1
                    continue
                sql = corregir_group_by(sql)
                try:
                    cursor = conexion.cursor()
                    cursor.execute(sql)
                    resultados = cursor.fetchall()
                    columnas = [descripcion[0] for descripcion in cursor.description]
                    resultado_final = (resultados, columnas)
                    break
                except sqlite3.OperationalError as e:
                    sql = generar_sql(pregunta, contexto, correccion={'sql_fallido': sql, 'error': str(e)})
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