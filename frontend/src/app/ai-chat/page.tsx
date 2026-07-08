"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { api } from "@/lib/api";
import { Send, Bot, User, Trash2, ClipboardList, MessageSquare, CheckCircle, Loader2 } from "lucide-react";
import { useChatStore, ChatMessage } from "@/stores/chat";

const FIELD_LABELS: Record<string, string> = {
  community: "小区名称", area: "面积", room_type: "户型", rent_price: "售价/租金",
  building_type: "建筑类型", total_floors: "总楼层", floor_info: "所在楼层",
  decoration: "装修", decoration_year: "装修年份",
  listed_on_beike: "贝壳挂牌", list_price: "挂牌价格",
  has_parking: "车位", occupancy_status: "居住状态",
  tenant_cooperation: "租客配合", key_location: "钥匙/看房",
  list_duration: "挂牌时长", unsold_reason: "未成交原因",
  purchase_year: "购置年份", is_only_home: "唯一住房",
  seller_motivation: "卖房动机",
};

export default function AIChatPage() {
  const messages = useChatStore((s) => s.messages);
  const addMessage = useChatStore((s) => s.addMessage);
  const clearMessages = useChatStore((s) => s.clearMessages);
  const mode = useChatStore((s) => s.mode);
  const setMode = useChatStore((s) => s.setMode);
  const collected = useChatStore((s) => s.collected);
  const setCollected = useChatStore((s) => s.setCollected);
  const collectScore = useChatStore((s) => s.collectScore);
  const setCollectScore = useChatStore((s) => s.setCollectScore);
  const savedHouseId = useChatStore((s) => s.savedHouseId);
  const setSavedHouseId = useChatStore((s) => s.setSavedHouseId);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || loading) return;
    const userInput = input;
    addMessage({ role: "user", content: userInput });
    setInput("");
    setLoading(true);

    try {
      if (mode === "collect") {
        // Build history from store messages
        const history = messages.map((m) => ({ role: m.role, content: m.content }));

        const result = await api.post<{
          reply: string; extracted: Record<string, string>;
          next_question: string; score: number;
          house_id: string | null; core_complete: boolean;
        }>("/ai/collect", {
          query: userInput,
          history: history.slice(-10),
          collected: collected,
          mode: "collect",
        });

        addMessage({ role: "assistant", content: result.reply });

        // Merge extracted fields
        if (result.extracted && Object.keys(result.extracted).length > 0) {
          setCollected((prev) => {
            const merged = { ...prev, ...result.extracted };
            return merged;
          });
        }
        setCollectScore(result.score);

        if (result.house_id) {
          setSavedHouseId(result.house_id);
        }
      } else {
        const result = await api.post<{ answer: string }>("/ai/chat", { query: userInput });
        addMessage({ role: "assistant", content: result.answer });
      }
    } catch {
      addMessage({ role: "assistant", content: "抱歉，AI 服务暂时不可用，请稍后再试。" });
    } finally {
      setLoading(false);
    }
  }, [input, loading, mode, messages, collected, addMessage]);

  const collectedKeys = Object.entries(collected).filter(([, v]) => v);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Navbar />
        <main className="flex-1 flex flex-col max-w-5xl mx-auto w-full p-6">
          {/* Header */}
          <div className="mb-4 flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">AI 业务助手</h2>
              <p className="text-gray-500 mt-1">
                {mode === "collect" ? "房源信息采集模式" : "基于知识库和房源数据的智能问答"}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {/* Mode toggle */}
              <div className="flex bg-gray-100 rounded-lg p-0.5 mr-2">
                <button
                  onClick={() => setMode("chat")}
                  className={`flex items-center gap-1 px-3 py-1.5 text-xs rounded-md transition-colors ${
                    mode === "chat" ? "bg-white shadow text-gray-800" : "text-gray-500"
                  }`}
                >
                  <MessageSquare className="w-3.5 h-3.5" /> 问答
                </button>
                <button
                  onClick={() => setMode("collect")}
                  className={`flex items-center gap-1 px-3 py-1.5 text-xs rounded-md transition-colors ${
                    mode === "collect" ? "bg-white shadow text-primary-700" : "text-gray-500"
                  }`}
                >
                  <ClipboardList className="w-3.5 h-3.5" /> 采集
                </button>
              </div>
              <button
                onClick={clearMessages}
                className="flex items-center gap-1 px-3 py-1.5 text-xs text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" /> 清空
              </button>
            </div>
          </div>

          <div className="flex gap-4 flex-1 min-h-0">
            {/* Chat panel */}
            <div className="flex-1 flex flex-col min-w-0">
              <div className="flex-1 bg-white rounded-xl border p-6 overflow-y-auto max-h-[58vh] space-y-4">
                {messages.map((msg, i) => (
                  <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
                    {msg.role === "assistant" && (
                      <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <Bot className="w-4 h-4 text-primary-600" />
                      </div>
                    )}
                    <div
                      className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
                        msg.role === "user" ? "bg-primary-600 text-white" : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                    {msg.role === "user" && (
                      <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                        <User className="w-4 h-4 text-gray-600" />
                      </div>
                    )}
                  </div>
                ))}
                {loading && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                      <Loader2 className="w-4 h-4 text-primary-600 animate-spin" />
                    </div>
                    <div className="bg-gray-100 rounded-xl px-4 py-2.5 text-sm text-gray-500">
                      AI 正在分析...
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>

              {/* Input */}
              <div className="mt-3 flex gap-2">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                  placeholder={mode === "collect" ? "描述你了解到的房源信息..." : "输入你的问题..."}
                  rows={2}
                  className="flex-1 px-4 py-2.5 border rounded-xl focus:ring-2 focus:ring-primary-500 outline-none resize-none"
                />
                <button
                  onClick={handleSend}
                  disabled={loading || !input.trim()}
                  className="px-4 py-2.5 bg-primary-600 text-white rounded-xl hover:bg-primary-700 disabled:opacity-50 transition-colors flex items-center"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Collect sidebar — only in collect mode */}
            {mode === "collect" && (
              <div className="w-64 flex-shrink-0 space-y-4">
                {/* Progress */}
                <div className="bg-white rounded-xl border p-4">
                  <h3 className="text-sm font-semibold mb-2">采集进度</h3>
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div
                      className="bg-primary-500 h-2 rounded-full transition-all"
                      style={{ width: `${collectScore}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500">{collectScore}% 完成</p>
                </div>

                {/* Collected fields */}
                <div className="bg-white rounded-xl border p-4">
                  <h3 className="text-sm font-semibold mb-2">
                    已采集 ({collectedKeys.length})
                  </h3>
                  {collectedKeys.length === 0 ? (
                    <p className="text-xs text-gray-400">等待AI引导采集...</p>
                  ) : (
                    <div className="space-y-1.5 max-h-64 overflow-y-auto">
                      {collectedKeys.map(([key, val]) => (
                        <div key={key} className="text-xs">
                          <span className="text-gray-400">{FIELD_LABELS[key] || key}:</span>
                          <span className="text-gray-700 ml-1 font-medium">
                            {typeof val === "boolean" ? (val ? "是" : "否") : String(val).slice(0, 30)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Saved indicator */}
                {savedHouseId && (
                  <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                    <div className="flex items-center gap-2 text-green-700 text-sm">
                      <CheckCircle className="w-4 h-4" />
                      已自动保存
                    </div>
                    <p className="text-xs text-green-600 mt-1">
                      房源已录入系统，可在房源管理中查看
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
