from pathlib import Path

import pint
from lark import Transformer

from ucumvert.parser import (
    get_ucum_parser,
    make_parse_tree_png,
    update_lark_ucum_grammar_file,
)

# TODO Handle unit conversions if a mapping to pint default units is not possible
# e.g. "mm[Hg]" in UCUM is interpreted as prefix "m" and unit "m[Hg]";
#   but pint directly defines Hg : ?,
# TODO no corresponding pint default unit exist. is not possenough, we need to define  a function to convert


class UcumToPintTransformer(Transformer):
    def __init__(self, ureg=None):
        if ureg is None:
            self.ureg = pint.UnitRegistry()
            # Append the local definitions for ucum units to the default registry
            self.ureg.load_definitions(
                Path(__file__).resolve().parent / "pint_ucum_defs.txt"
            )
        else:
            self.ureg = ureg

    def main_term(self, args):
        # print("DBGmt>", repr(args), len(args))
        if len(args) == 2:  # unary DIVIDE  # noqa: PLR2004
            if getattr(args[1], "type", None):  # no unit, only an ANNOTATION
                return self.ureg("")  # return <Quantity(1, 'dimensionless')>
            return 1 / args[1]
        return args[0]

    def term(self, args):
        # print("DBGt>", repr(args), len(args))
        if len(args) == 3:  # noqa: PLR2004
            if (
                getattr(args[0], "type", None) == "ANNOTATION"
            ):  # first term is annotation
                args[0] = 1
            if (
                getattr(args[2], "type", None) == "ANNOTATION"
            ):  # second term is annotation
                args[2] = 1
            if args[1] == ".":  # multiplication
                return args[0] * args[2]
            # division
            return args[0] / args[2]
        return args[0]  # no operator, return single component

    def component(self, args):
        # print("DBGc>", repr(args), len(args))
        if args[1].type == "ANNOTATION":  # ignore annotations
            # print(f"dropping annotation: {args[1]}")
            return args[0]
        return args[:]

    def simple_unit(self, args):
        # print("DBGsu>", repr(args), len(args))
        if len(args) == 2:  # prefix is present  # noqa: PLR2004
            return self.ureg(args[0] + args[1])

        # Catch UCUM atoms that cannot be defined in pint as units or aliases.
        if args[0].value in ["10*", "10^"]:
            return self.ureg("_10")

        return self.ureg(args[0])

    def annotatable(self, args):
        # print("DBGan>", repr(args), len(args))
        if len(args) == 2:  # exponent is present  # noqa: PLR2004
            return args[0] ** int(args[1])
        return args[0]


def run_examples():
    test_ucum_units = [
        "Cel",
        "/s2",
        "/s.m.N",
        "/s.m",
        "kg/(s.m2)",
        r"m.s{s_ann}",
    ]
    parser = get_ucum_parser()
    for unit in test_ucum_units:
        print("parsing ucum code:", unit)
        make_parse_tree_png(unit, filename="parse_tree.png")
        parsed_data = parser.parse(unit)
        q = UcumToPintTransformer().transform(parsed_data)
        print(f"Pint {q!r}")


if __name__ == "__main__":
    update_lark_ucum_grammar_file()
    run_examples()
