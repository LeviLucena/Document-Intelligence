import { useEffect, useRef, useState } from "react";
import { FileText, MoreHorizontal, X } from "lucide-react";

export function Menu({ items }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const close = (e) => !ref.current?.contains(e.target) && setOpen(false);
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  return (
    <div ref={ref}>
      <button className="dots" onClick={() => setOpen((o) => !o)} aria-label="Mais opções">
        <MoreHorizontal size={18} />
      </button>
      {open && (
        <div className="menu">
          {items.map(({ label, icon: Icon, onClick }) => (
            <button key={label} onClick={() => { setOpen(false); onClick(); }}>
              <Icon size={15} /> {label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function Card({ title, menu, children, className = "", ...rest }) {
  return (
    <section className={`card ${className}`} {...rest}>
      <div className="card-head">
        <h2>{title}</h2>
        {menu && <Menu items={menu} />}
      </div>
      {children}
    </section>
  );
}

export const fmtDate = (iso) =>
  new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });

export function PdfIcon({ tone = "" }) {
  return (
    <div className={`ficon ${tone}`}>
      <FileText size={18} />
    </div>
  );
}

export function DocRow({ doc, onDelete, detailed }) {
  return (
    <div className="doc">
      <PdfIcon />
      <div className="doc-name" title={doc.name}>
        {doc.name}
        {detailed && <small>{doc.pages} pág. · {doc.chunks} trechos</small>}
      </div>
      <span className="doc-date">{fmtDate(doc.added)}</span>
      <button className="doc-x" onClick={() => onDelete(doc.name)} title="Remover" aria-label={`Remover ${doc.name}`}>
        <X size={15} />
      </button>
    </div>
  );
}

// Transforma "[1]" do texto em botões clicáveis (sem innerHTML).
export function AnswerText({ text, onCite }) {
  return (
    <div className="answer">
      {text.split(/(\[\d+\])/g).map((part, i) => {
        const m = part.match(/^\[(\d+)\]$/);
        return m ? (
          <button key={i} className="cite" onClick={() => onCite(Number(m[1]))}>{part}</button>
        ) : (
          <span key={i}>{part}</span>
        );
      })}
    </div>
  );
}

export const Skeleton = () => (
  <div>
    {[100, 92, 96, 70].map((w, i) => (
      <div key={i} className="skel" style={{ width: `${w}%` }} />
    ))}
  </div>
);
