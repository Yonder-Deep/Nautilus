import React, { useEffect, useState, useRef } from "react";
import { ParametersForm, MotorTestForm, HeadingTestForm } from "./components/Forms.jsx";

const Graph = () => {
    return (
        <div className="graph">
            <h3>Graph Placeholder</h3>
        </div>
    )
}

const StatusItem = ({ statusType, statusData }) => {
    const statusListItems = statusData.map(dataPart =>
        <li key={dataPart.id}>{dataPart.title}: {dataPart.value}</li>
    )

    return (
        <div className="status-item">
            <h2>{statusType}</h2>
            <ul>{statusListItems}</ul>
        </div>
    )
}

export default function Tests() {
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

    // Handle all POST requests to set PID or run tests
    const handlePostRequest = async (url, data) => {
        console.log("Attempting post of data: " + JSON.stringify(data));
        try {
            const response = await fetch("http://localhost:6543/api/" + url, {
                method: 'POST',
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });
            console.log(response.data);
        } catch (error) {
            console.error('Error posting data:', error);
        }
    };

    // Register socket handlers for server-sent data
    const connection = useRef(null);
    useEffect(() => {
        /*const socket = new WebSocket(window.location.host + "/api/");

        socket.addEventListener("imuData", handleImuData);
        socket.addEventListener("insData", handleInsData);

        connection.current = socket;

        return () => connection.close();*/

        // Fetch polling with http requests every second
        const pollInterval = 1000;
        const dataPoll = setInterval(() => {
            const fetchData = async () => {
                const imuResponse = await fetch("http://localhost:6543/api/imu_calibration_data");
                const imuBody = await imuResponse.json();
                setImuData([
                    { title: 'Magnetometer', value: imuBody.magnetometer, id: 1 },
                    { title: 'Accelerometer', value: imuBody.accelerometer, id: 2 },
                    { title: 'Gyroscope', value: imuBody.gyroscope, id: 3 }
                ]);
                const insResponse = await fetch("http://localhost:6543/api/ins_data");
                const insBody = await insResponse.json();
                setInsData([
                    { title: 'Heading', value: insBody.heading, id: 1 },
                    { title: 'Roll', value: insBody.roll, id: 2 },
                    { title: 'Pitch', value: insBody.pitch, id: 3 }
                ]);
            }
            fetchData();
        }, pollInterval);

        return () => clearInterval(dataPoll);
    }, [useState]);

    return (
        <>
            <h1>Testing and Calibration</h1>
            <div className="upper-section">
                <div>
                    <Graph></Graph>
                </div>
                <div>
                    <Graph></Graph>
                </div>
                <div>
                    <Graph></Graph>
                </div>
            </div>
            <div className="lower-section">
                <div className="status-section">
                    <StatusItem statusType="IMU Status" statusData={imuData}></StatusItem>
                    <StatusItem statusType="INS Status" statusData={insData}></StatusItem>
                </div>
                <div className="testing-section">
                    <ParametersForm handlePostRequest={handlePostRequest}></ParametersForm>
                    <MotorTestForm handlePostRequest={handlePostRequest}></MotorTestForm>
                    <HeadingTestForm handlePostRequest={handlePostRequest}></HeadingTestForm>
                </div>
            </div>
        </>
    );
}
