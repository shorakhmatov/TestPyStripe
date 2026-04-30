

import stripe
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models

from .models import Item, Order, Discount, Tax, Payment


def buy_item(request, id):

    item = get_object_or_404(Item, id=id)

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        currency=item.currency,
        status='pending',  
        customer_email=request.user.email if request.user.is_authenticated else None,
        customer_name=request.user.get_full_name() if request.user.is_authenticated and request.user.get_full_name() else None,
    )
    
    # Добавляем товар в заказ
    from .models import OrderItem
    OrderItem.objects.create(
        order=order,
        item=item,
        quantity=1
    )
    

    order.update_total()
    
    stripe.api_key = settings.STRIPE_SECRET_KEYS.get(item.currency, settings.STRIPE_SECRET_KEY_USD)
    
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': item.currency,
                'product_data': {
                    'name': item.name,
                    'description': item.description or '',
                },
                'unit_amount': item.price,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri('/success/') + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri('/cancel/') + '?session_id={CHECKOUT_SESSION_ID}',
        metadata={
            'order_id': str(order.id),
            'payment_type': 'order',
        }
    )

    order.stripe_session_id = session.id
    order.save(update_fields=['stripe_session_id'])

    payment = Payment.objects.create(
        user=request.user if request.user.is_authenticated else None,
        payment_type='order',
        order=order,  
        item=item,
        amount=item.price,
        currency=item.currency,
        status='pending',
        stripe_session_id=session.id,
        customer_email=request.user.email if request.user.is_authenticated else None,
        customer_name=request.user.get_full_name() if request.user.is_authenticated and request.user.get_full_name() else None,
    )
    
    return JsonResponse({'session_id': session.id})


def item_detail(request, id):

    item = get_object_or_404(Item, id=id)
  
    stripe_public_key = settings.STRIPE_PUBLIC_KEYS.get(item.currency, settings.STRIPE_PUBLIC_KEY_USD)
    
    return render(request, 'payments/item_detail.html', {
        'item': item,
        'stripe_public_key': stripe_public_key,
    })


def item_list(request):
    items = Item.objects.all()
    return render(request, 'payments/item_list.html', {'items': items})



def buy_order(request, id):

    order = get_object_or_404(Order, id=id)

    order.update_total()
    
    stripe.api_key = settings.STRIPE_SECRET_KEYS.get(order.currency, settings.STRIPE_SECRET_KEY_USD)
    
    line_items = []
    for order_item in order.order_items.select_related('item'):
        item = order_item.item
        line_items.append({
            'price_data': {
                'currency': order.currency,
                'product_data': {
                    'name': item.name,
                    'description': item.description or '',
                },
                'unit_amount': item.price,
            },
            'quantity': order_item.quantity,
        })

    discounts = []
    if order.discount and order.discount.stripe_coupon_id:
        discounts = [{'coupon': order.discount.stripe_coupon_id}]
    
    tax_rates = []
    if order.tax and order.tax.stripe_tax_rate_id:
        tax_rates = [order.tax.stripe_tax_rate_id]

    session_data = {
        'payment_method_types': ['card'],
        'line_items': line_items,
        'mode': 'payment',
        'success_url': request.build_absolute_uri('/success/') + '?session_id={CHECKOUT_SESSION_ID}',
        'cancel_url': request.build_absolute_uri('/cancel/') + '?session_id={CHECKOUT_SESSION_ID}',
        'metadata': {
            'payment_type': 'order',
            'order_id': str(order.id),
        }
    }
    
    if discounts:
        session_data['discounts'] = discounts
    
    if tax_rates:
        session_data['tax_rates'] = tax_rates
    
    session = stripe.checkout.Session.create(**session_data)

    order.stripe_session_id = session.id
    order.save(update_fields=['stripe_session_id'])

    payment = Payment.objects.create(
        user=request.user if request.user.is_authenticated else None,
        payment_type='order',
        order=order,
        amount=order.total_amount,
        currency=order.currency,
        status='pending',
        stripe_session_id=session.id,
        customer_email=request.user.email if request.user.is_authenticated else order.customer_email,
        customer_name=request.user.get_full_name() if request.user.is_authenticated and request.user.get_full_name() else order.customer_name,
    )
    
    return JsonResponse({'session_id': session.id})


