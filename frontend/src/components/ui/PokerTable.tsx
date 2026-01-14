import pokerTableImg from "../../assets/table.png"
import Card from "./Card.tsx";
import type {CardId} from "../../types/game.ts";

interface PokerTableProps {
    pot: number,
    communityCards: CardId[]
}

const PokerTable = ({pot, communityCards,}: PokerTableProps) => {
    return (
        <div className='md:h-full w-full flex justify-center items-center relative'
        >
            <img
                src={pokerTableImg}
                alt="Poker Table"
                className="max-w-full max-h-full w-[80%] object-contain drop-shadow-xl hidden md:block"
            />

            <div className='static md:absolute inset-0 flex flex-col-reverse md:flex-col justify-center items-center gap-6 md:gap-12 md:-translate-y-10 mt-3 -mb-3 md:my-0'>
                <div className='bg-slate-800 px-6 py-2 rounded-lg border-2 border-amber-400 shadow-xl'>
                    <h3 className="text-lg md:text-xl">
                        Pot: ${pot}
                    </h3>
                </div>

                <div className="flex gap-2">
                    {communityCards.map((card: CardId, index: number) =>
                        card ? <Card key={index} card={card} /> : <Card key={index} card={null}/>
                    )}
                </div>
            </div>
        </div>
    );
};

export default PokerTable;
