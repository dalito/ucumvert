from pathlib import Path
from xml.etree import ElementTree

UCUM_ESSENCE_FILE = Path(__file__).parent.absolute() / "vendor" / "ucum-essence.xml"

tree = ElementTree.parse(UCUM_ESSENCE_FILE)  # noqa: S314
root = tree.getroot()

# set to "Code" for case-sensitive and to "CODE" for case-insensitive units
CODE_ATTRIB = "Code"


def get_prefixes():
    prefix_path = ".//{*}prefix[@" + CODE_ATTRIB + "]"
    return [p.attrib[CODE_ATTRIB] for p in root.findall(prefix_path)]


def get_units():
    units = []
    for unit in root.findall(".//{*}unit[@" + CODE_ATTRIB + "]"):
        cs = unit.attrib[CODE_ATTRIB]
        units.append(cs)
    return units


def get_metric_units():
    xpath = ".//{*}unit[@" + CODE_ATTRIB + "][@isMetric='yes']"
    return [p.attrib[CODE_ATTRIB] for p in root.findall(xpath)]


def get_non_metric_units():
    xpath = ".//{*}unit[@" + CODE_ATTRIB + "][@isMetric='no']"
    return [p.attrib[CODE_ATTRIB] for p in root.findall(xpath)]


def get_base_units():
    xpath = ".//{*}base-unit[@" + CODE_ATTRIB + "]"
    return [p.attrib[CODE_ATTRIB] for p in root.findall(xpath)]


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
