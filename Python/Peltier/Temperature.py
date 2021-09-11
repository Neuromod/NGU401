import serial
import numpy


class Temperature:
    #To avoid a reset of the ESP32, DTR and RTS are set to low. In this way the the ESP32 JTAG debugging is not interrupted
    def __init__(self, port, baudRate = 115_200, dataBits = 8, parity = 'N', stopBits = 1):
        self._uart = serial.Serial(None, baudrate = baudRate, bytesize = dataBits, parity = parity, stopbits = stopBits, dsrdtr = False, rtscts = False, timeout = 0)
        self._uart.port = port
        self._uart.dtr = False
        self._uart.rts = False
        self._uart.open()
        self._synced = False
        self._buffer = ''

    
    def read(self):
        measurements = []

        if self._uart.in_waiting > 0:
            self._buffer += self._uart.read(self._uart.in_waiting).decode('ascii')

            if not self._synced:
                idx = self._buffer.find('\n')
                
                if idx != -1:
                    self._buffer = self._buffer[idx + 1:]
                    self._synced = True

            if self._synced:
                idx = self._buffer.rfind('\n')

                if idx != -1:
                    measurements = [float(x) for x in self._buffer[0 : idx].split()]
                    self._buffer = self._buffer[idx:]

        return measurements
