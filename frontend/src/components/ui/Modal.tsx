import {XIcon} from "lucide-react";
import {type ReactNode, useEffect} from "react";

interface Props {
    isOpen: boolean,
    onClose: () => void,
    children: ReactNode,
    title: string,
}

const Modal = ({isOpen, onClose, children, title}: Props) => {
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                onClose();
            }
        }

        if (isOpen) {
            window.addEventListener('keydown', handleKeyDown);
        }

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
        }
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 z-9999 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div
                className="bg-slate-800 border border-slate-600 rounded-lg shadow-xl w-full max-w-2xl h-[90%] flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="border-b border-slate-600 p-6 relative">
                    <h3 className="font-semibold text-xl">
                        {title}
                    </h3>
                    <XIcon
                        className="opacity-60 hover:opacity-80 transition cursor-pointer absolute right-5 top-5"
                        onClick={onClose}
                    />
                </div>

                {children}

            </div>
        </div>
    );
};

export default Modal;