import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Loader2, ShieldAlert, Paperclip, ChevronDown, ListPlus, Activity } from 'lucide-react';

export function CentralChat() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'bot',
      content: 'Hello Admin. I am the Pineapple Corp RAG assistant powered by Llama 3.1 8B. System telemetry is stable, but I notice an elevated alert volume in the `us-east-1` region.\n\nHow can I assist with your incident response today?',
    },
    {
      id: 2,
      role: 'user',
      content: 'Generate a playbook for a suspected ransomware outbreak on the prod-db-cluster-01.',
    },
    {
      id: 3,
      role: 'bot',
      content: 'Based on our runbooks and current threat intel, I recommend the following immediate actions for `prod-db-cluster-01`:\n\n1. **Isolate:** Disconnect the cluster from the main VPC subnet.\n2. **Preserve:** Capture a memory dump for forensic analysis.\n3. **Identify:** Scan access logs for the initial payload entry point.\n\nShall I execute the automated isolation protocol?',
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = () => {
    if (!input.trim()) return;
    
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: input }]);
    setInput('');
    setIsTyping(true);
    
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        role: 'bot', 
        content: 'Analyzing your request against current threat intelligence feeds. I have identified 3 matching IoCs (Indicators of Compromise) related to recent ransomware variants. \n\nI am compiling a detailed report now. Would you like to review the IoCs while we wait?' 
      }]);
      setIsTyping(false);
    }, 1500);
  };

  return (
    <div className="flex-1 flex flex-col bg-[#F8FAFC] dark:bg-[#15151A] h-full relative z-0">
      {/* Chat Header */}
      <div className="h-14 lg:h-16 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-4 lg:px-8 shrink-0 bg-white/80 dark:bg-[#1C1C22]/80 backdrop-blur-md sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/30">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <h2 className="font-bold text-[15px] text-slate-900 dark:text-white flex items-center gap-1.5 leading-tight">
              Llama 3.1 8B <Sparkles className="h-3.5 w-3.5 text-amber-500" />
            </h2>
            <p className="text-[11px] text-slate-500 font-bold tracking-wide uppercase mt-0.5">Active Session • RAG Copilot</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white dark:bg-[#2A2A35] text-slate-600 dark:text-slate-300 text-xs font-semibold border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
            <ListPlus className="h-4 w-4" />
            Save Chat
          </button>
          <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-bold border border-emerald-100 dark:border-emerald-500/20 shadow-sm">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            System Normal
          </span>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 lg:p-8 space-y-8 scroll-smooth">
        <div className="max-w-4xl mx-auto space-y-8 pb-4">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-4 lg:gap-6 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`h-10 w-10 rounded-full flex items-center justify-center shrink-0 mt-1 shadow-sm ${
                msg.role === 'bot' 
                  ? 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/30' 
                  : 'bg-white dark:bg-[#2A2A35] text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700'
              }`}>
                {msg.role === 'bot' ? <Bot className="h-5 w-5" /> : <User className="h-5 w-5" />}
              </div>
              <div className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} max-w-[85%] lg:max-w-[75%]`}>
                <div className={`px-5 py-4 rounded-3xl text-[14px] lg:text-[15px] leading-relaxed shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-emerald-600 text-white rounded-tr-sm'
                    : 'bg-white dark:bg-[#2A2A35] text-slate-700 dark:text-slate-200 rounded-tl-sm border border-slate-200 dark:border-slate-800/80'
                }`}>
                  {msg.content.split('\n').map((line, i) => {
                    // Simple markdown-like rendering for bold text
                    if (line.includes('**')) {
                      const parts = line.split('**');
                      return (
                        <span key={i} className="block min-h-[1.5em]">
                          {parts.map((part, j) => j % 2 === 1 ? <strong key={j} className="font-bold">{part}</strong> : part)}
                        </span>
                      );
                    }
                    return <span key={i} className="block min-h-[1.5em]">{line}</span>;
                  })}
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    {msg.role === 'user' ? 'Admin User' : 'Pineapple AI'} • {new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </span>
                </div>
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="flex gap-4 lg:gap-6">
              <div className="h-10 w-10 rounded-full bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-200 dark:border-emerald-500/30 shadow-sm">
                <Loader2 className="h-5 w-5 animate-spin" />
              </div>
              <div className="bg-white dark:bg-[#2A2A35] px-5 py-4 rounded-3xl rounded-tl-sm border border-slate-200 dark:border-slate-800/80 shadow-sm flex items-center gap-2">
                <span className="h-2 w-2 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                <span className="h-2 w-2 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="h-2 w-2 bg-emerald-500 rounded-full animate-bounce"></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 lg:p-6 bg-white dark:bg-[#1C1C22] border-t border-slate-200 dark:border-slate-800">
        <div className="max-w-4xl mx-auto relative">
          <div className="relative flex items-end bg-slate-50 dark:bg-[#2A2A35] border border-slate-200 dark:border-slate-700 rounded-2xl shadow-sm focus-within:border-emerald-500 dark:focus-within:border-emerald-500/50 focus-within:ring-4 focus-within:ring-emerald-500/10 transition-all overflow-hidden">
            <button className="p-3.5 text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors shrink-0">
              <Paperclip className="h-5 w-5" />
            </button>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask for playbooks, investigate alerts, or request summaries..."
              className="w-full py-3.5 px-2 bg-transparent text-[15px] placeholder:text-slate-400 dark:placeholder:text-slate-500 text-slate-900 dark:text-white focus:outline-none resize-none max-h-32 min-h-[52px]"
              rows={1}
              style={{ height: '52px' }}
            />
            <div className="p-2 shrink-0 flex items-center gap-2">
              <button
                onClick={handleSend}
                disabled={!input.trim() || isTyping}
                className="p-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white rounded-xl transition-colors disabled:cursor-not-allowed shadow-sm"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
          </div>
          <div className="flex items-center justify-between mt-3 px-2">
            <p className="text-[11px] text-slate-400 font-semibold flex items-center gap-1.5">
              <ShieldAlert className="h-3.5 w-3.5" />
              AI responses should be verified before taking critical system actions.
            </p>
            <p className="text-[11px] text-slate-400 font-semibold hidden sm:block">
              Press <kbd className="font-sans px-1.5 py-0.5 rounded bg-slate-100 dark:bg-[#2A2A35] border border-slate-200 dark:border-slate-700">Enter</kbd> to send
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
