import { useEffect, useState } from "react";

export default function App() {
  const [patients, setPatients] = useState([]);
  const [selected, setSelected] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [meta, setMeta] = useState("");

  useEffect(() => {
    fetch("/api/patients").then((r) => r.json()).then(setPatients).catch(() => {});
  }, []);

  async function ask(e) {
    e.preventDefault();
    setLoading(true);
    setAnswer("");
    try {
      const r = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, patient_id: selected || null }),
      });
      const d = await r.json();
      setAnswer(d.answer ?? d.detail);
      setMeta(d.provider ? `${d.provider} · ${d.model}` : "");
    } catch {
      setAnswer("Could not reach the API.");
    }
    setLoading(false);
  }

  return (
    <main>
      <header>
        <h1>Project Name</h1>
        <p className="tag">Synthetic data only · Decision support, not diagnosis</p>
      </header>

      <form onSubmit={ask}>
        <label htmlFor="patient">Synthetic patient</label>
        <select id="patient" value={selected} onChange={(e) => setSelected(e.target.value)}>
          <option value="">— none —</option>
          {patients.map((p) => (
            <option key={p.id} value={p.id}>
              {p.id} · {p.age_band} · {p.condition} · {p.pathway_stage}
            </option>
          ))}
        </select>

        <label htmlFor="q">Question</label>
        <textarea id="q" rows={3} value={question} onChange={(e) => setQuestion(e.target.value)} required />

        <button disabled={loading}>{loading ? "Thinking…" : "Ask"}</button>
      </form>

      {answer && (
        <section className="answer" aria-live="polite">
          <h2>Response</h2>
          {meta && <p className="tag">AI: {meta}</p>}
          <p>{answer}</p>
        </section>
      )}
    </main>
  );
}
