export const getCardImage = (card: string | null): string => {
    if (card === null) {
        return '/cards/back.png'
    }

    return `cards/${card}.png`
}