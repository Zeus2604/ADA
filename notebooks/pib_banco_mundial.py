import requests
import pandas as pd

# Código de país: COL = Colombia. Puedes cambiarlo por MEX, USA, BRA, etc.
codigo_pais = "COL"

# Indicador NY.GDP.MKTP.KD.ZG = Crecimiento del PIB (% anual)
url = f"https://api.worldbank.org/v2/country/{codigo_pais}/indicator/NY.GDP.MKTP.KD.ZG?format=json&per_page=100"

respuesta = requests.get(url)
datos = respuesta.json()

# La API del Banco Mundial devuelve una lista con 2 partes: [metadata, datos_reales]
registros = datos[1]

# Convertimos a una tabla de pandas
tabla = pd.DataFrame([
    {"año": r["date"], "crecimiento_pib_%": r["value"]}
    for r in registros
])

# Ordenamos por año y quitamos filas sin dato
tabla = tabla.dropna()
tabla["año"] = tabla["año"].astype(int)
tabla = tabla.sort_values("año")

# Filtramos los últimos 10 años
ultimos_10 = tabla[tabla["año"] >= tabla["año"].max() - 9]

print(f"Crecimiento del PIB de {codigo_pais} - últimos 10 años:\n")
print(ultimos_10.to_string(index=False))

# Exportamos a Excel
ultimos_10.to_excel('notebooks/pib_colombia.xlsx', index=False)
print("\n✅ Exportado a: notebooks/pib_colombia.xlsx")