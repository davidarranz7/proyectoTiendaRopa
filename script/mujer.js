document.addEventListener("DOMContentLoaded", () => {
    const botonesFiltro = document.querySelectorAll(".filtro-cat");
    const productos = document.querySelectorAll(".tarjeta-producto");

    botonesFiltro.forEach(boton => {
        boton.addEventListener("click", () => {
            botonesFiltro.forEach(btn => btn.classList.remove("active"));
            boton.classList.add("active");

            const categoriaSeleccionada = boton.getAttribute("data-categoria");

            productos.forEach(producto => {
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