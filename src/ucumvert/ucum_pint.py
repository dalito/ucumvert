from pathlib import Path

import pint
from lark import Transformer
from lark.exceptions import VisitError

from ucumvert.parser import (
    get_ucum_parser,
    make_parse_tree_png,
    update_lark_ucum_grammar_file,
)
from ucumvert.xml_util import get_metric_units, get_non_metric_units, get_prefixes

# Some UCUM unit atoms are syntactically incompatiple with pint. For these we
# map to a pint-compatible unit name which we define in pint_ucum_defs.txt
# as alias or new unit. To determine what needs a mapping, use the function
# "find_ucum_codes_that_need_mapping()" below.

MAPPINGS_UCUM_TO_PINT = {
    # "UCUM_unit_atom": "pint_unit_name_or_alias"
    # === prefixes ===
    # all good!
    # === metric units ===
    "cal_[20]": "cal_20",
    "cal_[15]": "cal_15",
    "m[H2O]": "m_H2O",
    "m[Hg]": "m_Hg",
    "g%": "g%",  # invalid as unit name but correctly parsed as <Unit('gram * percent')>
    "B[SPL]": "B_SPL",
    "B[V]": "B_V",
    "B[mV]": "B_mV",
    "B[uV]": "B_uV",
    "B[10.nV]": "B_10nV",
    "B[W]": "B_W",
    "B[kW]": "B_kW",
    # === non-metric units ===
    "10*": "_10",
    "10^": "_10",
    "%": "%",  # invalid as unit name but correctly parsed as <Unit('percent')>
    "'": "minute",
    "''": "second",
    "[in_i'H2O]": "in_i_H2O",
    "[in_i'Hg]": "in_i_Hg",
    "[wood'U]": "wood_U",
    "[p'diop]": "p_diop",
    "%[slope]": "% slope",
    "[hnsf'U]": "hnsf_U",
    "[hp'_X]": "hp_X",
    "[hp'_C]": "hp_C",
    "[hp'_M]": "hp_M",
    "[hp'_Q]": "hp_Q",
    "[arb'U]": "arb_U",
    "[USP'U]": "USP_U",
    "[GPL'U]": "GPL_U",
    "[MPL'U]": "MPL_U",
    "[APL'U]": "APL_U",
    "[beth'U]": "beth_U",
    "[anti'Xa'U]": "anti_Xa_U",
    "[todd'U]": "todd_U",
    "[dye'U]": "dye_U",
    "[smgy'U]": "smgy_U",
    "[bdsk'U]": "bdsk_U",
    "[ka'U]": "ka_U",
    "[knk'U]": "knk_U",
    "[mclg'U]": "mclg_U",
    "[tb'U]": "tb_U",
    "[Amb'a'1'U]": "Amb_a_1_U",
    "[D'ag'U]": "D_ag_U",
    "[m/s2/Hz^(1/2)]": "meter_per_square_second_per_square_root_of_hertz",
}


class UcumToPintTransformer(Transformer):
    def __init__(self, ureg=None):
        if ureg is None:
            self.ureg = pint.UnitRegistry(on_redefinition="raise")
        else:
            self.ureg = ureg
        # Append the local definitions for ucum units to the default registry
        self.ureg.load_definitions(
            Path(__file__).resolve().parent / "pint_ucum_defs.txt"
        )

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
        return self.ureg(MAPPINGS_UCUM_TO_PINT.get(args[0], args[0]))

    def annotatable(self, args):
        # print("DBGan>", repr(args), len(args))
        if len(args) == 2:  # exponent is present  # noqa: PLR2004
            return args[0] ** int(args[1])
        return args[0]


