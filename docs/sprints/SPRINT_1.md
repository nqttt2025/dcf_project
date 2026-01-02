# 🏃 Sprint 1: DCF Stability

**Phase:** 1 - Core Stability  
**Thời gian:** Tuần 1-2 (02/01/2026 - 15/01/2026)  
**Mục tiêu:** Fix DCF tool, tăng success rate từ 70% → 95%

---

## 📊 Sprint Overview

| Metric | Target |
|--------|--------|
| DCF Success Rate | ≥ 95% |
| API Response Time | < 30s |
| Test Coverage | ≥ 80% |
| Days | 10 working days |

---

## 📋 Task Breakdown

### S1.1 - Fix DCF Timeout & Retry Mechanism
**Priority:** 🔴 High | **Estimate:** 3 days | **Status:** ⬜ Pending

**Mô tả:**
Hiện tại DCF timeout khi fetch data từ vnstock, cần implement retry mechanism.

**Tasks:**
- [ ] Install `tenacity` library
- [ ] Create `src/utils/retry.py` module
- [ ] Wrap vnstock API calls với retry decorator
- [ ] Configure: 3 retries, exponential backoff (2, 4, 8 seconds)
- [ ] Add timeout parameter (max 30s per request)
- [ ] Log retry attempts

**Files cần tạo/sửa:**
```
src/utils/retry.py          # NEW - Retry utilities
src/core/fcfs.py            # Apply retry to vnstock calls
src/core/dcf_calculator.py  # Use new retry mechanism
tests/unit/core/test_retry_mechanism.py  # NEW - Unit tests
tests/integration/test_dcf_retry.py      # NEW - Integration tests
```

**Code Example:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
async def fetch_financial_data(ticker: str):
    """Fetch data with retry mechanism"""
    pass
