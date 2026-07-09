"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { Table } from "@/components/Table";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Conversation } from "@/types";
import { useRouter } from "next/navigation";
import { MessageCircle, AlertCircle } from "lucide-react";

type TabType = "all" | "pending";

export default function ConversationsPage() {
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<TabType>("pending");

  const pageSize = 20;

  function fetchConversations() {
    setLoading(true);
    const endpoint =
      tab === "pending"
        ? `/conversations/pending?page=${page}&page_size=${pageSize}`
        : `/conversations?page=${page}&page_size=${pageSize}`;

    api
      .get<{ items: Conversation[]; total: number }>(endpoint)
      .then((data) => {
        setConversations(data.items);
        setTotal(data.total);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchConversations();
  }, [page, tab]);

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

  const columns = [
    { key: "wecom_group_id", header: "用户/群ID" },
    {
      key: "status",
      header: "状态",
      render: (c: Conversation) => (
        <span
          className={`inline-flex px-2 py-1 text-xs rounded-full font-medium ${statusColors[c.status] || "bg-gray-100 text-gray-600"}`}
        >
          {statusLabels[c.status] || c.status}
        </span>
      ),
    },
    {
      key: "participants",
      header: "参与人数",
      render: (c: Conversation) => `${c.participants?.length || 0}`,
    },
    {
      key: "updated_at",
      header: "更新时间",
      render: (c: Conversation) => formatDate(c.updated_at),
    },
    {
      key: "created_at",
      header: "创建时间",
      render: (c: Conversation) => formatDate(c.created_at),
    },
  ];

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1">
        <Navbar />
        <main className="p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-bold">对话管理</h2>
              <p className="text-gray-500 mt-1">
                {tab === "pending"
                  ? `${total} 条对话待审核`
                  : `共 ${total} 条对话`}
              </p>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => { setTab("pending"); setPage(1); }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                tab === "pending"
                  ? "bg-yellow-100 text-yellow-700"
                  : "bg-white text-gray-600 hover:bg-gray-50 border"
              }`}
            >
              <AlertCircle className="w-4 h-4" />
              待审核
            </button>
            <button
              onClick={() => { setTab("all"); setPage(1); }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                tab === "all"
                  ? "bg-primary-50 text-primary-700"
                  : "bg-white text-gray-600 hover:bg-gray-50 border"
              }`}
            >
              <MessageCircle className="w-4 h-4" />
              全部对话
            </button>
          </div>

          {loading ? (
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-200 rounded" />
              ))}
            </div>
          ) : (
            <>
              <Table
                columns={columns}
                data={conversations as unknown as Record<string, unknown>[]}
                onRowClick={(item) =>
                  router.push(`/conversations/${item.id}`)
                }
              />
              {totalPages > 1 && (
                <div className="flex justify-center gap-2 mt-4">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                    (p) => (
                      <button
                        key={p}
                        onClick={() => setPage(p)}
                        className={`px-3 py-1.5 text-sm rounded-lg border ${
                          p === page
                            ? "bg-primary-600 text-white border-primary-600"
                            : "hover:bg-gray-50"
                        }`}
                      >
                        {p}
                      </button>
                    )
                  )}
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
