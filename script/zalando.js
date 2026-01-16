document.addEventListener('DOMContentLoaded', () => {
    const tarjetas = document.querySelectorAll('.tarjeta-producto');

    tarjetas.forEach(tarjeta => {
        tarjeta.addEventListener('mouseenter', () => {
            const marca = tarjeta.querySelector('.marca').textContent;
            console.log("Explorando marca: " + marca);
        });
    });
});