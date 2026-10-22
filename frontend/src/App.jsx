import { useCallback, useEffect, useRef, useState } from "react";
import {
  Brain, ChevronDown, Clock, Coins, Copy, Cpu, Globe, ListFilter, LogOut, ScanSearch, Search, Trash2, Upload,
} from "lucide-react";
import * as api from "./api";
import Login from "./Login.jsx";
import { AnswerText, Card, DocRow, PdfIcon, Skeleton } from "./components.jsx";

const TOOLS = [
  { id: "web", label: "Web Search", icon: Globe, hint: "Visual apenas (não implementado)" },
  { id: "think", label: "Thinking", icon: Brain, hint: "Visual apenas (não implementado)" },
  { id: "deep", label: "Deep Search", icon: ScanSearch, hint: "Recupera 8 trechos em vez de 4" },
];

export default function App() {
  // "boot" → consulta se o login está ativo; "login" → mostra a tela; "app" → painel.
  const [stage, setStage] = useState("boot");
  const [authOn, setAuthOn] = useState(false);
  const [expired, setExpired] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    api.setUnauthorizedHandler(() => { api.setToken(null); setExpired(true); setStage("login"); });
    api.getAuthStatus()
      .then(async ({ enabled }) => {
        setAuthOn(enabled);
        if (!enabled) return setStage("app");
        if (!api.getToken()) return setStage("login");
        await api.getMe().then((me) => { setUser(me.email); setStage("app"); }).catch(() => setStage("login"));
      })
      .catch(() => setStage("app"));
  }, []);

  const logout = () => { api.setToken(null); setUser(null); setExpired(false); setStage("login"); };

  if (stage === "boot") return <div className="boot">Carregando…</div>;
  if (stage === "login") return <Login expired={expired} onSuccess={(email) => { setUser(email); setExpired(false); setStage("app"); }} />;
  return <Dashboard authOn={authOn} user={user} onLogout={logout} />;
}

// "admin@docintel.local" → nome "Admin", iniciais "AD"
const displayName = (email) => {
  const base = (email || "").split("@")[0].replace(/[._-]+/g, " ").trim();
  return base ? base.replace(/(^|\s)\S/g, (c) => c.toUpperCase()) : "Usuário";
};

