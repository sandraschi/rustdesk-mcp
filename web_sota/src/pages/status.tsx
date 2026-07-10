import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Cpu, MemoryStick as Memory, Shield } from "lucide-react";

export function Status() {
	return (
		<div className="space-y-6">
			<div>
				<h1 className="text-3xl font-bold text-white">System Status</h1>
				<p className="text-slate-400">
					Real-time telemetry from the RustDesk-MCP bridge.
				</p>
			</div>

			<div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
				<Card className="border-slate-800 bg-slate-900/50">
					<CardHeader className="flex flex-row items-center justify-between pb-2 text-white">
						<CardTitle className="text-sm font-medium uppercase tracking-wider text-slate-500">
							API Latency
						</CardTitle>
						<Activity className="h-4 w-4 text-emerald-400" />
					</CardHeader>
					<CardContent>
						<div className="text-2xl font-bold text-white">12ms</div>
						<p className="text-xs text-slate-500 mt-1">Direct P2P Link</p>
					</CardContent>
				</Card>
			</div>
		</div>
	);
}
