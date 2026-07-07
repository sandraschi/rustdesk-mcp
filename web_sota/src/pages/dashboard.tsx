import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Server, Wifi, WifiOff, Zap, Shield } from "lucide-react";
import { API_BASE } from "@/lib/api";
import { useCallback, useEffect, useRef, useState } from "react";

export function Dashboard() {
  const [health, setHealth] = useState<{
    status: string;
    server: string;
    version: string;
    tool_count?: number;
    uptime_seconds?: number;
    rustdesk_fork_api?: { available: boolean; status: string };
    hbbs_running?: { running: boolean };
  } | null>(null);
  const [forkStatus, setForkStatus] = useState<{
    fork_api: { status: string };
    hbbs: { status: string };
    hbbr: { status: string };
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [logCount, setLogCount] = useState(0);
  const retryRef = useRef(0);

  const fetchHealth = useCallback(async () => {
    try {
      const r = await fetch(API_BASE + "/api/health");
      const d = await r.json();
      setHealth(d);
      forkStatus; // keep in scope
      setError(null);
      retryRef.current = 0;
    } catch (e) {
      setError(String(e));
      const delay = Math.min(1000 * Math.pow(2, retryRef.current), 16000);
      retryRef.current++;
      setTimeout(fetchHealth, delay);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    fetch(API_BASE + "/api/status/fork")
      .then((r) => r.json())
      .then(setForkStatus)
      .catch(() => {});
    fetch(API_BASE + "/api/logs/stats")
      .then((r) => r.json())
      .then((d) => setLogCount(d.total || 0))
      .catch(() => {});
  }, [fetchHealth]);

  const connected = health?.status === "ok";
  const forkAvail = health?.rustdesk_fork_api?.available;
  const hbbsOk = health?.hbbs_running?.running;
  const stats = [
    {
      label: "API",
      value: connected ? "Online" : "Offline",
      icon: connected ? Wifi : WifiOff,
      color: connected ? "text-emerald-400" : "text-red-400",
      testid: "kpi-backend",
    },
    {
      label: "Fork API (:10806)",
      value: forkAvail ? "Online" : "Off",
      icon: Activity,
      color: forkAvail ? "text-emerald-400" : "text-slate-500",
      testid: "kpi-fork-api",
    },
    {
      label: "hbbs/hbbr",
      value: hbbsOk ? "Running" : "Stopped",
      icon: Server,
      color: hbbsOk ? "text-emerald-400" : "text-slate-500",
      testid: "kpi-server",
    },
    {
      label: "Log Entries",
      value: String(logCount),
      icon: Shield,
      color: "text-purple-400",
      testid: "kpi-logs",
    },
    {
      label: "Tools",
      value: health?.tool_count != null ? String(health.tool_count) : "--",
      icon: Zap,
      color: "text-yellow-400",
      testid: "kpi-tools",
    },
    {
      label: "Uptime",
      value: health?.uptime_seconds != null
        ? `${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m`
        : "--",
      icon: Activity,
      color: "text-sky-400",
      testid: "kpi-uptime",
    },
  ];

  return (
    <div className="space-y-6" data-testid="dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            RustDesk MCP
          </h2>
          <p className="text-slate-400">
            {health?.version ? `v${health.version} -- ` : ""}
            Remote desktop management and monitoring
          </p>
        </div>
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${connected ? "bg-emerald-950/40 text-emerald-400" : "bg-red-950/40 text-red-400"}`}
        >
          <span
            className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-400 animate-pulse" : "bg-red-400"}`}
            data-testid="backend-dot"
          />
          {connected ? "API Online" : error ? "Offline" : "Connecting..."}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, idx) => (
          <Card key={idx} className="bg-slate-950/50 border-slate-800" data-testid={stat.testid}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                {stat.label}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{stat.value}</div>
              <p className="text-xs text-slate-500 mt-1">
                {error || "Live from backend"}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="bg-slate-950/50 border-slate-800">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-white">
            System Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            {[
              {
                label: "API Status",
                value: connected ? "Responding" : "Unreachable",
                color: connected ? "text-emerald-400" : "text-red-400",
              },
              {
                label: "Service",
                value: health?.server || "--",
                color: "text-slate-200",
              },
              {
                label: "Uptime",
                value: health?.uptime_seconds != null
                  ? `${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m`
                  : "--",
                color: "text-slate-200",
              },
              {
                label: "Logging",
                value: `${logCount} entries (ring buffer, max 2000)`,
                color: "text-slate-200",
              },
              {
                label: "MCP Tools",
                value: health?.tool_count != null ? `${health.tool_count} registered` : "Available on MCP port",
                color: "text-slate-200",
              },
              { label: "Swagger Docs", value: "/docs", color: "text-blue-400" },
              { label: "Fork API", value: forkAvail ? "Running on :10806" : "Not detected", color: forkAvail ? "text-emerald-400" : "text-slate-500" },
              { label: "hbbs / hbbr", value: hbbsOk ? "Running on :21116/:21117" : "Not detected", color: hbbsOk ? "text-emerald-400" : "text-slate-500" },
            ].map((row, i) => (
              <div
                key={i}
                className="flex justify-between py-2 border-b border-slate-800 last:border-0"
              >
                <span className="text-slate-400">{row.label}</span>
                <span className={row.color}>{row.value}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
