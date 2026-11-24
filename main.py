import csv
import heapq
import math
from datetime import datetime
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
ARCHIVO_ENTRADA = CARPETA / "inventario.csv"
ARCHIVO_RESUMEN = CARPETA / "resumen_categorias.csv"
ARCHIVO_ALERTAS = CARPETA / "alertas_reposicion.txt"

UMBRAL_CRITICO = 5

# ==========================================
# CARGA Y VALIDACIÓN
# ==========================================

COLUMNAS_REQUERIDAS = {
    "id_producto",
    "nombre",
    "categoria",
    "stock",
    "precio_unitario",
    "fecha_ingreso",
}

productos = []
ids_vistos = set()
filas_leidas = 0
filas_descartadas = 0

with open(ARCHIVO_ENTRADA, "r", encoding="utf-8-sig", newline="") as archivo:
    lector = csv.DictReader(archivo)

    if not COLUMNAS_REQUERIDAS.issubset(lector.fieldnames or []):
        raise ValueError("El CSV no contiene todas las columnas requeridas.")

    for numero_fila, fila in enumerate(lector, start=2):
        filas_leidas += 1

        try:
            producto = {
                "id_producto": int(fila["id_producto"]),
                "nombre": fila["nombre"].strip(),
                "categoria": fila["categoria"].strip(),
                "stock": int(fila["stock"]),
                "precio_unitario": float(fila["precio_unitario"]),
                "fecha_ingreso": datetime.strptime(
                    fila["fecha_ingreso"].strip(), "%Y-%m-%d"
                ).date(),
            }

            if producto["id_producto"] <= 0:
                raise ValueError("El ID debe ser positivo.")

            if producto["id_producto"] in ids_vistos:
                raise ValueError(f"ID duplicado ({producto['id_producto']}).")

            if producto["stock"] < 0:
                raise ValueError("El stock no puede ser negativo.")

            if (
                not math.isfinite(producto["precio_unitario"])
                or producto["precio_unitario"] < 0
            ):
                raise ValueError("El precio debe ser un número no negativo.")

            if not producto["nombre"] or not producto["categoria"]:
                raise ValueError("Nombre y categoría no pueden estar vacíos.")

            ids_vistos.add(producto["id_producto"])
            productos.append(producto)

        except (ValueError, TypeError, KeyError, AttributeError) as error:
            filas_descartadas += 1
            print(f"Fila {numero_fila} descartada: {error}")

print("\n========== CARGA DEL ARCHIVO ==========")
print(f"Filas leídas:        {filas_leidas}")
print(f"Filas válidas:       {len(productos)}")
print(f"Filas descartadas:   {filas_descartadas}")


# ==========================================
# AGREGACIÓN POR CATEGORÍA (diccionario)
# ==========================================

categorias = {}

for producto in productos:
    categoria = producto["categoria"]

    if categoria not in categorias:
        categorias[categoria] = {
            "total_productos": 0,
            "total_stock": 0,
            "valor_total": 0.0,
            "suma_precios": 0.0,
        }

    datos = categorias[categoria]
    datos["total_productos"] += 1
    datos["total_stock"] += producto["stock"]
    datos["valor_total"] += producto["stock"] * producto["precio_unitario"]
    datos["suma_precios"] += producto["precio_unitario"]


# ==========================================
# PRODUCTOS CRÍTICOS (lista filtrada y ordenada)
# ==========================================

productos_criticos = [p for p in productos if p["stock"] < UMBRAL_CRITICO]
productos_criticos.sort(key=lambda p: p["stock"])


# ==========================================
# TOP 10 POR VALOR (cola de prioridad)
# ==========================================

def valor_en_inventario(producto):
    return producto["stock"] * producto["precio_unitario"]


top_10 = heapq.nlargest(10, productos, key=valor_en_inventario)

print("\n===== TOP 10 PRODUCTOS POR VALOR EN INVENTARIO =====")
for posicion, producto in enumerate(top_10, start=1):
    print(
        f"{posicion:>2}. {producto['nombre']} "
        f"({producto['categoria']}) - Valor: ${valor_en_inventario(producto):,.2f}"
    )


# ==========================================
# EXPORTACIÓN
# ==========================================

with open(ARCHIVO_RESUMEN, "w", newline="", encoding="utf-8") as archivo:
    campos = ["categoria", "total_productos", "total_stock", "valor_total"]
    escritor = csv.DictWriter(archivo, fieldnames=campos)
    escritor.writeheader()

    for categoria, datos in categorias.items():
        escritor.writerow(
            {
                "categoria": categoria,
                "total_productos": datos["total_productos"],
                "total_stock": datos["total_stock"],
                "valor_total": f"{datos['valor_total']:.2f}",
            }
        )

with open(ARCHIVO_ALERTAS, "w", encoding="utf-8") as archivo:
    for producto in productos_criticos:
        archivo.write(
            f"{producto['id_producto']} | "
            f"{producto['nombre']} | "
            f"Stock actual: {producto['stock']} | "
            f"Categoria: {producto['categoria']}\n"
        )


# ==========================================
# ANÁLISIS EN CONSOLA
# ==========================================

print("\n========== REPORTE GENERAL ==========")

if categorias:
    nombre_mayor, datos_mayor = max(
        categorias.items(), key=lambda item: item[1]["valor_total"]
    )
    print(
        f"\nCategoría con mayor valor total: "
        f"{nombre_mayor} (${datos_mayor['valor_total']:,.2f})"
    )

total_productos = len(productos)

if total_productos > 0:
    porcentaje = (len(productos_criticos) / total_productos) * 100
    print(
        f"Productos con stock crítico: {len(productos_criticos)} de "
        f"{total_productos} ({porcentaje:.2f}%)"
    )
else:
    print("No hay productos para calcular el porcentaje.")

print("\nPrecio promedio por categoría:")
for categoria, datos in categorias.items():
    promedio = datos["suma_precios"] / datos["total_productos"]
    print(f"  {categoria}: ${promedio:,.2f}")

print("\n========== ANTES Y DESPUÉS ==========")
print(f"Filas que entraron (leídas):   {filas_leidas}")
print(f"Filas válidas procesadas:      {len(productos)}")
print(f"Filas descartadas:             {filas_descartadas}")
print(f"Alertas de reposición:         {len(productos_criticos)}")

print("\n=====================================")
print("Archivos generados correctamente:")
print(f"- {ARCHIVO_RESUMEN.name}")
print(f"- {ARCHIVO_ALERTAS.name}")
