from pathlib import Path

import lark
import pytest
from lark import Token
from lark.tree import Tree
from ucumvert.parser import UnitsTransformer, parse_and_transform

datadir = Path(__file__).resolve().parents[1] / "src" / "ucumvert" / "vendor"

with Path(datadir / "ucum_examples.tsv").open(encoding="utf8") as f:
    ucum_examples_valid = {}
    for line in f.readlines():
        if line.startswith("Row #"):
            continue
        line_no, unit = line.split("\t")[:2]
        ucum_examples_valid[line_no] = unit

ucum_examples_valid.update(
    {  # add more valid examples beyond official examples
        "x1": "((kg)/(m.(s)))",  # bracket test,
        "x2": "(s)",  # bracketed unit atom
        "x3": "(/s)",  # bracketed unary divide
        "x4": "(/s2{sunit_s2}.(10{factor}.m{sunit_m}){term}){mterm}",  # annotations everywhere
        "x5": "dar",  # ambiguous prefix-unit combo: deci-are vs. deka-r (unit "r" does not exist)
        "x6": "{}/m",
        "x7": "{}",
    }
)


@pytest.mark.parametrize(
    "ucum_unit", ucum_examples_valid.values(), ids=ucum_examples_valid.keys()
)
def test_ucum_parser_official_examples(ucum_parse_fcn, ucum_unit):
    if ucum_unit == "Torr":
        # Torr is missing in ucum-essence.xml but included in the official examples.
        # https://github.com/ucum-org/ucum/issues/289
        pytest.skip("Torr is not defined in official ucum-essence.xml")
    ucum_parse_fcn(ucum_unit)


@pytest.mark.parametrize(
    "ucum_unit",
    [
        "bars",  # invalid unit
        "2mg",  # missing operator
        ".m",  # invalid operator position
        "m.",  # invalid operator position
        "m/",  # invalid operator position
        r"{red}m",  # invalid annotation position
        "m(/s)",  # invalid parentheses. Note, "(/s)" is valid.
        "(m/s)2",  # invalid since UCUM v 1.9
        "m{ann1}{ann2}",  # invalid double annotation
        "da",  # invalid prefix-unit combo (a is not metric)
    ],
)
def test_ucum_parser_invalid_ucum_codes(ucum_parse_fcn, ucum_unit):
    with pytest.raises(lark.exceptions.UnexpectedInput):
        ucum_parse_fcn(ucum_unit)


def test_ucum_parser_metric(ucum_parse_fcn):
    # Note: ucum_parse_fcn = ucum_parser().parse
    tree = ucum_parse_fcn("m")
    expected = Tree(
        Token("RULE", "main_term"),
        [Tree(Token("RULE", "simple_unit"), [Token("METRIC", "m")])],
    )
    assert tree == expected


@pytest.mark.skip("TODO: implement")
def test_parse_and_transform_metric():
    tree = parse_and_transform(UnitsTransformer, "m")
    expected = [{"type": "metric", "unit": "m"}]
    assert tree == expected


@pytest.mark.skip("TODO: implement")
@pytest.mark.parametrize(
    "ucum_unit", ucum_examples_valid.values(), ids=ucum_examples_valid.keys()
)
def test_parse_and_transform_official_examples(ucum_unit):
    if ucum_unit == "Torr":
        # Torr is missing in ucum-essence.xml but included in the official examples.
        # see https://github.com/ucum-org/ucum/issues/289
        pytest.skip("Torr is not defined in official ucum-essence.xml")
    parse_and_transform(UnitsTransformer, ucum_unit)
