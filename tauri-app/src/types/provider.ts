export interface Provider {
  id: string;
  name: string;
  preset: string;
  base_url: string;
  api_key_masked: string;
  text_model: string;
  vision_model: string;
  use_vision: boolean;
  created_at: string;
  updated_at: string;
}

export interface UiPrefs {
  theme: string;
  language: string;
}

export interface ConfigResponse {
  active_id: string;
  providers: Provider[];
  ui: UiPrefs;
}

export interface Preset {
  id: string;
  name: string;
  base_url: string;
  text_model: string;
  vision_model: string;
  use_vision: boolean;
}

export interface AddProviderInput {
  name: string;
  preset: string;
  base_url: string;
  api_key: string;
  text_model: string;
  vision_model: string;
  use_vision: boolean;
}

export interface UpdateProviderInput {
  id: string;
  name: string;
  preset: string;
  base_url: string;
  api_key?: string;
  text_model: string;
  vision_model: string;
  use_vision: boolean;
}
