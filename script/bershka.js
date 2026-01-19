document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("modal-filtros-bsk");
    const btnAbrir = document.getElementById("abrir-filtros");
    const btnCerrar = document.getElementById("cerrar-filtros");
    const btnConfirmar = document.getElementById("confirmar-filtros");
    const grid = document.getElementById("grid-articulos");

    if (btnAbrir) {
        btnAbrir.addEventListener("click", () => {
            modal.style.display = "block";
            document.body.style.overflow = "hidden";
        });
    }

    const cerrarModal = () => {
        modal.style.display = "none";
        document.body.style.overflow = "auto";
    };

    if (btnCerrar) btnCerrar.addEventListener("click", cerrarModal);
    if (btnConfirmar) btnConfirmar.addEventListener("click", cerrarModal);

    window.onclick = (event) => {
        if (event.target == modal) cerrarModal();
    };

    const categorias = document.querySelectorAll(".categorias-bsk li a");
    categorias.forEach(cat => {
        cat.addEventListener("click", (e) => {
            if (cat.getAttribute("href") === "#") e.preventDefault();
            categorias.forEach(c => c.classList.remove("active"));
            cat.classList.add("active");
        });
    });

    const ordenarBershka = (orden) => {
        const productos = Array.from(grid.querySelectorAll(".card-bsk"));

        productos.sort((a, b) => {
            const precioA = parseFloat(a.dataset.precio.replace(',', '.'));
            const precioB = parseFloat(b.dataset.precio.replace(',', '.'));
            return orden === 'asc' ? precioA - precioB : precioB - precioA;
        });

        grid.innerHTML = "";
        productos.forEach(p => grid.appendChild(p));
    };
});