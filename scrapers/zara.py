import asyncio
import re
from typing import Any, Dict, List, Optional, Tuple
from playwright.async_api import async_playwright


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
    # Busca un número con 2 decimales
    m = re.search(r"(\d+[\.,]\d{2})", t)
    if not m:
        return None
    num = m.group(1).replace(",", ".")
    try:
        return float(num)
    except:
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
        # quitar anchors raros
        return href.split("#")[0]
    return None


async def _aceptar_cookies_zara(page) -> None:
    # Zara suele usar OneTrust, pero no siempre aparece.
    try:
        btn = await page.query_selector("#onetrust-accept-btn-handler")
        if btn:
            await btn.click()
            await asyncio.sleep(1)
    except:
        pass


async def _scroll_hasta_fin(page, max_ciclos: int = 120, sin_cambios_max: int = 12) -> None:
    """
    Scroll real: se basa en que aumente el número de links/productos detectados en el grid.
    Para cuando no crece durante sin_cambios_max ciclos seguidos.
    """
    prev_count = 0
    sin_cambios = 0

    for ciclo in range(1, max_ciclos + 1):
        # intenta detectar productos en el grid (tolerante)
        links = await page.query_selector_all("a[href*='/es/es/'][href*='.html']")
        # Filtrado básico: que parezca ficha de producto (Zara suele tener *.html)
        hrefs = []
        for a in links:
            try:
                href = await a.get_attribute("href")
                u = _clean_url(href) if href else None
                if u and "zara.com" in u and u.endswith(".html"):
                    hrefs.append(u)
            except:
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

        # pequeña segunda bajada para forzar loads intermedios
        await page.evaluate("window.scrollBy(0, 1200)")
        await asyncio.sleep(1.4)

        if sin_cambios >= sin_cambios_max:
            break


async def _extraer_urls_listado(page) -> List[str]:
    """
    Extrae URLs de producto desde el listado, siendo tolerante a cambios de clases.
    """
    # Varias estrategias: a) selector general por href, b) grid link común
    candidatos = set()

    # a) general
    links = await page.query_selector_all("a[href*='/es/es/'][href*='.html']")
    for a in links:
        try:
            href = await a.get_attribute("href")
            u = _clean_url(href) if href else None
            if u and u.endswith(".html"):
                candidatos.add(u)
        except:
            continue

    # b) por patrones conocidos en Zara (por si cambian estructuras)
    #    (no pasa nada si no encuentra nada)
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
                if u and u.endswith(".html"):
                    candidatos.add(u)
        except:
            pass

    return list(candidatos)


async def _extraer_ficha_producto(page, url_prod: str) -> Optional[Dict[str, Any]]:
    """
    Entra en la ficha y devuelve dict si hay precio_final, si no -> None.
    """
    # Reintentos por si hay cargas incompletas
    for intento in range(1, 4):
        try:
            await page.goto(url_prod, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(2.5)

            # Nombre (Zara suele tener h1 del nombre)
            nombre = None
            for sel in ["h1", "h1.product-detail-info__header-name", "h1[data-qa='product-name']"]:
                el = await page.query_selector(sel)
                if el:
                    txt = (await el.inner_text()).strip()
                    if txt and len(txt) >= 2:
                        nombre = txt
                        break

            # Imagen principal (mejor esfuerzo)
            imagen = None
            # intenta imágenes típicas de Zara
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
                except:
                    continue

            # Precio(s): estrategia robusta
            # 1) Busca nodos típicos de precio
            textos_precio = []
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
                except:
                    continue

            # 2) Deduce valores numéricos únicos
            valores = []
            for t in textos_precio:
                val = _to_float_price(t)
                if val is not None:
                    valores.append(val)
            # únicos preservando orden
            vistos = set()
            valores_u = []
            for v in valores:
                if v not in vistos:
                    vistos.add(v)
                    valores_u.append(v)

            precio_original = None
            precio_final = None
            descuento_txt = None

            if len(valores_u) == 1:
                precio_final = valores_u[0]
            elif len(valores_u) >= 2:
                # Muchas veces aparece final y original (rebajas)
                precio_original = max(valores_u)
                precio_final = min(valores_u)

                # Si por algún motivo ambos son iguales, no hay descuento real
                if precio_original and precio_final and precio_original > precio_final:
                    pct = round(((precio_original - precio_final) / precio_original) * 100)
                    descuento_txt = f"-{pct}%"
                else:
                    precio_original = None

            # ✅ Filtro duro: si no hay precio_final, NO GUARDAR
            if not precio_final:
                return None

            # ✅ Filtro adicional: si no hay nombre, lo descartamos (para evitar basura)
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
            # Espera incremental y reintenta
            await asyncio.sleep(1.2 * intento)

    return None


async def extraer_categoria_zara(url: str, nombre_tarea: str = "desconocido") -> List[Dict[str, Any]]:
    """
    Scraper robusto de Zara:
    - Scroll hasta el final midiendo crecimiento real
    - Recoge todas las URLs del listado
    - Entra en cada producto y SOLO guarda si hay precio_final
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

            # Extraer URLs del listado
            urls = await _extraer_urls_listado(page)
            # Filtrar un poco: algunas urls pueden ser de editorial/otras cosas
            # nos quedamos con las que parezcan fichas de producto
            urls = [u for u in urls if u.startswith("https://www.zara.com/") and u.endswith(".html")]

            # Dedup
            urls = list(dict.fromkeys(urls))
            print(f"\n🏁 TOTAL URLS DETECTADAS: {len(urls)}")

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
                    print("❌ DESCARTADO (sin precio o sin nombre)")
                    continue

                ficha["categoria"] = nombre_tarea
                productos.append(ficha)
                guardados += 1
                print(f"✅ GUARDADO: {ficha['nombre'][:60]} | {ficha['precio_final']} | {ficha.get('descuento')}")

            print("\n" + "=" * 90)
            print(f"🏆 ZARA ROBUSTO COMPLETADO")
            print(f"✅ Guardados : {guardados}")
            print(f"❌ Descartados: {descartados}")
            print("=" * 90)

            await browser.close()
            return productos

        except Exception as e:
            print(f"❌ ERROR GRAVE EN ZARA: {e}")
            await browser.close()
            return []