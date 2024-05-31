import os
import csv
from datetime import datetime
from serial_com_helper import ReadPortData
import queue

def main_temp(port, path):
    data_queue = queue.Queue()
    read_temp = ReadPortData(port, 115200)
    temp_filename = os.path.join(path, 'temperature_data.csv')
    if not os.path.isfile(temp_filename):
        with open(temp_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Temperature'])
    data = read_temp.readDataLines(size2=1)
    print(data)
    if data is not None and not isinstance(data, OSError):
        for line in data:
            data_queue.put(line)
    decodedData = []
    while not data_queue.empty():
        decodedData.append(data_queue.get().decode('utf-8').strip())

    with open(temp_filename, mode='a', newline='') as f:
        writer = csv.writer(f)
        for temp in decodedData:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([timestamp, temp])
            print(f"Saved {temp} to {temp_filename} at {timestamp}")

if __name__ == '__main__':
    port = 'COM11'
    path = 'D:/Marta'
    while True:
        main_temp(port, path)
