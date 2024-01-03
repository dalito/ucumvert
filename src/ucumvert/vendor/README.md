# Vendored files

This directory contain copies of files from the [UCUM repository](https://github.com/ucum-org/ucum) to enable running the code without internet access.

* `ucum-essence.xml` - Version 2.1 (revision date: 2017-11-21 19:04:52 -0500)
  * Used to build the terminals of the lark parser.
* `table_of_examples.tsv` - Extracted from [TableOfExampleUcumCodesForElectronicMessaging.xlsx](https://github.com/ucum-org/ucum/blob/main/common-units/TableOfExampleUcumCodesForElectronicMessaging.xlsx), Version 1.5, released 06/2020
  * Used in unit tests. The tsv was created with the script `ucum_example_xlsx_to_tsv.py`.
