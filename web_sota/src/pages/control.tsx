import { cn } from "@/common/utils";
import { API_BASE } from "@/lib/api";
import {
	CheckCircle2,
	Eye,
	Joystick,
	Keyboard,
	Lock,
	MousePointer2,
	Play,
	Shield,
	ShieldAlert,
} from "lucide-react";
import { useCallback, useState } from "react";

export function Control() {
	const [securityApproval, setSecurityApproval] = useState(false);
	const [lastAction, setLastAction] = useState<string | null>(null);
	const [actionStatus, setActionStatus] = useState<
		"idle" | "working" | "ok" | "fail"
	>("idle");

	const handleAction = useCallback(
		async (action: string) => {
			if (!securityApproval) return;
			setLastAction(action);
			setActionStatus("working");
			try {
				const r = await fetch(`${API_BASE}/api/control/${action}`, {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ x: 100, y: 100, text: "" }),
				});
				if (r.ok) {
					setActionStatus("ok");
				} else {
					setActionStatus("fail");
				}
			} catch {
				setActionStatus("fail");
			}
		},
		[securityApproval],
	);

	return (
		<div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
			<div className="flex items-center justify-between">
				<div>
					<h1 className="text-3xl font-bold tracking-tight text-slate-100 italic">
						Advanced Control
					</h1>
					<p className="text-muted-foreground">
						Manage remote interactions and autonomous workflows.
					</p>
				</div>
				<div
					className={cn(
						"flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-semibold uppercase tracking-wider",
						securityApproval
							? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
							: "bg-red-500/10 text-red-400 border border-red-500/20",
					)}
				>
					{securityApproval ? (
						<CheckCircle2 className="h-4 w-4" />
					) : (
						<ShieldAlert className="h-4 w-4" />
					)}
					{securityApproval ? "Authorized" : "Unauthorized"}
				</div>
			</div>

			<div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
				<div className="group relative overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50 p-6 transition-all hover:bg-slate-900 hover:shadow-2xl hover:shadow-blue-500/10">
					<div className="flex items-center gap-4">
						<div className="rounded-lg bg-blue-500/10 p-3 text-blue-400 group-hover:scale-110 transition-transform">
							<Shield className="h-6 w-6" />
						</div>
						<div>
							<h3 className="font-semibold text-slate-100">Security Guard</h3>
							<p className="text-sm text-slate-400 font-mono italic">
								Explicit Consent Required
							</p>
						</div>
					</div>
					<div className="mt-6 flex flex-col gap-4">
						<div className="flex items-center justify-between">
							<span className="text-sm text-slate-300">
								Remote Control Permission
							</span>
							<button
								onClick={() => setSecurityApproval(!securityApproval)}
								className={cn(
									"relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2",
									securityApproval ? "bg-blue-600" : "bg-slate-700",
								)}
							>
								<span
									className={cn(
										"pointer-events-none block h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform",
										securityApproval ? "translate-x-5" : "translate-x-0",
									)}
								/>
							</button>
						</div>
						<p className="text-xs text-slate-500 bg-slate-950/50 p-3 rounded border border-slate-800/50">
							When enabled, you authorize the AI to perform clicks and typing
							actions in the active RustDesk window. All actions are logged.
						</p>
					</div>
				</div>

				<div className="group relative overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50 p-6 transition-all hover:bg-slate-900 hover:shadow-2xl hover:shadow-purple-500/10">
					<div className="flex items-center gap-4">
						<div className="rounded-lg bg-purple-500/10 p-3 text-purple-400 group-hover:scale-110 transition-transform">
							<Play className="h-6 w-6" />
						</div>
						<div>
							<h3 className="font-semibold text-slate-100">Agentic Workflow</h3>
							<p className="text-sm text-slate-400 font-mono italic">
								SEP-1577 Sampling
							</p>
						</div>
					</div>
					<div className="mt-6">
						<button
							disabled={!securityApproval}
							onClick={() => {}}
							className={cn(
								"w-full rounded-md py-2 px-4 text-sm font-medium transition-all",
								!securityApproval
									? "bg-slate-800 text-slate-500 cursor-not-allowed"
									: "bg-purple-500/10 text-purple-400 hover:bg-purple-500/20 border border-purple-500/20",
							)}
						>
							Start Autonomous Mission
						</button>
						<p className="mt-3 text-xs text-slate-500">
							Autonomous workflows use MCP sampling (ctx.sample) for multi-step
							reasoning. Requires an LLM host that supports FastMCP sampling.
						</p>
					</div>
				</div>

				<div className="group relative overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50 p-6 transition-all hover:bg-slate-900 hover:shadow-2xl hover:shadow-emerald-500/10">
					<div className="flex items-center gap-4">
						<div className="rounded-lg bg-emerald-500/10 p-3 text-emerald-400 group-hover:scale-110 transition-transform">
							<Eye className="h-6 w-6" />
						</div>
						<div>
							<h3 className="font-semibold text-slate-100">Action Audit</h3>
							<p className="text-sm text-slate-400 font-mono italic">
								Real-time Logging
							</p>
						</div>
					</div>
					<div className="mt-4 max-h-[120px] overflow-y-auto space-y-2 pr-2 custom-scrollbar">
						{lastAction ? (
							<div className="flex items-center justify-between rounded bg-slate-950/50 p-2 text-xs border border-slate-800/30">
								<span className="text-slate-300 capitalize">{lastAction}</span>
								<span
									className={cn(
										"text-xs",
										actionStatus === "ok"
											? "text-emerald-400"
											: actionStatus === "fail"
												? "text-red-400"
												: "text-slate-500",
									)}
								>
									{actionStatus === "working"
										? "..."
										: actionStatus === "ok"
											? "OK"
											: actionStatus === "fail"
												? "Failed"
												: new Date().toLocaleTimeString()}
								</span>
							</div>
						) : (
							<div className="flex h-[100px] items-center justify-center text-xs text-slate-600 italic">
								No actions recorded in this session.
							</div>
						)}
					</div>
				</div>
			</div>

			<div className="rounded-xl border border-slate-800 bg-slate-950/30 p-8 backdrop-blur-sm">
				<div className="flex items-center gap-3 mb-6">
					<Lock className="h-5 w-5 text-slate-500" />
					<h2 className="text-xl font-semibold text-slate-200">
						Manual Override Tools
					</h2>
				</div>
				<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
					<button
						onClick={() => handleAction("remote_click")}
						disabled={!securityApproval || actionStatus === "working"}
						className="flex items-center justify-center gap-3 rounded-lg border border-slate-700 bg-slate-800/50 p-8 text-lg font-medium text-slate-200 transition-all hover:bg-slate-700 hover:border-slate-500 disabled:opacity-50 disabled:cursor-not-allowed group"
					>
						<MousePointer2 className="h-6 w-6 text-blue-400 group-hover:scale-110 transition-transform" />
						Trigger Precision Click
					</button>
					<button
						onClick={() => handleAction("remote_type")}
						disabled={!securityApproval || actionStatus === "working"}
						className="flex items-center justify-center gap-3 rounded-lg border border-slate-700 bg-slate-800/50 p-8 text-lg font-medium text-slate-200 transition-all hover:bg-slate-700 hover:border-slate-500 disabled:opacity-50 disabled:cursor-not-allowed group"
					>
						<Keyboard className="h-6 w-6 text-emerald-400 group-hover:scale-110 transition-transform" />
						Inject Keyboard Sequence
					</button>
				</div>
				{!securityApproval && (
					<div className="mt-6 flex items-center justify-center gap-2 text-sm text-red-500 bg-red-500/5 border border-red-500/10 p-3 rounded-md italic">
						<ShieldAlert className="h-4 w-4" />
						Manual override controls disabled until Security Authorization is
						granted.
					</div>
				)}
			</div>
		</div>
	);
}
