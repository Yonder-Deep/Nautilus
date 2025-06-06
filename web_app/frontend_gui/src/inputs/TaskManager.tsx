import { useState, useEffect, useCallback, FC } from "react"
import { Tasks, isData } from "../types"
import { RestartSvg } from "../utils/icons"
import styles from "./TaskManager.module.css"

const tryJson = (raw: any): any => {
    try {
        return JSON.parse(raw)
    }
    catch {
        return undefined
    }
}

const useForceUpdate = () => {
     const [, setValue] = useState(0);
     return useCallback(() => setValue(value => value + 1), []);
   }

// Map from task status to displayed text on button
const displayMap = {
    "unknown": "Unknown",
    "active": "Disable",
    "inactive": "Enable",
} as const

// Map from current task value to possible action*/
const actionMap = {
    "unknown": "info",
    "active": "disable",
    "inactive": "enable"
} as const

export const TaskManager: FC<{ websocket: WebSocket }> = ({ websocket }) => {
    const forceUpdate = useForceUpdate();
    const [tasks, setTasks] = useState<Tasks>({
        "Localization": "unknown",
        "Perception": "unknown",
        "Control": "unknown",
        "Navigation": "unknown",
    });

    useEffect(() => {
        if (websocket)
            websocket.addEventListener("message", (raw: MessageEvent<string>) => {
                const msg = tryJson(raw.data);
                if (msg && isData(msg) && msg.type == "tasks") {
                    const content = msg.content as Tasks;
                    const newTasks = Object.assign(tasks, content);
                    setTasks(newTasks);
                    forceUpdate();
                }
            });
    }, [websocket]);

    const manageTask = (taskName: keyof Tasks | undefined) => {
        let subcommand: "info" | "enable" | "disable";
        if (taskName)
            subcommand = actionMap[tasks[taskName]];
        else
            subcommand = "info"
        const request = {
            command: "tasks",
            content: {
                sub: subcommand,
                task: taskName,
            },
        }
        websocket.send(JSON.stringify(request));
    }

    return (
        <div>
            <h2>Task Manager</h2>
            <div className={styles.taskOuter}>
                <div className={styles.taskMiddle}>
                    <div className={styles.taskInner}>
                        <p>Localization</p>
                        <button onClick={() => manageTask("Localization")}>
                            {displayMap[tasks["Localization"]]}
                        </button>
                    </div>
                    <div className={styles.taskInner}>
                        <p>Perception</p>
                        <button onClick={() => manageTask("Perception") }>
                            {displayMap[tasks["Perception"]]}
                        </button>
                    </div>
                </div>
                <div className={styles.taskMiddle}>
                    <div className={styles.taskInner}>
                        <p>Control</p>
                        <button onClick={() => manageTask("Control") }>
                            {displayMap[tasks["Control"]]}
                        </button>
                    </div>
                    <div className={styles.taskInner}>
                        <p>Navigation</p>
                        <button onClick={() => manageTask("Navigation") }>
                            {displayMap[tasks["Navigation"]]}
                        </button>
                    </div>
                </div>
            </div>
            <div className={styles.taskInner}>
                <button className={styles.taskButton} onClick={() => manageTask(undefined)}>
                    Refresh <RestartSvg/>
                </button>
            </div>
        </div>
    )
}
