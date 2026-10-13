# RustDesk MCP — User Tutorials

## 1. Getting Started: First Connection

### Prerequisites

Before you can connect to a remote machine, both computers need:
1. **RustDesk installed** on both the local and remote machines (download from rustdesk.com)
2. **Network connectivity** between the two machines (both on the internet or same LAN)
3. **The remote machine's RustDesk ID** (a 9-10 digit number shown in the RustDesk window)
4. **A password** set on the remote machine for unattended access

### Step 1: Check Your Local RustDesk Status

Before attempting any connection, verify that RustDesk is running on your local machine:

```
Use the tool: get_rustdesk_status()
```

This returns whether RustDesk is installed, running, and the current connection count. If mock mode is `true`, RustDesk is not actually installed — the server will return simulated responses.

### Step 2: Get Your Local RustDesk ID

To know what ID others use to connect to you:

```
Use the tool: get_rustdesk_id()
```

Returns your 9-10 digit RustDesk ID. Share this with someone who needs to connect to your machine.

### Step 3: Check the Remote Machine's Availability

Before connecting, verify the peer is reachable. If you have a self-hosted RustDesk server (hbbs/hbbr), you can check via the socket:

```
Use the tool: list_active_sessions()
```

This lists all currently active sessions. If the remote machine is connected to the same RustDesk server and has an active session, it appears here.

### Step 4: Connect to the Remote Machine

Once you have the peer's RustDesk ID and password:

```
Use the tool: connect_to_peer(peer_id="123456789", password="mypassword")
```

The connection may take several seconds to establish. The response includes a `session_id` — save this if you want to track this specific connection for later disconnection or file transfers.

For better session tracking, assign a custom session ID:

```
Use the tool: connect_to_peer(peer_id="123456789", password="mypassword", session_id="office-pc-morning")
```

The connection stays active until you explicitly disconnect it. While connected, you can transfer files, take screenshots, or monitor the remote machine.

### Step 5: Disconnect When Done

When you finish your remote session:

```
Use the tool: disconnect_peer(session_id="office-pc-morning")
```

To disconnect all active sessions at once:

```
Use the tool: disconnect_peer()
```

## 2. Connecting to a Peer — Tutorial

### Connection Workflow

The recommended workflow for establishing a reliable connection:

1. **Verify installation**: `check_rustdesk_installation()` — confirms RustDesk is installed and the executable path is valid
2. **Check service status**: `get_rustdesk_status()` — confirms RustDesk is running
3. **Get your ID**: `get_rustdesk_id()` — useful when the remote user asks for your ID
4. **Look up the peer**: `get_address_book()` — find the peer's ID if you've saved it before
5. **Connect**: `connect_to_peer(peer_id="...", password="...")`

### Connection via Address Book

If you've previously saved the peer in your address book:

```
First: get_address_book()
Find the peer's ID from the entries.
Then: connect_to_peer(peer_id="987654321", password="their-password")
```

### Connection with Custom Session Labels

For tracking multiple concurrent connections:

```
First connection: connect_to_peer(peer_id="111111111", password="pass1", session_id="server-a")
Second connection: connect_to_peer(peer_id="222222222", password="pass2", session_id="server-b")
```

Each session is tracked independently. The SessionManager keeps history, so you can audit when sessions were created, connected, and disconnected.

### Disconnecting Specific Sessions

```
Disconnect first: disconnect_peer(session_id="server-a")
Disconnect all: disconnect_peer()
```

## 3. Transferring Files — Tutorial

### File Transfer Overview

RustDesk MCP's `transfer_file` tool uses a multi-strategy fallback chain:

1. **RustDesk++ fork API** (fastest, on port 10806) — preferred for headless transfers
2. **RustDesk++ fork CLI** (`--send-file` / `--recv-file`) — works via relay server
3. **Stock RustDesk CLI** (`--file-transfer`) — requires v1.2.0+
4. **RustDesk Pro API** — if `RUSTDESK_API_URL` is configured

