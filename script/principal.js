document.addEventListener('DOMContentLoaded', () => {
    const infoCards = document.querySelectorAll('.info-card');

    const mostrarCards = () => {
        const triggerBottom = window.innerHeight / 5 * 4;

        infoCards.forEach(card => {
            const cardTop = card.getBoundingClientRect().top;

            if(cardTop < triggerBottom) {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }
        });
    };

    infoCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'all 0.6s ease-out';
    });

    window.addEventListener('scroll', mostrarCards);
    mostrarCards();
});