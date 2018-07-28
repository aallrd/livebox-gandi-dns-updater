# livebox-gandi-dns-updater

Update the DNS records for Gandi registered domains based on the current Livebox WAN address.

No static IP is available with the Orange ISP.

A Gandi API token is required to access the LiveDNS API: http://doc.livedns.gandi.net/

## Usage:

    usage: updater.py [-h] [-t API_TOKEN] [-d DOMAINS]
                  [-r {A,AAAA,CAA,CDS,CNAME,DNAME,DS,LOC,MX,NS,PTR,SPF,SRV,SSHFP,TLSA,TXT,WKS}]
                  [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--dry-run]
                  [--set-ip CUSTOM_IP]

    Update the DNS records for Gandi registered domains.
    
    optional arguments:
      -h, --help            show this help message and exit
      -t API_TOKEN, --api-token API_TOKEN
                            The Gandi API token to use.
      -d DOMAINS, --domains DOMAINS
                            A comma separated list of domains to update.
      -r {A,AAAA,CAA,CDS,CNAME,DNAME,DS,LOC,MX,NS,PTR,SPF,SRV,SSHFP,TLSA,TXT,WKS}, --records {A,AAAA,CAA,CDS,CNAME,DNAME,DS,LOC,MX,NS,PTR,SPF,SRV,SSHFP,TLSA,TXT,WKS}
                            The record type to update. Default is all.
      -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                            The log level to display. Default is INFO.
      --dry-run             Do not push the updated domain records.
      --set-ip CUSTOM_IP    Update the domain records using the specified IP.
                            Default is to extract the WAN address from the livebox
                            on the LAN.
                            
The Gandi API token and the list of domains to update can also be set from the environment:

    export GANDI_API_TOKEN=MY-GANDI-API-TOKEN
    export GANDI_DOMAINS=foo.com,bar.fr