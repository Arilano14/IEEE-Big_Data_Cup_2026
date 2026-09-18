"""AuditAI BI — XBRL XML Document Parser.

Parses XBRL Instance, Schema, Calculation, and Label linkbases into
strongly-typed canonical Silver entities without altering reported financial values.
"""
from __future__ import annotations

import io
import json
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

from src.canonical.schemas import (
    CalculationRelationship,
    FinancialFact,
    LabelRelationship,
    LogicalProvenance,
    XbrlConcept,
    XbrlContext,
    XbrlUnit,
)

UUID_NAMESPACE = uuid.NAMESPACE_DNS


def _clean_concept_href(href: str) -> str:
    """Extracts concept local identifier from href locator."""
    if "#" in href:
        return href.split("#")[-1]
    return href


def _normalize_concept_qname(raw_name: str, ns_prefixes: Dict[str, str], default_prefix: str = "us-gaap") -> str:
    """Normalizes a concept identifier (e.g. us-gaap_Assets or plasma_TotalExp) into a QName."""
    if ":" in raw_name:
        return raw_name
    
    # Check if prefixed with known prefix + underscore
    for pfx in ["us-gaap", "srt", "dei", "invest", "country", "currency"]:
        if raw_name.startswith(f"{pfx}_"):
            return f"{pfx}:{raw_name[len(pfx) + 1:]}"
            
    # Check custom schema prefix
    if default_prefix and raw_name.startswith(f"{default_prefix}_"):
        return f"{default_prefix}:{raw_name[len(default_prefix) + 1:]}"

    # Fallback to splitting on first underscore
    if "_" in raw_name:
        parts = raw_name.split("_", 1)
        return f"{parts[0]}:{parts[1]}"

    return f"{default_prefix}:{raw_name}" if default_prefix else raw_name


