import serial
import numpy as np
import serial.tools.list_ports

class PortReader:
    def readAvailablePorts():
        ports = serial.tools.list_ports.comports()
        portList = []
        for port, desc, hwind in sorted(ports):
            portList.append("{}: {} [{}]".format(port, desc, hwind))
        return portList

class ReadPortData:
    def __init__(self, port, baud):
        self.buf = bytearray()
        self.port = port
        self.baud = baud
        self.serialData = None

    def closePort(self):
        if self.serialData is not None:
            self.serialData.close()

    def readDataLines(self):
        try:
            self.serialData = serial.Serial(self.port, self.baud)
        except serial.SerialException:
            return EnvironmentError("Serial port can't be reached")

        dataArray = np.empty((0,), dtype=object)

        if self.serialData:
            try:
                self.serialData.close()
                self.serialData.open()
                if self.serialData.is_open:
                    self.portOpen = True
                    while self.portOpen == True:
                        size = self.serialData.in_waiting
                        if size > 8000: #twice the selected adxl355 odr
                            newDataRow = self.serialData.readlines(size)
                            newDataArray = np.array(newDataRow, dtype='object')
                            dataArray = np.hstack([dataArray, newDataArray])
                            return dataArray
                        else:
                            continue
            except Exception as e:
                self.serialData.close()
                self.portOpen = False
                return None
            finally:
                self.serialData.close()
