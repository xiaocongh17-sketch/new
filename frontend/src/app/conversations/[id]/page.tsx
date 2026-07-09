"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Conversation } from "@/types";
import { ArrowLeft, Send, XCircle, Loader2 } from "lucide-react";

interface Message {
  id: string;
  sender_id: string;
  content: string;
  msg_type: string;
  created_at: string;
}

interface ConversationDetail extends Conversation {
  messages: Message[];
}

export default function ConversationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [replyText, setReplyText] = useState("");
  const [sending, setSending] = useState(false);
  const [closing, setClosing] = useState(false);

  const conversationId = params.id as string;

  function fetchConversation() {
    setLoading(true);
    api
      .get<ConversationDetail>(`/conversations/${conversationId}`)
      .then(setConversation)
      .catch((err) => {
        alert("加载对话失败：" + err.message);
        router.push("/conversations");
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (conversationId) fetchConversation();
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation?.messages]);

  async function handleReply() {
    if (!replyText.trim()) return;
    setSending(true);
    try {
      await api.post(`/conversations/${conversationId}/reply`, {
        content: replyText.trim(),
      });
      setReplyText("");
      fetchConversation();
    } catch (err) {
      alert("发送失败：" + (err instanceof Error ? err.message : "未知错误"));
    } finally {
      setSending(false);
    }
  }

  async function handleClose() {
    if (!confirm("确定关闭此对话吗？")) return;
    setClosing(true);
    try {
      await api.patch(`/conversations/${conversationId}/close`);
      fetchConversation();
    } catch (err) {
      alert("关闭失败：" + (err instanceof Error ? err.message : "未知错误"));
    } finally {
      setClosing(false);
    }
  }

  const statusLabels: Record<string, string> = {
    active: "进行中",
    pending_review: "待审核",
    closed: "已关闭",
  };

  const statusColors: Record<string, string> = {
    active: "bg-green-100 text-green-700",
    pending_review: "bg-yellow-100 text-yellow-700",
    closed: "bg-gray-100 text-gray-600",
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <Sidebar />
        <div className="flex-1">
          <Navbar />
          <main className="p-6">
            <div className="animate-pulse space-y-4">
              <div className="h-8 w-48 bg-gray-200 rounded" />
              <div className="h-64 bg-gray-200 rounded" />
            </div>
          </main>
        </div>
      </div>
    );
  }

  if (!conversation) return null;

  const isPendingReview = conversation.status === "pending_review";
  const isClosed = conversation.status === "closed";

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Navbar />
        <main className="flex-1 flex flex-col p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push("/conversations")}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h2 className="text-2xl font-bold">对话详情</h2>
                <p className="text-sm text-gray-500 mt-1">
                  用户/群：{conversation.wecom_group_id}
                </p>
              </div>
              <span
                className={`inline-flex px-2 py-1 text-xs rounded-full font-medium ${statusColors[conversation.status] || "bg-gray-100 text-gray-600"}`}
              >
                {statusLabels[conversation.status] || conversation.status}
              </span>
            </div>

            {!isClosed && (
              <button
                onClick={handleClose}
                disabled={closing}
                className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 disabled:opacity-50 transition-colors"
              >
                <XCircle className="w-4 h-4" />
                {closing ? "关闭中..." : "关闭对话"}
              </button>
            )}
          </div>

          {/* Messages */}
          <div className="flex-1 bg-white rounded-xl border overflow-hidden flex flex-col">
            <div className="flex-1 overflow-y-auto p-6 space-y-4 max-h-[500px]">
              {conversation.messages.length === 0 ? (
                <p className="text-center text-gray-400 py-12">暂无消息</p>
              ) : (
                conversation.messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.msg_type === "system" ? "justify-center" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[70%] rounded-xl px-4 py-3 ${
                        msg.msg_type === "system"
                          ? "bg-gray-100 text-gray-500 text-sm"
                          : "bg-blue-50 text-gray-800"
                      }`}
                    >
                      {msg.msg_type !== "system" && (
                        <p className="text-xs text-gray-400 mb-1">
                          {msg.sender_id.slice(0, 8)}...
                        </p>
                      )}
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      <p className="text-xs text-gray-400 mt-1 text-right">
                        {msg.created_at ? formatDate(msg.created_at) : ""}
                      </p>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Reply input (only when not closed) */}
            {!isClosed && (
              <div className="border-t p-4">
                {isPendingReview && (
                  <div className="flex items-center gap-2 mb-3 px-3 py-2 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-700">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    此对话待审核，回复后将自动标记为"进行中"
                  </div>
                )}
                <div className="flex gap-3">
                  <textarea
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    placeholder="输入回复内容..."
                    rows={3}
                    className="flex-1 border rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-primary-500 outline-none resize-none"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleReply();
                      }
                    }}
                  />
                  <button
                    onClick={handleReply}
                    disabled={sending || !replyText.trim()}
                    className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors self-end"
                  >
                    <Send className="w-4 h-4" />
                    {sending ? "发送中..." : "发送"}
                  </button>
                </div>
              </div>
            )}

            {isClosed && (
              <div className="border-t p-4 text-center text-sm text-gray-400">
                此对话已关闭
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
