from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import json
import os

app = FastAPI()

# 1. Configuración de carpetas para recursos
app.mount("/estilos", StaticFiles(directory="estilos"), name="estilos")
app.mount("/script", StaticFiles(directory="script"), name="script")
templates = Jinja2Templates(directory="estatico")


# 2. Función para leer los JSON locales
def cargar_datos_tienda(nombre_archivo):
    ruta = os.path.join("datos", nombre_archivo)
    if not os.path.exists(ruta):
        print(f"⚠️ Advertencia: No se encontró el archivo {ruta}")
        return []

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error al leer {ruta}: {e}")
        return []


# --- RUTAS DE NAVEGACIÓN ---

@app.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    """Muestra todo el contenido disponible (Zara total)."""
    # Por ahora solo tienes Zara, cargamos el total
    articulos = cargar_datos_tienda("zara_total.json")
    return templates.TemplateResponse("principal.html", {"request": request, "articulos": articulos})


@app.get("/zara", response_class=HTMLResponse)
async def ver_zara(request: Request):
    """Ruta específica para la tienda Zara."""
    articulos = cargar_datos_tienda("zara_total.json")
    return templates.TemplateResponse("zara.html", {"request": request, "articulos": articulos})


@app.get("/ofertas", response_class=HTMLResponse)
async def ofertas(request: Request):
    """Filtra productos que tengan algún indicio de oferta."""
    todos = cargar_datos_tienda("zara_total.json")
    # Filtro básico: si el precio contiene algún símbolo o palabra de oferta
    solo_chollos = [p for p in todos if "oferta" in p.get("nombre", "").lower()]
    return templates.TemplateResponse("ofertas.html", {"request": request, "articulos": solo_chollos})


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)