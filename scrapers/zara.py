# scrapers/zara.py
import asyncio
import re
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright


# -----------------------------
# Helpers
# -----------------------------
def _to_float_price(text: str) -> Optional[float]:
    """
    Convierte textos tipo:
      "19,95" / "19.95" / "19,95 EUR" / "19,95€"
    a float 19.95
    """
    if not text:
        return None
    t = text.strip()
    t = t.replace("EUR", "").replace("€", "").strip()

    m = re.search(r"(\d+[\.,]\d{2})", t)
    if not m:
        return None

    num = m.group(1).replace(",", ".")
    try:
        return float(num)
    except Exception:
        return None


def _clean_url(href: str) -> Optional[str]:
    if not href:
        return None
    href = href.strip()
    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("/"):
        href = "https://www.zara.com" + href
    if href.startswith("http"):
        return href.split("#")[0]
    return None


def _is_product_url(url: str) -> bool:
    """
    Zara: ficha real de producto suele acabar con -pNNNNNNNN.html
    Ej: https://www.zara.com/es/es/camiseta-xxxx-p01234567.html
    """
    if not url:
        return False
    return bool(re.search(r"-p\d+\.html$", url))


def _product_id_from_url(url: str) -> Optional[str]:
    """
    Devuelve el id pXXXXXXXX como string, para deduplicar.
    """
    m = re.search(r"-p(\d+)\.html$", url or "")
    return m.group(1) if m else None


# -----------------------------
# Page actions
# -----------------------------
async def _aceptar_cookies_zara(page) -> None:
    # Zara suele usar OneTrust, pero no siempre aparece.
    try:
        btn = await page.query_selector("#onetrust-accept-btn-handler")
        if btn:
            await btn.click()
            await asyncio.sleep(1)
    except Exception:
        pass


async def _scroll_hasta_fin(page, max_ciclos: int = 160, sin_cambios_max: int = 14) -> None:
    """
    Scroll real: se basa en que aumente el número de *productos reales* detectados (-pXXXX.html)
    Para cuando no crece durante sin_cambios_max ciclos seguidos.
    """
    prev_count = 0
    sin_cambios = 0

    for _ciclo in range(1, max_ciclos + 1):
        # Contar SOLO URLs de producto (evita contar categorías -lXXXX.html, preowned -mkt, etc.)
        links = await page.query_selector_all("a[href*='/es/es/'][href*='.html']")
        hrefs: List[str] = []

        for a in links:
            try:
                href = await a.get_attribute("href")
                u = _clean_url(href) if href else None
                if u and _is_product_url(u):
                    hrefs.append(u)
            except Exception:
                continue

        count = len(set(hrefs))

        if count <= prev_count:
            sin_cambios += 1
        else:
            sin_cambios = 0
            prev_count = count

        # Scroll "humano" y espera a lazy-load
        await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        await asyncio.sleep(2.2)

        # Segunda bajada para forzar loads intermedios
        await page.evaluate("window.scrollBy(0, 1200)")
        await asyncio.sleep(1.4)

        if sin_cambios >= sin_cambios_max:
            break


async def _extraer_urls_listado(page) -> List[str]:
    """
    Extrae URLs de producto desde el listado.
    IMPORTANTE: solo devuelve fichas reales (-pXXXX.html).
    """
    candidatos: set[str] = set()

    # a) general por href
    links = await page.query_selector_all("a[href*='/es/es/'][href*='.html']")
    for a in links:
        try:
            href = await a.get_attribute("href")
            u = _clean_url(href) if href else None
            if u and _is_product_url(u):
                candidatos.add(u)
        except Exception:
            continue

    # b) por patrones conocidos (fallback)
    for sel in [
        "a.product-grid-product__link",
        "li.product-grid-product a",
        "a[href*='-p']",
    ]:
        try:
            links2 = await page.query_selector_all(sel)
            for a in links2:
                href = await a.get_attribute("href")
                u = _clean_url(href) if href else None
                if u and _is_product_url(u):
                    candidatos.add(u)
        except Exception:
            pass

    # devuelve como lista
    return list(candidatos)


