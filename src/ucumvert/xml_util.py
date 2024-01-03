from pathlib import Path
from xml.etree import ElementTree

UCUM_ESSENCE_FILE = Path(__file__).parent.absolute() / "vendor" / "ucum-essence.xml"

tree = ElementTree.parse(UCUM_ESSENCE_FILE)  # noqa: S314
root = tree.getroot()


def get_prefixes(case_sensitive=True):
    # prefixes = []
    # for prefix in root.findall(".//{*}prefix"):
    #     cs = prefix.attrib["Code"]  # case sensitive code
    #     ci = prefix.attrib["CODE"]  # case insensitive code
    #     prefixes.append(cs)
    #     print(cs, ci)
    #     for detail in prefix:
    #         if detail.attrib:
    #             print("->", detail.text, detail.attrib)
    #         else:
    #             print("->", detail.text)

    code = "Code" if case_sensitive else "CODE"
    prefix_path = ".//{*}prefix[@" + code + "]"
    return [p.attrib[code] for p in root.findall(prefix_path)]


def get_units(case_sensitive=True):
    code = "Code" if case_sensitive else "CODE"

    units = []
    for unit in root.findall(".//{*}unit[@" + code + "]"):
        cs = unit.attrib[code]
        units.append(cs)
        # print(f"{unit.tag.split('}')[-1]}: {cs}", unit.attrib)
        # for detail in unit:
        #     if detail.attrib:
        #         print("->", detail.tag.split("}")[-1], detail.text, detail.attrib)
        #     else:
        #         print("->", detail.tag.split("}")[-1], detail.text)

    return units


# optional attributes on some units: 'isArbitrary': 'yes' , 'isSpecial': 'yes'


def get_metric_units(case_sensitive=True):
    code = "Code" if case_sensitive else "CODE"
    xpath = ".//{*}unit[@" + code + "][@isMetric='yes']"
    return [p.attrib[code] for p in root.findall(xpath)]


def get_non_metric_units(case_sensitive=True):
    code = "Code" if case_sensitive else "CODE"
    xpath = ".//{*}unit[@" + code + "][@isMetric='no']"
    return [p.attrib[code] for p in root.findall(xpath)]


def get_base_units(case_sensitive=True):
    code = "Code" if case_sensitive else "CODE"
    xpath = ".//{*}base-unit[@" + code + "]"
    return [p.attrib[code] for p in root.findall(xpath)]


if __name__ == "__main__":
    print(get_units())
    prefixes = get_prefixes()
    print(f"\nprefixes ({len(prefixes)})")
    print(prefixes)

    metric_units = get_metric_units()
    print(f"\nmetric_units ({len(metric_units)})")
    print(metric_units)

    base_units = get_base_units()
    print(f"\nbase_units ({len(base_units)})")
    print(base_units)

    non_metric_units = get_non_metric_units()
    print(f"\nNumber of non_metric_units: {len(non_metric_units)}")
    # print(non_metric_units)

    units = get_units()
    print(f"Total number of units: {len(units)}")