If none of these paths work, the tool returns actionable suggestions (SCP/SFTP alternatives, upgrade instructions).

### Uploading a File (Local to Remote)

To send a file from your computer to the remote machine:

```
Use the tool: transfer_file(
    local_path="C:\\Users\\me\\documents\\report.pdf",
    remote_path="C:\\Users\\remote\\Desktop\\",
    direction="upload",
    peer_id="123456789"
)
```

The `peer_id` is required for the fork CLI transfer path. The `local_path` must be an absolute path to an existing file on your machine. The `remote_path` is the destination directory or file path on the remote machine.

### Downloading a File (Remote to Local)

To receive a file from the remote machine:

```
Use the tool: transfer_file(
    local_path="C:\\Users\\me\\downloads\\",
    remote_path="C:\\Users\\remote\\documents\\backup.zip",
    direction="download",
    peer_id="123456789"
)
```

Here, `local_path` is where the downloaded file will be saved on your machine, and `remote_path` is the file to download from the remote machine.

### File Transfer with Session Tracking

If you have an active session, you can associate the transfer with it:

```
Use the tool: transfer_file(
    local_path="C:\\data\\config.json",
    remote_path="/home/user/config.json",
    direction="upload",
    session_id="office-pc-morning",
    peer_id="123456789"
)
```

The session manager updates the session status to `file_transfer_completed` or `file_transfer_failed` when the transfer finishes.

### Comparing and Syncing Folders

Before bulk transfers, compare folders to see what needs updating:

```
Use the tool: compare_folders(
    local_dir="C:\\project\\src",
    remote_dir="/home/user/project/src",
    session_id="sess_123"
)
```

This returns five categories: files only in local, only in remote, size mismatches, newer on local, newer on remote, and identical files. Use this to decide what needs transferring.

To sync a folder (preview first):

```
Dry run (recommended first):
sync_folder(local_dir="./configs", remote_dir="/etc/configs", direction="to_remote", dry_run=True, peer_id="123456789")

Then actually transfer:
sync_folder(local_dir="./configs", remote_dir="/etc/configs", direction="to_remote", dry_run=False, peer_id="123456789")
```

### File Transfer Troubleshooting

**Problem**: `error_type="not_implemented"` — File transfer not available.
**Solutions**:
- Install the rustdesk++ fork which has headless file transfer support
- Use the RustDesk GUI to drag-and-drop files between remote desktop windows
- Use SCP or SFTP as an alternative: `scp file.txt user@remote:/path/`
- Configure `RUSTDESK_API_URL` pointing to a RustDesk Pro API server
- Ensure the fork API server is running: `rustdesk --api-server 10806`

**Problem**: Transfer fails with timeout.
**Solutions**:
- Verify both machines are online and can reach each other
- Check if the relay server (hbbr) is running
- Reduce file size or use compression before transfer
- Ensure firewalls allow RustDesk traffic on ports 21116-21119

## 4. Taking Screenshots — Tutorial

### Requirements

Screenshots require one of:
- **RustDesk CLI v1.2.0+** with `--screenshot` support
- **RustDesk Pro API server** with screenshot capability

Without these, the tool returns `error_type="not_implemented"` with upgrade suggestions.

### Basic Screenshot

```
Use the tool: take_screenshot()
```

This captures the remote desktop and saves to an auto-named file. The response includes the save path.

### Screenshot with Custom Path

```
Use the tool: take_screenshot(save_path="C:\\screenshots\\error_state.png")
```

Use a descriptive save path to organize your screenshots by purpose.

### Screenshot in a Session Context

```
Use the tool: take_screenshot(save_path="C:\\evidence\\bug_report.png", session_id="office-pc-morning")
```

The session manager records that a screenshot was taken during this session.

### Screenshot Workflow for Troubleshooting

A typical troubleshooting workflow:

