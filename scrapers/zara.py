import asyncio
import re
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright


def limpiar_precio(txt: str):
    """
    Devuelve float con el precio encontrado en un texto (ej: '19,95' o '19.95' o '19,95 EUR').
    """
    if not txt:
        return None
    t = txt.replace("EUR", "").replace("€", "").strip()
    m = re.search(r"(\d+[\.,]\d{2})", t)
    if not m:
        return None
    return float(m.group(1).replace(",", "."))


def es_url_producto_zara(url: str) -> bool:
    """
    En Zara, un producto real suele llevar '-p' en el path (ej: ...-p01234567.html).
    Listas/categorías suelen llevar '-l' (ej: ...-l855.html) y NO son producto.
    """
    try:
        path = urlparse(url).path.lower()
    except Exception:
        return False

    if "-p" not in path:
        return False
    # Normalmente los listados llevan -l####.html, historias también.
    if "-l" in path:
        return False
    return True


def coincide_seccion(url: str, nombre_tarea: str) -> bool:
    """
    Si la tarea es de hombre, rechazamos mujer (y viceversa).
    No “ata” a camisetas: solo a la sección.
    """
    u = url.lower()
    tarea = (nombre_tarea or "").lower()

    if "hombre" in tarea and "/mujer-" in u:
        return False
    if "mujer" in tarea and "/hombre-" in u:
        return False
    return True


async def extraer_categoria_zara(url_categoria: str, nombre_tarea: str = "desconocido"):
    async with async_playwright() as p:
        print(f"\n🚀 [ZARA] Scraping: {nombre_tarea}")
        print(f"🌍 URL categoría: {url_categoria}\n")

        browser = await p.chromium.launch(headless=False, slow_mo=120)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(url_categoria, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(2.5)

            # Cookies (OneTrust)
            try:
                btn = await page.wait_for_selector("#onetrust-accept-btn-handler", timeout=6000)
                await btn.click()
                print("✅ Cookies aceptadas\n")
                await asyncio.sleep(1.5)
            except:
                print("ℹ️ Cookies no detectadas / ya aceptadas\n")

            # ============================
            # FASE 1: SCROLL + RECOGER URLS (SOLO PRODUCTOS '-p')
            # ============================
            print("🟦 FASE 1 — Recolectando URLs de PRODUCTO (solo '-p')\n")

            urls = []
            vistos = set()
            intentos_sin_nuevos = 0
            scroll_n = 0

            # Un selector razonable del grid (Zara lo suele usar):
            selector_links = "li.product-grid-product a.product-grid-product__link"

            while True:
                scroll_n += 1

                # Recoger links del grid
                links = await page.query_selector_all(selector_links)
                nuevos_esta_vuelta = 0

                for a in links:
                    href = await a.get_attribute("href")
                    if not href:
                        continue

                    url_abs = href if href.startswith("http") else urljoin("https://www.zara.com", href)

                    # filtros duros
                    if not es_url_producto_zara(url_abs):
                        continue
                    if not coincide_seccion(url_abs, nombre_tarea):
                        continue

                    if url_abs not in vistos:
                        vistos.add(url_abs)
                        urls.append(url_abs)
                        nuevos_esta_vuelta += 1

                print(f"🔄 Scroll #{scroll_n} | URLs producto: {len(urls)} | +{nuevos_esta_vuelta}")

                # scroll hacia abajo para forzar carga
                await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                await asyncio.sleep(2.2)

                if nuevos_esta_vuelta == 0:
                    intentos_sin_nuevos += 1
                    print(f"⚠️ Sin nuevos productos ({intentos_sin_nuevos}/10)\n")
                else:
                    intentos_sin_nuevos = 0

                if intentos_sin_nuevos >= 10:
                    print("🛑 Final de carga detectado (sin nuevos productos)\n")
                    break

            print(f"🏁 TOTAL URLs de producto finales: {len(urls)}\n")

            # ============================
            # FASE 2: ENTRAR EN CADA PRODUCTO Y SACAR DATOS
            # ============================
            print("🟦 FASE 2 — Leyendo fichas de producto uno a uno\n")

            productos = []
            guardados = 0
            total = len(urls)

            for i, url_prod in enumerate(urls, start=1):
                print("-" * 80)
                print(f"--- 🛒 PRODUCTO {i}/{total} ---")
                print(f"➡️ {url_prod}")

                try:
                    await page.goto(url_prod, wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(2.2)

                    # NOMBRE
                    nombre = None
                    for sel in ["h1", "h3"]:
                        el = await page.query_selector(sel)
                        if el:
                            txt = (await el.inner_text()).strip()
                            if txt and len(txt) >= 3:
                                nombre = txt
                                break

                    # IMAGEN PRINCIPAL (primera que parezca válida)
                    imagen = None
                    try:
                        await page.wait_for_selector("img", timeout=8000)
                        imgs = await page.query_selector_all("img")
                        for img in imgs:
                            src = await img.get_attribute("src") or await img.get_attribute("data-src")
                            if not src:
                                continue
                            if src.startswith("//"):
                                src = "https:" + src
                            if src.startswith("http") and "static.zara.net" in src:
                                imagen = src
                                break
                    except:
                        pass

                    # PRECIOS
                    valores = []

                    # Selectores frecuentes de Zara para precio
                    price_nodes = await page.query_selector_all("span.money-amount__main, span.money-amount__main__value, span.money-amount")
                    for n in price_nodes:
                        try:
                            t = (await n.inner_text()).strip()
                        except:
                            continue
                        v = limpiar_precio(t)
                        if v is not None:
                            valores.append(v)

                    # Dedup preservando orden
                    valores_unicos = []
                    for v in valores:
                        if v not in valores_unicos:
                            valores_unicos.append(v)

                    precio_original = None
                    precio_final = None
                    descuento_txt = None

                    if len(valores_unicos) == 1:
                        precio_final = valores_unicos[0]
                    elif len(valores_unicos) >= 2:
                        precio_original = max(valores_unicos)
                        precio_final = min(valores_unicos)
                        if precio_original and precio_final and precio_original > 0 and precio_original > precio_final:
                            pct = round(((precio_original - precio_final) / precio_original) * 100)
                            descuento_txt = f"-{pct}%"

                    # REGLA: SOLO GUARDAR SI HAY PRECIO FINAL (y nombre)
                    if not nombre or precio_final is None:
                        print("❌ DESCARTADO (sin nombre o sin precio)")
                        continue

                    item = {
                        "nombre": nombre,
                        "imagen": imagen,
                        "url_producto": url_prod,
                        "precio_original": f"{precio_original:.2f}€" if precio_original else None,
                        "precio_final": f"{precio_final:.2f}€",
                        "descuento": descuento_txt,
                        "categoria": nombre_tarea
                    }

                    productos.append(item)
                    guardados += 1
                    print(f"📦 GUARDADO #{guardados} | 💶 {item['precio_final']}")

                except Exception as e:
                    print(f"🔥 ERROR EN PRODUCTO: {e}")
                    continue

            print("\n" + "=" * 80)
            print(f"🏆 ZARA COMPLETADO: {guardados} productos guardados (con precio)")
            print("=" * 80 + "\n")

            await browser.close()
            return productos

        except Exception as e:
            print(f"❌ ERROR GRAVE EN ZARA: {e}")
            await browser.close()
            return []