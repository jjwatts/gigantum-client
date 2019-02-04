#!/bin/bash

# We get the desired UID directly from /mnt/share, as that should always ALREADY be set correctly
GIG_UID=$(stat -c '%u' /mnt/share)
useradd --shell /bin/bash -u $GIG_UID -o -c "" -m giguser

if [ ! -d /mnt/share/mitmproxy ]; then
  mkdir -p /mnt/share/mitmproxy;
fi
chown giguser /mnt/share/mitmproxy

# RUN mitmproxy to log traffic.
# E.g., for RStudio, LBENDPOINT will be set to labbook_ip:8787
gosu giguser:root nohup mitmdump --mode reverse:$LBENDPOINT --setheader :~q:Host:localhost:8080 -w /mnt/share/mitmproxy/$PROXYID.rserver.dump < /dev/null >/dev/null 2>&1 &

# This is the nginx proxy by default, which *should* run as root
# If giguser is desired, specify in the alternative run command.
exec "$@"
