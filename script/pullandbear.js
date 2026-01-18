document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("modal-filtros");
    const btnAbrir = document.querySelector(".btn-filtro-pull");
    const btnCerrar = document.getElementById("cerrar-filtros");
    const btnConfirmar = document.getElementById("aplicar-filtros");

    // Manejo del Modal de Filtros
    if (btnAbrir) {
        btnAbrir.addEventListener("click", () => {
            modal.style.display = "block";
        });
    }

    const cerrarModal = () => { if(modal) modal.style.display = "none"; };

    if (btnCerrar) btnCerrar.addEventListener("click", cerrarModal);
    if (btnConfirmar) btnConfirmar.addEventListener("click", cerrarModal);

    window.onclick = (event) => {
        if (event.target == modal) cerrarModal();
    };

    // Estética del menú de categorías
    const categorias = document.querySelectorAll(".categorias-pull li a");
    categorias.forEach(cat => {
        cat.addEventListener("click", (e) => {
            if (cat.getAttribute("href") === "#") e.preventDefault();
            categorias.forEach(c => c.classList.remove("active"));
            cat.classList.add("active");
        });
    });
});