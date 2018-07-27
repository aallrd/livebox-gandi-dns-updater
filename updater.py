#!/usr/bin/env python3

import os

from requests import get, post, exceptions


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
    try:
        uri = "https://dns.api.gandi.net/api/v5/domains/{}/records".format(domain)
        r = get(uri, headers={'X-Api-Key': get_gandi_api_token()})
        return r.json()
    except exceptions.RequestException as e:
        raise Exception("Failed to retrieve the records for domain {}: {}".format(domain, e))
    except Exception as e:
        raise Exception("Unhandled exception while trying to retrieve the records for domain {}: {}".format(domain, e))


def get_configured_www_ip(records):
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


def main():
    try:
        get_gandi_api_token()
        domains = get_gandi_domains()
        livebox_ip = get_livebox_wan_ip()
        print("Livebox IP: {}".format(livebox_ip))
        for domain in domains:
            print("Checking domain: {}".format(domain))
            records = get_domain_records(domain)
            gandi_ip = get_configured_www_ip(records)
            print("Gandi WWW IP for {}: {}".format(domain, gandi_ip))
    except Exception as e:
        print("Something bad happened: {}".format(e))


if __name__ == "__main__":
    main()
