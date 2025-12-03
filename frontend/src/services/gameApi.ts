import type {GameStartPayload} from "../types/game.ts";

const API_URL = 'http://localhost:5000';


export const startGame = async (gameConfig: GameStartPayload) => {
    try {
        const response = await fetch(`${API_URL}/game/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(gameConfig),
        });

        if (!response.ok) {
            throw new Error(`ERROR: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        alert(":(");
    }
};