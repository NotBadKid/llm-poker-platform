import pokerTableImg from "../../assets/table.png"
import Card from "./Card.tsx";
import type {CardId} from "../../types/game.ts";

interface PokerTableProps {
    pot: number,
    communityCards: CardId[]
}

const PokerTable = ({pot, communityCards,}: PokerTableProps) => {
    return (
        <div
            style={{ backgroundImage: `url(${pokerTableImg})` }}
            id="poker-table"
        >

            <div id="pot">
                <h3 className="text-xl">
                    Pot: ${pot}
                </h3>
            </div>

            <div id="cards-container">
                {communityCards.map((card: CardId, index: number) =>
                    card ? <Card key={index} card={card} /> : <Card key={index} card={null}/>
                )}
            </div>
        </div>
    );
};

export default PokerTable;
