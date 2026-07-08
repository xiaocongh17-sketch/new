"use client";

import { LogOut, Menu } from "lucide-react";
import { useAuthStore } from "@/stores/auth";

interface NavbarProps {
  onMenuClick?: () => void;
}

export function Navbar({ onMenuClick }: NavbarProps) {
  const { user, logout } = useAuthStore();

  return (
    <header className="h-16 bg-white border-b flex items-center justify-between px-6">
      <button className="lg:hidden" onClick={onMenuClick}>
        <Menu className="w-6 h-6" />
      </button>

      <div className="flex-1" />

      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-600">
          {user?.name || "用户"}
        </span>
        <button
          onClick={logout}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-red-600 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          退出
        </button>
      </div>
    </header>
  );
}
