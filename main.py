from __future__ import annotations

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from pathlib import Path
import json
import random
from typing import Any, Dict, List, Optional, Tuple

app = FastAPI()

# Static
app.mount("/estilos", StaticFiles(directory="estilos"), name="estilos")
app.mount("/script", StaticFiles(directory="script"), name="script")
templates = Jinja2Templates(directory="estatico")

# Datos
DATOS_DIR = Path("datos")

# --- 1) DICCIONARIO DE SINÓNIMOS (Búsqueda Inteligente) ---
MAPEO_CATEGORIAS = {
    "camisetas": ["camiseta", "top", "tirantes", "polo", "t-shirt", "interlock", "manga corta"],
    "pantalones": ["pantalon", "jeans", "vaquero", "shorts", "bermuda", "denim", "satinado"],
    "sudaderas": ["sudadera", "hoodie", "jumper", "jersey", "punto"],
    "vestidos": ["vestido", "mono", "tunic", "gown"],
}


def normalizar_texto(texto: Any) -> str:
    """Elimina tildes y pasa a minúsculas para una búsqueda justa."""
    remplazos = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"}
    texto = str(texto or "").lower()
    for tilde, limpia in remplazos.items():
        texto = texto.replace(tilde, limpia)
    return texto.strip()


# ============================================================
# 2) CACHÉ DE LECTURA JSON (evita I/O constante)
# ============================================================

# cache: ruta -> (mtime, data)
_JSON_CACHE: Dict[Path, Tuple[float, List[Dict[str, Any]]]] = {}


def cargar_json_cacheado(ruta: Path) -> List[Dict[str, Any]]:
    if not ruta.exists() or not ruta.is_file():
        return []

    try:
        mtime = ruta.stat().st_mtime
        if ruta in _JSON_CACHE and _JSON_CACHE[ruta][0] == mtime:
            return _JSON_CACHE[ruta][1]

        with ruta.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            data = []

        # Guardar en caché
        _JSON_CACHE[ruta] = (mtime, data)
        return data
    except Exception as e:
        print(f"❌ Error leyendo {ruta}: {e}")
        return []


def inferir_tienda_y_categoria_desde_archivo(nombre_archivo: str) -> Tuple[str, Optional[str]]:
    """
    Ejemplos:
      zara_total.json -> ("Zara", None)
      zara_camisetas_hombre.json -> ("Zara", "camisetas_hombre")
      pullandbear_pantalones_mujer.json -> ("Pullandbear", "pantalones_mujer")
    """
    base = nombre_archivo.replace(".json", "")
    partes = base.split("_")
    tienda = (partes[0] if partes else "desconocido").capitalize()
    categoria = None
    if len(partes) >= 2 and partes[1] != "total":
        categoria = "_".join(partes[1:])  # camisetas_hombre, etc.
    return tienda, categoria


def clave_unica_producto(p: Dict[str, Any], tienda_fallback: str) -> str:
    """
    Clave robusta:
    1) tienda + url_producto (lo más estable)
    2) tienda + imagen (fallback)
    3) tienda + nombre + precio_final (último recurso)
    """
    tienda = str(p.get("tienda") or tienda_fallback or "").strip().lower()
    url = str(p.get("url_producto") or "").strip()
    if url:
        return f"{tienda}|{url}"

    img = str(p.get("imagen") or "").strip()
    if img:
        return f"{tienda}|img:{img}"

    nombre = str(p.get("nombre") or "").strip().lower()
    precio = str(p.get("precio_final") or "").strip()
    return f"{tienda}|{nombre}|{precio}"


def normalizar_producto(p: Dict[str, Any], tienda: str, categoria: Optional[str]) -> Dict[str, Any]:
    """
    Asegura campos consistentes sin pisar si ya vienen.
    """
    if not p.get("tienda"):
        p["tienda"] = tienda
    if categoria and not p.get("categoria"):
        p["categoria"] = categoria
    return p


def listar_archivos_json() -> List[Path]:
    if not DATOS_DIR.exists():
        return []
    return sorted([p for p in DATOS_DIR.iterdir() if p.is_file() and p.suffix == ".json"])


