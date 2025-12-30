"""
Unit tests for shares outstanding validator
"""
import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.shares_validator import (
    validate_shares,
    cross_validate_shares_with_market_cap,
    validate_and_cross_check
)


class TestSharesValidator(unittest.TestCase):
    """Test shares outstanding validation"""
    
    def test_validate_shares_valid(self):
        """Test validation with valid shares"""
        # Valid shares for Vietnamese stocks
        self.assertTrue(validate_shares(5136656600, "ACB", raise_error=False))
        self.assertTrue(validate_shares(1703507121, "FPT", raise_error=False))
        self.assertTrue(validate_shares(1000000000, "TEST", raise_error=False))  # 1 billion
    
    def test_validate_shares_none(self):
        """Test validation with None shares"""
        with self.assertRaises(ValueError):
            validate_shares(None, "TEST")
    
    def test_validate_shares_negative(self):
        """Test validation with negative shares"""
        with self.assertRaises(ValueError):
            validate_shares(-1000, "TEST")
    
    def test_validate_shares_zero(self):
        """Test validation with zero shares"""
        with self.assertRaises(ValueError):
            validate_shares(0, "TEST")
    
    def test_validate_shares_too_large(self):
        """Test validation with suspiciously large shares (>1 trillion)"""
        # This should raise error (unit error)
        with self.assertRaises(ValueError):
            validate_shares(5136656600000000, "ACB")  # Old wrong value
    
    def test_validate_shares_large_but_valid(self):
        """Test validation with large but potentially valid shares"""
        # 50 billion shares - should warn but not error
        result = validate_shares(5e10, "TEST", raise_error=False)
        self.assertTrue(result)
    
    def test_cross_validate_shares_valid(self):
        """Test cross-validation with valid data"""
        shares = 5136656600  # ACB
        price = 24000.0
        market_cap = shares * price  # Exact match
        
        is_valid, error = cross_validate_shares_with_market_cap(
            shares, price, market_cap, "ACB"
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_cross_validate_shares_within_tolerance(self):
        """Test cross-validation within tolerance"""
        shares = 5136656600
        price = 24000.0
        market_cap = shares * price * 1.1  # 10% difference (within 15% tolerance)
        
        is_valid, error = cross_validate_shares_with_market_cap(
            shares, price, market_cap, "ACB", tolerance=0.15
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_cross_validate_shares_outside_tolerance(self):
        """Test cross-validation outside tolerance"""
        shares = 5136656600
        price = 24000.0
        market_cap = shares * price * 0.5  # 50% difference (outside tolerance)
        
        is_valid, error = cross_validate_shares_with_market_cap(
            shares, price, market_cap, "ACB", tolerance=0.15
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("cross-validation failed", error.lower())
    
    def test_validate_and_cross_check_valid(self):
        """Test comprehensive validation with valid data"""
        shares = 5136656600
        price = 24000.0
        market_cap = shares * price
        
        result = validate_and_cross_check(
            shares, "ACB", price, market_cap, raise_error=False
        )
        self.assertTrue(result)
    
    def test_validate_and_cross_check_invalid_shares(self):
        """Test comprehensive validation with invalid shares"""
        shares = 5136656600000000  # Too large
        price = 24000.0
        market_cap = 123279758376000
        
        result = validate_and_cross_check(
            shares, "ACB", price, market_cap, raise_error=False
        )
        self.assertFalse(result)
    
    def test_validate_and_cross_check_no_price_market_cap(self):
        """Test validation without price/market cap (should still validate shares)"""
        shares = 5136656600
        
        result = validate_and_cross_check(
            shares, "ACB", price=None, market_cap=None, raise_error=False
        )
        self.assertTrue(result)


class TestSharesCalculationLogic(unittest.TestCase):
    """Test shares calculation logic from capital values"""
    
    def test_calculate_shares_from_common_shares(self):
        """Test calculation from Common shares (Bn. VND)"""
        # FPT example
        capital = 17035071210000  # VND
        par_value = 10000
        expected_shares = 1703507121
        
        shares = capital / par_value
        self.assertEqual(shares, expected_shares)
        
        # Validate
        self.assertTrue(validate_shares(shares, "FPT", raise_error=False))
    
    def test_calculate_shares_from_paid_in_capital(self):
        """Test calculation from Paid-in capital (Bn. VND)"""
        # ACB example
        capital = 51366566000000  # VND (NOT billions!)
        par_value = 10000
        expected_shares = 5136656600
        
        # Correct calculation
        shares_correct = capital / par_value
        self.assertEqual(shares_correct, expected_shares)
        
        # Wrong calculation (old bug)
        shares_wrong = capital * 1000000 / par_value
        self.assertNotEqual(shares_wrong, expected_shares)
        self.assertGreater(shares_wrong, 1e12)  # Too large
        
        # Validate correct shares
        self.assertTrue(validate_shares(shares_correct, "ACB", raise_error=False))
        
        # Validate wrong shares should fail
        with self.assertRaises(ValueError):
            validate_shares(shares_wrong, "ACB")
    
    def test_par_value_conversion(self):
        """Test par value conversion logic"""
        # Standard Vietnamese par value
        par_value = 10000  # 10,000 VND per share
        
        test_cases = [
            (51366566000000, 5136656600),  # ACB
            (17035071210000, 1703507121),  # FPT
            (83556751000000, 8355675100),  # VCB
        ]
        
        for capital_vnd, expected_shares in test_cases:
            shares = capital_vnd / par_value
            self.assertEqual(shares, expected_shares)
            self.assertTrue(validate_shares(shares, "TEST", raise_error=False))


if __name__ == '__main__':
    unittest.main()

