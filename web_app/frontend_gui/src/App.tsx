import React, { useEffect, useState, useRef } from "react";
import { Layouts } from "react-grid-layout";

import {
    ParametersForm,
    MotorTestForm,
    HeadingTestForm,
    StartMission,
} from "./inputs/Forms";
import { SocketHealth } from "./inputs/SocketHealth"
import { TaskManager} from "./inputs/TaskManager";
import { StatusItem, StatusMessages } from "./outputs/status";
import { Simulation } from "./outputs/sim";
import { Map } from "./outputs/map"
import { VideoStream } from "./outputs/video"
import {
    Command,
    isCommand,
    State,
    isState,
    Data,
    isData
} from "./types"
import { Grid } from "./Grid";
import { GridSvg } from "./utils/icons";

const tryJson = (raw: string): any => {
    try {
        return JSON.parse(raw)
    }
    catch {
        return undefined
    }
}

export default function App() {
    // These are the only state variables that need full scope
    const [imuData, setImuData] = useState([
        { title: 'Magnetometer', value: '', id: 1 },
        { title: 'Accelerometer', value: '', id: 2 },
        { title: 'Gyroscope', value: '', id: 3 }
    ]);
    const [insData, setInsData] = useState([
        { title: 'Heading', value: '', id: 1 },
        { title: 'Roll', value: '', id: 2 },
        { title: 'Pitch', value: '', id: 3 }
    ]);
    const [websocket, setWebsocket]: any = useState();
	const [statusMessages, setStatusMessages]: any = useState([]);
    const [attitude, setAttitude] = useState<number[]>([0,0,0]);

    const handleSocketData = (event: MessageEvent<string>) => {
        console.log("Socket data arrived: " + event.data);
        const data: Command | Data = tryJson(event.data)
        if (isData(data) && data.type == "state" && isState(data.content)) {
            setAttitude(data.content.attitude)
        } else {
            setStatusMessages((prev: any)  => [...prev, event.data]);
        }
    }

    // Register socket handler for server-sent data
    const connection: any = useRef(null);
    useEffect(() => {
        const socket: WebSocket = new WebSocket("ws://localhost:6543/api/websocket");

        socket.addEventListener("open", () => setWebsocket(socket));
        socket.addEventListener("message", handleSocketData);

        connection.current = socket;

        return () => connection.current.close();
    }, [useState]);

    // Grid Layout Section
    const [gridEnabled, setGridEnabled] = useState<boolean>(false);
    const [layouts, setLayouts] = useState<Layouts>();
    // On load try to get saved layout
    useEffect(() => {
        const fetchLayout = async () => {
            const response = await fetch("http://" + window.location.host + "/api/layouts");
            const initialLayout: Layouts = await response.json();
            setLayouts(initialLayout);
        }
        fetchLayout();
    }, []);
    // Save layouts at server
    const saveLayout = () => {
        fetch("http://" + window.location.host + "/api/layouts", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(layouts)
        });
    }

    return (
        <div className = "parent-container">
            <h1>Yonder Deep Nautilus Dashboard</h1>
            <div className="top-right-buttons">
                <button onClick={() => saveLayout()}>Save <GridSvg /></button>
                <button onClick={() => setGridEnabled(!gridEnabled)}
                        style={{"color": gridEnabled ? "#ff0000" : "#00ff00"}}
                >
                    {gridEnabled ? "Disable" : "Enable"}
                    {gridEnabled ? (<GridSvg color={"#ff0000"} />)
                                 : (<GridSvg color={"#00ff00"} />)
                    }
                </button>
            </div>
            <Grid enabled={gridEnabled} layouts={layouts} setLayouts={setLayouts}>
                <Simulation euler={attitude}></Simulation>
                <Map coordinates={[]}></Map>
                <StatusItem statusType="IMU Status" statusData={imuData}></StatusItem>
                <StatusItem statusType="INS Status" statusData={insData}></StatusItem>
                <ParametersForm websocket={websocket}></ParametersForm>
                <MotorTestForm websocket={websocket}></MotorTestForm>
                <HeadingTestForm websocket={websocket}></HeadingTestForm>
                <StartMission websocket={websocket}></StartMission>
                <StatusMessages statusMessages={statusMessages} setStatusMessages={ setStatusMessages}></StatusMessages>
                <SocketHealth websocket={websocket}></SocketHealth>
                <TaskManager websocket={websocket} />
                <VideoStream />
            </Grid>
        </div>
    );
}