class UcumToPintStrTransformer(Transformer):
    def main_term(self, args):
        # print("DBGmt>", repr(args), len(args))
        if len(args) == 2:  # unary DIVIDE  # noqa: PLR2004
            if getattr(args[1], "type", None):  # no unit, only an ANNOTATION
                return "1"  # will create <Quantity(1, 'dimensionless')>
            return f"(1 / {args[1]})"
        return f"({args[0]})"

    def term(self, args):
        # print("DBGt>", repr(args), len(args))
        if len(args) == 3:  # noqa: PLR2004
            if (
                getattr(args[0], "type", None) == "ANNOTATION"
            ):  # first term is annotation
                args[0] = "1"
            if (
                getattr(args[2], "type", None) == "ANNOTATION"
            ):  # second term is annotation
                args[2] = "1"
            if args[1] == ".":  # multiplication
                return f"({args[0]} * {args[2]})"
            # division
            return f"({args[0]} / {args[2]})"
        return f"({args[0]})"  # no operator, return single component

    def component(self, args):
        # print("DBGc>", repr(args), len(args))
        if args[1].type == "ANNOTATION":  # ignore annotations
            # print(f"dropping annotation: {args[1]}")
            return f"({args[0]})"
        return args[:]

    def simple_unit(self, args):
        # print("DBGsu>", repr(args), len(args))
        if len(args) == 2:  # prefix is present  # noqa: PLR2004
            return f"({args[0]} + {args[1]})"

        # Substitute UCUM atoms that cannot be defined in pint as units or aliases.
        ret = MAPPINGS_UCUM_TO_PINT.get(args[0], args[0])
        return f"({ret})"

    def annotatable(self, args):
        # print("DBGan>", repr(args), len(args))
        if len(args) == 2:  # exponent is present  # noqa: PLR2004
            return f"{args[0]}**{int(args[1])}"
        return f"({args[0]})"


def ucum_preprocessor(unit_input):
    """Preprocess UCUM code before parsing as pint unit.

    Usage:
        ureg = pint.UnitRegistry()
        ureg.preprocessors.append(ucum_preprocessor)
    """
    ucum_parser = get_ucum_parser()
    transformer = UcumToPintStrTransformer()
    # print("DBGpp in >", repr(unit_input))
    parsed_data = ucum_parser.parse(unit_input)
    # pintified_str = str(transformer.transform(parsed_data))
    # print(f"DBGpp out> {pintified_str}")
    return str(transformer.transform(parsed_data))


def find_ucum_codes_that_need_mapping(existing_mappings=MAPPINGS_UCUM_TO_PINT):
    """Find UCUM atoms that are syntactically incompatiple with pint."""
    print("The following UCUM atoms must be mapped to valid pint unit names.")
    ureg = pint.UnitRegistry()
    sections = {
        "prefixes": get_prefixes,
        "metric": get_metric_units,
        "non-metric": get_non_metric_units,
    }
    need_mappings = {k: [] for k in sections}
    for section, get_fcn in sections.items():
        print(f"\n=== {section} ===")
        for ucum_code in get_fcn():
            if ucum_code in existing_mappings:
                continue
            def_str = (
                f"{ucum_code}- = 1" if section == "prefixes" else f"{ucum_code} = 1"
            )
            try:
                ureg.define(def_str)
            except pint.DefinitionSyntaxError:
                need_mappings[section].append(ucum_code)
                print(f"{ucum_code}")
                continue
        if not need_mappings[section]:
            print("all good!")
    return need_mappings


def find_matching_pint_definitions(ureg=None):
    """Find Pint units that match UCUM units."""
    if ureg is None:
        ureg = pint.UnitRegistry()
    sections = {
        "prefixes": get_prefixes,
        "metric": get_metric_units,
        "non-metric": get_non_metric_units,
    }
    ucum_parser = get_ucum_parser()
    transformer = UcumToPintTransformer(ureg=ureg)
    for section, get_fcn in sections.items():
        print(f"\n=== {section} ===")
        for ucum_code in get_fcn():
            lookup_str = f"{ucum_code}m" if section == "prefixes" else ucum_code
            try:
                parsed_data = ucum_parser.parse(lookup_str)
            except VisitError as exc:
                print(f"PARSER ERROR: {exc.args[0]}")
                raise
            try:
                pint_quantity = transformer.transform(parsed_data)
            except pint.UndefinedUnitError as exc:
                msg = getattr(exc, "msg", "")
                print(f"NOT DEFINED: {msg}")
                continue
            except VisitError as exc:
                msg = exc.args[0].splitlines()[-1]
                print(f"TRANSFORM ERROR: {msg}")
                continue
            print(f"{ucum_code} --> {pint_quantity!r}")


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


def get_pint_registry(ureg=None):
    """Return a pint registry with the UCUM definitions loaded."""
    if ureg is None:
        ureg = pint.UnitRegistry(on_redefinition="raise")
    ureg.preprocessors.append(ucum_preprocessor)
    ureg.load_definitions(Path(__file__).resolve().parent / "pint_ucum_defs.txt")
    return ureg


if __name__ == "__main__":
    update_lark_ucum_grammar_file()
    # run_examples()

    # find_ucum_codes_that_need_mapping()
    find_matching_pint_definitions()

    # ureg = get_pint_registry()
    # print(ureg("Cel"))
    # print(ureg("'"))
