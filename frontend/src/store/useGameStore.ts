import type {GameState} from "../types/game.ts";
import {create} from "zustand/react";

const initialState: GameState = {
    gameStage: "Idle",
    pot: 0,
    communityCards: [null, null, null, null, null],
    players: [],
    activePlayer: null,
    chatLog: [],
    lastEvent: null,
}

interface GameStore extends GameState {
    setGameState: (newState: GameState) => void;
}

export const useGameStore = create<GameStore>((set) => ({
    ...initialState,
    setGameState: (newState) => set(newState)
}))