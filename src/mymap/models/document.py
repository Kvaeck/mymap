import json

def deterministic_doc_bytes(doc_dict: dict) -> bytes:
    # Ensure keys sorted so identical content always results in same bytes
    return json.dumps(doc_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
