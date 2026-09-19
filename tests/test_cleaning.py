from __future__ import annotations

import numpy as np
import pandas as pd

from src.app_insights import clean_play_store, _parse_installs, _parse_price, _parse_size


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
