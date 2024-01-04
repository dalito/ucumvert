# Easier access to UCUM from Python

> **This is work in progress.** The lark grammar to parse UCUM codes is done.
The transformer works but can probably be simplified. 
Conversion to pint is very basic and only correct for simple UCUM codes.
The converter must be completed to use the full information from the transformer. 
The unit mappings ucum-to-pint must be extended. 
For  units missing in pint we may need to extend the registry with new aliases or new units.

[UCUM](https://ucum.org/) (Unified Code for Units of Measure) is a code system intended to cover all units of measures.
It provides a formalism to express units in an unambiguous way suitable for electronic communication.
Note that UCUM does non provide a canonical representation, e.g. `m/s` and `m.s-1` are expressing the same unit in two ways.

**ucumvert** is a pip-installable Python package. Features:

- Converter for creating [pint](https://pypi.org/project/pint/) units from UCUM unit strings
- Parser for UCUM unit strings

**ucumvert** stores the UCUM grammar in a template that is dynamically filled with unit codes, prefixes etc. by parsing the official [ucum-essence.xml](https://github.com/ucum-org/ucum/blob/main/ucum-essence.xml) file (a copy is included in this repo).
So updating the parser for new UCUM releases is quasi automatic.
The parser is built with the great [lark](https://pypi.org/project/lark/) parser toolkit.

## Install

Installation from git in developer mode including creation of virtual environment:

Linux
```
git clone https://github.com/dalito/ucumvert.git
cd ucumvert
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Windows
```
git clone https://github.com/dalito/ucumvert.git
cd ucumvert
py -m venv .venv
.venv\Scripts\activate.bat
pip install -e .[dev]
```

## Demo

This is just a demo to show that the code does something...

```cmd
(.venv) $ ucumvert
Enter UCUM units to parse, or 'q' to quit.
> m
Parsing ucum unit "m"
Result: [{'type': 'metric', 'unit': 'm'}]
> mm
Parsing ucum unit "mm"
Result: [{'prefix': 'm', 'type': 'metric', 'unit': 'm'}]
> q
```

So we create a dictionary from the UCUM unit code.
From this we can for example create [pint](https://pint.readthedocs.io/) units, see `ucum_pint.py` (work in progress) or try

```bash
$ python src/ucumvert/ucum_pint.py
```

## Tests

The unit tests include a test to parse all common UCUM unit codes from the official repo. To see this run

```cmd
$ pytest
```

The common UCUM unit codes are available only in binary form (xlsx, docs, pdf).
Here we keep a copy in tsv-format `ucum_examples.tsv`.
To (re)generate this tsv-file from the official xlsx-file in the [UCUM repository](https://github.com/ucum-org/ucum/tree/main/common-units) run

```cmd
$ pip install openpyxl
$ python src/src/ucumvert/vendor/get_ucum_example_as_tsv.py
```

## Useful links

- UCUM [online-validator](https://ucum.nlm.nih.gov/ucum-lhc/demo.html)

## License

The code in this repository is distributed under MIT license with the exception of the `ucum-*.*` files in the directory `src/ucumvert/vendor` which fall under the [UCUM Copyright Notice and License](https://github.com/ucum-org/ucum/blob/main/LICENSE.md) (Version 1.0).
We consider **ucrumvert** according to §1.3 not as "Derivative Works" of UCUM because **ucrumvert** only *"interoperates with an unmodified instance of the Work"*.
