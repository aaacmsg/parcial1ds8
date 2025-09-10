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

# Diccionario para buscar autos por matrícula
autos_por_matricula = {}

# ---------------------------
# Funciones auxiliares
# ---------------------------
def generar_auto_aleatorio():
    global contador_coches
    modelos = ["Toyota", "Honda", "Ford", "Chevy", "BMW", "Mercedes"]
    colores = ["Rojo", "Azul", "Verde", "Negro", "Blanco", "Amarillo"]
    matricula = f"{random.randint(100,999)}-{random.randint(1000,9999)}"
    ahora = datetime.now()
    auto = [contador_coches, matricula, ahora, "entrando",
            random.choice(modelos), random.choice(colores), random.randint(2000,2025),
            None, 0.0, 0.0, ahora]
    contador_coches += 1
    return auto

def generar_auto_manual():
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
        autos_por_matricula[auto[1]] = auto
    autos_a_asignar = []

def elegir_auto_para_salir():
    estacionados = [auto for auto in coches if auto[3] == "estacionado"]
    if estacionados:
        auto = random.choice(estacionados)
        auto[3] = "saliendo"

def procesar_salida():
    for auto in coches:
        if auto[3] == "saliendo":
            plaza = auto[7]
            if plaza:
                parkingspots[plaza-1] = (plaza, False)
            timestamp_entrada = auto[10]
            ahora = datetime.now()
            tiempo_total = (ahora - timestamp_entrada).total_seconds()
            costo_total = round(tiempo_total * PRECIO_POR_SEGUNDO, 2)
            auto[3] = "ha_salido"
            auto[7] = None
            auto[8] = tiempo_total
            auto[9] = costo_total
            autos_por_matricula[auto[1]] = auto

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

def mostrar_coches_filtrados(filtro=None):
    """Muestra autos, filtrando por matrícula si se indica"""
    autos = coches + autos_a_asignar
    if filtro:
        autos = [auto for auto in autos if auto[1] == filtro]
    if not autos:
        print("No hay autos para mostrar.")
        return
    for auto in autos:
        tiempo = f"{auto[8]:.2f}s" if auto[3]=="ha_salido" else "-"
        costo = f"${auto[9]:.2f}" if auto[3]=="ha_salido" else "-"
        print(f"{auto[1]} | {auto[4]} {auto[5]} {auto[6]} | Plaza: {auto[7]} | Estado: {auto[3]} | Hora: {auto[2].strftime('%H:%M:%S')} | Tiempo: {tiempo} | Pago: {costo}")

def mostrar_coches_por_estado():
    estados = ["entrando","estacionado","saliendo","ha_salido"]
    for e in estados:
        print(f"\n--- {e.upper()} ---")
        mostrar_coches_filtrados_por_estado(e)

def mostrar_coches_filtrados_por_estado(estado):
    autos = [auto for auto in coches + autos_a_asignar if auto[3]==estado]
    for auto in autos:
        tiempo = f"{auto[8]:.2f}s" if estado=="ha_salido" else "-"
        costo = f"${auto[9]:.2f}" if estado=="ha_salido" else "-"
        print(f"{auto[1]} | {auto[4]} {auto[5]} {auto[6]} | Plaza: {auto[7]} | Hora: {auto[2].strftime('%H:%M:%S')} | Tiempo: {tiempo} | Pago: {costo}")

# ---------------------------
# Bucle principal
# ---------------------------
def bucle_principal():
    print("=== Simulador de Estacionamiento ===")
    print("Opciones: [p]ause, [c]ontinue, [i]ngresar auto manual, [m]ostrar autos")
    print("Presiona Ctrl+C para detener.\n")

    while True:
        accion = input("Ingrese acción (p/c/i/m): ").lower()
        if accion == "p":
            input("Simulación pausada. Presione Enter para continuar...")
        elif accion == "i":
            auto = generar_auto_manual()
            autos_a_asignar.append(auto)
            autos_por_matricula[auto[1]] = auto
            print(f"Auto {auto[1]} agregado como 'entrando'.")
        elif accion == "m":
            buscar = input("Ingrese matrícula o 'todos' para mostrar todos: ").strip()
            if buscar.lower() == "todos":
                mostrar_coches_filtrados()
            else:
                mostrar_coches_filtrados(buscar)

        # Procesar autos
        asignar_plazas()
        procesar_salida()

        # Decidir si entran nuevos autos o salen
        estacionados = [c for c in coches if c[3]=="estacionado"]
        eleccion = random.choice([0,1])
        if eleccion == 0 or not estacionados:
            for _ in range(random.randint(1,3)):
                auto_nuevo = generar_auto_aleatorio()
                autos_a_asignar.append(auto_nuevo)
                autos_por_matricula[auto_nuevo[1]] = auto_nuevo
        else:
            elegir_auto_para_salir()

        # Mostrar información general
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
