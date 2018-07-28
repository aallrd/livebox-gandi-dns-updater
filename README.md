# livebox-gandi-dns-updater

Update the DNS records for Gandi registered domains based on the current Livebox WAN address.

No static IP is available with the Orange ISP.

A Gandi API token is required to access the LiveDNS API: http://doc.livedns.gandi.net/

## Usage:

    export GANDI_API_TOKEN=MY-GANDI-API-TOKEN
    export GANDI_DOMAINS=foo.com,bar.fr
    ./updater.py
