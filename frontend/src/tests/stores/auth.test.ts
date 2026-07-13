import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "@/stores/auth";

// Mock localStorage for jsdom environment
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
    get length() { return Object.keys(store).length; },
    key: (index: number) => Object.keys(store)[index] ?? null,
  };
})();

Object.defineProperty(globalThis, "localStorage", {
  value: localStorageMock,
  writable: true,
  configurable: true,
});

describe("AuthStore", () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, isAuthenticated: false });
    localStorageMock.clear();
  });

  it("initial state has no user", () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it("setUser updates user and authentication status", () => {
    const mockUser = {
      id: "123",
      wecom_userid: "test_user",
      name: "测试用户",
      role: "agent",
      store_id: null,
      is_active: true,
    };
    useAuthStore.getState().setUser(mockUser);
    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.isAuthenticated).toBe(true);
  });

  it("logout clears user and token", () => {
    const mockUser = {
      id: "123",
      wecom_userid: "test_user",
      name: "测试用户",
      role: "agent",
      store_id: null,
      is_active: true,
    };
    useAuthStore.getState().setUser(mockUser);
    useAuthStore.getState().logout();
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });
});
