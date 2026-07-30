import pandas as pd

df = pd.read_csv('notebooks/btc_limpio.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['año'] = df['timestamp'].dt.year

# Para cada año, tomamos el precio de la fecha MÁS RECIENTE de ese año (cierre anual)
resumen = df.sort_values('timestamp').groupby('año').last().reset_index()
resumen = resumen[['año', 'timestamp', 'price']]
resumen.columns = ['año', 'fecha_cierre', 'precio_cierre']

print(resumen.to_string(index=False))

resumen.to_excel('notebooks/btc_resumen_anual.xlsx', index=False)
print("\n✅ Exportado a: notebooks/btc_resumen_anual.xlsx")