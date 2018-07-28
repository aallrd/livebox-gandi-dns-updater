#!/usr/bin/env python3

import argparse
import json
import logging
import os

from requests import get, post, exceptions, put

logger = logging.getLogger('updater')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

GANDI_API_TOKEN = None
GANDI_DOMAINS = []


def get_gandi_api_token():
    try:
        return os.environ["GANDI_API_TOKEN"]
    except KeyError:
        raise Exception("The GANDI_API_TOKEN environment variable is not set.")


def get_gandi_domains():
    try:
        return os.environ["GANDI_DOMAINS"].split(",")
    except KeyError:
        raise Exception("The GANDI_DOMAINS environment variable is not set.")


def get_domain_records(domain):
    global GANDI_API_TOKEN
    try:
        uri = "https://dns.api.gandi.net/api/v5/domains/{}/records".format(domain)
        headers = {'X-Api-Key': GANDI_API_TOKEN}
        r = get(uri, headers=headers)
        if not r.status_code == 200:
            raise exceptions.HTTPError("HTTP error: {}: {}".format(r.status_code, r.reason))
        else:
            return r.json()
    except exceptions.RequestException as e:
        raise Exception("Failed to retrieve the records for domain {}: {}".format(domain, e))
    except Exception as e:
        raise Exception("Unhandled exception while trying to retrieve the records for domain {}: {}".format(domain, e))


def get_records_www_ip(records):
    ip = None
    try:
        for record in records:
            if record["rrset_name"] == "www":
                ip = record["rrset_values"][0]
                break
        if ip == None:
            raise Exception("No IP configured in the WWW record.")
        else:
            return ip
    except Exception as e:
        raise Exception(e)


def update_gandi_domain_records(records, old_ip, new_ip):
    try:
        for record in records:
            for index, rrset_value in enumerate(record['rrset_values']):
                if rrset_value == old_ip:
                    record['rrset_values'][index] = new_ip
        return records
    except Exception as e:
        raise Exception("Failure while updating the IP address for domain records: {}".format(e))


def push_updated_domain_records(domain, updated_records):
    global GANDI_API_TOKEN
    try:
        uri = "https://dns.api.gandi.net/api/v5/domains/{}/records".format(domain)
        headers = {'X-Api-Key': GANDI_API_TOKEN, 'Content-Type': 'application/json'}
        data = {'items': updated_records}
        r = put(uri, headers=headers, data=json.dumps(data))
        r.raise_for_status()
        logger.info("Records updated for domain {}".format(domain))
    except exceptions.HTTPError:
        raise exceptions.HTTPError("HTTP error: {}: {}".format(r.status_code, r.json()))
    except exceptions.RequestException as e:
        raise Exception("Failed to push the updated records for domain {}: {}".format(domain, e))
    except Exception as e:
        raise Exception(
            "Unhandled exception while trying to push the updated records for domain {}: {}".format(domain, e))


def get_livebox_wan_ip():
    try:
        params = '''{"service":"NMC","method":"getWANStatus","parameters":{}}'''
        headers = {"Content-type": "application/x-sah-ws-4-call+json"}
        r = post("http://livebox/ws", headers=headers, data=params).json()
        return r["data"]["IPAddress"]
    except exceptions.RequestException as e:
        raise Exception("Failed to query the livebox webservices: {}".format(e))
    except Exception as e:
        raise Exception("Unhandled exception while querying the livebox webservices: {}".format(e))


def parse_args():
    global GANDI_API_TOKEN, GANDI_DOMAINS
    parser = argparse.ArgumentParser(description='Update the DNS records for Gandi registered domains.')
    parser.add_argument('--api-token', dest='api_token', action='store',
                        help='The Gandi API token to use.')
    parser.add_argument('--domains', dest='domains', action='store',
                        help='A comma separated list of domains to update.')
    parser.add_argument('--log', dest='log_level', action='store',
                        help='The log level to display.', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO')
    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.log_level, None))
    GANDI_API_TOKEN = args.api_token if args.api_token else get_gandi_api_token()
    GANDI_DOMAINS = args.domains.split(',') if args.domains else get_gandi_domains()


def main():
    global GANDI_DOMAINS
    try:
        parse_args()
        livebox_ip = get_livebox_wan_ip()
        logger.info("Livebox WAN IP: {}".format(livebox_ip))
        for domain in GANDI_DOMAINS:
            logger.info("Checking domain: {}".format(domain))
            records = get_domain_records(domain)
            gandi_ip = get_records_www_ip(records)
            if not gandi_ip == livebox_ip:
                logger.info("The IP address for domain {} must be updated ({}).".format(domain, gandi_ip))
                updated_domain_records = update_gandi_domain_records(records, gandi_ip, livebox_ip)
                push_updated_domain_records(domain, updated_domain_records)
            else:
                logger.info("The IP address configured for domain {} is valid: {}.".format(domain, gandi_ip))
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    main()
