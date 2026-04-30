# Django + Stripe API 


### ✅ Обязательные требования
- [x] **Модель Item** с полями: `name`, `description`, `price`, `currency`
- [x] **GET /buy/{id}** - создание Stripe Checkout Session и получение `session.id`
- [x] **GET /item/{id}** - HTML страница с информацией о товаре и кнопкой Buy
- [x] **JavaScript редирект** на Stripe Checkout через `stripe.redirectToCheckout()`

### ⭐ Бонусные задачи - ВСЕ реализованы
- [x] **Docker** - полная поддержка Docker и docker-compose
- [x] **Environment Variables** - все ключи и настройки через .env
- [x] **Django Admin** - полная настройка админки для всех моделей
- [x] **Модель Order** - объединение нескольких Item в заказ с общей оплатой
- [x] **Модели Discount, Tax** - скидки и налоги для заказов
- [x] **Мультивалютность** - USD и EUR с разными Stripe Keypair
- [x] **Модель Payment** - отслеживание всех платежей
- [x] **Аутентификация** - регистрация, вход, личный кабинет
- [x] **Workflow заказов** - полный цикл от pending до completed

## 📊 Workflow заказа

```
Пользователь выбирает товар
        ↓
GET /buy/{id} → Создается Order (status: pending)
        ↓
Stripe Checkout Session → Оплата
        ↓
Успешная оплата → Order status: paid → processing
        ↓
Админ управляет дальнейшими статусами:
  processing → confirmed → shipped → completed
```

**Статусы заказа (управляются админом):**
- ⏳ `pending` - Ожидает оплаты
- 💰 `paid` - Оплачен (автоматически после Stripe)
- ⚙️ `processing` - В обработке (автоматически после оплаты)
- ✅ `confirmed` - Подтвержден
- 🚚 `shipped` - Отправлен
- 🎉 `completed` - Завершен
- ❌ `cancelled` - Отменен

## 🚀 Быстрый старт (локально)

## 📋 Требования

- Python 3.10+
- Django 4.2+
- Stripe Account (бесплатный тестовый режим)

## 🚀 Быстрый старт

### 1. Настройка окружения

```bash
# Создай виртуальное окружение
python -m venv venv

# Активируй (Windows)
venv\Scripts\activate

# Установи зависимости
pip install -r requirements.txt
```

### 2. Настройка Stripe

