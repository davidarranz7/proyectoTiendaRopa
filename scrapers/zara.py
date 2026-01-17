import asyncio
from playwright.async_api import async_playwright


async def extraer_categoria_zara(url, nombre_tarea="desconocido"):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Aceptar cookies
            try:
                boton = await page.wait_for_selector("#onetrust-accept-btn-handler", timeout=5000)
                await boton.click()
                await asyncio.sleep(2)
            except:
                pass

            # Scroll infinito
            previous_count = 0
            while True:
                elementos = await page.query_selector_all("li[class*='product']")
                if len(elementos) == previous_count: break
                previous_count = len(elementos)
                await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                await asyncio.sleep(1.5)

            productos_lista = []
            vistos = set()

            for el in elementos:
                try:
                    # 1. Asegurar que el producto entra en pantalla para cargar la imagen
                    await el.scroll_into_view_if_needed()

                    nombre_el = await el.query_selector("h2, .product-grid-product-info__name")
                    if not nombre_el: continue
                    nombre = (await nombre_el.inner_text()).strip()
                    if nombre in vistos: continue

                    # 2. CAPTURA DEL ENLACE (URL del producto)
                    link_el = await el.query_selector("a")
                    href = await link_el.get_attribute("href") if link_el else ""
                    # Si el link es relativo (/es/es/producto...), le pegamos el dominio
                    url_completa = href if href.startswith("http") else f"https://www.zara.com{href}"

                    # 3. CAPTURA DE IMAGEN (Con espera de carga real)
                    imagen = ""
                    for _ in range(8):  # Intentamos durante 4 segundos (8 * 0.5s)
                        img_el = await el.query_selector("img")
                        if img_el:
                            src = await img_el.get_attribute("src")
                            if src and "transparent-background" not in src and "http" in src:
                                imagen = src
                                break
                        await asyncio.sleep(0.5)

                    # 4. CAPTURA DE PRECIOS
                    nodos_precio = await el.query_selector_all(".money-amount__main")
                    textos_precio = [(await p.inner_text()).strip() for p in nodos_precio]

                    p_original = p_intermedio = p_final = None
                    if len(textos_precio) == 1:
                        p_final = textos_precio[0]
                    elif len(textos_precio) == 2:
                        p_original, p_final = textos_precio
                    elif len(textos_precio) >= 3:
                        p_original, p_intermedio, p_final = textos_precio[:3]

                    # 5. DESCUENTO
                    badge = await el.query_selector("[class*='discount'], .discount-badge")
                    descuento = (await badge.inner_text()).strip() if badge else None

                    productos_lista.append({
                        "nombre": nombre,
                        "imagen": imagen,
                        "url_producto": url_completa,
                        "precio_original": p_original,
                        "precio_rebajado": p_intermedio,
                        "descuento": descuento,
                        "precio_final": p_final,
                        "categoria": nombre_tarea
                    })
                    vistos.add(nombre)
                    if len(productos_lista) % 10 == 0:
                        print(f"📦 Procesados {len(productos_lista)} productos...")

                except:
                    continue

            await browser.close()
            return productos_lista

        except Exception as e:
            print(f"❌ Error: {e}")
            await browser.close()
            return []