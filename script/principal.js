document.addEventListener("DOMContentLoaded", () => {
    const hero = document.querySelector('.hero-zara');

    if (hero) {
        window.addEventListener('scroll', () => {
            const scrollValue = window.scrollY;
            hero.style.backgroundPositionY = `${scrollValue * 0.5}px`;
        });
    }

    const tiendaCards = document.querySelectorAll('.tienda-card');

    const observerOptions = {
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
            }
        });
    }, observerOptions);

    tiendaCards.forEach(card => {
        card.style.opacity = "0";
        card.style.transform = "translateY(20px)";
        card.style.transition = "all 0.8s ease-out";
        observer.observe(card);
    });
});