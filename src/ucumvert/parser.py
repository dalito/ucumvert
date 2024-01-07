from lark import Lark, Transformer, tree

from ucumvert.xml_util import (
    get_base_units,
    get_metric_units,
    get_non_metric_units,
    get_prefixes,
)

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

# The following commented-out lark grammar closely follows the specification
#    above but fails for "100/{cells}" and "g/(8.h){shift}". Both are valid
#    UCUM strings from the official examples.
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
# - to fix "100/{cells}" issue, we moved FACTOR from component to the simple_unit rule
# - to fix "(8.h){shift}" issue, we moved "(" term ")" from component to the annotatable rule
# - Don't allow "0" as EXPONENT or FACTOR, see https://github.com/ucum-org/ucum/issues/121

# - Distinguish short prefixes (1 char) form long ones to handle parsing of "dar" as deci-are
#   instead of deca-r which does not exist.

UCUM_GRAMMAR = """
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
    simple_unit: METRIC
            | SHORT_PREFIX METRIC
            | LONG_PREFIX METRIC
            | NON_METRIC
            | FACTOR

    ANNOTATION: "{{" STRING "}}"
    STRING: /[\x21-\x7a|~]*/        // ASCII chars 33-126 without curly braces
    OPERATOR: "." | DIVIDE
    DIVIDE: "/"
    SHORT_PREFIX: {short_prefix_atoms}
    LONG_PREFIX: {long_prefix_atoms}
    METRIC: {metric_atoms}
    NON_METRIC: {non_metric_atoms}

    EXPONENT : ["+"|"-"] NON_ZERO_DIGITS
    FACTOR: NON_ZERO_DIGITS
    NON_ZERO_DIGITS : /[1-9][0-9]*/   // positive integers > 0
"""


class UnitsTransformer(Transformer):
    pass


class xUnitsTransformer(Transformer):
    def FACTOR(self, args):
        return {
            "factor": int(args),
        }

    def EXPONENT(self, args):
        if len(args) == 1:
            return {
                "exponent": int(args[0]),
            }
        if len(args) == 2:
            return {
                "exponent": int("".join(args)),
            }
        return None

    def start(self, args):
        # print("DBGs>", repr(args), len(args))
        if len(args) == 1:
            return [args[0]]
        if len(args) == 2:
            if isinstance(args[1], dict):
                return [{**args[0], **args[1]}]
            return [{**args[0], **args[1][0]}] + args[1][1:]
        return None

    def term(self, args):
        # print("DBGt>", repr(args), len(args))
        if len(args) == 1:
            return args[0]
        if len(args) == 3:
            if isinstance(args[0], dict):
                if "factor" in args[0] and len(args[0]) == 1:
                    return {**args[0], **args[1], **args[2]}
                return [args[0], {**args[1], **args[2]}]
            return args[0] + [{**args[1], **args[2]}]
        return None

    def component(self, args):
        if len(args) == 1:
            return args[0]
        if len(args) == 2:
            return {**args[0], **args[1]}
        return None

    def simple_unit(self, args):
        if len(args) == 1:
            return args[0]
        if len(args) == 2:
            return {**args[0], **args[1]}
        return None

    def annotatable(self, args):
        if len(args) == 1:
            return args[0]
        if len(args) == 2:
            return {**args[0], **args[1]}
        return None

    def ANNOTATION(self, args):
        return {
            "annotation": str(args),
        }

    def OPERATOR(self, args):
        return {
            "operator": args[0],
        }

    def DIVIDE(self, args):
        return {
            "operator": args[0],
        }

    def PREFIX(self, args):
        if args == "da":
            return {
                "prefix": args[0:2],
            }
        return {
            "prefix": args[0],
        }

    def METRIC(self, args):
        return {
            "type": "metric",
            "unit": args[:],
        }

    def NON_METRIC(self, args):
        return {
            "type": "non_metric",
            "unit": args[:],
        }


def ucum_parser(ucum_grammar_template=UCUM_GRAMMAR):
    prefixes = get_prefixes()
    short_prefixes = [i for i in prefixes if len(i) == 1]
    long_prefixes = [i for i in prefixes if len(i) > 1]
    short_prefix_atoms = " | ".join(f'"{i}"' for i in short_prefixes)
    long_prefix_atoms = " | ".join(f'"{i}"' for i in long_prefixes)
    metric_atoms = " | ".join(f'"{i}"' for i in (get_base_units() + get_metric_units()))
    non_metric_atoms = " | ".join(f'"{i}"' for i in get_non_metric_units())

    ucum_grammar = ucum_grammar_template.format(
        short_prefix_atoms = short_prefix_atoms,
        long_prefix_atoms = long_prefix_atoms,
        metric_atoms = metric_atoms,
        non_metric_atoms = non_metric_atoms,
    )
    return Lark(ucum_grammar, start="main_term", strict=True)


def parse_and_transform(transformer_cls, data):
    print(f'Tree of parsed ucum unit "{data}":')
    parsed_data = ucum_parser().parse(data)
    print(parsed_data.pretty())
    result = transformer_cls().transform(parsed_data)
    # print("Result:", result)
    return result


def make_parse_tree_png(data, filename="parse_tree_unit.png"):
    parsed_data = ucum_parser().parse(data)
    tree.pydot__tree_to_png(parsed_data, filename)
