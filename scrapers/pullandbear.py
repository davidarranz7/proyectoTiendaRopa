import asyncio
import re
from playwright.async_api import async_playwright


def limpiar_precio(texto):
    """Extrae el precio numérico evitando pegar números de IDs cercanos."""
    try:
        match = re.search(r'(\d+[\.,]\d{2})', texto)
        if match:
            valor = match.group(1).replace(',', '.')
            return float(valor)
        return None
    except:
        return None


async def extraer_categoria_pull(url, nombre_tarea="desconocido"):
    async with async_playwright() as p:
        print(f"\n🚀 [PULL] Iniciando con tu configuración de cookies...")
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"🌍 [PULL] Entrando en: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)

            # --- TU BLOQUE DE COOKIES ORIGINAL ---
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

            productos_lista = []
            vistos = set()
            intentos_sin_nuevos = 0

            # --- RECOLECCIÓN DE PRODUCTOS CON SCROLL MEJORADO ---
            while True:
                elementos = await page.query_selector_all("article, div[class*='product'], div[class*='Product']")
                nuevos_en_esta_vuelta = 0

                for el in elementos:
                    try:
                        nombre_el = await el.query_selector("h2, .product-name, [class*='name']")
                        if not nombre_el: continue
                        nombre = (await nombre_el.inner_text()).strip()

                        if len(nombre) < 5 or nombre in vistos: continue

                        # PRECIOS
                        precios_elementos = await el.query_selector_all("[class*='price'], [class*='Price'], span")
                        valores_numericos = []
                        for p_el in precios_elementos:
                            t = await p_el.inner_text()
                            if "€" in t:
                                val = limpiar_precio(t)
                                if val: valores_numericos.append(val)

                        valores_numericos = list(dict.fromkeys(valores_numericos))
                        precio_original, precio_final, descuento_txt = None, None, None

                        if len(valores_numericos) == 1:
                            precio_final = valores_numericos[0]
                        elif len(valores_numericos) >= 2:
                            val_max, val_min = max(valores_numericos), min(valores_numericos)
                            if val_max > (val_min * 6):
                                precio_final = val_min
                            else:
                                precio_original, precio_final = val_max, val_min
                                pct = round(((precio_original - precio_final) / precio_original) * 100)
                                descuento_txt = f"-{pct}%"

                        if not precio_final: continue

                        # IMAGEN Y LINK
                        link_el = await el.query_selector("a")
                        href = await link_el.get_attribute("href")

                        # Forzamos la carga de la imagen haciendo scroll al elemento
                        await el.scroll_into_view_if_needed()
                        img_el = await el.query_selector("img")
                        imagen = await img_el.get_attribute("src") if img_el else None

                        if not imagen or not href: continue

                        productos_lista.append({
                            "nombre": nombre,
                            "imagen": imagen,
                            "url_producto": href if href.startswith("http") else f"https://www.pullandbear.com{href}",
                            "precio_original": f"{precio_original:.2f}€" if precio_original else None,
                            "precio_final": f"{precio_final:.2f}€",
                            "descuento": descuento_txt,
                            "categoria": nombre_tarea
                        })

                        vistos.add(nombre)
                        nuevos_en_esta_vuelta += 1
                        print(f"📦 [{len(productos_lista)}] {nombre[:20]}.. | {precio_final}€")

                    except:
                        continue

                # LÓGICA DE SALIDA Y SCROLL
                if nuevos_en_esta_vuelta == 0:
                    intentos_sin_nuevos += 1
                    print(f"⚠️ Esperando nuevos productos... (Intento {intentos_sin_nuevos}/8)")
                else:
                    intentos_sin_nuevos = 0

                # Scroll más profundo y espera más larga para carga de red
                await page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(3.5)  # Pausa más larga para que la web respire

                # Si llegamos a 8 intentos sin ver nada nuevo, paramos.
                if intentos_sin_nuevos >= 8:
                    break

                # He quitado el límite de 15 para que te coja todos los posibles
                if len(productos_lista) >= 100:  # Límite de seguridad para que no sea infinito
                    break

            print(f"🏆 FINALIZADO: {len(productos_lista)} productos reales.")
            await browser.close()
            return productos_lista

        except Exception as e:
            print(f"❌ Error en Pull&Bear: {e}")
            await browser.close()
            return []