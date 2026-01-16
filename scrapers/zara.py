import asyncio
from playwright.async_api import async_playwright


async def extraer_categoria_zara(url, nombre_categoria):
    print(f"🚀 Iniciando extracción de Zara: {nombre_categoria}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Mantenlo en False para ver si carga
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # CAMBIO: Usamos 'domcontentloaded' que es más rápido que 'networkidle'
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Esperamos 10 segundos manuales para asegurar que los productos aparezcan
            print("⏳ Esperando a que aparezcan los productos...")
            await asyncio.sleep(10)

            # Hacemos scroll para activar la carga de imágenes
            await page.mouse.wheel(0, 2000)
            await asyncio.sleep(3)

            # EXTRAER DATOS: Buscamos por enlaces de producto (/p/)
            productos = await page.evaluate('''() => {
                const results = [];
                // Buscamos todos los enlaces que contienen "/p/" (formato de producto de Zara)
                const links = Array.from(document.querySelectorAll('a[href*="/p/"]'));

                links.forEach(link => {
                    // Buscamos el contenedor del producto (li o article)
                    const item = link.closest('li') || link.closest('article') || link.parentElement;

                    const nombre = item.querySelector('h2, h3, [class*="product-grid-product-info__name"]')?.innerText;
                    const precio = item.querySelector('.money-amount__main, [class*="price"]')?.innerText;
                    const imagen = item.querySelector('img')?.src;

                    // Solo añadimos si tiene nombre y no está repetido
                    if (nombre && !results.some(r => r.url === link.href)) {
                        results.push({
                            tienda: "Zara",
                            nombre: nombre.trim(),
                            precio_nuevo: precio ? precio.trim() : "0.00€",
                            imagen: imagen || "",
                            url: link.href
                        });
                    }
                });
                return results;
            }''')

            await browser.close()
            print(f"✅ ¡ÉXITO! Datos recogidos: {len(productos)} prendas.")
            return productos

        except Exception as e:
            print(f"❌ Error en Zara: {e}")
            await browser.close()
            return []