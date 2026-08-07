"""
Session management for RustDesk connections.
"""

import logging
import uuid
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage multiple concurrent RustDesk sessions"""

    def __init__(self):
        self.active_sessions: dict[str, dict] = {}
        self.session_history: list[dict] = []

    async def create_session(self, peer_id: str, password: str) -> dict[str, Any]:
        """Create new session and return session info.

        Args:
            peer_id: ID of the peer to connect to
            password: Password for the peer connection

        Returns:
            Dictionary containing session information
        """
        session_id = str(uuid.uuid4())
        session = {
            "id": session_id,
            "peer_id": peer_id,
            "status": "connecting",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "connection_info": {},
        }

        self.active_sessions[session_id] = session
        self.session_history.append(session)

        logger.info("Created new session %s for peer %s", session_id, peer_id)
        return session

    async def update_session_status(self, session_id: str, status: str, **kwargs) -> dict[str, Any]:
        """Update session status and additional information.

        Args:
            session_id: ID of the session to update
            status: New status (e.g., 'connected', 'disconnected', 'error')
            **kwargs: Additional session data to update

        Returns:
            Updated session information
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        session["status"] = status
        session["updated_at"] = datetime.utcnow().isoformat()
        session["connection_info"].update(kwargs)

        # Update in history
        for hist_session in self.session_history:
            if hist_session["id"] == session_id:
                hist_session.update(session)
                break

        logger.debug("Updated session %s status to %s", session_id, status)
        return session

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """Get session information by ID.

        Args:
            session_id: ID of the session to retrieve

        Returns:
            Session information dictionary
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        return self.active_sessions[session_id]

    async def list_active_sessions(self) -> list[dict[str, Any]]:
        """List all currently active sessions.

        Returns:
            List of active session dictionaries
        """
        return list(self.active_sessions.values())

    async def close_session(self, session_id: str) -> dict[str, Any]:
        """Close a session and clean up resources.

        Args:
            session_id: ID of the session to close

        Returns:
            Closed session information
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        session["status"] = "closed"
        session["closed_at"] = datetime.utcnow().isoformat()
        session["updated_at"] = datetime.utcnow().isoformat()

        # Remove from active sessions
        del self.active_sessions[session_id]

        # Update in history
        for hist_session in self.session_history:
            if hist_session["id"] == session_id:
                hist_session.update(session)
                break

        logger.info("Closed session %s", session_id)
        return session

    async def get_session_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get session history.

        Args:
            limit: Maximum number of historical sessions to return

        Returns:
            List of historical session dictionaries, most recent first
        """
        return sorted(self.session_history, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]
