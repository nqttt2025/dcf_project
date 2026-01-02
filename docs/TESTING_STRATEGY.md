# 🧪 Testing Strategy

**Version:** 1.0  
**Created:** 02/01/2026  
**Applies to:** All Sprints in Roadmap

---

## 📊 Testing Levels

```
┌─────────────────────────────────────────────────────────────┐
│                     TESTING PYRAMID                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                        ┌─────────┐                          │
│                        │  E2E    │  ← 10% (Critical paths)  │
│                       /│  Tests  │\                         │
│                      / └─────────┘ \                        │
│                     /               \                       │
│                    /  ┌───────────┐  \                      │
│                   /   │Integration│   \ ← 30% (APIs, DB)    │
│                  /    │   Tests   │    \                    │
│                 /     └───────────┘     \                   │
│                /                         \                  │
│               /     ┌─────────────┐       \                 │
│              /      │ Unit Tests  │        \ ← 60% (Core)   │
│             /       └─────────────┘         \               │
│            ─────────────────────────────────────            │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Test Directory Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Test dependencies
│
├── unit/                       # Unit Tests (60%)
│   ├── __init__.py
│   ├── core/
│   │   ├── test_dcf_calculator.py
│   │   ├── test_retry_mechanism.py
│   │   ├── test_cache_utils.py
│   │   └── test_validators.py
│   ├── services/
│   │   ├── test_ta_service.py
│   │   └── test_user_service.py
│   └── utils/
│       ├── test_cache_manager.py
│       └── test_redis_client.py
│
├── integration/                # Integration Tests (30%)
│   ├── __init__.py
│   ├── test_dcf_api.py
│   ├── test_ta_api.py
│   ├── test_database.py
│   └── test_redis_cache.py
│
├── e2e/                        # End-to-End Tests (10%)
│   ├── __init__.py
│   ├── test_dcf_full_flow.py
│   └── test_user_journey.py
│
├── fixtures/                   # Test data
│   ├── mock_financial_data.json
│   ├── mock_vnstock_responses.py
│   └── sample_configs/
│       └── FPT_test.cfg
│
└── performance/                # Performance tests
    ├── locustfile.py
    └── benchmark_dcf.py
```

---

## 🎯 Test Types & When to Use

### 1. Unit Tests (60% coverage target)
**Purpose:** Test individual functions/methods in isolation

| When | Example |
|------|---------|
| New function added | `test_calculate_dcf()` |
| Logic changed | `test_retry_with_backoff()` |
| Edge cases | `test_dcf_negative_fcf()` |

**Characteristics:**
- Fast (< 1s per test)
- No external dependencies (mock everything)
- High coverage

```python
# Example: tests/unit/core/test_retry_mechanism.py
def test_retry_succeeds_on_third_attempt(mock_vnstock):
    """Test retry mechanism succeeds after initial failures"""
    mock_vnstock.side_effect = [TimeoutError, TimeoutError, {"fcf": 1000000}]
    result = fetch_with_retry("FPT")
    assert result["fcf"] == 1000000
    assert mock_vnstock.call_count == 3
```

---

### 2. Integration Tests (30% coverage target)
**Purpose:** Test component interactions

| When | Example |
|------|---------|
| API endpoint | `test_dcf_endpoint_returns_200()` |
| Database operations | `test_save_analysis_to_db()` |
| Cache interactions | `test_redis_cache_hit()` |

**Characteristics:**
- Medium speed (< 5s per test)
- Uses real database (test container)
- Uses real Redis (test container)
- Mocks external APIs (vnstock)

```python
# Example: tests/integration/test_dcf_api.py
@pytest.mark.integration
async def test_dcf_endpoint(test_client, mock_vnstock_api):
    response = await test_client.post("/api/stocks/FPT/run")
    assert response.status_code == 200
    data = response.json()
    assert "dcf_fair_value" in data
```

---

### 3. End-to-End Tests (10% - Critical paths only)
**Purpose:** Test complete user journeys

| When | Example |
|------|---------|
| Critical user flow | Full DCF analysis flow |
| Payment flow | Subscription purchase |
| Auth flow | Login → Access protected resource |

**Characteristics:**
- Slow (> 10s per test)
- Full stack (real services)
- Run in CI/CD before deploy

```python
# Example: tests/e2e/test_dcf_full_flow.py
@pytest.mark.e2e
async def test_complete_dcf_analysis():
    # 1. Create config
    # 2. Run analysis
    # 3. Check result saved
    # 4. Verify cache updated
    pass
```

---

## ✅ Definition of Done (DoD) Template

Mỗi task trong Sprint PHẢI có DoD bao gồm:

### Task DoD Checklist
```markdown
### DoD for Task S1.X

**Implementation:**
- [ ] Code written and reviewed
- [ ] Documentation updated
- [ ] No linting errors

**Testing:**
- [ ] Unit tests written (coverage ≥ 80% for new code)
- [ ] Unit tests pass locally
- [ ] Integration test written (if API/DB involved)
- [ ] Integration tests pass
- [ ] Edge cases tested

**Verification:**
- [ ] Manual testing completed
- [ ] Reviewed by peer
- [ ] CI pipeline passes
```

---

## 📋 Sprint Testing Requirements

### Sprint 1: DCF Stability
| Task | Unit Tests | Integration Tests | E2E |
|------|------------|------------------|-----|
| S1.1 Retry | ✅ Required | ✅ Required | ❌ |
| S1.2 Cache | ✅ Required | ✅ Required | ❌ |
| S1.3 Validation | ✅ Required | ❌ | ❌ |
| S1.4 Error Recovery | ✅ Required | ✅ Required | ❌ |
| S1.5 Unit Tests | N/A | N/A | N/A |
| S1.6 Integration | N/A | ✅ Required | ❌ |

### Sprint 2-9: Similar pattern

---

## 🔧 Test Commands

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/core/test_retry_mechanism.py -v

# Run integration tests (requires Docker)
docker-compose -f docker-compose.test.yml up -d
pytest tests/integration/ -v

# Run E2E tests
pytest tests/e2e/ -v --slow

# Run all tests with markers
pytest -m "not slow" -v

# Generate coverage report
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

---

## 📦 Test Dependencies

```txt
# tests/requirements.txt
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pytest-timeout>=2.2.0
httpx>=0.24.0
fakeredis>=2.20.0
factory-boy>=3.3.0
respx>=0.20.0  # Mock httpx requests
```

---

## 🔄 CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r tests/requirements.txt
      - run: pytest tests/unit/ --cov=src --cov-fail-under=80

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/integration/ -v
```

---

## 📊 Coverage Targets

| Sprint | Unit Coverage | Integration | E2E |
|--------|--------------|-------------|-----|
| Sprint 1-2 | 80% | Key APIs | ❌ |
| Sprint 3-5 | 80% | All TA APIs | ❌ |
| Sprint 6-7 | 80% | Auth, Alerts | Basic flow |
| Sprint 8-9 | 80% | Payment | Critical paths |

---

## 🎯 Quality Gates

Before merge to main:
1. ✅ All unit tests pass
2. ✅ Coverage ≥ 80% for new code
3. ✅ No new linting errors
4. ✅ Integration tests pass (for API changes)
5. ✅ E2E tests pass (for release candidates)

---

**Last Updated:** 02/01/2026

