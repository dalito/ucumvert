# UCUM syntax in the Backus-Naur Form from https://ucum.org/ucum#section-Syntax-Rules
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

from lark import Lark, Transformer

from ucumvert.xml_util import (
    get_base_units,
    get_metric_units,
    get_non_metric_units,
    get_prefixes,
)

# Since we use string.format below to inject prefixes etc. into UCUM_GRAMMAR
# the curly braces require escaping: "{{".format() -> "{"
UCUM_GRAMMAR = """
        simple_unit: METRIC
                | PREFIX? METRIC
                | NON_METRIC
        annotatable: simple_unit EXPONENT
                | simple_unit
        component: annotatable annotation
                | annotatable
                | annotation
                | FACTOR
                | "(" term ")"
        term: term OPERATOR component
                | component
        start: DIVIDE term
                | term
        annotation: "{{" STRING "}}"
        STRING: /[^{{}}]+/
        OPERATOR: "." | DIVIDE
        DIVIDE: "/"
        PREFIX: {prefix_rule}
        METRIC: {metric_rule}
        NON_METRIC: {non_metric_rule}

        %import common.SIGNED_INT   -> EXPONENT
        %import common.INT          -> FACTOR
"""


class UnitsTransformer(Transformer):
    def FACTOR(self, args):
        return args[0]

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

    def annotation(self, args):
        return {
            "annotation": str(args[0]),
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


def lark_parser(data):
    prefix_rule = " | ".join(f'"{i}"' for i in get_prefixes())
    metric_rule = " | ".join(f'"{i}"' for i in (get_base_units() + get_metric_units()))
    non_metric_rule = " | ".join(f'"{i}"' for i in get_non_metric_units())

    ucum_grammar = UCUM_GRAMMAR.format(
        prefix_rule=prefix_rule,
        metric_rule=metric_rule,
        non_metric_rule=non_metric_rule,
    )
    ucum_parser = Lark(ucum_grammar)

    # TODO separate parser creation (above) from parsing (below)

    print(f'\nParsing ucum unit "{data}"')
    parsed_data = ucum_parser.parse(data)
    # print(parsed_data.pretty())
    result = UnitsTransformer().transform(parsed_data)
    print("Result:", result)
    return result
