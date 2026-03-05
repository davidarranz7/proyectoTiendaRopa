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


async def extraer_categoria_bershka(url, nombre_tarea="desconocido"):
    async with async_playwright() as p:
        print(f"\n🚀 [BERSHKA PRO] Iniciando scraping para: {nombre_tarea}")
        print(f"🌍 URL: {url}")

        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"➡️ Entrando en Bershka...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # --- COOKIES BERSHKA ---
            try:
                await page.wait_for_selector("#onetrust-accept-btn-handler", timeout=10000)
                await page.click("#onetrust-accept-btn-handler", force=True)
                print("✅ Cookies de Bershka aceptadas")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"⚠️ No se pudieron aceptar cookies automáticamente → {e}")

            print("\n🚜 Iniciando recolección profunda de productos...\n")

            productos_lista = []
            vistos = set()
            intentos_sin_nuevos = 0
            vuelta = 0

            # ============================================================
            # 🟦 BUCLE PRINCIPAL DE SCROLL PROFUNDO
            # ============================================================

            while True:
                vuelta += 1
                print("\n" + "=" * 80)
                print(f"🔄 VUELTA DE SCROLL #{vuelta}")
                print("=" * 80)

                elementos = await page.query_selector_all(
                    "article, div[class*='product'], div[class*='Product']"
                )

                print(f"🧩 Elementos detectados en DOM: {len(elementos)}")

                nuevos_en_esta_vuelta = 0

                for el in elementos:
                    try:
                        # -------------------------------
                        # NOMBRE
                        # -------------------------------
                        nombre_el = await el.query_selector("h2, .product-text, .name, [class*='name']")
                        if not nombre_el:
                            continue

                        nombre = (await nombre_el.inner_text()).strip()
                        if len(nombre) < 5:
                            continue

                        # -------------------------------
                        # LINK
                        # -------------------------------
                        link_el = await el.query_selector("a")
                        href = await link_el.get_attribute("href") if link_el else None
                        if not href:
                            continue

                        url_producto = href if href.startswith("http") else f"https://www.bershka.com{href}"

                        # Clave única real
                        clave = f"{nombre}|{url_producto}"
                        if clave in vistos:
                            continue

                        # -------------------------------
                        # PRECIOS
                        # -------------------------------
                        nodos_precio = await el.query_selector_all("[class*='price'], [class*='Price'], span")
                        valores_numericos = []

                        for p_el in nodos_precio:
                            t = await p_el.inner_text()
                            if "€" in t:
                                val = limpiar_precio(t)
                                if val:
                                    valores_numericos.append(val)

                        valores_numericos = list(dict.fromkeys(valores_numericos))

                        precio_original = None
                        precio_final = None
                        descuento_txt = None

                        if len(valores_numericos) == 1:
                            precio_final = valores_numericos[0]
                        elif len(valores_numericos) >= 2:
                            val_max = max(valores_numericos)
                            val_min = min(valores_numericos)

                            # Filtro anti-ID pegado (regla x6)
                            if val_max > (val_min * 6):
                                precio_final = val_min
                            else:
                                precio_original = val_max
                                precio_final = val_min
                                pct = round(((precio_original - precio_final) / precio_original) * 100)
                                descuento_txt = f"-{pct}%"

                        if not precio_final:
                            continue

                        # -------------------------------
                        # IMAGEN (FORZAMOS CARGA)
                        # -------------------------------
                        await el.scroll_into_view_if_needed()
                        await asyncio.sleep(0.3)

                        img_el = await el.query_selector("img")
                        imagen = await img_el.get_attribute("src") if img_el else None

                        if not imagen:
                            continue

                        # -------------------------------
                        # GUARDAR PRODUCTO
                        # -------------------------------
                        productos_lista.append({
                            "nombre": nombre,
                            "imagen": imagen,
                            "url_producto": url_producto,
                            "precio_original": f"{precio_original:.2f}€" if precio_original else None,
                            "precio_final": f"{precio_final:.2f}€",
                            "descuento": descuento_txt,
                            "categoria": nombre_tarea
                        })

                        vistos.add(clave)
                        nuevos_en_esta_vuelta += 1

                        print(f"📦 [{len(productos_lista)}] {nombre[:30]} | {precio_final}€")

                    except:
                        continue

                # ============================================================
                # 🔥 CONTROL REAL DE FINAL DE PÁGINA (MEJORADO)
                # ============================================================

                if nuevos_en_esta_vuelta == 0:
                    intentos_sin_nuevos += 1
                    print(f"⚠️ Sin nuevos productos ({intentos_sin_nuevos}/10)")
                else:
                    intentos_sin_nuevos = 0

                # Scroll profundo humano
                await page.evaluate("window.scrollBy(0, 1200)")
                await asyncio.sleep(3.5)

                # FINAL REAL
                if intentos_sin_nuevos >= 10:
                    print("\n🛑 FINAL REAL DE BERSHKA ALCANZADO")
                    break

            print("\n" + "=" * 90)
            print(f"🏆 FINALIZADO BERSHKA PRO: {len(productos_lista)} productos reales totales")
            print("=" * 90)

            await browser.close()
            return productos_lista

        except Exception as e:
            print(f"❌ ERROR GRAVE EN BERSHKA: {e}")
            await browser.close()
            return []
