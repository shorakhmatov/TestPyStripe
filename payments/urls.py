
from django.urls import path
from . import views

urlpatterns = [
    path('', views.item_list, name='home'),

    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('my-orders/', views.my_orders_view, name='my_orders'),

    path('items/', views.item_list, name='item_list'),
    path('buy/<int:id>/', views.buy_item, name='buy_item'),
    path('item/<int:id>/', views.item_detail, name='item_detail'),
    
    path('order/<int:id>/', views.order_detail, name='order_detail'),
    path('buy/order/<int:id>/', views.buy_order, name='buy_order'),
    
    path('success/', views.success_view, name='success'),
    path('cancel/', views.cancel_view, name='cancel'),
]