```

---

#### ✅ DoD (Definition of Done) - S1.1

**Implementation:**
- [ ] `src/utils/retry.py` created with retry decorators
- [ ] Retry applied to all vnstock API calls in `fcfs.py`
- [ ] Retry attempts logged with timing
- [ ] No linting errors

**Unit Tests:** (`tests/unit/core/test_retry_mechanism.py`)
- [ ] `test_retry_succeeds_first_attempt` - No retry needed
- [ ] `test_retry_succeeds_after_timeout` - Success on 2nd/3rd attempt
- [ ] `test_retry_exhausted_raises_error` - Fails after max retries
- [ ] `test_retry_logs_attempts` - Verify logging
- [ ] `test_exponential_backoff_timing` - Verify wait times
- [ ] Coverage ≥ 90% for `retry.py`

**Integration Tests:** (`tests/integration/test_dcf_retry.py`)
- [ ] `test_dcf_completes_with_slow_api` - Mock slow vnstock
- [ ] `test_dcf_retries_on_timeout` - Verify retry behavior

**Verification:**
- [ ] Run: `pytest tests/unit/core/test_retry_mechanism.py -v`
- [ ] Run: `pytest tests/integration/test_dcf_retry.py -v`
- [ ] Manual test với real API
- [ ] CI pipeline passes

**Acceptance Criteria:**
- [ ] DCF không fail do timeout
- [ ] Retry logs được ghi lại
- [ ] Max response time < 45s (kể cả retries)

---

### S1.2 - Implement Redis Caching với TTL
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Mô tả:**
Cache financial data và DCF results trong Redis để giảm API calls và tăng performance.

**Tasks:**
- [ ] Define cache key patterns
- [ ] Set TTL theo loại data
- [ ] Implement cache-aside pattern
- [ ] Add cache invalidation

**Files cần tạo/sửa:**
```
src/utils/cache_utils.py                  # NEW - Enhanced cache utilities
src/core/dcf_calculator.py               # Apply caching
tests/unit/utils/test_cache_utils.py     # NEW - Unit tests
tests/integration/test_redis_cache.py    # NEW - Integration tests
```

**Cache Strategy:**
| Key Pattern | TTL | Description |
|------------|-----|-------------|
| `dcf:{ticker}:result` | 1 hour | DCF calculation result |
| `financial:{ticker}:data` | 24 hours | Financial statements |
| `shares:{ticker}` | 24 hours | Shares outstanding |
| `price:{ticker}` | 5 minutes | Current price |

---

#### ✅ DoD (Definition of Done) - S1.2

**Implementation:**
- [ ] `src/utils/cache_utils.py` created
- [ ] Cache-aside pattern implemented
- [ ] TTL correctly set for each data type

**Unit Tests:** (`tests/unit/utils/test_cache_utils.py`)
- [ ] `test_cache_set_and_get` - Basic operations
- [ ] `test_cache_ttl_expiry` - TTL works correctly
- [ ] `test_cache_key_patterns` - Keys formatted correctly
- [ ] `test_cache_miss_returns_none` - Handle missing keys
- [ ] Coverage ≥ 90% for `cache_utils.py`

**Integration Tests:** (`tests/integration/test_redis_cache.py`)
- [ ] `test_dcf_uses_cache` - Cache hit scenario
- [ ] `test_cache_invalidation` - Clear cache works

**Verification:**
- [ ] Run: `pytest tests/unit/utils/test_cache_utils.py -v`
- [ ] Run: `pytest tests/integration/test_redis_cache.py -v`
- [ ] Cache hit rate > 50% (measured with metrics)

**Acceptance Criteria:**
- [ ] Cache hit rate > 50% cho repeated requests
- [ ] TTL được set đúng
- [ ] Cache invalidation hoạt động

---

### S1.3 - Cross-validation Shares Outstanding
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Mô tả:**
Số shares outstanding có thể không chính xác, cần cross-validate từ nhiều nguồn.

**Tasks:**
- [ ] Fetch shares từ multiple sources
- [ ] Compare và chọn giá trị reasonable (median)
- [ ] Log discrepancies (>10% deviation)
- [ ] Fallback mechanism

**Files cần tạo/sửa:**
```
src/utils/shares_validator.py            # Enhance existing
src/core/fcfs.py                         # Apply validation
tests/unit/utils/test_shares_validator.py  # NEW - Unit tests
```

---

#### ✅ DoD (Definition of Done) - S1.3

**Implementation:**
- [ ] `validate_shares_from_sources()` function created
- [ ] Median calculation implemented
- [ ] Discrepancy logging added

**Unit Tests:** (`tests/unit/utils/test_shares_validator.py`)
- [ ] `test_validate_with_matching_sources` - All sources agree
- [ ] `test_validate_with_discrepancy` - Sources differ >10%
- [ ] `test_validate_single_source` - Only 1 source available
- [ ] `test_validate_no_sources` - Handle empty input
- [ ] `test_median_calculation` - Correct median
- [ ] Coverage ≥ 90%

**Verification:**
- [ ] Run: `pytest tests/unit/utils/test_shares_validator.py -v`
- [ ] Test with known tickers (FPT, VNM, etc.)

**Acceptance Criteria:**
- [ ] Shares được validate từ ≥2 sources
- [ ] Discrepancies được logged
- [ ] Fallback khi chỉ có 1 source

---

### S1.4 - Error Recovery & Graceful Degradation
**Priority:** 🟡 Medium | **Estimate:** 2 days | **Status:** ⬜ Pending

**Mô tả:**
Khi một phần DCF calculation fail, hệ thống nên trả về partial results thay vì fail hoàn toàn.

**Tasks:**
- [ ] Create PartialResult response model
- [ ] Return available data + error messages
- [ ] Implement fallback values
- [ ] Graceful error handling

**Files cần tạo/sửa:**
```
src/core/dcf_calculator.py              # Add partial result logic
src/schemas/analysis.py                 # NEW - Response schemas
tests/unit/core/test_error_recovery.py  # NEW - Unit tests
tests/integration/test_partial_result.py # NEW - Integration tests
```

---

#### ✅ DoD (Definition of Done) - S1.4

**Implementation:**
- [ ] `PartialAnalysisResult` schema created
- [ ] Error collection in calculator
- [ ] Fallback values defined

**Unit Tests:** (`tests/unit/core/test_error_recovery.py`)
- [ ] `test_partial_result_missing_fcf` - DCF null, Graham available
- [ ] `test_partial_result_missing_growth` - Use industry average
- [ ] `test_partial_result_all_available` - Full result
- [ ] `test_error_messages_collected` - Errors in response
- [ ] `test_warnings_collected` - Warnings in response
- [ ] Coverage ≥ 85%

**Integration Tests:** (`tests/integration/test_partial_result.py`)
- [ ] `test_api_returns_partial_on_error` - API returns 200 with partial
- [ ] `test_api_returns_errors_list` - Errors included in response

**Verification:**
- [ ] Run: `pytest tests/unit/core/test_error_recovery.py -v`
- [ ] Run: `pytest tests/integration/test_partial_result.py -v`

**Acceptance Criteria:**
- [ ] Partial results được trả về khi có thể
- [ ] Errors và warnings rõ ràng
- [ ] API không crash khi thiếu data

---

### S1.5 - Unit Tests (Target 80% Coverage)
**Priority:** 🟡 Medium | **Estimate:** 2 days | **Status:** ⬜ Pending

**Mô tả:**
Consolidate và viết thêm unit tests cho DCF calculator và related functions.

**Tasks:**
- [ ] Setup pytest với proper fixtures
- [ ] Create mock data fixtures
- [ ] Write/update unit tests cho tất cả S1.1-S1.4 tasks
- [ ] Achieve 80% coverage

**Files cần tạo/sửa:**
```
tests/
├── conftest.py                    # Shared fixtures
├── fixtures/
│   ├── __init__.py
│   ├── mock_vnstock.py           # Mock vnstock responses
│   └── sample_data.py            # Sample financial data
├── unit/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── test_dcf_calculator.py
│   │   ├── test_retry_mechanism.py
│   │   └── test_error_recovery.py
│   └── utils/
│       ├── __init__.py
│       ├── test_cache_utils.py
│       └── test_shares_validator.py
```

---

#### ✅ DoD (Definition of Done) - S1.5

**Implementation:**
- [ ] `tests/conftest.py` with shared fixtures
- [ ] Mock data for vnstock API
- [ ] All unit tests from S1.1-S1.4 implemented

**Test Coverage Targets:**
| Module | Target | Actual |
|--------|--------|--------|
| `src/utils/retry.py` | 90% | TBD |
| `src/utils/cache_utils.py` | 90% | TBD |
| `src/utils/shares_validator.py` | 90% | TBD |
| `src/core/dcf_calculator.py` | 80% | TBD |
| **Overall** | **80%** | TBD |

**Verification:**
```bash
# Run all unit tests with coverage
pytest tests/unit/ --cov=src --cov-report=term-missing

