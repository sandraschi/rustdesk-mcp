import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Globe, Info, Shield, Zap } from "lucide-react";

export function About() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold tracking-tight text-white">
          About RustDesk MCP
        </h2>
        <p className="text-slate-400 text-lg">
          SOTA Remote Desktop Orchestration via Model Context Protocol.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-slate-800 bg-slate-950/50 backdrop-blur-sm shadow-xl">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Shield className="h-6 w-6 text-blue-400" />
              </div>
              <CardTitle className="text-white">Secure Access</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="text-slate-300">
            RustDesk MCP provides a secure bridge between your AI agents and
            remote machines. All communications are encrypted and respect your
            RustDesk server's security policies.
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50 backdrop-blur-sm shadow-xl">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <Zap className="h-6 w-6 text-purple-400" />
              </div>
              <CardTitle className="text-white">Real-time Control</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="text-slate-300">
            Execute remote commands, search for devices, and manage connections
            with sub-second latency using the optimized MCP transport layer.
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50 backdrop-blur-sm shadow-xl">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <Globe className="h-6 w-6 text-green-400" />
              </div>
              <CardTitle className="text-white">Fleet Orchestration</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="text-slate-300">
            Part of the SOTA MCP Ecosystem. Automatically discover and navigate
            between all your local and remote MCP services through the unified
            App Catalog.
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50 backdrop-blur-sm shadow-xl">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-500/10 rounded-lg">
                <Info className="h-6 w-6 text-orange-400" />
              </div>
              <CardTitle className="text-white">V1557 Compliance</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="text-slate-300">
            Built following the latest agentic standards for seamless
            integration with Claude, Gemini, and other frontier AI models.
          </CardContent>
        </Card>
      </div>

      <div className="p-6 rounded-lg border border-slate-800 bg-slate-900/20">
        <p className="text-sm text-slate-500 text-center">
          RustDesk MCP v1.0.0 • Vienna Materialist Standard • February 2026
        </p>
      </div>
    </div>
  );
}
