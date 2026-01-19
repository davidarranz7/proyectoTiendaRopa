import asyncio
from playwright.async_api import async_playwright

async def extraer_categoria_pull(url, nombre_tarea="desconocido"):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=300
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        page = await context.new_page()

        try:
            print(f"🌍 [PULL] Entrando en: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)

            cookies_aceptadas = False
            try:
                for _ in range(3):
                    await page.keyboard.press("Tab")
                    await asyncio.sleep(0.3)
                await page.keyboard.press("Enter")
                await asyncio.sleep(2)
                cookies_aceptadas = True
                print("✅ Cookies aceptadas correctamente.")
            except:
                pass

            if not cookies_aceptadas:
                print("⚠️ NO se pudieron aceptar las cookies.")

            print("🚜 Iniciando recolección de productos...")

            productos_lista = []
            vistos = set()
            intentos_sin_nuevos = 0

            while True:
                elementos = await page.query_selector_all(
                    "article, div[class*='product'], div[class*='Product']"
                )

                nuevos = 0

                for el in elementos:
                    try:
                        nombre_el = await el.query_selector(
                            "h2, .product-name, [class*='name']"
                        )
                        if not nombre_el:
                            continue

                        nombre = (await nombre_el.inner_text()).strip()

                        if len(nombre) < 5:
                            continue
                        if "pull" in nombre.lower() or "bear" in nombre.lower():
                            continue
                        if nombre in vistos:
                            continue

                        link_el = await el.query_selector("a")
                        href = await link_el.get_attribute("href") if link_el else None

                        if not href or "/es/" not in href:
                            continue

                        url_producto = (
                            href if href.startswith("http")
                            else f"https://www.pullandbear.com{href}"
                        )

                        await el.scroll_into_view_if_needed()

                        imagen = None
                        for _ in range(8):
                            img_el = await el.query_selector("img")
                            if img_el:
                                src = await img_el.get_attribute("src")
                                if src and src.startswith("http") and not src.endswith(".svg"):
                                    imagen = src
                                    break
                            await asyncio.sleep(0.4)

                        if not imagen:
                            continue

                        precio_original = None
                        precio_rebajado = None
                        precio_final = None
                        descuento = None

                        precios = await el.query_selector_all(
                            "[class*='price'], [class*='Price'], span"
                        )

                        textos_precio = []
                        for p in precios:
                            txt = (await p.inner_text()).strip()
                            if "€" in txt or "EUR" in txt:
                                textos_precio.append(txt)

                        textos_precio = list(dict.fromkeys(textos_precio))

                        if len(textos_precio) == 1:
                            precio_final = textos_precio[0]
                        elif len(textos_precio) == 2:
                            precio_original, precio_final = textos_precio
                        elif len(textos_precio) >= 3:
                            precio_original, precio_rebajado, precio_final = textos_precio[:3]

                        if not precio_final:
                            continue

                        badge = await el.query_selector(
                            "[class*='discount'], [class*='rebaja'], [class*='%']"
                        )
                        if badge:
                            descuento = (await badge.inner_text()).strip()

                        productos_lista.append({
                            "nombre": nombre,
                            "imagen": imagen,
                            "url_producto": url_producto,
                            "precio_original": precio_original,
                            "precio_rebajado": precio_rebajado,
                            "descuento": descuento,
                            "precio_final": precio_final,
                            "categoria": nombre_tarea
                        })

                        vistos.add(nombre)
                        nuevos += 1

                        if len(productos_lista) % 10 == 0:
                            print(f"📦 Procesados {len(productos_lista)} productos...")

                    except:
                        continue

                if nuevos == 0:
                    intentos_sin_nuevos += 1
                else:
                    intentos_sin_nuevos = 0

                await page.evaluate("window.scrollBy(0, 600)")
                await asyncio.sleep(2)

                fin_scroll = await page.evaluate(
                    "window.innerHeight + window.scrollY >= document.body.scrollHeight"
                )

                if intentos_sin_nuevos >= 5 and fin_scroll:
                    break

            print(f"🏆 FINALIZADO: {len(productos_lista)} productos reales.")
            await browser.close()
            return productos_lista

        except Exception as e:
            print(f"❌ Error en Pull&Bear: {e}")
            await browser.close()
            return []