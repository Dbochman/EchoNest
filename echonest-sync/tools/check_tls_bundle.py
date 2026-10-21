"""Offline packaging preflight; never access app config, keyring, or the network."""

import argparse
from importlib.metadata import version
import re
import ssl


MIN_CERTIFI = (2026, 10, 19)
# Known trust paths excluded by the incident-safe certifi bundle. The C3 ECC
# root is unaffected and was restored in certifi 2026.10.19; do not block it.
# This supplements the package floor to catch a stale copied bundle.
EXCLUDED_ROOTS = {
    "AAA Certificate Services",
    "emSign ECC Root CA - G3",
}


def check_bundle(certifi_version, ca_file):
    if not re.fullmatch(r"\d+\.\d+\.\d+", certifi_version):
        raise ValueError("Cannot verify certifi release version")
    if tuple(map(int, certifi_version.split("."))) < MIN_CERTIFI:
        raise ValueError("Install certifi>=2026.10.19 before packaging")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(cafile=ca_file)
    roots = context.get_ca_certs()
    if not roots:
        raise ValueError("The packaged CA bundle is empty")
    names = {
        value for root in roots for rdn in root["subject"]
        for key, value in rdn if key == "commonName"
    }
    if names & EXCLUDED_ROOTS:
        raise ValueError("The packaged CA bundle still contains incident-excluded roots")
    return len(roots)


def main():
    import certifi

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ca-file", default=certifi.where())
    args = parser.parse_args()
    count = check_bundle(version("certifi"), args.ca_file)
    print("TLS packaging preflight passed: {} CA certificates".format(count))


if __name__ == "__main__":
    main()
