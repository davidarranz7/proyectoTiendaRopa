document.addEventListener('DOMContentLoaded', () => {
    const etiquetasDescuento = document.querySelectorAll('.porcentaje-descuento');

    etiquetasDescuento.forEach(etiqueta => {
        // Extraemos el número del texto "-40%"
        const valor = Math.abs(parseInt(etiqueta.textContent));

        // Si el descuento es mayor al 30%, le damos un efecto de brillo
        if (valor >= 30) {
            etiqueta.style.backgroundColor = '#e84118';
            etiqueta.classList.add('super-oferta');
            console.log("¡Super oferta detectada!");
        }
    });
});