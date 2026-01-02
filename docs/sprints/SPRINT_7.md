# 🏃 Sprint 7: Alerts & Reports

**Phase:** 3 - User Experience  
**Thời gian:** Tuần 13-14 (27/03/2026 - 09/04/2026)  
**Mục tiêu:** Price alerts system, PDF/Excel reports, role-based access

---

## 📊 Sprint Overview

| Metric | Target |
|--------|--------|
| Alerts | Price alert system with notifications |
| Reports | PDF và Excel export |
| Roles | Free vs Premium tier logic |

---

## 📋 Task Breakdown

### S7.1 - Database: Alerts, Analysis History Tables
**Priority:** 🔴 High | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Create alerts table migration
- [ ] Create analysis_history table migration
- [ ] SQLAlchemy models
- [ ] Test migrations

**Migration:**
```python
def upgrade():
    op.create_table('alerts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('ticker', sa.String(10), nullable=False),
        sa.Column('condition', sa.String(50)),  # price_above, price_below, rsi_overbought
        sa.Column('value', sa.Numeric()),
        sa.Column('active', sa.Boolean(), default=True),
        sa.Column('triggered_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )
    
    op.create_table('analysis_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('ticker', sa.String(10), nullable=False),
        sa.Column('type', sa.String(50)),  # dcf, graham, technical
        sa.Column('result', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )
```

---

### S7.2 - Price Alerts System
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Create alert CRUD API
- [ ] Alert conditions: price_above, price_below, rsi_overbought, etc.
- [ ] UI: Alert creation form
- [ ] Alert list với status

**API:**
```
GET /api/alerts
Response: {
    "alerts": [
        {
            "id": 1,
            "ticker": "FPT",
            "condition": "price_above",
            "value": 95000,
            "active": true,
            "triggered_at": null
        }
    ]
}

POST /api/alerts
Body: {
    "ticker": "FPT",
    "condition": "price_above",
    "value": 95000
}

DELETE /api/alerts/{id}
PUT /api/alerts/{id}/toggle
```

**Condition Types:**
| Condition | Description |
|-----------|-------------|
| price_above | Price goes above threshold |
| price_below | Price goes below threshold |
| rsi_overbought | RSI > 70 |
| rsi_oversold | RSI < 30 |
| macd_cross_up | MACD bullish crossover |
| macd_cross_down | MACD bearish crossover |

---

### S7.3 - Worker: Alert Checking Task (Celery Beat)
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Create Celery Beat schedule
- [ ] Check alerts every 5 minutes during market hours
- [ ] Mark triggered alerts
- [ ] Queue notifications

**Code:**
```python
# services/worker/tasks/alert_tasks.py
from celery import Celery
from celery.schedules import crontab

app = Celery('worker')

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run every 5 minutes during market hours (9:00-15:00 Vietnam time)
    sender.add_periodic_task(
        crontab(minute='*/5', hour='9-15'),
        check_price_alerts.s(),
    )

@app.task
def check_price_alerts():
    """Check all active alerts against current prices"""
    from services.alert_service import AlertService
    
    service = AlertService()
    triggered = service.check_all_alerts()
    
    for alert in triggered:
        send_alert_notification.delay(alert.id)
    
    return f"Checked {len(triggered)} alerts"

@app.task
def send_alert_notification(alert_id: int):
    """Send notification for triggered alert"""
    # Email, push notification, etc.
    pass
```

**Celery Beat Config:**
```python
# services/worker/celeryconfig.py
beat_schedule = {
    'check-alerts-every-5-minutes': {
        'task': 'tasks.alert_tasks.check_price_alerts',
        'schedule': 300.0,  # 5 minutes
    },
}
```

---

### S7.4 - Email Notifications (SendGrid/Mailgun)
**Priority:** 🟡 Medium | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Choose email provider (SendGrid recommended)
- [ ] Create email templates
- [ ] Send alert notification emails
- [ ] Email preferences in user settings

**Code:**
```python
# services/worker/tasks/email_tasks.py
import sendgrid
from sendgrid.helpers.mail import Mail

sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))

@app.task
def send_alert_email(user_email: str, alert_data: dict):
    message = Mail(
        from_email='alerts@stockanalysis.vn',
        to_emails=user_email,
        subject=f'🔔 Alert: {alert_data["ticker"]} - {alert_data["condition"]}',
        html_content=render_template('alert_email.html', alert=alert_data)
    )
    response = sg.send(message)
    return response.status_code
```

