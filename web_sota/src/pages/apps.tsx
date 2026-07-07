import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { LayoutGrid, Plus, Search, Loader2, ExternalLink } from "lucide-react";
import { API_BASE } from "@/lib/api";
import { useEffect, useState } from "react";

interface FleetApp {
  id: string;
  label: string;
  description: string;
  port: number;
  tags: string[];
  alive?: boolean;
}

export function Apps() {
  const [query, setQuery] = useState("");
  const [apps, setApps] = useState<FleetApp[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const check = async () => {
      const ports = [10848, 10792, 10800, 10878, 10874, 10876, 10870, 10766, 10706, 10880, 10704, 10794, 10798, 10812, 10832, 10834, 10838, 10840, 10770, 10726, 10746, 10756, 10806];
      const results: FleetApp[] = [];
      for (const port of ports) {
        try {
          const r = await fetch(`http://127.0.0.1:${port}/api/health`, { signal: AbortSignal.timeout(2000) });
          if (r.ok) {
            const d = await r.json();
            results.push({ id: d.server || `app-${port}`, label: d.server || `App on :${port}`, description: `v${d.version || "?"} on port ${port}`, port, tags: [], alive: true });
          }
        } catch {}
      }
      if (results.length === 0) {
        results.push({ id: "rustdesk-mcp", label: "RustDesk MCP", description: "This server — you're here.", port: 10805, tags: ["self"], alive: true });
      }
      setApps(results);
      setLoading(false);
    };
    check();
  }, []);

  const filtered = query ? apps.filter((a) => a.label.toLowerCase().includes(query.toLowerCase())) : apps;

  return (
    <div className="space-y-6 animate-in fade-in duration-500" data-testid="apps-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">App Hub</h1>
          <p className="text-slate-400">{loading ? "Scanning fleet..." : `${apps.length} active fleet app(s) detected`}</p>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
        <Input placeholder="Search fleet apps..." value={query} onChange={(e) => setQuery(e.target.value)}
          className="pl-10 border-slate-800 bg-slate-900/50 text-slate-200" />
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : filtered.length === 0 ? (
        <Card className="border-slate-800 bg-slate-900/50">
          <CardContent className="py-8 text-center text-slate-500">No fleet apps detected. Are other MCP servers running?</CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((app) => (
            <Card key={app.id} className="border-slate-800 bg-slate-900/50 hover:border-slate-700 transition-colors">
              <CardHeader className="flex flex-row items-center gap-4 pb-2 text-white">
                <div className="rounded-lg bg-indigo-500/10 p-2">
                  <LayoutGrid className="h-6 w-6 text-indigo-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <CardTitle className="text-lg truncate">{app.label}</CardTitle>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`w-1.5 h-1.5 rounded-full ${app.alive !== false ? "bg-green-400" : "bg-slate-500"}`} />
                    <span className="text-[10px] text-slate-500">:{app.port}</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-400">{app.description}</p>
                <div className="mt-4 flex gap-2 flex-wrap">
                  {app.tags?.map((t) => <Badge key={t} variant="secondary" className="text-[10px]">{t}</Badge>)}
                  {app.port !== 10805 && (
                    <a href={`http://127.0.0.1:${app.port}`} target="_blank" rel="noreferrer"
                      className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] bg-primary/10 text-primary hover:bg-primary/20 transition-colors">
                      <ExternalLink className="h-3 w-3" /> Open
                    </a>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
