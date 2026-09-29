"""Vat canh."""


def apply(feat, spec, idx) -> str:
    p = feat.params
    distance = p["distance"]
    edges = p.get("edges", "all")
    selector_map = {"all": "'|Z'", "top": "'>Z'", "bottom": "'<Z'"}
    selector = selector_map.get(edges, "'|Z'")
    return f"result = result.edges({selector}).chamfer({distance})"
