from __future__ import annotations

import numpy as np
import pandas as pd

from src.app_insights import clean_play_store, _parse_installs, _parse_price, _parse_size
from src.hotel_harmony import clean_hotels
from src.heart_health import clean_heart


def test_play_store_parsers():
    assert _parse_installs("10,000+") == 10000
    assert _parse_price("$4.99") == 4.99
    assert _parse_price("0") == 0
    assert abs(_parse_size("19M") - 19) < 1e-9
    assert np.isnan(_parse_size("Varies with device"))


def test_play_store_cleaning_drops_bad_category_and_duplicates():
    raw = pd.DataFrame(
        {
            "App": ["A", "A", "B"],
            "Category": ["GAME", "GAME", "1.9"],
            "Rating": [4.5, 4.5, 19],
            "Reviews": ["10", "10", "3.0M"],
            "Size": ["19M", "19M", "Varies with device"],
            "Installs": ["10,000+", "10,000+", "Free"],
            "Type": ["Free", "Free", "0"],
            "Price": ["0", "0", "Everyone"],
            "Content Rating": ["Everyone", "Everyone", np.nan],
            "Genres": ["Action", "Action", np.nan],
            "Last Updated": ["January 1, 2018", "January 1, 2018", "1.0.19"],
            "Current Ver": ["1", "1", "4.0"],
            "Android Ver": ["4.0", "4.0", np.nan],
        }
    )
    clean = clean_play_store(raw)
    assert len(clean) == 1
    assert clean.loc[0, "Installs_num"] == 10000
    assert clean["Rating"].between(0, 5).all()


def test_hotel_cleaning_flags_and_nights():
    raw = pd.DataFrame(
        {
            "hotel": ["City Hotel", "Resort Hotel"],
            "is_canceled": [0, 1],
            "lead_time": [10, 200],
            "arrival_date_year": [2017, 2017],
            "arrival_date_month": ["July", "July"],
            "arrival_date_week_number": [27, 27],
            "arrival_date_day_of_month": [1, 2],
            "stays_in_weekend_nights": [1, 2],
            "stays_in_week_nights": [2, 3],
            "adults": [2, 0],
            "children": [np.nan, 0],
            "babies": [0, 0],
            "meal": ["BB", "BB"],
            "country": [np.nan, "PRT"],
            "market_segment": ["Direct", "Online TA"],
            "distribution_channel": ["Direct", "TA/TO"],
            "is_repeated_guest": [0, 0],
            "previous_cancellations": [0, 1],
            "previous_bookings_not_canceled": [0, 0],
            "reserved_room_type": ["A", "A"],
            "assigned_room_type": ["A", "A"],
            "booking_changes": [0, 0],
            "deposit_type": ["No Deposit", "No Deposit"],
            "agent": [np.nan, 1],
            "company": [np.nan, np.nan],
            "days_in_waiting_list": [0, 0],
            "customer_type": ["Transient", "Transient"],
            "adr": [100.0, 80.0],
            "required_car_parking_spaces": [0, 1],
            "total_of_special_requests": [1, 0],
            "reservation_status": ["Check-Out", "Canceled"],
            "reservation_status_date": ["2017-07-03", "2017-07-01"],
        }
    )
    clean = clean_hotels(raw)
    assert len(clean) == 1  # zero-guest row dropped
    assert clean.loc[0, "total_nights"] == 3
    assert clean.loc[0, "country"] == "Unknown"
    assert clean.loc[0, "children"] == 0


def test_heart_target_binarized_and_duplicates_removed():
    raw = pd.DataFrame(
        {
            "age": [63, 63, 41],
            "sex": [1, 1, 0],
            "cp": [3, 3, 1],
            "trestbps": [145, 145, 130],
            "chol": [233, 233, 250],
            "fbs": [1, 1, 0],
            "restecg": [0, 0, 1],
            "thalach": [150, 150, 168],
            "exang": [0, 0, 0],
            "oldpeak": [2.3, 2.3, 0.0],
            "slope": [0, 0, 2],
            "ca": [0, 0, 0],
            "thal": [1, 1, 2],
            "target": [1, 1, 0],
        }
    )
    clean = clean_heart(raw)
    assert len(clean) == 2
    assert set(clean["target"].unique()) <= {0, 1}
