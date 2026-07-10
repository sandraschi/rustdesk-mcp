import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE } from "@/lib/api";
import { BookOpen, Code2, ExternalLink } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

const ENDPOINT_EXAMPLES = [
	{ method: "GET", path: "/api/health", desc: "SOTA health check" },
	{ method: "GET", path: "/api/tools", desc: "List MCP tools" },
	{ method: "GET", path: "/api/skills", desc: "List skills" },
	{ method: "GET", path: "/api/llm/discover", desc: "LLM provider probe" },
	{ method: "GET", path: "/api/v1/status", desc: "Service status" },
	{ method: "GET", path: "/api/v1/performance", desc: "Performance metrics" },
	{ method: "POST", path: "/api/v1/connect", desc: "Connect to peer" },
	{ method: "POST", path: "/api/v1/disconnect", desc: "Disconnect session" },
	{ method: "POST", path: "/api/control/remote_click", desc: "Simulate click" },
	{ method: "POST", path: "/api/control/remote_type", desc: "Simulate typing" },
];

export function ApiDocs() {
	const [view, setView] = useState<"swagger" | "redoc">("swagger");
	const backendUrl = API_BASE || "http://127.0.0.1:10805";
	const [err, setErr] = useState(false);

	useEffect(() => {
		fetch(`${backendUrl}/docs`)
			.then((r) => setErr(!r.ok))
			.catch(() => setErr(true));
	}, [backendUrl]);

	return (
		<div className="space-y-6 animate-in fade-in duration-500">
			<div className="flex items-center justify-between">
				<div className="flex items-center gap-3">
					<div className="rounded-lg bg-blue-500/10 p-2">
						<Code2 className="h-5 w-5 text-blue-400" />
					</div>
					<div>
						<h2 className="text-2xl font-bold tracking-tight text-white">
							API Docs
						</h2>
						<p className="text-slate-400 text-sm">
							REST API reference for RustDesk MCP
						</p>
					</div>
				</div>
				<div className="flex items-center gap-2">
					<a
						href={`${backendUrl}/docs`}
						target="_blank"
						rel="noreferrer"
						className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 text-xs text-slate-300 hover:bg-slate-700 transition-colors"
					>
						<ExternalLink className="h-3.5 w-3.5" /> Open in browser
					</a>
				</div>
			</div>

			<div className="flex gap-2">
				<button
					onClick={() => setView("swagger")}
					className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${view === "swagger" ? "bg-primary/20 text-primary border border-primary/30" : "bg-muted/30 text-muted-foreground border border-border/40"}`}
				>
					Swagger UI
				</button>
				<button
					onClick={() => setView("redoc")}
					className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${view === "redoc" ? "bg-primary/20 text-primary border border-primary/30" : "bg-muted/30 text-muted-foreground border border-border/40"}`}
				>
					ReDoc
				</button>
			</div>

			<div className="flex gap-3 overflow-x-auto pb-2">
				{ENDPOINT_EXAMPLES.map((ep, i) => (
					<div
						key={i}
						className="flex items-center gap-1.5 shrink-0 px-2.5 py-1 rounded bg-slate-800/50 border border-slate-700 text-[10px]"
					>
						<Badge
							variant={ep.method === "GET" ? "secondary" : "default"}
							className="text-[9px] px-1"
						>
							{ep.method}
						</Badge>
						<code className="text-slate-300">{ep.path}</code>
						<span className="text-slate-500">— {ep.desc}</span>
					</div>
				))}
			</div>

			<Card className="bg-slate-950/50 border-slate-800">
				<CardContent className="p-0">
					{err ? (
						<div className="p-8 text-center text-slate-500">
							<BookOpen className="h-8 w-8 mx-auto mb-2 text-slate-600" />
							<p>Backend docs endpoint not reachable.</p>
							<a
								href={`${backendUrl}/docs`}
								target="_blank"
								rel="noreferrer"
								className="text-primary hover:underline text-sm mt-2 inline-block"
							>
								Open {backendUrl}/docs directly
							</a>
						</div>
					) : (
						<iframe
							src={
								view === "swagger"
									? `${backendUrl}/docs`
									: `${backendUrl}/redoc`
							}
							className="w-full h-[600px] border-0 rounded-lg"
							title={view === "swagger" ? "Swagger UI" : "ReDoc"}
						/>
					)}
				</CardContent>
			</Card>
		</div>
	);
}
