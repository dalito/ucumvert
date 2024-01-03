# Easier access to UCUM from Python

[UCUM](https://ucum.org/) (Unified Code for Units of Measure) is a code system intended to cover all units of measures. It provides a formalism to express units in an unambiguous way suitable for electronic communication. Note that ucum does non provide a canonical representation, e.g. `m/s` and `m.s-1` are expressing the same unit in two ways.

**ucumvert** is a pip-installable Python package. Features:

- Converter for creating [pint](https://pypi.org/project/pint/) units from ucum unit strings
- Parser for ucum unit strings

The parser is build with the great [lark](https://pypi.org/project/lark/) parser toolkit.

## Install

Installation from git in developer mode including creation of virtual environment:

Windows
```
git clone https://github.com/dalito/ucumvert.git
cd ucumvert
py -m venv .venv
.venv\Scripts\activate.bat
pip install -e .[dev]
```

Linux
```
git clone https://github.com/dalito/ucumvert.git
cd ucumvert
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```
