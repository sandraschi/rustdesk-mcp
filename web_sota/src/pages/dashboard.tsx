import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Shield, Wifi, WifiOff, Zap } from "lucide-react";
import { API_BASE } from "@/lib/api";
import { useEffect, useState } from "react";

export function Dashboard() {
  const [health, setHealth] = useState<{
    status: string;
    service: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [logCount, setLogCount] = useState(0);

  useEffect(() => {
    fetch(API_BASE + "/api/health")
      .then((r) => r.json())
      .then((d) => {
        setHealth(d);
        setError(null);
      })
      .catch((e) => setError(String(e)));
    fetch(API_BASE + "/api/logs/stats")
      .then((r) => r.json())
      .then((d) => setLogCount(d.total || 0))
      .catch(() => {});
  }, []);

  const connected = health?.status === "ok";
  const stats = [
    {
      label: "Backend",
      value: connected ? "Online" : "Offline",
      icon: connected ? Wifi : WifiOff,
      color: connected ? "text-emerald-400" : "text-red-400",
    },
    {
      label: "Service",
      value: health?.service?.replace("-backend", "") || "unknown",
      icon: Activity,
      color: "text-blue-400",
    },
    {
      label: "Log Entries",
      value: String(logCount),
      icon: Shield,
      color: "text-purple-400",
    },
    {
      label: "Status",
      value: error ? "Error" : "Healthy",
      icon: Zap,
      color: error ? "text-red-400" : "text-yellow-400",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            RustDesk MCP
          </h2>
          <p className="text-slate-400">
            Remote desktop management and monitoring
          </p>
        </div>
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${connected ? "bg-emerald-950/40 text-emerald-400" : "bg-red-950/40 text-red-400"}`}
        >
          <span
            className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-400 animate-pulse" : "bg-red-400"}`}
          />
          {connected ? "API Online" : "Disconnected"}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, idx) => (
          <Card key={idx} className="bg-slate-950/50 border-slate-800">
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
                value: health?.service || "—",
                color: "text-slate-200",
              },
              {
                label: "Logging",
                value: `${logCount} entries (ring buffer, max 2000)`,
                color: "text-slate-200",
              },
              {
                label: "MCP Tools",
                value: "Available on MCP port",
                color: "text-slate-200",
              },
              { label: "Swagger Docs", value: "/docs", color: "text-blue-400" },
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