# Check coverage meets threshold
pytest tests/unit/ --cov=src --cov-fail-under=80
```

**Acceptance Criteria:**
- [ ] Test coverage ≥ 80%
- [ ] All tests pass
- [ ] Mock external APIs (no real API calls)

---

### S1.6 - Integration Tests
**Priority:** 🟡 Medium | **Estimate:** 1 day | **Status:** ⬜ Pending

**Mô tả:**
Test end-to-end flow của DCF API với real services.

**Tasks:**
- [ ] Setup docker-compose.test.yml
- [ ] Test API endpoints
- [ ] Test Redis integration
- [ ] Test database operations

**Files cần tạo:**
```
tests/
├── integration/
│   ├── __init__.py
│   ├── conftest.py            # Integration test fixtures
│   ├── test_dcf_api.py        # API endpoint tests
│   ├── test_dcf_retry.py      # Retry with real timeout
│   ├── test_redis_cache.py    # Redis integration
│   └── test_partial_result.py # Error handling
├── docker-compose.test.yml    # Test environment
```

---

#### ✅ DoD (Definition of Done) - S1.6

**Implementation:**
- [ ] `docker-compose.test.yml` created
- [ ] Integration test fixtures setup
- [ ] All integration tests pass

**Integration Tests:**
| Test File | Test Cases |
|-----------|------------|
| `test_dcf_api.py` | POST /stocks/{ticker}/run returns 200 |
| `test_dcf_api.py` | Response contains dcf_fair_value |
| `test_dcf_retry.py` | API recovers from timeout |
| `test_redis_cache.py` | Cache hit works correctly |
| `test_partial_result.py` | Partial result returned on error |

**Verification:**
```bash
# Start test environment
docker-compose -f tests/docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/ -v

