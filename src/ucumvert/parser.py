from __future__ import annotations

import logging
import textwrap
from pathlib import Path

from lark import Lark, Transformer

import ucumvert
from ucumvert.xml_util import (
    get_base_units,
    get_metric_units,
    get_non_metric_units,
    get_prefixes,
)

logger = logging.getLogger(__name__)


# UCUM syntax in the Backus-Naur Form, copied from https://ucum.org/ucum#section-Syntax-Rules
# <sign>  : "+" | "-"
# <digit> : "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
# <digits>    : <digit><digits> | <digit>
# <factor>    : <digits>
# <exponent> 	: <sign><digits> | <digits>
# <simple-unit>   : <ATOM-SYMBOL>
#                 | <PREFIX-SYMBOL><ATOM-SYMBOL[metric]>
# <annotatable>   : <simple-unit><exponent>
#                 | <simple-unit>
# <component> : <annotatable><annotation>
#             | <annotatable>
#             | <annotation>
#             | <factor>
#             | "("<term>")"
# <term>  :   <term>"."<component>
#         | <term>"/"<component>
#         | <component>
# <main-term> : "/"<term>
#             | <term>
# <annotation>    : "{"<ANNOTATION-STRING>"}"
#
# The following commented-out lark grammar closely follows the specification
#    above but fails for "100/{cells}" and "g/(8.h){shift}". Both are valid
#    UCUM strings from the official examples. The BNF is not 100% correct.
# UCUM_GRAMMAR_almost_correct = """
#     simple_unit: METRIC
#             | PREFIX? METRIC
#             | NON_METRIC
#     annotatable: simple_unit EXPONENT
#             | simple_unit
#     component: annotatable annotation
#             | annotatable
#             | annotation
#             | FACTOR
#             | "(" term ")"
#     term: term OPERATOR component
#             | component
#     start: DIVIDE term
#             | term
#     annotation: "{{" STRING "}}"
#     STRING: /[^{{}}]+/
#     OPERATOR: "." | DIVIDE
#     DIVIDE: "/"
#     PREFIX: {prefix_rule}
#     METRIC: {metric_rule}
#     NON_METRIC: {non_metric_rule}

#     %import common.SIGNED_INT   -> EXPONENT
#     %import common.INT          -> FACTOR
# """

# Below is a fixed grammar that can parse all UCUM units in the official UCUM examples.
# and fixes some more edge cases not present in the official examples.
#
# Changes made:
# - To fix "100/{cells}" issue, we moved FACTOR from component to the simple_unit rule
# - To fix "(8.h){shift}" issue, we moved "(" term ")" from component to the annotatable rule
# - Don't allow "0" as EXPONENT or FACTOR, see https://github.com/ucum-org/ucum/issues/121
# - Don't allow curly braces {} inside of annotation STRING (ascii 123 and 125). Without this
#   or escaping rules the end of annotation STRING is ambiguous.
# - Move term from component rule to annotatable rule. Add maint_term and component to
#   annotatable rule. These changes solve various annotation issues with the original
#   grammar (e.g. "100{pc}", "(/m){ann}", "{ann1}{ann2}").
# - Distinguish short prefixes (1 char) form long ones to handle parsing of "dar" as deci-are
#   instead of deca-r which does not exist.

UCUM_GRAMMAR = """
    # Based on UCUM specification (Version 2.2, 2024-06-28)
    # Includes ucumvert-specific fixes to handle all common UCUM units
    # and some edge cases not present in the official examples.
    # This file is auto-created by parser.update_lark_ucum_grammar_file

    main_term: DIVIDE term
            | term
    ?term: term OPERATOR component
            | component
    ?component: annotatable ANNOTATION
            | annotatable
    ?annotatable: simple_unit EXPONENT
            | ANNOTATION
            | simple_unit
            | "(" main_term ")"
            | "(" term ")"
            | "(" component ")"
    simple_unit: UNIT_METRIC
            | PREFIX_SHORT UNIT_METRIC
            | PREFIX_LONG UNIT_METRIC
            | UNIT_NON_METRIC
            | FACTOR

    ANNOTATION: "{{" STRING "}}"
    STRING: /[!-z|~]*/  # ASCII chars 33-126 without curly braces

    OPERATOR: "." | DIVIDE
    DIVIDE: "/"

    PREFIX_SHORT: {short_prefix_atoms}
    PREFIX_LONG: {long_prefix_atoms}

    UNIT_METRIC: {metric_atoms}
    UNIT_NON_METRIC: {non_metric_atoms}

    EXPONENT : ["+"|"-"] NON_ZERO_DIGITS
    FACTOR: NON_ZERO_DIGITS
    NON_ZERO_DIGITS : /[1-9][0-9]*/  # positive integers > 0
"""


class UnitsTransformer(Transformer):
    pass


def update_lark_ucum_grammar_file(
    ucum_grammar_template: str = UCUM_GRAMMAR, grammar_file: Path | None = None
):
    """
    Update the lark grammar file with UCUM units and prefixes from ucum-essence.xml
    """
    if grammar_file is None:
        # case sensitive ucum_grammar.lark is the default
        ucumvert.xml_util.CODE_ATTRIB = "Code"
        grammar_file = Path(__file__).resolve().parent / "ucum_grammar.lark"

    prefixes = get_prefixes()
    short_prefixes = [i for i in prefixes if len(i) == 1]
    long_prefixes = [i for i in prefixes if len(i) > 1]
    short_prefix_atoms = " |".join(f'"{i}"' for i in short_prefixes)
    long_prefix_atoms = " |".join(f'"{i}"' for i in long_prefixes)
    metric_atoms = " |".join(f'"{i}"' for i in (get_base_units() + get_metric_units()))
    non_metric_atoms = " |".join(f'"{i}"' for i in get_non_metric_units())

    ucum_grammar = ucum_grammar_template.format(
        short_prefix_atoms=short_prefix_atoms,
        long_prefix_atoms=long_prefix_atoms,
        metric_atoms=metric_atoms,
        non_metric_atoms=non_metric_atoms,
    )
    # wrap too long lines in ucum_grammar to linewidth of 78
    wrapped = []
    for line in textwrap.dedent(ucum_grammar).strip().splitlines():
        dline = textwrap.fill(
            line,
            width=78,
            subsequent_indent=" " * 8,
            break_long_words=False,
            break_on_hyphens=False,
        )
        wrapped.append(dline)

    with grammar_file.open("w") as f:
        f.write("\n".join(wrapped))
        f.write("\n")  # newline at end of file
    logger.info("Updated grammar written to '%s'.", grammar_file)


def get_ucum_parser(grammar_file=None):
    if grammar_file is None:
        grammar_file = Path(__file__).resolve().parent / "ucum_grammar.lark"
    with grammar_file.open("r", encoding="utf8") as f:
        ucum_grammar = f.read()
    return Lark(ucum_grammar, start="main_term", strict=True)
