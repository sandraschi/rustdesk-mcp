import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Server, Activity, Wifi, WifiOff, Database } from "lucide-react";
import { API_BASE } from "@/lib/api";
import { useEffect, useState } from "react";

interface ServiceStatus {
  name: string;
  port: number;
  status: "up" | "down" | "checking";
  description: string;
}

export function ServerStatus() {
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: "MCP Backend", port: 10805, status: "checking", description: "Python FastMCP + FastAPI" },
    { name: "Fork API", port: 10806, status: "checking", description: "rustdesk++ HTTP API" },
    { name: "hbbs (ID)", port: 21116, status: "checking", description: "Rendezvous / ID server (UDP)" },
    { name: "hbbr (Relay)", port: 21117, status: "checking", description: "Relay server (TCP)" },
  ]);

  useEffect(() => {
    const checkService = async (port: number): Promise<boolean> => {
      try {
        const r = await fetch(`http://127.0.0.1:${port}/api/health`, { signal: AbortSignal.timeout(3000) });
        return r.ok;
      } catch {
        try {
          const r = await fetch(`http://127.0.0.1:${port}/api/v1/health`, { signal: AbortSignal.timeout(2000) });
          return r.ok;
        } catch {
          return false;
        }
      }
    };

    const checkPort = async (port: number): Promise<boolean> => {
      try {
        const r = await fetch(`http://127.0.0.1:${port}/`, { signal: AbortSignal.timeout(2000) });
        return r.ok;
      } catch {
        return false;
      }
    };

    Promise.all(
      services.map(async (svc) => {
        const alive = svc.port <= 10806
          ? await checkService(svc.port)
          : await checkPort(svc.port);
        svc.status = alive ? "up" : "down";
        return svc;
      })
    ).then(setServices);

    // Also try the fork status endpoint
    fetch(`${API_BASE}/api/status/fork`)
      .then((r) => r.json())
      .then((data) => {
        setServices((prev) =>
          prev.map((s) => {
            if (s.port === 10806) s.status = data.fork_api?.status === "available" ? "up" : "down";
            if (s.port === 21116) s.status = data.hbbs?.status === "responding" ? "up" : "down";
            if (s.port === 21117) s.status = data.hbbr?.status === "responding" ? "up" : "down";
            return s;
          })
        );
      })
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-6 animate-in fade-in duration-500" data-testid="server-status-page">
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-green-500/10 p-2">
          <Server className="h-5 w-5 text-green-400" />
        </div>
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Server Status</h2>
          <p className="text-slate-400 text-sm">Live status of all rustdesk++ components</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {services.map((svc) => (
          <Card key={svc.port} className={`border ${
            svc.status === "up" ? "border-emerald-800/50 bg-emerald-950/10" :
            svc.status === "down" ? "border-red-800/30 bg-red-950/10" :
            "border-slate-700 bg-slate-900/50"
          }`}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {svc.status === "up" ? <Wifi className="h-4 w-4 text-emerald-400" /> :
                   svc.status === "down" ? <WifiOff className="h-4 w-4 text-red-400" /> :
                   <Activity className="h-4 w-4 text-slate-500" />}
                  <CardTitle className="text-base text-white">{svc.name}</CardTitle>
                </div>
                <Badge variant={svc.status === "up" ? "secondary" : "outline"} className={
                  svc.status === "up" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                  svc.status === "down" ? "bg-red-500/10 text-red-400 border-red-500/20" :
                  "bg-slate-500/10 text-slate-400 border-slate-500/20"
                }>
                  {svc.status === "up" ? "Live" : svc.status === "down" ? "Down" : "..."}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-slate-500">{svc.description}</p>
              <p className="text-xs text-slate-600 mt-1">:{svc.port}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="bg-slate-950/50 border-slate-800">
        <CardHeader>
          <CardTitle className="text-lg text-white flex items-center gap-2">
            <Database className="h-4 w-4" />
            Quick Commands
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm text-slate-400">
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span>Start everything</span>
              <code className="text-xs text-slate-500">rustdesk-start.ps1</code>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span>Stop everything</span>
              <code className="text-xs text-slate-500">rustdesk-start.ps1 -Kill</code>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span>MCP backend</span>
              <code className="text-xs text-slate-500">:10805</code>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span>Fork API</span>
              <code className="text-xs text-slate-500">:10806</code>
            </div>
            <div className="flex justify-between py-1">
              <span>Self-hosted relay</span>
              <code className="text-xs text-slate-500">:21116 / :21117</code>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
