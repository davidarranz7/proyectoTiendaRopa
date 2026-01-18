import asyncio
from playwright.async_api import async_playwright

async def extraer_categoria_mango(url, nombre_tarea="desconocido"):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
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
            print(f"🌍 [MANGO] Entrando en: {url}")
            await page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(5)

            # ======================
            # ACEPTAR COOKIES
            # ======================
            cookies_aceptadas = False
            try:
                print("🍪 Método alternativo: TAB + ENTER...")
                for _ in range(3):
                    await page.keyboard.press("Tab")
                    await asyncio.sleep(0.3)
                await page.keyboard.press("Enter")
                await asyncio.sleep(2)
                cookies_aceptadas = True
                print("✅ Cookies aceptadas con TAB + ENTER")
            except:
                pass
            if not cookies_aceptadas:
                print("⚠️ NO se pudieron aceptar las cookies.")

            # ======================
            # SCRAPING PRINCIPAL
            # ======================
            productos_lista = []
            vistos = set()
            intentos_sin_nuevos = 0

            print("⏳ Esperando productos de Mango...")
            while True:
                # Ahora los productos están en role="listitem"
                elementos = await page.query_selector_all("div[role='listitem']")

                nuevos = 0
                for el in elementos:
                    try:
                        # Nombre
                        nombre_el = await el.query_selector("span[data-testid='product-name']")
                        if not nombre_el:
                            continue
                        nombre = (await nombre_el.inner_text()).strip()
                        if len(nombre) < 3 or nombre in vistos:
                            continue
                        vistos.add(nombre)
                        nuevos += 1

                        # URL
                        link_el = await el.query_selector("a")
                        href = await link_el.get_attribute("href") if link_el else None
                        if not href:
                            continue
                        url_producto = href if href.startswith("http") else f"https://shop.mango.com{href}"

                        # Imagen
                        imagen = ""
                        img_el = await el.query_selector("img")
                        if img_el:
                            for _ in range(8):
                                src = await img_el.get_attribute("src")
                                if src and src.startswith("http") and not src.endswith(".svg"):
                                    imagen = src
                                    break
                                await asyncio.sleep(0.3)

                        # Precios
                        precio_original = None
                        precio_rebajado = None
                        precio_final = None
                        descuento = None

                        precios_el = await el.query_selector_all("span[data-testid='product-price']")
                        textos_precio = [(await p.inner_text()).strip() for p in precios_el]
                        textos_precio = list(dict.fromkeys(textos_precio))

                        if len(textos_precio) == 1:
                            precio_final = textos_precio[0]
                        elif len(textos_precio) == 2:
                            precio_original, precio_final = textos_precio
                        elif len(textos_precio) >= 3:
                            precio_original, precio_rebajado, precio_final = textos_precio[:3]

                        # Descuento
                        badge_el = await el.query_selector("span[data-testid='product-discount']")
                        descuento = (await badge_el.inner_text()).strip() if badge_el else None

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

                        if len(productos_lista) % 10 == 0:
                            print(f"📦 Procesados {len(productos_lista)} productos...")

                    except:
                        continue

                if nuevos == 0:
                    intentos_sin_nuevos += 1
                else:
                    intentos_sin_nuevos = 0

                # Scroll lento
                await page.evaluate("window.scrollBy(0, 600)")
                await asyncio.sleep(2)

                fin_scroll = await page.evaluate(
                    "window.innerHeight + window.scrollY >= document.body.scrollHeight"
                )

                if intentos_sin_nuevos >= 5 and fin_scroll:
                    break

            print(f"🏆 MANGO FINALIZADO: {len(productos_lista)} productos reales.")
            await browser.close()
            return productos_lista

        except Exception as e:
            print(f"❌ Error en Mango: {e}")
            await browser.close()
            return []
