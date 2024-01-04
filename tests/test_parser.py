from pathlib import Path

import pytest
from lark import Token
from lark.tree import Tree
from ucumvert.parser import UnitsTransformer, parse_and_transform

datadir = Path(__file__).resolve().parents[1] / "src" / "ucumvert" / "vendor"
print(datadir)

with open(datadir / "ucum_examples.tsv", encoding="utf8") as f:
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
def test_ucum_parser_ucum_examples(ucum_parse_fcn, ucum_unit):
    # Note: ucum_parse_fcn = ucum_parser().parse
    print(f"line {line_no:>4}: {ucum_unit}")
    tree = ucum_parse_fcn(ucum_unit)
    print(tree)


def test_parse_and_transform_metric():
    tree = parse_and_transform(UnitsTransformer, "m")
    expected = [{"type": "metric", "unit": "m"}]
    assert tree == expected
