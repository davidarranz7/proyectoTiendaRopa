document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("modal-filtros-bsk");
    const btnAbrir = document.getElementById("abrir-filtros");
    const btnCerrar = document.getElementById("cerrar-filtros");
    const btnConfirmar = document.getElementById("confirmar-filtros");
    const grid = document.getElementById("grid-articulos");
    const tarjetas = document.querySelectorAll(".card-bsk");

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

    window.onclick = (event) => {
        if (event.target == modal) cerrarModal();
    };

    const categorias = document.querySelectorAll(".categorias-bsk li a");
    categorias.forEach(cat => {
        cat.addEventListener("click", (e) => {
            if (cat.getAttribute("href") === "#") e.preventDefault();

            const filtroRapido = cat.textContent.trim().toLowerCase();
            categorias.forEach(c => c.classList.remove("active"));
            cat.classList.add("active");

            tarjetas.forEach(t => {
                const nombre = t.querySelector(".name-bsk").textContent.toLowerCase();
                const esOferta = t.querySelector(".badge-bsk") !== null;

                if (filtroRapido === "todas las prendas") {
                    t.style.display = "block";
                } else if (filtroRapido === "rebajas") {
                    t.style.display = esOferta ? "block" : "none";
                } else {
                    t.style.display = nombre.includes(filtroRapido.replace(/s$/, '')) ? "block" : "none";
                }
            });
        });
    });

    if (btnConfirmar) {
        btnConfirmar.onclick = () => {
            const generos = Array.from(modal.querySelectorAll('.col-bsk:first-child input:checked')).map(i => i.parentElement.textContent.trim().toLowerCase());
            const tipos = Array.from(modal.querySelectorAll('.col-bsk:nth-child(2) input:checked')).map(i => i.parentElement.textContent.trim().toLowerCase().replace(/s$/, ''));
            const soloOferta = modal.querySelector('.sale-check input').checked;

            tarjetas.forEach(t => {
                const nombre = t.querySelector(".name-bsk").textContent.toLowerCase();
                const esOferta = t.querySelector(".badge-bsk") !== null;

                const cumpleGenero = generos.length === 0 || generos.some(g => nombre.includes(g));
                const cumpleTipo = tipos.length === 0 || tipos.some(tipo => nombre.includes(tipo));
                const cumpleOferta = !soloOferta || esOferta;

                t.style.display = (cumpleGenero && cumpleTipo && cumpleOferta) ? "block" : "none";
            });

            cerrarModal();
        };
    }
});