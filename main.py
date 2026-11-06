import csv
from datetime import datetime

# ==========================================
# FASE 2: CARGA Y VALIDACIÓN
# ==========================================

productos = []

with open("inventario.csv", "r", encoding="utf-8-sig") as archivo:
    lector = csv.DictReader(archivo)

    columnas = {
        "id_producto",
        "nombre",
        "categoria",
        "stock",
        "precio_unitario",
        "fecha_ingreso"
    }

    if not columnas.issubset(lector.fieldnames or []):
        raise ValueError("El CSV no contiene todas las columnas requeridas.")

    for numero_fila, fila in enumerate(lector, start=2):
        try:
            producto = {
                "id_producto": int(fila["id_producto"]),
                "nombre": fila["nombre"].strip(),
                "categoria": fila["categoria"].strip(),
                "stock": int(fila["stock"]),
                "precio_unitario": float(fila["precio_unitario"]),
                "fecha_ingreso": datetime.strptime(
                    fila["fecha_ingreso"], "%Y-%m-%d"
                ).date()
            }

            if producto["id_producto"] <= 0:
                raise ValueError("El ID debe ser positivo.")

            if producto["stock"] < 0:
                raise ValueError("El stock no puede ser negativo.")

            if producto["precio_unitario"] < 0:
                raise ValueError("El precio no puede ser negativo.")

            if not producto["nombre"] or not producto["categoria"]:
                raise ValueError("Nombre y categoría no pueden estar vacíos.")

            productos.append(producto)

        except (ValueError, TypeError) as error:
            print(f"Error en fila {numero_fila}: {error}")

# Validar IDs únicos
ids = [p["id_producto"] for p in productos]

if len(ids) != len(set(ids)):
    raise ValueError("Existen IDs de productos duplicados.")

print(f"\nProductos cargados correctamente: {len(productos)}")


# ==========================================
# FASE 2: AGREGACIÓN POR CATEGORÍA
# ==========================================

categorias = {}

for producto in productos:
    categoria = producto["categoria"]

    if categoria not in categorias:
        categorias[categoria] = {
            "total_productos": 0,
            "total_stock": 0,
            "valor_total": 0.0,
            "suma_precios": 0.0
        }

    categorias[categoria]["total_productos"] += 1
    categorias[categoria]["total_stock"] += producto["stock"]

    categorias[categoria]["valor_total"] += (
        producto["stock"] * producto["precio_unitario"]
    )

    categorias[categoria]["suma_precios"] += producto["precio_unitario"]


# ==========================================
# FASE 2: DETECCIÓN DE PRODUCTOS CRÍTICOS
# ==========================================

productos_criticos = []

for producto in productos:
    if producto["stock"] < 5:
        productos_criticos.append(producto)

# Ordenar por stock ascendente
productos_criticos.sort(key=lambda p: p["stock"])

print(f"Productos con stock crítico: {len(productos_criticos)}")


# ==========================================
# FASE 2: TOP 10 POR VALOR EN INVENTARIO
# ==========================================

top_10 = sorted(
    productos,
    key=lambda p: p["stock"] * p["precio_unitario"],
    reverse=True
)[:10]

print("\nTOP 10 PRODUCTOS POR VALOR EN INVENTARIO")

for producto in top_10:
    valor = producto["stock"] * producto["precio_unitario"]
    print(f"{producto['nombre']} - Valor: ${valor:.2f}")


# ==========================================
# FASE 3: EXPORTAR RESUMEN DE CATEGORÍAS
# ==========================================

with open("resumen_categorias.csv", "w", newline="", encoding="utf-8") as archivo:
    campos = [
        "categoria",
        "total_productos",
        "total_stock",
        "valor_total"
    ]

    escritor = csv.DictWriter(archivo, fieldnames=campos)
    escritor.writeheader()

    for categoria, datos in categorias.items():
        escritor.writerow({
            "categoria": categoria,
            "total_productos": datos["total_productos"],
            "total_stock": datos["total_stock"],
            "valor_total": round(datos["valor_total"], 2)
        })


# ==========================================
# FASE 3: EXPORTAR ALERTAS DE REPOSICIÓN
# ==========================================

with open("alertas_reposicion.txt", "w", encoding="utf-8") as archivo:
    for producto in productos_criticos:
        archivo.write(
            f"{producto['id_producto']} | "
            f"{producto['nombre']} | "
            f"{producto['stock']} | "
            f"{producto['categoria']}\n"
        )


# ==========================================
# FASE 3: ANÁLISIS TEXTUAL EN CONSOLA
# ==========================================

print("\n========== REPORTE GENERAL ==========")

# Categoría con mayor valor total
if categorias:
    mayor_categoria = max(
        categorias.items(),
        key=lambda item: item[1]["valor_total"]
    )

    print(
        f"\nCategoría con mayor valor total: "
        f"{mayor_categoria[0]} "
        f"(${mayor_categoria[1]['valor_total']:.2f})"
    )

# Porcentaje de productos críticos
total_productos = len(productos)

if total_productos > 0:
    porcentaje = (len(productos_criticos) / total_productos) * 100
    print(f"Porcentaje de productos críticos: {porcentaje:.2f}%")
else:
    print("No hay productos para calcular el porcentaje.")

# Precio promedio por categoría
print("\nPrecio promedio por categoría:")

for categoria, datos in categorias.items():
    promedio = datos["suma_precios"] / datos["total_productos"]

    print(f"{categoria}: ${promedio:.2f}")

print("\n=====================================")
print("Archivos generados correctamente:")
print("- resumen_categorias.csv")
print("- alertas_reposicion.txt")
