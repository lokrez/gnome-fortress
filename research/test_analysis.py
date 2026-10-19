import pytest
from research.analyze import km, quantiles


def test_kaplan_meier_death_before_tied_censor():
    rows = [dict(age_ticks=1, died=1), dict(age_ticks=1, died=0), dict(age_ticks=2, died=1)]
    curve = km(rows)
    assert curve[1]["risk"] == 3
    assert curve[1]["survival"] == pytest.approx(2/3)
    assert curve[2]["risk"] == 1
    assert curve[2]["survival"] == 0


def test_all_censored_is_not_zero_survival():
    curve = km([dict(age_ticks=2, died=0), dict(age_ticks=3, died=0)])
    assert all(row["survival"] == 1 for row in curve)
    assert quantiles([])["median"] is None
