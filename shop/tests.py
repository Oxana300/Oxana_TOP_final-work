"""
Тесты для приложения магазина
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Product, Category, Tag


class ProductModelTest(TestCase):
    """Тесты модели Product"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Электроника',
            slug='electronics'
        )
        self.product = Product.objects.create(
            name='Смартфон',
            slug='smartphone',
            price=599.99,
            category=self.category,
            status='published'
        )
    
    def test_product_creation(self):
        """Тест создания товара"""
        self.assertEqual(self.product.name, 'Смартфон')
        self.assertEqual(self.product.price, 599.99)
        self.assertEqual(self.product.category, self.category)
    
    def test_product_str(self):
        """Тест метода __str__"""
        self.assertEqual(str(self.product), 'Смартфон - $599.99')
    
    def test_get_final_price(self):
        """Тест метода получения итоговой цены"""
        self.assertEqual(self.product.get_final_price(), 599.99)
        
        # С добавлением скидки
        self.product.discount_price = 499.99
        self.product.save()
        self.assertEqual(self.product.get_final_price(), 499.99)


class CategoryModelTest(TestCase):
    """Тесты модели Category"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Одежда',
            slug='clothing'
        )
    
    def test_category_creation(self):
        """Тест создания категории"""
        self.assertEqual(self.category.name, 'Одежда')
        self.assertEqual(self.category.slug, 'clothing')


class ProductListViewTest(TestCase):
    """Тесты представления списка товаров"""
    
    def setUp(self):
        self.category = Category.objects.create(name='Тест', slug='test')
        self.product1 = Product.objects.create(
            name='Товар 1',
            slug='product-1',
            price=100,
            category=self.category,
            status='published'
        )
        self.product2 = Product.objects.create(
            name='Товар 2',
            slug='product-2',
            price=200,
            category=self.category,
            status='published'
        )
        self.product3 = Product.objects.create(
            name='Черновик',
            slug='draft',
            price=50,
            category=self.category,
            status='draft'
        )
    
    def test_product_list_view(self):
        """Тест отображения списка товаров"""
        response = self.client.get(reverse('shop:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Товар 1')
        self.assertContains(response, 'Товар 2')
        self.assertNotContains(response, 'Черновик')  # Черновики не показываются
    
    def test_product_list_by_category(self):
        """Тест фильтрации по категории"""
        response = self.client.get(
            reverse('shop:product_list_by_category', kwargs={'category_slug': 'test'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Товар 1')


class ProductDetailViewTest(TestCase):
    """Тесты детальной страницы товара"""
    
    def setUp(self):
        self.category = Category.objects.create(name='Тест', slug='test')
        self.product = Product.objects.create(
            name='Тестовый товар',
            slug='test-product',
            price=99.99,
            category=self.category,
            status='published'
        )
    
    def test_product_detail_view(self):
        """Тест отображения детальной страницы"""
        response = self.client.get(
            reverse('shop:product_detail', kwargs={'slug': 'test-product'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовый товар')
        self.assertContains(response, '99.99')


class ShopUrlsTest(TestCase):
    """Тесты URL-маршрутов"""
    
    def test_home_url(self):
        """Тест главной страницы"""
        response = self.client.get(reverse('shop:home'))
        self.assertEqual(response.status_code, 200)
    
    def test_about_url(self):
        """Тест страницы 'О нас'"""
        response = self.client.get(reverse('shop:about'))
        self.assertEqual(response.status_code, 200)
    
    def test_contact_url(self):
        """Тест страницы 'Контакты'"""
        response = self.client.get(reverse('shop:contact'))
        self.assertEqual(response.status_code, 200)