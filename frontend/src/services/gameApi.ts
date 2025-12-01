const API_URL = 'http://localhost:5000';

export const startGame = async () => {
    const body = {
        players: [
            { name: "kat-coder-pro", model_id: "kwaipilot/kat-coder-pro:free" },
            { name: "longcat-flash", model_id: "meituan/longcat-flash-chat:free" },
            { name: "tongyi-deepresearch", model_id: "alibaba/tongyi-deepresearch-30b-a3b:free" },
            { name: "longcat-flash 2", model_id: "meituan/longcat-flash-chat:free" },
        ],
        initial_stack: 10000,
        small_blind: 100,
        big_blind: 200,
        number_of_hands: 7
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