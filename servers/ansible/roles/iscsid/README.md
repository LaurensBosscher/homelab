# iscsid Role

Configures the iSCSI daemon for Longhorn distributed storage.

## What it does

1. **Enables and starts** `iscsid`
2. **Auto-restart on failure** — creates a systemd drop-in override so iscsid restarts automatically if it exits unexpectedly (`Restart=on-failure`, 5s delay)
3. **SELinux fix** — applies a custom SELinux module (`local_longhorn`) that grants `dac_override` capability to `iscsid_t`, required by Longhorn on SELinux-enforcing nodes

## Manual restart

If iscsid is in a bad state and the auto-restart hasn't kicked in:

```bash
sudo systemctl restart iscsid
```

Check status with:

```bash
sudo systemctl status iscsid
```
