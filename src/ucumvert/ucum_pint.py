from __future__ import annotations

import contextlib
import logging
from pathlib import Path

from lark import Transformer
from lark.exceptions import VisitError
from pint import (
    DefinitionSyntaxError,
    UndefinedUnitError,
    UnitRegistry,
    get_application_registry,
)

from ucumvert.parser import (
    get_ucum_parser,
)
from ucumvert.xml_util import (
    get_metric_units,
    get_non_metric_units,
    get_prefixes,
    get_units_with_full_definition,
)

logger = logging.getLogger(__name__)


# Some UCUM unit atoms are syntactically incompatible with pint. For these we
# map to a pint-compatible unit name which we define in pint_ucum_defs.txt
# as alias or new unit. To determine what needs a mapping, use the function
# "find_ucum_codes_that_need_mapping()" below.
# In addition, we also map UCUM units that are interpreted as another unit
# with pint's default unit files. Since pint ignores surrounding square braces
# it reduces "[pH]", to "pH" first which is the interpreted as pico-Henry.

MAPPINGS_UCUM_TO_PINT = {
    # "UCUM_unit_atom": "pint_unit_name_or_alias"
    # === prefixes ===
    # all good!
    # === metric units ===
    "cal_[20]": "cal_20",
    "cal_[15]": "cal_15",
    "m[H2O]": "meter_H2O",
    "m[Hg]": "meter_Hg",
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
    "%[slope]": r"% slope",
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
    # === ucum codes with incorrect default interpretation in pint ===
    "B": "bel",
    "AU": "astronomical_unit",
    "[crd_us]": "cord",
    "[dqt_us]": "US_dry_quart",
    "[dpt_us]": "US_dry_pint",
    "[min_us]": "minim",
    "[min_br]": "imperial_minim",
    "[mi_i]": "international_mile",  # We cannot define mi_i as alias because nmi_i would be misinterpreted.
    "[nmi_i]": "nautical_mile",
    "[pH]": "pH_value",
    "[S]": "svedberg",
    "[AU]": "allergen_unit",
    "[EU]": "Ehrlich_unit",
    "R": "roentgen",
    "ph": "phot",
    "[g]": "standard_gravity",
    "[G]": "gravitational_constant",
    "[h]": "planck_constant",
}


class UcumToPintTransformer(Transformer):
    def __init__(self, ureg=None):
        if ureg is None:
            self.ureg = get_application_registry()
            # Append definitions for ucum units to the registry if not already done.
            if "peripheral_vascular_resistance_unit" not in self.ureg:
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
            # Work around a pint bug: parsing of abbreviated custom unit with prefix
            #   that could be a unit (k,m,M) does not detect the prefix but 2 units.
            #   e.g. m[IU] --> <Quantity(1, 'meter * [IU]')> instead of <Quantity(1, 'milli[IU]')>
            # Therefore, this fails (pint 0.23):
            #   return self.ureg(args[0] + args[1])

            with contextlib.suppress(UndefinedUnitError):
                return self.ureg(args[0] + str(self.ureg(args[1]).units))

            return self.ureg(args[0] + MAPPINGS_UCUM_TO_PINT.get(str(args[1]), str(args[1])))

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
            return f"({args[0]}{args[1]})"

        # Substitute UCUM atoms that cannot be defined in pint as units or aliases.
        ret = MAPPINGS_UCUM_TO_PINT.get(args[0], args[0])
        return f"({ret})"

    def annotatable(self, args):
        # print("DBGan>", repr(args), len(args))
        if len(args) == 2:  # exponent is present  # noqa: PLR2004
            return f"{args[0]}**{int(args[1])}"
        return f"({args[0]})"


def ucum_preprocessor(unit_input):
    """
    Preprocessor for pint to convert all input from UCUM to pint units.

    Note: This will make most standard pint unit expressions invalid.

    Usage:
        >>> from ucumvert import PintUcumRegistry, ucum_preprocessor
        >>> ureg = PintUcumRegistry()
        >>> ureg.preprocessors.append(ucum_preprocessor)
    """
    ucum_parser = get_ucum_parser()
    transformer = UcumToPintStrTransformer()
    parsed_data = ucum_parser.parse(unit_input)
    return str(transformer.transform(parsed_data))


def find_ucum_codes_that_need_mapping(existing_mappings=MAPPINGS_UCUM_TO_PINT):
    """Find UCUM atoms that are syntactically incompatible with pint."""
    logger.info("The following UCUM atoms must be mapped to valid pint unit names.")
    ureg = UnitRegistry()
    sections = {
        "prefixes": get_prefixes,
        "metric": get_metric_units,
        "non-metric": get_non_metric_units,
    }
    need_mappings = {k: [] for k in sections}
    for section, get_fcn in sections.items():
        logger.info(f"\n=== {section} ===")  # noqa: G004
        for ucum_code in get_fcn():
            if ucum_code in existing_mappings:
                continue
            def_str = (
                f"{ucum_code}- = 1" if section == "prefixes" else f"{ucum_code} = 1"
            )
            try:
                ureg.define(def_str)
            except DefinitionSyntaxError:
                need_mappings[section].append(ucum_code)
                logger.info(f"{ucum_code}")  # noqa: G004
                continue
        if not need_mappings[section]:
            logger.info("all good!")

    return need_mappings


