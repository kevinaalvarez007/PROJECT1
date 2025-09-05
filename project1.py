# -*- coding: utf-8 -*-
"""
Created on Thu Sep  4 12:38:28 2025

@author: andre
"""

import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

# ================================
# FUNCIONES AUXILIARES
# ================================

def solar_position(lat, lon, fecha, horas):
    """
    Calcula la posición solar (altura y azimut) a lo largo del día.
    - lat: latitud del lugar en grados
    - lon: longitud del lugar en grados
    - fecha: string con la fecha (YYYY-MM-DD)
    - horas: vector con las horas decimales (ej: 5.5 = 5:30 a.m.)
    Retorna:
    - alt: altura solar en radianes
    - az: azimut solar en radianes
    """
    # Día del año (1–365)
    n = datetime.fromisoformat(fecha).timetuple().tm_yday
    
    # Declinación solar (ángulo de inclinación de la Tierra respecto al sol)
    dec = np.radians(23.45 * np.sin(np.deg2rad((360/365) * (284 + n))))
    
    # Convertimos latitud a radianes
    lat = np.radians(lat)

    # Tiempo solar local aproximado
    lst = horas - 1 + lon/15   # ajusta por longitud (15° = 1 hora)

    # Ángulo horario (diferencia en tiempo respecto al mediodía solar)
    hra = np.radians(15*(lst-12))

    # Altura solar (ángulo sobre el horizonte)
    alt = np.arcsin(np.sin(dec)*np.sin(lat) +
                    np.cos(dec)*np.cos(lat)*np.cos(hra))

    # Azimut solar (posición en el horizonte)
    az = np.arccos((np.sin(dec)*np.cos(lat) -
                    np.cos(dec)*np.sin(lat)*np.cos(hra)) / np.cos(alt))
    az = np.where(hra > 0, 2*np.pi - az, az)  # corrige orientación (este/oeste)

    return alt, az


def irradiancia_panel(alt, az, inc, az_panel):
    """
    Calcula la irradiancia que recibe un panel inclinado.
    - alt: altura solar
    - az: azimut solar
    - inc: inclinación del panel respecto al suelo
    - az_panel: orientación del panel (azimut)
    Retorna:
    - Irradiancia en kW/m²
    """

    # Inicializamos irradiancia en cero
    s_inc = np.zeros_like(alt)
    
    # Consideramos solo cuando el sol está sobre el horizonte
    mask = alt > 0
    
    # Modelo  de irradiancia (evitara errores cuando alt <= 0)
    s_inc[mask] = 1.4883 * 0.7**(np.sin(alt[mask])**-0.678)

    # Cálculo del ángulo entre el sol y la superficie del panel
    cos_theta = (np.sin(alt)*np.cos(np.radians(inc)) +
                 np.cos(alt)*np.sin(np.radians(inc))*np.cos(az - np.radians(az_panel)))
    
    # Se recorta a valores físicos válidos [0, 1]
    cos_theta = np.clip(cos_theta, 0, 1)

    return s_inc * cos_theta


def produccion_panel(s_tilt, area=1.6, eff=0.18):
    """
    Calcula la potencia que produce un panel.
    - s_tilt: irradiancia sobre el panel
    - area: área del panel (m²)
    - eff: eficiencia del panel
    Retorna:
    - Potencia producida en W
    """
    return 1000 * s_tilt * area * eff   # 1000 convierte de kW a W


# ================================
# ENTRADAS DEL USUARIO
# ================================
lat = float(input("Ingrese la latitud (°): "))
lon = float(input("Ingrese la longitud (°): "))
fecha = input("Ingrese la fecha (YYYY-MM-DD): ")
inc = float(input("Ingrese la inclinación del panel (°): "))
az_panel = float(input("Ingrese el azimut del panel (0° = Sur, 90° = Este, 180° = Norte, 270° = Oeste.): "))

# Vector de horas (desde las 5:30 a.m. hasta las 8:00 p.m. cada 15 min)
horas = np.arange(5.5, 20.25, 0.25)


# ================================
# CÁLCULOS PRINCIPALES
# ================================
# Posición del sol
alt, az = solar_position(lat, lon, fecha, horas)

# Irradiancia recibida en el panel
s_tilt = irradiancia_panel(alt, az, inc, az_panel)

# Producción del panel en W
production = produccion_panel(s_tilt)

# Eliminar valores negativos durante la noche
production[alt <= 0] = 0

# Energía diaria (Wh), área bajo la curva de potencia
energia_diaria = np.trapezoid(production, horas)
print(f"\nEnergía diaria estimada: {energia_diaria:.2f} Wh")


# ================================
# GRÁFICAS DE RESULTADOS
# ================================
fig, axs = plt.subplots(2, 2, figsize=(14, 8))

# Gráfico 1: Altura solar
axs[0,0].plot(horas, np.degrees(alt), "orange")
axs[0,0].set_title("Altura solar")
axs[0,0].set_xlabel("Hora [h]"); axs[0,0].set_ylabel("Altura [°]"); axs[0,0].grid()

# Gráfico 2: Azimut solar
axs[0,1].plot(horas, np.degrees(az), "blue")
axs[0,1].set_title("Azimut solar")
axs[0,1].set_xlabel("Hora [h]"); axs[0,1].set_ylabel("Azimut [°]"); axs[0,1].grid()

# Gráfico 3: Irradiancia en panel inclinado
axs[1,0].plot(horas, s_tilt, "red")
axs[1,0].fill_between(horas, s_tilt, color="red", alpha=0.3)
axs[1,0].set_title("Irradiancia en panel inclinado")
axs[1,0].set_xlabel("Hora [h]"); axs[1,0].set_ylabel("Irradiancia [kW/m²]"); axs[1,0].grid()

# Gráfico 4: Producción del panel
axs[1,1].plot(horas, production, "green")
axs[1,1].fill_between(horas, production, color="green", alpha=0.3)
axs[1,1].set_title("Producción estimada del panel")
axs[1,1].set_xlabel("Hora [h]"); axs[1,1].set_ylabel("Potencia [W]"); axs[1,1].grid()

# Ajusta el diseño
plt.tight_layout(); plt.show()
# LECTURA Y GRÁFICA DE ARCHIVO CSV
# Cargar datos externos 
df = pd.read_csv("datos.csv", sep=";")

# Convertir la columna de tiempo a formato datetime
df["Timestamp"] = pd.to_datetime(df["Timestamp"], dayfirst=True, errors="coerce")

# Reemplazar comas por puntos 
for col in ["AH3", "LSParking"]:
    df[col] = (
        df[col]
        .astype(str)              # convertir a texto
        .str.replace(",", ".")    # cambiar coma por punto
    )
    df[col] = pd.to_numeric(df[col], errors="coerce")  # convertir a número

# ================================
# Gráfica de datos del archivo
# ================================
plt.figure(figsize=(12, 5))

plt.plot(df["Timestamp"], df["AH3"], label="AH3", color="purple")
plt.plot(df["Timestamp"], df["LSParking"], label="LSParking", color="teal")

plt.title("Datos del archivo CSV")
plt.xlabel("Tiempo")
plt.ylabel("Valor medido")
plt.legend()
plt.grid(True)
plt.xticks(rotation=30)
plt.tight_layout()

plt.show()
