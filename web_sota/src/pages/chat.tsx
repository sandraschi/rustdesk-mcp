import { Bot, Download, Loader2, Mic, MicOff, Send, Sparkles, Trash2, User, Volume2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { isSTTSupported, isTTSSupported, speak, createSpeechRecognition, stripMarkdown } from "@/common/speech";
import { useChatStore } from "@/stores/chat-store";

const PERSONALITIES: Record<string, string> = {
  "Remote Support": "You are an expert remote support technician using RustDesk. Help users connect to remote devices, troubleshoot connection issues, and manage remote sessions efficiently. Be clear and step-by-step.",
  "System Admin": "You are a senior system administrator managing remote devices. Advise on security configurations, access policies, address book management, and unattended access setup for enterprise deployments.",
  "Security Auditor": "You are a security-focused remote access auditor. Review connection logs, verify access policies, audit session recordings for compliance, and recommend security hardening for RustDesk deployments.",
  "Quick Summarizer": "You are a concise assistant. Answer in 1-3 sentences. Be direct and to the point.",
  "Custom": "",
};

const EXAMPLE_PROMPTS = [
  { group: "Devices", items: ["List all devices in the address book", "Connect to a remote workstation with file transfer", "Check connection status for all managed devices"] },
  { group: "Sessions", items: ["Start an unattended remote session", "Transfer files between local and remote machine", "Record a remote support session for audit"] },
  { group: "Security", items: ["Set up a permanent password for a device", "Configure two-factor authentication", "Review recent connection logs"] },
];

const API_URL = "http://127.0.0.1:10805";

async function fetchSkills(): Promise<string | null> {
  try {
    const r = await fetch(`${API_URL}/api/skills`);
    if (!r.ok) return null;
    const data = await r.json();
    const skills = data.skills || [];
    if (skills.length > 0) {
      const skillR = await fetch(`${API_URL}/api/skills/${skills[0].name || skills[0]}`);
      if (skillR.ok) return await skillR.text();
    }
  } catch {}
  return null;
}

async function probeProvider(): Promise<string | null> {
  try {
    const r = await fetch(`${API_URL}/api/llm/discover`);
    if (r.ok) {
      const d = await r.json();
      return d.provider || d.model || "connected";
    }
  } catch {}
  return null;
}

export function Chat() {
  const {
    messages, personality, skillContent, providerStatus, isLoading,
    addMessage, appendToLast, setPersonality, setSkillContent, setProviderStatus, setIsLoading, clear,
  } = useChatStore();

  const [inputValue, setInputValue] = useState("");
  const [showExamples, setShowExamples] = useState(false);
  const [listening, setListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<ReturnType<typeof createSpeechRecognition> | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    fetchSkills().then((s) => setSkillContent(s || "You are a RustDesk remote desktop assistant with access to remote device management tools."));
    probeProvider().then(setProviderStatus);
  }, [setSkillContent, setProviderStatus]);

  useEffect(() => {
    if (!isSTTSupported()) return;
    recognitionRef.current = createSpeechRecognition(
      (transcript, isFinal) => {
        if (isFinal) {
          setInputValue((prev) => (prev ? `${prev} ${transcript}` : transcript));
          setInterimTranscript("");
        } else {
          setInterimTranscript(transcript);
        }
      },
      () => setListening(false),
    );
    return () => { recognitionRef.current?.stop(); };
  }, []);

  const buildSystemPrompt = useCallback(() => {
    const base = skillContent || PERSONALITIES[personality] || "";
    const role = personality === "Custom" ? PERSONALITIES[personality] : "";
    return [base, role].filter(Boolean).join("\n\n---\n\n## Role\n");
  }, [skillContent, personality]);

  const handleSend = useCallback(async () => {
    const text = inputValue.trim();
    if (!text || isLoading) return;
    setShowExamples(false);

    addMessage({ role: "user", content: text, timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) });
    addMessage({ role: "assistant", content: "", timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) });
    setInputValue("");
    setIsLoading(true);

    try {
      const history = [...messages, { role: "user" as const, content: text }].map((m) => ({ role: m.role, content: m.content }));

      // Try streaming first, fall back to non-streaming
      const streamR = await fetch(`${API_URL}/api/ai/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, system_prompt: buildSystemPrompt(), context: { history } }),
      });

      if (streamR.ok && streamR.body) {
        const reader = streamR.body.getReader();
        const decoder = new TextDecoder();
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          appendToLast(chunk);
        }
      } else {
        const response = await fetch(`${API_URL}/api/ai/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text, system_prompt: buildSystemPrompt(), context: { history } }),
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        const reply = data.reply || data.response || "No response from model.";
        appendToLast(reply);
      }
    } catch {
      appendToLast("Request failed. Check that the backend is running and an LLM provider is configured.");
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }, [messages, isLoading, inputValue, addMessage, appendToLast, setIsLoading, buildSystemPrompt]);

  const toggleMic = () => {
    if (!recognitionRef.current) return;
    if (listening) { recognitionRef.current.stop(); setListening(false); }
    else { recognitionRef.current.start(); setListening(true); }
  };

  const lastMsg = messages[messages.length - 1];
  const canSpeak = lastMsg?.role === "assistant" && lastMsg.content && isTTSSupported();
  const providerColor = providerStatus === null ? "bg-gray-500" : providerStatus === "not found" ? "bg-red-500" : "bg-green-500";

  return (
    <div className="flex flex-col space-y-4 animate-in fade-in duration-500 h-full" data-testid="chat-page">
      <div className="flex items-center justify-between shrink-0" data-testid="chat-controls">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <h2 className="text-2xl font-bold tracking-tight text-foreground">Chat</h2>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full animate-pulse ${providerColor}`} title={providerStatus || "detecting..."} />
            <span className="text-xs text-muted-foreground bg-muted/30 px-2 py-0.5 rounded font-mono">
              {skillContent ? "skill:remote-support" : "no skill loaded"}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full animate-pulse ${providerColor}`} data-testid="backend-dot" />
          <button type="button" onClick={() => {
            const text = messages.map((m) => `[${m.timestamp}] ${m.role === "user" ? "You" : "Assistant"}: ${m.content}`).join("\n\n");
            const blob = new Blob([text], { type: "text/plain" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `rustdesk-mcp-chat-${new Date().toISOString().split("T")[0]}.txt`;
            a.click();
            URL.revokeObjectURL(url);
          }} data-testid="chat-export"
            className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs text-muted-foreground hover:bg-secondary transition-colors">
            <Download className="h-3.5 w-3.5" /> Export
          </button>
          <button type="button" onClick={clear} data-testid="chat-clear"
            className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs text-muted-foreground hover:bg-secondary transition-colors">
            <Trash2 className="h-3.5 w-3.5" /> Clear
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2 flex-wrap shrink-0" data-testid="personality-select">
        <span className="text-xs text-muted-foreground">Personality:</span>
        {Object.keys(PERSONALITIES).map((p) => (
          <button key={p} type="button" onClick={() => setPersonality(p)}
            className={`px-2.5 py-1 rounded text-[10px] font-medium transition-all ${
              personality === p
                ? "bg-primary/20 text-primary border border-primary/30"
                : "bg-muted/30 text-muted-foreground border border-border/40 hover:bg-muted/50"
            }`}>
            {p}
          </button>
        ))}
      </div>

      <div className="flex-1 flex flex-col overflow-hidden rounded-xl border border-border bg-background/20">
        <div className="flex-1 overflow-y-auto p-4 space-y-4" data-testid="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className="flex gap-3 animate-in slide-in-from-bottom-2 duration-300">
              <div className={`h-8 w-8 rounded-full flex items-center justify-center border shrink-0 ${
                msg.role === "user" ? "bg-secondary border-border/50" : "bg-primary/10 border-primary/20"
              }`}>
                {msg.role === "user" ? <User className="h-4 w-4 text-primary/70" /> : <Bot className="h-4 w-4 text-primary" />}
              </div>
              <div className="flex-1 space-y-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium ${msg.role === "user" ? "text-foreground" : "text-primary"}`}>
                    {msg.role === "user" ? "You" : personality}
                  </span>
                  <span className="text-[10px] text-muted-foreground">{msg.timestamp}</span>
                  {canSpeak && i === messages.length - 1 && (
                    <button type="button" onClick={() => speak(stripMarkdown(msg.content))}
                      className="p-1 rounded text-slate-400 hover:text-white transition-colors" title="Speak">
                      <Volume2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
                <div className={`text-sm p-3 rounded-lg border inline-block max-w-[85%] whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-secondary/30 border-border/30 text-foreground"
                    : "bg-primary/5 border-primary/10 text-foreground"
                }`}>
                  {msg.content || ""}
                </div>
              </div>
            </div>
          ))}
          {isLoading && !messages[messages.length - 1]?.content && (
            <div className="flex gap-3 animate-pulse">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20 shrink-0">
                <Loader2 className="h-4 w-4 text-primary animate-spin" />
              </div>
              <div className="bg-primary/5 border border-primary/10 p-3 rounded-lg h-10 w-48">
                <div className="h-2 w-full bg-primary/20 rounded animate-pulse" />
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <div className="p-4 border-t border-border/30 bg-secondary/10 shrink-0">
          {!showExamples && (
            <div className="mb-2 flex items-center gap-1.5 flex-wrap" data-testid="example-prompts">
              {EXAMPLE_PROMPTS.map((group) => (
                <div key={group.group} className="flex items-center gap-1">
                  <span className="text-[10px] text-muted-foreground mr-1">{group.group}:</span>
                  {group.items.map((p) => (
                    <button key={p} type="button" onClick={() => { setInputValue(p); inputRef.current?.focus(); }}
                      className="px-2 py-0.5 rounded text-[10px] bg-muted/30 text-muted-foreground hover:bg-muted/50 transition-colors border border-border/30">
                      {p}
                    </button>
                  ))}
                </div>
              ))}
              <button type="button" onClick={() => setShowExamples(true)}
                className="px-2 py-0.5 rounded text-[10px] text-primary hover:text-primary/80 transition-colors">
                Show all
              </button>
            </div>
          )}
          {showExamples && (
            <div className="mb-2 flex flex-wrap gap-1.5" data-testid="example-prompts">
              {EXAMPLE_PROMPTS.map((group) => (
                <div key={group.group} className="flex flex-wrap items-center gap-1">
                  <span className="text-[10px] text-muted-foreground font-medium mr-1">{group.group}:</span>
                  {group.items.map((p) => (
                    <button key={p} type="button" onClick={() => { setInputValue(p); setShowExamples(false); inputRef.current?.focus(); }}
                      className="px-2 py-0.5 rounded text-[10px] bg-muted/30 text-muted-foreground hover:bg-muted/50 transition-colors border border-border/30">
                      {p}
                    </button>
                  ))}
                </div>
              ))}
              <button type="button" onClick={() => setShowExamples(false)}
                className="px-2 py-0.5 rounded text-[10px] text-primary hover:text-primary/80 transition-colors">
                Less
              </button>
            </div>
          )}
          <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-3">
            <div className="flex-1 flex items-center gap-2 bg-black/20 border border-border/50 rounded-lg px-3 transition-all focus-within:ring-1 focus-within:ring-primary/50">
              <input ref={inputRef}
                className="flex-1 bg-transparent py-2.5 text-sm text-foreground focus:outline-none placeholder:text-muted-foreground/50"
                placeholder="Ask about remote access..."
                value={inputValue + (interimTranscript ? ` ${interimTranscript}` : "")}
                onChange={(e) => setInputValue(e.target.value)}
                disabled={isLoading}
                data-testid="chat-input"
              />
              {isSTTSupported() && (
                <button type="button" onClick={toggleMic} title={listening ? "Stop" : "Voice input"}
                  className={`p-1.5 rounded transition-colors ${listening ? "text-red-400 bg-red-500/10" : "text-slate-400 hover:text-white"}`}>
                  {listening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                </button>
              )}
            </div>
            <button type="submit" disabled={isLoading || !inputValue.trim()} data-testid="chat-send"
              className="p-2.5 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg shadow-primary/20 shrink-0 disabled:opacity-50 transition-all">
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
