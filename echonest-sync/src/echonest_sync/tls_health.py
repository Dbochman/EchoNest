"""Opt-in TLS-only diagnostic for the actual frozen application's certifi bundle."""

from concurrent.futures import ThreadPoolExecutor
import json
import socket
import ssl
import sys

import certifi


CONTROLS = ("github.com", "pypi.org")
CANARIES = {
    "{}-{}-{}.we-have-a-problem.com".format(kind, variant, chain):
        "EM {} TLS CA - {}".format(kind.upper(), variant.upper())
    for chain in ("emudhra", "aaa-emudhra")
    for kind in ("dv", "ov", "ev")
    for variant in ("g3b", "g3c")
}


def probe(host, expected_issuer, context):
    try:
        with socket.create_connection((host, 443), timeout=8) as connection:
            with context.wrap_socket(connection, server_hostname=host) as tls:
                certificate = tls.getpeercert()
        issuer = dict(item for rdn in certificate.get("issuer", ()) for item in rdn).get("commonName")
        if expected_issuer is None:
            result = "control_passed"
        else:
            result = "exposed" if issuer == expected_issuer else "canary_changed"
        return {"host": host, "result": result}
    except ssl.SSLCertVerificationError as error:
        code = getattr(error, "verify_code", None)
        result = "rejected" if expected_issuer and code in (2, 19, 20, 21, 23, 27, 28) else "inconclusive"
        return {"host": host, "result": result, "verify_code": code}
    except (OSError, ssl.SSLError) as error:
        return {"host": host, "result": "inconclusive", "error": type(error).__name__}


def exit_code(results):
    if any(item["result"] == "exposed" for item in results):
        return 1
    if not results or any(item["result"] not in ("rejected", "control_passed") for item in results):
        return 2
    return 0


def main():
    # Load ONLY the embedded bundle, not ambient system/extra-CA settings.
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(cafile=certifi.where())
    targets = [(host, None) for host in CONTROLS] + list(CANARIES.items())
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda target: probe(*target, context), targets))
    code = exit_code(results)
    print(json.dumps({"ok": code == 0, "frozen": bool(getattr(sys, "frozen", False)),
                      "python": sys.version.split()[0], "certifi": certifi.__version__,
                      "results": results}, sort_keys=True))
    return code
