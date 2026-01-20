document.addEventListener("DOMContentLoaded", () => {
    const filtrosCheck = document.querySelectorAll(".filtro-check");
    const soloRebajas = document.getElementById("solo-rebajas");
    const productos = document.querySelectorAll(".tarjeta-zara");

    const aplicarFiltros = () => {
        const generosSeleccionados = Array.from(document.querySelectorAll('.filtro-check[data-tipo="genero"]:checked')).map(c => c.value);
        const catsSeleccionadas = Array.from(document.querySelectorAll('.filtro-check[data-tipo="cat"]:checked')).map(c => c.value);
        const rebajasActivo = soloRebajas ? soloRebajas.checked : false;

        productos.forEach(p => {
            const nombre = p.getAttribute("data-nombre");
            const esOferta = p.getAttribute("data-oferta") === "true";

            const cumpleGenero = generosSeleccionados.length === 0 || generosSeleccionados.some(g => nombre.includes(g));
            const cumpleCat = catsSeleccionadas.length === 0 || catsSeleccionadas.some(c => nombre.includes(c));
            const cumpleRebaja = !rebajasActivo || esOferta;

            if (cumpleGenero && cumpleCat && cumpleRebaja) {
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