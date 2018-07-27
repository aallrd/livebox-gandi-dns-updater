# livebox-gandi-dns-updater

Update the DNS records for Gandi registered domains based on the current Livebox WAN address.

No static IP is available with the Orange ISP.

## Usage:

    export GANDI_API_TOKEN=MY-GANDI-API-TOKEN
    export GANDI_DOMAINS=foo.com,bar.fr
    ./updater.py
