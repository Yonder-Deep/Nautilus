import { useRef, useEffect } from "react"

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

export const StatusMessages = ({ statusMessages, setStatusMessages }:any) => {
    const bottomRef = useRef<HTMLDivElement>(null!);

    const scrollToMessagesBottom = () => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    };
	const clearMessages = () => {
		setStatusMessages([]);
	};

    useEffect(() => {
        if (bottomRef.current.scrollHeight - bottomRef.current.clientHeight <= bottomRef.current.scrollTop + 5)
            scrollToMessagesBottom()
    }, [statusMessages]);

	return (
		<div className="status-messages-container">
			<h2>Status Messages</h2>
			<ul className="status-messages">
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
                <div ref={bottomRef}></div>
			</ul>
			<div className="status-messages-bottom-bar">
				<button onClick={() => clearMessages()}>Clear Output</button>
			</div>
		</div>
	)
}