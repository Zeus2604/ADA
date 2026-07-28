library(readxl)

# Leemos el Excel que generamos con Python
datos <- read_excel("notebooks/migracion_desempleo.xlsx")

# Nos quedamos solo con los años donde tenemos AMBOS datos (sin NA)
datos_completos <- na.omit(datos)

cat("Años analizados:", nrow(datos_completos), "\n")
cat("Rango de años:", min(datos_completos$año), "-", max(datos_completos$año), "\n\n")

# Correlación de Pearson entre migración neta y tasa de desempleo
correlacion <- cor(datos_completos$migracion_neta, datos_completos$`tasa_desempleo_%`)

cat("Correlación entre migración neta y desempleo:", round(correlacion, 3), "\n\n")

# Interpretación automática de la fuerza de la correlación
if (abs(correlacion) < 0.3) {
  cat("Interpretación: Correlación débil o inexistente.\n")
} else if (abs(correlacion) < 0.6) {
  cat("Interpretación: Correlación moderada.\n")
} else {
  cat("Interpretación: Correlación fuerte.\n")
}

if (correlacion > 0) {
  cat("Dirección: Positiva (cuando una sube, la otra tiende a subir también).\n")
} else {
  cat("Dirección: Negativa (cuando una sube, la otra tiende a bajar).\n")
}