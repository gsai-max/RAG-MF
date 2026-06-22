import { useState, useEffect, useRef } from 'react';

interface Fund {
  slug: string;
  scheme_name: string;
  category: string;
  source_url: string;
  nav: string;
  nav_date: string;
}

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  citation_url?: string;
  last_updated?: string;
  is_refusal?: boolean;
  disclaimer?: string;
}

// 6 default funds to display as fallbacks if endpoint fails
const DEFAULT_FUNDS: Fund[] = [
  {
    slug: "icici-prudential-commodities-fund-direct-growth",
    scheme_name: "ICICI Prudential Commodities Fund",
    category: "Equity — Sectoral/Thematic",
    source_url: "https://groww.in/mutual-funds/icici-prudential-commodities-fund-direct-growth",
    nav: "₹51.71",
    nav_date: "19-Jun-2026"
  },
  {
    slug: "icici-prudential-large-cap-fund-direct-growth",
    scheme_name: "ICICI Prudential Large Cap Fund",
    category: "Equity — Large Cap",
    source_url: "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
    nav: "₹119.13",
    nav_date: "19-Jun-2026"
  },
  {
    slug: "icici-prudential-technology-fund-direct-growth",
    scheme_name: "ICICI Prudential Technology Direct Plan-Growth",
    category: "Equity — Sectoral/Thematic",
    source_url: "https://groww.in/mutual-funds/icici-prudential-technology-fund-direct-growth",
    nav: "₹187.48",
    nav_date: "19-Jun-2026"
  },
  {
    slug: "icici-prudential-value-direct-growth",
    scheme_name: "ICICI Prudential Value Discovery Fund",
    category: "Equity — Value Oriented",
    source_url: "https://groww.in/mutual-funds/icici-prudential-value-direct-growth",
    nav: "₹508.63",
    nav_date: "19-Jun-2026"
  },
  {
    slug: "icici-prudential-dynamic-plan-direct-growth",
    scheme_name: "ICICI Prudential Multi-Asset Fund",
    category: "Hybrid — Multi Asset Allocation",
    source_url: "https://groww.in/mutual-funds/icici-prudential-dynamic-plan-direct-growth",
    nav: "₹890.03",
    nav_date: "19-Jun-2026"
  },
  {
    slug: "icici-prudential-balanced-direct-growth",
    scheme_name: "ICICI Prudential Equity & Debt Fund",
    category: "Hybrid — Aggressive Hybrid",
    source_url: "https://groww.in/mutual-funds/icici-prudential-balanced-direct-growth",
    nav: "₹449.10",
    nav_date: "19-Jun-2026"
  }
];

