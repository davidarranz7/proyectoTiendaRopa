import asyncio
import re
from playwright.async_api import async_playwright


def limpiar_precio(texto):
    """Extrae el precio numérico."""
    try:
        match = re.search(r'(\d+[\.,]\d{2})', texto)
        if match:
            valor = match.group(1).replace(",", ".")
            return float(valor)
        return None
    except:
        return None


async def extraer_categoria_pull(url, nombre_tarea="desconocido"):
    async with async_playwright() as p:
        print(f"\n🚀 [PULL PRO] Iniciando scraping para: {nombre_tarea}")
        print(f"🌍 URL: {url}")

        browser = await p.chromium.launch(headless=False, slow_mo=150)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="es-ES",
        )
        page = await context.new_page()

        try:
            print("➡️ Entrando en Pull&Bear...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(4000)

            # --- COOKIES (tu método) ---
            try:
                for _ in range(3):
                    await page.keyboard.press("Tab")
                    await page.wait_for_timeout(250)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(1500)
                print("✅ Cookies aceptadas correctamente.")
            except:
                print("⚠️ No se pudieron aceptar cookies automáticamente.")

            # Espera a que aparezcan productos del grid real
            await page.wait_for_selector("legacy-product", timeout=60000)
            await page.wait_for_load_state("networkidle")

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

                elementos = await page.query_selector_all("legacy-product")
                print(f"🧩 legacy-product detectados: {len(elementos)}")

                nuevos_en_esta_vuelta = 0

                for el in elementos:
                    try:
                        # Asegura que el elemento “existe” visualmente (lazy load)
                        await el.scroll_into_view_if_needed()
                        await page.wait_for_timeout(120)

                        # Extraemos TODO dentro del navegador (mejor para Shadow DOM)
                        data = await el.evaluate(
                            """
                            (node) => {
                              // helpers
                              const text = (x) => (x ? x.textContent.trim() : null);

                              // Nombre
                              const nameEl = node.querySelector(".product-name");
                              const nombre = text(nameEl);

                              // URL producto
                              const linkEl = node.querySelector("a.carousel-item-container[href], a[href]");
                              const href = linkEl ? linkEl.getAttribute("href") : null;

                              // Imagen
                              const imgEl = node.querySelector("img.image-responsive, img");
                              const imagen = imgEl ? (imgEl.getAttribute("src") || imgEl.getAttribute("data-src")) : null;

                              // Tag (Exclusivo Online, Mix & Match -10%...) -> Shadow DOM
                              const tagEls = Array.from(node.querySelectorAll("product-grid-tag"));
                              const tags = [];
                              for (const t of tagEls) {
                                const sr = t.shadowRoot;
                                if (!sr) continue;
                                const tt = sr.querySelector(".tag-text");
                                if (tt && tt.textContent) tags.push(tt.textContent.trim());
                              }

                              // Precio -> price-element Shadow DOM
                              let precioTexto = null;
                              const priceHost = node.querySelector("price-element");
                              if (priceHost && priceHost.shadowRoot) {
                                const priceP = priceHost.shadowRoot.querySelector("p.price");
                                precioTexto = priceP ? priceP.textContent.replace(/\\s+/g, " ").trim() : null;
                              } else {
                                // fallback por si a veces renderiza fuera
                                const p = node.querySelector("p.price, [class*='price']");
                                precioTexto = p ? p.textContent.replace(/\\s+/g, " ").trim() : null;
                              }

                              // Tallas -> size-selector Shadow DOM (si está en grid)
                              const sizes = [];
                              const sizeHost = node.querySelector("size-selector");
                              if (sizeHost && sizeHost.shadowRoot) {
                                const btns = Array.from(sizeHost.shadowRoot.querySelectorAll("button.size-button"));
                                for (const b of btns) {
                                  const talla = (b.getAttribute("data-size-name") || b.textContent || "").trim();
                                  if (!talla) continue;
                                  const disponible = !(b.disabled || b.classList.contains("is-disabled"));
                                  sizes.push({ talla, disponible });
                                }
                              }

                              return { nombre, href, imagen, tags, precioTexto, sizes };
                            }
                            """
                        )

                        if not data:
                            continue

                        nombre = (data.get("nombre") or "").strip()
                        href = data.get("href")
                        imagen = data.get("imagen")
                        precioTexto = data.get("precioTexto")
                        tags = data.get("tags") or []
                        sizes = data.get("sizes") or []

                        if not nombre or len(nombre) < 3:
                            continue
                        if not href:
                            continue
                        if not imagen:
                            continue

                        url_producto = href if href.startswith("http") else f"https://www.pullandbear.com{href}"

                        clave = f"{nombre}|{url_producto}"
                        if clave in vistos:
                            continue

                        # Precio numérico
                        precio_final = None
                        if precioTexto and "€" in precioTexto:
                            precio_final = limpiar_precio(precioTexto)

                        if not precio_final:
                            # si no hay € visible, saltamos
                            continue

                        productos_lista.append({
                            "nombre": nombre,
                            "imagen": imagen,
                            "url_producto": url_producto,
                            "precio_original": None,  # en grid suele venir 1 precio; el original real muchas veces está en ficha
                            "precio_final": f"{precio_final:.2f}€",
                            "descuento": tags[0] if tags else None,   # si quieres, te lo separo en "tags": [...]
                            "tags": tags,
                            "tallas": sizes,
                            "categoria": nombre_tarea
                        })

                        vistos.add(clave)
                        nuevos_en_esta_vuelta += 1

                        print(f"📦 [{len(productos_lista)}] {nombre[:35]} | {precio_final:.2f}€")

                    except:
                        continue

                # ============================================================
                # 🔥 CONTROL FINAL (tu lógica)
                # ============================================================
                if nuevos_en_esta_vuelta == 0:
                    intentos_sin_nuevos += 1
                    print(f"⚠️ Sin nuevos productos ({intentos_sin_nuevos}/10)")
                else:
                    intentos_sin_nuevos = 0

                # Scroll “humano”
                await page.evaluate("window.scrollBy(0, 1400)")
                await page.wait_for_timeout(2200)

                if intentos_sin_nuevos >= 10:
                    print("\n🛑 FINAL REAL DE PULL&BEAR ALCANZADO")
                    break

            print("\n" + "=" * 90)
            print(f"🏆 FINALIZADO PULL PRO: {len(productos_lista)} productos reales totales")
            print("=" * 90)

            await browser.close()
            return productos_lista

        except Exception as e:
            print(f"❌ ERROR GRAVE EN PULL&BEAR: {e}")
            await browser.close()
            return []