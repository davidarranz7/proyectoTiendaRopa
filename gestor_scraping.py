import asyncio
import json
import os
import sys
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from scrapers.zara import extraer_categoria_zara
    from scrapers.mango import extraer_categoria_mango
    from scrapers.pullandbear import extraer_categoria_pull
    from scrapers.bershka import extraer_categoria_bershka
except ImportError as e:
    print(f"❌ Error crítico al importar scrapers: {e}")
    sys.exit()

async def ejecutar_todo():
    print("\n--- 🏁 INICIANDO SCRAPING MULTITIENDA 🏁 ---")

    CARPETA_DATOS = "datos"
    if not os.path.exists(CARPETA_DATOS):
        os.makedirs(CARPETA_DATOS)

    tareas_mango = [
        {"nombre": "camisetas_mujer", "url": "https://shop.mango.com/es/es/c/mujer/rebajas--50/camisetas_29da5fb2"}
    ]

    tareas_pull = [
        {"nombre": "camisetas_mujer", "url": "https://www.pullandbear.com/es/mujer/rebajas/ropa/camisetas-y-tops-n7097"}
    ]

    tareas_bershka = [
        {"nombre": "camisetas_mujer", "url": "https://www.bershka.com/es/mujer/sale/camisetas-y-tops-c1010850199.html"}
    ]

    tareas_zara = [
        {"nombre": "camisetas_mujer", "url": "https://www.zara.com/es/es/mujer-camisetas-l10252.html"},
        {"nombre": "pantalones_mujer", "url": "https://www.zara.com/es/es/s-mujer-pantalones-l10194.html?v1=2581636"}
    ]

    total_mango = []
    for tarea in tareas_mango:
        print(f"\n🚀 [MANGO] Procesando: {tarea['nombre']}...")
        datos = await extraer_categoria_mango(tarea["url"], tarea["nombre"])
        if datos:
            ruta = os.path.join(CARPETA_DATOS, f"mango_{tarea['nombre']}.json")
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            total_mango.extend(datos)
    if total_mango:
        with open(os.path.join(CARPETA_DATOS, "mango_total.json"), 'w', encoding='utf-8') as f:
            json.dump(total_mango, f, indent=4, ensure_ascii=False)

    total_pull = []
    for tarea in tareas_pull:
        print(f"\n🚀 [PULL&BEAR] Procesando: {tarea['nombre']}...")
        datos = await extraer_categoria_pull(tarea["url"], tarea["nombre"])
        if datos:
            ruta = os.path.join(CARPETA_DATOS, f"pullandbear_{tarea['nombre']}.json")
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            total_pull.extend(datos)
    if total_pull:
        with open(os.path.join(CARPETA_DATOS, "pullandbear_total.json"), 'w', encoding='utf-8') as f:
            json.dump(total_pull, f, indent=4, ensure_ascii=False)

    total_bershka = []
    for tarea in tareas_bershka:
        print(f"\n🚀 [BERSHKA] Procesando: {tarea['nombre']}...")
        datos = await extraer_categoria_bershka(tarea["url"], tarea["nombre"])
        if datos:
            ruta = os.path.join(CARPETA_DATOS, f"bershka_{tarea['nombre']}.json")
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            total_bershka.extend(datos)
    if total_bershka:
        with open(os.path.join(CARPETA_DATOS, "bershka_total.json"), 'w', encoding='utf-8') as f:
            json.dump(total_bershka, f, indent=4, ensure_ascii=False)

    total_zara = []
    for tarea in tareas_zara:
        print(f"\n🚀 [ZARA] Procesando: {tarea['nombre']}...")
        datos = await extraer_categoria_zara(tarea["url"], tarea["nombre"])
        if datos:
            ruta = os.path.join(CARPETA_DATOS, f"zara_{tarea['nombre']}.json")
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            total_zara.extend(datos)
    if total_zara:
        with open(os.path.join(CARPETA_DATOS, "zara_total.json"), 'w', encoding='utf-8') as f:
            json.dump(total_zara, f, indent=4, ensure_ascii=False)

    print(f"\n✨ PROCESO GLOBAL FINALIZADO ✨")

if __name__ == "__main__":
    asyncio.run(ejecutar_todo())