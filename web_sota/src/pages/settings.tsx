import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { API_BASE } from "@/lib/api";
import { Cpu } from "lucide-react";
import { useEffect, useState } from "react";

export function Settings() {
	const [providers, setProviders] = useState<
		Record<string, { name: string }[]>
	>({});
	const [selectedProvider, setSelectedProvider] = useState("ollama");
	const [selectedModel, setSelectedModel] = useState("");
	const [status, setStatus] = useState<"loading" | "ready" | "error">(
		"loading",
	);

	useEffect(() => {
		fetch(API_BASE + "/api/llm/providers")
			.then((r) => r.json())
			.then((d) => {
				setProviders(d);
				const savedP = localStorage.getItem("llm_provider") || "ollama";
				const savedM = localStorage.getItem("llm_model") || "";
				setSelectedProvider(savedP);
				const models = d[savedP === "ollama" ? "ollama" : "lm_studio"] || [];
				setSelectedModel(
					savedM && models.some((m: { name: string }) => m.name === savedM)
						? savedM
						: models[0]?.name || "",
				);
				setStatus(models.length > 0 ? "ready" : "error");
			})
			.catch(() => {
				setProviders({ ollama: [{ name: "llama3.2:3b" }] });
				setSelectedModel(localStorage.getItem("llm_model") || "llama3.2:3b");
				setStatus("ready");
			});
	}, []);

	const save = (p: string, m: string) => {
		localStorage.setItem("llm_provider", p);
		localStorage.setItem("llm_model", m);
	};

	const models =
		providers[selectedProvider === "ollama" ? "ollama" : "lm_studio"] || [];

	return (
		<div className="space-y-6">
			<div>
				<h2 className="text-2xl font-bold tracking-tight text-white">
					Settings
				</h2>
				<p className="text-slate-400">
					Configure LLM provider and remote desktop preferences
				</p>
			</div>

			<Card className="border-slate-800 bg-slate-950/50">
				<CardHeader>
					<div className="flex items-center gap-2">
						<Cpu className="h-5 w-5 text-blue-500" />
						<CardTitle className="text-white">Local LLM</CardTitle>
					</div>
					<CardDescription className="text-slate-400">
						AI provider for agentic workflows.
						{status === "ready" ? (
							<span className="ml-2 inline-flex items-center gap-1 text-emerald-400">
								<span className="h-2 w-2 rounded-full bg-emerald-400" />{" "}
								{models.length} model(s) available
							</span>
						) : (
							<span className="ml-2 inline-flex items-center gap-1 text-amber-400">
								<span className="h-2 w-2 rounded-full bg-amber-400" />{" "}
								probing...
							</span>
						)}
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<div>
						<label className="text-xs text-slate-400 mb-1 block">
							Provider
						</label>
						<select
							className="h-10 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-100"
							value={selectedProvider}
							onChange={(e) => {
								setSelectedProvider(e.target.value);
								save(e.target.value, "");
							}}
						>
							<option value="ollama">Ollama</option>
							<option value="lm_studio">LM Studio</option>
						</select>
					</div>
					<div>
						<label className="text-xs text-slate-400 mb-1 block">Model</label>
						<select
							className="h-10 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-100"
							value={selectedModel}
							onChange={(e) => {
								setSelectedModel(e.target.value);
								save(selectedProvider, e.target.value);
							}}
						>
							{models.map((m) => (
								<option key={m.name} value={m.name}>
									{m.name}
								</option>
							))}
						</select>
					</div>
					<p className="text-xs text-slate-500">
						Selection saved to browser storage. Used by AI tools and LLM chat.
					</p>
				</CardContent>
			</Card>

			<Card className="border-slate-800 bg-slate-950/50">
				<CardHeader>
					<CardTitle className="text-white">App Information</CardTitle>
				</CardHeader>
				<CardContent className="text-sm text-slate-400 space-y-1">
					<p>RustDesk MCP v0.1.0 (SOTA)</p>
					<p>Dual Transport: STDIO + HTTP (10802)</p>
				</CardContent>
			</Card>
		</div>
	);
}
