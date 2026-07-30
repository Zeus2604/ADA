import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("COINMARKETCAP_API_KEY")

url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
parametros = {"symbol": "BTC", "convert": "USD"}
headers = {"X-CMC_PRO_API_KEY": api_key}

respuesta = requests.get(url, params=parametros, headers=headers)
datos = respuesta.json()

precio = datos["data"]["BTC"]["quote"]["USD"]["price"]
cambio_24h = datos["data"]["BTC"]["quote"]["USD"]["percent_change_24h"]

print(f"Precio actual de Bitcoin: ${precio:,.2f} USD")
print(f"Cambio en las últimas 24h: {cambio_24h:.2f}%")