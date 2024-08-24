import pytest

import ucumvert
from ucumvert.xml_util import get_metric_units, get_non_metric_units, get_prefixes


def get_units_2casings():
    ucumvert.xml_util.CODE_ATTRIB = "Code"
    cased = get_metric_units() + get_non_metric_units()
    # Unit code "L" has no no-case version so we remove it.
    cased.remove("L")
    ucumvert.xml_util.CODE_ATTRIB = "CODE"
    nocase = get_metric_units() + get_non_metric_units()
    ucumvert.xml_util.CODE_ATTRIB = "Code"
    assert len(cased) == len(nocase)
    return zip(cased, nocase)


def get_prefixes_2casings():
    ucumvert.xml_util.CODE_ATTRIB = "Code"
    cased = get_prefixes()
    ucumvert.xml_util.CODE_ATTRIB = "CODE"
    nocase = get_prefixes()
    ucumvert.xml_util.CODE_ATTRIB = "Code"
    ret = zip(cased, nocase)
    assert len(cased) == len(nocase)
    return ret


@pytest.mark.parametrize(("cased_code", "nocase_code"), get_units_2casings())
def test_transformability_unitcodes_nocase_to_cased(cased_code, nocase_code):
    """Document differences cased vs. no-case UCUM units and check case of no-case codes."""

    # Cased UCUM atoms that cannot be upper-cased to get its no-case version
    non_derivable_units = {
        # metric units
        "Pa": "PAL",
        "S": "SIE",
        "t": "TNE",
        "u": "AMU",
        "pc": "PRS",
        "[G]": "[GC]",
        "Gal": "GL",
        "G": "GS",
        "ph": "PHT",
        "R": "ROE",
        "RAD": "[RAD]",
        "REM": "[REM]",
        "Np": "NEP",
        "st": "STR",
        # non-metric units
        "h": "HR",
        "a_t": "ANN_T",
        "a_j": "ANN_J",
        "a_g": "ANN_G",
        "a": "ANN",
        "AU": "ASU",
        "b": "BRN",
    }
    if nocase_code in ("[degR]", "[degRe]"):
        pytest.skip("[degR] is defined in UCUM with wrong case")
    if cased_code in non_derivable_units:
        assert non_derivable_units[cased_code] == nocase_code
    else:
        assert cased_code.upper() == nocase_code
    assert nocase_code == nocase_code.upper()  # assert correct case


@pytest.mark.parametrize(("cased_code", "nocase_code"), get_prefixes_2casings())
def test_transformability_prefixcodes_nocase_to_cased(cased_code, nocase_code):
    """Document differences cased vs. no-case UCUM prefixes and check case of no-case codes."""
    # Cased UCUM atoms that cannot be upper-cased to get its no-case version
    non_derivable_prefixes = {
        # prefixes
        "Y": "YA",
        "Z": "ZA",
        "E": "EX",
        "P": "PT",
        "T": "TR",
        "G": "GA",
        "M": "MA",
        "z": "ZO",
        "y": "YO",
        "Ki": "KIB",
        "Mi": "MIB",
        "Gi": "GIB",
        "Ti": "TIB",
    }
    if cased_code in non_derivable_prefixes:
        assert nocase_code == non_derivable_prefixes[cased_code]
    else:
        assert cased_code.upper() == nocase_code
    assert nocase_code == nocase_code.upper()  # assert correct case
