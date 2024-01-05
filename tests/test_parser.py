from pathlib import Path

import lark
import pytest
from lark import Token
from lark.tree import Tree
from ucumvert.parser import UnitsTransformer, parse_and_transform

datadir = Path(__file__).resolve().parents[1] / "src" / "ucumvert" / "vendor"

with Path(datadir / "ucum_examples.tsv").open(encoding="utf8") as f:
    ucum_examples_valid = []
    ucum_examples_valid_ids = []
    for line in f.readlines():
        if line.startswith("Row #"):
            continue
        line_no, unit = line.split("\t")[:2]
        ucum_examples_valid.append(unit)
        ucum_examples_valid_ids.append(line_no)


def test_ucum_parser_metric(ucum_parse_fcn):
    # Note: ucum_parse_fcn = ucum_parser().parse
    tree = ucum_parse_fcn("m")
    expected = Tree(
        Token("RULE", "start"),
        [
            Tree(
                Token("RULE", "term"),
                [
                    Tree(
                        Token("RULE", "component"),
                        [
                            Tree(
                                Token("RULE", "annotatable"),
                                [
                                    Tree(
                                        Token("RULE", "simple_unit"),
                                        [Token("METRIC", "m")],
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    assert tree == expected


@pytest.mark.parametrize("ucum_unit", ucum_examples_valid, ids=ucum_examples_valid_ids)
def test_ucum_parser_official_examples(ucum_parse_fcn, ucum_unit):
    if ucum_unit == "Torr":
        # Torr is missing in ucum-essence.xml but included in the official examples.
        # TODO: create issue in https://github.com/ucum-org/ucum/
        pytest.skip("Torr is not defined in official ucum-essence.xml")
    ucum_parse_fcn(ucum_unit)


@pytest.mark.parametrize(
    "ucum_unit",
    [
        "bars",  # invalid unit
        "2mg",  # missing operator
        ".m",  # invalid operator positions
        "m.",
        "m/",
        r"{red}m",  # invalid annotation position
    ],
)
def test_ucum_parser_invalid_ucum_codes(ucum_parse_fcn, ucum_unit):
    with pytest.raises(lark.exceptions.UnexpectedInput):
        ucum_parse_fcn(ucum_unit)


def test_parse_and_transform_metric():
    tree = parse_and_transform(UnitsTransformer, "m")
    expected = [{"type": "metric", "unit": "m"}]
    assert tree == expected
