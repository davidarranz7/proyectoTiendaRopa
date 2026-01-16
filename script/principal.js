document.addEventListener('DOMContentLoaded', () => {
    const tarjetas = document.querySelectorAll('.tarjeta-producto');

    // Efecto de aparición gradual para los productos
    tarjetas.forEach((tarjeta, index) => {
        tarjeta.style.opacity = '0';
        tarjeta.style.transform = 'translateY(20px)';
        tarjeta.style.transition = 'all 0.5s ease';

        setTimeout(() => {
            tarjeta.style.opacity = '1';
            tarjeta.style.transform = 'translateY(0)';
        }, index * 100); // Aparecen uno tras otro
    });
});