def order_detail(request, id):

    order = get_object_or_404(Order.objects.prefetch_related('order_items__item'), id=id)

    order.update_total()

    stripe_public_key = settings.STRIPE_PUBLIC_KEYS.get(order.currency, settings.STRIPE_PUBLIC_KEY_USD)
    
    return render(request, 'payments/order_detail.html', {
        'order': order,
        'stripe_public_key': stripe_public_key,
    })


@csrf_exempt
def create_payment_intent(request):
    pass


def stripe_webhook(request):

    pass


def success_view(request):

    session_id = request.GET.get('session_id')
    
    if session_id:
        try:
            payment = Payment.objects.get(stripe_session_id=session_id)
            payment.mark_as_paid()

            if payment.order:
                payment.order.mark_as_paid()

                try:
                    payment.order.transition_to('processing')
                except ValueError:
                    pass 
            
            stripe.api_key = settings.STRIPE_SECRET_KEY_USD
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                if session.payment_status == 'paid' and session.customer_details:
                    
                    payment.customer_email = session.customer_details.email
                    payment.customer_name = session.customer_details.name
                    payment.save(update_fields=['customer_email', 'customer_name'])
                    
                    if payment.order:
                        payment.order.customer_email = session.customer_details.email
                        payment.order.customer_name = session.customer_details.name
                        payment.order.save(update_fields=['customer_email', 'customer_name'])
            except Exception as e:
                print(f"Stripe API error: {e}")
                
        except Payment.DoesNotExist:
            pass
    else:

        if request.user.is_authenticated:
            try:
                payment = Payment.objects.filter(
                    user=request.user,
                    status='pending'
                ).latest('created_at')
                payment.mark_as_paid()
            except Payment.DoesNotExist:
                pass
    
    return render(request, 'payments/success.html')


def cancel_view(request):
    session_id = request.GET.get('session_id')
    
    if session_id:
        try:
            payment = Payment.objects.get(stripe_session_id=session_id)
            payment.status = 'failed'
            payment.save(update_fields=['status'])
        except Payment.DoesNotExist:
            pass
    
    return render(request, 'payments/cancel.html')

def register_view(request):
    """
    Регистрация нового пользователя
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        errors = []
        if not username:
            errors.append('Имя пользователя обязательно')
        if not email:
            errors.append('Email обязателен')
        if not password:
            errors.append('Пароль обязателен')
        if password != password2:
            errors.append('Пароли не совпадают')
        if len(password) < 6:
            errors.append('Пароль должен быть минимум 6 символов')
        
        if User.objects.filter(username=username).exists():
            errors.append('Пользователь с таким именем уже существует')
        if User.objects.filter(email=email).exists():
            errors.append('Пользователь с таким email уже существует')
        
        if errors:
            return render(request, 'payments/register.html', {
                'errors': errors,
                'username': username,
                'email': email,
            })
        
        # Создание пользователя
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Автоматический вход
        login(request, user)
        messages.success(request, f'Добро пожаловать, {username}! Вы успешно зарегистрировались.')
        return redirect('profile')
    
    return render(request, 'payments/register.html')


@login_required
def profile_view(request):
    """
    Личный кабинет пользователя
    """
    user = request.user

    orders_count = user.orders.count()
    payments_count = user.payments.filter(status='completed').count()
    
    total_spent = user.payments.filter(
        status='completed'
    ).aggregate(
        total=models.Sum('amount')
    )['total'] or 0

    recent_orders = user.orders.order_by('-created_at')[:5]
    
    recent_payments = user.payments.order_by('-created_at')[:5]
    
    return render(request, 'payments/profile.html', {
        'user': user,
        'orders_count': orders_count,
        'payments_count': payments_count,
        'total_spent': total_spent / 100,  
        'recent_orders': recent_orders,
        'recent_payments': recent_payments,
    })


@login_required
def my_orders_view(request):
    """
    История заказов пользователя
    """
    user = request.user
    orders = user.orders.order_by('-created_at')
    
    return render(request, 'payments/my_orders.html', {
        'orders': orders,
    })
