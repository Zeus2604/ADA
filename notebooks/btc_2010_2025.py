import pandas as pd

df = pd.read_csv('notebooks/btc_limpio.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

precio_inicial = df.iloc[0]['price']
fecha_inicial = df.iloc[0]['timestamp']

# Buscamos el dato real más cercano al 31 de diciembre de 2025
objetivo = pd.Timestamp('2025-12-31')
df['diferencia'] = (df['timestamp'] - objetivo).abs()
fila_cercana = df.loc[df['diferencia'].idxmin()]

precio_2025 = fila_cercana['price']
fecha_real_2025 = fila_cercana['timestamp']

crecimiento = ((precio_2025 - precio_inicial) / precio_inicial) * 100
inversion_final = 100 * (precio_2025 / precio_inicial)

print(f"Precio inicial ({fecha_inicial.date()}): ${precio_inicial:,.4f}")
print(f"Precio más cercano a fin de 2025 ({fecha_real_2025.date()}): ${precio_2025:,.2f}")
print(f"Crecimiento 2010-2025: {crecimiento:,.0f}%")
print(f"$100 USD invertidos se habrían convertido en: ${inversion_final:,.2f}")