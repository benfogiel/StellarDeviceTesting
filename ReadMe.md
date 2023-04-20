# Stellar Device Testing Suite

This repository contains a comprehensive testing suite for Stellar devices, featuring a C++ simulated device program and a Python Qt GUI for communication and visualization. The C++ program simulates a test device that can send test data to connected clients through a UDP server. The Python Qt GUI enables users to communicate with multiple test devices simultaneously, sending requests to initiate and transmit test data. It also plots the received test data in real time and allows users to save the data in a PDF file.

## Usage: C++ Simulated Device

The simulated device program is located in the `device` directory.

1. Navigate to the `device` directory (i.e. `cd device`).
2. Run `make` to compile the program.
3. Run `./device <port>` to start the program. Optionally, you can specify the model and serial number of the device by running `./device <port> <model> <serial>`. The default model is `default_model`, and the default serial number is `1234`.

To simulate multiple devices, you can run multiple instances of the program on different ports (i.e. `./device 5000`, from another terminal: `./device 5001`, etc.).

## Usage: Python Communication and Visualization Program

Ensure you have a running simulated device (see 'Usage: C++ Simulated Device').

1. Install dependencies:

   - Install Qt5 from [here](https://wiki.qt.io/Install_Qt_5_on_Ubuntu). Ensure that `$QMAKE` is set to your `/qmake` file path.
   - From the root directory, run `pip install -r comm_program/requirements.txt`

   NOTE: If pip hangs during the installation of PyQt5, you may need to install it using the following command: `pip install pyqt5 --config-settings --confirm-license= --verbose`

2. Run the program. From the root directory, run `python3 -m comm_program.comm_program`.
3. Click `Add Device` and enter a name for the device.
4. Navigate to the `Connect` tab, input the IP address and port of the simulated device, and click `Connect`. If the connection is successful, the text at the top will change to `Connected to <device name> (<device serial number>)`.
5. Go to the `Test` tab, enter a test duration, and click `Run Test`. The test data will be plotted in real time, and the `Save` button will be enabled, allowing you to save the data to a PDF file.
