from ucumvert.xml_util import get_metric_units, get_non_metric_units, get_units


def test_get_units():
    assert len(get_units()) == 303  # noqa: PLR2004
    assert set(get_units()) == set(get_metric_units() + get_non_metric_units())
