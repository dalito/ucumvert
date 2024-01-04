import functools
import operator

import pint

from ucumvert.parser import UnitsTransformer, parse_and_transform

ucum_to_pint_map = {
    "Cel": "degC",
}


def ucum_to_pint(p, value):
    ureg = pint.UnitRegistry()

    # TODO the parser should return consistent results independent of the number of units terms,
    #      It should always return a list of dictionaries with one dictionary per unit term.
    if isinstance(p[0], list):  # fix inconsistent parser results
        p = p[0]

    # TODO apply division operator (division is ignored now)
    # TODO correctly use factors which are ignored now

    u_strs = []
    for unit_term in p:
        prefix = unit_term.get("prefix", "")
        exp = unit_term.get("exponent", None)
        unit = unit_term.get("unit", "")
        # replace ucum unit code with pint unit code
        unit_fixed = ucum_to_pint_map.get(unit, unit)
        u_str = ureg(prefix + unit_fixed + (f"**{exp}" if exp else ""))
        # print("pint unit:", u_str)
        u_strs.append(u_str)
    units = functools.reduce(operator.mul, u_strs)
    print("-> pint unit:", units)
    return pint.Quantity(value, units)


def test():
    test_ucum_units = [
        "mm[Hg]{sealevel}",
        "Cel",
        "/s2",
        "/s.m.N",
        "/s.m",
        "kcal/10",
        "kcal/10{cookies}",
        "(8.h){shift}",
        # "2mg",  # expected failure (should be "2.mg")
    ]
    for unit in test_ucum_units:
        print("ucum unit:", unit)
        p = parse_and_transform(UnitsTransformer, unit)
        ucum_to_pint(p, 10)


def main():
    print(
        "Enter quantity with UCUM units, or 'q' to quit. The value and unit must be separated by a space."
    )
    while True:
        s = input("> ")
        if s in "qQ":
            break
        try:
            value, unit = s.split()
            p = parse_and_transform(UnitsTransformer, unit)
            print(ucum_to_pint(p, value))
        except Exception as e:
            print(e)


if __name__ == "__main__":
    test()
    # main()
