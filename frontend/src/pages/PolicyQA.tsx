import { useState, useRef, useEffect } from "react";
import { Send, BookOpen } from "lucide-react";
import { askPolicyQuestion } from "../api/policyQa";
import { CitationBadge } from "../components/CitationBadge";
import type { CitedClause } from "../types";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: CitedClause[];
  refused?: boolean;
  refusal_reason?: string | null;
}

export default function PolicyQA() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const question = input.trim();
    if (!question || loading) return;

    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    const userMsg: ChatMessage = { role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const resp = await askPolicyQuestion(question, history);
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: resp.refused ? "" : resp.answer,
        citations: resp.citations,
        refused: resp.refused,
        refusal_reason: resp.refusal_reason,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 flex flex-col h-[calc(100vh-4rem)]">
      <div className="flex items-center gap-2 mb-6">
        <BookOpen className="w-6 h-6 text-blue-600" aria-hidden />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Policy Library Q&A</h1>
          <p className="text-sm text-gray-500">Ask anything about Northwind T&E policies</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-1">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 text-sm mt-12">
            <p>Try asking:</p>
            <p className="mt-2 font-medium text-gray-600">"What is the meal cap for solo travel?"</p>
            <p className="mt-1 font-medium text-gray-600">"What class can I fly for domestic trips?"</p>
            <p className="mt-1 font-medium text-gray-600">"Can I expense alcohol at a client dinner?"</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : msg.refused
                  ? "bg-gray-100 text-gray-600 border border-gray-200"
                  : "bg-white border border-gray-200 text-gray-800"
              }`}
            >
              {msg.role === "user" ? (
                <p className="text-sm">{msg.content}</p>
              ) : msg.refused ? (
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-1">Out of scope</p>
                  <p className="text-sm">{msg.refusal_reason ?? "This question is outside the T&E policy scope."}</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="border-t border-gray-100 pt-2 mt-2">
                      <p className="text-xs text-gray-400 mb-1">Citations</p>
                      {msg.citations.map((c, ci) => (
                        <div key={ci} className="mb-2">
                          <div className="flex items-center gap-1 mb-1">
                            <CitationBadge docIds={[c.doc_id]} />
                            <span className="text-xs text-gray-500">{c.section_id} — {c.section_title}</span>
                          </div>
                          <p className="text-xs text-gray-500 italic bg-gray-50 rounded p-2">{c.text.slice(0, 300)}…</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
              <div className="flex gap-1 items-center text-gray-400 text-sm">
                <span className="animate-pulse">Searching policies</span>
                <span className="animate-bounce delay-75">.</span>
                <span className="animate-bounce delay-150">.</span>
                <span className="animate-bounce delay-200">.</span>
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {error && <p className="text-sm text-red-600 mb-2">{error}</p>}

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Ask a policy question…"
          disabled={loading}
          aria-label="Policy question input"
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          className="bg-blue-600 text-white rounded-xl px-4 py-2.5 hover:bg-blue-700 disabled:opacity-50 transition-colors"
          aria-label="Send question"
        >
          <Send className="w-4 h-4" aria-hidden />
        </button>
      </div>
    </div>
  );
}
