document.addEventListener("DOMContentLoaded", () => {
    const botonesFiltro = document.querySelectorAll(".filtro-cat");
    const productos = document.querySelectorAll(".tarjeta-producto");

    botonesFiltro.forEach(boton => {
        boton.addEventListener("click", () => {
            // 1. Gestionar estado visual de los botones
            botonesFiltro.forEach(btn => btn.classList.remove("active"));
            boton.classList.add("active");

            // 2. Obtener la categoría seleccionada
            const categoriaSeleccionada = boton.getAttribute("data-categoria");

            // 3. Filtrar los productos
            productos.forEach(producto => {
                // Obtenemos la categoría del producto (asegúrate de que venga en minúsculas)
                const categoriaProducto = producto.getAttribute("data-categoria").toLowerCase();

                if (categoriaSeleccionada === "todos") {
                    producto.style.display = "flex";
                } else if (categoriaProducto.includes(categoriaSeleccionada)) {
                    producto.style.display = "flex";
                } else {
                    producto.style.display = "none";
                }
            });
        });
    });
});