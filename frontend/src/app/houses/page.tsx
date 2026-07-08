"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { Table } from "@/components/Table";
import { api } from "@/lib/api";
import { formatPrice, formatDate } from "@/lib/utils";
import { House } from "@/types";
import Link from "next/link";
import { Plus, Search, Trash2 } from "lucide-react";

export default function HousesPage() {
  const [houses, setHouses] = useState<House[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  const pageSize = 20;

  function fetchHouses() {
    setLoading(true);
    api
      .get<{ items: House[]; total: number }>(
        `/houses?page=${page}&page_size=${pageSize}${search ? `&community=${search}` : ""}`
      )
      .then((data) => {
        setHouses(data.items);
        setTotal(data.total);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchHouses();
  }, [page, search]);

  async function handleDelete(id: string, community: string) {
    if (!confirm(`确定删除房源 "${community}" 吗？此操作不可恢复。`)) return;
    setDeleting(id);
    try {
      await api.delete(`/houses/${id}`);
      fetchHouses();
    } catch (err) {
      alert(err instanceof Error ? err.message : "删除失败");
    } finally {
      setDeleting(null);
    }
  }

  const columns = [
    { key: "community", header: "小区" },
    {
      key: "area",
      header: "面积",
      render: (h: House) => `${h.area}㎡`,
    },
    { key: "room_type", header: "户型" },
    {
      key: "rent_price",
      header: "租金",
      render: (h: House) => formatPrice(h.rent_price),
    },
    {
      key: "status",
      header: "状态",
      render: (h: House) => (
        <span
          className={`inline-flex px-2 py-1 text-xs rounded-full font-medium ${
            h.status === "active"
              ? "bg-green-100 text-green-700"
              : h.status === "rented"
              ? "bg-blue-100 text-blue-700"
              : "bg-gray-100 text-gray-600"
          }`}
        >
          {h.status === "active" ? "出租中" : h.status === "rented" ? "已出租" : "已下架"}
        </span>
      ),
    },
    {
      key: "created_at",
      header: "创建时间",
      render: (h: House) => formatDate(h.created_at),
    },
    {
      key: "actions",
      header: "操作",
      render: (h: House) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            handleDelete(h.id, h.community);
          }}
          disabled={deleting === h.id}
          className="flex items-center gap-1 px-2 py-1 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 rounded disabled:opacity-50 transition-colors"
        >
          <Trash2 className="w-3 h-3" />
          {deleting === h.id ? "删除中..." : "删除"}
        </button>
      ),
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
              <h2 className="text-2xl font-bold">房源管理</h2>
              <p className="text-gray-500 mt-1">共 {total} 套房源</p>
            </div>
            <Link
              href="/houses/new"
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              新增房源
            </Link>
          </div>

          <div className="mb-4 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="搜索小区名称..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full max-w-md pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
            />
          </div>

          {loading ? (
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-200 rounded" />
              ))}
            </div>
          ) : (
            <>
              <Table columns={columns} data={houses as unknown as Record<string, unknown>[]} />
              {totalPages > 1 && (
                <div className="flex justify-center gap-2 mt-4">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
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
                  ))}
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