---

### S7.5 - PDF Report Generation (WeasyPrint)
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Install WeasyPrint
- [ ] Create HTML template for report
- [ ] Generate PDF from analysis data
- [ ] API endpoint: POST /api/reports/pdf
- [ ] Queue heavy generation to Worker

**API:**
```
POST /api/reports/generate
Body: {
    "ticker": "FPT",
    "type": "full",  # full, dcf_only, technical_only
    "format": "pdf"
}
Response: {
    "job_id": "abc123",
    "status": "processing"
}

GET /api/reports/{job_id}/status
GET /api/reports/{job_id}/download
```

**Report Sections:**
1. Company Overview
2. Price Chart
3. DCF Valuation
4. Graham Valuation
5. Technical Analysis Summary
6. Financial Highlights

---

### S7.6 - Excel Export (openpyxl)
**Priority:** 🟡 Medium | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Install openpyxl
- [ ] Export analysis data to Excel
- [ ] Multiple sheets (DCF, Technical, Financials)

**Code:**
```python
from openpyxl import Workbook

def generate_excel_report(ticker: str, analysis_data: dict) -> bytes:
    wb = Workbook()
    
    # DCF Sheet
    ws_dcf = wb.active
    ws_dcf.title = "DCF Valuation"
    ws_dcf['A1'] = 'Ticker'
    ws_dcf['B1'] = ticker
    # ... more data
    
    # Technical Sheet
    ws_ta = wb.create_sheet("Technical Analysis")
    # ... add data
    
    # Save to bytes
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
```

---

### S7.7 - Role-based Access (Free/Premium)
**Priority:** 🟡 Medium | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Define tier limits
- [ ] Middleware to check limits
- [ ] UI feedback for limit reached
- [ ] Upgrade prompts

**Tier Limits:**
| Feature | Free | Basic | Pro |
|---------|------|-------|-----|
| Watchlist stocks | 3 | 20 | ∞ |
| DCF analyses/day | 1 | 10 | ∞ |
| Alerts | ❌ | 5 | ∞ |
| PDF Reports | ❌ | ❌ | ✅ |
| Excel Export | ❌ | ✅ | ✅ |

**Code:**
```python
# services/api/middleware/tier_limit.py
from functools import wraps

TIER_LIMITS = {
    'free': {'watchlist': 3, 'dcf_daily': 1, 'alerts': 0},
    'basic': {'watchlist': 20, 'dcf_daily': 10, 'alerts': 5},
    'pro': {'watchlist': -1, 'dcf_daily': -1, 'alerts': -1},  # -1 = unlimited
}

def check_tier_limit(feature: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            user = request.state.user
            limit = TIER_LIMITS[user.tier][feature]
            
            if limit != -1:
                current_usage = get_usage(user.id, feature)
                if current_usage >= limit:
                    raise HTTPException(403, f"Limit reached. Upgrade to increase limit.")
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
```

---

## 📅 Daily Plan

### Week 1 (27/03 - 02/04)
| Day | Tasks |
|-----|-------|
| 1 | S7.1 - Database migrations |
| 2 | S7.2 - Alert CRUD (part 1) |
| 3 | S7.2 - Alert CRUD (part 2) |
| 4 | S7.3 - Celery Beat setup |
| 5 | S7.3 - Alert checking task |

### Week 2 (03/04 - 09/04)
| Day | Tasks |
|-----|-------|
| 6 | S7.4 - Email notifications |
| 7 | S7.5 - PDF template |
| 8 | S7.5 - PDF generation + S7.6 Excel |
| 9 | S7.7 - Tier limits backend |
| 10 | S7.7 - Tier limits UI + Polish |

---

## ✅ Definition of Done

- [ ] Alerts CRUD working
- [ ] Celery Beat checking alerts every 5 min
- [ ] Email notifications sent
- [ ] PDF reports generated
- [ ] Excel export working
- [ ] Tier limits enforced

---

## 📦 Dependencies

```txt
weasyprint>=60.0
openpyxl>=3.1.0
sendgrid>=6.10.0
celery[redis]>=5.3.0
```

---

**Previous Sprint:** [Sprint 6 - Dashboard](./SPRINT_6.md)  
**Next Sprint:** [Sprint 8 - Payment](./SPRINT_8.md)

