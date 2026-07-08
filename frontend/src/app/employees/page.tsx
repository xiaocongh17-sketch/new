"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { Table } from "@/components/Table";
import { api } from "@/lib/api";
import { Employee } from "@/types";

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<{ items: Employee[] }>("/employees")
      .then((data) => setEmployees(data.items))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const columns = [
    { key: "name", header: "姓名" },
    { key: "wecom_userid", header: "企业微信 ID" },
    {
      key: "role",
      header: "角色",
      render: (e: Employee) => {
        const roleMap: Record<string, string> = {
          admin: "管理员",
          store_manager: "店长",
          agent: "业务员",
          landlord: "房东",
        };
        return (
          <span className="inline-flex px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-700">
            {roleMap[e.role] || e.role}
          </span>
        );
      },
    },
    { key: "phone", header: "电话", render: (e: Employee) => e.phone || "-" },
    {
      key: "is_active",
      header: "状态",
      render: (e: Employee) => (
        <span
          className={`inline-flex px-2 py-1 text-xs rounded-full ${
            e.is_active
              ? "bg-green-100 text-green-700"
              : "bg-gray-100 text-gray-500"
          }`}
        >
          {e.is_active ? "活跃" : "已禁用"}
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
            <h2 className="text-2xl font-bold">员工管理</h2>
            <p className="text-gray-500 mt-1">共 {employees.length} 名员工</p>
          </div>

          {loading ? (
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-200 rounded" />
              ))}
            </div>
          ) : (
            <Table columns={columns} data={employees as unknown as Record<string, unknown>[]} />
          )}
        </main>
      </div>
    </div>
  );
}
