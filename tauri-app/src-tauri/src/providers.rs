use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Provider {
    pub id: String,
    pub name: String,
    pub preset: String,
    pub base_url: String,
    #[serde(default)]
    pub api_key: String,
    pub text_model: String,
    pub vision_model: String,
    #[serde(default = "default_true")]
    pub use_vision: bool,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

fn default_true() -> bool {
    true
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UiPrefs {
    #[serde(default = "default_theme")]
    pub theme: String,
    #[serde(default = "default_lang")]
    pub language: String,
}

fn default_theme() -> String {
    "system".into()
}
fn default_lang() -> String {
    "zh".into()
}

impl Default for UiPrefs {
    fn default() -> Self {
        Self {
            theme: default_theme(),
            language: default_lang(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProvidersConfig {
    #[serde(default = "default_version")]
    pub version: u32,
    pub active_id: String,
    pub providers: Vec<Provider>,
    #[serde(default)]
    pub ui: UiPrefs,
}

fn default_version() -> u32 {
    1
}

impl Default for ProvidersConfig {
    fn default() -> Self {
        Self {
            version: 1,
            active_id: String::new(),
            providers: Vec::new(),
            ui: UiPrefs::default(),
        }
    }
}

impl ProvidersConfig {
    #[allow(dead_code)]
    pub fn active_provider(&self) -> Option<&Provider> {
        self.providers.iter().find(|p| p.id == self.active_id)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Preset {
    pub id: &'static str,
    pub name: &'static str,
    pub base_url: &'static str,
    pub text_model: &'static str,
    pub vision_model: &'static str,
    pub use_vision: bool,
}

pub static PRESETS: &[Preset] = &[
    Preset {
        id: "siliconflow",
        name: "硅基流动 SiliconFlow",
        base_url: "https://api.siliconflow.cn",
        text_model: "deepseek-ai/DeepSeek-V3",
        vision_model: "Qwen/Qwen2.5-VL-7B-Instruct",
        use_vision: true,
    },
    Preset {
        id: "deepseek",
        name: "DeepSeek 官方",
        base_url: "https://api.deepseek.com",
        text_model: "deepseek-chat",
        vision_model: "",
        use_vision: false,
    },
    Preset {
        id: "openai",
        name: "OpenAI",
        base_url: "https://api.openai.com",
        text_model: "gpt-4o",
        vision_model: "gpt-4o",
        use_vision: true,
    },
    Preset {
        id: "anthropic",
        name: "Anthropic Claude",
        base_url: "https://api.anthropic.com",
        text_model: "claude-sonnet-4-6-20250514",
        vision_model: "claude-sonnet-4-6-20250514",
        use_vision: true,
    },
    Preset {
        id: "zhipu",
        name: "智谱 GLM",
        base_url: "https://open.bigmodel.cn/api/paas",
        text_model: "glm-4-flash",
        vision_model: "glm-4v-flash",
        use_vision: true,
    },
    Preset {
        id: "moonshot",
        name: "月之暗面 Kimi",
        base_url: "https://api.moonshot.cn",
        text_model: "moonshot-v1-8k",
        vision_model: "",
        use_vision: false,
    },
    Preset {
        id: "qwen",
        name: "阿里通义千问",
        base_url: "https://dashscope.aliyuncs.com/compatible-mode",
        text_model: "qwen-plus",
        vision_model: "qwen-vl-max",
        use_vision: true,
    },
    Preset {
        id: "volcengine",
        name: "火山方舟 (豆包)",
        base_url: "https://ark.cn-beijing.volces.com/api",
        text_model: "doubao-1.5-pro-32k",
        vision_model: "doubao-1.5-vision-pro-32k",
        use_vision: true,
    },
    Preset {
        id: "custom",
        name: "自定义 (OpenAI 兼容)",
        base_url: "http://localhost:8000",
        text_model: "",
        vision_model: "",
        use_vision: false,
    },
];
