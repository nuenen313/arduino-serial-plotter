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
                        if size > 12000: #twice the selected adxl355 odr
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

class DataSaving:
    def __init__(self, data_queue, path):
        self.data_queue = data_queue
        self.path = path

    def save(self):
        save_thread = threading.Thread(target=self._save_thread, daemon=True)
        save_thread.start()

    def _save_thread(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_{timestamp}.csv"
        filepath = os.path.join(self.path, filename)
        with open(filepath, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['X', 'Y', 'Z'])
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
                    writer.writerow([x[i], y[i], z[i]])
            print(f'Saved to {filepath}')
        file.close()

    def combineFiles(self):
        combineThread = threading.Thread(target=self._combine_thread, daemon=True)
        combineThread.start()

    def _combine_thread(self):
        files = os.listdir(self.path)
        if 'combined' in files:
            files.pop(files.index('combined'))
            combined_files_dir = os.path.join(self.path, 'combined')
            combined_files = os.listdir(combined_files_dir)
            if "combined_twice" in combined_files:
                combined_files.pop(combined_files.index("combined_twice"))
            combined_files_number = len(combined_files)
            uber_comb_directory = os.path.join(combined_files_dir, "combined_twice")
            if not os.path.isdir(uber_comb_directory):
                os.mkdir(uber_comb_directory)
            if combined_files_number > 100:
                print(combined_files_number)
                timestamp0 = datetime.now().strftime("%Y%m%d_%H%M%S")
                combined_twice_file_name = f"combined_twice_data_{timestamp0}.csv"
                combined_twice_file_path = os.path.join(uber_comb_directory, combined_twice_file_name)
                with open(combined_twice_file_path, 'w', newline='') as combined_twice_file:
                    writer_comb = csv.writer(combined_twice_file)
                    writer_comb.writerow(['X', 'Y', 'Z'])
                    for comb_file in combined_files:
                        comb_file_path = os.path.join(combined_files_dir, comb_file)
                        if os.path.isfile(comb_file_path):
                            with open(comb_file_path, 'r') as cf:
                                reader_comb = csv.reader(cf)
                                next(reader_comb)
                                next(reader_comb)
                                for row_comb in reader_comb:
                                    writer_comb.writerow(row_comb)
                            os.remove(comb_file_path)

        files_number = len(files)
        if files_number > 99:
            print(files_number)
            combined_files_dir = os.path.join(self.path, 'combined')
            if not os.path.isdir(combined_files_dir):
                os.mkdir(combined_files_dir)
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                first_file_timestamp = datetime.fromtimestamp(os.path.getmtime(os.path.join(self.path, files[0]))).strftime("%Y%m%d_%H%M%S")
                combinedfile_name = f"combined_data_{timestamp}.csv"
                combinedfile_path = os.path.join(combined_files_dir, combinedfile_name)
                with open(combinedfile_path, 'w', newline='') as combined_file:
                    writer = csv.writer(combined_file)
                    writer.writerow([f'Combining 100 files, starting from file saved at: {first_file_timestamp}'])
                    writer.writerow(['X', 'Y', 'Z'])
                    for file in files:
                        file_path = os.path.join(self.path, file)
                        if os.path.isfile(file_path):
                            with open(file_path, 'r') as f:
                                reader = csv.reader(f)
                                next(reader)
                                for row in reader:
                                    writer.writerow(row)
                            os.remove(file_path)
                combined_file.close()
