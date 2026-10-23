"""Load and execute named HTTP commands from a Control API JSON file."""

import json
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


def load_commands(path):
    with open(path, encoding="utf-8-sig") as source:
        commands = json.load(source)
    if not isinstance(commands, dict) or not commands:
        raise ValueError("JSON must contain a non-empty object of named commands.")
    for name, command in commands.items():
        if not name.strip() or not isinstance(command, dict):
            raise ValueError(f"Invalid command: {name!r}")
        method = command.get("type", "")
        if not isinstance(method, str) or method.upper() not in {
            "GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"
        }:
            raise ValueError(f"{name}: unsupported HTTP request type.")
        url = command.get("url", "")
        if not isinstance(url, str):
            raise ValueError(f"{name}: URL must be a string.")
        parts = urlsplit(url)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise ValueError(f"{name}: URL must start with http:// or https://.")
        if not isinstance(command.get("param", {}), dict):
            raise ValueError(f"{name}: param must be an object.")
    return commands


def send_command(command, timeout=3, *, include_body=False):
    """Send one request using its configured method, query parameters and JSON body."""
    parts = urlsplit(command["url"])
    params = urlencode(command.get("param", {}), doseq=True)
    query = "&".join(value for value in (parts.query, params) if value)
    url = urlunsplit(parts._replace(query=query))
    data = None
    headers = {}
    if "body" in command:
        data = json.dumps(command["body"], ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=command["type"].upper())
    with urlopen(request, timeout=timeout) as response:
        if include_body:
            encoding = response.headers.get_content_charset() or "utf-8"
            body = response.read(8192).decode(encoding, errors="replace").strip()
            return response.status, body
        return response.status
