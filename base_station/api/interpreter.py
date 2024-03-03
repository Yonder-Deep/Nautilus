from static import constants


def decode_command(self_obj, header, line):
    remain = line & constants.INTERPRETER_TRUNC
    if header == constants.POSITION_DATA:
        no_fix = remain >> 58
        if no_fix:
            self_obj.out_q.put("set_auv_gps_status(\"No fix\")")
        else:
            lat_bits = remain >> 29
            long_bits = remain & 0x1FFFFFFF

            lat_sign = lat_bits >> 28
            long_sign = long_bits >> 28
            lat_val = lat_bits & 0xFFFFFFF
            long_val = long_bits & 0xFFFFFFF

            lat_wi = int(lat_val >> 20)
            long_wi = int(long_val >> 20)
            lat_di = int(lat_val & 0xFFFFF)
            long_di = int(long_val & 0xFFFFF)

            if lat_sign:
                lat_wi *= -1
            if long_sign:
                long_wi *= -1

            lat = str(lat_wi) + "." + str(lat_di)
            long = str(long_wi) + "." + str(long_di)

            self_obj.out_q.put("set_auv_gps_position(" + lat + ", " + long + ")")
            self_obj.out_q.put("set_auv_gps_status(\"Recieving data\")")
            print("Lat: " + lat + ", Long: " + long)

    elif header == constants.HEADING_DATA:
        data = remain & 0x1FFFF
        whole = data >> 7
        decimal = data & 0x7F
        decimal /= 100
        heading = whole + decimal
        print("HEADING", str(heading))
        self_obj.out_q.put("set_heading(" + str(heading) + ")")

    elif header == constants.MISC_DATA:
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

    elif header == constants.DEPTH_DATA:
        data = remain & 0x7FF
        whole = data >> 4
        decimal = float(data & 0xF)
        depth = whole + decimal/10
        print("Depth: ", depth)

        self_obj.out_q.put("set_depth(" + str(depth) + ")")

    elif header == constants.CALIBRATION_DATA:
        data = line & ((1 << 59) - 1)

        def decode_data(data, *lengths):
            decoded = []
            for length in reversed(lengths):
                decoded.append(data & (1 << length) - 1)
                data >>= length
            return tuple(reversed(decoded))

        (sign_heading, whole_heading, decimal_heading,
         sign_roll, whole_roll, decimal_roll,
         sign_pitch, whole_pitch, decimal_pitch,
         system, gyro, accel, mag) = decode_data(data, 1, 9, 7, 1, 9, 7, 1, 9, 7, 2, 2, 2, 2)

        def join_decimal(sign, whole, decimal, digits=2):
            sign_multiplier = -1 if sign else 1
            num = sign_multiplier * whole + decimal / (10 ** digits)
            return num

        heading = join_decimal(sign_heading, whole_heading, decimal_heading)
        roll = join_decimal(sign_roll, whole_roll, decimal_roll)
        pitch = join_decimal(sign_pitch, whole_pitch, decimal_pitch)

        output = 'Heading={0:0.2F} Roll={1:0.2F} Pitch={2:0.2F}\tSys_cal={3} Gyro_cal={4} Accel_cal={5} Mag_cal={6}'.format(
            heading, roll, pitch, system, gyro, accel, mag)

        self_obj.out_q.put("log('" + output + "'")