1. Зарегистрируйся на [stripe.com](https://stripe.com)
2. Перейди в Developers → API keys
3. Скопируй `Publishable key` и `Secret key`
4. Бонус: создай второй keypair для EUR валюты (добавь новый аккаунт в Stripe)

### 3. Конфигурация

```bash
# Скопируй пример env файла
cp .env.example .env

# Отредактируй .env, добавить свои ключи:
SECRET_KEY=your-secret-key
STRIPE_PUBLIC_KEY_USD=pk_test_...
STRIPE_SECRET_KEY_USD=sk_test_...
STRIPE_PUBLIC_KEY_EUR=pk_test_...
STRIPE_SECRET_KEY_EUR=sk_test_...
```

### 4. Инициализация БД

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py init_data  # Создаст тестовые товары
```

### 5. Запуск

```bash
python manage.py runserver
```

http://localhost:8000/

---

## 📁 Структура проекта

```
TestPyStripe/
├── payments/
│   ├── models.py              # Item, Order, Discount, Tax, Payment
│   ├── views.py               # API endpoints + frontend
│   ├── urls.py                # URL routing
│   ├── admin.py               # Django Admin config
│   └── management/
│       └── commands/
│           └── init_data.py   # Создание тестовых товаров
├── templates/
│   └── payments/
│       ├── item_list.html     # Каталог товаров
│       ├── item_detail.html   # Страница товара + Stripe JS
│       ├── order_detail.html  # Страница заказа
│       ├── success.html       # Успешная оплата
│       ├── cancel.html        # Отмена оплаты
│       ├── register.html      # Регистрация
│       ├── profile.html       # Личный кабинет
│       └── my_orders.html     # История заказов
├── stripe_project/
│   ├── settings.py            # Настройки + Stripe keys
│   └── urls.py                # Корневые URL + auth
├── requirements.txt
├── .env.example
├── Dockerfile                 # Docker support
├── docker-compose.yml
└── README.md                  # Этот файл
```

---

## 🔌 API Endpoints

### Основные endpoints
| Method | URL | Описание |
|--------|-----|----------|
| GET | `/` | Главная страница - каталог товаров |
| GET | `/items/` | Список всех товаров |
| GET | `/item/{id}/` | Страница товара с кнопкой Buy |
| GET | `/buy/{id}/` | Создает Stripe Session для товара |
| GET | `/order/{id}/` | Страница заказа с несколькими товарами |
| GET | `/buy/order/{id}/` | Оплата всего заказа |
| GET | `/success/` | Страница успешной оплаты |
| GET | `/cancel/` | Страница отмены оплаты |

### Аутентификация
| Method | URL | Описание |
|--------|-----|----------|
| GET/POST | `/register/` | Регистрация нового пользователя |
| GET/POST | `/accounts/login/` | Вход в систему |
| GET | `/accounts/logout/` | Выход из системы |
| GET | `/profile/` | Личный кабинет (требует вход) |
| GET | `/my-orders/` | История заказов (требует вход) |

### Админка
| URL | Описание |
|-----|----------|
| `/admin/` | Django Admin панель |

## 🧪 Тестирование с помощью curl

### Получение Stripe Session ID для товара:
```bash
curl -X GET http://localhost:8000/buy/1/
```

**Ответ:**
```json
{"session_id": "cs_test_xxxxxxxxxxxx"}
```

### Получение HTML страницы товара:
```bash
curl -X GET http://localhost:8000/item/1/
```

### Получение JSON данных товара (для API):
```bash
curl -X GET http://localhost:8000/item/1/ -H "Accept: application/json"
```

## 🎨 Как это работает

### 1. Просмотр товаров
1. Откройте http://localhost:8000/ - главная страница с каталогом
2. Или http://localhost:8000/items/ - список всех товаров
3. Товары в разных валютах (USD/EUR) используют разные Stripe ключи

### 2. Покупка товара
1. Откройте страницу товара: http://localhost:8000/item/1/
2. Нажмите кнопку "Купить сейчас"
3. Происходит:
   - AJAX запрос на `/buy/1/`
   - Создается **Order** со статусом `pending`
   - Создается Stripe Checkout Session
   - Редирект на Stripe Checkout
4. Введите тестовую карту `4242 4242 4242 4242`
5. После оплаты:
   - Order автоматически меняет статус: `pending` → `paid` → `processing`
   - Показывается страница успеха

### 3. Управление заказами (админ)
1. Зайдите в админку: http://localhost:8000/admin/
2. Перейдите в раздел **Заказы**
3. Видите все заказы с:
   - Информацией о покупателе
   - Список товаров
   - Текущий статус и этап workflow
   - Возможные переходы
4. Используйте **Actions** (вверху списка) для массовой смены статуса:
   - ⚙️ Перевести в обработку
   - ✅ Подтвердить заказ
   - 🚚 Отметить отправленным
   - 🎉 Завершить заказ
   - ❌ Отменить заказ

### 4. Личный кабинет пользователя
1. Зарегистрируйтесь: http://localhost:8000/register/
2. Или войдите: http://localhost:8000/accounts/login/
   - Тестовый аккаунт: `testuser` / `test123`
3. После входа в личном кабинете `/profile/`:
   - Статистика заказов и платежей
   - Последние заказы с workflow прогресс-баром
   - История платежей
4. На странице `/my-orders/` видны все заказы с визуальным workflow

### 5. Workflow заказа

**Автоматические переходы:**
- Пользователь нажимает "Купить" → `pending` (ожидает оплаты)
- Успешная оплата в Stripe → `paid` (оплачен)
- Автоматически после оплаты → `processing` (в обработке)

**Управляемые админом переходы:**
- `processing` → `confirmed` (подтвержден)
- `confirmed` → `shipped` (отправлен)
- `shipped` → `completed` (завершен)

**Дополнительные переходы:**
- Любой статус → `cancelled` (отменен)
- Оплаченные статусы → `refunded` (возвращен)

## 🐳 Запуск через Docker

```bash
# Собрать и запустить
docker-compose up --build

# Или в фоновом режиме
docker-compose up -d --build

# Создать суперпользователя
docker-compose exec web python manage.py createsuperuser

# Создать тестовые данные
docker-compose exec web python manage.py init_data
```

Приложение будет доступно на http://localhost:8000/

## 📊 Модели данных

### Item
- `name` - название товара
- `description` - описание
- `price` - цена в копейках/центах
- `currency` - валюта (usd/eur)

### Order
- `user` - покупатель (FK к User)
- `items` - ManyToMany через OrderItem
- `total_amount` - общая сумма (автоматический расчет)
- `currency` - валюта заказа
- `status` - статус заказа (workflow)
- `is_paid` - флаг оплаты
- `paid_at` - дата оплаты
- `discount` - скидка (FK)
- `tax` - налог (FK)
- `stripe_session_id` - ID сессии Stripe
- `customer_email/name` - данные покупателя

### OrderItem
- `order` - заказ (FK)
- `item` - товар (FK)
- `quantity` - количество
- `unit_price` - цена на момент покупки

### Payment
- `user` - пользователь (FK)
- `order` - заказ (FK, optional)
- `item` - товар (FK, optional)
- `payment_type` - тип (item/order)
- `amount` - сумма
- `currency` - валюта
- `status` - статус платежа
- `stripe_session_id` - ID сессии
- `stripe_payment_intent_id` - ID Payment Intent

### Discount
- `name` - название
- `percent_off` - процент скидки
- `stripe_coupon_id` - ID купона в Stripe

### Tax
- `name` - название
- `percentage` - процент налога
- `stripe_tax_rate_id` - ID налоговой ставки в Stripe

## 🔑 Тестовые аккаунты

| Роль | Логин | Пароль | URL |
|------|-------|--------|-----|
| Администратор | `admin` | `admin123` | /admin/ |
| Администратор | `admin2` | `123456` | /admin/ |
| Пользователь | `testuser` | `test123` | /profile/ |

## ✅ Проверка работоспособности

1. **Проверка API:**
   ```bash
   curl http://localhost:8000/buy/1/
   # Должен вернуть {"session_id": "cs_..."}
   ```

2. **Проверка HTML страницы:**
   ```bash
   curl http://localhost:8000/item/1/ | grep -i "stripe"
   # Должен содержать ссылки на Stripe JS
   ```

3. **Проверка админки:**
   - Откройте http://localhost:8000/admin/
   - Войдите как `admin` / `admin123`
   - Проверьте разделы: Items, Orders, Payments, Discounts, Tax

4. **Проверка workflow:**
   - Купите товар через интерфейс
   - Проверьте в админке, что Order создался со статусом `processing`
   - Поменяйте статус через Actions
   - Проверьте в `/my-orders/` (предварительно войдя)

## 📚 Полезные ссылки

- [Stripe Checkout Documentation](https://stripe.com/docs/checkout)
- [Stripe Python Library](https://stripe.com/docs/api/python)
- [Stripe Test Cards](https://stripe.com/docs/testing)
- [Django Documentation](https://docs.djangoproject.com/)

## 📝 Лицензия

Этот проект создан для тестового задания.

---

**Готов к тестированию!** 🚀

---

## 📚 Полезные ссылки

**Stripe Документация:**
- [Quick Start](https://stripe.com/docs/checkout/quickstart)
- [Python API](https://stripe.com/docs/api?lang=python)
- [Checkout Session](https://stripe.com/docs/api/checkout/sessions/create)
- [Test Cards](https://stripe.com/docs/testing#cards)

**Django:**
- [Models](https://docs.djangoproject.com/en/4.2/topics/db/models/)
- [Views](https://docs.djangoproject.com/en/4.2/topics/http/views/)

---

## 🧪 Тестовые карты Stripe

| Номер | Результат |
|-------|-----------|
| `4242 4242 4242 4242` | Успешная оплата |
| `4000 0000 0000 0002` | Карта отклонена |

Дата: любая будущая, CVC: любой 3 цифры

---

## 🐳 Запуск с Docker 

```bash
docker-compose up --build
```

#   t e s t P y S t r i p e  
 #   t e s t P y S t r i p e  
 #   t e s t P y S t r i p e  
 