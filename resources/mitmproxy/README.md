# Gigantum's mitmproxy

The repository of a man-in-the-middle reverse proxy that sits 
between the gtm client and project containers running rstudio-server
for now, but it's general to any http tool.

The path to rstudio server is:

proxy-route -> rservermitm:8080 -> project:8787

This container proxies all request and uses the 
Man-In-The-Middle proxy to log http traffic (including 
request payloads) to the a shared volume at /mnt/share

## Contributing

Gigantum uses the [Developer Certificate of Origin](https://developercertificate.org/). 
This is lightweight approach that doesn't require submission and review of a
separate contributor agreement.  Code is signed directly by the developer using
facilities built into git.

Please see [`docs/contributing.md` in the gtm
repository](https://github.com/gigantum/gtm/tree/integration/docs/contributing.md).

## Credits
