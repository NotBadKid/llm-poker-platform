import React, {useRef, useState} from "react";
import {HiMiniQuestionMarkCircle} from "react-icons/hi2";

interface Props {
    children: React.ReactNode
}

const Tooltip = ({children,}: Props) => {
    const [isVisible, setIsVisible] = useState<boolean>(false)
    const timeoutRef = useRef<number>(0);

    const handleMouseEnter = () => {
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }
        setIsVisible(true);
    };

    const handleMouseLeave = () => {
        timeoutRef.current = setTimeout(() => {
            setIsVisible(false);
        }, 300);
    };

    return (
        <div className="relative inline-block"
             onMouseEnter={() => {handleMouseEnter()}}
             onMouseLeave={() => {handleMouseLeave()}}
        >
            <TooltipTrigger/>

            {isVisible && (
                <TooltipContent>
                    {children}
                </TooltipContent>
            )}
        </div>
    );
};


function TooltipTrigger() {
    return <div className="text-3xl text-purple-700 cursor-pointer hover:text-purple-500 transition-colors">
        <HiMiniQuestionMarkCircle />
    </div>
}

function TooltipContent({children,}: Props ) {
    return <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-lg opacity-95 bg-slate-900 p-4 rounded-xl border border-purple-500 shadow-2xl text-slate-400 text-lg">
        {children}
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-purple-500"></div>
    </div>
}

export default Tooltip;
