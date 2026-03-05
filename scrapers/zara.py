import asyncio
import re
from playwright.async_api import async_playwright


def limpiar_precio(txt):
    try:
        txt = txt.replace("EUR", "").replace("€", "").strip()
        return float(txt.replace(",", "."))
    except:
        return None


async def extraer_categoria_zara(url, nombre_tarea="desconocido"):
    async with async_playwright() as p:
        print(f"\n🚀 [ZARA PRODUCCIÓN DEFINITIVA] Scraping: {nombre_tarea}")
        print(f"🌍 URL: {url}")

        browser = await p.chromium.launch(headless=False, slow_mo=150)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # --- ABRIR CATEGORÍA ---
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)

            # --- COOKIES ---
            try:
                boton = await page.wait_for_selector("#onetrust-accept-btn-handler", timeout=5000)
                await boton.click()
                print("✅ Cookies aceptadas")
                await asyncio.sleep(2)
            except:
                print("⚠️ Cookies no detectadas o ya aceptadas")

            # ============================================================
            # 🟦 FASE 1 — SCROLL + RECOGER TODAS LAS URLS
            # ============================================================

            print("\n🟦 FASE 1 — RECOGIENDO TODAS LAS URLS\n")

            urls = []
            vistos = set()
            intentos_sin_cambios = 0
            scroll = 0

            while True:
                scroll += 1
                print(f"🔄 Scroll #{scroll}")

                bloques = await page.query_selector_all("li.product-grid-product a.product-grid-product__link")

                for a in bloques:
                    href = await a.get_attribute("href")
                    if not href:
                        continue

                    url_producto = href if href.startswith("http") else f"https://www.zara.com{href}"

                    if url_producto not in vistos:
                        vistos.add(url_producto)
                        urls.append(url_producto)

                print(f"🔗 URLs detectadas hasta ahora: {len(urls)}")

                # Scroll profundo real
                await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                await asyncio.sleep(3)

                # Control de fin real  🔥 AQUÍ EL ÚNICO CAMBIO (6 → 10)
                if len(urls) == len(vistos):
                    intentos_sin_cambios += 1
                    print(f"⚠️ Sin cambios ({intentos_sin_cambios}/10)")
                else:
                    intentos_sin_cambios = 0

                if intentos_sin_cambios >= 10:
                    print("\n🛑 FINAL DE CARGA DE CATEGORÍA ALCANZADO")
                    break

            print(f"\n🏁 TOTAL URLS FINALES: {len(urls)}\n")

            # ============================================================
            # 🟦 FASE 2 — ENTRAR UNO A UNO Y LEER FICHA
            # ============================================================

            print("\n🟦 FASE 2 — LEYENDO PRODUCTOS UNO A UNO\n")

            productos = []

            total = len(urls)
            num = 0

            for url_prod in urls:
                num += 1
                print("\n" + "-" * 90)
                print(f"🛒 PRODUCTO #{num}/{total}")
                print(f"➡️ Entrando en: {url_prod}")
                print("-" * 90)

                try:
                    await page.goto(url_prod, wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(3)

                    # -------------------------------
                    # NOMBRE
                    # -------------------------------
                    nombre = None
                    try:
                        h3 = await page.query_selector("h1, h3")
                        nombre = (await h3.inner_text()).strip()
                    except:
                        pass

                    print(f"📝 Nombre: {nombre}")

                    # -------------------------------
                    # IMAGEN PRINCIPAL (CORRECTA)
                    # -------------------------------
                    imagen = None

                    try:
                        await page.wait_for_selector("img.media-image__image", timeout=8000)
                        imgs = await page.query_selector_all("img.media-image__image")

                        for img in imgs:
                            src = await img.get_attribute("src")
                            if not src:
                                src = await img.get_attribute("data-src")

                            if src and src.startswith("http"):
                                imagen = src
                                break
                    except:
                        pass

                    print(f"🖼️ Imagen: {imagen}")

                    # -------------------------------
                    # PRECIOS
                    # -------------------------------
                    valores = []

                    nodos = await page.query_selector_all("span.money-amount__main")

                    print(f"💰 Nodos de precio encontrados: {len(nodos)}")

                    for n in nodos:
                        txt = await n.inner_text()
                        val = limpiar_precio(txt)
                        if val:
                            valores.append(val)
                            print(f"   ➕ Precio detectado: {val}")

                    valores = list(dict.fromkeys(valores))

                    precio_original = None
                    precio_final = None
                    descuento_txt = None

                    if len(valores) == 1:
                        precio_final = valores[0]
                    elif len(valores) >= 2:
                        precio_original = max(valores)
                        precio_final = min(valores)
                        pct = round(((precio_original - precio_final) / precio_original) * 100)
                        descuento_txt = f"-{pct}%"

                    print(f"💶 Precio final   : {precio_final}")
                    print(f"💶 Precio original: {precio_original}")
                    print(f"🏷️ Descuento      : {descuento_txt}")

                    if not precio_final or not nombre:
                        print("❌ PRODUCTO DESCARTADO (sin datos suficientes)")
                        continue

                    productos.append({
                        "nombre": nombre,
                        "imagen": imagen,
                        "url_producto": url_prod,
                        "precio_original": f"{precio_original:.2f}€" if precio_original else None,
                        "precio_final": f"{precio_final:.2f}€",
                        "descuento": descuento_txt,
                        "categoria": nombre_tarea
                    })

                    print("✅ PRODUCTO GUARDADO CORRECTAMENTE")

                except Exception as e:
                    print(f"🔥 ERROR EN PRODUCTO: {e}")
                    continue

            print("\n" + "=" * 90)
            print(f"🏆 ZARA CLICK COMPLETADO: {len(productos)} productos reales finales")
            print("=" * 90)

            await browser.close()
            return productos

        except Exception as e:
            print(f"❌ ERROR GRAVE EN ZARA: {e}")
            await browser.close()
            return []
