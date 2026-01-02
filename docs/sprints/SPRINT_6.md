# 🏃 Sprint 6: Dashboard & User System

**Phase:** 3 - User Experience  
**Thời gian:** Tuần 11-12 (13/03/2026 - 26/03/2026)  
**Mục tiêu:** New dashboard UI, user authentication, watchlist

---

## 📊 Sprint Overview

| Metric | Target |
|--------|--------|
| Auth | JWT-based login/register |
| UI | Responsive dashboard |
| Features | Watchlist, Stock screener |

---

## 📋 Task Breakdown

### S6.1 - Database: Users, Watchlists Tables
**Priority:** 🔴 High | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Create Alembic migration cho users table
- [ ] Create migration cho watchlists table
- [ ] Add SQLAlchemy models
- [ ] Test migrations

**Migration:**
```python
# alembic/versions/002_users_watchlists.py
def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('tier', sa.String(50), default='free'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )
    
    op.create_table('watchlists',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('ticker', sa.String(10), nullable=False),
        sa.Column('added_at', sa.DateTime(), default=sa.func.now()),
    )
```

---

### S6.2 - User Authentication (JWT)
**Priority:** 🔴 High | **Estimate:** 3 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Install python-jose, passlib
- [ ] Create auth service (hash password, verify, create token)
- [ ] Login endpoint
- [ ] Protected route decorator
- [ ] Refresh token logic

**API:**
```
POST /api/users/login
Body: {"email": "user@example.com", "password": "secret"}
Response: {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

**Code:**
```python
# services/api/services/auth_service.py
from passlib.context import CryptContext
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"])
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(hours=1)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
```

---

### S6.3 - User Registration + Email Verification
**Priority:** 🟡 Medium | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Register endpoint
- [ ] Email validation
- [ ] Password strength check
- [ ] (Optional) Email verification flow

**API:**
```
POST /api/users/register
Body: {
    "email": "user@example.com",
    "password": "StrongP@ss123"
}
Response: {
    "message": "User created successfully",
    "user_id": 1
}
```

---

### S6.4 - Dashboard Redesign (Tailwind CSS)
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Install Tailwind CSS via CDN
- [ ] Create new dashboard layout
- [ ] Summary cards (market overview)
- [ ] Top movers widget
- [ ] Watchlist widget

**Layout:**
```html
<div class="dashboard-grid">
    <!-- Row 1: Summary Cards -->
    <div class="summary-card">VN-Index: 1,250 (+1.2%)</div>
    <div class="summary-card">HNX: 230 (+0.8%)</div>
    <div class="summary-card">UPCOM: 92 (-0.3%)</div>
    <div class="summary-card">Portfolio: +5.2%</div>
    
    <!-- Row 2: Charts + Movers -->
    <div class="market-chart col-span-2">Market Overview</div>
    <div class="top-movers">Top Gainers/Losers</div>
    
    <!-- Row 3: Watchlist -->
    <div class="watchlist col-span-3">My Watchlist</div>
</div>
```

---

### S6.5 - Watchlist Feature (CRUD)
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] GET /api/watchlist - list user's watchlist
- [ ] POST /api/watchlist - add stock
- [ ] DELETE /api/watchlist/{ticker} - remove stock
- [ ] UI: Add/remove button on stock page
- [ ] Real-time price updates

**API:**
```
GET /api/watchlist
Response: {
    "watchlist": [
        {"ticker": "FPT", "price": 92500, "change": 2.5},
        {"ticker": "VNM", "price": 78000, "change": -1.2}
    ]
}

POST /api/watchlist
Body: {"ticker": "MWG"}

DELETE /api/watchlist/MWG
```

---

### S6.6 - Stock Screener
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Filter UI (PE ratio, market cap, sector, ...)
- [ ] POST /api/screener/filter endpoint
- [ ] Results table with pagination
- [ ] Save filter presets (optional)

**API:**
```
POST /api/screener/filter
Body: {
    "filters": {
        "pe_ratio": {"min": 5, "max": 20},
        "market_cap": {"min": 1000000000000},
        "sector": ["Technology", "Banking"],
        "rsi": {"max": 30}  // Oversold stocks
    },
    "sort_by": "market_cap",
    "order": "desc",
    "page": 1,
    "limit": 20
}
Response: {
    "results": [...],
    "total": 45,
    "page": 1,
    "pages": 3
}
```

**Filter Options:**
| Filter | Type | Description |
|--------|------|-------------|
| pe_ratio | range | Price/Earnings ratio |
| pb_ratio | range | Price/Book ratio |
| market_cap | range | Market capitalization |
| sector | multi-select | Industry sector |
| exchange | select | HOSE, HNX, UPCOM |
| rsi | range | RSI indicator |
| price_change | range | % change today |

---

## 📁 New Files

```
services/api/
├── routers/
│   ├── users.py          # Auth endpoints
│   ├── watchlist.py      # Watchlist CRUD
│   └── screener.py       # Stock screener
├── services/
│   ├── auth_service.py   # JWT, password
│   └── user_service.py   # User operations
└── models/
    ├── user.py           # User model
    └── watchlist.py      # Watchlist model

services/frontend/pages/
├── dashboard.html        # New dashboard
├── login.html            # Login page
├── register.html         # Register page
└── screener.html         # Stock screener
```

---

## 📅 Daily Plan

### Week 1 (13/03 - 19/03)
| Day | Tasks |
|-----|-------|
| 1 | S6.1 - Database migrations |
| 2 | S6.2 - Auth service setup |
| 3 | S6.2 - Login endpoint |
| 4 | S6.2 - Protected routes |
| 5 | S6.3 - Registration |

### Week 2 (20/03 - 26/03)
| Day | Tasks |
|-----|-------|
| 6 | S6.4 - Dashboard UI (part 1) |
| 7 | S6.4 - Dashboard UI (part 2) |
| 8 | S6.5 - Watchlist backend |
| 9 | S6.5 - Watchlist UI + S6.6 Screener backend |
| 10 | S6.6 - Screener UI + Polish |

---

## ✅ Definition of Done

- [ ] Users can register and login
- [ ] JWT authentication working
- [ ] New dashboard live
- [ ] Watchlist CRUD works
- [ ] Stock screener filtering works
- [ ] Mobile responsive

---

## 📦 Dependencies

```txt
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
```

---

**Previous Sprint:** [Sprint 5 - Charts](./SPRINT_5.md)  
**Next Sprint:** [Sprint 7 - Alerts & Reports](./SPRINT_7.md)

