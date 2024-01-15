import argparse
import logging
import sys
import textwrap
from pathlib import Path

from lark.exceptions import LarkError, UnexpectedInput, VisitError

from ucumvert import __version__, setup_logging
from ucumvert.parser import (
    get_ucum_parser,
    make_parse_tree_png,
    update_lark_ucum_grammar_file,
)
from ucumvert.ucum_pint import UcumToPintTransformer, find_matching_pint_definitions

try:
    import pydot  # noqa: F401

    has_pydot = True
except ImportError:
    has_pydot = False

logger = logging.getLogger(__name__)


def interactive():
    print("Enter UCUM unit code to parse, or 'q' to quit.")
    if not has_pydot:
        print("Package pydot not installed, skipping parse-tree image generation.")

    ucum_parser = get_ucum_parser()

    while True:
        ucum_code = input("> ")
        if ucum_code in "qQ":
            break
        try:
            if has_pydot:
                parsed_data = make_parse_tree_png(
                    ucum_code, filename="parse_tree.png", parser=ucum_parser
                )
                print("Created visualization of parse tree (parse_tree.png).")
            else:
                parsed_data = ucum_parser.parse(ucum_code)
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


# ===  argparse-cli-related code  ===


class DecentFormatter(argparse.HelpFormatter):
    """
    An argparse formatter that preserves newlines & keeps indentation.
    """

    def _fill_text(self, text, width, indent):
        """
        Reformat text while keeping newlines for lines shorter than width.
        """
        lines = []
        for line in textwrap.indent(textwrap.dedent(text), indent).splitlines():
            lines.append(  # noqa: PERF401
                textwrap.fill(line, width, subsequent_indent=indent)
            )
        return "\n".join(lines)

    def _split_lines(self, text, width):
        """
        Conserve indentation in help/description lines when splitting long lines.
        """
        lines = []
        for line in textwrap.dedent(text).splitlines():
            if not line.strip():
                continue
            indent = " " * (len(line) - len(line.lstrip()))
            lines.extend(
                textwrap.fill(line, width, subsequent_indent=indent).splitlines()
            )
        return lines


def root_cmds(args):
    if args.version:  # pragma: no cover
        print(f"ucumvert {__version__}")
    if args.interactive:
        interactive()
    if args.mapping_report:
        find_matching_pint_definitions(report_file=args.mapping_report)
    if args.grammar_update:
        grammar_file = Path(__file__).resolve().parent / "ucum_grammar.lark"
        update_lark_ucum_grammar_file(grammar_file=grammar_file)


def create_root_parser():
    parser = argparse.ArgumentParser(
        prog="ucumvert",
        description=("Simple CLI for ucumvert."),
        allow_abbrev=False,
        formatter_class=DecentFormatter,
    )
    parser.add_argument(
        "-V",
        "--version",
        help="The version of ucumvert.",
        action="store_true",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        help="Interactive mode to explore parsing of UCUM unit codes.",
        action="store_true",
    )
    parser.add_argument(
        "-g",
        "--grammar_update",
        help=(
            "Recreate grammar file 'ucum_grammar.lark' with UCUM atoms "
            "extracted from ucum-essence.xml."
        ),
        action="store_true",
    )
    parser.add_argument(
        "-m",
        "--mapping_report",
        help=(
            "Write a report of mappings between UCUM unit atoms and pint "
            "definitions to the given file. Default is to write to "
            "'pint_ucum_defs_mapping_report.txt' in the current directory."
        ),
        type=Path,
        metavar=("FILE"),
        nargs="?",  # make file an optional argument
        const=Path("pint_ucum_defs_mapping_report.txt"),  # default value
    )
    parser.set_defaults(func=root_cmds)
    return parser


def main_cli(raw_args=None):
    """Setup CLI app and run commands based on arguments."""
    # Create root parser for cli app
    parser = create_root_parser()

    if not raw_args:
        parser.print_help()
        return

    # Parse the command-line arguments
    #   parse_args will call sys.exit(2) if invalid commands are given.
    args = parser.parse_args(raw_args)
    setup_logging(loglevel=logging.INFO)
    args.func(args)


def run_cli_app(raw_args=None):
    """Entry point for running the cli app."""
    if raw_args is None:
        raw_args = sys.argv[1:]
    try:
        main_cli(raw_args)
    except LarkError:
        logger.exception("Terminating with ucumvert error.")
        sys.exit(1)
    except Exception:
        logger.exception("Unexpected error.")
        sys.exit(3)  # value 2 is used by argparse for invalid args.


if __name__ == "__main__":
    run_cli_app(sys.argv[1:])
