import asyncio
import json
import re
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl, urlencode

from playwright.async_api import async_playwright

# ==========================================
# UTILS
# ==========================================

PRODUCT_URL_RE = re.compile(r"/es/.*-c0p\d+\.html", re.IGNORECASE)

def _safe_json_loads(s: str):
    try:
        return json.loads(s)
    except:
        return None

def normalizar_url(href: str) -> str | None:
    if not href:
        return None
    return href if href.startswith("http") else urljoin("https://www.bershka.com", href)

def es_url_producto_bershka(url: str) -> bool:
    try:
        u = urlparse(url)
        if "bershka.com" not in u.netloc:
            return False
        return bool(PRODUCT_URL_RE.search(u.path))
    except:
        return False

def canonizar_url_producto(url: str) -> str:
    """
    Quita params ruidosos para deduplicar (dejamos colorId si quieres, aquí lo quitamos).
    """
    u = urlparse(url)
    # Conserva solo path y query mínima (si quieres mantener colorId, filtra aquí)
    # En dedupe suele ser mejor quitar todo query:
    return urlunparse((u.scheme, u.netloc, u.path, "", "", ""))

def limpiar_precio_a_float(texto: str):
    if not texto:
        return None
    m = re.search(r"(\d+[\.,]\d{2})", texto)
    if not m:
        return None
    return float(m.group(1).replace(",", "."))

def formatear_precio(valor_float):
    return f"{valor_float:.2f}€" if valor_float is not None else None

def genero_esperado(nombre_tarea: str) -> str | None:
    if nombre_tarea.startswith("hombre_"):
        return "hombre"
    if nombre_tarea.startswith("mujer_"):
        return "mujer"
    return None

def valida_genero_por_url(url_producto: str, nombre_tarea: str) -> bool:
    g = genero_esperado(nombre_tarea)
    if not g:
        return True
    u = (url_producto or "").lower()
    # Bershka suele incluir /hombre/ o /mujer/ en fichas; si no, no descartamos agresivo:
    if "/hombre/" in u:
        return g == "hombre"
    if "/mujer/" in u:
        return g == "mujer"
    return True  # no concluyente -> no tiramos

def valida_genero_por_titulo(nombre: str, nombre_tarea: str) -> bool:
    g = genero_esperado(nombre_tarea)
    if not g:
        return True
    t = (nombre or "").lower()
    # OG title suele traer "- Hombre" / "- Mujer" / "#bershkastyle - Hombre"
    if " - hombre" in t:
        return g == "hombre"
    if " - mujer" in t:
        return g == "mujer"
    return True  # no concluyente -> no tiramos

# ==========================================
# EXTRAER DETALLE (PRODUCT PAGE)
# ==========================================

