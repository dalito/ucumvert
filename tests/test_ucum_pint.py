from pint import Quantity, UnitRegistry
from ucumvert.ucum_pint import ucum_to_pint


def test_ucum_to_pint():
    p = [{"prefix": "m", "type": "metric", "unit": "m"}]
    ureg = UnitRegistry()
    value = 17
    expected_quantity = Quantity(value, ureg("millimeter"))
    assert ucum_to_pint(p, value) == expected_quantity