def format_unit_as_pint_definition(u):
    """Format a UCUM unit as a pint definition."""
    op = "" if u.defining_unit.startswith("/") else " * "
    ucum_code_dcls = f"{u.code_cs} = {u.conversion_factor}{op}{u.defining_unit}  #"
    utype = "METRIC" if u.is_metric else "NON_METRIC"
    ucum_code_dcls += f" {utype}, {u.name}, {u.property_} ({u.class_})"
    return ucum_code_dcls


def is_in_registry(transformer, ucum_code):
    try:
        transformer.transform(ucum_code)
    except (UndefinedUnitError, VisitError):
        return False
    return True


def find_matching_pint_definitions(report_file: Path | None = None) -> None:
    """Find Pint units that match UCUM units."""
    if report_file is None:
        report_file = (
            Path(__file__).resolve().parent / "pint_ucum_defs_mapping_report.txt"
        )

    report = [
        "# Computed list of mappings between pint, ucumvert and UCUM units for easy review."
    ]

    ureg_default = UnitRegistry()
    ureg_ucum = UnitRegistry()
    ureg_ucum.load_definitions(Path(__file__).resolve().parent / "pint_ucum_defs.txt")
    ucum_parser = get_ucum_parser()
    transformer_default = UcumToPintTransformer(ureg=ureg_default)
    transformer_ucum = UcumToPintTransformer(ureg=ureg_ucum)

    details_by_unit = {u.code_cs: u for u in get_units_with_full_definition()}
    sections = {
        "prefixes": get_prefixes,
        "metric": get_metric_units,
        "non-metric": get_non_metric_units,
    }
    for section, get_fcn in sections.items():
        report.append(f"\n# === {section} ===")
        for ucum_code in get_fcn():
            lookup_str = f"{ucum_code}m" if section == "prefixes" else ucum_code
            try:
                parsed_data = ucum_parser.parse(lookup_str)
            except VisitError as exc:
                logger.exception("PARSER ERROR: %s", {exc.args[0]})
                raise
            lookup_str = MAPPINGS_UCUM_TO_PINT.get(ucum_code, ucum_code)
            if is_in_registry(transformer_default, parsed_data):
                if section == "prefixes":
                    pint_prefix = str(ureg_default(f"{ucum_code}m").units).removesuffix(
                        "meter"
                    )
                    report.append(
                        f"# {lookup_str:>10} --> {pint_prefix} (default registry)"
                    )
                else:
                    info = format_unit_as_pint_definition(details_by_unit[ucum_code])
                    pint_unit = f"{ureg_default(lookup_str).units} (default registry)"
                    report.append(f"# {ucum_code:>10} --> {pint_unit:<42} # {info}")
                continue
            if is_in_registry(transformer_ucum, parsed_data):
                info = format_unit_as_pint_definition(details_by_unit[ucum_code])
                pint_unit = f"{ureg_ucum(lookup_str).units} (ucumvert registry)"
                report.append(f"# {ucum_code:>10} --> {pint_unit:<42} # {info}")
            else:
                info = format_unit_as_pint_definition(details_by_unit[ucum_code])
                report.append(f"# {ucum_code:>10} --> {'NOT DEFINED':<42} # {info}")

    with Path(report_file).open("w", encoding="utf8") as fp:
        fp.write("\n".join(report) + "\n")
    logger.info("Created mapping report: %s", report_file)


class PintUcumRegistry(UnitRegistry):
    def _after_init(self) -> None:
        """This is called after all __init__"""
        super()._after_init()  # load pint's default unit definitions

        # Append definitions for ucum units to the registry.
        loaded_files = self.load_definitions(
            Path(__file__).resolve().parent / "pint_ucum_defs.txt"
        )
        self._build_cache(loaded_files)

        # Initialise UCUM parser and transformer
        self._ucum_parser = get_ucum_parser()
        self._from_ucum_transformer = UcumToPintTransformer().transform

    def from_ucum(self, ucum_code):
        """Transform an ucum_code to a pint unit.

        Parameters
        ----------
        ucum_code :
            Ucum code as string.
        """
        parsed_data = self._ucum_parser.parse(ucum_code)
        return self._from_ucum_transformer(parsed_data)


def run_examples():  # pragma: no cover
    test_ucum_units = [
        # "Cel",
        # "/s2",
        # r"m.s{s_ann}",
        "[arb'U]",
    ]
    parser = get_ucum_parser()
    for unit in test_ucum_units:
        print("parsing ucum code:", unit)
        parsed_data = parser.parse(unit)
        q = UcumToPintTransformer().transform(parsed_data)
        print(f"Pint {q!r}")


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO)
    # run_examples()
    find_matching_pint_definitions()
    find_ucum_codes_that_need_mapping()
