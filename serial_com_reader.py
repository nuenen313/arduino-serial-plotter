import sys
import os
import serial
import glob
import numpy as np
import serial.tools.list_ports
from collections import deque
from threading import Thread, Lock

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
    def readDataLines(self):
        try:
            serialData = serial.Serial(self.port, self.baud)
        except serial.SerialException:
            return EnvironmentError("Serial port can't be reached")
      
        dataArray = np.empty((0,), dtype=object)

        if serialData:
            try:
                serialData.close()
                serialData.open()
                if serialData.is_open:
                    portOpen = True
                    while portOpen == True:
                        size = serialData.in_waiting
                        if size:
                            newDataRow = serialData.readlines(size)
                            newDataArray = np.array(newDataRow, dtype='object')
                            dataArray = np.hstack([dataArray, newDataArray])
                        else:
                            continue
                return dataArray
            except KeyboardInterrupt:
                serialData.close()
                print('Interrupted')
                portOpen = False
                return dataArray
            except Exception as e:
                serialData.close()
                print(f"An error occurred: {e}")
                return None
            finally:
                serialData.close()