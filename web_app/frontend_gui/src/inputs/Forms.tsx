import React, { useState } from 'react';

export const ParametersForm = ({ websocket }: any) => {
    const [pidAxis, setPidAxis] = useState('');
    const [constantP, setConstantP] = useState('');
    const [constantI, setConstantI] = useState('');
    const [constantD, setConstantD] = useState('');
    const makePidRequest = () => {
        if (!pidAxis || !constantP || !constantI || !constantD) { return; }
        const pidConstants = {
            axis: '' + pidAxis,
            p: '' + constantP,
            i: '' + constantI,
            d: '' + constantD
        };
        const request = {
            command: "pidConstants",
            content: pidConstants
        };
        websocket.send(JSON.stringify(request));
    }

    return (
        <div className="parameters-form">
            <h2>Set PID Constants</h2>
            <div className="form-body">
                <select defaultValue={"Default"} onChange={e => setPidAxis(e.target.value)}>
                    <option value="Default" disabled>Select Axis</option>
                    <option value="Pitch">Pitch</option>
                    <option value="Yaw">Yaw</option>
                    <option value="Roll">Roll</option>
                </select>
                <input placeholder="P" onChange={e => setConstantP(e.target.value)} />
                <input placeholder="I" onChange={e => setConstantI(e.target.value)} />
                <input placeholder="D" onChange={e => setConstantD(e.target.value)} />
                <button onClick={() => makePidRequest()}>Set Constants</button>
            </div>
        </div>
    )
}

export const MotorTestForm = ({ websocket }: any) => {
    const [motorType, setMotorType] = useState('');
    const [motorSpeed, setMotorSpeed] = useState('');
    const [motorDuration, setMotorDuration] = useState('');

    const [motor1, setMotor1] = useState<number>();
    const [motor2, setMotor2] = useState<number>();
    const [motor3, setMotor3] = useState<number>();
    const [motor4, setMotor4] = useState<number>();

    const makeMotorRequest = () => {
        console.log("Making motor request.")
        const motorTest = [
            motor1,
            motor2,
            motor3,
            motor4,
        ];
        const request = {
            command: "motorTest",
            content: motorTest
        };
        websocket.send(JSON.stringify(request));
    }

    return (
        <div className="motor-form">
            <h2>Motor Testing</h2>
            <div className="form-body">
                <input placeholder="Enter motor 1 speed" onChange={e => setMotor1(parseFloat(e.target.value))} />
                <input placeholder="Enter motor 2 speed" onChange={e => setMotor2(parseFloat(e.target.value))} />
                <input placeholder="Enter motor 3 speed" onChange={e => setMotor3(parseFloat(e.target.value))} />
                <input placeholder="Enter motor 4 speed" onChange={e => setMotor4(parseFloat(e.target.value))} />
                <button onClick={() => makeMotorRequest()}>Begin Test</button>
            </div>
        </div>
    )
}

export const HeadingTestForm = ({ websocket }: any) => {
    const [targetHeading, setTargetHeading] = useState('');
    const headingRequest = () => {
        console.log("Making heading request.")
        const request = {
            command: "headingTest",
            content: targetHeading
        };
        websocket.send(JSON.stringify(request));
    }

    return (
        <div className="testing-form">
            <h2>Heading Test</h2>
            <div className="form-body">
                <input placeholder="Enter target heading" onChange={e => (setTargetHeading(e.target.value))} />
                <button onClick={() => headingRequest()}>Begin Test</button>
            </div>
        </div>
    )
}

export const StartMission = ({ websocket }: any) => {
    const [targetPoint, setTargetPoint] = useState('');
    const missionRequest = () => {
        websocket.send(JSON.stringify({
            command: "mission",
            content: targetPoint
        }))
    }

    return (
    <div className="testing-form">
        <h2>Start Mission</h2>
        <div className="form-body">
            <input placeholder="Enter target point: (x,y,0)" onChange={e => (setTargetPoint(e.target.value))} />
            <button onClick={() => missionRequest()}>Start Mission</button>
        </div>
    </div>
    )
}
