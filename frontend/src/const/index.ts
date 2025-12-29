export const AVAILABLE_MODELS = [
    { name: "Mistral: Devstral 2 2512", id: "mistralai/devstral-2512:free" },
    { name: "AllenAI: Olmo 3 32B Think", id: "allenai/olmo-3-32b-think:free" },
    { name: "Kwaipilot: KAT-Coder-Pro V1", id: "kwaipilot/kat-coder-pro:free" },
    { name: "Meituan: LongCat Flash Chat", id: "meituan/longcat-flash-chat:free" },
    { name: "OpenAI: gpt-oss-20b (free)", id: "openai/gpt-oss-20b:free" },
    { name: "Qwen: Qwen3 4B", id: "qwen/qwen3-4b:free"},
    { name: "Qwen: Qwen3 235B A22B", id: "qwen/qwen3-235b-a22b:free" },
    { name: "Google: Gemma 3 27B", id: "google/gemma-3-27b-it:free" },
    { name: "Venice: Uncensored", id: "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"}

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