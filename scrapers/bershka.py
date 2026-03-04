import asyncio
import re
from playwright.async_api import async_playwright


# ==========================================
# LIMPIAR PRECIO
# ==========================================

def limpiar_precio(texto):

    try:
        match = re.search(r'(\d+[\.,]\d{2})', texto)

        if match:
            return float(match.group(1).replace(",", "."))

        return None

    except:
        return None


# ==========================================
# SCRAPER BERSHKA
# ==========================================

async def extraer_categoria_bershka(url, nombre_tarea="desconocido"):

    async with async_playwright() as p:

        print("\n" + "=" * 70)
        print("🚀 BERSHKA SCRAPER")
        print(f"📂 Categoría: {nombre_tarea}")
        print(f"🌍 URL: {url}")
        print("=" * 70)

        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )

        page = await context.new_page()

        try:

            await page.goto(url, wait_until="domcontentloaded")

            # ==========================================
            # COOKIES
            # ==========================================

            try:
                await page.wait_for_selector("#onetrust-accept-btn-handler", timeout=5000)
                await page.click("#onetrust-accept-btn-handler")
                print("🍪 Cookies aceptadas")
                await asyncio.sleep(2)
            except:
                pass

            productos = []
            vistos = set()

            scroll_intentos = 0
            scroll_max = 10
            vuelta = 0

            while True:

                vuelta += 1

                print("\n" + "-" * 60)
                print(f"🔄 SCROLL #{vuelta}")
                print("-" * 60)

                # ==========================================
                # PRODUCTOS
                # ==========================================

                items = await page.query_selector_all("div[data-testid='product-card']")

                print(f"🧩 Productos detectados: {len(items)}")

                nuevos = 0

                for item in items:

                    try:

                        # ==========================
                        # NOMBRE
                        # ==========================

                        nombre_el = await item.query_selector("[data-testid='product-name']")

                        if not nombre_el:
                            continue

                        nombre = (await nombre_el.inner_text()).strip()

                        # ==========================
                        # LINK
                        # ==========================

                        link_el = await item.query_selector("a")

                        href = await link_el.get_attribute("href")

                        if not href:
                            continue

                        if not href.startswith("http"):
                            href = "https://www.bershka.com" + href

                        clave = f"{nombre}|{href}"

                        if clave in vistos:
                            continue

                        # ==========================
                        # PRECIO
                        # ==========================

                        precio_el = await item.query_selector("[data-testid='product-price']")

                        if not precio_el:
                            continue

                        precio_texto = await precio_el.inner_text()

                        precio_final = limpiar_precio(precio_texto)

                        if not precio_final:
                            continue

                        # ==========================
                        # IMAGEN
                        # ==========================

                        img = await item.query_selector("img")

                        imagen = await img.get_attribute("src")

                        if not imagen:
                            imagen = await img.get_attribute("data-src")

                        if not imagen:
                            continue

                        # ==========================
                        # GUARDAR
                        # ==========================

                        producto = {
                            "nombre": nombre,
                            "imagen": imagen,
                            "url_producto": href,
                            "precio_original": None,
                            "precio_final": f"{precio_final:.2f}€",
                            "descuento": None,
                            "categoria": nombre_tarea
                        }

                        productos.append(producto)

                        vistos.add(clave)

                        nuevos += 1

                        print(f"📦 {len(productos)} | {nombre[:35]} | {precio_final}€")

                    except:
                        continue

                # ==========================================
                # CONTROL FIN
                # ==========================================

                if nuevos == 0:

                    scroll_intentos += 1
                    print(f"⚠ Sin nuevos productos ({scroll_intentos}/{scroll_max})")

                else:

                    scroll_intentos = 0

                await page.mouse.wheel(0, 2500)
                await asyncio.sleep(3)

                if scroll_intentos >= scroll_max:

                    print("\n🛑 FIN DE LISTADO")
                    break

            print("\n" + "=" * 70)
            print(f"🏆 TOTAL PRODUCTOS: {len(productos)}")
            print("=" * 70)

            await browser.close()

            return productos

        except Exception as e:

            print(f"❌ ERROR BERSHKA: {e}")

            await browser.close()

            return []