```
1. Check if RustDesk is running:
   get_rustdesk_status()

2. List active sessions to confirm connection:
   list_active_sessions()

3. Take a screenshot of the issue:
   take_screenshot(save_path="C:\\screenshots\\issue_2026-07-14.png")

4. Transfer the screenshot back:
   transfer_file(
       local_path="C:\\screenshots\\issue_2026-07-14.png",
       remote_path="/home/tech/screenshots/",
       direction="upload",
       peer_id="123456789"
   )

5. Disconnect when done:
   disconnect_peer()
```

## 5. Recording Sessions — Tutorial

### Current Limitations

RustDesk's CLI does not support screen recording commands. The `start_recording` and `stop_recording` tools will return `error_type="not_implemented"` with suggestions. Screen recording must be done through the RustDesk GUI application.

### Workarounds

**Option A: RustDesk GUI**
Open the RustDesk GUI application, connect to the remote machine, and use the built-in recording controls in the toolbar.

**Option B: OBS Studio**
Use OBS Studio (free, open-source) to capture the RustDesk window:
1. Open OBS Studio
2. Add a Window Capture source targeting the RustDesk window
3. Click Start Recording

**Option C: Third-party tools**
Use dedicated screen recording software (ShareX, Snagit, etc.) targeted at the RustDesk viewer window.

## 6. Monitoring Resources — Tutorial

### Quick System Check

For a one-shot snapshot of the remote system:

```
Use the tool: monitor_resources(duration_seconds=10, interval=5.0)
```

This samples CPU, memory, disk, and network every 5 seconds for 10 seconds (2 samples).

### Extended Monitoring

To watch system performance over time (e.g., while running a task on the remote machine):

```
Use the tool: monitor_resources(duration_seconds=300, interval=10.0)
```

This runs for 5 minutes, taking a sample every 10 seconds (30 samples total). The response includes both individual measurements and summary statistics.

### Understanding the Summary

The summary includes:

```
CPU: avg, max, min percentage across all samples
Memory: avg, max, min percentage across all samples
Network: total bytes sent/received during the monitoring period
```

High CPU or memory in the summary indicates resource contention on the remote machine.

### Connection Quality Check

For a quick check of network utilization (not RustDesk per-connection quality, but system-wide counters):

```
Use the tool: get_connection_quality()
```

This returns bytes sent/recv, packets sent/recv, error counts, and drop counts. Use it to diagnose whether the network is saturated, dropping packets, or experiencing errors.

### Monitoring Workflow for Performance Diagnosis

```
1. Quick system check:
   monitor_resources(duration_seconds=30, interval=3.0)

2. Check network quality:
   get_connection_quality()

3. If CPU is high, check processes via the remote system tools

4. Run extended monitor while performing a task:
   monitor_resources(duration_seconds=120, interval=5.0)

5. Compare before/after metrics to identify bottlenecks
```

## 7. Managing the Address Book — Tutorial

### Viewing Saved Peers

To see all peers you've saved:

```
Use the tool: get_address_book()
```

Entries include the RustDesk ID, alias (human-readable name), note, tags, and last used timestamp. If the address book is empty or the file doesn't exist, the tool returns an empty list.

### Adding a New Peer

Save a frequently-accessed remote machine:

```
Basic: add_address_book_entry(peer_id="123456789", alias="Office Workstation")

With details: add_address_book_entry(
    peer_id="987654321",
    alias="Home Server",
    note="Ubuntu 24.04, in living room",
    tags=["linux", "server", "home"]
)
```

Tags help categorize peers for filtering. Use tags like `windows`, `linux`, `server`, `work`, `home`, `urgent`, etc.

### Updating a Peer

To change an existing entry's alias, note, or tags:

```
Update alias only: update_address_book_entry(peer_id="123456789", alias="New Office PC")

Update everything: update_address_book_entry(
    peer_id="123456789",
    alias="New Office PC",
    note="Moved to 3rd floor",
    tags=["windows", "work"]
)
```

Fields you omit are preserved from the existing entry.

### Removing a Peer

To delete an entry you no longer need:

```
Use the tool: remove_address_book_entry(peer_id="123456789")
```

### Full Address Book Workflow

