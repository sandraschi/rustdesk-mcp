# Agentic Control & Autonomous Orchestration

> [!WARNING]
> **POWER & DANGER**: The tools described here enable the AI to perform physical actions (clicks and typing) on a remote desktop. This is extremely powerful for automation but carries significant risks if misused.

## 🚀 The Power: Autonomous Orchestration (SEP-1577)

The RustDesk MCP now supports **SEP-1577 Sampling**, allowing the AI to orchestrate complex remote tasks autonomously. Instead of just "taking a screenshot," the AI can now:
- **Scan the environment**: Use vision to identify UI elements.
- **Formulate a plan**: Sample its own LLM to decide on a sequence of actions.
- **Execute multi-step workflows**: Automatically navigate menus, install software, or troubleshoot issues.

### Key Tools
- `agentic_workflow_tool`: The entry point for autonomous missions.
- `remote_click`: Precision mouse interaction within the RustDesk window.
- `remote_type`: Injected keyboard sequences into the remote session.

## ⚠️ The Danger: Remote Execution Risks

Giving an AI control over your mouse and keyboard is inherently dangerous. Potential risks include:
- **Destructive Actions**: The AI might accidentally delete files or close critical applications if it misinterprets a UI state.
- **Security Escalation**: If the remote session has administrator privileges, the AI could potentially perform system-level changes.
- **Infinite Loops**: Unbounded automation could lead to repetitive actions that drain resources or cause instability.

## 🛡️ Security Measures (The Safeguards)

To mitigate these risks, we have implemented several layers of protection:

### 1. Mandatory Explicit Consent
The webapp includes a **Security Guard** toggle. No remote actions (`click` or `type`) will be executed unless this is manually enabled by the user in the "Control" tab.

### 2. Coordinate Sanitization
The system performs "Source of Truth" window detection. Clicks are mathematically clamped to the detected bounds of the RustDesk remote window, preventing the AI from clicking "outside" onto the host OS.

### 3. Action Throttling & Rate Limiting
Remote actions are throttled to prevent rapid-fire execution that could be used for malicious purposes or lead to race conditions.

### 4. Read-Only Mode Support
The MCP respects the session's read-only status. If a session is established as "view only," the control tools will refuse to execute destructive actions.

### 5. Comprehensive Action Audit
Every remote interaction is logged with:
- Timestamp
- Action type (Click/Type)
- Coordinates/Text
- Target Window ID

## 🚦 Usage Best Practices

1. **Monitor the Mission**: Never leave an autonomous workflow unattended.
2. **Start with Safe Mode**: Use vision tools to "observe" before granting click/type permissions.
3. **Limit Privileges**: Only connect to remote sessions with the minimum required privileges for the task.
4. **Audit Logs**: Regularly review the "Action Audit" in the Control tab to ensure transparency.

---

*This documentation is part of the SOTA 2026 RustDesk MCP Standard.*
