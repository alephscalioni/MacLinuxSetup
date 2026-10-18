#!/usr/bin/env bash
set -euo pipefail
[[ "$EUID" == 0 ]] || { echo 'Use pkexec para instalar as regras RGB.' >&2; exit 1; }
base_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
backup_dir="/var/lib/maclinux-aplicador/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$backup_dir" /etc/udev/rules.d
for rule in 60-openrgb.rules 60-aleph-rgb-smbus.rules; do
    target="/etc/udev/rules.d/$rule"
    [[ ! -f "$target" ]] || cp -a "$target" "$backup_dir/$rule"
    install -m 644 "$base_dir/payload/system/etc/udev/rules.d/$rule" "$target"
done
udevadm control --reload-rules
udevadm trigger --subsystem-match=usb --action=change
udevadm trigger --subsystem-match=hidraw --action=change
udevadm trigger --subsystem-match=i2c-dev --action=change
udevadm settle
