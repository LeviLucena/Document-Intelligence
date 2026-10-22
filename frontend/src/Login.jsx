import { useState } from "react";
import { Eye, EyeOff, ListFilter, Loader2, Lock, Mail } from "lucide-react";
import * as api from "./api";

function GlassLogo({ size = "lg" }) {
  return (
    <span className={`glass-logo ${size}`}>
      <ListFilter strokeWidth={2.2} />
    </span>
  );
}

export default function Login({ onSuccess, expired }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(expired ? "Sua sessão expirou. Entre novamente." : "");

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const r = await api.login(email, password);
      api.setToken(r.token);
      onSuccess(r.email);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="auth">
      <aside className="auth-hero">
        <span className="orb orb-a" />
        <span className="orb orb-b" />
        <div className="brand">
          <GlassLogo />
          <span>AI Search</span>
        </div>
        <div className="hero-copy">
          <h2>Do documento à resposta, com fontes e citações.</h2>
          <p>
            Envie seus PDFs empresariais, faça perguntas em linguagem natural e receba respostas
            fundamentadas, com a página de cada trecho usado. Powered by Amazon Bedrock.
          </p>
        </div>
        <p className="hero-foot">Enterprise Document Intelligence · 2026</p>
      </aside>

      <main className="auth-main">
        <form className="auth-card" onSubmit={submit} noValidate={false}>
          <div className="auth-card-logo"><GlassLogo size="md" /></div>
          <h1>Bem-vindo ao AI Search</h1>
          <p className="sub">Entre para consultar sua base de conhecimento</p>

          <label className="field">
            <span>E-mail</span>
            <div className="input">
              <Mail size={17} />
              <input type="email" autoComplete="username" placeholder="seu@email.com" value={email}
                onChange={(e) => setEmail(e.target.value)} disabled={loading} required autoFocus />
            </div>
          </label>

          <label className="field">
            <span>Senha</span>
            <div className="input">
              <Lock size={17} />
              <input type={show ? "text" : "password"} autoComplete="current-password" placeholder="••••••••"
                value={password} onChange={(e) => setPassword(e.target.value)} disabled={loading} required />
              <button type="button" className="eye" onClick={() => setShow((s) => !s)}
                aria-label={show ? "Ocultar senha" : "Mostrar senha"}>
                {show ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
          </label>

          {error && <div className="auth-error" role="alert">{error}</div>}

          <button className="submit" type="submit" disabled={loading || !email || !password}>
            {loading ? <><Loader2 size={17} className="spin" /> Entrando...</> : "Entrar"}
          </button>
        </form>
      </main>
    </div>
  );
}
