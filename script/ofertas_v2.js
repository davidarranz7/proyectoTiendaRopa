document.addEventListener("DOMContentLoaded", () => {
    const grid = document.getElementById("grid-ofertas");
    const btnAsc = document.getElementById("btn-asc");
    const btnDesc = document.getElementById("btn-desc");

    // 1. Resaltado de Super Ofertas (>= 30%)
    document.querySelectorAll('.porcentaje-descuento').forEach(el => {
        const valor = Math.abs(parseInt(el.textContent));
        if (valor >= 30) {
            el.style.backgroundColor = '#e84118';
            el.classList.add('super-oferta');
        }
    });

    // 2. Limpiador de precios para que JS entienda los números
    const parsePrice = (v) => {
        if (!v) return 0;
        // Cambia coma por punto y elimina todo lo que no sea número o punto
        let limpio = v.toString().replace(',', '.').replace(/[^\d.]/g, '');
        return parseFloat(limpio) || 0;
    };

    // 3. Función de ordenación del Grid
    const sortGrid = (asc) => {
        const items = Array.from(grid.querySelectorAll('.tarjeta-producto'));

        items.sort((a, b) => {
            const pa = parsePrice(a.getAttribute('data-precio'));
            const pb = parsePrice(b.getAttribute('data-precio'));
            return asc ? pa - pb : pb - pa;
        });

        // Vaciamos y reinyectamos las tarjetas ordenadas
        grid.innerHTML = "";
        items.forEach(i => grid.appendChild(i));
    };

    // 4. Asignación de los botones
    if (btnAsc) btnAsc.onclick = () => sortGrid(true);
    if (btnDesc) btnDesc.onclick = () => sortGrid(false);
});