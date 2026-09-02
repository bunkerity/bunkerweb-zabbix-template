#!/usr/bin/env python3
"""Import the template into Zabbix and enforce its release metadata."""

from argparse import ArgumentParser
from json import dumps, loads
from pathlib import Path
from re import fullmatch
from sys import exit as sys_exit, stderr
from time import sleep, time
from urllib.error import URLError
from urllib.request import Request, urlopen

TEMPLATE_NAME = "BunkerWeb by HTTP"
VENDOR_NAME = "Bunkerity"
VERSION_PATTERN = r"(\d+)\.(\d+)-(\d+)"
HOST_NAME = "bunkerweb-template-test"
GROUP_NAME = "BunkerWeb template test"
REQUIRED_ITEMS = ("bw.scrape.ok", "bw.build.version", "bw.metric_errors")
REQUIRED_DISCOVERED_PREFIXES = (
    "bw.requests.total[",
    "bw.latency.avg[",
    "bw.shm.capacity[",
)


class ZabbixError(RuntimeError):
    pass


def call(url, method, params, token=None, timeout=30):
    request = Request(
        url,
        data=dumps(
            {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        ).encode(),
        headers={"Content-Type": "application/json-rpc"},
    )
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urlopen(request, timeout=timeout) as response:
        body = loads(response.read().decode())
    if "error" in body:
        raise ZabbixError(f"{method}: {body['error'].get('data') or body['error']}")
    return body["result"]


def wait_for_api(url, deadline):
    while time() < deadline:
        try:
            return call(url, "apiinfo.version", {}, timeout=5)
        except (ZabbixError, URLError, OSError, ValueError):
            sleep(2)
    raise ZabbixError("Zabbix API never became ready")


def import_template(url, token, path):
    rules = {
        name: {"createMissing": True, "updateExisting": True}
        for name in (
            "template_groups",
            "templates",
            "items",
            "discoveryRules",
            "triggers",
            "valueMaps",
            "host_groups",
        )
    }
    call(
        url,
        "configuration.import",
        {"format": "yaml", "rules": rules, "source": path.read_text(encoding="utf-8")},
        token,
    )
    templates = call(
        url,
        "template.get",
        {
            "filter": {"host": [TEMPLATE_NAME]},
            "output": ["templateid", "vendor_name", "vendor_version"],
        },
        token,
    )
    if not templates:
        raise ZabbixError(f"template {TEMPLATE_NAME!r} is absent after import")
    return templates[0]


def create_test_host(url, token, templateid, target):
    existing = call(url, "host.get", {"filter": {"host": [HOST_NAME]}}, token)
    if existing:
        call(url, "host.delete", [existing[0]["hostid"]], token)

    groups = call(url, "hostgroup.get", {"filter": {"name": [GROUP_NAME]}}, token)
    groupid = (
        groups[0]["groupid"]
        if groups
        else call(url, "hostgroup.create", {"name": GROUP_NAME}, token)["groupids"][0]
    )
    is_ipv4 = target.count(".") == 3 and all(
        part.isdigit() for part in target.split(".")
    )
    params = {
        "host": HOST_NAME,
        "interfaces": [
            {
                "type": 1,
                "main": 1,
                "useip": 1 if is_ipv4 else 0,
                "ip": target if is_ipv4 else "127.0.0.1",
                "dns": "" if is_ipv4 else target,
                "port": "10050",
            }
        ],
        "groups": [{"groupid": groupid}],
        "templates": [{"templateid": templateid}],
        "macros": [
            {"macro": "{$BUNKERWEB.EXPORTER.PORT}", "value": "80"},
            {"macro": "{$BUNKERWEB.EXPORTER.INTERVAL}", "value": "5s"},
        ],
    }
    return call(url, "host.create", params, token)["hostids"][0]


def wait_for_collection(url, token, hostid, deadline):
    missing = list(REQUIRED_DISCOVERED_PREFIXES)
    while time() < deadline:
        items = call(
            url,
            "item.get",
            {"hostids": hostid, "output": ["key_", "state", "error", "lastvalue"]},
            token,
        )
        keys = [item["key_"] for item in items]
        missing = [
            prefix
            for prefix in REQUIRED_DISCOVERED_PREFIXES
            if not any(key.startswith(prefix) for key in keys)
        ]
        unsupported = [item for item in items if item["state"] == "1"]
        required = [item for item in items if item["key_"] in REQUIRED_ITEMS]
        if (
            not missing
            and len(required) == len(REQUIRED_ITEMS)
            and all(item["lastvalue"] != "" for item in required)
            and not unsupported
        ):
            return len(items)
        sleep(5)

    if missing:
        raise ZabbixError(
            f"low-level discovery did not create items for: {', '.join(missing)}"
        )
    if unsupported:
        details = "; ".join(f"{item['key_']}: {item['error']}" for item in unsupported)
        raise ZabbixError(f"unsupported items: {details}")
    raise ZabbixError("required items did not collect values")


def version_tuple(version):
    match = fullmatch(VERSION_PATTERN, version)
    if not match:
        raise ZabbixError(f"vendor version {version!r} must use Zabbix's X.Y-N format")
    return tuple(map(int, match.groups()))


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--previous-template", type=Path)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    deadline = time() + args.timeout
    api_version = wait_for_api(args.url, deadline)
    token = call(args.url, "user.login", {"username": "Admin", "password": "zabbix"})

    previous_version = None
    if args.previous_template:
        previous_version = import_template(args.url, token, args.previous_template)[
            "vendor_version"
        ]

    template = import_template(args.url, token, args.template)
    vendor = template["vendor_name"]
    version = template["vendor_version"]
    if vendor != VENDOR_NAME:
        raise ZabbixError(f"vendor must be {VENDOR_NAME!r}, got {vendor!r}")
    current = version_tuple(version)

    if (
        previous_version
        and args.template.read_bytes() != args.previous_template.read_bytes()
    ):
        previous = version_tuple(previous_version)
        if current <= previous:
            raise ZabbixError(
                f"changed template must bump vendor version above {previous_version}, got {version}"
            )

    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as output:
            output.write(f"version={version}\n")

    hostid = create_test_host(args.url, token, template["templateid"], args.target)
    item_count = wait_for_collection(args.url, token, hostid, deadline)
    print(
        f"Imported {TEMPLATE_NAME} {version} into Zabbix {api_version}; {item_count} host items are supported"
    )


if __name__ == "__main__":
    try:
        main()
    except (ZabbixError, URLError, OSError, ValueError) as exc:
        print(f"import_template: {exc}", file=stderr)
        sys_exit(1)
