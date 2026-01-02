# 🏃 Sprint 8: Payment & Subscription

**Phase:** 4 - Monetization & Launch  
**Thời gian:** Tuần 15-16 (10/04/2026 - 23/04/2026)  
**Mục tiêu:** Payment integration, subscription management

---

## 📊 Sprint Overview

| Metric | Target |
|--------|--------|
| Payment | Stripe + VNPay working |
| Subscription | Tier upgrade/downgrade |
| Admin | Basic admin dashboard |

---

## 📋 Task Breakdown

### S8.1 - Database: Subscriptions Table
**Priority:** 🔴 High | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Create subscriptions table migration
- [ ] Add payment_history table
- [ ] SQLAlchemy models

**Migration:**
```python
def upgrade():
    op.create_table('subscriptions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('tier', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('stripe_subscription_id', sa.String(255)),
        sa.Column('status', sa.String(50), default='active'),
    )
    
    op.create_table('payment_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('amount', sa.Numeric(10, 2)),
        sa.Column('currency', sa.String(3), default='VND'),
        sa.Column('provider', sa.String(50)),  # stripe, vnpay
        sa.Column('status', sa.String(50)),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )
```

---

### S8.2 - Subscription Tiers Logic
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Define subscription plans
- [ ] API: GET /api/subscriptions/plans
- [ ] Subscription status check
- [ ] Expiration handling

**Plans:**
```python
SUBSCRIPTION_PLANS = {
    'free': {
        'name': 'Free',
        'price_vnd': 0,
        'price_usd': 0,
        'features': {
            'watchlist_limit': 3,
            'dcf_daily': 1,
            'alerts': 0,
            'pdf_reports': False,
        }
    },
    'basic': {
        'name': 'Basic',
        'price_vnd': 99000,
        'price_usd': 4,
        'stripe_price_id': 'price_xxx',
        'features': {
            'watchlist_limit': 20,
            'dcf_daily': 10,
            'alerts': 5,
            'pdf_reports': False,
        }
    },
    'pro': {
        'name': 'Pro',
        'price_vnd': 299000,
        'price_usd': 12,
        'stripe_price_id': 'price_yyy',
        'features': {
            'watchlist_limit': -1,
            'dcf_daily': -1,
            'alerts': -1,
            'pdf_reports': True,
        }
    }
}
```

**API:**
```
GET /api/subscriptions/plans
Response: {
    "plans": [
        {"id": "basic", "name": "Basic", "price": 99000, ...},
        {"id": "pro", "name": "Pro", "price": 299000, ...}
    ]
}

GET /api/subscriptions/current
Response: {
    "tier": "basic",
    "expires_at": "2026-05-10",
    "status": "active"
}
```

---

### S8.3 - Stripe Integration
**Priority:** 🔴 High | **Estimate:** 3 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Install stripe package
- [ ] Setup Stripe account và API keys
- [ ] Create checkout session
- [ ] Webhook handler for payment events
- [ ] Handle subscription lifecycle

**API:**
```
POST /api/payment/stripe/create-checkout
Body: {"plan": "pro"}
Response: {
    "checkout_url": "https://checkout.stripe.com/..."
}

POST /api/payment/stripe/webhook
(Stripe webhook events)
```

**Code:**
```python
# services/api/routers/payment.py
import stripe

stripe.api_key = os.environ['STRIPE_SECRET_KEY']

@router.post("/stripe/create-checkout")
async def create_checkout(plan: str, user: User = Depends(get_current_user)):
    price_id = SUBSCRIPTION_PLANS[plan]['stripe_price_id']
    
    session = stripe.checkout.Session.create(
        customer_email=user.email,
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url="https://app.stockanalysis.vn/payment/success",
        cancel_url="https://app.stockanalysis.vn/payment/cancel",
        metadata={"user_id": user.id, "plan": plan}
    )
    
    return {"checkout_url": session.url}

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    event = stripe.Webhook.construct_event(
        payload, sig_header, os.environ['STRIPE_WEBHOOK_SECRET']
    )
    
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await activate_subscription(
            user_id=session["metadata"]["user_id"],
            plan=session["metadata"]["plan"],
            stripe_subscription_id=session["subscription"]
        )
    
    return {"status": "success"}
```

---

### S8.4 - VNPay Integration (Vietnam)
**Priority:** 🟡 Medium | **Estimate:** 2 days | **Status:** ⬜ Pending

**Mô tả:**
VNPay là payment gateway phổ biến ở Việt Nam, support ATM cards và QR code.

