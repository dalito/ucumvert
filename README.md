[![CI - main](https://github.com/dalito/ucumvert/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/dalito/ucumvert/actions/workflows/ci.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/ucumvert)](https://pypi.org/project/ucumvert)

# Easier access to UCUM from Python

> **Feedback welcome!**
> Currently only the conversion direction from UCM to pint is supported.
> Please review the definitions before you trust them.
> While we have many tests in place and reviewed the mappings carefully, bugs may still be present.

[UCUM](https://ucum.org/) (Unified Code for Units of Measure) is a code system intended to cover all units of measures.
It provides a formalism to express units in an unambiguous way suitable for electronic communication.
Note that UCUM does not provide a canonical representation, e.g. `m/s` and `m.s-1` are expressing the same unit in two ways.

**ucumvert** is a pip-installable Python package. Features:

- Parser for UCUM unit strings that implements the full grammar.
- Converter for creating [pint](https://pypi.org/project/pint/) units from UCUM unit strings.
- A pint unit definition file [pint_ucum_defs.txt](https://github.com/dalito/ucumvert/blob/main/src/ucumvert/pint_ucum_defs.txt) that extends pint´s default units with UCUM units. All UCUM units from the new version 2.2 of the specification (June 2024) are included.

**ucumvert** generates the UCUM grammar by filling a template with unit codes, prefixes etc. from the official [ucum-essence.xml](https://github.com/ucum-org/ucum/blob/main/ucum-essence.xml) file (a copy is included in this repo).
So updating the parser for new UCUM releases is straight forward.
The parser is built with the great [lark](https://pypi.org/project/lark/) parser toolkit.
The generated lark grammar file for case-sensitive UCUM codes is included in the repository, see [ucum_grammar.lark](https://github.com/dalito/ucumvert/blob/main/src/ucumvert/ucum_grammar.lark).

Some of the UCUM unit atoms are invalid unit names in pint, for example `cal_[15]`, `m[H2O]`, `10*`, `[in_i'H2O]`.
For all of them we define mappings to valid pint unit names in [ucum_pint.py](https://github.com/dalito/ucumvert/blob/main/src/ucumvert/ucum_pint.py), e.g. `{"cal_[15]": "cal_15"}`.

## Install

ucumvert is available as Python package from [PyPi](https://pypi.org/project/ucumvert) and can be pip-installed in the usual way.

```bash
pip install ucumvert
```

To install the most recent code from git in developer mode including creation of a virtual environment use:

Linux

```bash
git clone https://github.com/dalito/ucumvert.git
cd ucumvert
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .[dev]
```

Windows

```bash
git clone https://github.com/dalito/ucumvert.git
cd ucumvert
py -m venv .venv
.venv\Scripts\activate.bat
py -m pip install --upgrade pip
pip install -e .[dev]
```

Optionally you can visualize the parse trees with [Graphviz](https://www.graphviz.org/) as shown below. It requires the additional package [pydot](https://pypi.org/project/pydot/); install by running `pip install pydot`.

## Demo

We provide a basic command line interface.

```cmd
(.venv) $ ucumvert
```

It has an interactive mode to test parsing UCUM codes:

```cmd
(.venv) $ ucumvert -i
Enter UCUM unit code to parse, or 'q' to quit.
> m/s2.kg
Created visualization of parse tree (parse_tree.png).
main_term
  term
    term
      simple_unit       m
      /
      annotatable
        simple_unit     s
        2
    .
    simple_unit
      k
      g
--> Pint <Quantity(1.0, 'kilogram * meter / second ** 2')>
> q
```

So the intermediate result is a tree which is then traversed to convert the elements to pint quantities (or pint-compatible strings):

![parse tree kg*m*s**-2](https://raw.githubusercontent.com/dalito/ucumvert/main/parse_tree.png)

The package includes an UCUM-aware pint UnitRegistry which loads all definitions for UCUM units on instantiation.
It comes with an additional method `from_ucum` to convert UCUM codes to pint.

```python
>>> from ucumvert import PintUcumRegistry
>>> ureg = PintUcumRegistry()
>>> ureg.from_ucum("m/s2.kg")
<Quantity(1.0, 'kilogram * meter / second ** 2')>
>>> ureg.from_ucum("m[H2O]{35Cel}")  # UCUM code with annotation
<Quantity(1, 'm_H2O')>
>>> _.to("mbar")
<Quantity(98.0665, 'millibar')>
>>> ureg("degC")   # a standard pint unit
<Quantity(1, 'degree_Celsius')>
>>>
```

## Tests

The unit tests include parsing and converting all common UCUM unit codes from the official repo. Run the test suite by:

```bash
pytest
```

The common UCUM unit codes are available only in binary form (xlsx, docs, pdf).
Here we keep a copy in tsv-format `ucum_examples.tsv`.
To (re)generate this tsv-file from the official xlsx-file in the [UCUM repository](https://github.com/ucum-org/ucum/tree/main/common-units) run

```bash
pip install openpyxl
python src/ucumvert/vendor/get_ucum_example_as_tsv.py
```

## Useful links

- UCUM [online-validator](https://ucum.nlm.nih.gov/ucum-lhc/demo.html)
- Issue in pint that motivated this work: [To what extent is pint compatible with UCUM?](https://github.com/hgrecco/pint/issues/1769)

## License

The code in this repository is distributed under MIT license with the exception of the `ucum-*.*` files in the directory `src/ucumvert/vendor`
that fall under the [UCUM Copyright Notice and License](https://github.com/ucum-org/ucum/blob/main/LICENSE.md) (Version 1.0).
We consider **ucumvert** according to §1.3 not as "Derivative Works" of UCUM because **ucumvert** only *"interoperates with an unmodified instance of the Work"*.
