document.addEventListener("DOMContentLoaded", () => {
    const filtrosCheck = document.querySelectorAll(".filtro-check");
    const soloRebajas = document.getElementById("solo-rebajas");
    const productos = document.querySelectorAll(".tarjeta-mujer");

    const aplicarFiltros = () => {
        const tiendasSeleccionadas = Array.from(document.querySelectorAll('.filtro-check[data-tipo="tienda"]:checked')).map(c => c.value);
        const catsSeleccionadas = Array.from(document.querySelectorAll('.filtro-check[data-tipo="cat"]:checked')).map(c => c.value);
        const rebajasActivo = soloRebajas ? soloRebajas.checked : false;

        productos.forEach(p => {
            const tienda = p.getAttribute("data-tienda");
            const nombre = p.getAttribute("data-nombre");
            const esOferta = p.getAttribute("data-oferta") === "true";

            const cumpleTienda = tiendasSeleccionadas.length === 0 || tiendasSeleccionadas.includes(tienda);
            const cumpleCat = catsSeleccionadas.length === 0 || catsSeleccionadas.some(c => {
                const base = c.replace(/s$/, '');
                return nombre.includes(base);
            });
            const cumpleRebaja = !rebajasActivo || esOferta;

            if (cumpleTienda && cumpleCat && cumpleRebaja) {
                p.style.display = "";
            } else {
                p.style.display = "none";
            }
        });
    };

    filtrosCheck.forEach(check => {
        check.addEventListener("change", aplicarFiltros);
    });

    if (soloRebajas) {
        soloRebajas.addEventListener("change", aplicarFiltros);
    }
});