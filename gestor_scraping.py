import asyncio
import json
import os
import sys

# Asegurar que Python encuentre la carpeta de scrapers
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from scrapers.zara import extraer_categoria_zara
    from scrapers.pullandbear import extraer_categoria_pull
    from scrapers.bershka import extraer_categoria_bershka

    print("✅ Scrapers cargados correctamente.")
except ImportError as e:
    print(f"❌ Error crítico al importar scrapers: {e}")
    sys.exit()


async def ejecutar_todo():
    print("\n" + "=" * 50)
    print("🚀 INICIANDO SCRAPING MULTITIENDA: MODO PRODUCCIÓN")
    print("=" * 50)

    CARPETA_DATOS = "datos"
    if not os.path.exists(CARPETA_DATOS):
        os.makedirs(CARPETA_DATOS)
        print(f"📁 Carpeta '{CARPETA_DATOS}' creada.")

    # --- LISTADOS DE TAREAS ---
    tareas_pull = [
        {"nombre": "camisetas_hombre",
         "url": "https://www.pullandbear.com/es/hombre/rebajas/ropa/camisetas-y-polos-n7087"},
        {"nombre": "sudaderas_hombre", "url": "https://www.pullandbear.com/es/hombre/rebajas/ropa/sudaderas-n7089"},
        {"nombre": "pantalones_hombre", "url": "https://www.pullandbear.com/es/hombre/rebajas/ropa/pantalones-n7091"},
        {"nombre": "camisetas_mujer",
         "url": "https://www.pullandbear.com/es/mujer/rebajas/ropa/camisetas-y-tops-n7097"},
        {"nombre": "pantalones_mujer", "url": "https://www.pullandbear.com/es/mujer/rebajas/ropa/pantalones-n7104"},
        {"nombre": "vestidos_mujer", "url": "https://www.pullandbear.com/es/mujer/rebajas/ropa/vestidos-y-monos-n7102"},
        {"nombre": "sudaderas_mujer", "url": "https://www.pullandbear.com/es/mujer/rebajas/ropa/sudaderas-n7100"}
    ]

    tareas_bershka = [
        {"nombre": "camisetas_hombre",
         "url": "https://www.bershka.com/es/hombre/sale/camisetas-y-polos-c1010747937.html"},
        {"nombre": "pantalones_hombre",
         "url": "https://www.bershka.com/es/hombre/sale/pantalones-y-jeans-c1010747956.html"},
        {"nombre": "sudaderas_hombre",
         "url": "https://www.bershka.com/es/hombre/sale/sudaderas-y-jers%C3%A9is-c1010747929.html"},
        {"nombre": "camisetas_mujer", "url": "https://www.bershka.com/es/mujer/sale/camisetas-y-tops-c1010850199.html"},
        {"nombre": "pantalones_mujer",
         "url": "https://www.bershka.com/es/mujer/sale/pantalones-y-jeans-c1010850196.html"},
        {"nombre": "vestidos_mujer", "url": "https://www.bershka.com/es/mujer/sale/vestidos-y-monos-c1010850201.html"},
        {"nombre": "sudaderas_mujer",
         "url": "https://www.bershka.com/es/mujer/sale/jers%C3%A9is-y-sudaderas-c1010850198.html"}
    ]

    tareas_zara = [
        {"nombre": "camisetas_hombre",
         "url": "https://www.zara.com/es/es/s-hombre-camisetas-polos-l11480.html?v1=2636785"},
        {"nombre": "sudaderas_hombre", "url": "https://www.zara.com/es/es/s-hombre-sudaderas-l11281.html?v1=2637270"},
        {"nombre": "pantalones_hombre",
         "url": "https://www.zara.com/es/es/s-hombre-pantalones-vaqueros-l11446.html?v1=2109823"},
        {"nombre": "camisetas_mujer", "url": "https://www.zara.com/es/es/s-mujer-camisetas-l10252.html?v1=2580457"},
        {"nombre": "pantalones_mujer", "url": "https://www.zara.com/es/es/s-mujer-pantalones-l10194.html?v1=2581636"},
        {"nombre": "vestidos_mujer", "url": "https://www.zara.com/es/es/s-mujer-vestidos-l8887.html?v1=2580270"},
        {"nombre": "sudaderas_mujer", "url": "https://www.zara.com/es/es/s-mujer-sudaderas-l10036.html?v1=2581747"}
    ]

    # --- BLOQUE PULL & BEAR ---
    total_pull = []
    for t in tareas_pull:
        print(f"\n--- 🛠️  PROCESANDO: PULLANDBEAR {t['nombre'].upper()} ---")
        try:
            datos = await extraer_categoria_pull(t["url"], t["nombre"])
            if datos:
                # Cambio de nombre: pullandbear_nombre.json
                archivo_json = os.path.join(CARPETA_DATOS, f"pullandbear_{t['nombre']}.json")
                with open(archivo_json, 'w', encoding='utf-8') as f:
                    json.dump(datos, f, indent=4, ensure_ascii=False)
                total_pull.extend(datos)
                print(f"💾 Guardado: {archivo_json} | 📊 {len(datos)} productos")
        except Exception as e:
            print(f"🔥 Error en Pull {t['nombre']}: {e}")

    # Guardar total Pull
    if total_pull:
        with open(os.path.join(CARPETA_DATOS, "pullandbear_total.json"), 'w', encoding='utf-8') as f:
            json.dump(total_pull, f, indent=4, ensure_ascii=False)

    # --- BLOQUE BERSHKA ---
    total_bershka = []
    for t in tareas_bershka:
        print(f"\n--- 🛠️  PROCESANDO: BERSHKA {t['nombre'].upper()} ---")
        try:
            datos = await extraer_categoria_bershka(t["url"], t["nombre"])
            if datos:
                # Cambio de nombre: bershka_nombre.json
                archivo_json = os.path.join(CARPETA_DATOS, f"bershka_{t['nombre']}.json")
                with open(archivo_json, 'w', encoding='utf-8') as f:
                    json.dump(datos, f, indent=4, ensure_ascii=False)
                total_bershka.extend(datos)
                print(f"💾 Guardado: {archivo_json} | 📊 {len(datos)} productos")
        except Exception as e:
            print(f"🔥 Error en Bershka {t['nombre']}: {e}")

    # Guardar total Bershka
    if total_bershka:
        with open(os.path.join(CARPETA_DATOS, "bershka_total.json"), 'w', encoding='utf-8') as f:
            json.dump(total_bershka, f, indent=4, ensure_ascii=False)

    # --- BLOQUE ZARA ---
    total_zara = []
    for t in tareas_zara:
        print(f"\n--- 🛠️  PROCESANDO: ZARA {t['nombre'].upper()} ---")
        try:
            datos = await extraer_categoria_zara(t["url"], t["nombre"])
            if datos:
                # Cambio de nombre: zara_nombre.json
                archivo_json = os.path.join(CARPETA_DATOS, f"zara_{t['nombre']}.json")
                with open(archivo_json, 'w', encoding='utf-8') as f:
                    json.dump(datos, f, indent=4, ensure_ascii=False)
                total_zara.extend(datos)
                print(f"💾 Guardado: {archivo_json} | 📊 {len(datos)} productos")
        except Exception as e:
            print(f"🔥 Error en Zara {t['nombre']}: {e}")

    # Guardar total Zara
    if total_zara:
        with open(os.path.join(CARPETA_DATOS, "zara_total.json"), 'w', encoding='utf-8') as f:
            json.dump(total_zara, f, indent=4, ensure_ascii=False)

    # --- RESUMEN FINAL ---
    print("\n" + "=" * 50)
    print(f"✨ PROCESO GLOBAL FINALIZADO ✨")
    print(f"📦 Resumen total: Pull ({len(total_pull)}) | Bershka ({len(total_bershka)}) | Zara ({len(total_zara)})")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(ejecutar_todo())
    except KeyboardInterrupt:
        print("\n🛑 Proceso detenido por el usuario.")