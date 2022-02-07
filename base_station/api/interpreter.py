# Encoding headers
POSITION_DATA = 0b000
HEADING_DATA = 0b001
COMBINATION_DATA = 0b010
DEPTH_DATA = 0b011


def decode_command(self_obj, header, line):
    remain = line & 0x1FFFFF
    if header == POSITION_DATA:
        data = remain & 0x7FFFF
        x = data >> 10
        x_sign = (x & 0x200) >> 9
        y = data & 0x1FF
        y_sign = (y & 0x200) >> 9

        x &= 0x1FF
        y &= 0x1FF

        x = -x if x_sign else x
        y = -y if y_sign else y

        self_obj.out_q.put("set_position(" + str(int(x)) + ", " + str(int(y)) + ")")
    elif header == HEADING_DATA:
        data = remain & 0x1FFFF
        whole = data >> 7
        decimal = data & 0x7F
        decimal /= 100
        heading = whole + decimal
        print("HEADING", str(heading))
        self_obj.out_q.put("set_heading(" + str(heading) + ")")
    elif header == COMBINATION_DATA:
        data = remain & 0xFFFFF
        battery = data >> 14  # bits 14-20
        temp_sign = (data >> 13) & 0x1  # bit 13
        temp_mag = (data >> 7) & 0x3F  # bits 7-12
        # Combine temp data
        temp = (temp_mag * -1) if (temp_sign == 1) else temp_mag
        mvmt = (data >> 3) & 0x7  # bits 4-6
        mission_stat = (data >> 1) & 0x3  # bits 2-3
        flooded = data & 0x1  # bit 1
        # TODO: Update gui
        print("Battery: " + str(int(battery)))
        self_obj.out_q.put("set_temperature(" + str(temp) + ")")
        print("Movement status: " + str(int(mvmt)))
        print("Mission status: " + str(int(mission_stat)))
        print("Flooded: " + str(int(flooded)))

        self_obj.out_q.put("set_battery_voltage(" + str(battery) + ")")
        self_obj.out_q.put("set_flooded(" + str(flooded) + ")")
        self_obj.out_q.put("set_movement(" + str(mvmt) + ")")
        self_obj.out_q.put("set_mission_status(" + str(battery) + ")")

    elif header == DEPTH_DATA:
        data = remain & 0x7FF
        whole = data >> 4
        decimal = float(data & 0xF)
        depth = whole + decimal/10
        print("Depth: ", depth)

        self_obj.out_q.put("set_depth(" + str(depth) + ")")

        #         self.in_q.put(message)
