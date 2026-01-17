from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import json
import os

app = FastAPI()

app.mount("/estilos", StaticFiles(directory="estilos"), name="estilos")
app.mount("/script", StaticFiles(directory="script"), name="script")
templates = Jinja2Templates(directory="estatico")


def cargar_datos_tienda(nombre_archivo):
    ruta = os.path.join("datos", nombre_archivo)
    if not os.path.exists(ruta):
        return []
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error al leer {ruta}: {e}")
        return []


# --- NUEVA FUNCIÓN PARA AGREGAR TODAS LAS TIENDAS ---
def cargar_todos_los_chollos():
    todos_los_productos = []
    CARPETA_DATOS = "datos"

    if not os.path.exists(CARPETA_DATOS):
        return []

    # Busca cada archivo que termine en _total.json (zara_total, bershka_total, etc.)
    for archivo in os.listdir(CARPETA_DATOS):
        if archivo.endswith("_total.json"):
            productos = cargar_datos_tienda(archivo)
            todos_los_productos.extend(productos)

    return todos_los_productos


# --- RUTAS ---

@app.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    articulos = cargar_datos_tienda("zara_total.json")
    return templates.TemplateResponse("principal.html", {"request": request, "articulos": articulos})


@app.get("/zara", response_class=HTMLResponse)
async def ver_zara(request: Request):
    articulos = cargar_datos_tienda("zara_total.json")
    return templates.TemplateResponse("zara.html", {"request": request, "articulos": articulos})


@app.get("/ofertas", response_class=HTMLResponse)
async def ofertas(request: Request):
    """Carga todos los chollos de cualquier tienda en la carpeta datos."""
    solo_chollos = []
    CARPETA_DATOS = "datos"

    if os.path.exists(CARPETA_DATOS):
        for archivo in os.listdir(CARPETA_DATOS):
            if archivo.endswith("_total.json"):
                productos = cargar_datos_tienda(archivo)
                for p in productos:
                    # Filtro: Solo si hay descuento escrito o el precio bajó
                    desc = p.get("descuento")
                    p_orig = p.get("precio_original")
                    p_final = p.get("precio_final")

                    if (desc and desc != "") or (p_orig and p_orig != p_final):
                        # Detecta la tienda por el nombre del archivo
                        if not p.get("tienda"):
                            p["tienda"] = archivo.replace("_total.json", "").capitalize()
                        solo_chollos.append(p)

    return templates.TemplateResponse("ofertas.html", {"request": request, "articulos": solo_chollos})

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)