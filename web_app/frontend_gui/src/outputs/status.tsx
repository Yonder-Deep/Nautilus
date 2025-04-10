import React, { useRef, useEffect, useState} from "react"

interface dataPart {
    id: number,
    title: string,
    value: string
}

export const StatusItem = ({ statusType, statusData }:any) => {
    const statusListItems = statusData.map((dataPart: dataPart) =>
        <li key={dataPart.id}>{dataPart.title}: {dataPart.value}</li>
    )

    return (
        <div className="status-item">
            <h2>{statusType}</h2>
            <ul>{statusListItems}</ul>
        </div>
    )
}

export const StatusMessages = ({
    statusMessages,
    setStatusMessages
}: {
        statusMessages: string[],
        setStatusMessages: React.Dispatch<React.SetStateAction<string[]>>
    }) => {
    const listRef = useRef<HTMLUListElement>(undefined!);
    const [doScroll, setDoScroll] = useState<boolean>();

    const clearMessages = () => {
        setStatusMessages([]);
    };

    const checkScroll = () => {
        const list = listRef.current;
        setDoScroll(list.scrollHeight - list.clientHeight <= list.scrollTop);
    };

    useEffect(() => { // Check for scroll decoupled from react render loop
        listRef.current.addEventListener("scroll", checkScroll);
    });

    useEffect(() => { // This bit is for autoscroll (50px as a buffer to bottom of scroll container)
        const list = listRef.current;
        if(doScroll) {
            list.scrollTop = list.scrollHeight - list.clientHeight;
        }
        checkScroll();
    }, [statusMessages]);

    return (
        <div className="status-messages-container">
            <h2>Status Messages</h2>
            <ul ref={listRef} className="status-messages">
                {statusMessages?.map((message: any, index: any) => {
                    try {
                        const newMessage: any = JSON.parse(message);
                        message = JSON.stringify(newMessage, null, 2);
                    }
                    catch {}
                    return (
                        <li key={index}>
                            <pre>{message}</pre>
                        </li>
                    )
                })}
            </ul>
            <div className="status-messages-bottom-bar">
                <button onClick={() => clearMessages()}>Clear Output</button>
                <h3>Scroll?: {doScroll + ""}</h3>
            </div>
        </div>
    )
}
