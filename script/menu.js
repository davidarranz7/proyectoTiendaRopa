document.addEventListener("DOMContentLoaded", () => {
    const botonBusqueda = document.getElementById("busqueda-btn");
    const inputBusqueda = document.getElementById("busqueda-input");

    // Función para búsqueda global (Redirige a /buscar)
    const buscarEnServidor = () => {
        const query = inputBusqueda.value.trim();
        if (query.length > 0) {
            window.location.href = `/buscar?q=${encodeURIComponent(query)}`;
        }
    };

    if (inputBusqueda) {
        inputBusqueda.addEventListener("input", (e) => {
            const termino = e.target.value.toLowerCase().trim();
            const productos = document.querySelectorAll(".tarjeta-producto");

            // Si hay productos en pantalla (estamos en Mujer, Hombre u Ofertas)
            if (productos.length > 0) {
                productos.forEach(producto => {
                    const nombre = producto.querySelector(".nombre-prenda").textContent.toLowerCase();
                    producto.style.display = nombre.includes(termino) ? "flex" : "none";
                });
            }
        });

        // Al pulsar Enter, SIEMPRE hace búsqueda global en todos los JSON
        inputBusqueda.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                buscarEnServidor();
            }
        });
    }

    if (botonBusqueda) {
        botonBusqueda.addEventListener("click", buscarEnServidor);
    }
});