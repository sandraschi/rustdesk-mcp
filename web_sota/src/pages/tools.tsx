import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, ChevronDown, ChevronRight, Loader2, Play, Wrench } from "lucide-react";
import { API_BASE } from "@/lib/api";
import { useEffect, useState } from "react";

interface ToolInfo {
  name: string;
  description?: string;
  annotations?: Record<string, unknown>;
}

export function Tools() {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    fetch(API_BASE + "/api/tools")
      .then((r) => r.json())
      .then((data) => {
        setTools(data.tools || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="tools-page">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="tools-page">
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-amber-500/10 p-2">
          <Wrench className="h-5 w-5 text-amber-400" />
        </div>
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">MCP Tools</h2>
          <p className="text-slate-400 text-sm">{tools.length} tools registered on this server</p>
        </div>
      </div>

      {tools.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-slate-500">
          <AlertCircle className="h-8 w-8 text-slate-600 mb-2" />
          <p>No tools detected from backend</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {tools.map((tool) => {
            const isExpanded = expanded === tool.name;
            const isReadOnly = tool.annotations && (tool.annotations as Record<string, unknown>).readonly === true;
            return (
              <Card key={tool.name} className="bg-slate-950/50 border-slate-800">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <CardTitle className="text-base font-mono text-slate-200 truncate">{tool.name}</CardTitle>
                      <Badge variant={isReadOnly ? "secondary" : "default"} className="text-[10px] shrink-0">
                        {isReadOnly ? "READ" : "RW"}
                      </Badge>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 shrink-0"
                      onClick={() => setExpanded(isExpanded ? null : tool.name)}
                    >
                      {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                    </Button>
                  </div>
                  {tool.description && (
                    <CardDescription className="text-xs text-slate-400 mt-1">
                      {tool.description}
                    </CardDescription>
                  )}
                </CardHeader>
                {isExpanded && (
                  <CardContent className="pt-0">
                    <div className="text-xs text-slate-500 space-y-1 border-t border-slate-800 pt-3">
                      <div className="flex gap-2">
                        <span className="text-slate-600">Annotations:</span>
                        <code className="text-slate-400">{JSON.stringify(tool.annotations || {})}</code>
                      </div>
                      <div className="flex gap-2">
                        <span className="text-slate-600">Endpoint:</span>
                        <code className="text-slate-400">mcp://rustdesk-mcp/{tool.name}</code>
                      </div>
                    </div>
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
