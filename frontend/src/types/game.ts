export type CardId = string | null;

export interface ChatLog {
    player: string,
    action: string,
    message: string,
}

export interface Player {
    name: string,
    chipCount: number,
    currentBet: number,
    holeCards: [CardId, CardId],
}

export interface LastEvent {
    action: string,
    player: string,
    amount: number,
    comment: string,
}

export interface GameState {
    gameStage: string | null,
    pot: number,
    communityCards: CardId[],
    players: Player[],
    activePlayer: string | null,
    chatLog: ChatLog[],
    lastEvent: LastEvent | null,
}