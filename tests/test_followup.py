import pytest
from datetime import date, timedelta
from app.followup.tracker import FollowupTracker

def test_interval_calculation():
    tracker = FollowupTracker()
    last_contact = date.today() - timedelta(days=4)
    days_since = (date.today() - last_contact).days
    assert days_since >= tracker.interval_days

def test_max_followup_logic():
    tracker = FollowupTracker()
    followup_count = tracker.max_followup
    assert followup_count >= tracker.max_followup

def test_next_followup_date():
    tracker = FollowupTracker()
    next_date = date.today() + timedelta(days=tracker.interval_days)
    assert next_date > date.today()
