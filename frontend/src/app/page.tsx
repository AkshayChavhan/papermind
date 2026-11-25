"use client";

import { useState, type FormEvent, type ReactNode } from "react";

type Message = {
  role: "user" | "assistant";
  text: string;
  grounded?: boolean;
  pages?: string[];
  streaming?: boolean;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const CITATION_PATTERN = /(\(page [\w.]+\))/gi;

function renderWithCitations(text: string): ReactNode[] {
  return text.split(CITATION_PATTERN).map((part, index) =>
    /^\(page [\w.]+\)$/i.test(part) ? (
      <span key={index} className="citation">
        {part}
      </span>
    ) : (
      <span key={index}>{part}</span>
    ),
  );
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);

  async function ask(event: FormEvent) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) return;

    setQuestion("");
    setLoading(true);
    setMessages((prev) => [
      ...prev,
      { role: "user", text: trimmed },
      { role: "assistant", text: "", streaming: true },
    ]);

    try {
      const response = await fetch(`${API_URL}/ask/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });

      if (!response.body) {
        throw new Error("No response body from /ask/stream");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";

        for (const rawEvent of events) {
          const line = rawEvent.replace(/^data: /, "").trim();
          if (!line) continue;
          const payload = JSON.parse(line);

          if (payload.type === "token") {
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              next[next.length - 1] = { ...last, text: last.text + payload.text };
              return next;
            });
          } else if (payload.type === "done") {
            setMessages((prev) => {
              const next = [...prev];
              next[next.length - 1] = {
                role: "assistant",
                text: payload.answer,
                grounded: payload.grounded,
                pages: payload.pages,
                streaming: false,
              };
              return next;
            });
          }
        }
      }
    } catch {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: "assistant",
          text: "Something went wrong talking to the backend.",
          streaming: false,
        };
        return next;
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="chat">
      <h1>papermind</h1>
      <div className="messages">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div className="bubble">
              {renderWithCitations(message.text)}
              {message.streaming && <span className="cursor">▌</span>}
            </div>
            {message.role === "assistant" && !message.streaming && (
              <div className="meta">
                {message.grounded ? "grounded" : "not grounded"}
                {message.pages && message.pages.length > 0 && ` · pages: ${message.pages.join(", ")}`}
              </div>
            )}
          </div>
        ))}
      </div>
      <form onSubmit={ask} className="composer">
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about the uploaded PDF"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !question.trim()}>
          Ask
        </button>
      </form>
    </main>
  );
}
