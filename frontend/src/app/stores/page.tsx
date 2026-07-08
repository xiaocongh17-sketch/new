"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { Table } from "@/components/Table";
import { api } from "@/lib/api";

interface Store {
  id: string;
  name: string;
  code: string;
  address?: string;
  contact_phone?: string;
  is_active: boolean;
}

export default function StoresPage() {
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<{ items: Store[] }>("/stores")
      .then((data) => setStores(data.items))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const columns = [
    { key: "name", header: "门店名称" },
    { key: "code", header: "门店编码" },
    { key: "address", header: "地址", render: (s: Store) => s.address || "-" },
    { key: "contact_phone", header: "联系电话", render: (s: Store) => s.contact_phone || "-" },
    {
      key: "is_active",
      header: "状态",
      render: (s: Store) => (
        <span
          className={`inline-flex px-2 py-1 text-xs rounded-full ${
            s.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
          }`}
        >
          {s.is_active ? "营业中" : "已关闭"}
        </span>
      ),
    },
  ];

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1">
        <Navbar />
        <main className="p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-bold">门店管理</h2>
            <p className="text-gray-500 mt-1">共 {stores.length} 家门店</p>
          </div>

          {loading ? (
            <div className="animate-pulse space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-200 rounded" />
              ))}
            </div>
          ) : (
            <Table columns={columns} data={stores as unknown as Record<string, unknown>[]} />
          )}
        </main>
      </div>
    </div>
  );
}
