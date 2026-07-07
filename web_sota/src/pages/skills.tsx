import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Loader2 } from "lucide-react";
import { API_BASE } from "@/lib/api";
import { useEffect, useState } from "react";

interface SkillInfo {
  name: string;
  content?: string;
}

export function Skills() {
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/skills`)
      .then((r) => r.json())
      .then(async (data) => {
        const skillList: SkillInfo[] = (data.skills || []).map((s: SkillInfo) => ({ name: s.name }));
        for (const s of skillList) {
          try {
            const r = await fetch(`${API_BASE}/api/skills/${s.name}`);
            if (r.ok) s.content = await r.text();
          } catch {}
        }
        setSkills(skillList);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-purple-500/10 p-2">
          <BookOpen className="h-5 w-5 text-purple-400" />
        </div>
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Skills</h2>
          <p className="text-slate-400 text-sm">Available server skills loaded at chat start</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : skills.length === 0 ? (
        <Card className="bg-slate-950/50 border-slate-800">
          <CardContent className="py-8 text-center text-slate-500">No skills registered on this server.</CardContent>
        </Card>
      ) : (
        <div className="flex gap-6">
          <div className="w-48 shrink-0 space-y-1">
            {skills.map((s) => (
              <button key={s.name} onClick={() => setSelected(s.name)}
                className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                  selected === s.name ? "bg-primary/10 text-primary border border-primary/20" : "text-slate-400 hover:bg-slate-800 border border-transparent"
                }`}>
                <Badge variant="outline" className="mr-2 text-[10px]">skill</Badge>
                {s.name}
              </button>
            ))}
          </div>
          <div className="flex-1">
            {selected ? (
              <Card className="bg-slate-950/50 border-slate-800">
                <CardHeader>
                  <CardTitle className="text-lg text-white font-mono">{selected}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-invert prose-sm max-w-none text-slate-300 [&_h1]:text-lg [&_h2]:text-base [&_h3]:text-sm [&_code]:bg-slate-800 [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_pre]:bg-slate-900 [&_pre]:p-3 [&_pre]:rounded [&_pre]:border [&_pre]:border-slate-700">
                    {skills.find((s) => s.name === selected)?.content?.split("\n").map((line, i) => (
                      <p key={i} className="text-sm leading-relaxed">{line || "\u00A0"}</p>
                    )) || "No content."}
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="bg-slate-950/50 border-slate-800">
                <CardContent className="py-8 text-center text-slate-500">Select a skill to view its content.</CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
