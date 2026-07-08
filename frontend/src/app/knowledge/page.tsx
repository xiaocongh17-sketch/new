"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { Table } from "@/components/Table";
import { api } from "@/lib/api";
import { KnowledgeDoc } from "@/types";
import { formatDate } from "@/lib/utils";

const categoryLabels: Record<string, string> = {
  SOP: "SOP 流程",
  TRAINING: "培训资料",
  FAQ: "常见问题",
  MARKET: "市场数据",
};

export default function KnowledgePage() {
  const [docs, setDocs] = useState<KnowledgeDoc[]>([]);
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const endpoint = `/knowledge?page=1&page_size=50${category ? `&category=${category}` : ""}`;
    api
      .get<{ items: KnowledgeDoc[] }>(endpoint)
      .then((data) => setDocs(data.items))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [category]);

  const columns = [
    { key: "title", header: "标题" },
    {
      key: "category",
      header: "分类",
      render: (d: KnowledgeDoc) => (
        <span className="inline-flex px-2 py-1 text-xs rounded-full bg-primary-50 text-primary-700">
          {categoryLabels[d.category] || d.category}
        </span>
      ),
    },
    {
      key: "content",
      header: "内容预览",
      render: (d: KnowledgeDoc) => (
        <span className="text-gray-500 truncate block max-w-md">
          {d.content.slice(0, 100)}...
        </span>
      ),
    },
    {
      key: "created_at",
      header: "创建时间",
      render: (d: KnowledgeDoc) => (d.created_at ? formatDate(d.created_at) : "-"),
    },
  ];

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1">
        <Navbar />
        <main className="p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-bold">知识库</h2>
            <p className="text-gray-500 mt-1">共 {docs.length} 篇文档</p>
          </div>

          <div className="mb-4 flex gap-2">
            {["", "SOP", "TRAINING", "FAQ", "MARKET"].map((cat) => (
              <button
                key={cat}
                onClick={() => setCategory(cat)}
                className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                  category === cat
                    ? "bg-primary-600 text-white border-primary-600"
                    : "hover:bg-gray-50"
                }`}
              >
                {cat === "" ? "全部" : categoryLabels[cat] || cat}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-200 rounded" />
              ))}
            </div>
          ) : (
            <Table columns={columns} data={docs as unknown as Record<string, unknown>[]} />
          )}
        </main>
      </div>
    </div>
  );
}
