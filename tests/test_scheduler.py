from datetime import datetime, timedelta, timezone
from scheduler.daily import get_next_run_time, IST

def test_get_next_run_time_before_target():
    # 8:00 AM IST on June 22
    now_ist = datetime(2026, 6, 22, 8, 0, 0, tzinfo=IST)
    next_run = get_next_run_time(now_ist, target_hour=9, target_minute=15)
    
    # Expected: 9:15 AM IST on June 22
    expected = datetime(2026, 6, 22, 9, 15, 0, tzinfo=IST)
    assert next_run == expected

def test_get_next_run_time_after_target():
    # 10:00 AM IST on June 22
    now_ist = datetime(2026, 6, 22, 10, 0, 0, tzinfo=IST)
    next_run = get_next_run_time(now_ist, target_hour=9, target_minute=15)
    
    # Expected: 9:15 AM IST on June 23
    expected = datetime(2026, 6, 23, 9, 15, 0, tzinfo=IST)
    assert next_run == expected

def test_get_next_run_time_exactly_target():
    # Exactly 9:15 AM IST on June 22
    now_ist = datetime(2026, 6, 22, 9, 15, 0, tzinfo=IST)
    next_run = get_next_run_time(now_ist, target_hour=9, target_minute=15)
    
    # Expected: 9:15 AM IST on June 23 (tomorrow)
    expected = datetime(2026, 6, 23, 9, 15, 0, tzinfo=IST)
    assert next_run == expected