def parse_instance_document(
    instance_xml: str,
    case_id: str,
    full_query: str = "",
) -> Tuple[List[XbrlContext], List[XbrlUnit], List[FinancialFact], Optional[str]]:
    """Extracts contexts, units, facts, and registrant CIK from Instance XML.
    
    Args:
        instance_xml: XML string of the Instance document.
        case_id: Task 3 case identifier (e.g. "DEV_000000").
        full_query: Complete raw query string for character offset computation.
        
    Returns:
        Tuple of (contexts, units, facts, cik).
    """
    if not instance_xml.strip():
        return [], [], [], None

    # 1. Build URI -> prefix mapping using iterparse
    uri_to_prefix: Dict[str, str] = {}
    try:
        for _, (prefix, uri) in ET.iterparse(io.StringIO(instance_xml), events=["start-ns"]):
            if uri:
                uri_to_prefix[uri] = prefix
    except Exception:
        pass

    try:
        root = ET.fromstring(instance_xml)
    except Exception:
        try:
            root = ET.fromstring(f"<root>{instance_xml}</root>")
        except Exception:
            return [], [], [], None

    contexts: List[XbrlContext] = []
    units: List[XbrlUnit] = []
    facts: List[FinancialFact] = []
    entity_cik: Optional[str] = None

    context_map: Dict[str, XbrlContext] = {}
    fact_locator = 0

    for elem in list(root):
        tag = elem.tag
        local_tag = tag.split("}")[-1] if "}" in tag else tag

        # --- Context Parsing ---
        if local_tag == "context":
            cid = elem.attrib.get("id", "")
            if not cid:
                continue

            cik = ""
            for id_elem in elem.iter():
                if id_elem.tag.endswith("identifier"):
                    cik = (id_elem.text or "").strip()
                    if cik and not entity_cik:
                        entity_cik = cik
                    break

            period_type = "unknown"
            start_date: Optional[str] = None
            end_date: Optional[str] = None
            instant_date: Optional[str] = None

            for p_elem in elem.iter():
                p_local = p_elem.tag.split("}")[-1]
                if p_local == "startDate":
                    start_date = (p_elem.text or "").strip()
                elif p_local == "endDate":
                    end_date = (p_elem.text or "").strip()
                elif p_local == "instant":
                    instant_date = (p_elem.text or "").strip()

            if start_date and end_date:
                period_type = "duration"
            elif instant_date:
                period_type = "instant"

            # Dimensions parsing
            dims: Dict[str, str] = {}
            for dim_elem in elem.iter():
                if dim_elem.tag.endswith("explicitMember"):
                    dim_axis = dim_elem.attrib.get("dimension", "")
                    dim_val = (dim_elem.text or "").strip()
                    if dim_axis:
                        dims[dim_axis] = dim_val

            dims_json = json.dumps(dims, sort_keys=True) if dims else None
            context_key = str(uuid.uuid5(UUID_NAMESPACE, f"{case_id}:context:{cid}"))

            ctx = XbrlContext(
                context_key=context_key,
                case_id=case_id,
                context_id=cid,
                cik=cik or (entity_cik or ""),
                period_type=period_type,
                start_date=start_date,
                end_date=end_date,
                instant_date=instant_date,
                dimensions_json=dims_json,
            )
            contexts.append(ctx)
            context_map[cid] = ctx

        # --- Unit Parsing ---
        elif local_tag == "unit":
            uid = elem.attrib.get("id", "")
            if not uid:
                continue

            measure_text = ""
            for m_elem in elem.iter():
                if m_elem.tag.endswith("measure"):
                    measure_text = (m_elem.text or "").strip()
                    break

            # Categorize unit type
            unit_type = "other"
            meas_lower = measure_text.lower()
            if "iso4217:" in meas_lower or "usd" in meas_lower or "eur" in meas_lower:
                unit_type = "currency"
            elif "shares" in meas_lower:
                unit_type = "shares"
            elif "pure" in meas_lower:
                unit_type = "rate"

            unit_key = str(uuid.uuid5(UUID_NAMESPACE, f"{case_id}:unit:{uid}"))
            x_unit = XbrlUnit(
                unit_key=unit_key,
                case_id=case_id,
                unit_id=uid,
                measure=measure_text,
                unit_type=unit_type,
            )
            units.append(x_unit)

        # --- Fact Parsing ---
        elif "contextRef" in elem.attrib:
            fact_locator += 1
            cid = elem.attrib.get("contextRef", "")
            uid = elem.attrib.get("unitRef")
            decimals = elem.attrib.get("decimals")
            scale_attr = elem.attrib.get("scale")
            scale: Optional[int] = int(scale_attr) if scale_attr and scale_attr.lstrip("-").isdigit() else None

            # Resolve concept QName
            if tag.startswith("{"):
                uri, local = tag[1:].split("}")
                pfx = uri_to_prefix.get(uri, "")
                concept_qname = f"{pfx}:{local}" if pfx else local
            else:
                concept_qname = tag

            # Fact value extraction
            is_nil = elem.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}nil", "false").lower() == "true"
            raw_text = elem.text
            raw_value = raw_text.strip() if raw_text is not None else None

            if raw_value is None or raw_value == "":
                is_nil = True

            numeric_val: Optional[float] = None
            sign = "N/A"

            if not is_nil and raw_value is not None:
                cleaned_str = raw_value.replace(",", "").strip()
                if cleaned_str.startswith("(") and cleaned_str.endswith(")"):
                    cleaned_str = "-" + cleaned_str[1:-1].strip()
                try:
                    numeric_val = float(cleaned_str)
                    if numeric_val > 0:
                        sign = "+"
                    elif numeric_val < 0:
                        sign = "-"
                    else:
                        sign = "0"
                except ValueError:
                    numeric_val = None
                    sign = "N/A"

            char_start = None
            char_end = None
            if full_query and raw_value:
                pos = full_query.find(f">{raw_value}<")
                if pos != -1:
                    char_start = pos + 1
                    char_end = char_start + len(raw_value)

            fact_id = str(uuid.uuid5(UUID_NAMESPACE, f"{case_id}:fact:{concept_qname}:{cid}:{uid}:{fact_locator}"))

            prov = LogicalProvenance(
                dataset="TheFinAI/FinMR",
                artifact="test-00000-of-00001.parquet",
                case_id=case_id,
                source_section="## Instance document",
                document_type="xbrl_instance",
                filing_reference=entity_cik,
                xbrl_concept=concept_qname,
                context_id=cid,
                element_locator=fact_locator,
                char_offset_start=char_start,
                char_offset_end=char_end,
            )

            fact = FinancialFact(
                fact_id=fact_id,
                case_id=case_id,
                concept_qname=concept_qname,
                context_id=cid,
                unit_id=uid,
                raw_value=raw_value,
                numeric_value=numeric_val,
                decimals=decimals,
                scale=scale,
                sign=sign,
                is_nil=is_nil,
                provenance=prov,
            )
            facts.append(fact)

    return contexts, units, facts, entity_cik


