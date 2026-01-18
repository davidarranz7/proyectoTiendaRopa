document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("modal-filtros-mango");
    const btnAbrir = document.getElementById("abrir-filtros");
    const btnCerrar = document.getElementById("cerrar-filtros");
    const btnConfirmar = document.getElementById("confirmar-filtros");
    const grid = document.getElementById("grid-articulos");

    // 1. GESTIÓN DEL MODAL DE FILTROS
    if (btnAbrir) {
        btnAbrir.addEventListener("click", () => {
            modal.style.display = "block";
            // Bloqueamos el scroll del cuerpo para mejorar la experiencia de filtrado
            document.body.style.overflow = "hidden";
        });
    }

    const cerrarModal = () => {
        if (modal) {
            modal.style.display = "none";
            document.body.style.overflow = "auto";
        }
    };

    if (btnCerrar) btnCerrar.addEventListener("click", cerrarModal);
    if (btnConfirmar) btnConfirmar.addEventListener("click", cerrarModal);

    // Cerrar el modal si el usuario hace clic fuera del contenido
    window.onclick = (event) => {
        if (event.target == modal) {
            cerrarModal();
        }
    };

    // 2. INTERACTIVIDAD DEL MENÚ DE CATEGORÍAS
    const categorias = document.querySelectorAll(".categorias-mango li a");
    categorias.forEach(cat => {
        cat.addEventListener("click", (e) => {
            if (cat.getAttribute("href") === "#") e.preventDefault();

            // Cambiar estado visual
            categorias.forEach(c => c.classList.remove("active"));
            cat.classList.add("active");

            console.log("Filtrando Mango por: " + cat.textContent.trim());
        });
    });

    // 3. LÓGICA DE ORDENACIÓN (Preparada para botones de precio)
    const ordenarPorPrecio = (orden) => {
        const productos = Array.from(grid.querySelectorAll(".card-mango"));

        productos.sort((a, b) => {
            const precioA = parseFloat(a.dataset.precio.replace(',', '.'));
            const precioB = parseFloat(b.dataset.precio.replace(',', '.'));
            return orden === 'asc' ? precioA - precioB : precioB - precioA;
        });

        // Reinyectar productos ordenados
        grid.innerHTML = "";
        productos.forEach(p => grid.appendChild(p));
    };
});