```
1. Add frequently-used machines:
   add_address_book_entry(peer_id="111111", alias="Main Server")
   add_address_book_entry(peer_id="222222", alias="Backup Server", tags=["linux"])

2. Before connecting, check the book:
   book = get_address_book()
   # Find the peer's ID

3. Connect using the saved entry:
   connect_to_peer(peer_id="111111", password="admin123")

4. Update notes after the session:
   update_address_book_entry(peer_id="111111", note="Last connected to fix logrotate")

5. Clean up stale entries:
   remove_address_book_entry(peer_id="222222")
```

## 8. Wake-on-LAN — Tutorial

### Prerequisites

Wake-on-LAN requires:
- The **liaison machine** (the one running this MCP server) must be on the **same local network** as the target machine
- **WOL enabled in BIOS/UEFI** on the target machine (sometimes called "Wake on LAN", "Power On by PCIe", or "PME Event Wake Up")
- **Network driver configured** to allow magic packets (check "Wake on Magic Packet" in the network adapter properties on Windows)
- The target must be **powered off gracefully** (not a hard shutdown) for WOL to work

### Sending a Magic Packet

Basic usage (works for most local network setups):

```
Use the tool: wake_on_lan(mac_address="aa:bb:cc:dd:ee:ff")
```

This sends the magic packet to `255.255.255.255:9` (limited broadcast on UDP port 9). The target machine's NIC should detect this packet and wake the system.

### With Specific Broadcast Address

For more reliable delivery, use the subnet broadcast:

```
Use the tool: wake_on_lan(
    mac_address="aa:bb:cc:dd:ee:ff",
    broadcast_ip="192.168.1.255",
    port=9
)
```

Use the subnet broadcast instead of the limited broadcast when:
- You have multiple network interfaces
- You want to be sure the packet reaches a specific subnet
- You're on a VLAN or segmented network

### Cross-Subnet WOL

If you need to wake a machine on a different subnet, use that subnet's broadcast address:

```
Use the tool: wake_on_lan(
    mac_address="AA-BB-CC-DD-EE-FF",
    broadcast_ip="10.0.1.255",
    port=7
)
```

Port 7 (echo) may work where port 9 (discard) is blocked by network equipment.

### Full WOL Workflow

```
1. Wake the machine:
   wake_on_lan(mac_address="aa:bb:cc:dd:ee:ff", hostname="goliath")

2. Wait for it to boot (30-60 seconds):
   The magic packet triggers the power-on sequence. BIOS POST, then OS boot.

3. Wait until the RustDesk service starts on the target
   (depends on startup configuration)

4. Check if it's reachable:
   # You may need to wait another 10-20 seconds for RustDesk service

5. Connect:
   connect_to_peer(peer_id="123456789", password="boot-password")
```

### MAC Address Formats

The tool accepts any of these formats:
- `aa:bb:cc:dd:ee:ff` (colon-separated lowercase)
- `AA:BB:CC:DD:EE:FF` (colon-separated uppercase)
- `AA-BB-CC-DD-EE-FF` (dash-separated)
- `aabb.ccdd.eeff` (Cisco-style dotted)

### Wake-on-LAN Troubleshooting

**Problem**: Machine does not wake up.
**Solutions**:
- Verify WOL is enabled in BIOS/UEFI (most common cause)
- Check that the network adapter is configured to allow magic packets
- In Windows: Device Manager → Network Adapter → Properties → Power Management → "Allow this device to wake the computer" must be checked
- In Windows: Device Manager → Network Adapter → Advanced → "Wake on Magic Packet" must be enabled
- Verify the power cable is connected (WOL may not work on battery)
- Try port 7 instead of port 9
- Try the specific subnet broadcast instead of 255.255.255.255
- Use a WOL testing tool (e.g., Depicus WOL) to verify the target responds

## 9. Checking Installation and Status — Tutorial

### Installation Check

```
Use the tool: check_rustdesk_installation()
```

Returns:
- `installed`: whether the executable was found at `RUSTDESK_PATH`
- `running`: whether a `rustdesk` process is currently running
- `executable_path`: resolved path to rustdesk.exe
- `config_dir`: resolved config directory path
- `mock_mode`: true if no real RustDesk was detected

