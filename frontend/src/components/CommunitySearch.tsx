"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import { Search, CheckCircle, AlertCircle } from "lucide-react";

interface CommunityItem {
  name: string;
  region: string;
}

interface CommunitySearchProps {
  value: string;
  onChange: (name: string, valid: boolean) => void;
}

export function CommunitySearch({ value, onChange }: CommunitySearchProps) {
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<CommunityItem[]>([]);
  const [open, setOpen] = useState(false);
  const [validated, setValidated] = useState<"valid" | "invalid" | null>(null);
  const [checking, setChecking] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  async function searchCommunities(q: string) {
    if (q.length < 1) {
      setSuggestions([]);
      setOpen(false);
      return;
    }
    try {
      const result = await api.get<{ items: CommunityItem[]; total: number }>(
        `/communities/search?q=${encodeURIComponent(q)}&limit=8`
      );
      setSuggestions(result.items);
      setOpen(result.items.length > 0);
    } catch {
      setSuggestions([]);
    }
  }

  async function checkCommunity(name: string) {
    if (!name.trim()) return;
    setChecking(true);
    try {
      const result = await api.get<{ exists: boolean }>(
        `/communities/check?name=${encodeURIComponent(name.trim())}`
      );
      setValidated(result.exists ? "valid" : "invalid");
      onChange(name, result.exists);
    } catch {
      setValidated(null);
      onChange(name, false);
    } finally {
      setChecking(false);
    }
  }

  function handleInputChange(val: string) {
    setQuery(val);
    setValidated(null);
    onChange(val, false);

    // Debounce search
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => searchCommunities(val), 200);
  }

  function handleSelect(item: CommunityItem) {
    setQuery(item.name);
    setOpen(false);
    setValidated("valid");
    onChange(item.name, true);
  }

  function handleBlur() {
    // Validate on blur
    if (query.trim() && validated === null) {
      setTimeout(() => checkCommunity(query), 200);
    }
  }

  return (
    <div ref={wrapperRef} className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => handleInputChange(e.target.value)}
          onFocus={() => { if (suggestions.length > 0) setOpen(true); }}
          onBlur={handleBlur}
          required
          className={`w-full pl-10 pr-10 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none ${
            validated === "valid"
              ? "border-green-400 bg-green-50"
              : validated === "invalid"
              ? "border-red-400 bg-red-50"
              : ""
          }`}
          placeholder="搜索小区名称..."
        />
        <div className="absolute right-3 top-1/2 -translate-y-1/2">
          {checking ? (
            <span className="w-4 h-4 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin inline-block" />
          ) : validated === "valid" ? (
            <CheckCircle className="w-4 h-4 text-green-500" />
          ) : validated === "invalid" ? (
            <AlertCircle className="w-4 h-4 text-red-500" />
          ) : null}
        </div>
      </div>

      {/* Suggestions dropdown */}
      {open && suggestions.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {suggestions.map((item, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleSelect(item)}
              className="w-full text-left px-3 py-2 hover:bg-primary-50 transition-colors border-b last:border-b-0"
            >
              <span className="text-sm font-medium text-gray-800">{item.name}</span>
              <span className="text-xs text-gray-400 ml-2">{item.region}</span>
            </button>
          ))}
        </div>
      )}

      {/* Validation message */}
      {validated === "invalid" && query.trim() && (
        <p className="text-sm text-amber-600 mt-1 flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />
          该小区暂未开通服务，请确认小区名称是否正确
        </p>
      )}
    </div>
  );
}
