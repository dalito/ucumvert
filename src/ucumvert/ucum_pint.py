import functools
import operator

import pint

from ucumvert.parser import lark_parser

ucum_to_pint_map = {
    "Cel": "degC",
}


def ucum_to_pint(p, value, ucum_unit):
    ureg = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)

    # TODO the parser should return consistent results independent of the number of units terms,
    #      It should always return a list of dictionaries with one dictionary per unit term.
    if isinstance(p[0], list):  # fix inconsistent parser results
        p = p[0]

    # TODO apply devision operator (division is ignored now)
    # TODO correctly use multipliers which are ignored now
    u_strs = []
    for unit_term in p:
        prefix = unit_term.get("prefix", "")
        exp = unit_term.get("exponent", None)
        # replace ucum unit atom with pint unit atom
        if unit_term["unit"] in ucum_to_pint_map:
            unit_term["unit"] = ucum_to_pint_map[unit_term["unit"]]
        u_str = ureg(prefix + unit_term["unit"] + (f"**{exp}" if exp else ""))
        # print("pint unit:", u_str)
        u_strs.append(u_str)
    units = functools.reduce(operator.mul, u_strs)
    print("-> pint unit:", units)
    q = pint.Quantity(value, units)
    return q


def test():
    test_ucum_units = [
        "mm[Hg]{sealevel}",
        "Cel",
        "/s",
        "/s.m.N",
        "/s.m",
    ]
    for unit in test_ucum_units:
        p = lark_parser(unit)
        ucum_to_pint(p, 10, unit)


def main():
    print(
        "Enter quantity with UCUM units, or 'q' to quit. The value and unit must be sepearated by a space."
    )
    while True:
        s = input("> ")
        if s in "qQ":
            break
        try:
            value, unit = s.split()
            p = lark_parser(unit)
            print(ucum_to_pint(p, value, unit))
        except Exception as e:
            print(e)


if __name__ == "__main__":
    test()
    main()
