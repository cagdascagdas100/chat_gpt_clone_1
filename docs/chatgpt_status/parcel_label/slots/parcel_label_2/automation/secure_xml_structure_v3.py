from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("secure_xml_structure_v2.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_xml_structure_v2", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_XML_STRUCTURE_V2_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

SECURITY_PATH = Path(__file__).with_name("secure_xml_preflight_v2.py")
security_spec = importlib.util.spec_from_file_location("parcel_label_2_xml_security_v2", SECURITY_PATH)
if security_spec is None or security_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_XML_SECURITY_V2_IMPORT_FAILED")
security = importlib.util.module_from_spec(security_spec)
security_spec.loader.exec_module(security)

# The v2 structural parser resolves its security helper through this module global.
# Rebind it to the 2.7.2 floor without mutating the historical source file.
previous.previous = security
validate_xml_structure = previous.validate_xml_structure
