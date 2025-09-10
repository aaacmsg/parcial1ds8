import random
import time
from datetime import datetime

# ---------------------------
# Constantes
# ---------------------------
CANTIDAD_PLAZAS = 25
PRECIO_POR_SEGUNDO = 0.03
SPOTS_POR_FILA = 5

# ---------------------------
# Inicializar "tablas"
# ---------------------------
parkingspots = [(i, False) for i in range(1, CANTIDAD_PLAZAS + 1)]
coches = []  # historial completo
autos_a_asignar = []  # autos que entran y esperan para asignar plaza
contador_coches = 1

# ---------------------------
# Funciones auxiliares
# ---------------------------
def generar_auto_aleatorio():
    """Genera un auto aleatorio que entra al sistema"""
    global contador_coches
    modelos = ["Toyota", "Honda", "Ford", "Chevy", "BMW", "Mercedes"]
    colores = ["Rojo", "Azul", "Verde", "Negro", "Blanco", "Amarillo"]
    matricula = f"{random.randint(100,999)}-{random.randint(1000,9999)}"
    ahora = datetime.now()
    auto = [contador_coches, matricula, ahora, "entrando",
            random.choice(modelos), random.choice(colores), random.randint(2000,2025),
            None, 0.0, 0.0, ahora]  # el último campo es timestamp_entrada_real
    contador_coches += 1
    return auto

def generar_auto_manual():
    """Permite al usuario ingresar un auto manualmente"""
    global contador_coches
    print("\n--- Ingreso manual de auto ---")
    matricula = input("Ingrese matrícula: ")
    modelo = input("Ingrese modelo: ")
    color = input("Ingrese color: ")
    while True:
        try:
            anio = int(input("Ingrese año: "))
            break
        except ValueError:
            print("Año inválido, intente de nuevo.")
    ahora = datetime.now()
    auto = [contador_coches, matricula, ahora, "entrando",
            modelo, color, anio, None, 0.0, 0.0, ahora]
    contador_coches += 1
    return auto

def asignar_plazas():
    """Convierte los autos en autos_a_asignar a 'estacionado' si hay plazas libres,
       o a 'saliendo' si no hay plazas"""
    global autos_a_asignar, coches, parkingspots
    if not autos_a_asignar:
        return
    plazas_libres = [i for i, ocupada in parkingspots if not ocupada]
    for auto in autos_a_asignar:
        if plazas_libres:
            index_plaza = random.randint(0, len(plazas_libres)-1)
            plaza = plazas_libres.pop(index_plaza)
            parkingspots[plaza-1] = (plaza, True)
            auto[3] = "estacionado"
            auto[7] = plaza
        else:
            auto[3] = "saliendo"
        coches.append(auto)
    autos_a_asignar = []  # ya procesados

def elegir_auto_para_salir():
    """Selecciona un auto aleatorio que esté estacionado para cambiarlo a 'saliendo'"""
    estacionados = [auto for auto in coches if auto[3] == "estacionado"]
    if estacionados:
        auto = random.choice(estacionados)
        auto[3] = "saliendo"

def procesar_salida():
    """Convierte los autos 'saliendo' en 'ha_salido' y libera la plaza"""
    for auto in coches:
        if auto[3] == "saliendo":
            plaza = auto[7]
            if plaza:
                parkingspots[plaza-1] = (plaza, False)
            # calcular tiempo y costo usando timestamp de entrada real
            timestamp_entrada = auto[10]
            ahora = datetime.now()
            tiempo_total = (ahora - timestamp_entrada).total_seconds()
            costo_total = round(tiempo_total * PRECIO_POR_SEGUNDO, 2)
            auto[3] = "ha_salido"
            auto[7] = None
            auto[8] = tiempo_total
            auto[9] = costo_total

def contar_estados():
    estados = ["entrando","estacionado","saliendo"]
    conteos = {e: 0 for e in estados}
    for auto in coches + autos_a_asignar:
        if auto[3] in conteos:
            conteos[auto[3]] += 1
    return conteos

def porcentaje_ocupacion():
    ocupadas = sum(1 for s in parkingspots if s[1])
    return ocupadas / CANTIDAD_PLAZAS * 100

def estado_ocupacion():
    perc = porcentaje_ocupacion()
    if perc == 100:
        return "LLENO"
    elif perc < 50:
        return "DISPONIBLE"
    else:
        return "MEDIO LLENO"

def mostrar_matriz_plazas():
    for i, (plaza, ocupada) in enumerate(parkingspots):
        color = "🟦" if ocupada else "⬜"
        print(color, end=" ")
        if (i+1) % SPOTS_POR_FILA == 0:
            print()
    print()

def mostrar_coches_por_estado():
    estados = ["entrando","estacionado","saliendo","ha_salido"]
    for e in estados:
        print(f"\n--- {e.upper()} ---")
        for auto in coches + autos_a_asignar:
            if auto[3] == e:
                tiempo = f"{auto[8]:.2f}s" if auto[3]=="ha_salido" else "-"
                costo = f"${auto[9]:.2f}" if auto[3]=="ha_salido" else "-"
                print(f"{auto[1]} | {auto[4]} {auto[5]} {auto[6]} | Plaza: {auto[7]} | Hora: {auto[2].strftime('%H:%M:%S')} | Tiempo: {tiempo} | Pago: {costo}")

# ---------------------------
# Bucle principal
# ---------------------------
def bucle_principal():
    print("=== Simulador de Estacionamiento ===")
    print("Opciones: [p]ause, [c]ontinue, [i]ngresar auto manual")
    print("Presiona Ctrl+C para detener.\n")
    while True:
        # Entrada del usuario antes de cada ciclo
        accion = input("Ingrese acción (p/c/i): ").lower()
        if accion == "p":
            input("Simulación pausada. Presione Enter para continuar...")
        elif accion == "i":
            auto = generar_auto_manual()
            autos_a_asignar.append(auto)
            print(f"Auto {auto[1]} agregado como 'entrando'.")
        # continuar normalmente si es 'c' o cualquier otra tecla

        # Primero procesamos cambios de ciclos anteriores
        asignar_plazas()
        procesar_salida()

        # Decidir si entran nuevos autos o salen
        estacionados = [c for c in coches if c[3]=="estacionado"]
        eleccion = random.choice([0,1])
        if eleccion == 0 or not estacionados:
            # Se generan nuevos autos que quedan en "entrando" y esperan próximo ciclo
            for _ in range(random.randint(1,3)):
                autos_a_asignar.append(generar_auto_aleatorio())
        else:
            # Solo autos que estaban estacionados pueden salir
            elegir_auto_para_salir()

        # Mostrar información
        print("\n" + "="*60)
        mostrar_matriz_plazas()
        conteos = contar_estados()
        print(f"Ocupación: {porcentaje_ocupacion():.1f}% | Estado: {estado_ocupacion()}")
        print(f"Entrando: {conteos['entrando']} | Estacionados: {conteos['estacionado']} | Saliendo: {conteos['saliendo']}")
        mostrar_coches_por_estado()
        print("="*60 + "\n")
        time.sleep(5)

if __name__ == "__main__":
    bucle_principal()
