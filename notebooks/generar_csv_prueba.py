import pandas as pd
import random

nombres = ["Andrés", "María", "Carlos", "Laura", "Juan", "Camila", "Diego", "Valentina"]
apellidos = ["Gómez", "Rodríguez", "Martínez", "López", "García", "Pérez"]
cargos = ["Analista", "Coordinador", "Gerente", "Auxiliar", "Director"]
areas = ["Ventas", "Finanzas", "Tecnología", "Recursos Humanos", "Operaciones"]

registros = []
for i in range(150):
    registros.append({
        "id_empleado": i + 1,
        "nombre_completo": f"{random.choice(nombres)} {random.choice(apellidos)}",
        "cargo": random.choice(cargos),
        "area": random.choice(areas),
        "salario_mensual": round(random.uniform(1500000, 12000000), 0),
        "años_experiencia": random.randint(0, 25)
    })

tabla = pd.DataFrame(registros)
tabla.to_csv('notebooks/empleados_prueba.csv', index=False)
print("Archivo CSV de prueba generado: notebooks/empleados_prueba.csv")
print(tabla.head())