export const DEFAULT_AVAILABLE_MODELS = [
    {
        name: "Mistral: Devstral 2 2512 (free)",
        model_id: "mistralai/devstral-2512:free",
        parameters: 123000000000,
        input_price: 0,
        output_price: 0,
        structured_outputs: true,
        description: "Devstral 2 is a state-of-the-art open-source model by Mistral AI specializing in agentic coding. It is a 123B-parameter dense transformer model supporting a 256K context window. Devstral 2 supports exploring codebases and orchestrating changes across multiple files while maintaining architecture-level context",
        context: 262144,
        open_router_url: "https://openrouter.ai/mistralai/devstral-2512:free",
    },
    {
        name: "Kwaipilot: KAT-Coder-Pro V1 (free)",
        model_id: "kwaipilot/kat-coder-pro:free",
        parameters: null,
        input_price: 0,
        output_price: 0,
        structured_outputs: true,
        description: "KAT-Coder-Pro V1 is KwaiKAT's most advanced agentic coding model in the KAT-Coder series. Designed specifically for agentic coding tasks, it excels in real-world software engineering scenarios, achieving 73.4% solve rate on the SWE-Bench Verified benchmark.",
        context: 256000,
        open_router_url: "https://openrouter.ai/kwaipilot/kat-coder-pro:free",
    },
    {
        name: "OpenAI: gpt-oss-20b (free)",
        model_id: "openai/gpt-oss-20b:free",
        parameters: 3600000000,
        input_price: 0,
        output_price: 0,
        structured_outputs: true,
        description: "gpt-oss-20b is an open-weight 21B parameter model released by OpenAI under the Apache 2.0 license. It uses a Mixture-of-Experts (MoE) architecture with 3.6B active parameters per forward pass, optimized for lower-latency inference and deployability on consumer or single-GPU hardware.",
        context: 131072,
        open_router_url: "https://openrouter.ai/openai/gpt-oss-20b:free",
    },
    {
        name: "AllenAI: Olmo 3.1 32B Think (free)",
        model_id: "allenai/olmo-3.1-32b-think:free",
        parameters: 32000000000,
        input_price: 0,
        output_price: 0,
        structured_outputs: true,
        description: "Olmo 3.1 32B Think is a large-scale, 32-billion-parameter model designed for deep reasoning, complex multi-step logic, and advanced instruction following. Building on the Olmo 3 series, version 3.1 delivers refined reasoning behavior and stronger performance across demanding evaluations and nuanced conversational tasks.",
        context: 65536,
        open_router_url: "https://openrouter.ai/allenai/olmo-3.1-32b-think:free",
    },
];

export const STATS_HEADERS = [
    {
        header: "Parameters",
        sortKey: "parameters",
    },
    {
        header: "Hands Played",
        sortKey: "hands_played",
    },
    {
        header: "Hands Won",
        sortKey: "hands_won",
    },
    {
        header: "Win Rate",
        sortKey: "win_rate",
    },
    {
        header: "Total Profit",
        sortKey: "total_profit",
    },
    {
        header: "Avg Profit/Hand",
        sortKey: "avg_profit_per_hand",
    },
]