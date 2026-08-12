export interface User {
  username: string;
  display_name: string | null;
  created_at: string;
  email: string | null;
  silaeder_linked: boolean;
}

export type MediaType = "image" | "audio" | "text" | "other";

export interface Creation {
  id: string;
  title: string | null;
  description: string | null;
  media_type: MediaType;
  file_url: string | null;
  category: string | null;
  created_at: string;
}

export interface CreationWithStats extends Creation {
  likes_count: number;
  is_hidden: boolean;
}

export interface FeedResponse {
  creation: Creation | null;
  exhausted: boolean;
}

export interface LikeToggleResponse {
  creation_id: string;
  liked: boolean;
  likes_count: number;
}
