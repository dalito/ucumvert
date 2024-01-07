from lark.exceptions import UnexpectedInput, VisitError

from ucumvert.parser import UnitsTransformer, make_parse_tree_png, parse_and_transform


def main():
    print("Enter UCUM units to parse, or 'q' to quit.")
    while True:
        s = input("> ")
        if s in "qQ":
            break
        try:
            make_parse_tree_png(s, filename="parse_tree.png")
            print("Created visualization of parse tree (parse_tree.png).")
        except UnexpectedInput as e:
            print(e)
            continue
        try:
            parse_and_transform(UnitsTransformer, s)
        except (VisitError, ValueError) as e:
            print(e)
            continue


def run_cli_app():
    main()


if __name__ == "__main__":
    main()
