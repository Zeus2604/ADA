import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("COINMARKETCAP_API_KEY")

url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/historical"
parametros = {
    "symbol": "BTC",
    "time_start": "2020-01-01",
    "time_end": "2020-01-10",
    "interval": "daily",
    "convert": "USD"
}
headers = {"X-CMC_PRO_API_KEY": api_key}

respuesta = requests.get(url, params=parametros, headers=headers)
datos = respuesta.json()

print(datos)