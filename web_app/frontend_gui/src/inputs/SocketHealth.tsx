import { useState } from "react";
import styles from "./SocketHealth.module.css";
import { RestartSvg, PingSvg } from "../utils/icons";

export const SocketHealth = ({ websocket }: any) => {
    const [status, setStatus] = useState<"open"|"closed"|"unknown">("unknown");
    const restart = () => {
        const request = {
            command: "websocket",
            content: "restart",
        };
        websocket.send(JSON.stringify(request));
    }
    const ping = () => {
        setStatus("unknown");
        const request = {
            command: "websocket",
            content: "ping",
        };
        websocket.send(JSON.stringify(request));
    }

    return (
        <div>
            <h2>Websocket Health</h2>
            <div className={styles.socketForm}>
                <p>Status: {status}</p>
                <div className={styles.socketButtons}>
                    <button onClick={() => ping()}>
                        <PingSvg/>
                    </button>
                    <button onClick={() => restart()}>
                        <RestartSvg/>
                    </button>
            </div>
            </div>
        </div>
    )
}
