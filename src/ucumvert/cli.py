from lark.exceptions import UnexpectedInput, VisitError

from ucumvert.parser import get_ucum_parser, make_parse_tree_png
from ucumvert.ucum_pint import UcumToPintTransformer


def main():
    print("Enter UCUM unit code to parse, or 'q' to quit.")
    ucum_parser = get_ucum_parser()

    while True:
        ucum_code = input("> ")
        if ucum_code in "qQ":
            break
        try:
            parsed_data = make_parse_tree_png(
                ucum_code, filename="parse_tree.png", parser=ucum_parser
            )
            print("Created visualization of parse tree (parse_tree.png).")
            print(parsed_data.pretty())
        except UnexpectedInput as e:
            print(e)
            continue
        try:
            # parsed_data = ucum_parser.parse(data)  # parse data without visualization
            pint_quantity = UcumToPintTransformer().transform(parsed_data)
            print(f"--> Pint {pint_quantity!r}")
        except (VisitError, ValueError) as e:
            print(e)
            continue


def run_cli_app():
    main()


if __name__ == "__main__":
    main()
