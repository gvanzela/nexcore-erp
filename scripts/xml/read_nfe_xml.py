# scripts/xml/read_nfe_xml.py
from xml.etree import ElementTree as ET

def read_nfe_xml(path: str):
    """
    Read a Brazilian NF-e XML file and extract minimal purchase data.

    - No persistence
    - Just parsing
    """

    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

    # ---------------------------------------------------------
    # Header (purchase-level data)
    # ---------------------------------------------------------
    inf_nfe = root.find(".//nfe:infNFe", ns)
    source_id = inf_nfe.attrib.get("Id") if inf_nfe is not None else None

    emit = root.find(".//nfe:emit", ns)
    supplier_document = (
        emit.findtext("nfe:CNPJ", namespaces=ns)
        or emit.findtext("nfe:CPF", namespaces=ns)
    )

    ide = root.find(".//nfe:ide", ns)
    issue_date = ide.findtext("nfe:dhEmi", namespaces=ns)

    total_amount = root.findtext(".//nfe:ICMSTot/nfe:vNF", namespaces=ns)

    items = []

    # ---------------------------------------------------------
    # Items
    # ---------------------------------------------------------
    for det in root.findall(".//nfe:det", ns):
        prod = det.find("nfe:prod", ns)
        if prod is None:
            continue

        items.append(
            {
                "ean": prod.findtext("nfe:cEAN", default=None, namespaces=ns),
                "manufacturer_code": prod.findtext("nfe:cProd", default=None, namespaces=ns),
                "unit": prod.findtext("nfe:uCom", default="", namespaces=ns),
                "quantity": prod.findtext("nfe:qCom", default="0", namespaces=ns),
                "unit_price": prod.findtext("nfe:vUnCom", default="0", namespaces=ns),
                "description": prod.findtext("nfe:xProd", default="", namespaces=ns),
            }
        )

    return {
        "source_id": source_id,                 # NF-e key
        "supplier_document": supplier_document,
        "issue_date": issue_date,
        "total_amount": total_amount,
        "items": items,
    }