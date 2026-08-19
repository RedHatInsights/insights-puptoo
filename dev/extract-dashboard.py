#!/usr/bin/env python3
"""Extract the Grafana dashboard JSON from the ConfigMap YAML for local dev use."""

import json
from pathlib import Path

import yaml

CONFIGMAP = Path(__file__).resolve().parent.parent / (
    "dashboards/grafana-dashboard-insights-puptoo-general.configmap.yaml"
)
OUTPUT = Path(__file__).resolve().parent / "grafana/dashboards/puptoo.json"


TEMPLATE_UIDS = ("${datasource}", "${datasource_aws}")


def _normalize_panel(panel):
    ds = panel.get("datasource", {})
    if ds.get("uid") in TEMPLATE_UIDS:
        ds["uid"] = "prometheus"
    for target in panel.get("targets", []):
        tds = target.get("datasource", {})
        if tds.get("uid") in TEMPLATE_UIDS:
            tds["uid"] = "prometheus"
    for child in panel.get("panels", []):
        _normalize_panel(child)


def main():
    cm = yaml.safe_load(CONFIGMAP.read_text())
    dashboard = json.loads(cm["data"]["general.json"])

    for panel in dashboard["panels"]:
        _normalize_panel(panel)

    dashboard["templating"] = {"list": []}
    dashboard["title"] = "Puptoo (local)"
    dashboard.pop("uid", None)
    dashboard.pop("id", None)
    dashboard["version"] = 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(dashboard, indent=2) + "\n")
    print(f"Dashboard extracted: {len(dashboard['panels'])} panels -> {OUTPUT}")


if __name__ == "__main__":
    main()
