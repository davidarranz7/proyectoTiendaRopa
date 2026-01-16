document.addEventListener('DOMContentLoaded', () => {
    // 1. MARCAR ENLACE ACTIVO
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // 2. LÓGICA DEL BUSCADOR
    const inputBusqueda = document.getElementById('busqueda-input');
    const btnBusqueda = document.getElementById('busqueda-btn');

    const filtrarProductos = () => {
        const texto = inputBusqueda.value.toLowerCase();
        const productos = document.querySelectorAll('.tarjeta-producto');

        productos.forEach(producto => {
            // Buscamos dentro de la marca y el nombre del producto
            const nombre = producto.querySelector('.nombre-prenda').textContent.toLowerCase();
            const marca = producto.querySelector('.marca').textContent.toLowerCase();

            if (nombre.includes(texto) || marca.includes(texto)) {
                producto.style.display = 'flex'; // Muestra si coincide
            } else {
                producto.style.display = 'none'; // Oculta si no coincide
            }
        });
    };

    // Filtrar al pulsar el botón o al escribir
    btnBusqueda.addEventListener('click', filtrarProductos);
    inputBusqueda.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') filtrarProductos();
    });
});