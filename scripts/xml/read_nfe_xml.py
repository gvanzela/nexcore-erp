# scripts/xml/read_nfe_xml.py

from xml.etree import ElementTree as ET


def read_nfe_xml(path: str):
    """
    Read a Brazilian NF-e XML file and extract basic product information.

    IMPORTANT:
    - This function DOES NOT persist anything.
    - It only parses and returns raw data.
    - This is intentional: we validate the real XML structure first.
    """

    # ---------------------------------------------------------
    # Parse XML file into a tree structure
    # ---------------------------------------------------------
    tree = ET.parse(path)
    root = tree.getroot()

    # ---------------------------------------------------------
    # NF-e uses XML namespaces.
    # Without this, ElementTree will not find any tags.
    # ---------------------------------------------------------
    ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

    items = []

    # ---------------------------------------------------------
    # Each <det> node represents ONE item in the invoice
    # ---------------------------------------------------------
    for det in root.findall(".//nfe:det", ns):
        prod = det.find("nfe:prod", ns)

        if prod is None:
            continue

        # -----------------------------------------------------
        # Extract minimal fields we care about for MVP
        # -----------------------------------------------------
        item = {
            # EAN / barcode used to match products
            "ean": prod.findtext("nfe:cEAN", default=None, namespaces=ns),

            # Quantity sold (commercial unit)
            "quantity": prod.findtext("nfe:qCom", default="0", namespaces=ns),

            # Unit price from supplier
            "unit_price": prod.findtext("nfe:vUnCom", default="0", namespaces=ns),

            # Product description from XML
            "description": prod.findtext("nfe:xProd", default="", namespaces=ns),
        }

        items.append(item)

    return items


if __name__ == "__main__":
    """
    Manual test runner.

    Run this file directly to see how the XML is parsed.
    No database, no API, no side effects.
    """

    xml_path = r"C:\Users\gabri\Downloads\35260104771370000345550010006486301879500382.xml"  # replace with your real XML path
    data = read_nfe_xml(xml_path)

    for item in data:
        print(item)
