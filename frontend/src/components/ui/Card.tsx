import {getCardImage} from "../../utils/cardUtils.ts";

interface CardProps {
    card: string | null,
}

const Card = ({card}: CardProps) => {
    const imageUrl = getCardImage(card);

    return (
        <img
            className="w-14 md:w-16 rounded"
            src={imageUrl}
            alt={card || "Card"}
        />
    );
};

export default Card;
