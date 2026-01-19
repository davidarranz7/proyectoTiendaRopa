document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("modal-filtros");
    const btnAbrir = document.querySelector(".btn-filtro-pull");
    const btnCerrar = document.getElementById("cerrar-filtros");
    const btnConfirmar = document.getElementById("aplicar-filtros");
    const tarjetas = document.querySelectorAll(".card-pull");

    if (btnAbrir) {
        btnAbrir.addEventListener("click", () => {
            modal.style.display = "block";
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

    window.onclick = (event) => {
        if (event.target == modal) cerrarModal();
    };

    const categorias = document.querySelectorAll(".categorias-pull li a");
    categorias.forEach(cat => {
        cat.addEventListener("click", (e) => {
            if (cat.getAttribute("href") === "#") e.preventDefault();

            const filtroRapido = cat.textContent.trim().toLowerCase();
            categorias.forEach(c => c.classList.remove("active"));
            cat.classList.add("active");

            tarjetas.forEach(t => {
                const nombre = t.querySelector(".name-pull").textContent.toLowerCase();
                const esOferta = t.querySelector(".promo-tag") !== null;

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
            const generos = Array.from(modal.querySelectorAll('.seccion-col:first-child input:checked')).map(i => i.parentElement.textContent.trim().toLowerCase());
            const tipos = Array.from(modal.querySelectorAll('.seccion-col:nth-child(2) input:checked')).map(i => i.parentElement.textContent.trim().toLowerCase().replace(/s$/, ''));
            const soloOferta = modal.querySelector('.check-rebajas input').checked;

            tarjetas.forEach(t => {
                const nombre = t.querySelector(".name-pull").textContent.toLowerCase();
                const esOferta = t.querySelector(".promo-tag") !== null;

                const cumpleGenero = generos.length === 0 || generos.some(g => nombre.includes(g));
                const cumpleTipo = tipos.length === 0 || tipos.some(tipo => nombre.includes(tipo));
                const cumpleOferta = !soloOferta || esOferta;

                t.style.display = (cumpleGenero && cumpleTipo && cumpleOferta) ? "block" : "none";
            });

            cerrarModal();
        };
    }
});