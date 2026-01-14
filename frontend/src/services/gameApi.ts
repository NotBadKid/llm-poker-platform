import type {GameStartPayload} from "../types/game.ts";

const API_URL = '';


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

export const pauseGame = async (gameId: string) => {
    const response = await fetch(`${API_URL}/game/${gameId}/pause`, {
        method: 'POST',
    });
    if (!response.ok) throw new Error("Failed to pause");
    return response.json();
};

export const resumeGame = async (gameId: string) => {
    const response = await fetch(`${API_URL}/game/${gameId}/resume`, {
        method: 'POST',
    });
    if (!response.ok) throw new Error("Failed to resume");
    return response.json();
};

export const stepGame = async (gameId: string) => {
    const response = await fetch(`${API_URL}/game/${gameId}/step`, {
        method: 'POST',
    });
    if (!response.ok) throw new Error("Failed to step");
    return response.json();
};