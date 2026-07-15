"use client"
import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";

export default function Home() {

  const [messages, setMessages] = useState<{role:string;content:string}[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [repoUrl, setRepoUrl] = useState("")
  const [isIngesting, setIsIngesting] = useState(false)
  const [ingestMessage, setIngestMessage] = useState("")
  const [activeRepo, setActiveRepo] = useState("")

  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  const handleIngest = async () => {
    if (!repoUrl.trim()) return;
    const targetUrl = repoUrl.trim();
    setIsIngesting(true);
    setIngestMessage("Cloning repository and generating embeddings. This may take up to a minute...");

    try {
      const response = await fetch("/api/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: targetUrl }),
      });
      const data = await response.json();
      if (response.ok) {
        setIngestMessage(`Ready. Indexed ${data.files_scanned} files across ${data.chunks_created} chunks.`);
        setActiveRepo(targetUrl);
        setMessages([]);
      } else {
        setIngestMessage("Ingestion failed. Please check the URL and try again.");
      }
    } catch {
      setIngestMessage("Could not connect to the server. Is the backend running?");
    } finally {
      setIsIngesting(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !activeRepo) return;

    const newMessages = [...messages, { role: "user", content: input }]
    setMessages(newMessages)
    setInput("")
    setIsLoading(true)

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newMessages, url: activeRepo })
      })
      const data = await response.json()
      if (data.answer) {
        setMessages((prev) => [...prev, { role: "assistant", content: data.answer }])
      }
    } catch {
      // silently fail
    } finally {
      setIsLoading(false)
    }
  }

  const ingestStatusColor = ingestMessage.includes("Ready")
    ? "text-emerald-600"
    : ingestMessage.includes("failed") || ingestMessage.includes("Could not")
    ? "text-red-500"
    : "text-zinc-400"

  return (
    <div className="h-screen flex flex-col bg-white text-zinc-900 font-sans antialiased overflow-hidden">

      {/* Header */}
      <header className="flex-shrink-0 bg-white border-b border-zinc-200 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
          <span className="font-semibold text-sm tracking-tight text-zinc-800">DevDocs RAG</span>
          <span className="text-xs text-zinc-400 hidden sm:block">/ AI-Powered Codebase Explorer</span>
        </div>
        <div className="flex items-center gap-3">
          {activeRepo && (
            <span className="text-xs bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-md border border-emerald-200 font-mono truncate max-w-[220px]">
              {activeRepo.split("/").slice(-2).join("/")}
            </span>
          )}
          <span className="text-xs font-medium bg-zinc-100 text-zinc-500 px-3 py-1.5 rounded-full border border-zinc-200">
            pgVector + LLaMA 3
          </span>
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">

        {/* Sidebar */}
        <aside className="w-72 flex-shrink-0 hidden lg:flex flex-col bg-zinc-50 border-r border-zinc-200 p-5 gap-6 overflow-y-auto">

          {/* Step 1 - Ingest */}
          <div>
            <p className="text-[10px] font-semibold text-zinc-400 uppercase tracking-widest mb-3">Step 1 — Load a Repository</p>
            <div className="flex flex-col gap-2">
              <input
                type="text"
                className="w-full bg-white border border-zinc-300 rounded-lg px-3 py-2.5 text-sm text-zinc-800 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-400 transition-all"
                placeholder="https://github.com/user/repo"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleIngest()}
                disabled={isIngesting}
              />
              <button
                onClick={handleIngest}
                disabled={isIngesting || !repoUrl.trim()}
                className="w-full bg-indigo-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-700 active:scale-[0.98] disabled:bg-zinc-200 disabled:text-zinc-400 disabled:cursor-not-allowed transition-all"
              >
                {isIngesting ? "Processing..." : "Ingest Repository"}
              </button>
            </div>
            {ingestMessage && (
              <p className={`text-xs mt-2.5 leading-relaxed ${ingestStatusColor} ${!ingestMessage.includes("Ready") && !ingestMessage.includes("failed") && !ingestMessage.includes("Could not") ? "animate-pulse" : ""}`}>
                {ingestMessage}
              </p>
            )}
          </div>

          <div className="border-t border-zinc-200" />

          {/* Step 2 - How to use */}
          <div>
            <p className="text-[10px] font-semibold text-zinc-400 uppercase tracking-widest mb-3">Step 2 — How to Use</p>
            <ul className="space-y-3">
              {[
                { label: "1", text: "Paste a public GitHub repository URL above and click Ingest." },
                { label: "2", text: "Wait for the success message. Ingestion may take up to 60 seconds." },
                { label: "3", text: "Ask any question about the codebase in the chat panel." },
                { label: "4", text: "Re-ingest a different repository at any time to switch context." },
              ].map((item) => (
                <li key={item.label} className="flex gap-3 items-start">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-indigo-100 text-indigo-600 text-[10px] font-bold flex items-center justify-center mt-0.5">
                    {item.label}
                  </span>
                  <span className="text-xs text-zinc-500 leading-snug">{item.text}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="border-t border-zinc-200" />

          {/* Step 3 - Suggestions */}
          <div>
            <p className="text-[10px] font-semibold text-zinc-400 uppercase tracking-widest mb-3">Step 3 — Try These Questions</p>
            <ul className="space-y-2">
              {[
                "What is the overall folder structure?",
                "How does authentication work?",
                "Where is the database connection defined?",
                "Explain the main API routes.",
              ].map((q, i) => (
                <li
                  key={i}
                  onClick={() => { if (activeRepo) setInput(q); }}
                  className={`text-xs text-zinc-500 bg-white border border-zinc-200 px-3 py-2 rounded-lg leading-snug transition-all
                    ${activeRepo ? "cursor-pointer hover:border-indigo-300 hover:text-indigo-600 hover:bg-indigo-50" : "opacity-40 cursor-not-allowed"}`}
                >
                  {q}
                </li>
              ))}
            </ul>
          </div>

        </aside>

        {/* Chat Panel */}
        <div className="flex-1 flex flex-col overflow-hidden">

          {/* Mobile ingest bar */}
          <div className="lg:hidden flex-shrink-0 bg-zinc-50 border-b border-zinc-200 px-4 py-3 flex gap-2">
            <input
              type="text"
              className="flex-1 bg-white border border-zinc-300 rounded-lg px-3 py-2 text-sm text-zinc-800 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 transition-all"
              placeholder="https://github.com/user/repo"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              disabled={isIngesting}
            />
            <button
              onClick={handleIngest}
              disabled={isIngesting || !repoUrl.trim()}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:bg-zinc-200 disabled:text-zinc-400 disabled:cursor-not-allowed transition-all whitespace-nowrap"
            >
              {isIngesting ? "..." : "Ingest"}
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5 bg-white">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center select-none">
                <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <p className="text-sm font-medium text-zinc-500">No messages yet</p>
                <p className="text-xs text-zinc-400 mt-1">
                  {activeRepo ? `Ask a question about ${activeRepo.split("/").pop()}` : "Ingest a repository from the sidebar to get started"}
                </p>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div key={index} className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`px-4 py-3 max-w-[80%] text-sm leading-relaxed
                      ${msg.role === "user"
                        ? "bg-indigo-600 text-white rounded-2xl rounded-tr-sm shadow-sm shadow-indigo-200"
                        : "bg-zinc-50 text-zinc-700 rounded-2xl rounded-tl-sm border border-zinc-200"}`}
                  >
                    {msg.role === "user" ? (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <ReactMarkdown
                        components={{
                          code(props) {
                            const { children, className, ...rest } = props
                            const match = /language-(\w+)/.exec(className || '')
                            return !match ? (
                              <code {...rest} className="bg-white border border-zinc-200 text-indigo-600 px-1.5 py-0.5 rounded text-xs font-mono">
                                {children}
                              </code>
                            ) : (
                              <div className="bg-zinc-900 text-zinc-100 p-4 rounded-xl overflow-x-auto my-3 text-xs font-mono border border-zinc-800">
                                <code {...rest} className={className}>{children}</code>
                              </div>
                            )
                          },
                          p({ children }) { return <p className="mb-2 last:mb-0">{children}</p> },
                          ul({ children }) { return <ul className="list-disc ml-4 mb-2 space-y-1">{children}</ul> },
                          ol({ children }) { return <ol className="list-decimal ml-4 mb-2 space-y-1">{children}</ol> },
                          h3({ children }) { return <h3 className="font-semibold text-zinc-800 mt-3 mb-1">{children}</h3> },
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    )}
                  </div>
                </div>
              ))
            )}

            {/* Typing indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-zinc-50 px-4 py-3.5 rounded-2xl rounded-tl-sm border border-zinc-200 flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Input bar */}
          <div className="flex-shrink-0 px-6 py-4 bg-white border-t border-zinc-200 flex gap-3 items-center">
            <input
              type="text"
              className="flex-1 bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3 text-sm text-zinc-800 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-400 transition-all"
              placeholder={activeRepo ? `Ask about ${activeRepo.split("/").pop()}...` : "Ingest a repository to begin..."}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              disabled={isLoading || !activeRepo}
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !input.trim() || !activeRepo}
              className="bg-indigo-600 text-white px-5 py-3 rounded-xl text-sm font-medium hover:bg-indigo-700 active:scale-[0.98] disabled:bg-zinc-100 disabled:text-zinc-400 disabled:cursor-not-allowed transition-all flex items-center gap-2 min-w-[88px] justify-center"
            >
              {isLoading ? (
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  Send
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </>
              )}
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
