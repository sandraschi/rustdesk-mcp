"""Prefab UI cards for RustDesk MCP status and list tools."""

from fastmcp import FastMCP
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Badge,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Div,
    Heading,
    Row,
    Separator,
    Text,
)

from ..services.rustdesk_service import RustDeskService

_READ_ONLY = {"readonly": True}


def register_prefab_cards(mcp: FastMCP, service: RustDeskService) -> None:
    """Register all Prefab card tools on the given FastMCP instance."""

    @mcp.tool(app=True, annotations=_READ_ONLY)
    async def show_rustdesk_status_card() -> PrefabApp:
        """Show RustDesk service status as a rich card.

        ## Return Format
        PrefabApp with service status, connections, version.

        ## Examples
        await show_rustdesk_status_card()
        """
        status = await service.get_status()
        service_status = status.get("service_status", "unknown")
        mock = status.get("mock_mode", True)
        version = status.get("version", "?")
        conns = status.get("connections", 0)
        installed = status.get("installed", False)

        status_badge = Badge(
            text="Online" if installed and not mock else "Offline",
            variant="success" if installed and not mock else "destructive",
        )
        conn_badge = Badge(
            text=str(conns),
            variant="default" if conns > 0 else "secondary",
        )

        view = Div(
            children=[
                Heading("RustDesk Status"),
                Div(
                    children=[
                        Row(label="Version", value=version),
                        Row(label="Service", value=service_status),
                        Row(label="Status", value=status_badge),
                        Row(label="Connections", value=conn_badge),
                        Row(label="Mock mode", value="Yes" if mock else "No"),
                        Row(label="Installed", value="Yes" if installed else "No"),
                    ]
                ),
            ]
        )
        return PrefabApp(view=view, title="RustDesk Status")

    @mcp.tool(app=True, annotations=_READ_ONLY)
    async def show_active_sessions_card() -> PrefabApp:
        """Show active RustDesk sessions as a rich card.

        ## Return Format
        PrefabApp with session list and connection details.

        ## Examples
        await show_active_sessions_card()
        """
        result = await service.list_active_sessions()
        sessions = result.get("sessions", [])

        cards = []
        for s in sessions[:10]:
            conn_type = s.get("connection_type", "unknown")
            remote_ip = s.get("remote_ip", s.get("peer_addr", "?"))
            status = s.get("status", "?")
            session_id = s.get("session_id", s.get("connection_id", "?"))

            cards.append(
                Card(
                    children=[
                        CardHeader(children=[CardTitle(f"Session {session_id}")]),
                        CardContent(
                            children=[
                                Row(label="Type", value=conn_type),
                                Row(label="Remote", value=remote_ip),
                                Row(label="Status", value=status),
                            ]
                        ),
                    ]
                )
            )

        if not cards:
            cards.append(Text("No active sessions"))

        view = Div(
            children=[
                Heading(f"Active Sessions ({len(sessions)})"),
                Separator(),
                *cards,
            ]
        )
        return PrefabApp(view=view, title="Active Sessions")

    @mcp.tool(app=True, annotations=_READ_ONLY)
    async def show_address_book_card() -> PrefabApp:
        """Show RustDesk address book entries as a rich card.

        ## Return Format
        PrefabApp with saved peer entries.

        ## Examples
        await show_address_book_card()
        """
        result = await service.get_address_book()
        entries = result.get("entries", [])

        cards = []
        for entry in entries[:20]:
            peer_id = entry.get("id", entry.get("peer_id", "?"))
            alias = entry.get("alias", entry.get("name", ""))
            username = entry.get("username", entry.get("user", ""))

            detail = f"{alias}" if alias else peer_id
            if username:
                detail = f"{detail} ({username})"

            cards.append(Text(detail))

        if not cards:
            cards.append(Text("No address book entries"))

        view = Div(
            children=[
                Heading(f"Address Book ({len(entries)})"),
                Separator(),
                *cards,
            ]
        )
        return PrefabApp(view=view, title="Address Book")

    @mcp.tool(app=True, annotations=_READ_ONLY)
    async def show_installation_card() -> PrefabApp:
        """Show RustDesk installation check details as a rich card.

        ## Return Format
        PrefabApp with install path, config dir, runtime status.

        ## Examples
        await show_installation_card()
        """
        installed = service.is_installed()
        running = service.is_running()
        exe_path = str(service.rustdesk_path) if service.rustdesk_path else "N/A"
        config_dir = str(service.config_dir) if service.config_dir else "N/A"

        install_badge = Badge(
            text="Installed" if installed else "Not installed",
            variant="success" if installed else "destructive",
        )
        run_badge = Badge(
            text="Running" if running else "Stopped",
            variant="success" if running else "secondary",
        )

        view = Div(
            children=[
                Heading("RustDesk Installation"),
                Div(
                    children=[
                        Row(label="Installed", value=install_badge),
                        Row(label="Service", value=run_badge),
                        Row(label="Executable", value=exe_path),
                        Row(label="Config dir", value=config_dir),
                        Row(label="Mock mode", value="Yes" if service.mock_mode else "No"),
                    ]
                ),
            ]
        )
        return PrefabApp(view=view, title="RustDesk Installation")
