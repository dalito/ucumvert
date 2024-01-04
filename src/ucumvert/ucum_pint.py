import functools
import operator

import pint

from ucumvert.parser import UnitsTransformer, parse_and_transform

# TODO Handle unit conversions if a mapping to pint default units is not possible
# e.g. "mm[Hg]" in UCUM is interpreted as prefix "m" and unit "m[Hg]";
#   but pint directly defines Hg : ?, # TODO no corresponding pint default unit exist. is not possenough, we need to define  a function to convert

ucum_to_pint_map = {
    "Cel": "degC",
    "m[Hg]": "Hg * g_0",
}


def ucum_to_pint(p, value):
    ureg = pint.UnitRegistry()

    # TODO the parser should return consistent results independent of the number of units terms,
    #      It should always return a list of dictionaries with one dictionary per unit term.
    if isinstance(p[0], list):  # dirty fix
        p = p[0]

    # TODO apply division operator (division is ignored now)
    # TODO convert units with factors; there are many of these in ucum but few in pint

    u_strs = []
    for unit_term in p:
        op = unit_term.get("operator", None)
        prefix = unit_term.get("prefix", "")
        unit = unit_term.get("unit", "")
        exp = unit_term.get("exponent", None)

        # replace ucum unit code with pint unit code
        unit_fixed = ucum_to_pint_map.get(unit, unit)
        u_str = prefix + unit_fixed + (f"**{exp}" if exp else "")
        if u_str:
            u_str = u_str if op is None else f"1{op}{u_str}"

        print(f"calling pint.ureg with: {u_str!r}")
        u_strs.append(ureg(u_str))
    units = functools.reduce(operator.mul, u_strs)
    print("-> pint unit:", units)
    return pint.Quantity(value, units)


def test():
    test_ucum_units = [
        "Cel",
        "/s2",
        "/s.m.N",
        "/s.m",
        "mm[Hg]{sealevel}",
        "kcal/10",
        "kcal/10{cookies}",
        "g/kg/(8.h){shift}",
        # "2mg",  # expected failure (should be "2.mg")
    ]
    for unit in test_ucum_units:
        p = parse_and_transform(UnitsTransformer, unit)
        q = ucum_to_pint(p, 123)
        print("pint quantity:", q)


def main():
    print(
        "\nEnter quantity with UCUM units, or 'q' to quit. Value and unit must be separated by one space."
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
    main()
