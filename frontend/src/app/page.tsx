"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { StatCard } from "@/components/StatCard";
import { api } from "@/lib/api";
import { DashboardStats } from "@/types";
import { Home, Users, MessageSquare, AlertCircle } from "lucide-react";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<DashboardStats>("/dashboard/stats")
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1">
        <Navbar />
        <main className="p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-bold">Dashboard</h2>
            <p className="text-gray-500 mt-1">门店经营概览</p>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="bg-white rounded-xl border p-6 animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
                  <div className="h-8 bg-gray-200 rounded w-1/3" />
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                title="房源总数"
                value={stats?.total_houses ?? 0}
                icon={Home}
                description="全部房源"
              />
              <StatCard
                title="在租房源"
                value={stats?.active_houses ?? 0}
                icon={Home}
                description="当前出租中"
              />
              <StatCard
                title="员工数"
                value={stats?.total_employees ?? 0}
                icon={Users}
                description="门店团队"
              />
              <StatCard
                title="待审对话"
                value={stats?.pending_review_conversations ?? 0}
                icon={AlertCircle}
                description="需人工处理"
              />
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <div className="bg-white rounded-xl border p-6">
              <h3 className="text-lg font-semibold mb-4">对话概览</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">总对话数</span>
                  <span className="font-medium">{stats?.total_conversations ?? 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">待审对话</span>
                  <span className="font-medium text-amber-600">
                    {stats?.pending_review_conversations ?? 0}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl border p-6">
              <h3 className="text-lg font-semibold mb-4">房源状态</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">全部房源</span>
                  <span className="font-medium">{stats?.total_houses ?? 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">在租房源</span>
                  <span className="font-medium text-green-600">
                    {stats?.active_houses ?? 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
