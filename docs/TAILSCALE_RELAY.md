# hbbs/hbbr on the Tailnet (no public ports)

Goal: Goliath's self-hosted RustDesk rendezvous (hbbs) and relay (hbbr) are
reachable **only over Tailscale**. Nothing RustDesk-shaped listens on the
public internet. The cafe laptop and the iPad join the same tailnet and dial
Goliath's tailnet IP.

Why this instead of port-forwarding 21115-21119 to the world:

- No internet-exposed password auth to brute-force.
- Cafe NAT traversal becomes Tailscale's problem (WireGuard, DERP fallback),
  not your router's.
- The stock iOS client supports a custom ID server, so the iPad works
  unchanged — it just points at a tailnet address.

## Prerequisites

- Tailscale installed and `up` on: Goliath, the cafe laptop, the iPad
  (same tailnet; note Goliath's MagicDNS name and its `100.x.y.z` address
  from `tailscale ip -4`).
- hbbs/hbbr binaries on Goliath (see `install-server.bat` in the
  `sandraschi/rustdesk` fork for the ONSTART scheduled-task setup).
- One shared private key string (`-k`). Empty (`-k ""`) is LAN-discovery
  mode — do **not** use empty on a tailnet shared with other people; set a
  real key.

## 1. Bind hbbs/hbbr to the tailnet

Find Goliath's tailnet address:

```powershell
tailscale ip -4   # e.g. 100.71.22.10
```

Start the servers pinned to it (replace `TS-IP` and `SECRET`):

```powershell
.\hbbs.exe -r TS-IP -k SECRET
.\hbbr.exe -k SECRET
```

`-r` tells hbbs which address to hand out to peers, so clients get routed
back over the tailnet instead of your public IP. If you used
`install-server.bat`, add the same flags to the scheduled-task actions it
creates, then restart the tasks.

Verify locally (hbbs API/probe port + relay):

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 21116
Test-NetConnection -ComputerName 127.0.0.1 -Port 21117
```

## 2. Close the public door

Remove (or never create) the router port-forwards for 21115-21119. Then lock
the Windows firewall so the RustDesk ports only answer the tailnet:

```powershell
# Example: restrict hbbs/hbbr to the Tailscale CGNAT range
New-NetFirewallRule -DisplayName "hbbs tailnet only" -Direction Inbound `
  -LocalPort 21115,21116 -Protocol TCP -RemoteAddress 100.64.0.0/10 -Action Allow
New-NetFirewallRule -DisplayName "hbbr tailnet only" -Direction Inbound `
  -LocalPort 21117 -Protocol TCP -RemoteAddress 100.64.0.0/10 -Action Allow
```

Confirm from outside the tailnet (phone hotspot with Tailscale **off**):
connection to `your-home-ip:21117` must fail.

## 3. Point the clients at the tailnet

In every RustDesk client (including iOS: Settings → ID/Relay server):

| Setting       | Value                          |
|---------------|--------------------------------|
| ID server     | `TS-IP:21116` (Goliath tailnet IP) |
| Relay server  | `TS-IP:21117`                  |
| Key           | same `SECRET` as the servers   |

Test matrix (each should show online in `list_active_sessions` / peer_info):

1. Laptop on home LAN → connects (baseline).
2. Laptop on phone hotspot, Tailscale on → connects via tailnet.
3. Hotspot, Tailscale off → fails (proves no public fallback).

## 4. Point the fork at the tailnet too

The fork resolves its rendezvous from `Config::get_rendezvous_server()` /
`custom-rendezvous-server`, with a hardcoded public fallback when neither is
set (see `get_rendezvous_addr()` in the fork source — it also has known DNS
flakiness, so be explicit):

```powershell
.\rustdesk.exe --option custom-rendezvous-server TS-IP:21116
```

After that, fork CLI (`--peer-info`, `--send-file`, `--list-dir`) and the
`rustdesk-mcp` file/sync tools ride the tailnet with no further config —
they talk to hbbs/hbbr, and hbbs/hbbr only exist on the tailnet now.

## 5. What still doesn't cross the tailnet

- **Wake-on-LAN stays LAN-only.** Magic packets are L2 broadcasts;
  Tailscale does not forward them. If Goliath sleeps, only a box on the
  home LAN (always-on mini-PC via this repo's `wake_on_lan` tool) can wake
  it. From the cafe, Goliath must already be awake.
- **Latency is still Goliath's upload.** The tailnet removes NAT pain, not
  physics. Thin home upload = laggy screen + slow `sync_folder` pushes over
  relay. Prefer direct tailnet paths for bulk file moves (`git`, `scp`
  over `100.x` addresses) and keep RustDesk for GUI-bound moments.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ID does not exist` | Client hitting the wrong hbbs (public fallback) | Check ID-server setting; set `custom-rendezvous-server` explicitly |
| `LICENSE_MISMATCH` / `key mismatch` | `-k` differs between client and server | Re-enter the same key everywhere, restart hbbs/hbbr |
| `Remote desktop is offline` from cafe, fine at home | Tailscale down/expiry on one end | `tailscale status`; re-auth (`tailscale up`), disable key expiry for Goliath in the admin console |
| Slow but connected | Relayed inside WireGuard (double tunnel) or DERP-relayed tailnet | `tailscale status` — look for `direct` vs `relay`; direct is normal and fine |
| Fork CLI hangs on rendezvous | Fork's DNS workaround + default server | Pin `custom-rendezvous-server` to the numeric `100.x` IP, not the MagicDNS name |

## Security notes

- Tailnet ACLs: restrict which devices can reach Goliath's 21115-21117
  (tag-based rules in the Tailscale admin console).
- Turn off key expiry for the always-on nodes (Goliath, liaison mini-PC)
  or they will drop off the tailnet silently.
- The fork's permanent-password auth is unchanged — tailnet membership is
  an additional gate, not a replacement for a strong RustDesk password.
