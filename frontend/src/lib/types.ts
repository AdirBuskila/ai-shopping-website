export interface Product {
  id: number;
  name: string;
  brand?: string | null;
  category?: string | null;
  price_usd: number;
  stock: number;
  image_url?: string | null;
  description?: string | null;
}

export interface UserPublic {
  id: number;
  username: string;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
}

export interface OrderItem {
  product_id: number;
  name: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

export interface Order {
  id: number;
  user_id: number;
  status: "TEMP" | "CLOSE";
  shipping_address?: string | null;
  total_price: number;
  created_at?: string | null;
  closed_at?: string | null;
  items: OrderItem[];
}

export interface ProductRef {
  id: number;
  name: string;
  image_url?: string | null;
  price_usd: number;
}

export interface ChatResponse {
  reply: string;
  remaining_prompts: number;
  available: boolean;
  sources: ProductRef[];
}

export interface RegisterData {
  username: string;
  password: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  country?: string;
  city?: string;
}
