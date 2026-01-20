from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import json
import os
import random

from starlette.responses import RedirectResponse

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


def cargar_todos_los_chollos():
    todos_los_productos = []
    CARPETA_DATOS = "datos"

    if not os.path.exists(CARPETA_DATOS):
        return []

    for archivo in os.listdir(CARPETA_DATOS):
        if archivo.endswith("_total.json"):
            productos = cargar_datos_tienda(archivo)
            todos_los_productos.extend(productos)

    return todos_los_productos


@app.get("/")
async def inicio(request: Request):
    articulos = []
    return templates.TemplateResponse("principal.html", {"request": request, "articulos": articulos})


@app.get("/zara", response_class=HTMLResponse)
async def ver_zara(request: Request):
    articulos = cargar_datos_tienda("zara_total.json")
    return templates.TemplateResponse("zara.html", {"request": request, "articulos": articulos})


@app.get("/ofertas", response_class=HTMLResponse)
async def ofertas(request: Request):
    solo_chollos = []
    CARPETA_DATOS = "datos"

    if os.path.exists(CARPETA_DATOS):
        for archivo in os.listdir(CARPETA_DATOS):
            if archivo.endswith("_total.json"):
                productos = cargar_datos_tienda(archivo)
                for p in productos:
                    desc = p.get("descuento")
                    p_orig = p.get("precio_original")
                    p_final = p.get("precio_final")

                    if (desc and desc != "") or (p_orig and p_orig != p_final):
                        if not p.get("tienda"):
                            p["tienda"] = archivo.replace("_total.json", "").capitalize()
                        solo_chollos.append(p)

    random.shuffle(solo_chollos)

    return templates.TemplateResponse("ofertas.html", {"request": request, "articulos": solo_chollos})


@app.get("/mujer", response_class=HTMLResponse)
async def ver_mujer(request: Request):
    articulos_mujer = []
    CARPETA_DATOS = "datos"

    if os.path.exists(CARPETA_DATOS):
        for archivo in os.listdir(CARPETA_DATOS):
            if archivo.endswith("_mujer.json"):
                productos = cargar_datos_tienda(archivo)

                partes = archivo.replace(".json", "").split("_")
                tienda_nombre = partes[0].capitalize()
                categoria_nombre = partes[1]

                for p in productos:
                    p["tienda"] = tienda_nombre
                    p["categoria"] = categoria_nombre
                    articulos_mujer.append(p)

    random.shuffle(articulos_mujer)

    return templates.TemplateResponse("mujer.html", {
        "request": request,
        "articulos": articulos_mujer
    })


@app.get("/hombre", response_class=HTMLResponse)
async def ver_hombre(request: Request):
    articulos_hombre = []
    CARPETA_DATOS = "datos"

    if os.path.exists(CARPETA_DATOS):
        for archivo in os.listdir(CARPETA_DATOS):
            if archivo.endswith("_hombre.json"):
                productos = cargar_datos_tienda(archivo)
                partes = archivo.replace(".json", "").split("_")
                tienda_nombre = partes[0].capitalize()
                categoria_nombre = partes[1]

                for p in productos:
                    p["tienda"] = tienda_nombre
                    p["categoria"] = categoria_nombre
                    articulos_hombre.append(p)

    random.shuffle(articulos_hombre)
    return templates.TemplateResponse("hombre.html", {"request": request, "articulos": articulos_hombre})


from fastapi import Query


@app.get("/buscar", response_class=HTMLResponse)
async def buscar_productos(request: Request, q: str = Query(None)):
    resultados = []
    CARPETA_DATOS = "datos"

    if not q:
        return RedirectResponse(url="/ofertas")

    termino = q.lower().strip()
    print(f"--- Iniciando búsqueda para: '{termino}' ---")

    if os.path.exists(CARPETA_DATOS):
        for archivo in os.listdir(CARPETA_DATOS):
            if archivo.endswith(".json"):
                productos = cargar_datos_tienda(archivo)

                tienda_nombre = archivo.split("_")[0].capitalize()

                for p in productos:
                    nombre = str(p.get("nombre", "")).lower()
                    categoria = str(p.get("categoria", "")).lower()

                    if termino in nombre or termino in categoria or termino in archivo.lower():
                        p["tienda"] = p.get("tienda", tienda_nombre)
                        if not p.get("categoria"):
                            partes = archivo.split("_")
                            if len(partes) > 1:
                                p["categoria"] = partes[1]

                        resultados.append(p)

    print(f"--- Búsqueda finalizada: {len(resultados)} productos encontrados ---")

    return templates.TemplateResponse("ofertas.html", {
        "request": request,
        "articulos": resultados,
        "termino_busqueda": q
    })


@app.get("/pullandbear", response_class=HTMLResponse)
async def pagina_pullandbear(request: Request):
    articulos = cargar_datos_tienda("pullandbear_total.json")

    random.shuffle(articulos)

    return templates.TemplateResponse("pullandbear.html", {
        "request": request,
        "articulos": articulos,
        "tienda": "Pull&Bear"
    })


@app.get("/bershka", response_class=HTMLResponse)
async def pagina_bershka(request: Request):
    articulos = cargar_datos_tienda("bershka_total.json")

    random.shuffle(articulos)

    return templates.TemplateResponse("bershka.html", {
        "request": request,
        "articulos": articulos,
        "tienda": "Bershka"
    })


@app.get("/mango", response_class=HTMLResponse)
async def pagina_mango(request: Request):
    articulos = cargar_datos_tienda("mango_total.json")

    random.shuffle(articulos)

    return templates.TemplateResponse("mango.html", {
        "request": request,
        "articulos": articulos,
        "tienda": "Mango"
    })


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)