def cargar_productos_globales(modo: str = "total_preferido") -> List[Dict[str, Any]]:
    """
    modo:
      - "solo_total": solo *_total.json (evita duplicados por diseño)
      - "total_preferido": usa *_total.json si existe por tienda; si no, usa categorías.
      - "todo": carga todo y deduplica por clave (más pesado)
    """
    archivos = listar_archivos_json()
    if not archivos:
        return []

    # Agrupar por tienda
    por_tienda: Dict[str, Dict[str, List[Path]]] = {}
    for ruta in archivos:
        tienda, categoria = inferir_tienda_y_categoria_desde_archivo(ruta.name)
        por_tienda.setdefault(tienda, {}).setdefault(categoria or "total", []).append(ruta)

    seleccion: List[Path] = []

    if modo == "solo_total":
        for tienda, grupos in por_tienda.items():
            if "total" in grupos:
                # si hay varios, cogemos todos (por si lo separas en el futuro)
                seleccion.extend(grupos["total"])
        # si no hay total para una tienda, no entra nada (decisión explícita)
    elif modo == "total_preferido":
        for tienda, grupos in por_tienda.items():
            if "total" in grupos:
                seleccion.extend(grupos["total"])
            else:
                # No existe total: usar las categorías
                for cat, rutas in grupos.items():
                    if cat != "total":
                        seleccion.extend(rutas)
    else:  # "todo"
        seleccion = archivos

    # Cargar y deduplicar
    vistos: Dict[str, Dict[str, Any]] = {}
    for ruta in seleccion:
        tienda, categoria = inferir_tienda_y_categoria_desde_archivo(ruta.name)
        productos = cargar_json_cacheado(ruta)

        for p in productos:
            if not isinstance(p, dict):
                continue
            p = normalizar_producto(p, tienda, categoria)
            k = clave_unica_producto(p, tienda)

            # Estrategia: si ya existe, preferimos el que tenga más info
            if k in vistos:
                anterior = vistos[k]
                # “Mejor” = tiene descuento o más campos no vacíos
                score_new = sum(1 for v in p.values() if v not in (None, "", []))
                score_old = sum(1 for v in anterior.values() if v not in (None, "", []))
                if score_new > score_old:
                    vistos[k] = p
            else:
                vistos[k] = p

    return list(vistos.values())


# ============================================================
# 3) RUTAS
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    # Home vacío (como lo tenías)
    return templates.TemplateResponse("principal.html", {"request": request, "articulos": []})


@app.get("/zara", response_class=HTMLResponse)
async def ver_zara(request: Request):
    # Mejor: cargar solo el total de Zara
    ruta = DATOS_DIR / "zara_total.json"
    articulos = cargar_json_cacheado(ruta)
    # Asegurar tienda
    articulos = [normalizar_producto(p, "Zara", None) for p in articulos if isinstance(p, dict)]
    return templates.TemplateResponse("zara.html", {"request": request, "articulos": articulos})


@app.get("/pullandbear", response_class=HTMLResponse)
async def pagina_pullandbear(request: Request):
    ruta = DATOS_DIR / "pullandbear_total.json"
    articulos = cargar_json_cacheado(ruta)
    articulos = [normalizar_producto(p, "Pullandbear", None) for p in articulos if isinstance(p, dict)]
    random.shuffle(articulos)
    return templates.TemplateResponse(
        "pullandbear.html",
        {"request": request, "articulos": articulos, "tienda": "Pull&Bear"},
    )


@app.get("/bershka", response_class=HTMLResponse)
async def pagina_bershka(request: Request):
    ruta = DATOS_DIR / "bershka_total.json"
    articulos = cargar_json_cacheado(ruta)
    articulos = [normalizar_producto(p, "Bershka", None) for p in articulos if isinstance(p, dict)]
    random.shuffle(articulos)
    return templates.TemplateResponse("bershka.html", {"request": request, "articulos": articulos, "tienda": "Bershka"})


