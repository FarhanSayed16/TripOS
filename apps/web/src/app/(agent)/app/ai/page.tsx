"use client";

import { useState } from "react";
import { useSearchAndDraftMutation } from "@/lib/api/aiApi";
import { useCreateQuoteMutation } from "@/lib/api/quotesApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, ArrowRight, Loader2, Info, CheckCircle2, AlertTriangle, Send } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

export default function AICopilotPage() {
  const [query, setQuery] = useState("");
  const [searchAndDraft, { isLoading }] = useSearchAndDraftMutation();
  const [createQuote, { isLoading: isCreating }] = useCreateQuoteMutation();
  const [result, setResult] = useState<any>(null);
  const router = useRouter();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    try {
      const res = await searchAndDraft(query).unwrap();
      setResult(res);
    } catch (err: any) {
      alert("AI Copilot request failed: " + (err?.data?.detail || err.message));
    }
  };

  const handleCreateQuote = async () => {
    if (!result) return;
    
    // Select the offers from the actual search results that AI recommended
    const selectedOffers = result.search_results.filter((o: any) => 
      result.draft.selected_offer_ids.includes(o.id)
    );
    
    if (selectedOffers.length === 0) {
      alert("No valid offers selected by AI.");
      return;
    }

    const payload: any = {
      customer_id: null,
      items: selectedOffers.map((offer: any) => ({
        type: result.intent.type,
        offer_id: offer.id,
        supplier_id: offer.supplier_id,
        agent_markup_paise: result.draft.suggested_markup_paise || 50000, 
      })),
    };

    try {
      const created = await createQuote(payload).unwrap();
      router.push(`/app/quotes/${created.id}`);
    } catch (err: any) {
      alert("Failed to create quote.");
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-10">
      <div>
        <h1 className="page-title text-2xl tracking-tight flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-teal/20 to-teal-dark/20 flex items-center justify-center border border-teal/30">
            <Sparkles className="w-5 h-5 text-teal" />
          </div>
          AI Assistant
        </h1>
        <p className="page-subtitle mt-2">
          Type what your customer wants in natural language. The Assistant will search live inventory and draft a quote based on live fares.
        </p>
      </div>

      <div className="bg-paper border border-line shadow-sm rounded-2xl overflow-hidden flex flex-col">
        {/* Chat History Area */}
        <div className="flex-1 p-6 space-y-6 min-h-[300px] max-h-[500px] overflow-y-auto bg-surface/30">
          
          {/* Welcome Message */}
          <div className="flex gap-4">
            <div className="w-8 h-8 rounded-full bg-teal/10 flex items-center justify-center shrink-0 border border-teal/20">
              <Sparkles className="w-4 h-4 text-teal" />
            </div>
            <div className="space-y-2 max-w-[80%]">
              <div className="bg-paper border border-line p-4 rounded-2xl rounded-tl-sm shadow-sm text-sm text-ink leading-relaxed">
                Hello! I can help you build quotes faster. Just paste a customer's message or describe what they need.
                <div className="mt-3 space-y-1.5 text-xs text-muted-foreground border-t border-line/50 pt-3">
                  <div className="flex items-start gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> I search real-time supplier inventory.</div>
                  <div className="flex items-start gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> I am locale and currency aware.</div>
                  <div className="flex items-start gap-1.5"><AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" /> I will never hallucinate fares or invent flights.</div>
                </div>
              </div>
              
              {!result && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {["Delhi to Goa for 2 adults", "Cheapest Mumbai flight tomorrow", "Weekend Udaipur package"].map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setQuery(s)}
                      className="px-3 py-1.5 text-xs font-medium rounded-full bg-surface border border-line text-muted-foreground hover:bg-teal/5 hover:text-teal hover:border-teal/30 transition-colors"
                    >
                      "{s}"
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* User Message (if submitted) */}
          {result && (
            <div className="flex gap-4 flex-row-reverse animate-in fade-in slide-in-from-bottom-4">
              <div className="w-8 h-8 rounded-full bg-ink flex items-center justify-center shrink-0">
                <span className="text-white text-xs font-medium">ME</span>
              </div>
              <div className="bg-ink text-white p-3 px-4 rounded-2xl rounded-tr-sm shadow-sm text-sm max-w-[80%]">
                {query}
              </div>
            </div>
          )}

          {/* AI Response (if resulted) */}
          {result && (
            <div className="flex gap-4 animate-in fade-in slide-in-from-bottom-4">
              <div className="w-8 h-8 rounded-full bg-teal/10 flex items-center justify-center shrink-0 border border-teal/20 mt-1">
                <Sparkles className="w-4 h-4 text-teal" />
              </div>
              <div className="space-y-4 max-w-[90%]">
                <div className="bg-paper border border-line p-4 rounded-2xl rounded-tl-sm shadow-sm text-sm text-ink">
                  <p className="mb-4">I've parsed your request and found <span className="font-semibold">{result.draft.selected_offer_ids.length}</span> matching options from live inventory. Here is a suggested quote draft:</p>
                  
                  <div className="bg-surface border border-line/60 rounded-xl p-4 space-y-4">
                    <div className="text-sm font-medium text-ink italic border-l-2 border-teal pl-3">
                      "{result.draft.summary}"
                    </div>
                    
                    <div className="flex justify-between items-center text-xs bg-sand/30 p-2.5 rounded-md border border-line/50">
                      <span className="text-muted-foreground flex items-center gap-1.5"><Info className="w-3.5 h-3.5" /> Suggested Markup</span>
                      <span className="font-semibold text-emerald-600 font-mono">₹{result.draft.suggested_markup_paise / 100} / item</span>
                    </div>

                    <div className="space-y-2 pt-2 border-t border-line/60">
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Selected Itinerary</p>
                      {result.search_results
                        .filter((o: any) => result.draft.selected_offer_ids.includes(o.id))
                        .map((offer: any) => (
                          <div key={offer.id} className="flex justify-between items-center p-3 rounded-lg border border-line bg-paper hover:bg-surface transition-colors cursor-default">
                            <div>
                              <p className="font-semibold text-ink text-sm">{offer.title}</p>
                              <p className="text-xs text-muted-foreground mt-0.5">{offer.description}</p>
                            </div>
                            <div className="text-right">
                              <p className="font-bold font-mono text-sm tracking-tight text-ink">₹{(offer.price.total_amount / 100).toLocaleString()}</p>
                              <Badge variant="outline" className="mt-1 text-[9px] uppercase px-1.5 py-0 border-line text-muted-foreground">Live Fare</Badge>
                            </div>
                          </div>
                      ))}
                    </div>
                  </div>

                  <div className="mt-4 flex gap-3">
                    <Button
                      onClick={handleCreateQuote}
                      disabled={isCreating}
                      className="bg-teal hover:bg-teal-dark shadow-sm text-sm h-9"
                    >
                      {isCreating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : "Review in Quote Editor"}
                      {!isCreating && <ArrowRight className="w-3.5 h-3.5 ml-2" />}
                    </Button>
                    <Button variant="outline" className="text-sm h-9" onClick={() => {setResult(null); setQuery("");}}>
                      Start Over
                    </Button>
                  </div>
                </div>

                <div className="flex gap-2 items-center">
                  <Badge variant="outline" className="bg-blue-50/50 text-blue-700 border-blue-200 text-[10px] font-mono font-normal flex gap-1 items-center">
                    <Info className="w-3 h-3" />
                    Intent: {result.intent.type} • {result.intent.origin || 'Any'} → {result.intent.destination || 'Any'}
                  </Badge>
                </div>
              </div>
            </div>
          )}

          {isLoading && !result && (
            <div className="flex gap-4 animate-in fade-in slide-in-from-bottom-4">
              <div className="w-8 h-8 rounded-full bg-teal/10 flex items-center justify-center shrink-0 border border-teal/20 mt-1">
                <Sparkles className="w-4 h-4 text-teal" />
              </div>
              <div className="bg-paper border border-line p-4 rounded-2xl rounded-tl-sm shadow-sm flex gap-2 items-center">
                <Loader2 className="w-4 h-4 animate-spin text-teal" />
                <span className="text-sm text-muted-foreground">Searching live inventory & drafting...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 bg-paper border-t border-line">
          <form onSubmit={handleSearch} className="relative flex items-center">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder='Paste a customer message or type a request...'
              className="w-full pl-4 pr-14 py-4 rounded-xl border border-line bg-surface text-sm text-ink focus:outline-none focus:ring-2 focus:ring-teal/20 focus:border-teal transition-all placeholder:text-muted-foreground"
              disabled={isLoading}
            />
            <Button
              type="submit"
              size="icon"
              disabled={isLoading || !query.trim()}
              className="absolute right-2 w-10 h-10 rounded-lg bg-teal hover:bg-teal-dark disabled:bg-surface disabled:text-muted-foreground disabled:border disabled:border-line"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </form>
          <div className="text-center mt-2">
            <span className="text-[10px] text-muted-foreground">AI can make mistakes. Please verify pricing and availability in the Quote Editor.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
