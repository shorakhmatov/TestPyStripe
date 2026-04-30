from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import User
import uuid


class Item(models.Model):
    
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.IntegerField(help_text="Цена в копейках (например, 1000 = $10.00)")
    currency = models.CharField(max_length=3, default='usd', choices=[('usd', 'USD'), ('eur', 'EUR')])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
    
    def __str__(self):
        return f"{self.name} - {self.get_display_price()}"
    
    def get_display_price(self):
        symbol = '$' if self.currency == 'usd' else '€'
        return f"{symbol}{self.price / 100:.2f}"
    
    def get_stripe_price(self):
        return self.price


class Discount(models.Model):

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name='Название')
    percent_off = models.IntegerField(
        verbose_name='Процент скидки',
        help_text='От 0 до 100',
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    stripe_coupon_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='ID купона в Stripe',
        help_text='Заполняется автоматически при создании'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = 'Скидка'
        verbose_name_plural = 'Скидки'
    
    def __str__(self):
        return f"{self.name} (-{self.percent_off}%)"


class Tax(models.Model):

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name='Название')
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Процент налога',
        help_text='Например: 20.00 для 20%'
    )
    stripe_tax_rate_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='ID налога в Stripe',
        help_text='Заполняется автоматически при создании'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = 'Налог'
        verbose_name_plural = 'Налоги'
    
    def __str__(self):
        return f"{self.name} ({self.percentage}%)"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', '⏳ Ожидает оплаты'),
        ('paid', '💰 Оплачен'),
        ('processing', '⚙️ В обработке'),
        ('confirmed', '✅ Подтвержден'),
        ('shipped', '🚚 Отправлен'),
        ('completed', '🎉 Завершен'),
        ('cancelled', '❌ Отменен'),
        ('refunded', '↩️ Возвращен'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Пользователь'
    )
    items = models.ManyToManyField(Item, through='OrderItem', related_name='orders')
    discount = models.ForeignKey(
        Discount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Скидка'
    )
    tax = models.ForeignKey(
        Tax,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Налог'
    )
    total_amount = models.IntegerField(
        default=0,
        verbose_name='Общая сумма',
        help_text='В копейках/центах'
    )
    currency = models.CharField(
        max_length=3,
        default='usd',
        choices=[('usd', 'USD'), ('eur', 'EUR')],
        verbose_name='Валюта'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    is_paid = models.BooleanField(default=False, verbose_name='Оплачен')
    stripe_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='ID сессии Stripe'
    )
    customer_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email покупателя'
    )
    customer_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Имя покупателя'
    )
    paid_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Дата оплаты'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Заказ #{self.id} - {self.get_display_total()}"
    
    def calculate_total(self):
        subtotal = sum(
            order_item.get_subtotal()
            for order_item in self.order_items.all()
        )
        
        # Применяем скидку
        if self.discount:
            discount_amount = int(subtotal * self.discount.percent_off / 100)
            subtotal -= discount_amount
        
        # Добавляем налог
        if self.tax:
            tax_amount = int(subtotal * float(self.tax.percentage) / 100)
            subtotal += tax_amount
        
        return max(0, subtotal)
    
    def update_total(self):
        self.total_amount = self.calculate_total()
        self.save(update_fields=['total_amount'])
    
    def get_display_total(self):
        symbol = '$' if self.currency == 'usd' else '€'
        return f"{symbol}{self.total_amount / 100:.2f}"
    
    def get_items_count(self):
        return self.order_items.count()
    
    def mark_as_paid(self):
        self.status = 'paid'
        self.is_paid = True
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'is_paid', 'paid_at'])
    
    def can_transition_to(self, new_status):
        valid_transitions = {
            'pending': ['paid', 'cancelled'],
            'paid': ['processing', 'cancelled', 'refunded'],
            'processing': ['confirmed', 'cancelled', 'refunded'],
            'confirmed': ['shipped', 'cancelled', 'refunded'],
            'shipped': ['completed', 'refunded'],
            'completed': ['refunded'],
            'cancelled': [],
            'refunded': [],
        }
        return new_status in valid_transitions.get(self.status, [])
    
    def transition_to(self, new_status):
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Невозможно перевести заказ из '{self.get_status_display()}' в '{dict(self.STATUS_CHOICES).get(new_status, new_status)}'"
            )
        
        old_status = self.status
        self.status = new_status

        if new_status == 'paid':
            self.is_paid = True
            self.paid_at = timezone.now()
        
        self.save(update_fields=['status', 'is_paid', 'paid_at'])
        return True
    
    def get_status_color(self):
        colors = {
            'pending': 'orange',
            'paid': 'green',
            'processing': 'blue',
            'confirmed': 'purple',
            'shipped': 'cyan',
            'completed': 'darkgreen',
            'cancelled': 'red',
            'refunded': 'gray',
        }
        return colors.get(self.status, 'gray')
    
    def get_next_statuses(self):
        transitions = {
            'pending': ['paid', 'cancelled'],
            'paid': ['processing', 'cancelled', 'refunded'],
            'processing': ['confirmed', 'cancelled', 'refunded'],
            'confirmed': ['shipped', 'cancelled', 'refunded'],
            'shipped': ['completed', 'refunded'],
            'completed': ['refunded'],
            'cancelled': [],
            'refunded': [],
        }
        return transitions.get(self.status, [])


class OrderItem(models.Model):

    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='Заказ'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='Товар'
    )
    quantity = models.IntegerField(
        default=1,
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )
    
    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'
        unique_together = ['order', 'item']
    
    def __str__(self):
        return f"{self.item.name} x{self.quantity}"
    
    def get_subtotal(self):
        return self.quantity * self.item.price
    
    def get_display_subtotal(self):
        symbol = '$' if self.item.currency == 'usd' else '€'
        return f"{symbol}{self.get_subtotal() / 100:.2f}"


class Payment(models.Model):

    PAYMENT_TYPE_CHOICES = [
        ('item', 'Оплата товара'),
        ('order', 'Оплата заказа'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('completed', 'Завершен'),
        ('failed', 'Ошибка'),
        ('refunded', 'Возвращен'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Пользователь'
    )
    payment_type = models.CharField(
        max_length=10,
        choices=PAYMENT_TYPE_CHOICES,
        verbose_name='Тип оплаты'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Товар'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Заказ'
    )
    amount = models.IntegerField(
        verbose_name='Сумма',
        help_text='В копейках/центах'
    )
    currency = models.CharField(
        max_length=3,
        default='usd',
        choices=[('usd', 'USD'), ('eur', 'EUR')],
        verbose_name='Валюта'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Stripe Payment Intent ID'
    )
    stripe_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Stripe Session ID'
    )
    customer_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email покупателя'
    )
    customer_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Имя покупателя'
    )
    paid_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Дата оплаты'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.payment_type == 'item' and self.item:
            return f"Платеж #{self.id} - {self.item.name} ({self.get_display_amount()})"
        elif self.payment_type == 'order' and self.order:
            return f"Платеж #{self.id} - Заказ #{self.order.id} ({self.get_display_amount()})"
        return f"Платеж #{self.id} ({self.get_display_amount()})"
    
    def get_display_amount(self):
        symbol = '$' if self.currency == 'usd' else '€'
        return f"{symbol}{self.amount / 100:.2f}"
    
    def mark_as_paid(self):
        self.status = 'completed'
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'paid_at'])
        
        # Обновляем связанный заказ
        if self.order:
            self.order.is_paid = True
            self.order.status = 'paid'
            self.order.paid_at = timezone.now()
            self.order.save(update_fields=['is_paid', 'status', 'paid_at'])
