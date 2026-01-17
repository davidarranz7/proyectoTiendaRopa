document.addEventListener("DOMContentLoaded", () => {
    const tarjetas = document.querySelectorAll(".tarjeta-zara");
    const btnAbrir = document.getElementById("btn-abrir-filtro");
    const panel = document.getElementById("panel-filtros");
    const btnConfirmar = document.getElementById("btn-confirmar-filtro");

    // 1. ABRIR Y CERRAR EL PANEL DE FILTRO
    if (btnAbrir && panel) {
        btnAbrir.onclick = () => {
            panel.style.display = (panel.style.display === "none" || panel.style.display === "") ? "block" : "none";
        };
    }

    // 2. LÓGICA DE LA BOTONERA PRINCIPAL
    document.querySelectorAll(".btn-directo").forEach(btn => {
        btn.onclick = () => {
            const filtro = btn.getAttribute("data-filter").toLowerCase();

            tarjetas.forEach(t => {
                const cat = (t.getAttribute("data-full-cat") || "").toLowerCase();
                const esOferta = t.getAttribute("data-es-oferta") === "si";

                if (filtro === "todas") {
                    t.style.display = "block"; // Cambiado de flex a block
                } else if (filtro === "rebajas") {
                    t.style.display = esOferta ? "block" : "none";
                } else {
                    t.style.display = cat.includes(filtro) ? "block" : "none";
                }
            });
        };
    });

    // 3. LÓGICA DEL PANEL AVANZADO (CONFIRMAR)
    if (btnConfirmar) {
        btnConfirmar.onclick = () => {
            const generosMarcados = Array.from(document.querySelectorAll('input[name="f-genero"]:checked')).map(i => i.value);
            const tiposMarcados = Array.from(document.querySelectorAll('input[name="f-tipo"]:checked')).map(i => i.value);
            const soloOferta = document.getElementById("f-solo-oferta").checked;

            tarjetas.forEach(t => {
                const cat = (t.getAttribute("data-full-cat") || "").toLowerCase();
                const esOferta = t.getAttribute("data-es-oferta") === "si";

                const cumpleGenero = generosMarcados.length === 0 || generosMarcados.some(g => cat.includes(g));
                const cumpleTipo = tiposMarcados.length === 0 || tiposMarcados.some(tipo => cat.includes(tipo));
                const cumpleOferta = !soloOferta || esOferta;

                t.style.display = (cumpleGenero && cumpleTipo && cumpleOferta) ? "block" : "none";
            });

            panel.style.display = "none";
        };
    }
});