# -----------------------------
# Product extraction
# -----------------------------
async def _extraer_ficha_producto(page, url_prod: str) -> Optional[Dict[str, Any]]:
    """
    Entra en la ficha y devuelve dict si hay precio_final + nombre.
    Si no -> None.
    """
    # Guardrail: si no es URL de producto, fuera (evita landings coladas)
    if not _is_product_url(url_prod):
        return None

    for intento in range(1, 4):
        try:
            await page.goto(url_prod, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(2.5)

            # Nombre
            nombre: Optional[str] = None
            for sel in ["h1", "h1.product-detail-info__header-name", "h1[data-qa='product-name']"]:
                el = await page.query_selector(sel)
                if el:
                    txt = (await el.inner_text()).strip()
                    if txt and len(txt) >= 2:
                        nombre = txt
                        break

            # Imagen principal (mejor esfuerzo)
            imagen: Optional[str] = None
            for sel in [
                "img.media-image__image",
                "img[data-qa='product-image']",
                "img[src*='static.zara.net']",
                "img[src*='zara.net']",
            ]:
                try:
                    await page.wait_for_selector(sel, timeout=3500)
                    imgs = await page.query_selector_all(sel)
                    for img in imgs:
                        src = await img.get_attribute("src")
                        if not src:
                            src = await img.get_attribute("data-src")
                        if src and src.startswith("http"):
                            imagen = src
                            break
                    if imagen:
                        break
                except Exception:
                    continue

            # Precio(s)
            textos_precio: List[str] = []
            for sel in [
                "span.money-amount__main",
                "span[data-qa='price-current']",
                "[data-qa='product-price']",
                "span.price",
                "span[class*='price']",
            ]:
                try:
                    els = await page.query_selector_all(sel)
                    for e in els:
                        t = (await e.inner_text()).strip()
                        if "€" in t or "EUR" in t or re.search(r"\d+[\.,]\d{2}", t):
                            textos_precio.append(t)
                except Exception:
                    continue

            # Deducir valores
            valores: List[float] = []
            for t in textos_precio:
                val = _to_float_price(t)
                if val is not None:
                    valores.append(val)

            # únicos preservando orden
            vistos = set()
            valores_u: List[float] = []
            for v in valores:
                if v not in vistos:
                    vistos.add(v)
                    valores_u.append(v)

            precio_original: Optional[float] = None
            precio_final: Optional[float] = None
            descuento_txt: Optional[str] = None

            if len(valores_u) == 1:
                precio_final = valores_u[0]
            elif len(valores_u) >= 2:
                precio_original = max(valores_u)
                precio_final = min(valores_u)

                if precio_original and precio_final and precio_original > precio_final:
                    pct = round(((precio_original - precio_final) / precio_original) * 100)
                    descuento_txt = f"-{pct}%"
                else:
                    precio_original = None

            # Filtros duros
            if not precio_final:
                return None
            if not nombre:
                return None

            return {
                "nombre": nombre,
                "imagen": imagen,
                "url_producto": url_prod,
                "precio_original": f"{precio_original:.2f}€" if precio_original else None,
                "precio_final": f"{precio_final:.2f}€",
                "descuento": descuento_txt,
            }

        except Exception:
            await asyncio.sleep(1.2 * intento)

    return None


# -----------------------------
# Public API (NO CAMBIAR NOMBRE)
# -----------------------------
async def extraer_categoria_zara(url: str, nombre_tarea: str = "desconocido") -> List[Dict[str, Any]]:
    """
    Scraper Zara:
    - Scroll hasta el final midiendo crecimiento real (solo productos -pXXXX.html)
    - Recoge URLs de producto reales
    - Entra en cada producto y SOLO guarda si hay precio_final y nombre
    """
    async with async_playwright() as p:
        print(f"\n🚀 [ZARA ROBUSTO] Scraping: {nombre_tarea}")
        print(f"🌍 URL: {url}")

        browser = await p.chromium.launch(headless=False, slow_mo=120)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        productos: List[Dict[str, Any]] = []

        try:
            # Abrir listado
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)
            await _aceptar_cookies_zara(page)

            # Scroll completo real
            print("\n🟦 SCROLL PROFUNDO HASTA FINAL (con control real)")
            await _scroll_hasta_fin(page, max_ciclos=160, sin_cambios_max=14)

            # Extraer URLs del listado (solo productos)
            urls = await _extraer_urls_listado(page)
            urls = [u for u in urls if _is_product_url(u)]

            # Dedup por product id (mejor que dedup por url literal)
            dedup: Dict[str, str] = {}
            for u in urls:
                pid = _product_id_from_url(u) or u
                if pid not in dedup:
                    dedup[pid] = u
            urls = list(dedup.values())

            print(f"\n🏁 TOTAL URLS PRODUCTO DETECTADAS: {len(urls)}")

            # Entrar uno por uno y leer ficha
            print("\n🟦 LEYENDO FICHAS (solo guarda si hay precio)")
            total = len(urls)
            guardados = 0
            descartados = 0

            for i, url_prod in enumerate(urls, start=1):
                print(f"\n--- 🛒 PRODUCTO {i}/{total} ---")
                print(f"➡️ {url_prod}")

                ficha = await _extraer_ficha_producto(page, url_prod)
                if not ficha:
                    descartados += 1
                    print("❌ DESCARTADO (sin precio o sin nombre / o no era producto real)")
                    continue

                ficha["categoria"] = nombre_tarea
                productos.append(ficha)
                guardados += 1
                print(f"✅ GUARDADO: {ficha['nombre'][:60]} | {ficha['precio_final']} | {ficha.get('descuento')}")

            print("\n" + "=" * 90)
            print("🏆 ZARA ROBUSTO COMPLETADO")
            print(f"✅ Guardados : {guardados}")
            print(f"❌ Descartados: {descartados}")
            print("=" * 90)

            await browser.close()
            return productos

        except Exception as e:
            print(f"❌ ERROR GRAVE EN ZARA: {e}")
            await browser.close()
            return []