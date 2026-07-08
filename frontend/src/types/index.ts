export interface House {
  id: string;
  community: string;
  area: number;
  room_type: string;
  rent_price: number;
  unit_price?: number;
  decoration?: string;
  floor_info?: string;
  address?: string;
  status: string;
  owner_id: string;
  store_id?: string;
  created_at: string;
}

export interface HouseListResponse {
  items: House[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Employee {
  id: string;
  wecom_userid: string;
  name: string;
  role: string;
  phone?: string;
  is_active: boolean;
  created_at?: string;
}

export interface KnowledgeDoc {
  id: string;
  title: string;
  content: string;
  category: string;
  created_at?: string;
}

export interface DashboardStats {
  total_houses: number;
  active_houses: number;
  total_employees: number;
  total_conversations: number;
  pending_review_conversations: number;
}

export interface Conversation {
  id: string;
  wecom_group_id: string;
  participants: string[];
  context: Record<string, unknown>;
  status: string;
  created_at: string;
  updated_at: string;
}