**Tasks:**
- [ ] Register VNPay merchant account
- [ ] Implement VNPay signature
- [ ] Create payment URL
- [ ] Handle return/IPN callback

**API:**
```
POST /api/payment/vnpay/create
Body: {"plan": "pro", "bank_code": "NCB"}
Response: {
    "payment_url": "https://sandbox.vnpayment.vn/paymentv2/..."
}

GET /api/payment/vnpay/return  (VNPay redirects here)
POST /api/payment/vnpay/ipn    (VNPay server callback)
```

**Code:**
```python
# services/api/services/vnpay_service.py
import hashlib
import hmac
from urllib.parse import urlencode

class VNPayService:
    def __init__(self):
        self.tmn_code = os.environ['VNPAY_TMN_CODE']
        self.secret_key = os.environ['VNPAY_SECRET_KEY']
        self.url = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
    
    def create_payment_url(self, order_id: str, amount: int, order_info: str) -> str:
        params = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": self.tmn_code,
            "vnp_Amount": amount * 100,  # VNPay uses smallest currency unit
            "vnp_CurrCode": "VND",
            "vnp_TxnRef": order_id,
            "vnp_OrderInfo": order_info,
            "vnp_OrderType": "subscription",
            "vnp_Locale": "vn",
            "vnp_ReturnUrl": "https://app.stockanalysis.vn/payment/vnpay/return",
            "vnp_CreateDate": datetime.now().strftime("%Y%m%d%H%M%S"),
        }
        
        # Sort and create query string
        sorted_params = sorted(params.items())
        query_string = urlencode(sorted_params)
        
        # Create signature
        signature = hmac.new(
            self.secret_key.encode(),
            query_string.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return f"{self.url}?{query_string}&vnp_SecureHash={signature}"
```

---

### S8.5 - Invoice Generation
**Priority:** 🟡 Medium | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Generate invoice after payment
- [ ] PDF invoice template
- [ ] Send invoice via email
- [ ] Invoice history API

**Invoice Data:**
```python
invoice = {
    "invoice_number": "INV-2026-0001",
    "date": "2026-04-10",
    "customer": {
        "name": "Nguyen Van A",
        "email": "a@example.com"
    },
    "items": [
        {"description": "Pro Subscription (1 month)", "amount": 299000}
    ],
    "total": 299000,
    "currency": "VND"
}
```

---

### S8.6 - Admin Dashboard (Basic)
**Priority:** 🟡 Medium | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Admin authentication
- [ ] User list với subscription status
- [ ] Revenue metrics
- [ ] Manual subscription management

**Admin API:**
```
GET /api/admin/users?page=1
GET /api/admin/subscriptions
GET /api/admin/revenue/summary
PUT /api/admin/users/{id}/subscription
```

**Metrics:**
- Total users
- Paying users
- MRR (Monthly Recurring Revenue)
- Churn rate

---

## 📅 Daily Plan

### Week 1 (10/04 - 16/04)
| Day | Tasks |
|-----|-------|
| 1 | S8.1 - Database schema |
| 2 | S8.2 - Subscription logic |
| 3 | S8.3 - Stripe setup + checkout |
| 4 | S8.3 - Stripe webhook |
| 5 | S8.3 - Testing Stripe flow |

### Week 2 (17/04 - 23/04)
| Day | Tasks |
|-----|-------|
| 6 | S8.4 - VNPay integration (part 1) |
| 7 | S8.4 - VNPay integration (part 2) |
| 8 | S8.5 - Invoice generation |
| 9 | S8.6 - Admin dashboard (part 1) |
| 10 | S8.6 - Admin dashboard (part 2) |

---

## ✅ Definition of Done

- [ ] Stripe checkout working
- [ ] VNPay payment working
- [ ] Subscription tier updates correctly
- [ ] Invoices generated
- [ ] Admin can view/manage users
- [ ] End-to-end payment flow tested

---

## 📦 Dependencies

```txt
stripe>=7.0.0
```

---

## 💰 Pricing Summary

| Tier | Price VND | Price USD | Billing |
|------|-----------|-----------|---------|
| Free | 0 | 0 | - |
| Basic | 99,000 | $4 | Monthly |
| Pro | 299,000 | $12 | Monthly |

---

**Previous Sprint:** [Sprint 7 - Alerts](./SPRINT_7.md)  
**Next Sprint:** [Sprint 9 - Launch](./SPRINT_9.md)

