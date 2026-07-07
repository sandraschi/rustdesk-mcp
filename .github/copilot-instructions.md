## Session Context (RustDesk MCP)

You have access to RustDesk remote desktop management via MCP protocol.

**Before starting, get the lay of the land:**
1. Check RustDesk status: get_rustdesk_status()
2. List saved peers: get_address_book()
3. List active remote sessions: list_active_sessions()

**Key tools:**
- Connect: connect_to_peer(peer_id="...", password="...")
- File transfer: transfer_file(local_path="...", remote_path="...")
- Wake-on-LAN: wake_on_lan(mac_address="aa:bb:cc:dd:ee:ff")
- Resource monitor: monitor_resources(duration_seconds=30)
- Get device ID: get_rustdesk_id()

**At end of work, clean up:**
- Disconnect sessions: disconnect_peer()
- Verify state: list_active_sessions()
