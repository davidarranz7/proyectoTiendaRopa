import asyncio
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.zara import extraer_categoria_zara

# Si ya tienes estos scrapers creados, descomenta los imports:
# from scrapers.bershka import extraer_categoria_bershka
# from scrapers.pullandbear import extraer_categoria_pullandbear


# ==========================================
# CONFIGURACIÓN DE URLS
# ==========================================

TIENDAS = {

    #"zara": {

        # ========================
        # HOMBRE
        # ========================

     #   "camisetas_hombre": "https://www.zara.com/es/es/hombre-camisetas-l855.html",
      #  "pantalones_hombre": "https://www.zara.com/es/es/hombre-pantalones-l838.html",
      #  "sudaderas_hombre": "https://www.zara.com/es/es/hombre-sudaderas-l821.html",

        # ========================
        # MUJER
        # ========================

       # "camisetas_mujer": "https://www.zara.com/es/es/mujer-camisetas-l1362.html",
       # "pantalones_mujer": "https://www.zara.com/es/es/mujer-pantalones-l1336.html",
       # "sudadera_mujer": "https://www.zara.com/es/es/mujer-sudaderas-l1375.html",
       # "vestidos_mujer": "https://www.zara.com/es/es/mujer-vestidos-l1066.html",
    #},

    # =========================================================
    # BERSHKA (COMENTADO PARA TENERLO LISTO, PERO NO SE EJECUTA)
    # =========================================================
     "bershka": {
    #
    #     # ========================
    #     # HOMBRE
    #     # ========================
         "hombre_camisetas": "https://www.bershka.com/es/hombre/ropa/camisetas-n3294.html?celement=1010193239",
         "hombre_pantalones": "https://www.bershka.com/es/hombre/ropa/pantalones-n3288.html",
         "hombre_sudaderas": "https://www.bershka.com/es/hombre/ropa/sudaderas-n3714.html",

         # ========================
         # MUJER
         # ========================
         "mujer_camisetas": "https://www.bershka.com/es/mujer/ropa/camisetas-n4365.html",
         "mujer_pantalones": "https://www.bershka.com/es/mujer/ropa/pantalones-n3888.html",
         "mujer_sudaderas": "https://www.bershka.com/es/mujer/ropa/sudaderas-n3873.html",
         "mujer_vestidos": "https://www.bershka.com/es/mujer/ropa/vestidos-n3802.html?celement=1010193213",
     },

    # ============================================================
    # PULL&BEAR (COMENTADO PARA TENERLO LISTO, PERO NO SE EJECUTA)
    # ============================================================
    # "pullandbear": {
    #
    #     # ========================
    #     # HOMBRE
    #     # ========================
    #     "hombre_camisetas": "PEGA_AQUI_URL_PULLANDBEAR_HOMBRE_CAMISETAS",
    #     "hombre_pantalones": "PEGA_AQUI_URL_PULLANDBEAR_HOMBRE_PANTALONES",
    #     "hombre_sudaderas": "PEGA_AQUI_URL_PULLANDBEAR_HOMBRE_SUDADERAS",
    #
    #     # ========================
    #     # MUJER
    #     # ========================
    #     "mujer_camisetas": "PEGA_AQUI_URL_PULLANDBEAR_MUJER_CAMISETAS",
    #     "mujer_pantalones": "PEGA_AQUI_URL_PULLANDBEAR_MUJER_PANTALONES",
    #     "mujer_sudaderas": "PEGA_AQUI_URL_PULLANDBEAR_MUJER_SUDADERAS",
    #     "mujer_vestidos": "PEGA_AQUI_URL_PULLANDBEAR_MUJER_VESTIDOS",
    # },
}


CARPETA_DATOS = "datos"


# ==========================================
# GUARDAR JSON
# ==========================================

def guardar_json(productos, archivo):
    os.makedirs(CARPETA_DATOS, exist_ok=True)
    ruta = os.path.join(CARPETA_DATOS, archivo)

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(productos, f, indent=4, ensure_ascii=False)

    print(f"💾 Guardado: {ruta} | {len(productos)} productos")


# ==========================================
# EJECUCIÓN DEL SCRAPING
# ==========================================

async def ejecutar():

    print("\n" + "=" * 60)
    print("🚀 GESTOR SCRAPING (ZARA activo / BERSHKA + PULL&BEAR comentados)")
    print("=" * 60)

    todos_los_productos = []

    for tienda, tareas in TIENDAS.items():

        print(f"\n🏪 TIENDA: {tienda.upper()}")

        for nombre_tarea, url in tareas.items():

            print("\n" + "-" * 60)
            print(f"🛠️ CATEGORÍA: {nombre_tarea}")
            print(f"🌍 URL: {url}")

            productos = []

            # ==========================
            # ZARA (ACTIVO)
            # ==========================
            if tienda == "zara":
                productos = await extraer_categoria_zara(url, nombre_tarea)

            # ==========================
            # BERSHKA (DESACTIVADO)
            # ==========================
            # if tienda == "bershka":
            #     productos = await extraer_categoria_bershka(url, nombre_tarea)

            # ==========================
            # PULL&BEAR (DESACTIVADO)
            # ==========================
            # if tienda == "pullandbear":
            #     productos = await extraer_categoria_pullandbear(url, nombre_tarea)

            if not productos:
                print("⚠ No se encontraron productos")
                continue

            # guardar json individual
            nombre_archivo = f"{tienda}_{nombre_tarea}.json"
            guardar_json(productos, nombre_archivo)

            todos_los_productos.extend(productos)

    # ==========================================
    # JSON TOTAL
    # ==========================================

    if todos_los_productos:
        guardar_json(todos_los_productos, "total.json")  # total de TODO lo activo
        print(f"\n📦 TOTAL PRODUCTOS: {len(todos_los_productos)}")
    else:
        print("\n⚠ No se recogieron productos")

    print("\n" + "=" * 60)
    print("✅ SCRAPING COMPLETADO")
    print("=" * 60)


# ==========================================
# ARRANQUE
# ==========================================

if __name__ == "__main__":
    try:
        asyncio.run(ejecutar())
    except KeyboardInterrupt:
        print("\n🛑 Scraping detenido por el usuario.")