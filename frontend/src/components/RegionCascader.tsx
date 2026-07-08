"use client";

import { useState, useMemo } from "react";
import regions from "@/data/regions.json";

interface RegionCascaderProps {
  value?: { province: string; city: string; district: string };
  onChange?: (value: { province: string; city: string; district: string; label: string }) => void;
}

export function RegionCascader({ value, onChange }: RegionCascaderProps) {
  const [province, setProvince] = useState(value?.province || "");
  const [city, setCity] = useState(value?.city || "");
  const [district, setDistrict] = useState(value?.district || "");

  const selectedProvince = useMemo(
    () => regions.find((p) => p.name === province),
    [province]
  );

  const selectedCity = useMemo(
    () => selectedProvince?.cities.find((c) => c.name === city),
    [selectedProvince, city]
  );

  function handleProvinceChange(name: string) {
    setProvince(name);
    setCity("");
    setDistrict("");
    if (onChange) onChange({ province: name, city: "", district: "", label: name });
  }

  function handleCityChange(name: string) {
    setCity(name);
    setDistrict("");
    if (onChange) {
      onChange({ province, city: name, district: "", label: `${province} ${name}` });
    }
  }

  function handleDistrictChange(name: string) {
    setDistrict(name);
    if (onChange) {
      onChange({
        province,
        city,
        district: name,
        label: `${province} ${city} ${name}`,
      });
    }
  }

  return (
    <div className="grid grid-cols-3 gap-3">
      <div>
        <label className="block text-sm font-medium text-gray-600 mb-1">
          省份 <span className="text-red-500">*</span>
        </label>
        <select
          value={province}
          onChange={(e) => handleProvinceChange(e.target.value)}
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none text-sm"
        >
          <option value="">选择省份</option>
          {regions.map((p) => (
            <option key={p.name} value={p.name}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-600 mb-1">
          城市 <span className="text-red-500">*</span>
        </label>
        <select
          value={city}
          onChange={(e) => handleCityChange(e.target.value)}
          disabled={!province}
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <option value="">选择城市</option>
          {selectedProvince?.cities.map((c) => (
            <option key={c.name} value={c.name}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-600 mb-1">
          区/县 <span className="text-red-500">*</span>
        </label>
        <select
          value={district}
          onChange={(e) => handleDistrictChange(e.target.value)}
          disabled={!city}
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <option value="">选择区/县</option>
          {selectedCity?.districts.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
