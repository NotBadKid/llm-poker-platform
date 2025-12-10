export type CardId = string | null;

export interface ChatMessage {
    player: string,
    action: string | null,
    amount?: number | null,
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
    gameId: string | null,
    gameStage: string | null,
    pot: number,
    communityCards: CardId[],
    players: Player[],
    activePlayer: string | null,
    chatLog: ChatMessage[],
    lastEvent: LastEvent | null,
}

export interface BotPlayerConfig {
    name: string,
    model_id: string,
    user_prompt: string,
    temperature: number,
}

export interface GameStartPayload {
    players: BotPlayerConfig[];
    initial_stack: number,
    small_blind: number,
    big_blind: number,
    number_of_hands: number,
}

export interface BotPlayerConfigUI extends BotPlayerConfig {
    id: number,
    useCustomPrompt: boolean,
}

export interface PlayerStats {
    name: string;
    hands_played: number;
    hands_won: number;
    win_rate: number;
    total_profit: number;
    avg_profit_per_hand: number;
}