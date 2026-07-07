# RustDesk MCP -- Remote Support Skill

## Purpose

This server provides remote desktop management through RustDesk. You can check device status, connect to peers, manage address books, transfer files, capture screenshots, monitor resources, and wake sleeping machines on the LAN.

## Available Tools

### Status & Discovery
- `get_rustdesk_status` -- Service status, connection count, mock mode check
- `get_detailed_rustdesk_status` -- Local ID, active sessions, address book, network config, performance metrics
- `check_rustdesk_installation` -- Installation verification, service state, path validation
- `get_rustdesk_id` -- Local RustDesk ID for incoming connections

### Connection Management
- `list_active_sessions` -- Active sessions via socket/API/log parsing
- `get_address_book` -- Saved peer connections
- `connect_to_peer(peer_id, password, session_id?)` -- Connect to a remote machine
- `disconnect_peer(session_id?)` -- Disconnect sessions

### File Transfer
- `transfer_file(local_path, remote_path, direction="upload", session_id?)` -- Upload/download files
- `list_remote_files(remote_path="/", session_id?)` -- Browse remote directories

### Screen Capture
- `take_screenshot(save_path?, session_id?)` -- Capture remote desktop screenshot
- `start_recording(save_path?, session_id?)` -- Start recording session
- `stop_recording(session_id?)` -- Stop recording

### Monitoring
- `monitor_resources(duration_seconds=60, interval=5.0, session_id?)` -- CPU/memory/disk/network over time
- `get_connection_quality(session_id?)` -- Network metrics

### Network
- `wake_on_lan(mac_address, broadcast_ip?, port?, hostname?)` -- Wake sleeping machine on LAN

## Best Practices

1. **Always check status first**: Call `get_rustdesk_status()` before any operation to confirm RustDesk is running.
2. **Session tracking**: Use `session_id` on `connect_to_peer` to track sessions. Close them with `disconnect_peer`.
3. **File transfers**: Transfer direction must be "upload" (local → remote) or "download" (remote → local). File transfers require RustDesk CLI v1.2.0+ or an API server. Falls back to SCP/SFTP suggestions.
4. **Wake-on-LAN**: After sending a magic packet, wait 30-60 seconds for the target to boot before attempting `connect_to_peer`.
5. **Monitoring**: `monitor_resources` is stateful -- it runs for the specified duration and returns all samples. Use lower `duration_seconds` for quick checks.

## Configuration

- `RUSTDESK_PATH` -- Path to rustdesk.exe (auto-detected)
- `RUSTDESK_API_URL` -- Pro API server URL (optional)
- `RUSTDESK_API_KEY` -- API authentication key
- `MCP_PORT` -- HTTP transport port (default 10805)
