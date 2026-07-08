"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { api } from "@/lib/api";
import { formatPrice, formatDate } from "@/lib/utils";
import { House } from "@/types";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function HouseDetailPage() {
  const params = useParams();
  const [house, setHouse] = useState<House | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.id) {
      api
        .get<House>(`/houses/${params.id}`)
        .then(setHouse)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [params.id]);

  if (loading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <Sidebar />
        <div className="flex-1 p-6 animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4" />
          <div className="h-64 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (!house) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <Sidebar />
        <div className="flex-1 p-6">
          <p className="text-gray-500">房源未找到</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1">
        <Navbar />
        <main className="p-6">
          <Link
            href="/houses"
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-6"
          >
            <ArrowLeft className="w-4 h-4" />
            返回房源列表
          </Link>

          <div className="bg-white rounded-xl border p-6">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-2xl font-bold">{house.community}</h2>
                <p className="text-gray-500 mt-1">{house.room_type}</p>
              </div>
              <span
                className={`px-3 py-1 text-sm rounded-full font-medium ${
                  house.status === "active"
                    ? "bg-green-100 text-green-700"
                    : house.status === "rented"
                    ? "bg-blue-100 text-blue-700"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                {house.status === "active" ? "出租中" : house.status === "rented" ? "已出租" : "已下架"}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {house.address && (
                <InfoItem label="地址" value={house.address} />
              )}
              <InfoItem label="面积" value={`${house.area} ㎡`} />
              <InfoItem
                label="租金"
                value={formatPrice(house.rent_price)}
              />
              <InfoItem
                label="单价"
                value={house.unit_price ? `${formatPrice(house.unit_price)}/㎡` : "-"}
              />
              <InfoItem
                label="装修"
                value={house.decoration || "未说明"}
              />
              <InfoItem label="楼层" value={house.floor_info || "未说明"} />
              <InfoItem
                label="创建时间"
                value={formatDate(house.created_at)}
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-lg font-semibold mt-1">{value}</p>
    </div>
  );
}
