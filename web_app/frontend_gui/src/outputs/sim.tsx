import { useRef, useState, useEffect } from "react";
import {
    Canvas,
    useFrame
} from "@react-three/fiber"
import * as THREE from "three"

THREE.Object3D.DEFAULT_UP.set(0, 0, 1);

const Mesh = ({quat}: {quat: number[]}) => {
    const quaternion = new THREE.Quaternion()
    let meshRef = useRef<THREE.Mesh>(null!);
    const [attitude, setAttitude] = useState<THREE.Quaternion>(null!);

    useEffect(() => {
        const tempQuat: any = [...quat];
        const last: number | undefined = tempQuat.pop();
        tempQuat.unshift(last);
        setAttitude(quaternion.fromArray(tempQuat))
    },[quat])

    useFrame(() => {
        meshRef.current.rotation.setFromQuaternion(attitude);
    })

    return (
        <mesh ref={meshRef}>
            <boxGeometry args={[2,2,4]}/>
            <meshStandardMaterial />
        </mesh>
    )
}

export const Simulation = ({quat}: {quat: number[]}) => {

    return (
        <>
            <h2>Visualization</h2>
            <Canvas frameloop="demand" camera={{rotation: [0, -0.25, Math.PI/2] ,position: [-2,0,6]}}>
                <Mesh quat={quat}></Mesh>
                <ambientLight intensity={0.1} />
                <directionalLight position={[0, 0, 5]} color="red" />
                <axesHelper position={[2, 0, 0]}/>
            </Canvas>
        </>
    )
}
