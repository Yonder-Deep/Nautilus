# Fake module for smbus when testing without a Raspberry Pi

class smbus():
    def SMBUS(bus):
        print("Fake SMBUS initiated")