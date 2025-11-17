import { useEffect } from 'react';
import { io } from 'socket.io-client';
import { useGameStore } from '../store/useGameStore';
import type {GameState} from '../types/game';

const SERVER_URL = "http://localhost:5000";

export const useGameSocket = () => {
    const setGameState = useGameStore((state) => state.setGameState);

    useEffect(() => {
        const socket = io(SERVER_URL, {
            transports: ['websocket'],
        });

        socket.on('connect', () => {
            console.log('Connected:', socket.id);
        });

        socket.on('game_update', (data: GameState) => {
            console.log('update:\n', data);
            setGameState(data);
        });
        return () => {
            socket.disconnect();
            console.log('Bye bye');
        };
    }, [setGameState]);
};