#!/bin/sh
# ProxyCommand target: openstick-ssh-proxy.sh %h %p
exec ssh \
  -i "${HOME}/.ssh/id_rsa_kubernetes" \
  -o BatchMode=yes \
  -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=accept-new \
  -W "$1:$2" \
  root@100.81.190.71
