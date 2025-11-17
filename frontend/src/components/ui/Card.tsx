import {getCardImage} from "../../utils/cardUtils.ts";

interface CardProps {
    card: string | null,
}

const Card = ({card}: CardProps) => {
    const imageUrl = getCardImage(card);

    return (
        <img
            className="w-16"
            src={imageUrl}
            alt={card || "Card"}
        />
    );
};

export default Card;
