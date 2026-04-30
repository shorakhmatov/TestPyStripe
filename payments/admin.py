from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Item, Order, Discount, Tax, OrderItem, Payment


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):

    list_display = ['id', 'name', 'get_display_price', 'currency', 'get_sales_count', 'created_at']
    list_filter = ['currency', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'get_sales_count']
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'name', 'description')
        }),
        ('Цена', {
            'fields': ('price', 'currency', 'get_display_price')
        }),
        ('Статистика', {
            'fields': ('get_sales_count',),
            'description': 'Количество продаж этого товара'
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_sales_count(self, obj):
        return obj.payments.filter(status='completed').count()
    get_sales_count.short_description = 'Продажи'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    autocomplete_fields = ['item']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['get_display_amount', 'status', 'customer_email', 'paid_at']
    fields = ['payment_type', 'get_display_amount', 'status', 'customer_email', 'paid_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def get_display_amount(self, obj):
        return obj.get_display_amount()
    get_display_amount.short_description = 'Сумма'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'get_user_info', 'get_items_summary', 'get_display_total', 
        'currency', 'get_status_display', 'get_workflow_stage', 'created_at'
    ]
    list_filter = [
        'status', 'is_paid', 'currency', 'created_at', 
        'discount', 'tax', 'user'
    ]
    search_fields = [
        'id', 'stripe_session_id', 'customer_email', 
        'customer_name', 'user__username', 'user__email'
    ]
    readonly_fields = [
        'id', 'created_at', 'total_amount', 'get_display_total',
        'paid_at', 'get_next_statuses_display'
    ]
    filter_horizontal = ['items']
    inlines = [OrderItemInline, PaymentInline]
    date_hierarchy = 'created_at'
    actions = ['mark_processing', 'mark_confirmed', 'mark_shipped', 'mark_completed', 'mark_cancelled']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'user', 'status', 'get_next_statuses_display', 'currency', 'created_at')
        }),
        ('Покупатель', {
            'fields': ('customer_name', 'customer_email'),
            'description': 'Информация о покупателе (если не авторизован)'
        }),
        ('Финансы', {
            'fields': ('total_amount', 'get_display_total', 'paid_at')
        }),
        ('Скидки и налоги', {
            'fields': ('discount', 'tax'),
            'classes': ('collapse',)
        }),
        ('Stripe', {
            'fields': ('stripe_session_id',),
            'classes': ('collapse',)
        }),
    )
    
    def get_user_info(self, obj):
        if obj.user:
            return f"👤 {obj.user.username}"
        elif obj.customer_email:
            return f"✉️ {obj.customer_email}"
        return "🛒 Гость"
    get_user_info.short_description = 'Покупатель'
    
    def get_items_summary(self, obj):
        count = obj.get_items_count()
        total_qty = sum(item.quantity for item in obj.order_items.all())
        return f"{count} товара ({total_qty} шт.)"
    get_items_summary.short_description = 'Товары'
    
    def get_display_total(self, obj):
        return obj.get_display_total()
    get_display_total.short_description = 'Сумма'
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    get_status_display.short_description = 'Статус'
    get_status_display.admin_order_field = 'status'
    
    def get_workflow_stage(self, obj):
        stages = {
            'pending': '⏳ Ожидание',
            'paid': '� Оплачен',
            'processing': '⚙️ Обработка',
            'confirmed': '✅ Подтвержден',
            'shipped': '🚚 Отправлен',
            'completed': '🎉 Завершен',
            'cancelled': '❌ Отменен',
            'refunded': '↩️ Возвращен',
        }
        return stages.get(obj.status, obj.status)
    get_workflow_stage.short_description = 'Этап'
    
    def get_next_statuses_display(self, obj):
        next_statuses = obj.get_next_statuses()
        if not next_statuses:
            return "Нет доступных переходов"
        
        status_labels = dict(Order.STATUS_CHOICES)
        labels = [status_labels.get(s, s) for s in next_statuses]
        return " → ".join(labels)
    get_next_statuses_display.short_description = 'Возможные переходы'
    
    # смены статусов
    def mark_processing(self, request, queryset):
        updated = 0
        for order in queryset:
            try:
                order.transition_to('processing')
                updated += 1
            except ValueError as e:
                self.message_user(request, f"Заказ #{order.id}: {e}", level='ERROR')
        self.message_user(request, f'{updated} заказов переведено в обработку')
    mark_processing.short_description = '⚙️ Перевести в обработку'
    
    def mark_confirmed(self, request, queryset):
        updated = 0
        for order in queryset:
            try:
                order.transition_to('confirmed')
                updated += 1
            except ValueError as e:
                self.message_user(request, f"Заказ #{order.id}: {e}", level='ERROR')
        self.message_user(request, f'{updated} заказов подтверждено')
    mark_confirmed.short_description = '✅ Подтвердить заказ'
    
    def mark_shipped(self, request, queryset):
        updated = 0
        for order in queryset:
            try:
                order.transition_to('shipped')
                updated += 1
            except ValueError as e:
                self.message_user(request, f"Заказ #{order.id}: {e}", level='ERROR')
        self.message_user(request, f'{updated} заказов отмечено как отправленные')
    mark_shipped.short_description = '🚚 Отметить отправленным'
    
    def mark_completed(self, request, queryset):
        updated = 0
        for order in queryset:
            try:
                order.transition_to('completed')
                updated += 1
            except ValueError as e:
                self.message_user(request, f"Заказ #{order.id}: {e}", level='ERROR')
        self.message_user(request, f'{updated} заказов завершено')
    mark_completed.short_description = '🎉 Завершить заказ'
    
    def mark_cancelled(self, request, queryset):
        updated = 0
        for order in queryset:
            try:
                order.transition_to('cancelled')
                updated += 1
            except ValueError as e:
                self.message_user(request, f"Заказ #{order.id}: {e}", level='ERROR')
        self.message_user(request, f'{updated} заказов отменено')
    mark_cancelled.short_description = '❌ Отменить заказ'


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['name', 'percent_off', 'is_active', 'stripe_coupon_id', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'stripe_coupon_id']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'percent_off', 'is_active')
        }),
        ('Stripe', {
            'fields': ('stripe_coupon_id',),
            'description': 'ID купона создается автоматически в Stripe'
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ['name', 'percentage', 'is_active', 'stripe_tax_rate_id', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'stripe_tax_rate_id']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'percentage', 'is_active')
        }),
        ('Stripe', {
            'fields': ('stripe_tax_rate_id',),
            'description': 'ID налоговой ставки создается автоматически в Stripe'
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'item', 'quantity', 'get_display_subtotal']
    list_filter = ['order__currency', 'order__status']
    search_fields = ['order__id', 'item__name']
    autocomplete_fields = ['order', 'item']
    
    def get_display_subtotal(self, obj):
        return obj.get_display_subtotal()
    get_display_subtotal.short_description = 'Подытог'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'get_user_info', 'payment_type', 'get_item_or_order', 
        'get_display_amount', 'get_status_display', 'paid_at', 'created_at'
    ]
    list_filter = [
        'status', 'payment_type', 'currency', 'created_at', 'user'
    ]
    search_fields = [
        'id', 'stripe_payment_intent_id', 'stripe_session_id',
        'customer_email', 'customer_name', 'user__username', 'user__email'
    ]
    readonly_fields = [
        'id', 'created_at', 'paid_at', 'get_display_amount'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'user', 'payment_type', 'status', 'created_at')
        }),
        ('Оплаченный объект', {
            'fields': ('item', 'order'),
            'description': 'Товар или заказ, который был оплачен'
        }),
        ('Финансы', {
            'fields': ('amount', 'currency', 'get_display_amount', 'paid_at')
        }),
        ('Покупатель', {
            'fields': ('customer_name', 'customer_email'),
        }),
        ('Stripe', {
            'fields': ('stripe_payment_intent_id', 'stripe_session_id'),
            'classes': ('collapse',)
        }),
    )
    
    def get_user_info(self, obj):
        if obj.user:
            return f"👤 {obj.user.username}"
        elif obj.customer_email:
            return f"✉️ {obj.customer_email}"
        return "🛒 Гость"
    get_user_info.short_description = 'Покупатель'
    
    def get_item_or_order(self, obj):
        if obj.payment_type == 'item' and obj.item:
            return f"📦 {obj.item.name}"
        elif obj.payment_type == 'order' and obj.order:
            return f"🛒 Заказ #{obj.order.id}"
        return "❓ Неизвестно"
    get_item_or_order.short_description = 'Объект оплаты'
    
    def get_display_amount(self, obj):
        return obj.get_display_amount()
    get_display_amount.short_description = 'Сумма'
    
    def get_status_display(self, obj):
        status_colors = {
            'pending': '🟡',
            'completed': '🟢',
            'failed': '🔴',
            'refunded': '🔵',
        }
        return f"{status_colors.get(obj.status, '⚪')} {obj.get_status_display()}"
    get_status_display.short_description = 'Статус'



class UserPaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['get_display_amount', 'status', 'created_at']
    fields = ['payment_type', 'get_display_amount', 'status', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def get_display_amount(self, obj):
        return obj.get_display_amount()
    get_display_amount.short_description = 'Сумма'


class UserOrderInline(admin.TabularInline):
    model = Order
    extra = 0
    readonly_fields = ['get_display_total', 'status', 'created_at']
    fields = ['get_display_total', 'status', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def get_display_total(self, obj):
        return obj.get_display_total()
    get_display_total.short_description = 'Сумма'


admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = [
        'username', 'email', 'get_total_spent', 'get_orders_count', 
        'get_payments_count', 'is_staff', 'date_joined'
    ]
    list_filter = ['is_staff', 'is_superuser', 'date_joined']
    inlines = [UserOrderInline, UserPaymentInline]
    
    def get_total_spent(self, obj):
        total = sum(
            p.amount for p in obj.payments.filter(status='completed')
        )
        symbol = '$'  
        return f"{symbol}{total / 100:.2f}"
    get_total_spent.short_description = '💰 Потрачено'
    
    def get_orders_count(self, obj):
        return obj.orders.count()
    get_orders_count.short_description = '🛒 Заказы'
    
    def get_payments_count(self, obj):
        return obj.payments.filter(status='completed').count()
    get_payments_count.short_description = '💳 Платежи'
