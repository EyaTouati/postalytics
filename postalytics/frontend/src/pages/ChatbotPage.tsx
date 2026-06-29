import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Database, Lightbulb } from "lucide-react";
import api from "../services/api";
import type { ChatMessage } from "../types";

const EXAMPLE_QUESTIONS = [
  "Quel est le volume total de colis envoyés cette année ?",
  "Quelles régions génèrent le plus d'envois express personnalisés ?",
  "Quel est le chiffre d'affaires vers la France ?",
  "Combien de colis internationaux ont été traités au 2e trimestre ?",
  "Quelle est la destination la plus fréquente hors Tunisie ?",
];

export default function ChatbotPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Bonjour ! Je suis l'assistant analytique de PostalBI. Posez-moi vos questions sur les flux de colis en langage naturel et je consulterai le Data Warehouse pour vous répondre.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastSQL, setLastSQL] = useState<string | null>(null);
  const [showSQL, setShowSQL] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(text?: string) {
    const content = (text ?? input).trim();
    if (!content) return;

    const userMsg: ChatMessage = { role: "user", content };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const { data } = await api.post("/chatbot/", {
        message: content,
        history: messages.slice(-6),
      });
      setMessages([...newMessages, { role: "assistant", content: data.answer }]);
      if (data.sql_query) setLastSQL(data.sql_query);
    } catch {
      setMessages([
        ...newMessages,
        { role: "assistant", content: "Une erreur s'est produite. Veuillez réessayer." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full p-6">
      <div className="mb-4">
        <h1 className="font-display text-2xl font-bold text-navy-900">Assistant IA</h1>
        <p className="text-sm text-gray-400 mt-0.5">
          Posez vos questions en français — je génère et exécute la requête SQL pour vous
        </p>
      </div>

      <div className="flex gap-4 flex-1 min-h-0">
        {/* ── Zone de conversation ── */}
        <div className="flex-1 flex flex-col bg-white rounded-xl shadow-sm border border-surface-muted overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                <div
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    msg.role === "assistant" ? "bg-postal text-white" : "bg-amber-postal text-navy-900"
                  }`}
                >
                  {msg.role === "assistant" ? (
                    <Bot className="w-4 h-4" />
                  ) : (
                    <User className="w-4 h-4" />
                  )}
                </div>
                <div
                  className={`max-w-[75%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                    msg.role === "assistant"
                      ? "bg-surface text-navy-900 rounded-tl-none"
                      : "bg-navy-900 text-white rounded-tr-none"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-postal text-white flex items-center justify-center">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-surface px-4 py-3 rounded-2xl rounded-tl-none">
                  <div className="flex gap-1">
                    {[0, 1, 2].map((i) => (
                      <div
                        key={i}
                        className="w-2 h-2 rounded-full bg-postal animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* SQL debug */}
          {lastSQL && (
            <div className="border-t border-surface-muted px-4 py-2">
              <button
                onClick={() => setShowSQL(!showSQL)}
                className="flex items-center gap-2 text-xs text-gray-400 hover:text-navy-700"
              >
                <Database className="w-3 h-3" />
                {showSQL ? "Masquer" : "Voir"} la requête SQL générée
              </button>
              {showSQL && (
                <pre className="mt-2 text-xs bg-navy-900 text-green-400 p-3 rounded-lg overflow-x-auto">
                  {lastSQL}
                </pre>
              )}
            </div>
          )}

          {/* Input */}
          <div className="border-t border-surface-muted p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
                placeholder="Posez votre question…"
                className="flex-1 px-4 py-2.5 bg-surface border border-surface-muted rounded-xl text-sm
                           focus:outline-none focus:ring-2 focus:ring-postal text-navy-900"
                disabled={loading}
              />
              <button
                onClick={() => sendMessage()}
                disabled={loading || !input.trim()}
                className="btn-primary px-3 rounded-xl disabled:opacity-40"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* ── Questions suggérées ── */}
        <div className="w-64 flex-shrink-0">
          <div className="bg-white rounded-xl shadow-sm border border-surface-muted p-4">
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-4 h-4 text-amber-postal" />
              <h3 className="font-display font-semibold text-sm text-navy-900">Questions suggérées</h3>
            </div>
            <div className="space-y-2">
              {EXAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  disabled={loading}
                  className="w-full text-left text-xs text-gray-600 hover:text-navy-900
                             bg-surface hover:bg-surface-muted px-3 py-2.5 rounded-lg
                             transition-colors leading-relaxed disabled:opacity-40"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
