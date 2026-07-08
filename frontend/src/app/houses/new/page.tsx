"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { api } from "@/lib/api";
import { RegionCascader } from "@/components/RegionCascader";
import { CommunitySearch } from "@/components/CommunitySearch";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

function getUserId(): string | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem("access_token");
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.sub || null;
  } catch {
    return null;
  }
}

export default function NewHousePage() {
  const router = useRouter();

  const [form, setForm] = useState({
    community: "",
    area: "",
    room_type: "",
    rent_price: "",
    decoration: "",
    floor_info: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [regionLabel, setRegionLabel] = useState("");
  const [communityValid, setCommunityValid] = useState(false);

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const ownerId = getUserId();
      if (!ownerId) {
        setError("无法获取用户信息，请重新登录");
        setLoading(false);
        return;
      }
      if (!communityValid) {
        setError("该小区暂未开通服务，请从楼盘字典中选择小区");
        setLoading(false);
        return;
      }

      const body = {
        community: form.community,
        address: regionLabel || undefined,
        area: parseFloat(form.area),
        room_type: form.room_type,
        rent_price: parseFloat(form.rent_price),
        decoration: form.decoration || undefined,
        floor_info: form.floor_info || undefined,
        owner_id: ownerId,
      };

      await api.post("/houses", body);
      router.push("/houses");
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
    } finally {
      setLoading(false);
    }
  }

  const roomTypes = ["一室一厅", "两室一厅", "三室一厅", "三室两厅", "四室两厅", "开间", "其他"];
  const decorations = ["精装", "简装", "毛坯", "其他"];

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1">
        <Navbar />
        <main className="p-6 max-w-2xl">
          <Link
            href="/houses"
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-6"
          >
            <ArrowLeft className="w-4 h-4" />
            返回房源列表
          </Link>

          <div className="bg-white rounded-xl border p-6">
            <h2 className="text-xl font-bold mb-6">新增房源</h2>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  小区名称 <span className="text-red-500">*</span>
                </label>
                <CommunitySearch
                  value={form.community}
                  onChange={(name, valid) => {
                    setForm({ ...form, community: name });
                    setCommunityValid(valid);
                  }}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  所在区域 <span className="text-red-500">*</span>
                </label>
                <RegionCascader
                  onChange={(v) => setRegionLabel(v.label)}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    面积 (㎡) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    name="area"
                    value={form.area}
                    onChange={handleChange}
                    required
                    step="0.01"
                    min="0"
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
                    placeholder="如：89.5"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    户型 <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="room_type"
                    value={form.room_type}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
                  >
                    <option value="">选择户型</option>
                    {roomTypes.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    月租金 (元) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    name="rent_price"
                    value={form.rent_price}
                    onChange={handleChange}
                    required
                    step="0.01"
                    min="0"
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
                    placeholder="如：3500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    装修情况
                  </label>
                  <select
                    name="decoration"
                    value={form.decoration}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
                  >
                    <option value="">选择装修</option>
                    {decorations.map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  楼层信息
                </label>
                <input
                  type="text"
                  name="floor_info"
                  value={form.floor_info}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
                  placeholder="如：15层/共30层"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors"
              >
                {loading ? "创建中..." : "创建房源"}
              </button>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
}
