# Datos de saldo de los clientes (los mismos de nuestra base de datos)
saldos <- c(1500000, 2300000, 980000)
ciudades <- c("Bogotá", "Medellín", "Cali")

# Estadística descriptiva básica
cat("Promedio de saldo:", mean(saldos), "\n")
cat("Saldo máximo:", max(saldos), "\n")
cat("Saldo mínimo:", min(saldos), "\n")
cat("Desviación estándar:", sd(saldos), "\n")
cat("Suma total:", sum(saldos), "\n")

# Tabla resumen
resumen <- data.frame(ciudad = ciudades, saldo = saldos)
print(resumen)