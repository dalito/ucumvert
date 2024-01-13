from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

UCUM_ESSENCE_FILE = Path(__file__).parent.absolute() / "vendor" / "ucum-essence.xml"

# set to "Code" for case-sensitive and to "CODE" for case-insensitive units
CODE_ATTRIB = "Code"

tree = ElementTree.parse(UCUM_ESSENCE_FILE)  # noqa: S314
root = tree.getroot()


@dataclass
class UcumUnitDefinition:
    code_cs: str  # case-sensitive code
    code_ci: str  # case-insensitive code
    is_metric: bool
    is_special: bool
    is_arbitrary: bool
    class_: str
    name: str
    print_symbol: str
    property_: str
    defining_unit: str
    conversion_factor: float = float("Nan")


def get_prefixes() -> list:
    prefix_path = ".//{*}prefix[@" + CODE_ATTRIB + "]"
    return [p.attrib[CODE_ATTRIB] for p in root.findall(prefix_path)]


def get_units() -> list:
    units = []
    for unit in root.findall(".//{*}unit[@" + CODE_ATTRIB + "]"):
        cs = unit.attrib[CODE_ATTRIB]
        units.append(cs)
    return units


def get_metric_units() -> list:
    xpath = ".//{*}unit[@" + CODE_ATTRIB + "][@isMetric='yes']"
    return [p.attrib[CODE_ATTRIB] for p in root.findall(xpath)]


def get_non_metric_units() -> list:
    xpath = ".//{*}unit[@" + CODE_ATTRIB + "][@isMetric='no']"
    return [p.attrib[CODE_ATTRIB] for p in root.findall(xpath)]


def get_base_units() -> list:
    xpath = ".//{*}base-unit[@" + CODE_ATTRIB + "]"
    return [p.attrib[CODE_ATTRIB] for p in root.findall(xpath)]


def get_units_with_full_definition() -> list:
    data = []
    for el in root.findall(".//{*}unit[@" + CODE_ATTRIB + "]"):
        el_data = dict(el.items())
        # rename some keys
        el_data["code_ci"] = el_data.pop("CODE", "")
        el_data["code_cs"] = el_data.pop("Code", "")
        el_data["is_metric"] = el_data.pop("isMetric", "") == "yes"
        el_data["is_special"] = el_data.pop("isSpecial", "") == "yes"
        el_data["is_arbitrary"] = el_data.pop("isArbitrary", "") == "yes"
        el_data["class_"] = el_data.pop("class", "")

        # iterate over child elements of unit
        for child in el:
            childname = child.tag.rsplit("}", 1)[-1]
            if "Unit" in child.attrib:  # element "value" with conversion info
                el_data["defining_unit"] = child.attrib["Unit"]
                el_data["conversion_factor"] = child.attrib.get("value", float("Nan"))
                # The attribute "value" is sometimes in an element "function" one level deeper.
                for el_fcn in child:
                    if "value" in el_fcn.attrib:
                        el_data["conversion_factor"] = el_fcn.attrib.get("value")
                        break
            else:  # elements: Name, printSymbol, ...
                el_data[childname] = child.text

        el_data["print_symbol"] = el_data.pop("printSymbol", "")
        el_data["property_"] = el_data.pop("property", "")
        data.append(UcumUnitDefinition(**el_data))

    return data


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

    units_data = get_units_with_full_definition()
    print(f"Units in dataclasses {len(units_data)}")
