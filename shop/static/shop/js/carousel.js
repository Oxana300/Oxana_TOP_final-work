// shop/static/shop/js/carousel.js

class ProductCarousel {
    constructor(containerId, products) {
        this.container = document.getElementById(containerId);
        this.products = products;
        this.currentIndex = 0;
        this.totalItems = products.length;
        this.autoRotateInterval = null;

        this.init();
    }

    init() {
        if (!this.container || this.totalItems === 0) return;

        // Устанавливаем количество элементов
        this.container.style.setProperty('--n', this.totalItems);

        this.render();
        this.startAutoRotate();
        this.bindEvents();
    }

    render() {
        const assembly = this.container.querySelector('.carousel-assembly');
        if (!assembly) return;

        assembly.innerHTML = '';

        this.products.forEach((product, i) => {
            const angle = (i / this.totalItems) * 360;
            const item = document.createElement('div');
            item.className = 'carousel-item';
            item.style.transform = `rotateY(${angle}deg) translateZ(300px)`;

            // Получаем URL изображения
            let imgUrl = product.image_url || '/static/shop/images/default-product.jpg';

            item.innerHTML = `
                <div class="carousel-item-inner">
                    <img src="${imgUrl}" alt="${product.name}" loading="lazy">
                    <div class="carousel-item-info">
                        <h4>${product.name}</h4>
                        <p>${product.price} ₽</p>
                    </div>
                </div>
            `;

            item.addEventListener('click', () => {
                window.location.href = `/product/${product.slug}/`;
            });

            assembly.appendChild(item);
        });

        this.updateActiveItem();
    }

    updateActiveItem() {
        const items = this.container.querySelectorAll('.carousel-item');
        items.forEach((item, i) => {
            const angle = (i / this.totalItems) * 360;
            const rotation = angle - (this.currentIndex / this.totalItems) * 360;
            item.style.transform = `rotateY(${rotation}deg) translateZ(300px)`;
        });

        // Обновляем индикаторы
        const dots = this.container.querySelectorAll('.carousel-dot');
        dots.forEach((dot, i) => {
            if (i === this.currentIndex) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }

    next() {
        this.currentIndex = (this.currentIndex + 1) % this.totalItems;
        this.updateActiveItem();
    }

    prev() {
        this.currentIndex = (this.currentIndex - 1 + this.totalItems) % this.totalItems;
        this.updateActiveItem();
    }

    goTo(index) {
        this.currentIndex = index;
        this.updateActiveItem();
    }

    startAutoRotate() {
        if (this.autoRotateInterval) clearInterval(this.autoRotateInterval);
        this.autoRotateInterval = setInterval(() => this.next(), 5000);
    }

    stopAutoRotate() {
        if (this.autoRotateInterval) {
            clearInterval(this.autoRotateInterval);
            this.autoRotateInterval = null;
        }
    }

    bindEvents() {
        const container = this.container;

        // Пауза при наведении
        container.addEventListener('mouseenter', () => this.stopAutoRotate());
        container.addEventListener('mouseleave', () => this.startAutoRotate());

        // Кнопки навигации
        const prevBtn = container.querySelector('.carousel-prev');
        const nextBtn = container.querySelector('.carousel-next');

        if (prevBtn) prevBtn.addEventListener('click', () => this.prev());
        if (nextBtn) nextBtn.addEventListener('click', () => this.next());

        // Индикаторы
        const dots = container.querySelectorAll('.carousel-dot');
        dots.forEach((dot, i) => {
            dot.addEventListener('click', () => this.goTo(i));
        });
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Получаем данные товаров из атрибута data
    const carouselContainer = document.getElementById('productCarousel');
    if (carouselContainer && window.carouselProducts) {
        new ProductCarousel('productCarousel', window.carouselProducts);
    }
});
