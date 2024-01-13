from pathlib import Path

import lark
import pytest
from lark import Token
from lark.tree import Tree

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
        "x8": "{/ann1/2.g}/m",  # operators in annotation
    }
)


@pytest.mark.parametrize(
    "ucum_code",
    ucum_examples_valid.values(),
    ids=[" ".join(kv) for kv in ucum_examples_valid.items()],
)
def test_ucum_parser_official_examples(ucum_parser, ucum_code):
    if ucum_code == "Torr":
        # Torr is missing in ucum-essence.xml but included in the official examples.
        # https://github.com/ucum-org/ucum/issues/289
        pytest.skip("Torr is not defined in official ucum-essence.xml")
    if ucum_code == "[pH]":
        pytest.skip("[ph] = pH_value is not defined in pint due to an issue.")
    ucum_parser.parse(ucum_code)


@pytest.mark.parametrize(
    "ucum_code",
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
def test_ucum_parser_invalid_ucum_codes(ucum_parser, ucum_code):
    with pytest.raises(lark.exceptions.UnexpectedInput):
        ucum_parser.parse(ucum_code)


def test_ucum_parser_metric(ucum_parser):
    # Note: ucum_parser.parse = ucum_parser().parse
    tree = ucum_parser.parse("m")
    expected = Tree(
        Token("RULE", "main_term"),
        [Tree(Token("RULE", "simple_unit"), [Token("UNIT_METRIC", "m")])],
    )
    assert tree == expected
