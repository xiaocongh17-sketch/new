"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";

export default function LoginPage() {
  const [wecomUserid, setWecomUserid] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginMode, setLoginMode] = useState<"wecom" | "password">("wecom");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();
  const { setUser } = useAuthStore();

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const payload: Record<string, string> = {};
      if (loginMode === "wecom") {
        payload.wecom_userid = wecomUserid;
      } else {
        payload.username = username;
        payload.password = password;
      }

      const result = await api.post<{
        access_token: string;
        refresh_token: string;
      }>("/auth/login", payload);

      localStorage.setItem("access_token", result.access_token);
      if (result.refresh_token) {
        localStorage.setItem("refresh_token", result.refresh_token);
      }

      // Decode user info from JWT token payload
      const jwtPayload = JSON.parse(atob(result.access_token.split(".")[1]));
      const displayName = loginMode === "wecom" ? wecomUserid : username;
      setUser({
        id: jwtPayload.sub,
        wecom_userid: wecomUserid || username || "",
        name: displayName || "",
        role: jwtPayload.role || "agent",
        store_id: jwtPayload.store_id || null,
        is_active: true,
      });

      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-sm border p-8">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-gray-900">
              AI Store Copilot
            </h1>
            <p className="text-gray-500 mt-2">门店经营助手 · 登录</p>
          </div>

          {/* Login mode toggle */}
          <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
            <button
              type="button"
              onClick={() => setLoginMode("wecom")}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                loginMode === "wecom"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              企业微信登录
            </button>
            <button
              type="button"
              onClick={() => setLoginMode("password")}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                loginMode === "password"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              密码登录
            </button>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            {loginMode === "wecom" ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  企业微信 UserID
                </label>
                <input
                  type="text"
                  value={wecomUserid}
                  onChange={(e) => setWecomUserid(e.target.value)}
                  placeholder="输入企业微信 ID"
                  className="w-full px-3 py-2.5 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                  required
                />
              </div>
            ) : (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    用户名
                  </label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="输入用户名"
                    className="w-full px-3 py-2.5 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    密码
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="输入密码"
                    className="w-full px-3 py-2.5 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                    required
                  />
                </div>
              </>
            )}

            {error && (
              <p className="text-sm text-red-600">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors"
            >
              {loading ? "登录中..." : "登录"}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-500">
            还没有账号？{" "}
            <Link href="/register" className="text-primary-600 hover:text-primary-700 font-medium">
              立即注册
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
