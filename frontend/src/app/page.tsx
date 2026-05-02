"use client"
import { useState } from "react";

export default function Home() {
  
  const [messages, setMessages] = useState<{role:string;content:string}[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)

 
  const [repoUrl, setRepoUrl] = useState("")
  const [isIngesting, setIsIngesting] = useState(false)
  const [ingestMessage, setIngestMessage] = useState("")

 
  const handleIngest = async () => {
    if (!repoUrl.trim()) return;
    
    setIsIngesting(true);
    setIngestMessage("Downloading and processing repository... this may take a minute.");

    try {
      const response = await fetch("/api/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: repoUrl }),
      });

      const data = await response.json();

      if (response.ok) {
        setIngestMessage(`Success! Embedded ${data.files_scanned} files into ${data.chunks_created} chunks.`);

        setMessages([]);
      } else {
        setIngestMessage(`Error: ${data.detail || data.error || 'Failed to ingest'}`);
      }


    } catch (error) {
      console.error("Ingestion error:", error);
      setIngestMessage("Failed to connect to server.");
    } finally {
      setIsIngesting(false);
    }
  };

  const sendMessage = async() => {
    if(!input.trim()) return;

    const newMessages = [...messages, {role: "user", content: input}]
    setMessages(newMessages)
    setInput("")
    setIsLoading(true)

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newMessages })
      })

      const data = await response.json()

      if(data.answer) {
        setMessages((prev) => [...prev, {role: "assistant", content: data.answer}])
      }

    } catch(error) {
      console.log("Chat error: ", error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 sm:p-8 bg-zinc-50 text-zinc-900 font-sans antialiased">
      <div className="w-full max-w-4xl bg-white rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-zinc-100 overflow-hidden flex flex-col h-[85vh]">

        
        <div className="bg-white/80 backdrop-blur-xl border-b border-zinc-100 px-6 py-5 flex justify-between items-center z-10">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></div>
            <span className="font-semibold text-lg tracking-tight text-zinc-800">Enterprise RAG Assistant</span>
          </div>
          <span className="text-xs font-medium bg-zinc-100 text-zinc-600 px-3 py-1.5 rounded-full border border-zinc-200/60 shadow-sm">
            pgVector + LLaMA 3
          </span>
        </div>

        {/*  Ingestion Bar */}
        <div className="bg-zinc-50/50 border-b border-zinc-100 px-6 py-4 flex flex-col gap-3">
          <div className="flex gap-3 items-center">
            <input
              type="text"
              className="flex-1 bg-white border border-zinc-200 rounded-xl px-4 py-2.5 text-[15px] text-zinc-800 placeholder:text-zinc-400 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-400 transition-all shadow-sm"
              placeholder="Paste GitHub Repository URL (e.g., https://github.com/user/repo)"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              disabled={isIngesting}
            />
            <button
              onClick={handleIngest}
              disabled={isIngesting || !repoUrl.trim()}
              className="bg-indigo-600 text-white px-5 py-2.5 rounded-xl text-[15px] font-medium hover:bg-indigo-700 active:scale-[0.98] disabled:bg-indigo-400 disabled:cursor-not-allowed transition-all shadow-sm whitespace-nowrap"
            >
              {isIngesting ? "Processing..." : "Ingest Repo"}
            </button>
          </div>
          {/* Status Message */}
          {ingestMessage && (
            <p className={`text-sm font-medium ${ingestMessage.includes('✅') ? 'text-emerald-600' : ingestMessage.includes('❌') ? 'text-red-500' : 'text-zinc-500 animate-pulse'}`}>
              {ingestMessage}
            </p>
          )}
        </div>

        {/* Chat area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-zinc-50/30 scroll-smooth">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-zinc-400 animate-in fade-in duration-700">
              <div className="bg-white p-4 rounded-full shadow-sm border border-zinc-100 mb-4">
                <svg className="w-8 h-8 text-indigo-500/80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path>
                </svg>
              </div>
              <p className="text-sm font-medium text-zinc-500">First ingest a repo, then ask your questions here...</p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div 
                  className={`px-5 py-3.5 max-w-[85%] text-[15px] leading-relaxed shadow-sm transition-all 
                  ${msg.role === "user" 
                    ? "bg-indigo-600 text-white rounded-2xl rounded-tr-sm shadow-indigo-600/20" 
                    : "bg-white text-zinc-700 rounded-2xl rounded-tl-sm border border-zinc-100"}`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))
          )}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white px-5 py-4 rounded-2xl rounded-tl-sm border border-zinc-100 shadow-sm flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="p-4 sm:p-5 bg-white border-t border-zinc-100 flex gap-3 items-center">
          <input 
            type="text"
            className="flex-1 bg-zinc-50 border border-zinc-200 rounded-xl px-5 py-3.5 text-[15px] text-zinc-800 placeholder:text-zinc-400 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-400 transition-all"
            placeholder="e.g., How does the database connection work in db.py?"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            disabled={isLoading}
          />

          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="bg-zinc-900 text-white px-6 py-3.5 rounded-xl font-medium hover:bg-zinc-800 active:scale-[0.98] disabled:bg-zinc-100 disabled:text-zinc-400 disabled:cursor-not-allowed transition-all shadow-sm flex items-center justify-center min-w-[100px]"
          >
            Send
          </button>
        </div>
        
      </div>
    </div>
  );
}