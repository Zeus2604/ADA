import pandas as pd

df = pd.read_csv('notebooks/BTC_All_graph_coinmarketcap.csv', sep=None, engine='python', encoding='utf-8-sig')

df.columns = ['timestamp', 'price', 'volume']
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp')

precio_inicial = df.iloc[0]['price']
precio_final = df.iloc[-1]['price']
fecha_inicial = df.iloc[0]['timestamp']
fecha_final = df.iloc[-1]['timestamp']

crecimiento_total = ((precio_final - precio_inicial) / precio_inicial) * 100
años_transcurridos = (fecha_final - fecha_inicial).days / 365.25

print(f"Fecha inicial: {fecha_inicial.date()} - Precio: ${precio_inicial:,.4f}")
print(f"Fecha final: {fecha_final.date()} - Precio: ${precio_final:,.2f}")
print(f"Crecimiento total: {crecimiento_total:,.0f}%")
print(f"Años transcurridos: {años_transcurridos:.1f}")

df.to_csv('notebooks/btc_limpio.csv', index=False)
print("\n✅ Archivo limpio guardado: notebooks/btc_limpio.csv")