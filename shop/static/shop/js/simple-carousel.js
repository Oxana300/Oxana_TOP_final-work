// simple-carousel.js
class SimpleCarousel {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.track = this.container.querySelector('.carousel-track');
        this.slides = Array.from(this.track.children);
        this.prevBtn = this.container.querySelector('.carousel-prev');
        this.nextBtn = this.container.querySelector('.carousel-next');
        this.dotsNav = this.container.querySelector('.carousel-dots');

        this.currentIndex = 0;
        this.slideWidth = this.slides[0]?.getBoundingClientRect().width || 280;
        this.autoPlayInterval = null;

        this.init();
    }

    init() {
        if (this.slides.length === 0) return;

        // Устанавливаем ширину слайдов
        this.slides.forEach(slide => {
            slide.style.flex = `0 0 ${this.slideWidth}px`;
        });

        // Создаем точки навигации
        this.createDots();

        // Обновляем положение
        this.updatePosition();

        // Добавляем обработчики
        if (this.prevBtn) this.prevBtn.addEventListener('click', () => this.prev());
        if (this.nextBtn) this.nextBtn.addEventListener('click', () => this.next());

        // Автовоспроизведение
        this.startAutoPlay();

        // Пауза при наведении
        this.container.addEventListener('mouseenter', () => this.stopAutoPlay());
        this.container.addEventListener('mouseleave', () => this.startAutoPlay());

        // Адаптация при изменении размера окна
        window.addEventListener('resize', () => this.handleResize());
    }

    createDots() {
        if (!this.dotsNav) return;
        this.dotsNav.innerHTML = '';

        this.slides.forEach((_, i) => {
            const dot = document.createElement('div');
            dot.classList.add('carousel-dot');
            if (i === this.currentIndex) dot.classList.add('active');
            dot.addEventListener('click', () => this.goTo(i));
            this.dotsNav.appendChild(dot);
        });
    }

    updatePosition() {
        const offset = -this.currentIndex * this.slideWidth;
        this.track.style.transform = `translateX(${offset}px)`;

        // Обновляем точки
        const dots = this.dotsNav?.querySelectorAll('.carousel-dot');
        dots?.forEach((dot, i) => {
            if (i === this.currentIndex) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }

    next() {
        if (this.currentIndex >= this.slides.length - 1) {
            this.currentIndex = 0;
        } else {
            this.currentIndex++;
        }
        this.updatePosition();
    }

    prev() {
        if (this.currentIndex <= 0) {
            this.currentIndex = this.slides.length - 1;
        } else {
            this.currentIndex--;
        }
        this.updatePosition();
    }

    goTo(index) {
        if (index >= 0 && index < this.slides.length) {
            this.currentIndex = index;
            this.updatePosition();
        }
    }

    startAutoPlay() {
        if (this.autoPlayInterval) clearInterval(this.autoPlayInterval);
        this.autoPlayInterval = setInterval(() => this.next(), 5000);
    }

    stopAutoPlay() {
        if (this.autoPlayInterval) {
            clearInterval(this.autoPlayInterval);
            this.autoPlayInterval = null;
        }
    }

    handleResize() {
        this.slideWidth = this.slides[0]?.getBoundingClientRect().width || 280;
        this.slides.forEach(slide => {
            slide.style.flex = `0 0 ${this.slideWidth}px`;
        });
        this.updatePosition();
    }
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('productCarousel')) {
        new SimpleCarousel('productCarousel');
    }
});
