# Vendored files

This directory contain copies of files from the [UCUM repository](https://github.com/ucum-org/ucum) to enable running the code without internet access. The copied files fall under the [UCUM Copyright Notice and License](https://github.com/ucum-org/ucum/blob/main/LICENSE.md) (Version 1.0).

* `ucum-essence.xml` - Version 2.2 (revision date: 2024-06-17).
  * Used to build the terminals of the lark parser.
* `ucum_examples.tsv` - Extracted from [TableOfExampleUcumCodesForElectronicMessaging.xlsx](https://github.com/ucum-org/ucum/blob/main/common-units/TableOfExampleUcumCodesForElectronicMessaging.xlsx), Version 1.5, released 06/2020
  * Used in unit tests. The tsv was created with the script `get_ucum_examples_as_tsv.py`.

There are minor inconsistencies in these files. For example, the unit  "Torr" is included as a valid UCUM code example but not defined in `ucum-essence.xml`. Also others have observed [this](https://lhncbc.github.io/ucum-lhc/UcumEssenceModifications.html).
