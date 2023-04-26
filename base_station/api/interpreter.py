# Encoding headers
POSITION_DATA = 0b000
HEADING_DATA = 0b001
COMBINATION_DATA = 0b010
DEPTH_DATA = 0b011


def decode_command(self_obj, header, line):
    remain = line & 0x1FFFFFFFFFFFFF
    if header == POSITION_DATA:
        no_fix = remain >> 52
        if no_fix:
            self_obj.out_q.put("set_auv_gps_status(\"No fix\")")
        else:
            lat_bits = remain >> 26
            long_bits = remain & 0x3FFFFFF

            lat_sign = lat_bits >> 25
            long_sign = long_bits >> 25

            lat_wi = int(lat_bits >> 17)
            long_wi = int(long_bits >> 17)
            lat_di = int(lat_bits & 0x1FFFF)
            long_di = int(long_bits & 0x1FFFF)

            if lat_sign:
                lat_wi *= -1
            if long_sign:
                long_wi *= -1

            lat = str(lat_wi) + "." + str(lat_di)
            long = str(long_wi) + "." + str(long_di)

            self_obj.out_q.put("set_auv_gps_position(" + lat + ", " + long + ")")
            self_obj.out_q.put("set_auv_gps_status(\"Recieving data\")")

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
