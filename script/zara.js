document.addEventListener('DOMContentLoaded', () => {
    console.log("Zara Editorial Mode: ON");

    // Animación de entrada suave para las fotos
    const fotos = document.querySelectorAll('.img-wrapper');
    fotos.forEach((foto, i) => {
        foto.style.opacity = '0';
        setTimeout(() => {
            foto.style.transition = 'opacity 1s ease';
            foto.style.opacity = '1';
        }, i * 150);
    });
});