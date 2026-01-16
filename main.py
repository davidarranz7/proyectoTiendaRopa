from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apify_client import ApifyClient
import uvicorn
import os
from dotenv import load_dotenv


app = FastAPI()

# Configuración de carpetas para recursos
app.mount("/estilos", StaticFiles(directory="estilos"), name="estilos")
app.mount("/script", StaticFiles(directory="script"), name="script")
templates = Jinja2Templates(directory="estatico")

# Configuración de Apify (Tu Token)
load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
client = ApifyClient(APIFY_TOKEN)


# Diccionario de Actores - H&M Eliminado
TIENDAS_IDS = {
    "zalando": "vistics/zalando-scraper",
    "zara": "karamelo/zara-scraper"
}


def obtener_datos_tienda(actor_id, nombre_tienda):
    """Extrae datos de Apify y normaliza precios y enlaces como intermediario."""
    articulos_formateados = []
    try:
        # Obtenemos las últimas ejecuciones exitosas
        runs = client.actor(actor_id).runs().list(limit=3)
        last_run = next((r for r in sorted(runs.items, key=lambda x: x["startedAt"], reverse=True)
                         if r["status"] == "SUCCEEDED"), None)

        if last_run:
            items = client.dataset(last_run["defaultDatasetId"]).list_items().items
            for item in items:
                # 1. CAPTURA DE PRECIOS SEGÚN EL SCRAPER
                p_orig_raw = item.get("originalPrice") or item.get("price")
                p_prom_raw = item.get("promotionalPrice") or item.get("salePrice")

                def corregir_precio(valor):
                    if not valor: return 0.0
                    try:
                        # Si es un string con símbolos, lo limpiamos, si es número lo convertimos
                        num = float(str(valor).replace("€", "").replace("£", "").strip())
                        # LÓGICA DE INTERMEDIARIO:
                        # Zalando manda céntimos (3999). Zara manda euros (39.95).
                        # Si el número es > 500, asumimos céntimos y dividimos por 100.
                        if num > 500:
                            return num / 100
                        return num
                    except:
                        return 0.0

                p_original = corregir_precio(p_orig_raw)
                p_promo = corregir_precio(p_prom_raw)

                # Si no hay oferta, el precio nuevo es igual al original
                if p_promo == 0 or p_promo >= p_original:
                    p_promo = p_original
                    descuento = ""
                else:
                    descuento = item.get("discountPercent") or "OFERTA"

                # 2. CONSTRUCCIÓN DEL OBJETO UNIFICADO
                articulos_formateados.append({
                    "tienda": nombre_tienda,
                    "marca": item.get("brand") or nombre_tienda,
                    "nombre": item.get("name", "Prenda de Temporada"),
                    "precio_original": f"{p_original:.2f}€",
                    "precio_nuevo": f"{p_promo:.2f}€",
                    "descuento": descuento,
                    "imagen": item.get("imageUrl") or item.get("image") or item.get("thumbnail"),
                    "url": item.get("productUrl") or item.get("url", "#")  # Enlace directo para el intermediario
                })
    except Exception as e:
        print(f"⚠️ Error cargando {nombre_tienda}: {e}")

    return articulos_formateados


# --- RUTAS DE NAVEGACIÓN ---

@app.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    """Mezcla productos de todas las tiendas para la Home."""
    todos = []
    for nombre, actor_id in TIENDAS_IDS.items():
        todos.extend(obtener_datos_tienda(actor_id, nombre.capitalize()))
    return templates.TemplateResponse("principal.html", {"request": request, "articulos": todos})


@app.get("/ofertas", response_class=HTMLResponse)
async def ofertas(request: Request):
    """Solo productos con descuento detectado en los scrapers."""
    todos = []
    for nombre, actor_id in TIENDAS_IDS.items():
        todos.extend(obtener_datos_tienda(actor_id, nombre.capitalize()))
    solo_chollos = [p for p in todos if p["descuento"]]
    return templates.TemplateResponse("ofertas.html", {"request": request, "articulos": solo_chollos})


@app.get("/zalando", response_class=HTMLResponse)
async def ver_zalando(request: Request):
    articulos = obtener_datos_tienda(TIENDAS_IDS["zalando"], "Zalando")
    return templates.TemplateResponse("zalando.html", {"request": request, "articulos": articulos})


@app.get("/zara", response_class=HTMLResponse)
async def ver_zara(request: Request):
    articulos = obtener_datos_tienda(TIENDAS_IDS["zara"], "Zara")
    return templates.TemplateResponse("zara.html", {"request": request, "articulos": articulos})


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)