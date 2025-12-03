import {FaLock} from "react-icons/fa";

interface Props {
    content: string,
    onClick: () => void,
    className?: string,
    disabled?: boolean
}

const HomeButton = ({content, onClick, className, disabled}: Props) => {
    return (
        <button
            onClick={onClick}
            className={`px-10 py-2 rounded-2xl text-xl shadow-lg focus:outline-none pointer 
                ${className} 
                ${disabled ? 'disabled flex items-center gap-4 justify-center' : 'hover:scale-110 transition transform cursor-pointer'}`
            }
        >
            {content}
            {disabled && <FaLock/>}
        </button>
    );
};

export default HomeButton;
