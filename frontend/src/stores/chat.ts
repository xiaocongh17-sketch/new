import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

const WELCOME: ChatMessage = {
  role: "assistant",
  content:
    "你好！我是 AI 门店业务助手，已关联房源数据库。\n\n" +
    "💬 业务咨询：\n- 如何邀约房东？\n- 佣金怎么算？\n\n" +
    "🏠 房源查询：\n- 有哪些一室一厅在出租？\n- 2000以内的房源推荐\n- 朝阳区有什么房源？",
};

const COLLECT_WELCOME: ChatMessage = {
  role: "assistant",
  content:
    "🏠 **房源采集模式已开启**\n\n我是你的AI采集助手。请直接告诉我你了解到的房源信息，我会一步步引导你完善所有关键字段。\n\n例如：*\"今天联系了一个房东，融创壹号院的，120平三房两厅，想卖350万\"*",
};

interface ChatState {
  messages: ChatMessage[];
  mode: "chat" | "collect";
  collected: Record<string, string>;
  collectScore: number;
  savedHouseId: string | null;
  addMessage: (msg: ChatMessage) => void;
  setMessages: (msgs: ChatMessage[]) => void;
  clearMessages: () => void;
  setMode: (mode: "chat" | "collect") => void;
  setCollected: (collected: Record<string, string> | ((prev: Record<string, string>) => Record<string, string>)) => void;
  setCollectScore: (score: number) => void;
  setSavedHouseId: (id: string | null) => void;
  resetCollect: () => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: [WELCOME],
      mode: "chat" as const,
      collected: {},
      collectScore: 0,
      savedHouseId: null,

      addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
      setMessages: (msgs) => set({ messages: msgs }),
      clearMessages: () => set((s) => ({
        messages: s.mode === "collect" ? [COLLECT_WELCOME] : [WELCOME],
        collected: {},
        collectScore: 0,
        savedHouseId: null,
      })),

      setMode: (mode) => set((s) => {
        if (mode === s.mode) return {};
        if (mode === "collect") {
          return {
            mode,
            messages: [COLLECT_WELCOME],
            collected: {},
            collectScore: 0,
            savedHouseId: null,
          };
        }
        return {
          mode,
          messages: [WELCOME],
          collected: {},
          collectScore: 0,
          savedHouseId: null,
        };
      }),

      setCollected: (collected) => set((s) => ({
        collected: typeof collected === "function" ? collected(s.collected) : collected,
      })),
      setCollectScore: (score) => set({ collectScore: score }),
      setSavedHouseId: (id) => set({ savedHouseId: id }),
      resetCollect: () => set({ collected: {}, collectScore: 0, savedHouseId: null }),
    }),
    { name: "ai-chat-store" }
  )
);