### Service Status

```
Use the tool: get_rustdesk_status()
```

Returns connection count, service status string, and mock mode indicator. Use this to confirm the service is healthy before any connection attempt.

### Full Detailed Status

For a complete picture of the RustDesk environment:

```
Use the tool: get_detailed_rustdesk_status()
```

This combines local ID, active sessions, address book, network configuration (IP addresses, gateway, DNS), and performance metrics (CPU, memory, disk) in one response. Use this for a comprehensive health check.

### Automated Health Check Workflow

```
1. Quick check:
   result = check_rustdesk_installation()

2. If not installed, attempt to locate or guide installation

3. If installed but not running, start the RustDesk service

4. Get detailed status:
   full_status = get_detailed_rustdesk_status()

5. Proceed with remote support
```

## 10. Using Prefab UI Cards — Tutorial

The server provides four rich in-chat Prefab cards that render structured UI in supported MCP hosts. These cards give you a visual overview without needing to parse raw JSON.

### Service Status Card

Display a rich card with the current RustDesk service status, version, connection count, and installation state:

```
Use the tool: show_rustdesk_status_card()
```

The card shows:
- Version string
- Service status (Online/Offline badge)
- Connection count badge
- Mock mode indicator
- Installation status

This is equivalent to calling `get_rustdesk_status()` but presented as a visual card.

### Active Sessions Card

View all active sessions rendered as individual nested cards:

```
Use the tool: show_active_sessions_card()
```

Each session card shows:
- Session ID
- Connection type (tracked_session, network_detected, log_detected)
- Remote IP address
- Connection status

Up to 10 sessions are shown. If no sessions are active, it displays "No active sessions".

### Address Book Card

Browse saved peer connections in a compact card layout:

```
Use the tool: show_address_book_card()
```

Shows entries with peer IDs, aliases, and usernames. Up to 20 entries are displayed. Use this for a quick visual scan of your saved connections before initiating a remote session.

### Installation Status Card

Check the RustDesk installation status with visual badges:

```
Use the tool: show_installation_card()
```

Shows:
- Installation badge (Installed/Not installed) with color coding
- Service status (Running/Stopped) badge
- Executable path
- Config directory path
- Mock mode indicator

### When to Use Prefab Cards vs JSON Tools

- **Use Prefab cards** when you want a quick visual overview during a conversation or when presenting status to a user
- **Use JSON tools** when you need the raw data for programmatic processing, comparison, or integration with other tools

## 11. Viewing Active Sessions — Tutorial

### Basic Session List

```
Use the tool: list_active_sessions()
```

The tool attempts multiple methods to detect sessions:

1. **Socket communication** (primary): direct TCP to hbbs:21116 — fastest, least reliable in practice
2. **API server** (fallback): queries `/api/sessions` or `/api/audit/conn` on the RustDesk Pro API
3. **Session Manager** (final fallback): shows locally tracked sessions from `connect_to_peer` calls

### Enhanced Detection

The tool also enhances results by:
- Scanning `psutil.net_connections()` for ESTABLISHED connections on RustDesk ports (21116-21119)
- Parsing the connection manager log file (`RustDesk_rCURRENT.log`) for recent connection activity
- Listing running `rustdesk` processes as fallback

### Understanding Session Types

- `tracked_session`: Session managed by this MCP server's SessionManager — most reliable
- `network_detected`: Found via network port scan — may be partial information
- `log_detected`: Found in RustDesk connection manager logs — recent but possibly historical
- `process_only`: RustDesk process is running but no confirmed remote sessions

### Session Management Best Practices

1. Always use custom `session_id` labels on `connect_to_peer` for easy identification
2. Call `list_active_sessions()` before connecting to avoid duplicate connections
3. Call `disconnect_peer()` after completing remote work to free resources
4. Use `get_connection_quality()` during active sessions to monitor performance

## 12. Troubleshooting Common Issues — Tutorial