def parse_schema_document(
    schema_xml: str,
    case_id: str,
) -> Tuple[List[XbrlConcept], Optional[str], Optional[str]]:
    """Extracts custom element definitions and target namespace from Schema XML."""
    if not schema_xml.strip():
        return [], None, None

    try:
        root = ET.fromstring(schema_xml)
    except Exception:
        try:
            root = ET.fromstring(f"<root>{schema_xml}</root>")
        except Exception:
            return [], None, None

    target_ns = root.attrib.get("targetNamespace")
    custom_prefix = None
    if target_ns:
        for k, v in root.attrib.items():
            if k.startswith("xmlns:") and v == target_ns:
                custom_prefix = k.split(":")[1]
                break
        if not custom_prefix:
            parts = target_ns.replace("http://", "").replace("https://", "").split("/")
            custom_prefix = parts[0] if parts else "custom"

    concepts: List[XbrlConcept] = []
    for elem in root.iter():
        if elem.tag.endswith("element"):
            name = elem.attrib.get("name")
            if not name:
                continue

            data_type = elem.attrib.get("type")
            sub_group = elem.attrib.get("substitutionGroup")
            abstract_str = elem.attrib.get("abstract", "false").lower()
            nillable_str = elem.attrib.get("nillable", "true").lower()

            period_type = None
            balance_type = None
            for attr_k, attr_v in elem.attrib.items():
                if "periodType" in attr_k:
                    period_type = attr_v
                elif "balance" in attr_k:
                    balance_type = attr_v

            prefix = custom_prefix or "custom"
            qname = f"{prefix}:{name}"
            concept_id = str(uuid.uuid5(UUID_NAMESPACE, f"{case_id}:concept:{qname}"))

            c = XbrlConcept(
                concept_id=concept_id,
                qname=qname,
                prefix=prefix,
                local_name=name,
                namespace_uri=target_ns,
                data_type=data_type,
                period_type=period_type,
                balance_type=balance_type,
                substitution_group=sub_group,
                is_abstract=(abstract_str == "true"),
                is_nillable=(nillable_str == "true"),
            )
            concepts.append(c)

    return concepts, target_ns, custom_prefix


