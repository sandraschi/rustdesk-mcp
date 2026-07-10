import { create } from "zustand";

interface Message {
	role: "user" | "assistant";
	content: string;
	timestamp: string;
}

interface ChatState {
	messages: Message[];
	personality: string;
	skillContent: string | null;
	providerStatus: string | null;
	isLoading: boolean;
	addMessage: (msg: Message) => void;
	appendToLast: (content: string) => void;
	setMessages: (msgs: Message[]) => void;
	setPersonality: (p: string) => void;
	setSkillContent: (s: string | null) => void;
	setProviderStatus: (s: string | null) => void;
	setIsLoading: (v: boolean) => void;
	clear: () => void;
}

const STORAGE_KEY = "rustdesk-mcp-chat-history";
const PERSONALITY_KEY = "rustdesk-mcp-chat-personality";

function loadMessages(): Message[] {
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (raw) return JSON.parse(raw);
	} catch {}
	return [];
}

function saveMessages(msgs: Message[]) {
	try {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs));
	} catch {}
}

export const useChatStore = create<ChatState>((set, get) => ({
	messages:
		loadMessages().length > 0
			? loadMessages()
			: [
					{
						role: "assistant",
						content:
							"I'm your RustDesk remote desktop assistant. I can help with device management, remote sessions, file transfers, and security configuration. How can I assist?",
						timestamp: new Date().toLocaleTimeString([], {
							hour: "2-digit",
							minute: "2-digit",
						}),
					},
				],
	personality: (() => {
		try {
			return localStorage.getItem(PERSONALITY_KEY) || "Remote Support";
		} catch {
			return "Remote Support";
		}
	})(),
	skillContent: null,
	providerStatus: null,
	isLoading: false,

	addMessage: (msg) => {
		const updated = [...get().messages, msg];
		const capped = updated.slice(-100);
		set({ messages: capped });
		saveMessages(capped);
	},

	appendToLast: (content) => {
		const msgs = [...get().messages];
		const last = msgs[msgs.length - 1];
		if (last && last.role === "assistant") {
			msgs[msgs.length - 1] = { ...last, content: last.content + content };
			set({ messages: msgs });
			saveMessages(msgs);
		}
	},

	setMessages: (msgs) => {
		set({ messages: msgs });
		saveMessages(msgs);
	},
	setPersonality: (p) => {
		set({ personality: p });
		try {
			localStorage.setItem(PERSONALITY_KEY, p);
		} catch {}
	},
	setSkillContent: (s) => set({ skillContent: s }),
	setProviderStatus: (s) => set({ providerStatus: s }),
	setIsLoading: (v) => set({ isLoading: v }),

	clear: () => {
		const fresh: Message[] = [
			{
				role: "assistant",
				content: "Conversation cleared. How can I help with remote access?",
				timestamp: new Date().toLocaleTimeString([], {
					hour: "2-digit",
					minute: "2-digit",
				}),
			},
		];
		set({ messages: fresh });
		saveMessages(fresh);
	},
}));