### RustDesk Not Found (Mock Mode)

**Symptom**: All status tools return `mock_mode: true`. `check_rustdesk_installation()` shows `installed: false`.

**Causes**:
- RustDesk is not installed on this machine
- The `RUSTDESK_PATH` environment variable points to the wrong location
- The auto-detection logic failed to find the executable

**Solutions**:
1. Install RustDesk from https://rustdesk.com
2. Set `RUSTDESK_PATH` to the full path of `rustdesk.exe`
3. Run `check_rustdesk_installation()` again to verify
4. If using the portable version, ensure the exe is in a standard location

### Cannot Connect to Peer

**Symptom**: `connect_to_peer()` returns `success: false`.

**Causes**:
- Incorrect peer ID (wrong number or typo)
- Wrong password
- Remote machine is offline or has no network connectivity
- Remote machine's RustDesk service is not running
- Firewall blocking RustDesk traffic (ports 21116-21119)
- Both machines are not connected to the same RustDesk server (public or self-hosted)

**Solutions**:
1. Verify the peer ID with the remote user — it is a 9-10 digit number
2. Confirm the password matches the one set on the remote machine
3. Check that the remote machine is powered on and connected to the internet
4. Verify the remote machine's RustDesk service is running (check system tray)
5. Ensure UDP ports 21116 and TCP ports 21117-21119 are open in both firewalls
6. For self-hosted servers, verify hbbs and hbbr are running on both ends
7. Test connectivity using the RustDesk GUI application independently

### File Transfer Fails

**Symptom**: `transfer_file()` returns `error_type: "not_implemented"`.

**Causes**:
- Stock RustDesk CLI without the rustdesk++ fork
- RustDesk CLI version is older than 1.2.0
- No API server configured via `RUSTDESK_API_URL`
- Fork API server not running (required for headless transfers)

**Solutions**:
1. Install the rustdesk++ fork which includes `--send-file` and `--recv-file` support
2. Start the fork API server: `rustdesk --api-server 10806` on the liaison machine
3. Configure `RUSTDESK_API_URL` pointing to a RustDesk Pro server
4. Use the RustDesk GUI to drag-and-drop files during a remote session
5. Use SCP or SFTP as an alternative for file transfer

### Screenshot Not Available

**Symptom**: `take_screenshot()` returns `error_type: "not_implemented"`.

**Causes**:
- RustDesk CLI version is older than 1.2.0
- The `--screenshot` flag is not supported in the installed build
- No API server configured

**Solutions**:
1. Update RustDesk to the latest version (v1.2.0+ required)
2. Use the RustDesk GUI to capture screenshots manually (Ctrl+Shift+S shortcut)
3. Configure `RUSTDESK_API_URL` for API-based screenshot capture
4. Use the remote machine's own screenshot tools (Snipping Tool, PrtScn)

### Wake-on-LAN Does Not Wake the Machine

**Symptom**: `wake_on_lan()` returns `success: true` but the target machine does not power on.

**Causes**:
- WOL is disabled in the target machine's BIOS/UEFI settings
- The network adapter driver does not allow magic packets
- The machine was shut down via hard power-off (WOL requires graceful shutdown)
- The broadcast IP is wrong (cross-subnet without proper broadcast address)
- The liaison machine is not on the same network segment
- A switch or router between the machines does not forward broadcast packets

**Solutions**:
1. Enter the target machine's BIOS/UEFI and enable WOL (look for "Wake on LAN", "Power On by PCIe", "PME Event Wake Up")
2. On Windows: Open Device Manager, find the network adapter, go to Power Management tab, check "Allow this device to wake the computer" and "Only allow a magic packet to wake the computer"
3. On Linux: Install `ethtool` and run `sudo ethtool -s eth0 wol g` to enable WOL via magic packet
4. Verify the target machine was shut down gracefully (Start Menu > Shut Down, not holding the power button)
5. Use the specific subnet broadcast address (e.g., 192.168.1.255) instead of the limited broadcast (255.255.255.255)
6. Try sending the magic packet from a different machine on the same subnet to isolate the issue
7. Use a WOL testing utility (e.g., Depicus WOL, NirSoft WakeMeOnLan) to confirm the target responds
8. After sending the packet, wait a full 60 seconds before assuming it failed — some machines take longer to POST

