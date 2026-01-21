from fastapi import FastAPI, Request, Query
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

# --- 1. DICCIONARIO DE SINÓNIMOS (Búsqueda Inteligente) ---
MAPEO_CATEGORIAS = {
    "camisetas": ["camiseta", "top", "tirantes", "polo", "t-shirt", "interlock", "manga corta"],
    "pantalones": ["pantalon", "jeans", "vaquero", "shorts", "bermuda", "denim", "satinado"],
    "sudaderas": ["sudadera", "hoodie", "jumper", "jersey", "punto"],
    "vestidos": ["vestido", "mono", "tunic", "gown"]
}


def normalizar_texto(texto):
    """Elimina tildes y pasa a minúsculas para una búsqueda justa."""
    remplazos = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u"}
    texto = str(texto).lower()
    for tilde, limpia in remplazos.items():
        texto = texto.replace(tilde, limpia)
    return texto.strip()


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
            # Solo analizamos archivos de productos totales o por categoría
            if archivo.endswith(".json"):
                productos = cargar_datos_tienda(archivo)
                tienda_nombre = archivo.split("_")[0].capitalize()

                for p in productos:
                    # FILTRO CRÍTICO: Solo si tiene descuento real
                    tiene_descuento = p.get("descuento") is not None and p.get("descuento") != ""

                    if tiene_descuento:
                        # Aseguramos que el nombre de la tienda aparezca
                        if not p.get("tienda"):
                            p["tienda"] = tienda_nombre
                        solo_chollos.append(p)

    # Mezclamos para que no salgan siempre los mismos primero
    random.shuffle(solo_chollos)

    return templates.TemplateResponse("ofertas.html", {
        "request": request,
        "articulos": solo_chollos
    })


@app.get("/nueva-coleccion", response_class=HTMLResponse)
async def nueva_coleccion(request: Request):
    novedades = []
    CARPETA_DATOS = "datos"

    if os.path.exists(CARPETA_DATOS):
        for archivo in os.listdir(CARPETA_DATOS):
            if archivo.endswith(".json"):
                productos = cargar_datos_tienda(archivo)
                tienda_nombre = archivo.split("_")[0].capitalize()

                for p in productos:
                    # FILTRO: Solo si NO tiene descuento (es nueva colección)
                    es_novedad = p.get("descuento") is None or p.get("descuento") == ""

                    if es_novedad:
                        if not p.get("tienda"):
                            p["tienda"] = tienda_nombre
                        novedades.append(p)

    random.shuffle(novedades)
    return templates.TemplateResponse("nuevacolecion.html", {
        "request": request,
        "articulos": novedades
    })

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
    return templates.TemplateResponse("mujer.html", {"request": request, "articulos": articulos_mujer})


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


@app.get("/buscar", response_class=HTMLResponse)
async def buscar_productos(request: Request, q: str = Query(None)):
    resultados = []
    CARPETA_DATOS = "datos"

    if not q:
        return RedirectResponse(url="/ofertas")

    # 2. LÓGICA DE BÚSQUEDA INTELIGENTE
    termino_usuario = normalizar_texto(q)
    print(f"--- Iniciando búsqueda inteligente para: '{termino_usuario}' ---")

    # Expandir términos usando el diccionario de sinónimos
    terminos_a_buscar = [termino_usuario]
    for categoria_madre, sinonimos in MAPEO_CATEGORIAS.items():
        # Si el usuario busca la categoría madre o un sinónimo, incluimos todo el grupo
        if termino_usuario == categoria_madre or termino_usuario in sinonimos:
            terminos_a_buscar.extend(sinonimos)
            terminos_a_buscar.append(categoria_madre)

    terminos_a_buscar = list(set(terminos_a_buscar))  # Eliminar duplicados

    if os.path.exists(CARPETA_DATOS):
        # Buscamos en todos los archivos .json para asegurar cobertura
        for archivo in os.listdir(CARPETA_DATOS):
            if archivo.endswith(".json"):
                productos = cargar_datos_tienda(archivo)
                tienda_nombre = archivo.split("_")[0].capitalize()

                for p in productos:
                    nombre_prod = normalizar_texto(p.get("nombre", ""))
                    categoria_prod = normalizar_texto(p.get("categoria", ""))

                    # Si alguno de nuestros términos expandidos coincide con el producto
                    if any(term in nombre_prod for term in terminos_a_buscar) or \
                            any(term in categoria_prod for term in terminos_a_buscar):

                        p["tienda"] = p.get("tienda", tienda_nombre)
                        if not p.get("categoria"):
                            partes = archivo.split("_")
                            if len(partes) > 1:
                                p["categoria"] = partes[1]

                        resultados.append(p)

    # Eliminar duplicados de productos (por si aparecen en categoría y total)
    resultados_unicos = {p['imagen']: p for p in resultados}.values()
    print(f"--- Búsqueda finalizada: {len(resultados_unicos)} productos encontrados ---")

    return templates.TemplateResponse("ofertas.html", {
        "request": request,
        "articulos": list(resultados_unicos),
        "termino_busqueda": q
    })


@app.get("/pullandbear", response_class=HTMLResponse)
async def pagina_pullandbear(request: Request):
    articulos = cargar_datos_tienda("pullandbear_total.json")
    random.shuffle(articulos)
    return templates.TemplateResponse("pullandbear.html",
                                      {"request": request, "articulos": articulos, "tienda": "Pull&Bear"})


@app.get("/bershka", response_class=HTMLResponse)
async def pagina_bershka(request: Request):
    articulos = cargar_datos_tienda("bershka_total.json")
    random.shuffle(articulos)
    return templates.TemplateResponse("bershka.html", {"request": request, "articulos": articulos, "tienda": "Bershka"})


@app.get("/mango", response_class=HTMLResponse)
async def pagina_mango(request: Request):
    articulos = cargar_datos_tienda("mango_total.json")
    random.shuffle(articulos)
    return templates.TemplateResponse("mango.html", {"request": request, "articulos": articulos, "tienda": "Mango"})


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)