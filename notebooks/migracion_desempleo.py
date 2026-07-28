import requests
import pandas as pd

codigo_pais = "COL"

def obtener_indicador(indicador, nombre_columna):
    url = f"https://api.worldbank.org/v2/country/{codigo_pais}/indicator/{indicador}?format=json&per_page=100"
    respuesta = requests.get(url)
    datos = respuesta.json()
    registros = datos[1]

    tabla = pd.DataFrame([
        {"año": r["date"], nombre_columna: r["value"]}
        for r in registros
    ])
    tabla = tabla.dropna()
    tabla["año"] = tabla["año"].astype(int)
    return tabla

# Migración neta (cada varios años, dato estructural)
migracion = obtener_indicador("SM.POP.NETM", "migracion_neta")

# Tasa de desempleo (% de la fuerza laboral, anual)
desempleo = obtener_indicador("SL.UEM.TOTL.ZS", "tasa_desempleo_%")

# Unimos ambas tablas por año (solo donde coinciden ambos datos)
combinado = pd.merge(migracion, desempleo, on="año", how="outer").sort_values("año")

print("=== Migración neta y tasa de desempleo en Colombia ===\n")
print(combinado.to_string(index=False))

combinado.to_excel('notebooks/migracion_desempleo.xlsx', index=False)
print("\n✅ Exportado a: notebooks/migracion_desempleo.xlsx")