### Connection Quality is Poor

**Symptom**: Remote desktop is laggy, slow to respond, or frequently disconnects.

**Diagnosis**:
1. Run `get_connection_quality()` to check system-level network metrics
2. Look for high error counts (`errors_in`, `errors_out`) or dropped packets (`drop_in`, `drop_out`)
3. Run `monitor_resources(duration_seconds=60, interval=5.0)` to check CPU and memory on the liaison machine
4. Compare `bytes_sent` and `bytes_recv` to see if the connection is symmetric

**Solutions**:
1. Switch both machines to a wired network connection instead of Wi-Fi
2. Reduce remote desktop quality settings in the RustDesk GUI (lower resolution, color depth, or frame rate)
3. Check for bandwidth-intensive applications running on either machine
4. Verify the relay server (hbbr) is not overloaded
5. Configure a direct peer-to-peer connection instead of relay if possible

### Address Book Read/Write Errors

**Symptom**: Address book tools return errors or empty entries.

**Causes**:
- The address book file does not exist (first-time use)
- Permission denied reading or writing `addrbook.toml`
- The config directory is not correctly configured
- The address book file is in an unexpected format

**Solutions**:
1. Run `get_address_book()` to see if any entries exist — if `file_exists` is false, no address book has been created yet
2. Check `RUSTDESK_CONFIG_DIR` points to the correct RustDesk config directory
3. Open the RustDesk GUI and add a peer — this creates the `addrbook.toml` file
4. If `access_denied` is true, run the MCP server with appropriate permissions
5. Verify the address book file format: RustDesk uses TOML format with a `[peers]` section

## 13. Automation and Scripting — Tutorial

The RustDesk MCP server is designed to be called programmatically by AI agents. You can chain multiple tool calls to automate common remote support scenarios.

### Automating Peer Status Checks

To periodically check if a peer is online without connecting:

```
1. Get the peer's ID from the address book:
   get_address_book()

2. Check your own service readiness:
   get_rustdesk_status()

3. List active sessions to see if anyone is connected:
   list_active_sessions()

4. Get detailed network health:
   get_connection_quality()
```

### Automating File Sync Between Machines

For a regular sync between a local config directory and a remote server:

```
1. Compare folders to see what changed:
   compare_folders(local_dir="/opt/app/config", remote_dir="/srv/app/config")

2. If there are differences, run a dry-run sync:
   sync_folder(local_dir="/opt/app/config", remote_dir="/srv/app/config", direction="to_remote", dry_run=true, peer_id="123456789")

3. Execute the sync:
   sync_folder(local_dir="/opt/app/config", remote_dir="/srv/app/config", direction="to_remote", dry_run=false, peer_id="123456789")
```

### Automating Wake-Up and Connect

To wake a machine and connect once it is ready:

```
1. Send the WOL magic packet:
   wake_on_lan(mac_address="aa:bb:cc:dd:ee:ff", hostname="backup-server")

2. Wait 60 seconds for the machine to boot

3. Attempt connection (may need retries):
   connect_to_peer(peer_id="555666777", password="batch-password", session_id="automated-backup")

4. Run monitoring or file operations

5. Disconnect when done:
   disconnect_peer(session_id="automated-backup")
```

### Automating Diagnostic Collection

To collect a full system diagnostic from a remote machine:

```
1. Connect:
   connect_to_peer(peer_id="123456789", password="diag-password", session_id="diag-collect")

2. Take screenshots of current state:
   take_screenshot(save_path="/tmp/diag_before.png", session_id="diag-collect")

3. Run performance monitoring:
   monitor_resources(duration_seconds=120, interval=5.0, session_id="diag-collect")

4. Check network quality:
   get_connection_quality(session_id="diag-collect")

5. Transfer collected diagnostics back:
   # (Upload from remote to local using transfer_file with direction="download")

6. Disconnect:
   disconnect_peer(session_id="diag-collect")
```

