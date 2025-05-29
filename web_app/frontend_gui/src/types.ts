export interface Command {
    command: string
    content: any
    ack?: boolean
}

export const isCommand = (obj: any): obj is Command => {
    return (
        typeof obj === 'object' &&
        obj !== null &&
        typeof obj.command === 'string' &&
        typeof obj.content === 'number'
    )
}

export interface State {
    position: number[]
    velocity: number[]
    //local_velocity: number[]
    local_force: number[]
    attitude: number[]
    angular_velocity: number[]
    local_torque: number[]
    //forward_m_input: number
    //turn_m_input: number
}

const isNumberArray = (value: any): value is number[] => {
    return Array.isArray(value) && value.every((item) => typeof item === "number");
}

export const isState = (obj: any): obj is State => {
    return (
        typeof obj === 'object' &&
        obj !== null &&
        isNumberArray(obj.position) &&
        isNumberArray(obj.velocity) &&
        //isNumberArray(obj.local_velocity) &&
        //isNumberArray(obj.local_force) &&
        isNumberArray(obj.attitude) &&
        isNumberArray(obj.angular_velocity) //&&
        //isNumberArray(obj.local_torque)// &&
        //typeof obj.forward_m_input === 'number' &&
        //typeof obj.turn_m_input === 'number'
    )
}

export interface Data {
    source: string
    type: string
    content: State | string
} 

export const isData = (obj: any): obj is Data => {
    return (
        typeof obj === 'object' &&
        obj !== null &&
        typeof obj.source === 'string' &&
        typeof obj.type === 'string' &&
        (isState(obj.content) || typeof obj.content === 'string')
    )
}
