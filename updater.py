#!/usr/bin/env python3

import argparse
import json
import logging
import os
import sys
import time

from requests import get, post, exceptions, put

logger = logging.getLogger('updater')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

GANDI_API_TOKEN = None
GANDI_DOMAINS = []
GANDI_RECORD_TYPES = ['A', 'AAAA', 'CAA', 'CDS', 'CNAME',
                      'DNAME', 'DS', 'LOC', 'MX', 'NS', 'PTR',
                      'SPF', 'SRV', 'SSHFP', 'TLSA', 'TXT', 'WKS']
DRY_RUN = False


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
        logger.debug("Gandi API response: {}".format(r.json()))
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
        if ip is None:
            raise Exception("No IP configured in the WWW record.")
        else:
            return ip
    except Exception as e:
        raise Exception(e)


def update_gandi_domain_records(records, old_ip, new_ip):
    global GANDI_RECORD_TYPES
    try:
        for record in records:
            if record['rrset_type'] in GANDI_RECORD_TYPES:
                for index, rrset_value in enumerate(record['rrset_values']):
                    if rrset_value == old_ip:
                        record['rrset_values'][index] = new_ip
                    else:
                        logger.debug("{}: {} ({})".format(record['rrset_type'], rrset_value, index))
            else:
                logger.debug("Discarding record type {} not in targeted list {}.".format(record['rrset_type'],
                                                                                         GANDI_RECORD_TYPES))
        return records
    except Exception as e:
        raise Exception("Failure while updating the IP address for domain records: {}".format(e))


def push_updated_domain_records(domain, updated_records):
    global GANDI_API_TOKEN, DRY_RUN
    try:
        uri = "https://dns.api.gandi.net/api/v5/domains/{}/records".format(domain)
        headers = {'X-Api-Key': GANDI_API_TOKEN, 'Content-Type': 'application/json'}
        data = {'items': updated_records}
        if not DRY_RUN:
            r = put(uri, headers=headers, data=json.dumps(data))
            r.raise_for_status()
            logger.info("Records updated for domain {}".format(domain))
        else:
            logger.info("URI: {}".format(uri))
            logger.info("headers: {}".format(headers))
            logger.info("data: {}".format(data))
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
        r = post("http://livebox.local/ws", headers=headers, data=params).json()
        logger.debug("Livebox WS response: {}".format(r))
        livebox_wan_ip = r["data"]["IPAddress"]
        logger.info("Livebox WAN IP: {}".format(livebox_wan_ip))
        return livebox_wan_ip
    except exceptions.RequestException as e:
        raise Exception("Failed to query the livebox webservices: {}".format(e))
    except Exception as e:
        raise Exception("Unhandled exception while querying the livebox webservices: {}".format(e))


def parse_args():
    global GANDI_API_TOKEN, GANDI_DOMAINS, GANDI_RECORD_TYPES, DRY_RUN
    parser = argparse.ArgumentParser(description='Update the DNS records for Gandi registered domains.')
    parser.add_argument('-d', '--daemon', dest='daemon', action='store_true',
                        help='Run in background.')
    parser.add_argument('-i', '--interval', dest='time', action='store',
                        help='Time interval between checks. Default is %(default)ssec.',
                        default=10800)
    parser.add_argument('-t', '--api-token', dest='api_token', action='store',
                        help='The Gandi API token to use.')
    parser.add_argument('-n', '--domains', dest='domains', action='store',
                        help='A comma separated list of domains to update.')
    parser.add_argument('-r', '--records', dest='records', action='store', choices=GANDI_RECORD_TYPES,
                        help='The record type to update. Default is %(default)s.', default='all')
    parser.add_argument('-l', '--log', dest='log_level', action='store',
                        help='The log level to display. Default is %(default)s.',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO')
    parser.add_argument('--dry-run', dest='dry_run', action='store_true',
                        help='Do not push the updated domain records.')
    parser.add_argument('--set-ip', dest='custom_ip', action='store',
                        help='Update the domain records using the specified IP. '
                             'Default is to extract the WAN address from the livebox on the LAN.')
    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.log_level, None))
    logger.debug("Daemon mode: {}".format(args.daemon))
    if args.daemon: logger.debug("Time interval set: {}".format(args.time))
    GANDI_API_TOKEN = args.api_token if args.api_token else get_gandi_api_token()
    GANDI_DOMAINS = args.domains.split(',') if args.domains else get_gandi_domains()
    logger.debug("Targeted domains: {}".format(GANDI_DOMAINS))
    if not args.records == "all": GANDI_RECORD_TYPES = list(args.records)
    logger.debug("Targeted record types: {}".format(GANDI_RECORD_TYPES))
    DRY_RUN = args.dry_run
    logger.debug("Dry run mode: {}".format(DRY_RUN))
    if args.custom_ip:
        wan_ip = args.custom_ip
        logger.debug("User defined WAN IP: {}".format(wan_ip))
    else:
        wan_ip = get_livebox_wan_ip()
        logger.debug("Livebox WAN IP: {}".format(wan_ip))
    return wan_ip, args.daemon, int(args.time)


def main():
    global GANDI_DOMAINS
    while True:
        try:
            wan_ip, daemon_mode, time_interval = parse_args()
            for domain in GANDI_DOMAINS:
                logger.info("Checking domain: {}".format(domain))
                records = get_domain_records(domain)
                gandi_ip = get_records_www_ip(records)
                if not gandi_ip == wan_ip:
                    logger.info("The IP address for domain {} must be updated ({}).".format(domain, gandi_ip))
                    updated_domain_records = update_gandi_domain_records(records, gandi_ip, wan_ip)
                    push_updated_domain_records(domain, updated_domain_records)
                else:
                    logger.info("The IP address configured for domain {} is valid: {}.".format(domain, gandi_ip))
            if not daemon_mode:
                break
            else:
                logger.debug("Sleeping for {}sec".format(time_interval))
                time.sleep(time_interval)
        except Exception as e:
            logger.error(e)
            sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