function Dashboard({ authOn, user, onLogout }) {
  const [tab, setTab] = useState("dashboard");
  const [provider, setProvider] = useState("…");
  const [docs, setDocs] = useState([]);
  const [question, setQuestion] = useState("");
  const [tools, setTools] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [active, setActive] = useState(null);
  const [toast, setToast] = useState(null);
  const [drag, setDrag] = useState(false);
  const fileRef = useRef(null);

  const notify = (text, err = false) => {
    setToast({ text, err });
    setTimeout(() => setToast(null), 3200);
  };

  const loadDocs = useCallback(() => api.getDocuments().then(setDocs).catch(() => {}), []);

  useEffect(() => {
    api.getHealth().then((h) => setProvider(h.provider)).catch(() => setProvider("offline"));
    loadDocs();
  }, [loadDocs]);

  const upload = async (files) => {
    for (const f of files) {
      try {
        const r = await api.uploadDocument(f);
        notify(`${r.name} indexado (${r.chunks} trechos)`);
      } catch (e) {
        notify(`${f.name}: ${e.message}`, true);
      }
    }
    loadDocs();
  };

  const remove = async (name) => {
    await api.deleteDocument(name).catch((e) => notify(e.message, true));
    loadDocs();
  };

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setActive(null);
    try {
      setResult(await api.ask(question, tools.deep ? 8 : undefined));
    } catch (err) {
      setResult(null);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const cite = (n) => {
    setActive(n);
    document.getElementById(`chunk-${n}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };

  const docMenu = [{ label: "Enviar PDF", icon: Upload, onClick: () => fileRef.current?.click() }];
  const chunkMenu = [{ label: "Limpar trechos", icon: Trash2, onClick: () => { setResult(null); setActive(null); } }];
  const answerMenu = [{
    label: "Copiar resposta", icon: Copy,
    onClick: () => result && navigator.clipboard.writeText(result.answer).then(() => notify("Resposta copiada")),
  }];

  const sourceCard = (detailed) => (
    <Card
      title="Source Documents"
      menu={docMenu}
      className={drag ? "drag" : ""}
      onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => { e.preventDefault(); setDrag(false); upload([...e.dataTransfer.files]); }}
    >
      {docs.length === 0 && <div className="empty">Nenhum documento ainda.</div>}
      {docs.map((d) => <DocRow key={d.name} doc={d} onDelete={remove} detailed={detailed} />)}
      <div className="drop">
        Arraste PDFs aqui ou <button onClick={() => fileRef.current?.click()}>escolha arquivos</button>
      </div>
    </Card>
  );

  const m = result?.metrics;

  return (
    <div className="shell">
      <input ref={fileRef} type="file" accept="application/pdf" multiple hidden
        onChange={(e) => { upload([...e.target.files]); e.target.value = ""; }} />

      <header className="topbar">
        <div className="logo">
          <div className="logo-mark"><ListFilter size={20} /></div> AI SEARCH
        </div>
        <nav className="tabs">
          {[["dashboard", "Dashboard"], ["documents", "Documents"], ["settings", "Settings"]].map(([id, label]) => (
            <button key={id} className={`tab ${tab === id ? "on" : ""}`} onClick={() => setTab(id)}>{label}</button>
          ))}
        </nav>
        <div className="user">
          <div className="avatar">{displayName(user).slice(0, 2).toUpperCase()}</div>
          <div className="user-name" title={user || ""}>{displayName(user)}<small>{provider}</small></div>
          <ChevronDown size={16} color="#62766e" />
          {authOn && (
            <button className="logout" onClick={onLogout} title="Sair" aria-label="Sair"><LogOut size={17} /></button>
          )}
        </div>
      </header>

      {tab === "dashboard" && (
        <>
          <h1 className="title">AI Knowledge RAG</h1>
          <form className="search" onSubmit={submit}>
            <label className="search-field">
              <Search size={22} />
              <input value={question} onChange={(e) => setQuestion(e.target.value)} minLength={3} required
                placeholder="Ask anything to your internal knowledge base..." />
            </label>
            {TOOLS.map(({ id, label, icon: Icon, hint }) => (
              <button key={id} type="button" title={hint} className={`tool ${tools[id] ? "on" : ""}`}
                onClick={() => setTools((t) => ({ ...t, [id]: !t[id] }))}>
                <Icon size={26} strokeWidth={1.6} />
                {label}
              </button>
            ))}
          </form>

          <div className="grid">
            <div className="col">
              {sourceCard(false)}
              <Card title="Document Chunks" menu={chunkMenu}>
                {!result || result.citations.length === 0 ? (
                  <div className="empty">Os trechos recuperados aparecem aqui.</div>
                ) : (
                  <div className="chunks">
                    {result.citations.map((c) => (
                      <div key={c.n} id={`chunk-${c.n}`} className={`chunk ${active === c.n ? "active" : ""}`}>
                        <b>Chunk {c.n}:</b> <span className="clamp">…{c.text}…</span>
                        <div className="src">Source: {c.doc}, p. {c.page} · score {c.score}</div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>

            <Card title="AI-Generated Answer" menu={answerMenu}>
              {loading ? <Skeleton />
                : error ? <div className="error">{error}</div>
                : result ? <AnswerText text={result.answer} onCite={cite} />
                : <div className="empty">Faça uma pergunta para ver a resposta com citações.</div>}

              <div className="divider" />
              <h2 style={{ fontSize: 17, margin: "0 0 4px" }}>References</h2>
              {result?.citations.length ? result.citations.map((c) => (
                <div key={c.n} className={`ref ${active === c.n ? "active" : ""}`}>
                  <PdfIcon tone="green" />
                  <div className="ref-text">
                    {c.doc}, p. {c.page}{" "}
                    <button className="cite" onClick={() => cite(c.n)}>[{c.n}]</button>
                  </div>
                </div>
              )) : <div className="empty">—</div>}

              {m && !loading && (
                <div className="metrics">
                  <span className="chip"><Clock size={13} />{m.total_ms} ms (busca {m.retrieval_ms} · geração {m.generation_ms})</span>
                  <span className="chip"><Cpu size={13} />{m.input_tokens} → {m.output_tokens} tokens</span>
                  <span className="chip"><Coins size={13} />≈ US$ {m.estimated_cost_usd}</span>
                </div>
              )}
            </Card>
          </div>
        </>
      )}

      {tab === "documents" && <div style={{ marginTop: 24 }}>{sourceCard(true)}</div>}

      {tab === "settings" && (
        <div style={{ marginTop: 24 }}>
          <Card title="Settings">
            <div className="settings-row"><span>Provider ativo</span><b>{provider}</b></div>
            <div className="settings-row"><span>Trocar para Bedrock</span><span><code>PROVIDER=bedrock</code> no <code>.env</code></span></div>
            <div className="settings-row"><span>Documentos indexados</span><b>{docs.length}</b></div>
          </Card>
        </div>
      )}

      {toast && <div className={`toast ${toast.err ? "err" : ""}`}>{toast.text}</div>}
    </div>
  );
}
