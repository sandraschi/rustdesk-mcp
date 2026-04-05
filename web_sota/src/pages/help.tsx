import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Book, Shield, Zap, Info } from "lucide-react";

export function Help() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">Help & Documentation</h2>
                <p className="text-slate-400">Reference guide for Remote Desktop MCP</p>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Book className="h-5 w-5 text-blue-500" />
                            <CardTitle className="text-white">Quick Start</CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent className="text-sm text-slate-400 space-y-4">
                        <p>1. Ensure RustDesk is installed and running on this machine.</p>
                        <p>2. Configure your Peer ID in RustDesk settings.</p>
                        <p>3. Use the AI Command page to issue natural language commands like "Show active sessions" or "Connect to ID 12345".</p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Shield className="h-5 w-5 text-purple-500" />
                            <CardTitle className="text-white">Security & Auth</CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent className="text-sm text-slate-400 space-y-4">
                        <p>Basic Authentication is required for web access. Credentials are managed via environment variables.</p>
                        <p>RustDesk passwords for peers are handled securely through the tool parameters.</p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Zap className="h-5 w-5 text-yellow-500" />
                            <CardTitle className="text-white">MCP Parameters</CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent className="text-sm text-slate-400 space-y-4">
                        <p>Port: 10802 (Standard for Remote Desktop MCP)</p>
                        <p>Transport: Dual (STDIO + HTTP Bridge)</p>
                        <p>API Base: /api/v1</p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Info className="h-5 w-5 text-emerald-500" />
                            <CardTitle className="text-white">About SOTA</CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent className="text-sm text-slate-400">
                        <p>Part of the Sandra SOTA Fleet (January 2026). Standardized UI, dual transport mode, and AI-first design philosophy.</p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
