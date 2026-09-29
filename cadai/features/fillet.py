"""Bo tron canh."""


def apply(feat, spec, idx) -> str:
    p = feat.params
    radius = p["radius"]
    edges = p.get("edges", "all")
    selector_map = {"all": "'|Z'", "top": "'>Z'", "bottom": "'<Z'", "corners": "'|Z'"}
    selector = selector_map.get(edges, "'|Z'")
    return f"result = result.edges({selector}).fillet({radius})"