# Cleanup
docker-compose -f tests/docker-compose.test.yml down
```

**Acceptance Criteria:**
- [ ] All integration tests pass
- [ ] Docker test environment works
- [ ] CI/CD pipeline can run these tests

---

## 📁 Files Summary

### Files cần sửa:
| File | Changes |
|------|---------|
| `src/core/dcf_calculator.py` | Retry, cache, validation |
| `services/dcf/main.py` | Error handling |
| `requirements.txt` | Add tenacity, pytest packages |

### Files cần tạo:
| File | Purpose |
|------|---------|
| `src/utils/cache.py` | Redis caching utilities |
| `src/utils/validators.py` | Data validators |
| `tests/test_dcf_calculator.py` | Unit tests |
| `tests/test_graham_valuation.py` | Unit tests |
| `tests/conftest.py` | Pytest fixtures |
| `tests/integration/test_dcf_api.py` | Integration tests |

---

## 📦 Dependencies cần thêm

```txt
# requirements.txt (additions)
tenacity>=8.2.0          # Retry mechanism
pytest>=7.4.0            # Testing
pytest-asyncio>=0.21.0   # Async test support
pytest-cov>=4.1.0        # Coverage
httpx>=0.24.0            # Test client
```

---

## 📅 Daily Plan

### Week 1 (02/01 - 08/01)
| Day | Date | Tasks | Owner |
|-----|------|-------|-------|
| 1 | 02/01 | S1.1 - Setup tenacity, basic retry | Dev |
| 2 | 03/01 | S1.1 - Integrate retry into dcf_calculator | Dev |
| 3 | 06/01 | S1.1 - Testing & refinement | Dev |
| 4 | 07/01 | S1.2 - Cache implementation | Dev |
| 5 | 08/01 | S1.2 - Cache testing | Dev |

### Week 2 (09/01 - 15/01)
| Day | Date | Tasks | Owner |
|-----|------|-------|-------|
| 6 | 09/01 | S1.3 - Shares validation logic | Dev |
| 7 | 10/01 | S1.3 - Integration & testing | Dev |
| 8 | 13/01 | S1.4 - Error recovery | Dev |
| 9 | 14/01 | S1.5 - Unit tests | Dev |
| 10 | 15/01 | S1.6 - Integration tests, Sprint review | Dev |

---

## ✅ Definition of Done

- [ ] All 6 tasks completed
- [ ] DCF success rate ≥ 95% (tested with 20+ tickers)
- [ ] API response time < 30s average
- [ ] Test coverage ≥ 80%
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] No critical bugs

---

## 🎯 Sprint Success Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| DCF Success Rate | ~70% | TBD | ≥ 95% |
| Avg Response Time | ~45s | TBD | < 30s |
| Test Coverage | 0% | TBD | ≥ 80% |
| Cache Hit Rate | 0% | TBD | > 50% |

---

## 📝 Notes

- **Risk:** vnstock API có thể thay đổi → cần monitor
- **Dependency:** Redis phải running cho cache tests
- **Blocker potential:** Nếu vnstock down, integration tests fail

---

**Next Sprint:** [Sprint 2 - Infrastructure](./SPRINT_2.md)

