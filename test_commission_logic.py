#!/usr/bin/env python3

"""
A simplified script to test the logic of the one-year commission window 
without creating database records.
"""

from datetime import datetime, timedelta

def is_within_commission_window(first_commissioned_purchase_at, transaction_date):
    """
    Pure logic implementation of the commission window check.
    
    Args:
        first_commissioned_purchase_at: The date of the first commissioned purchase
        transaction_date: The date of the transaction to check
        
    Returns:
        bool: True if within window, False otherwise
    """
    if not first_commissioned_purchase_at:
        # No first purchase yet, so any transaction is eligible
        return True
        
    # Calculate the end of the eligibility window (one year after first purchase)
    eligibility_end_date = first_commissioned_purchase_at + timedelta(days=365)
    
    # Check if transaction_date is before or equal to eligibility_end_date
    return transaction_date <= eligibility_end_date

def run_test():
    """Run tests on the commission window logic"""
    # Set up test dates
    now = datetime.utcnow()
    one_year_ago = now - timedelta(days=365)
    one_year_ago_minus_one_day = now - timedelta(days=364)
    one_year_ago_plus_one_day = now - timedelta(days=366)
    
    # Test case 1: No first purchase date (always eligible)
    result1 = is_within_commission_window(None, now)
    print(f"Test 1 - No first purchase date: {result1}")
    assert result1 == True, "Error: Should be eligible when no first purchase date"
    
    # Test case 2: Transaction on the same day as first purchase
    result2 = is_within_commission_window(one_year_ago_minus_one_day, one_year_ago_minus_one_day)
    print(f"Test 2 - Transaction on same day as first purchase: {result2}")
    assert result2 == True, "Error: Should be eligible on same day as first purchase"
    
    # Test case 3: Transaction within the 1-year window (today, first purchase was 364 days ago)
    result3 = is_within_commission_window(one_year_ago_minus_one_day, now)
    print(f"Test 3 - Transaction within 1-year window: {result3}")
    assert result3 == True, "Error: Should be eligible within 1-year window"
    
    # Test case 4: Transaction exactly on the 1-year boundary
    result4 = is_within_commission_window(one_year_ago, now)
    print(f"Test 4 - Transaction exactly on 1-year boundary: {result4}")
    assert result4 == True, "Error: Should be eligible exactly on 1-year boundary"
    
    # Test case 5: Transaction just outside the 1-year window (366 days after first purchase)
    future_date = one_year_ago_plus_one_day + timedelta(days=366)
    result5 = is_within_commission_window(one_year_ago_plus_one_day, future_date)
    print(f"Test 5 - Transaction outside 1-year window: {result5}")
    assert result5 == False, "Error: Should not be eligible outside 1-year window"
    
    print("\nAll logic tests passed successfully! The commission window calculation works as expected.")
    return True

if __name__ == "__main__":
    print("=== Testing One-Year Commission Window Logic ===\n")
    run_test()