@app.get("/mango", response_class=HTMLResponse)
async def pagina_mango(request: Request):
    ruta = DATOS_DIR / "mango_total.json"
    articulos = cargar_json_cacheado(ruta)
    articulos = [normalizar_producto(p, "Mango", None) for p in articulos if isinstance(p, dict)]
    random.shuffle(articulos)
    return templates.TemplateResponse("mango.html", {"request": request, "articulos": articulos, "tienda": "Mango"})


@app.get("/ofertas", response_class=HTMLResponse)
async def ofertas(request: Request):
    # Importante: evitar duplicados cargando por defecto el "total_preferido"
    productos = cargar_productos_globales(modo="total_preferido")

    solo_chollos = []
    for p in productos:
        desc = p.get("descuento")
        tiene_descuento = desc is not None and str(desc).strip() != ""
        if tiene_descuento:
            solo_chollos.append(p)

    random.shuffle(solo_chollos)
    return templates.TemplateResponse("ofertas.html", {"request": request, "articulos": solo_chollos})


@app.get("/nueva-coleccion", response_class=HTMLResponse)
async def nueva_coleccion(request: Request):
    productos = cargar_productos_globales(modo="total_preferido")

    novedades = []
    for p in productos:
        desc = p.get("descuento")
        es_novedad = desc is None or str(desc).strip() == ""
        if es_novedad:
            novedades.append(p)

    random.shuffle(novedades)

    # OJO: tu template se llama "nuevacolecion.html" (sin doble c).
    # Si en realidad se llama "nuevacoleccion.html", cámbialo aquí.
    return templates.TemplateResponse("nuevacolecion.html", {"request": request, "articulos": novedades})


@app.get("/mujer", response_class=HTMLResponse)
async def ver_mujer(request: Request):
    productos = cargar_productos_globales(modo="total_preferido")
    articulos_mujer = []

    for p in productos:
        cat = normalizar_texto(p.get("categoria", ""))
        # soporta "camisetas_mujer", "mujer_camisetas", etc si algún día cambias
        if "mujer" in cat:
            articulos_mujer.append(p)

    random.shuffle(articulos_mujer)
    return templates.TemplateResponse("mujer.html", {"request": request, "articulos": articulos_mujer})


@app.get("/hombre", response_class=HTMLResponse)
async def ver_hombre(request: Request):
    productos = cargar_productos_globales(modo="total_preferido")
    articulos_hombre = []

    for p in productos:
        cat = normalizar_texto(p.get("categoria", ""))
        if "hombre" in cat:
            articulos_hombre.append(p)

    random.shuffle(articulos_hombre)
    return templates.TemplateResponse("hombre.html", {"request": request, "articulos": articulos_hombre})


@app.get("/buscar", response_class=HTMLResponse)
async def buscar_productos(request: Request, q: str = Query(None)):
    if not q:
        return RedirectResponse(url="/ofertas")

    termino_usuario = normalizar_texto(q)
    print(f"--- Iniciando búsqueda inteligente para: '{termino_usuario}' ---")

    # Expandir términos usando sinónimos
    terminos_a_buscar = [termino_usuario]
    for categoria_madre, sinonimos in MAPEO_CATEGORIAS.items():
        if termino_usuario == categoria_madre or termino_usuario in sinonimos:
            terminos_a_buscar.extend(sinonimos)
            terminos_a_buscar.append(categoria_madre)
    terminos_a_buscar = list(set(terminos_a_buscar))

    productos = cargar_productos_globales(modo="total_preferido")

    resultados = []
    for p in productos:
        nombre_prod = normalizar_texto(p.get("nombre", ""))
        categoria_prod = normalizar_texto(p.get("categoria", ""))

        if any(t in nombre_prod for t in terminos_a_buscar) or any(t in categoria_prod for t in terminos_a_buscar):
            resultados.append(p)

    print(f"--- Búsqueda finalizada: {len(resultados)} resultados (dedupe ya aplicado globalmente) ---")

    return templates.TemplateResponse(
        "ofertas.html",
        {"request": request, "articulos": resultados, "termino_busqueda": q},
    )
