"""Intersight Credential Helper

Copied from https://github.com/CiscoDevNet/intersight-python-utils (credentials.py)

This module configures an intersight API client instance using an API key ID
and secret key file (v3 API keys, HTTP signature scheme).  It takes the
following CLI arguments (or equivalent environment variables):

    --url               The Intersight root URL for the API endpoint
                         (default https://intersight.com)
    --ignore-tls         Ignore TLS server-side certificate verification
    --api-key-id         API client key id for the HTTP signature scheme
                         (env: INTERSIGHT_API_KEY_ID)
    --api-key-file       Path to file containing the secret key for the
                         HTTP signature scheme
                         (env: INTERSIGHT_API_PRIVATE_KEY)
"""

import argparse
import os
import datetime
import re

import intersight

# This argument parser instance should be used within scripts where
# additional CLI arguments are required.
Parser = argparse.ArgumentParser(description='Intersight Python SDK credential lookup')


def config_credentials(description=None):
    """config_credentials configures and returns an Intersight api client

    Arguments:
        description {string}: Optional description used within argparse help

    Returns:
        api_client [intersight.api_client.ApiClient]: base intersight api client class
    """
    if description is not None:
        Parser.description = description
    Parser.add_argument('--url', default='https://intersight.com',
                         help='The Intersight root URL for the API endpoint. The default is https://intersight.com')
    Parser.add_argument('--ignore-tls', action='store_true',
                         help='Ignore TLS server-side certificate verification')
    Parser.add_argument(
        '--https-proxy',
        default=os.getenv('https_proxy'),
        help="https_proxy with port if required for connecting to Intersight (e.g., 'http://proxy.esl.cisco.com:80')")
    Parser.add_argument(
        '--api-key-id',
        default=os.getenv('INTERSIGHT_API_KEY_ID'),
        help='API client key id for the HTTP signature scheme')
    Parser.add_argument(
        '--api-key-file',
        default=os.getenv('INTERSIGHT_API_PRIVATE_KEY', '~/Downloads/SecretKey.txt'),
        help='Name of file containing secret key for the HTTP signature scheme')

    args = Parser.parse_args()

    if args.api_key_id and args.api_key_file:
        key_file = os.path.expanduser(args.api_key_file)
        with open(key_file, 'r') as file:
            private_key = file.read()
        regex = re.compile(r"\s*-----BEGIN (.*)-----\s+")
        match = regex.match(private_key)
        if not match:
            raise ValueError("API key file does not have a valid PEM pre boundary")
        pem_header = match.group(1)
        # HTTP signature scheme - v3 API keys can be RSA or EC based.
        if pem_header == 'RSA PRIVATE KEY':
            signing_scheme = intersight.signing.SCHEME_RSA_SHA256
            signing_algorithm = intersight.signing.ALGORITHM_RSASSA_PKCS1v15
        elif pem_header == 'EC PRIVATE KEY':
            signing_scheme = intersight.signing.SCHEME_HS2019
            signing_algorithm = intersight.signing.ALGORITHM_ECDSA_MODE_FIPS_186_3
        else:
            raise Exception("Unsupported key: {0}".format(pem_header))

        configuration = intersight.Configuration(
            host=args.url,
            signing_info=intersight.HttpSigningConfiguration(
                key_id=args.api_key_id,
                private_key_path=key_file,
                signing_scheme=signing_scheme,
                signing_algorithm=signing_algorithm,
                hash_algorithm=intersight.signing.HASH_SHA256,
                signed_headers=[intersight.signing.HEADER_REQUEST_TARGET,
                                 intersight.signing.HEADER_CREATED,
                                 intersight.signing.HEADER_EXPIRES,
                                 intersight.signing.HEADER_HOST,
                                 intersight.signing.HEADER_DATE,
                                 intersight.signing.HEADER_DIGEST,
                                 'Content-Type',
                                 'User-Agent'
                                 ],
                signature_max_validity=datetime.timedelta(minutes=5)
            )
        )
    else:
        raise Exception('Must provide API key information')

    if args.ignore_tls:
        configuration.verify_ssl = False

    configuration.proxy = args.https_proxy
    api_client = intersight.ApiClient(configuration)
    api_client.set_default_header('referer', args.url)
    api_client.set_default_header('x-requested-with', 'XMLHttpRequest')
    api_client.set_default_header('Content-Type', 'application/json')

    return api_client


if __name__ == "__main__":
    config_credentials()
