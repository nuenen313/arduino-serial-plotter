import serial
import os
import csv
import numpy as np
import serial.tools.list_ports
import threading
from datetime import datetime

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

    def readDataLines(self, data_displayed_size=24000):
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
                        if size > data_displayed_size:
                            newDataRow = self.serialData.readlines(size)
                            newDataArray = np.array(newDataRow, dtype='object')
                            dataArray = np.hstack([dataArray, newDataArray])
                            return dataArray
                        else:
                            continue
            except Exception as e:
                self.serialData.close()
                self.portOpen = False
                return None, None
            finally:
                self.serialData.close()

class DataSaving:
    def __init__(self, data_queue, path):
        self.data_queue = data_queue
        self.path = path

    def save(self, filename):
        save_thread = threading.Thread(target=self._save_thread(filename=filename), daemon=True)
        save_thread.start()

    def _save_thread(self, filename):
        filepath = os.path.join(self.path, filename)
        if not os.path.isfile(filepath):
            with open(filepath, 'w', newline='') as f:
                f.close()
        with open(filepath, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Time','X', 'Y', 'Z'])
            decodedData = self.data_queue
            if decodedData:
                decodedData = decodedData[0]
                decodedData = decodedData[1:]
                x = np.array([], dtype=float)
                y = np.array([], dtype=float)
                z = np.array([], dtype=float)
                for j in decodedData:
                    numbers = np.array([float(num_str) for num_str in j.split(',')])
                    x = np.append(x, numbers[0])
                    y = np.append(y, numbers[1])
                    z = np.append(z, numbers[2])
                for i in range(len(z)):
                    timestamp2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    writer.writerow([timestamp2,x[i], y[i], z[i]])
        file.close()
