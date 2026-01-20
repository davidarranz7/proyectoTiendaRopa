document.addEventListener("DOMContentLoaded", () => {
    const botonBusqueda = document.getElementById("busqueda-btn");
    const inputBusqueda = document.getElementById("busqueda-input");

    const buscarEnServidor = () => {
        const query = inputBusqueda.value.trim();
        if (query.length > 0) {
            window.location.href = `/buscar?q=${encodeURIComponent(query)}`;
        }
    };

    if (inputBusqueda) {
        inputBusqueda.addEventListener("input", (e) => {
            const termino = e.target.value.toLowerCase().trim();
            const productos = document.querySelectorAll(".tarjeta-producto, .card-pull, .card-bsk");

            productos.forEach(producto => {
                const nombreElemento = producto.querySelector(".nombre-prenda, .name-pull, .name-bsk");
                if (nombreElemento) {
                    const nombre = nombreElemento.textContent.toLowerCase();
                    producto.style.display = nombre.includes(termino) ? "" : "none";
                }
            });
        });

        inputBusqueda.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                buscarEnServidor();
            }
        });
    }

    if (botonBusqueda) {
        botonBusqueda.addEventListener("click", buscarEnServidor);
    }

    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll(".nav-link");
    navLinks.forEach(link => {
        if (link.getAttribute("href") === currentPath) {
            link.style.opacity = "0.5";
            link.style.borderBottom = "1px solid #000";
        }
    });
});