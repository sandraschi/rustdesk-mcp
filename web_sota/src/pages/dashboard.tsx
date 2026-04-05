import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Monitor, Clock, Shield, Zap } from "lucide-react";

export function Dashboard() {
    const stats = [
        { label: 'Active Sessions', value: '3', change: '2 local, 1 remote', icon: Monitor, color: 'text-blue-500' },
        { label: 'System Load', value: '12%', change: 'Nominal', icon: Activity, color: 'text-green-500' },
        { label: 'Security', value: 'Locked', change: '2FA Active', icon: Shield, color: 'text-purple-500' },
        { label: 'Network', value: 'Stable', change: '4ms Latency', icon: Zap, color: 'text-yellow-500' },
    ];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Remote Desktop</h2>
                    <p className="text-slate-400">Centralized remote management and monitoring</p>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {stats.map((stat, idx) => (
                    <Card key={idx} className="glass-panel neon-border animate-in slide-in-from-bottom-2 duration-500 overflow-hidden">
                        <div className="absolute inset-x-0 h-1 top-0 bg-gradient-to-r from-transparent via-blue-500/20 to-transparent" />
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-slate-200">
                                {stat.label}
                            </CardTitle>
                            <stat.icon className={`h-4 w-4 ${stat.color}`} />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-white">{stat.value}</div>
                            <p className="text-xs text-slate-400">
                                {stat.change}
                            </p>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4 glass-panel border border-white/5 shadow-2xl">
                    <CardHeader>
                        <CardTitle className="text-white">Active Connections</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="flex items-center gap-4 p-3 rounded-lg bg-slate-900/40 border border-slate-800">
                                    <div className="p-2 rounded bg-blue-500/10">
                                        <Monitor className="h-4 w-4 text-blue-500" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-slate-200 truncate">Workstation-{i}</p>
                                        <p className="text-xs text-slate-500 truncate">ID: 123 456 {780 + i}</p>
                                    </div>
                                    <div className="text-xs text-emerald-400 font-mono">Connected</div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
                <Card className="col-span-3 glass-panel border border-white/5 shadow-2xl">
                    <CardHeader>
                        <CardTitle className="text-white">Recent Activity</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex items-center text-sm gap-2 text-slate-400">
                                <Clock className="h-4 w-4" />
                                <span>Disconnected from Peer 456...</span>
                                <span className="ml-auto text-xs">2m ago</span>
                            </div>
                            <div className="flex items-center text-sm gap-2 text-slate-400">
                                <Activity className="h-4 w-4" />
                                <span>File transfer complete (2.4GB)</span>
                                <span className="ml-auto text-xs">15m ago</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
