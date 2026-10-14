#!/bin/bash
# Paste on k3s-london-2 via provider console (SSH currently broken: TCP/22 accepts, no banner).
# Joins V2 as agent: bazzite SQLite CP @ 100.81.190.71:6443, Flannel on public WAN.
set -euo pipefail

K3S_VERSION="${K3S_VERSION:-v1.36.2+k3s1}"
K3S_URL="${K3S_URL:-https://100.81.190.71:6443}"
# node-token from bazzite:/var/lib/rancher/k3s/server/node-token
K3S_TOKEN="${K3S_TOKEN:?set K3S_TOKEN}"

WAN_IP="${WAN_IP:-46.33.10.90}"
# Same pandahost /26 as london-1 — usually ens3
IFACE="${IFACE:-$(ip -o route get 1.1.1.1 | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')}"

echo "hostname=$(hostname) iface=$IFACE wan=$WAN_IP"

# Fix SSH first if needed
systemctl restart sshd 2>/dev/null || systemctl restart ssh 2>/dev/null || true
ss -lntp | grep -E ':22\s' || true

# Tear down any leftover V1 agent cleanly (prefer no k3s-killall — it can flush SSH rules)
systemctl stop k3s-agent k3s 2>/dev/null || true
systemctl disable k3s-agent k3s 2>/dev/null || true
if command -v k3s >/dev/null 2>&1; then
  /usr/local/bin/k3s-uninstall.sh 2>/dev/null || true
  /usr/local/bin/k3s-agent-uninstall.sh 2>/dev/null || true
fi

mkdir -p /etc/rancher/k3s
cat >/etc/rancher/k3s/config.yaml <<EOF
bind-address: ${WAN_IP}
node-ip: ${WAN_IP}
node-external-ip: ${WAN_IP}
prefer-bundled-bin: true
flannel-iface: ${IFACE}
kubelet-arg:
  - "config=/etc/rancher/k3s/kubelet-config.yaml"
selinux: true
EOF

cat >/etc/rancher/k3s/kubelet-config.yaml <<'EOF'
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
failSwapOn: false
memorySwap:
  swapBehavior: LimitedSwap
featureGates:
  NodeSwap: true
seccompDefault: true
EOF

curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="$K3S_VERSION" K3S_URL="$K3S_URL" K3S_TOKEN="$K3S_TOKEN" sh -s - agent

# Tailscale must not use Flannel as "direct" path
cat >/usr/local/sbin/block-tailscale-on-flannel.sh <<'SH'
#!/bin/bash
set -euo pipefail
for iface in flannel-wg flannel.1 cni0; do
  iptables -C INPUT -i "$iface" -p udp --dport 41641 -j DROP 2>/dev/null \
    || iptables -I INPUT -i "$iface" -p udp --dport 41641 -j DROP
  iptables -C OUTPUT -o "$iface" -p udp --dport 41641 -j DROP 2>/dev/null \
    || iptables -I OUTPUT -o "$iface" -p udp --dport 41641 -j DROP
  iptables -C OUTPUT -o "$iface" -p udp --sport 41641 -j DROP 2>/dev/null \
    || iptables -I OUTPUT -o "$iface" -p udp --sport 41641 -j DROP
done
SH
chmod +x /usr/local/sbin/block-tailscale-on-flannel.sh
cat >/usr/local/sbin/fix-overlay-mss.sh <<'SH'
#!/bin/bash
set -euo pipefail
ip link set dev tailscale0 mtu 1200 2>/dev/null || true
for iface in tailscale0 flannel-wg; do
  iptables -t mangle -C POSTROUTING -o "$iface" -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1100 2>/dev/null \
    || iptables -t mangle -I POSTROUTING -o "$iface" -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1100
  iptables -t mangle -C PREROUTING -i "$iface" -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1100 2>/dev/null \
    || iptables -t mangle -I PREROUTING -i "$iface" -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1100
done
SH
chmod +x /usr/local/sbin/fix-overlay-mss.sh
/usr/local/sbin/block-tailscale-on-flannel.sh
/usr/local/sbin/fix-overlay-mss.sh

systemctl is-active k3s-agent
echo "Join attempted. On CP: kubectl get nodes -o wide"
