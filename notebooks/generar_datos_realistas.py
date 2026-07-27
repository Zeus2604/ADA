import sqlite3
import random
from datetime import datetime, timedelta

# Listas de valores realistas para generar datos aleatorios
nombres = ["Andrés", "María", "Carlos", "Laura", "Juan", "Camila", "Diego", "Valentina",
           "Santiago", "Isabella", "Felipe", "Sofía", "Miguel", "Daniela", "Alejandro"]
apellidos = ["Gómez", "Rodríguez", "Martínez", "López", "García", "Pérez", "Sánchez",
             "Ramírez", "Torres", "Flórez", "Díaz", "Vargas", "Castro", "Ortiz"]
ciudades = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena", "Bucaramanga",
            "Pereira", "Manizales", "Cúcuta", "Ibagué"]
productos = ["Cuenta Ahorros", "Cuenta Corriente", "CDT", "Crédito de Consumo", "Crédito Hipotecario"]
estados_mora = ["Al día", "Mora temprana", "Mora avanzada"]
# Ponderamos para que la mayoría esté "Al día" (más realista)
pesos_mora = [0.75, 0.18, 0.07]
segmentos = ["Persona Natural", "Pyme", "Empresarial"]
pesos_segmento = [0.70, 0.22, 0.08]

conexion = sqlite3.connect('notebooks/ejemplo.db')
cursor = conexion.cursor()

# Recreamos la tabla con las nuevas columnas
cursor.execute('DROP TABLE IF EXISTS clientes')
cursor.execute('''
CREATE TABLE clientes (
    id INTEGER PRIMARY KEY,
    nombre TEXT,
    ciudad TEXT,
    saldo REAL,
    producto TEXT,
    fecha_vinculacion TEXT,
    estado_mora TEXT,
    segmento TEXT
)
''')

fecha_inicio = datetime(2018, 1, 1)
fecha_fin = datetime(2026, 1, 1)
rango_dias = (fecha_fin - fecha_inicio).days

registros = []
for i in range(200):
    nombre_completo = f"{random.choice(nombres)} {random.choice(apellidos)}"
    ciudad = random.choice(ciudades)
    saldo = round(random.uniform(50000, 15000000), 2)
    producto = random.choice(productos)
    fecha = fecha_inicio + timedelta(days=random.randint(0, rango_dias))
    estado = random.choices(estados_mora, weights=pesos_mora)[0]
    segmento = random.choices(segmentos, weights=pesos_segmento)[0]

    registros.append((nombre_completo, ciudad, saldo, producto, fecha.strftime('%Y-%m-%d'), estado, segmento))

cursor.executemany('''
INSERT INTO clientes (nombre, ciudad, saldo, producto, fecha_vinculacion, estado_mora, segmento)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', registros)

conexion.commit()
conexion.close()

print(f"Se generaron {len(registros)} registros ficticios con éxito.")
print("Base de datos actualizada: notebooks/ejemplo.db")