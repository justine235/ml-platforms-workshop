from __future__ import annotations

import argparse
import json

import requests


def main() -> int:
    parser = argparse.ArgumentParser(description="Invoke the fleet managed online endpoint with an Entra or key token.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--request-file", default="sample-request.json")
    args = parser.parse_args()
    with open(args.request_file, "r", encoding="utf-8") as handle:
        payload = json.loads(handle.read())
    response = requests.post(
        args.url,
        headers={"Authorization": f"Bearer {args.token}", "Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=180,
    )
    response.raise_for_status()
    print(response.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
