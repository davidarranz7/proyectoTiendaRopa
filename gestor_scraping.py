import asyncio
import json
import os
import sys

# Asegura que Python encuentre la carpeta 'scrapers'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from scrapers.zara import extraer_categoria_zara
except ImportError as e:
    print(f"❌ Error crítico: {e}")
    sys.exit()


async def ejecutar_todo():
    print("\n--- 🏁 INICIANDO SCRAPING LOCAL 🏁 ---")

    CARPETA_DATOS = "datos"
    if not os.path.exists(CARPETA_DATOS):
        os.makedirs(CARPETA_DATOS)

    # CONFIGURACIÓN: Aquí es donde añadimos los pantalones sin romper el zara.py
    tareas_zara = [
        {
            "nombre": "camisetas_mujer",
            "url": "https://www.zara.com/es/es/mujer-camisetas-l10252.html"
        },
        {
            "nombre": "pantalones_mujer",
            "url": "https://www.zara.com/es/es/s-mujer-pantalones-l10194.html?v1=2581636"
        }
    ]

    total_zara = []

    for tarea in tareas_zara:
        print(f"\n🚀 Procesando categoría: {tarea['nombre']}...")
        # Llama a la función de zara.py que ya te funciona perfectamente
        datos = await extraer_categoria_zara(tarea["url"], tarea["nombre"])

        if datos:
            # Guarda el archivo individual (ej: zara_pantalones_mujer.json)
            ruta = os.path.join(CARPETA_DATOS, f"zara_{tarea['nombre']}.json")
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)

            total_zara.extend(datos)
            print(f"💾 Archivo guardado: {ruta}")

    # Guardado del total unificado (Camisetas + Pantalones)
    if total_zara:
        ruta_total = os.path.join(CARPETA_DATOS, "zara_total.json")
        with open(ruta_total, 'w', encoding='utf-8') as f:
            json.dump(total_zara, f, indent=4, ensure_ascii=False)
        print(f"\n✨ PROCESO FINALIZADO ✨")
        print(f"📦 Total productos guardados: {len(total_zara)}")
    else:
        print("\n⚠️ No se ha podido extraer nada. Revisa la ventana del navegador.")


if __name__ == "__main__":
    asyncio.run(ejecutar_todo())