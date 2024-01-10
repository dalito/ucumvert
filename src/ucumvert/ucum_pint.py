from pathlib import Path

import pint
from lark import Transformer

from ucumvert.parser import (
    get_ucum_parser,
    make_parse_tree_png,
    update_lark_ucum_grammar_file,
)

# Some UCUM unit atoms are syntactically incompatiple with pint. For these we
# map to a pint-compatible unit name which we define in pint_ucum_defs.txt
# as alias or new unit.
# TODO Define the commented out units in pint_ucum_defs.txt

mappings_ucum_to_pint = {
    # "UCUM_unit_atom": "pint_unit_name_or_alias"
    # === metric units ===
    "cal_[20]": "cal_20",
    "cal_[15]": "cal_15",
    # === non-metric units ===
    "10*": "_10",
    "10^": "_10",
    "'": "minute",
    "''": "second",
    # "[in_i'H2O]": "in_i_H2O",
    # "[in_i'Hg]": "in_i_Hg",
    # "[wood'U]": "wood_U",
    # "[p'diop]": "p_diop",
    # "[hnsf'U]": "hnsf_U",
    # "[hp'_X]": "hp_X",
    # "[hp'_C]": "hp_C",
    # "[hp'_M]": "hp_M",
    # "[hp'_Q]": "hp_Q",
    "[arb'U]": "arb_U",
    "[USP'U]": "USP_U",
    "[GPL'U]": "GPL_U",
    "[MPL'U]": "MPL_U",
    "[APL'U]": "APL_U",
    "[beth'U]": "beth_U",
    # "[anti'Xa'U]": "anti_Xa_U",
    "[todd'U]": "todd_U",
    # "[dye'U]": "dye_U",
    # "[smgy'U]": "smgy_U",
    "[bdsk'U]": "bdsk_U",
    # "[ka'U]": "ka_U",
    "[knk'U]": "knk_U",
    "[mclg'U]": "mclg_U",
    "[tb'U]": "tb_U",
    # "[Amb'a'1'U]": "Amb_a_1_U",
    # "[D'ag'U]": "D_ag_U",
    "[m/s2/Hz^(1/2)]": "meter_per_square_second_per_square_root_of_hertz",
}


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

        # Substitute UCUM atoms that cannot be defined in pint as units or aliases.
        return self.ureg(mappings_ucum_to_pint.get(args[0], args[0]))

    def annotatable(self, args):
        # print("DBGan>", repr(args), len(args))
        if len(args) == 2:  # exponent is present  # noqa: PLR2004
            return args[0] ** int(args[1])
        return args[0]


def run_examples():
    test_ucum_units = [
        # "Cel",
        # "/s2",
        # r"m.s{s_ann}",
        "[arb'U]",
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
