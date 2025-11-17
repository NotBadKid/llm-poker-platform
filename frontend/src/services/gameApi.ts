const API_URL = 'http://localhost:5000';

export const startGame = async () => {
    const body = {
        players: [
            { name: "KAWIPILOT", model_id: "kwaipilot/kat-coder-pro:free" },
            { name: "NEMOTRONNANO ale to kot", model_id: "meituan/longcat-flash-chat:free" },
            { name: "ALIBABA KRUL KEBABA", model_id: "alibaba/tongyi-deepresearch-30b-a3b:free" },
            { name: "DLUGI KOT", model_id: "meituan/longcat-flash-chat:free" },
        ],
        initial_stack: 10000,
        small_blind: 10,
        big_blind: 20,
        number_of_hands: 5
    };

    try {
        const response = await fetch(`${API_URL}/game/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            throw new Error(`ERROR: ${response.status}`);
        }

        console.log("Here we go brotha'");
        return await response.json();
    } catch (error) {
        console.error('NOOOOO', error);
        alert(":(");
    }
};