import { useState, useRef, useEffect } from "react";
import { Search, Loader2, MessageSquare, ChevronDown, ChevronRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useDash } from "@/store/dashboardStore";
import { useI18n } from "@/lib/i18n";
import { queryApi } from "@/api/endpoints";
import { classHex } from "@/lib/colors";
import { toast } from "@/hooks/use-toast";
import type { QueryMatchedCell } from "@/api/types";

export function AiQueryPanel() {
  const { t } = useI18n();
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const gridId = useDash((s) => s.gridId);
  const queryResults = useDash((s) => s.queryResults);
  const queryHistory = useDash((s) => s.queryHistory);
  const isQuerying = useDash((s) => s.isQuerying);
  const queryError = useDash((s) => s.queryError);
  const setQueryResults = useDash((s) => s.setQueryResults);
  const addQueryHistory = useDash((s) => s.addQueryHistory);
  const setIsQuerying = useDash((s) => s.setIsQuerying);
  const setQueryError = useDash((s) => s.setQueryError);
  const setMatchedCellIds = useDash((s) => s.setMatchedCellIds);
  const aiQueryOpen = useDash((s) => s.aiQueryOpen);
  const setAiQueryOpen = useDash((s) => s.setAiQueryOpen);

  const handleQuery = async (question: string) => {
    const q = question.trim();
    if (!q || isQuerying) return;
    if (!gridId) {
      toast({
        title: "No Grid Loaded",
        description: "Please load an area first before querying.",
        variant: "destructive",
      });
      return;
    }
    setIsQuerying(true);
    setQueryError(null);
    try {
      const result = await queryApi({ question: q, grid_id: gridId });
      setQueryResults(result);
      setMatchedCellIds(result.matched_cells.map((c) => c.cell_id));
      addQueryHistory(q);
      setInput("");
    } catch {
      setQueryError("failed");
      toast({
        title: "Query Failed",
        description: "An error occurred while processing your query. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsQuerying(false);
    }
  };

  const handleSubmit = () => handleQuery(input);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSubmit();
  };

  const handleHistoryClick = (q: string) => {
    setInput(q);
    handleQuery(q);
  };

  const avgConfidence = queryResults?.matched_cells.length
    ? queryResults.matched_cells.reduce((s, c) => s + c.confidence, 0) / queryResults.matched_cells.length
    : 0;

  const topCategories = queryResults?.matched_cells.length
    ? [...new Set(queryResults.matched_cells.flatMap((c) => c.poi_categories))].slice(0, 5)
    : [];

  useEffect(() => {
    if (aiQueryOpen) inputRef.current?.focus();
  }, [aiQueryOpen]);

  return (
    <div className="border-t border-border">
      <button
        onClick={() => setAiQueryOpen(!aiQueryOpen)}
        className="flex items-center gap-2 w-full px-4 py-2.5 text-[11px] uppercase tracking-wider text-muted-foreground font-semibold hover:bg-muted/50 transition-colors"
      >
        {aiQueryOpen ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        <Sparkles className="h-3.5 w-3.5" />
        {t("ai_query")}
      </button>

      {aiQueryOpen && (
        <div className="px-4 pb-4 space-y-3">
          <div className="flex gap-1.5">
            <div className="relative flex-1">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={t("ai_query_placeholder")}
                disabled={isQuerying}
                className="pl-8 pr-2 h-9 text-xs"
              />
            </div>
            <Button
              size="sm"
              className="h-9 text-xs gap-1"
              onClick={handleSubmit}
              disabled={isQuerying || !input.trim()}
            >
              {isQuerying ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Search className="h-3.5 w-3.5" />
              )}
              {isQuerying ? t("ai_query_searching") : t("ai_query_search")}
            </Button>
          </div>

          {isQuerying && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              {t("ai_query_searching")}
            </div>
          )}

          {queryError && !isQuerying && (
            <p className="text-xs text-destructive">{t("ai_query_error")}</p>
          )}

          {queryResults && !isQuerying && queryResults.matched_cells.length === 0 && (
            <div className="text-xs text-muted-foreground text-center py-6">
              <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-40" />
              {t("ai_query_no_results")}
            </div>
          )}

          {queryResults && queryResults.matched_cells.length > 0 && !isQuerying && (
            <div className="space-y-2">
              <p className="text-xs text-foreground/80 leading-relaxed">{queryResults.answer}</p>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-secondary/40 rounded p-2">
                  <span className="text-muted-foreground">{t("ai_query_found").replace("{n}", String(queryResults.matched_cells.length))}</span>
                  <span className="block font-semibold mt-0.5">{queryResults.matched_cells.length}</span>
                </div>
                <div className="bg-secondary/40 rounded p-2">
                  <span className="text-muted-foreground">{t("ai_query_avg_confidence")}</span>
                  <span className="block font-semibold mt-0.5">{(avgConfidence * 100).toFixed(0)}%</span>
                </div>
              </div>

              {topCategories.length > 0 && (
                <div className="text-xs">
                  <span className="text-muted-foreground">{t("ai_query_top_categories")}:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {topCategories.map((cat) => (
                      <span key={cat} className="px-1.5 py-0.5 bg-secondary rounded text-[10px]">{cat}</span>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <h4 className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold mb-1.5">
                  {t("ai_query_matched_cells")}
                </h4>
                <div className="max-h-[240px] overflow-y-auto space-y-1 pr-1">
                  {queryResults.matched_cells.map((cell) => (
                    <MatchedCellRow key={cell.cell_id} cell={cell} />
                  ))}
                </div>
              </div>
            </div>
          )}

          {queryHistory.length > 0 && !queryResults && (
            <div className="text-xs">
              <h4 className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold mb-1.5">
                {t("ai_query_history")}
              </h4>
              <div className="space-y-0.5">
                {queryHistory.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleHistoryClick(q)}
                    className="w-full text-left px-2 py-1.5 rounded hover:bg-muted transition-colors text-muted-foreground hover:text-foreground truncate"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function MatchedCellRow({ cell }: { cell: QueryMatchedCell }) {
  const setSelectedCellId = useDash((s) => s.setSelectedCellId);
  const hex = classHex[cell.dominant_class as keyof typeof classHex] || "#888";

  return (
    <button
      onClick={() => setSelectedCellId(cell.cell_id)}
      className="w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs hover:bg-muted transition-colors text-left group"
    >
      <span className="h-2.5 w-2.5 rounded-sm shrink-0" style={{ backgroundColor: hex }} />
      <span className="font-medium shrink-0">{cell.cell_id}</span>
      <span className="text-muted-foreground truncate">{cell.dominant_class}</span>
      <span className="ml-auto text-muted-foreground font-mono">
        {(cell.confidence * 100).toFixed(0)}%
      </span>
    </button>
  );
}