def parse_calculation_linkbase(
    calc_xml: str,
    case_id: str,
    custom_prefix: str = "us-gaap",
) -> List[CalculationRelationship]:
    """Extracts directed summation arcs from Calculation linkbase XML."""
    if not calc_xml.strip():
        return []

    try:
        root = ET.fromstring(calc_xml)
    except Exception:
        try:
            root = ET.fromstring(f"<root>{calc_xml}</root>")
        except Exception:
            return []

    locators: Dict[str, str] = {}
    for elem in root.iter():
        if elem.tag.endswith("loc"):
            label = elem.attrib.get("{http://www.w3.org/1999/xlink}label") or elem.attrib.get("xlink:label")
            href = elem.attrib.get("{http://www.w3.org/1999/xlink}href") or elem.attrib.get("xlink:href", "")
            if label and href:
                raw_concept = _clean_concept_href(href)
                concept_qname = _normalize_concept_qname(raw_concept, {}, default_prefix=custom_prefix)
                locators[label] = concept_qname

    relationships: List[CalculationRelationship] = []
    for link in root.iter():
        if link.tag.endswith("calculationLink"):
            role_uri = link.attrib.get("{http://www.w3.org/1999/xlink}role") or link.attrib.get("xlink:role", "")

            for arc in link.iter():
                if arc.tag.endswith("calculationArc"):
                    from_lbl = arc.attrib.get("{http://www.w3.org/1999/xlink}from") or arc.attrib.get("xlink:from")
                    to_lbl = arc.attrib.get("{http://www.w3.org/1999/xlink}to") or arc.attrib.get("xlink:to")
                    weight_str = arc.attrib.get("weight", "1.0")
                    order_str = arc.attrib.get("order")
                    arcrole = arc.attrib.get("{http://www.w3.org/1999/xlink}arcrole") or arc.attrib.get(
                        "xlink:arcrole", "http://www.xbrl.org/2003/arcrole/summation-item"
                    )

                    parent = locators.get(from_lbl, from_lbl or "")
                    child = locators.get(to_lbl, to_lbl or "")

                    if not parent or not child:
                        continue

                    try:
                        weight = float(weight_str)
                    except ValueError:
                        weight = 1.0

                    order = float(order_str) if order_str else None
                    rel_id = str(uuid.uuid5(UUID_NAMESPACE, f"{case_id}:calc:{role_uri}:{parent}:{child}"))

                    rel = CalculationRelationship(
                        relationship_id=rel_id,
                        case_id=case_id,
                        role_uri=role_uri,
                        parent_concept=parent,
                        child_concept=child,
                        weight=weight,
                        order=order,
                        arcrole=arcrole,
                    )
                    relationships.append(rel)

    return relationships


def parse_label_linkbase(
    label_xml: str,
    case_id: str,
    custom_prefix: str = "us-gaap",
) -> List[LabelRelationship]:
    """Extracts concept-to-human-readable label mappings from Label linkbase XML."""
    if not label_xml.strip():
        return []

    try:
        root = ET.fromstring(label_xml)
    except Exception:
        try:
            root = ET.fromstring(f"<root>{label_xml}</root>")
        except Exception:
            return []

    locators: Dict[str, str] = {}
    labels_by_lbl: Dict[str, Tuple[str, str, str]] = {}

    for elem in root.iter():
        if elem.tag.endswith("loc"):
            lbl = elem.attrib.get("{http://www.w3.org/1999/xlink}label") or elem.attrib.get("xlink:label")
            href = elem.attrib.get("{http://www.w3.org/1999/xlink}href") or elem.attrib.get("xlink:href", "")
            if lbl and href:
                raw_c = _clean_concept_href(href)
                locators[lbl] = _normalize_concept_qname(raw_c, {}, default_prefix=custom_prefix)
        elif elem.tag.endswith("label"):
            lbl = elem.attrib.get("{http://www.w3.org/1999/xlink}label") or elem.attrib.get("xlink:label")
            role = elem.attrib.get("{http://www.w3.org/1999/xlink}role") or elem.attrib.get("xlink:role", "")
            lang = elem.attrib.get("{http://www.w3.org/XML/1998/namespace}lang") or elem.attrib.get("xml:lang", "en-US")
            text = (elem.text or "").strip()
            if lbl and text:
                labels_by_lbl[lbl] = (text, role, lang)

    label_relationships: List[LabelRelationship] = []
    for arc in root.iter():
        if arc.tag.endswith("labelArc"):
            from_lbl = arc.attrib.get("{http://www.w3.org/1999/xlink}from") or arc.attrib.get("xlink:from")
            to_lbl = arc.attrib.get("{http://www.w3.org/1999/xlink}to") or arc.attrib.get("xlink:to")

            concept = locators.get(from_lbl)
            label_data = labels_by_lbl.get(to_lbl)

            if concept and label_data:
                text, role, lang = label_data
                label_id = str(uuid.uuid5(UUID_NAMESPACE, f"{case_id}:label:{concept}:{role}"))
                lr = LabelRelationship(
                    label_id=label_id,
                    case_id=case_id,
                    concept_qname=concept,
                    role_uri=role,
                    label_text=text,
                    language=lang,
                )
                label_relationships.append(lr)

    return label_relationships


