document.addEventListener("DOMContentLoaded", () => {
    const filtrosCheck = document.querySelectorAll(".filtro-check");
    const grid = document.getElementById("grid-productos");
    const productosInitial = Array.from(document.querySelectorAll(".tarjeta-oferta"));

    const aplicarFiltros = () => {
        const tiendasSeleccionadas = Array.from(document.querySelectorAll('.filtro-check[data-tipo="tienda"]:checked')).map(c => c.value);
        const catsSeleccionadas = Array.from(document.querySelectorAll('.filtro-check[data-tipo="cat"]:checked')).map(c => c.value);

        let productosFiltrados = productosInitial.filter(p => {
            const tienda = p.getAttribute("data-tienda");
            const nombre = p.getAttribute("data-nombre");

            const cumpleTienda = tiendasSeleccionadas.length === 0 || tiendasSeleccionadas.includes(tienda);
            const cumpleCat = catsSeleccionadas.length === 0 || catsSeleccionadas.some(c => {
                const base = c.replace(/s$/, ''); // Quita la 's' final para buscar mejor
                return nombre.includes(base);
            });

            return cumpleTienda && cumpleCat;
        });

        // Ocultamos todos primero
        productosInitial.forEach(p => p.style.display = "none");

        // Mostramos solo los filtrados
        productosFiltrados.forEach(p => {
            p.style.display = "";
        });
    };

    filtrosCheck.forEach(check => {
        check.addEventListener("change", aplicarFiltros);
    });
});