## 14. Complete Remote Support Workflow — Tutorial

A comprehensive workflow for providing remote support to a colleague:

```
Phase 1 — Preparation (on the supporter's machine):
1. Verify RustDesk is installed and running:
   check_rustdesk_installation()
   get_rustdesk_status()

2. Get your own RustDesk ID to share if needed:
   get_rustdesk_id()

Phase 2 — Connection (after receiving peer's ID and password):
3. Add the peer to your address book for future reference:
   add_address_book_entry(peer_id="123456789", alias="Colleague PC", tags=["remote-support"])

4. Connect with a tracking session:
   connect_to_peer(peer_id="123456789", password="temp-password", session_id="support-jul14")

5. Verify the connection is established:
   list_active_sessions()
   get_connection_quality()

Phase 3 — Diagnostics:
6. Take a screenshot to see what the user is looking at:
   take_screenshot(save_path="C:\\support\\initial_state.png", session_id="support-jul14")

7. Run a quick resource check:
   monitor_resources(duration_seconds=30, interval=5.0, session_id="support-jul14")

Phase 4 — Remediation:
8. Transfer any needed files (patches, tools, configs):
   transfer_file(local_path="C:\\tools\\fix_tool.exe", remote_path="C:\\Users\\colleague\\Downloads\\", direction="upload", peer_id="123456789")

9. If the remote machine needs to be rebooted and supports WOL, note its MAC:
   # After the user reboots, wake it if needed:
   wake_on_lan(mac_address="aa:bb:cc:dd:ee:ff", hostname="colleague-pc")

10. After reboot, reconnect and verify:
    connect_to_peer(peer_id="123456789", password="temp-password", session_id="support-jul14-part2")

Phase 5 — Wrap-up:
11. Take an after screenshot for documentation:
    take_screenshot(save_path="C:\\support\\after_fix.png", session_id="support-jul14")

12. Update the address book entry:
    update_address_book_entry(peer_id="123456789", note="Support session Jul 14 — applied fix_tool.exe")

13. Disconnect:
     disconnect_peer(session_id="support-jul14")
     disconnect_peer(session_id="support-jul14-part2")
```

## 15. Folder Sync, Remote Input, and Shutdown — Tutorial

### Comparing and syncing folders

`compare_folders` diffs a local directory against a remote one (recursive,
exclude patterns, size/mtime comparison) without moving any bytes. When the
diff shows drift, `sync_folder` pushes or pulls only the missing, newer, or
diverged files, with `dry_run=true` for a safe preview and a SHA-256 manifest
written after every real run. `verify_file_integrity` then cross-checks a local
SHA-256 digest against the remote size, because the fork protocol exposes no
remote-hash primitive. Typical order: compare, dry-run sync, real sync, verify.

### Driving the remote GUI

`remote_click`, `remote_type`, and `send_remote_keys` act on the active RustDesk
session window on the liaison machine (left/right/middle clicks, double-click,
chords like ctrl+c or alt+F4). They are rate-limited to one action per
RUSTDESK_CONTROL_MIN_INTERVAL (default 0.5 s), audit-logged, and killed entirely
by RUSTDESK_CONTROL_ENABLED=false. Prefer them for small GUI nudges only; bulk
work belongs in file sync or the remote shell, not simulated keystrokes.

### Shutting down the server

`rustdesk_shutdown(confirm=True)` and POST /api/shutdown stop the MCP server
itself (not the remote machine): the call returns immediately and the process
exits about 500 ms later so in-flight responses flush. The fleet launcher calls
this before NSSM restarts. Never call it mid-workflow unless you intend to end
the session.

1. Always use custom `session_id` labels on `connect_to_peer` for easy identification
2. Call `list_active_sessions()` before connecting to avoid duplicate connections
3. Call `disconnect_peer()` after completing remote work to free resources
4. Use `get_connection_quality()` during active sessions to monitor performance
