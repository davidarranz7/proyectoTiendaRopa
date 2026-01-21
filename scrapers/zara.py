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


async def extraer_categoria_zara(url, nombre_tarea="desconocido"):
    async with async_playwright() as p:
        print(f"\n🚀 [ZARA] Iniciando recolección para: {nombre_tarea}...")
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"🌍 [ZARA] Entrando en: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # --- TU BLOQUE DE COOKIES ORIGINAL ---
            try:
                boton = await page.wait_for_selector("#onetrust-accept-btn-handler", timeout=5000)
                await boton.click()
                print("✅ Cookies de Zara aceptadas")
                await asyncio.sleep(2)
            except:
                pass

            productos_lista = []
            vistos = set()
            intentos_sin_nuevos = 0

            while True:
                # Selector de contenedores
                elementos = await page.query_selector_all("article, li[class*='product']")
                nuevos_en_esta_vuelta = 0

                for el in elementos:
                    try:
                        # 1. Movimiento de ratón para activar precios (Lógica Escaneo Profundo)
                        box = await el.bounding_box()
                        if box:
                            await page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)

                        nombre_el = await el.query_selector("h2, [class*='name']")
                        if not nombre_el: continue

                        nombre = (await nombre_el.inner_text()).strip()
                        if not nombre or nombre in vistos: continue

                        # 2. Captura de Precios (Búsqueda por texto bruto)
                        valores = []
                        nodos_texto = await el.query_selector_all("span, div, p")
                        for nodo in nodos_texto:
                            txt = await nodo.inner_text()
                            if "€" in txt or "EUR" in txt:
                                val = limpiar_precio(txt)
                                if val: valores.append(val)

                        valores = list(dict.fromkeys(valores))

                        # Intento final si falla lo anterior
                        if not valores:
                            full_text = await el.inner_text()
                            match_precios = re.findall(r'(\d+[\.,]\d{2})\s*€', full_text)
                            for m in match_precios:
                                valores.append(float(m.replace(',', '.')))
                            valores = list(dict.fromkeys(valores))

                        if not valores: continue

                        precio_original, precio_final, descuento_txt = None, None, None
                        if len(valores) == 1:
                            precio_final = valores[0]
                        elif len(valores) >= 2:
                            val_max, val_min = max(valores), min(valores)
                            precio_original, precio_final = val_max, val_min
                            pct = round(((precio_original - precio_final) / precio_original) * 100)
                            descuento_txt = f"-{pct}%"

                        # 3. Imagen y Link (CORREGIDO)
                        link_el = await el.query_selector("a")
                        href = await link_el.get_attribute("href") if link_el else ""
                        # Generamos la URL individual real
                        url_producto_real = href if href.startswith("http") else f"https://www.zara.com{href}"

                        img_el = await el.query_selector("img")
                        src = await img_el.get_attribute("src") if img_el else None
                        if not src or "transparent" in src:
                            src = await img_el.get_attribute("data-src")

                        if not src or not src.startswith("http"): continue

                        productos_lista.append({
                            "nombre": nombre,
                            "imagen": src,
                            "url_producto": url_producto_real, # <--- CAMBIO AQUÍ PARA CAPTURAR LA URL REAL
                            "precio_original": f"{precio_original:.2f}€" if precio_original else None,
                            "precio_final": f"{precio_final:.2f}€",
                            "descuento": descuento_txt,
                            "categoria": nombre_tarea
                        })

                        vistos.add(nombre)
                        nuevos_en_esta_vuelta += 1

                        # --- TUS PRINTS ESTILO PULL&BEAR ---
                        print(
                            f"   📦 [{len(productos_lista)}] {nombre[:20]}.. | {precio_final}€ {'[OFERTA]' if descuento_txt else ''}")

                    except:
                        continue

                # Control de scroll y salida
                if nuevos_en_esta_vuelta == 0:
                    intentos_sin_nuevos += 1
                    print(f"⚠️  Esperando nuevos productos... (Intento {intentos_sin_nuevos}/8)")
                else:
                    intentos_sin_nuevos = 0

                await page.mouse.wheel(0, 1000)
                await asyncio.sleep(4)

                if intentos_sin_nuevos >= 8: break
                if len(productos_lista) >= 120: break

            print(f"🏆 ZARA FINALIZADO: {len(productos_lista)} productos reales.")
            await browser.close()
            return productos_lista

        except Exception as e:
            print(f"❌ Error en Zara: {e}")
            await browser.close()
            return []