async def extraer_detalle_producto(page, url_producto: str, nombre_tarea: str):
    await page.goto(url_producto, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(0.8)

    nombre = None
    imagen = None
    precio_final = None

    # OG tags
    try:
        og_img = await page.query_selector('meta[property="og:image"]')
        if og_img:
            imagen = await og_img.get_attribute("content")
    except:
        pass

    try:
        og_title = await page.query_selector('meta[property="og:title"]')
        if og_title:
            nombre = await og_title.get_attribute("content")
    except:
        pass

    # JSON-LD Product
    try:
        scripts = await page.query_selector_all('script[type="application/ld+json"]')
        for sc in scripts:
            txt = await sc.inner_text()
            data = _safe_json_loads(txt)
            if not data:
                continue

            candidates = data if isinstance(data, list) else [data]

            expanded = []
            for obj in candidates:
                if isinstance(obj, dict) and "@graph" in obj and isinstance(obj["@graph"], list):
                    expanded.extend(obj["@graph"])
                else:
                    expanded.append(obj)

            for obj in expanded:
                if not isinstance(obj, dict):
                    continue
                t = obj.get("@type")
                es_product = (t == "Product") or (isinstance(t, list) and "Product" in t)
                if not es_product:
                    continue

                if not nombre:
                    nombre = obj.get("name") or nombre

                if not imagen:
                    img = obj.get("image")
                    if isinstance(img, str):
                        imagen = img
                    elif isinstance(img, list) and img:
                        imagen = img[0]

                offers = obj.get("offers")
                if isinstance(offers, dict):
                    p = offers.get("price")
                    if p is not None:
                        try:
                            precio_final = float(str(p).replace(",", "."))
                        except:
                            pass

                if nombre and precio_final is not None:
                    break

            if nombre and precio_final is not None:
                break
    except:
        pass

    # fallback precio
    if precio_final is None:
        try:
            body_txt = await page.inner_text("body")
            m = re.search(r"(\d+[\.,]\d{2})\s*€", body_txt)
            if m:
                precio_final = float(m.group(1).replace(",", "."))
        except:
            pass

    if not nombre or precio_final is None:
        return None

    # Validación género (SUAVE, no filtra por "camiseta"; solo evita mezcla Hombre/Mujer si se puede)
    if not valida_genero_por_titulo(nombre, nombre_tarea):
        return None
    if not valida_genero_por_url(url_producto, nombre_tarea):
        return None

    if imagen and not (imagen.startswith("http://") or imagen.startswith("https://")):
        imagen = None

    return {
        "nombre": nombre.strip(),
        "imagen": imagen,
        "url_producto": url_producto,
        "precio_original": None,
        "precio_final": formatear_precio(precio_final),
        "descuento": None,
        "categoria": nombre_tarea,
    }

# ==========================================
# SCRAPER CATEGORÍA (CORRECTO: SOLO GRID)
# ==========================================

async def extraer_categoria_bershka(url, nombre_tarea="desconocido", headless=False, max_productos=None):
    """
    Cambios clave respecto a tu versión:
    1) NO recolecta <a> de toda la página: solo dentro del GRID principal de productos.
    2) El fin del scroll se decide por crecimiento de "cards" / links del grid, no por links globales.
    3) Dedupe por URL canónica (sin query) para evitar stylismId/params duplicados.
    4) Validación suave de género en la ficha para evitar mezcla Hombre/Mujer.
    """
    async with async_playwright() as p:
        print("\n" + "=" * 70)
        print("🚀 BERSHKA SCRAPER (GRID DE CATEGORÍA)")
        print(f"📂 Categoría: {nombre_tarea}")
        print(f"🌍 URL: {url}")
        print("=" * 70)

        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Cookies
            try:
                await page.wait_for_selector("#onetrust-accept-btn-handler", timeout=8000)
                await page.click("#onetrust-accept-btn-handler", force=True)
                print("🍪 Cookies aceptadas")
                await asyncio.sleep(1.0)
            except:
                pass

            # ==========================================
            # 0) LOCALIZAR GRID PRINCIPAL (robusto)
            # ==========================================
            # Estrategia: probar varios selectores típicos y quedarse con el primero visible
            grid_selectors = [
                # comunes en ecoms/Inditex (pueden variar; por eso probamos varios)
                '[data-testid*="product-grid"]',
                '[data-testid*="productGrid"]',
                '[data-testid*="products-grid"]',
                '[data-testid*="product-list"]',
                'main section:has(a[href*="-c0p"])',
                'main:has(a[href*="-c0p"])',
            ]

            grid = None
            for sel in grid_selectors:
                try:
                    loc = page.locator(sel).first
                    if await loc.count() > 0 and await loc.is_visible():
                        grid = loc
                        break
                except:
                    continue

            # Fallback final: main
            if grid is None:
                grid = page.locator("main").first

            print("🧩 Grid localizado (modo robusto)")

            # ==========================================
            # 1) SCROLL Y RECOGER LINKS SOLO DEL GRID
            # ==========================================
            vistos_links = set()
            sin_nuevos = 0
            intentos_max = 8
            vuelta = 0

            while True:
                vuelta += 1
                print("\n" + "-" * 60)
                print(f"🔄 SCROLL GRID #{vuelta}")
                print("-" * 60)

                # Links solo dentro del grid
                anchors = grid.locator('a[href]')
                count = await anchors.count()

                nuevos = 0
                for i in range(count):
                    href = await anchors.nth(i).get_attribute("href")
                    full = normalizar_url(href)
                    if not full or not es_url_producto_bershka(full):
                        continue

                    full_canon = canonizar_url_producto(full)
                    if full_canon not in vistos_links:
                        vistos_links.add(full_canon)
                        nuevos += 1

                print(f"🔗 Links PRODUCTO (GRID): {len(vistos_links)} | nuevos: {nuevos}")

                if nuevos == 0:
                    sin_nuevos += 1
                    print(f"⚠ Sin nuevos (grid) ({sin_nuevos}/{intentos_max})")
                else:
                    sin_nuevos = 0

                if max_productos and len(vistos_links) >= max_productos:
                    print("\n🛑 FIN (max_productos alcanzado)")
                    break

                if sin_nuevos >= intentos_max:
                    print("\n🛑 FIN (grid no crece más)")
                    break

                # Scroll: mejor bajar el viewport y también intentar scroll al final del grid
                try:
                    await page.mouse.wheel(0, 3200)
                except:
                    pass
                await asyncio.sleep(1.8)

            links = list(vistos_links)

            # ==========================================
            # 2) DETALLE PRODUCTO
            # ==========================================
            productos = []
            vistos_producto = set()

            detalle_page = await context.new_page()

            for link in links:
                if max_productos and len(productos) >= max_productos:
                    break
                try:
                    data = await extraer_detalle_producto(detalle_page, link, nombre_tarea)
                    if not data:
                        continue

                    # Validación final por patrón (por si hay redirects raros)
                    if not es_url_producto_bershka(data["url_producto"]):
                        continue

                    # Dedupe por url canónica (mejor que nombre|url con query)
                    key = canonizar_url_producto(data["url_producto"])
                    if key in vistos_producto:
                        continue
                    vistos_producto.add(key)

                    productos.append(data)

                    if len(productos) <= 10 or len(productos) % 20 == 0:
                        print(f"📦 [{len(productos)}] {data['nombre'][:55]} | {data['precio_final']}")
                except:
                    continue

            await detalle_page.close()

            print("\n" + "=" * 70)
            print(f"🏆 TOTAL PRODUCTOS BERSHKA: {len(productos)}")
            print("=" * 70)

            await browser.close()
            return productos

        except Exception as e:
            print(f"\n❌ ERROR EN BERSHKA: {e}")
            await browser.close()
            return []