document.addEventListener("DOMContentLoaded", () => {
    const grid = document.getElementById("grid-ofertas");
    const btnAsc = document.getElementById("btn-asc");
    const btnDesc = document.getElementById("btn-desc");

    const parsePrice = (v) => {
        if (!v) return 0;
        let limpio = v.toString().replace(',', '.').replace(/[^\d.]/g, '');
        return parseFloat(limpio) || 0;
    };

    const sortGrid = (asc) => {
        const items = Array.from(grid.querySelectorAll('.tarjeta-producto'));

        items.sort((a, b) => {
            const pa = parsePrice(a.getAttribute('data-precio'));
            const pb = parsePrice(b.getAttribute('data-precio'));
            return asc ? pa - pb : pb - pa;
        });

        grid.innerHTML = "";
        items.forEach(i => {
            // Aseguramos que el display no sea 'flex' directo sino que respete el grid
            i.style.display = "block";
            grid.appendChild(i);
        });
    };

    if (btnAsc) btnAsc.onclick = () => sortGrid(true);
    if (btnDesc) btnDesc.onclick = () => sortGrid(false);
});