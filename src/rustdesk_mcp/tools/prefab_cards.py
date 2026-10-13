"""Prefab UI cards for RustDesk MCP status and list tools."""

from fastmcp import FastMCP
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Badge,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Component,
    Div,
    Heading,
    Row,
    Separator,
    Text,
)

from ..services.rustdesk_service import RustDeskService

_READ_ONLY = {"readonly": True}


def _kv(label: str, value: str | Component) -> Row:
    """One label/value row. Plain strings become Text; Badges pass through."""
    val: Component = value if isinstance(value, Component) else Text(value)
    return Row(children=[Text(f"{label}:"), val])


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
        service_status = str(status.get("service_status", "unknown"))
        mock = bool(status.get("mock_mode", True))
        version = str(status.get("version", "?"))
        conns = int(status.get("connections", 0) or 0)
        installed = bool(status.get("installed", False))

        rows: list[Component] = [
            _kv("Version", version),
            _kv("Service", service_status),
            _kv(
                "Status",
                Badge(
                    label="Online" if installed and not mock else "Offline",
                    variant="success" if installed and not mock else "destructive",
                ),
            ),
            _kv(
                "Connections",
                Badge(label=str(conns), variant="default" if conns > 0 else "secondary"),
            ),
            _kv("Mock mode", "Yes" if mock else "No"),
            _kv("Installed", "Yes" if installed else "No"),
        ]
        view = Div(children=[Heading(content="RustDesk Status"), Div(children=rows)])
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

        cards: list[Component] = []
        for s in sessions[:10]:
            conn_type = str(s.get("connection_type", "unknown"))
            remote_ip = str(s.get("remote_ip", s.get("peer_addr", "?")))
            status = str(s.get("status", "?"))
            session_id = str(s.get("session_id", s.get("connection_id", "?")))

            rows: list[Component] = [
                _kv("Type", conn_type),
                _kv("Remote", remote_ip),
                _kv("Status", status),
            ]
            cards.append(
                Card(
                    children=[
                        CardHeader(children=[CardTitle(content=f"Session {session_id}")]),
                        CardContent(children=rows),
                    ]
                )
            )

        if not cards:
            cards.append(Text("No active sessions"))

        view = Div(children=[Heading(content=f"Active Sessions ({len(sessions)})"), Separator(), *cards])
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

        cards: list[Component] = []
        for entry in entries[:20]:
            peer_id = str(entry.get("id", entry.get("peer_id", "?")))
            alias = str(entry.get("alias", entry.get("name", "")))
            username = str(entry.get("username", entry.get("user", "")))

            detail = alias if alias else peer_id
            if username:
                detail = f"{detail} ({username})"

            cards.append(Text(detail))

        if not cards:
            cards.append(Text("No address book entries"))

        view = Div(children=[Heading(content=f"Address Book ({len(entries)})"), Separator(), *cards])
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

        rows: list[Component] = [
            _kv(
                "Installed",
                Badge(
                    label="Installed" if installed else "Not installed",
                    variant="success" if installed else "destructive",
                ),
            ),
            _kv(
                "Service",
                Badge(label="Running" if running else "Stopped", variant="success" if running else "secondary"),
            ),
            _kv("Executable", exe_path),
            _kv("Config dir", config_dir),
            _kv("Mock mode", "Yes" if service.mock_mode else "No"),
        ]
        body: list[Component] = [Heading(content="RustDesk Installation"), Div(children=rows)]
        view = Div(children=body)
        return PrefabApp(view=view, title="RustDesk Installation")
