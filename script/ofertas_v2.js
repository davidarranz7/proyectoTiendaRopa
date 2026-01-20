document.addEventListener("DOMContentLoaded", () => {
    const filtrosCheck = document.querySelectorAll(".filtro-check");
    const ordenChecks = document.querySelectorAll(".orden-check");
    const grid = document.getElementById("grid-productos");
    const productosInitial = Array.from(document.querySelectorAll(".tarjeta-oferta"));

    const aplicarFiltrosYOrden = () => {
        const tiendasSeleccionadas = Array.from(document.querySelectorAll('.filtro-check[data-tipo="tienda"]:checked')).map(c => c.value);
        const catsSeleccionadas = Array.from(document.querySelectorAll('.filtro-check[data-tipo="cat"]:checked')).map(c => c.value);
        const ordenSeleccionado = Array.from(ordenChecks).find(r => r.checked)?.value;

        let productosFiltrados = productosInitial.filter(p => {
            const tienda = p.getAttribute("data-tienda");
            const nombre = p.getAttribute("data-nombre");

            const cumpleTienda = tiendasSeleccionadas.length === 0 || tiendasSeleccionadas.includes(tienda);
            const cumpleCat = catsSeleccionadas.length === 0 || catsSeleccionadas.some(c => {
                const base = c.replace(/s$/, '');
                return nombre.includes(base);
            });

            return cumpleTienda && cumpleCat;
        });

        if (ordenSeleccionado === "precio-asc") {
            productosFiltrados.sort((a, b) => {
                return parseFloat(a.getAttribute("data-precio")) - parseFloat(b.getAttribute("data-precio"));
            });
        } else if (ordenSeleccionado === "desc") {
            productosFiltrados.sort((a, b) => {
                return parseInt(b.getAttribute("data-descuento")) - parseInt(a.getAttribute("data-descuento"));
            });
        }

        grid.innerHTML = "";
        productosInitial.forEach(p => p.style.display = "none");

        productosFiltrados.forEach(p => {
            p.style.display = "";
            grid.appendChild(p);
        });
    };

    filtrosCheck.forEach(check => {
        check.addEventListener("change", aplicarFiltrosYOrden);
    });

    ordenChecks.forEach(radio => {
        radio.addEventListener("change", aplicarFiltrosYOrden);
    });
});