def parse_taxonomy_document(
    tax_content: str,
    case_id: str,
) -> List[XbrlConcept]:
    """Extracts supplementary US GAAP taxonomy element declarations from structured text blocks or XML."""
    if not tax_content.strip():
        return []

    concepts: List[XbrlConcept] = []

    # 1. Check for structured text block format [Concept Core]
    if "[Concept Core]" in tax_content:
        blocks = re.split(r"\[Concept Core\]", tax_content)
        for b in blocks[1:]:
            id_m = re.search(r"ID:\s*([\w\-:]+)", b)
            type_m = re.search(r"Type:\s*([\w\-:]+)", b)
            bal_m = re.search(r"Balance:\s*([\w\-:]+)", b)
            per_m = re.search(r"PeriodType:\s*([\w\-:]+)", b)
            abs_m = re.search(r"Abstract:\s*([\w\-:]+)", b)

            if id_m:
                qname = id_m.group(1).strip()
                pfx = qname.split(":")[0] if ":" in qname else "us-gaap"
                loc = qname.split(":")[1] if ":" in qname else qname
                data_type = type_m.group(1).strip() if type_m else None
                bal = bal_m.group(1).strip() if bal_m and bal_m.group(1) != "None" else None
                ptype = per_m.group(1).strip() if per_m and per_m.group(1) != "None" else None
                is_abs = abs_m.group(1).lower() == "true" if abs_m else False

                cid = str(uuid.uuid5(UUID_NAMESPACE, f"{case_id}:concept:{qname}"))
                c = XbrlConcept(
                    concept_id=cid,
                    qname=qname,
                    prefix=pfx,
                    local_name=loc,
                    namespace_uri="http://fasb.org/us-gaap/2021-01-31",
                    data_type=data_type,
                    period_type=ptype,
                    balance_type=bal,
                    substitution_group="xbrli:item",
                    is_abstract=is_abs,
                    is_nillable=True,
                )
                concepts.append(c)
        return concepts

    # 2. XML fallback if taxonomy is XML element declarations
    try:
        root = ET.fromstring(tax_content)
    except Exception:
        try:
            root = ET.fromstring(f"<root>{tax_content}</root>")
        except Exception:
            return []

    for elem in root.iter():
        if elem.tag.endswith("element"):
            name = elem.attrib.get("name")
            if not name:
                continue

            qname = f"us-gaap:{name}" if ":" not in name else name
            pfx = qname.split(":")[0]
            loc = qname.split(":")[1]
            data_type = elem.attrib.get("type")
            sub_group = elem.attrib.get("substitutionGroup")
            abstract_str = elem.attrib.get("abstract", "false").lower()
            nillable_str = elem.attrib.get("nillable", "true").lower()

            period_type = None
            balance_type = None
            for attr_k, attr_v in elem.attrib.items():
                if "periodType" in attr_k:
                    period_type = attr_v
                elif "balance" in attr_k:
                    balance_type = attr_v

            cid = str(uuid.uuid5(UUID_NAMESPACE, f"{case_id}:concept:{qname}"))
            c = XbrlConcept(
                concept_id=cid,
                qname=qname,
                prefix=pfx,
                local_name=loc,
                namespace_uri="http://fasb.org/us-gaap/2021-01-31",
                data_type=data_type,
                period_type=period_type,
                balance_type=balance_type,
                substitution_group=sub_group,
                is_abstract=(abstract_str == "true"),
                is_nillable=(nillable_str == "true"),
            )
            concepts.append(c)

    return concepts