export default function App() {
  // Navigation tab for mobile view: 'chat' | 'history' | 'funds'
  const [activeTab, setActiveTab] = useState<'chat' | 'history' | 'funds'>('chat');
  
  // Modal state (desktop centered dialog, mobile full-screen)
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Funds & selections
  const [funds, setFunds] = useState<Fund[]>(DEFAULT_FUNDS);
  const [selectedSlugs, setSelectedSlugs] = useState<string[]>([]);
  
  // Chat state
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome-1",
      sender: "assistant",
      text: "Hello! I am your Mutual Fund FAQ Assistant. I can help you with factual details (like exit load, expense ratio, fund managers, and NAV) for ICICI Prudential schemes.",
      is_refusal: false,
      disclaimer: "Facts-only. No investment advice."
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Simple history of past user prompts
  const [promptHistory, setPromptHistory] = useState<string[]>([]);
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Fetch fund registry metadata from the backend
  useEffect(() => {
    fetch('/api/funds')
      .then(res => {
        if (!res.ok) throw new Error("Backend server error");
        return res.json();
      })
      .then((data: Fund[]) => {
        if (Array.isArray(data) && data.length > 0) {
          // Clean schema fields just in case
          const formatted = data.map(f => ({
            ...f,
            scheme_name: f.scheme_name.replace(/Direct Growth|Direct Plan Growth/gi, '').trim()
          }));
          setFunds(formatted);
        }
      })
      .catch(err => {
        console.warn("Failed to fetch funds registry, using fallbacks:", err);
      });
  }, []);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Handle mobile bottom nav navigation
  const handleMobileNav = (tab: 'chat' | 'history' | 'funds') => {
    setActiveTab(tab);
    if (tab === 'funds') {
      setIsModalOpen(true);
      setActiveTab('chat'); // Reset back to chat in background
    }
  };

  // Click handler for selected fund checkbox toggle
  const toggleFundSelection = (slug: string) => {
    setSelectedSlugs(prev =>
      prev.includes(slug)
        ? prev.filter(s => s !== slug)
        : [...prev, slug]
    );
  };

  const handleClearAll = () => {
    setSelectedSlugs([]);
  };

  const handleApplySelection = () => {
    setIsModalOpen(false);
  };

  // Assemble message payload and send to backend
  const handleSendMessage = async (textToSend: string) => {
    const cleanText = textToSend.trim();
    if (!cleanText) return;

    // Create unique message IDs
    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `assistant-${Date.now()}`;

    // Add user message to state
    const newUserMessage: Message = {
      id: userMsgId,
      sender: 'user',
      text: cleanText
    };
    
    setMessages(prev => [...prev, newUserMessage]);
    setPromptHistory(prev => [cleanText, ...prev.filter(p => p !== cleanText)]);
    setInputText('');
    setIsLoading(true);

    // Apply scoping logic: If 1 fund is selected and its name isn't mentioned in the text, suffix it
    let messagePayload = cleanText;
    if (selectedSlugs.length === 1) {
      const selectedFund = funds.find(f => f.slug === selectedSlugs[0]);
      if (selectedFund) {
        const nameKeywords = ['icici', 'prudential', 'commodities', 'bluechip', 'technology', 'value', 'asset'];
        const textLower = cleanText.toLowerCase();
        const mentionsFund = nameKeywords.some(kw => textLower.includes(kw));

        if (!mentionsFund) {
          messagePayload = `${cleanText} on ${selectedFund.scheme_name}`;
        }
      }
    }

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messagePayload,
          selected_funds: selectedSlugs
        })
      });

      if (!response.ok) {
        throw new Error("API call failed");
      }

      const data = await response.json();
      
      const newAssistantMessage: Message = {
        id: assistantMsgId,
        sender: 'assistant',
        text: data.answer,
        citation_url: data.citation_url,
        last_updated: data.last_updated,
        is_refusal: data.is_refusal,
        disclaimer: data.disclaimer
      };
      
      setMessages(prev => [...prev, newAssistantMessage]);
    } catch (error) {
      console.error("Error calling chat API:", error);
      const errorMessage: Message = {
        id: assistantMsgId,
        sender: 'assistant',
        text: "Sorry, I am having trouble reaching the server. Please ensure the backend is running and try again.",
        is_refusal: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleClick = (question: string) => {
    // Set appropriate selected fund if applicable
    if (question.includes("Commodities Fund")) {
      const commFund = funds.find(f => f.slug.includes("commodities"));
      if (commFund) setSelectedSlugs([commFund.slug]);
    } else if (question.includes("Large Cap Fund")) {
      const lcFund = funds.find(f => f.slug.includes("large-cap"));
      if (lcFund) setSelectedSlugs([lcFund.slug]);
    } else if (question.includes("Technology")) {
      const techFund = funds.find(f => f.slug.includes("technology"));
      if (techFund) setSelectedSlugs([techFund.slug]);
    }
    
    handleSendMessage(question);
  };

  // Filtered funds list for modal search
  const filteredFunds = funds.filter(fund => {
    const q = searchQuery.toLowerCase();
    return fund.scheme_name.toLowerCase().includes(q) || fund.category.toLowerCase().includes(q);
  });

  return (
    <div className="bg-[#F8FAFC] text-[#1E293B] font-body-md text-[14px] min-h-screen flex flex-col antialiased">
      
      {/* TopAppBar - Desktop Only */}
      <header className="hidden md:flex fixed top-0 left-0 w-full z-50 justify-between items-center px-padding-global h-16 bg-white/80 backdrop-blur-md shadow-sm border-b border-slate-200">
        <div className="flex items-center gap-2">
          <span className="font-headline-md text-[24px] font-bold text-[#006c50]">Mutual Fund Assistant</span>
        </div>
        <div className="flex items-center gap-4 text-[#006c50]">
          {/* Select Funds button */}
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-[#00b589] text-white rounded-full font-label-md text-[13px] hover:opacity-90 transition-all active:scale-[0.98] shadow-sm mr-2"
          >
            <span className="material-symbols-outlined text-[20px]">account_balance_wallet</span>
            {selectedSlugs.length > 0 ? `Selected Funds (${selectedSlugs.length})` : 'Select Funds'}
          </button>
          
          <button className="hover:bg-slate-100 transition-colors p-2 rounded-full flex items-center justify-center opacity-80 hover:opacity-100">
            <span className="material-symbols-outlined">info</span>
          </button>
          <button className="hover:bg-slate-100 transition-colors p-2 rounded-full flex items-center justify-center opacity-80 hover:opacity-100">
            <span className="material-symbols-outlined">help</span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col items-center pt-0 md:pt-24 pb-20 md:pb-28 px-4 md:px-gutter w-full">
        {/* Central Chat Container */}
        <div className="w-full max-w-container-max bg-white border border-slate-200 shadow-xl md:rounded-2xl flex flex-col overflow-hidden md:min-h-[70vh] min-h-[calc(100vh-64px)] w-screen md:w-full flex-1">
          
          {/* Local Header (Inside Container) */}
          <div className="w-full py-4 px-6 border-b border-slate-200 bg-white/50 flex items-center justify-between md:justify-center">
            <h1 className="font-headline-md text-[20px] font-semibold text-[#0F172A] text-center flex-1">
              Mutual Fund Assistant
            </h1>
            {/* Mobile Modal Trigger */}
            <button 
              onClick={() => setIsModalOpen(true)} 
              className="md:hidden flex items-center justify-center p-2 rounded-full bg-slate-100 hover:bg-slate-200 text-[#006c50] transition-colors"
            >
              <span className="material-symbols-outlined text-[22px]">account_balance_wallet</span>
              {selectedSlugs.length > 0 && (
                <span className="absolute top-2 right-12 w-4 h-4 bg-red-500 text-white text-[9px] rounded-full flex items-center justify-center font-bold">
                  {selectedSlugs.length}
                </span>
              )}
            </button>
          </div>

          {/* Disclaimer Banner */}
          <div className="w-full bg-[#FFFBEB] text-[#B45309] font-label-md text-[13px] py-2 px-4 flex justify-center items-center font-medium">
            <span>⚠️ Facts-only. No investment advice.</span>
          </div>

          {/* Chat Messaging Area */}
          <div className="flex-1 p-4 md:p-6 flex flex-col gap-gap-bubble overflow-y-auto min-h-[40vh]">
            <div className="flex flex-col gap-6 w-full">
              
              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-message-enter`}>
                  {msg.sender === 'user' ? (
                    /* User Chat Bubble */
                    <div className="max-w-[80%] bg-[#00b589] text-white p-4 rounded-2xl rounded-br-[2px] shadow-sm">
                      <p className="font-body-lg text-[15px] whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                    </div>
                  ) : (
                    /* Assistant Chat Bubble */
                    <div className="max-w-[85%] bg-white border border-slate-200 p-4 rounded-2xl rounded-bl-[2px] shadow-[0_2px_4px_rgba(0,0,0,0.02)]">
                      {/* Answer Text */}
                      <div className="text-[#0F172A] font-body-lg text-[15px] leading-relaxed whitespace-pre-wrap">
                        {msg.text}
                      </div>

                      {/* Citation block if present */}
                      {msg.citation_url && (
                        <div className="mt-2 pt-2 border-t border-slate-100 flex flex-wrap items-center gap-x-2 gap-y-1">
                          <span className="text-[#64748B] font-semibold text-[13px]">Sources:</span>
                          {msg.citation_url.split(',').map((url, index, arr) => {
                            const trimmedUrl = url.trim();
                            if (!trimmedUrl) return null;
                            return (
                              <div key={trimmedUrl} className="flex items-center gap-1">
                                <a 
                                  className="text-link font-body-md text-[14px] flex items-center gap-0.5 hover:underline font-medium" 
                                  href={trimmedUrl} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                >
                                  {trimmedUrl.includes("groww.in") 
                                    ? `${funds.find(f => f.source_url === trimmedUrl)?.scheme_name || 'ICICI Prudential Mutual Fund'} - Groww`
                                    : trimmedUrl.includes("sebi.gov.in")
                                    ? "SEBI Investor Education Portal"
                                    : trimmedUrl.includes("amfiindia.com")
                                    ? "AMFI India Portal"
                                    : "Source Page"
                                  }
                                  <span className="material-symbols-outlined text-[15px] ml-0.5">open_in_new</span>
                                </a>
                                {index < arr.length - 1 && <span className="text-slate-300 font-normal select-none">|</span>}
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {/* Footer Details */}
                      {msg.last_updated && msg.last_updated !== 'N/A' && (
                        <div className="mt-1">
                          <p className="text-text-muted font-label-sm text-[12px]">
                            Last updated from sources: {msg.last_updated}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {/* Typing indicator for API load state */}
              {isLoading && (
                <div className="flex justify-start animate-message-enter">
                  <div className="max-w-[85%] bg-white border border-slate-200 p-4 rounded-2xl rounded-bl-[2px] shadow-[0_2px_4px_rgba(0,0,0,0.02)] flex items-center gap-2">
                    <span className="w-2.5 h-2.5 bg-[#00b589] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2.5 h-2.5 bg-[#00b589] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2.5 h-2.5 bg-[#00b589] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                </div>
              )}

              {/* Scroll anchor */}
              <div ref={chatEndRef} />

              {/* Empty state: Pre-defined prompt chips */}
              {messages.length === 1 && !isLoading && (
                <div className="mt-8 flex flex-col gap-4 max-w-lg mx-auto w-full">
                  <p className="text-[#64748B] text-center font-medium Outfit text-[15px]">Frequently Asked Questions</p>
                  <div className="grid grid-cols-1 gap-3">
                    <button 
                      onClick={() => handleExampleClick("What is the exit load on ICICI Prudential Commodities Fund?")}
                      className="p-4 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-all hover:-translate-y-0.5 active:translate-y-0 text-left shadow-sm font-semibold text-[#1E293B] flex items-center justify-between"
                    >
                      <span>What is the exit load on ICICI Prudential Commodities Fund?</span>
                      <span className="material-symbols-outlined text-slate-400">chevron_right</span>
                    </button>
                    <button 
                      onClick={() => handleExampleClick("What is the expense ratio of ICICI Prudential Large Cap Fund?")}
                      className="p-4 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-all hover:-translate-y-0.5 active:translate-y-0 text-left shadow-sm font-semibold text-[#1E293B] flex items-center justify-between"
                    >
                      <span>What is the expense ratio of ICICI Prudential Large Cap Fund?</span>
                      <span className="material-symbols-outlined text-slate-400">chevron_right</span>
                    </button>
                    <button 
                      onClick={() => handleExampleClick("Who manages ICICI Prudential Technology Direct Plan-Growth?")}
                      className="p-4 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-all hover:-translate-y-0.5 active:translate-y-0 text-left shadow-sm font-semibold text-[#1E293B] flex items-center justify-between"
                    >
                      <span>Who manages ICICI Prudential Technology Direct Plan-Growth?</span>
                      <span className="material-symbols-outlined text-slate-400">chevron_right</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Sticky Bottom Input Area */}
          <footer className="p-4 md:p-6 bg-white border-t border-slate-200 sticky bottom-0 z-45">
            <div className="relative flex items-center max-w-3xl mx-auto w-full">
              <input 
                type="text" 
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage(inputText)}
                disabled={isLoading}
                placeholder={selectedSlugs.length === 1 
                  ? `Ask about ${funds.find(f => f.slug === selectedSlugs[0])?.scheme_name.substring(0,25)}...`
                  : "Ask a factual question about a fund..."
                }
                className="peer w-full h-12 bg-[#F1F5F9] rounded-full pl-5 pr-14 border-transparent focus:border-slate-300 focus:ring-0 text-[#0F172A] font-body-md text-[15px] placeholder-[#64748B] transition-colors outline-none"
              />
              <button 
                onClick={() => handleSendMessage(inputText)}
                disabled={isLoading || !inputText.trim()}
                className={`absolute right-1.5 w-9 h-9 rounded-full flex items-center justify-center shadow-sm transition-all ${
                  inputText.trim() && !isLoading 
                    ? 'bg-[#00b589] text-white hover:opacity-90 active:scale-95 peer-focus:animate-pulse-fast' 
                    : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                }`}
              >
                <span className="material-symbols-outlined font-semibold text-[20px]">arrow_upward</span>
              </button>
            </div>
            
            {/* Show active selection tag */}
            {selectedSlugs.length > 0 && (
              <div className="mt-2 flex flex-wrap justify-center gap-1.5 max-w-3xl mx-auto w-full">
                {selectedSlugs.map(slug => {
                  const fund = funds.find(f => f.slug === slug);
                  return fund ? (
                    <div key={slug} className="flex items-center gap-1 bg-[#E8F0EA] text-[#006c50] py-0.5 px-2.5 rounded-full text-[11px] font-semibold">
                      <span>{fund.scheme_name.replace("ICICI Prudential", "IPru")}</span>
                      <button onClick={() => toggleFundSelection(slug)} className="hover:text-red-500 font-bold ml-1 flex items-center">
                        <span className="material-symbols-outlined text-[12px]">close</span>
                      </button>
                    </div>
                  ) : null;
                })}
              </div>
            )}
          </footer>
        </div>
      </main>

      {/* BottomNavBar - Mobile Only */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full z-48 flex justify-center items-end pb-4 px-4 bg-transparent pointer-events-none">
        <div className="flex items-center gap-2 bg-white/90 backdrop-blur-md border border-slate-200 p-1.5 rounded-full shadow-lg pointer-events-auto">
          {/* Chat (Active) */}
          <button 
            onClick={() => handleMobileNav('chat')}
            className={`flex flex-col items-center justify-center rounded-full px-5 py-2 scale-95 transition-all ${
              activeTab === 'chat' ? 'bg-[#00b589] text-white shadow-sm' : 'text-slate-500 hover:text-[#00b589]'
            }`}
          >
            <span className="material-symbols-outlined text-[20px] font-medium">chat</span>
            <span className="font-label-md text-[10px] mt-0.5">Chat</span>
          </button>
          
          {/* Funds (Opens Selection Modal) */}
          <button 
            onClick={() => handleMobileNav('funds')}
            className="flex flex-col items-center justify-center text-slate-500 px-4 py-2 hover:text-[#00b589] transition-colors"
          >
            <span className="material-symbols-outlined text-[20px]">account_balance_wallet</span>
            <span className="font-label-md text-[10px] mt-0.5">Funds</span>
          </button>
        </div>
      </nav>

      {/* Select Funds Modal (Centered Card Dialog on Desktop, Full-screen on Mobile) */}
      {isModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/30 backdrop-blur-sm p-0 md:p-4">
          <div className="w-full h-full md:h-auto md:max-h-[80vh] md:max-w-md bg-white shadow-2xl md:rounded-2xl flex flex-col overflow-hidden animate-message-enter">
            
            {/* Modal Header */}
            <div className="p-4 md:p-6 border-b border-slate-200">
              <div className="flex justify-between items-center mb-4">
                <h2 className="font-headline-md text-[20px] font-semibold text-[#0F172A]">Select Schemes</h2>
                <button 
                  onClick={() => setIsModalOpen(false)}
                  className="p-2 text-slate-400 hover:text-[#006c50] hover:bg-slate-100 rounded-full transition-all"
                >
                  <span className="material-symbols-outlined text-[22px]">close</span>
                </button>
              </div>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">search</span>
                <input 
                  type="text" 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 h-11 bg-[#F1F5F9] border-transparent rounded-xl focus:ring-2 focus:ring-[#00b589]/50 text-[14px] outline-none text-[#0F172A]" 
                  placeholder={`Search ${funds.length} funds...`}
                />
              </div>
            </div>

            {/* Scrollable Fund List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2 max-h-[50vh] md:max-h-[40vh]">
              {filteredFunds.length > 0 ? (
                filteredFunds.map((fund) => {
                  const isChecked = selectedSlugs.includes(fund.slug);
                  return (
                    <label 
                      key={fund.slug}
                      className={`flex items-center justify-between p-3.5 rounded-xl cursor-pointer transition-all border ${
                        isChecked 
                          ? 'bg-[#E8F0EA]/40 border-[#00b589]/30' 
                          : 'bg-slate-50/50 hover:bg-slate-100/50 border-slate-100'
                      }`}
                    >
                      <div className="flex flex-col gap-0.5 pr-2">
                        <span className="font-semibold text-[#0F172A] leading-tight text-[14px]">{fund.scheme_name}</span>
                        <span className="text-[11px] text-[#64748B] font-medium">{fund.category}</span>
                      </div>
                      <input 
                        type="checkbox" 
                        checked={isChecked}
                        onChange={() => toggleFundSelection(fund.slug)}
                        className="w-5.5 h-5.5 rounded border-slate-300 text-[#00b589] focus:ring-[#00b589]"
                      />
                    </label>
                  );
                })
              ) : (
                <div className="py-8 text-center text-slate-400 italic">No funds found matching your search.</div>
              )}
            </div>

            {/* Fixed Modal Footer Action */}
            <div className="p-4 md:p-6 border-t border-slate-200 flex gap-3 bg-white sticky bottom-0">
              <button 
                onClick={handleClearAll}
                className="flex-1 py-3 border border-slate-300 text-slate-600 font-semibold rounded-full hover:bg-slate-50 transition-colors active:scale-[0.98]"
              >
                Clear All
              </button>
              <button 
                onClick={handleApplySelection}
                className="flex-1 py-3 bg-[#00b589] text-white font-semibold rounded-full hover:opacity-95 transition-opacity shadow-sm active:scale-[0.98]"
              >
                {selectedSlugs.length > 0 ? `Apply Selection (${selectedSlugs.length})` : 'Apply Selection'}
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
