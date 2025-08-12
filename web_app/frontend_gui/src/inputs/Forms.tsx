import React, { useState, useEffect, FC } from 'react';
import styles from "./forms.module.css"

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
            command: "pid",
            content: pidConstants
        };
        websocket.send(JSON.stringify(request));
    }

    return (
        <div>
            <h2>Set PID Constants</h2>
            <div className={styles.formBody}>
                <div className={styles.parameterForm}>
                    <select 
                        defaultValue={"Default"} 
                        onChange={e => setPidAxis(e.target.value)}
                    >
                        <option value="Default" disabled>Select Axis</option>
                        <option value="surge">Surge</option>
                        <option value="sway">Sway</option>
                        <option value="heave">Heave</option>
                        <option value="roll">Pitch</option>
                        <option value="pitch">Yaw</option>
                        <option value="yaw">Roll</option>
                    </select>
                    <input 
                        placeholder="P"
                        value={constantP}
                        onChange={e => setConstantP(e.target.value)}
                    />
                    <input 
                        placeholder="I"
                        value={constantI}
                        onChange={e => setConstantI(e.target.value)}
                    />
                    <input 
                        placeholder="D"
                        value={constantD}
                        onChange={e => setConstantD(e.target.value)}
                    />
                </div>
                <button onClick={() => makePidRequest()}>Set Constants</button>
            </div>
        </div>
    )
}

export const MotorTestForm = ({ websocket }: any) => {
    const [motor1, setMotor1] = useState<string>("0");
    const [motor2, setMotor2] = useState<string>("0");
    const [motor3, setMotor3] = useState<string>("0");
    const [motor4, setMotor4] = useState<string>("0");

    const makeMotorRequest = (arr: number[] | undefined = undefined) => {
        console.log("Making motor request.")
        let motorTest = []
        try {
            if (arr) motorTest = arr;
            else motorTest = [
                parseFloat(motor1),
                parseFloat(motor2),
                parseFloat(motor3),
                parseFloat(motor4),
            ];
        } catch {
            return
        }
        const request = {
            command: "motor",
            content: motorTest
        };
        websocket.send(JSON.stringify(request));
    }

    const zeroOut = () => {
        setMotor1("0");
        setMotor2("0");
        setMotor3("0");
        setMotor4("0");
        makeMotorRequest([0,0,0,0]);
    }

    const [keymap, setKeymap] = useState<boolean>(false);

    return (
        <div>
            <h2>Motor Testing</h2>
            <div className={styles.formBody}>
                <div className={styles.motorForm}>
                    <input
                        placeholder="↑" 
                        value={motor1}
                        onChange={e => setMotor1(e.target.value)}
                    />
                    <input
                        placeholder="↻"
                        value={motor2}
                        onChange={e => setMotor2(e.target.value)}
                    />
                    <input
                        placeholder="⇅"
                        value={motor3}
                        onChange={e => setMotor3(e.target.value)}
                    />
                    <input
                        placeholder="⇅"
                        value={motor4}
                        onChange={e => setMotor4(e.target.value)}
                    />
                </div>
                <div className={styles.motorForm}>
                    <button onClick={() => makeMotorRequest()}>Set Speeds</button>
                    <button onClick={() => zeroOut()}>Zero All</button>
                    <button onClick={() => setKeymap(!keymap)}>K</button>
                </div>
            </div>
        </div>
    )
}

export const HeadingTestForm = ({ websocket }: any) => {
    const [targetHeading, setTargetHeading] = useState('');
    const headingRequest = () => {
        console.log("Making heading request.")
        const request = {
            command: "control",
            content: targetHeading
        };
        websocket.send(JSON.stringify(request));
    }

    return (
        <div className="testing-form">
            <h2>Heading Test</h2>
            <div className={styles.formBody}>
                <input
                    placeholder="Enter target heading"
                    value={targetHeading}
                    onChange={e => (setTargetHeading(e.target.value))}
                />
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
        <div className={styles.formBody}>
            <input
                placeholder="Enter target point: (x,y,0)"
                value={targetPoint}
                onChange={e => (setTargetPoint(e.target.value))}
                />
            <button onClick={() => missionRequest()}>Start Mission</button>
        </div>
    </div>
    )
}
