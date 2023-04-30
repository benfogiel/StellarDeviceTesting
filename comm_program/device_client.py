"""A client class that connects and communicates with a test device."""

import socket
import select


class DeviceClient:
    """
    A client class that connects and communicates with a test device.

    Attributes:
        host (str): The host name of the server.
        port (int): The port number of the server.
    """

    def __init__(self, ip: str, port: int) -> None:
        """
        The constructor for DeviceClient class.

        Args:
            ip (str): The IP of the server.
            port (int): The port number of the server.
        """
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)  # don't clog the pipes!

        self.device_model = None
        self.device_serial_num = None

    def send_msg(self, msg: str) -> None:
        """
        Sends a message to the server.

        Args:
            msg (str): The message to send.
        """
        message_bytes = msg.encode("ISO-8859-1")
        try:
            self.sock.sendto(message_bytes, (self.ip, self.port))
        except socket.error as err:
            print(f"Error sending message: {err}")

    def receive_msg(self, buffer_size: int = 1024, timeout: int = 1) -> dict:
        """
        Receives a message from the server.

        Args:
            buffer_size (int): The size of the buffer to receive the message.
            timeout (int): The timeout in seconds to wait for a message.

        Returns:
            dict: A dictionary containing the message type and the message parameters.
                If an error occurs during message retrieval or the message is invalid,
                returns empty dictionary.
        """
        ready_to_read, _, _ = select.select([self.sock], [], [], timeout)
        if not ready_to_read:
            print("Receive timed out.")
            return {}
        try:
            data, _ = self.sock.recvfrom(buffer_size)
            msg = data.decode("ISO-8859-1")
            print("Received Message: ", msg)
            msg = msg.split(";")
            if len(msg) < 2:
                print("Invalid message received.")
                return (
                    {}
                )  # invalid message. Message should be terminated with a semicolon.
            parsed_msg = {m.split("=")[0]: m.split("=")[1] for m in msg if "=" in m}
            parsed_msg["TYPE"] = msg[0]
            return parsed_msg
        except socket.error as err:
            print(f"Error receiving message: {err}")
            return {}

    def discover(self) -> tuple:
        """
        Sends a discovery message to the server.

        Returns:
            tuple: A tuple containing the model and serial number of the device.
                If the device is not found, returns None.
        """
        self.send_msg("ID;")
        discover_resp = self.receive_msg()
        if discover_resp and discover_resp.get("TYPE") == "ID":
            self.device_model = discover_resp["MODEL"]
            self.device_serial_num = discover_resp["SERIAL"]
            return discover_resp["MODEL"], discover_resp["SERIAL"]
        # invalid discover response
        print("Invalid discover response from server.")
        return None

    def disconnect(self) -> None:
        """
        Clears the device model and serial number and closes the socket.
        """
        self.device_model = None
        self.device_serial_num = None
        self.sock.close()

    def start_test(self, duration: int, rate: int) -> tuple[int, str]:
        """
        Sends a start test command to the server.

        Args:
            duration (int): The duration of the test in seconds.
            rate (int): The desired test status report rate in ms.

        Returns:
            tuple: A tuple containing the result code and a message describing the result.
        """
        self.send_msg(f"TEST;CMD=START;DURATION={duration};RATE={rate};")
        resp = self.receive_msg()
        if resp and resp.get("TYPE") == "TEST":
            if resp.get("RESULT") == "STARTED":
                return 0, "Test successfully started."
            if resp.get("RESULT") == "ERROR1":
                # ERROR1 - client tried to start a test on a device that is currently running a test
                return 1, resp["MSG"]
        return -1, "Invalid response from server."

    def stop_test(self) -> tuple[int, str]:
        """
        Sends a stop test command to the server.

        Returns:
            tuple: A tuple containing the result code and a message describing the result.
        """
        self.send_msg("TEST;CMD=STOP;")
        while True:
            stop_resp = self.receive_msg()
            if stop_resp and stop_resp.get("TYPE") == "TEST":
                if stop_resp.get("RESULT") == "STOPPED":
                    # Get IDLE message
                    idle_resp = self.receive_msg()
                    if idle_resp and idle_resp.get("TYPE") == "STATUS":
                        return 0, "Test successfully stopped."
                elif stop_resp.get("RESULT") == "ERROR2":
                    # ERROR2 - client tried to stop a test on a device that is not running a test
                    return 2, stop_resp["MSG"]
            elif stop_resp and stop_resp.get("TYPE") == "STATUS":
                if stop_resp.get("STATE") == "IDLE":
                    # received IDLE message first
                    # get STOPPED Message
                    stop_msg = self.receive_msg()
                    if (
                        stop_msg
                        and stop_msg.get("TYPE") == "TEST"
                        and stop_msg.get("RESULT") == "STOPPED"
                    ):
                        return 0, "Test successfully stopped."
                else:
                    # received test status message, get next message
                    continue
            print("Invalid response from server: ", stop_resp)
            return -1, "Invalid response from server."

    def get_status(self) -> dict:
        """
        Receives a status message from the server.

        Returns:
            dict: A dictionary containing the device status and message:
                - If status = IDLE, message = "No test running."
                - If status = TESTING, message = time, voltage, and current values.
                - if status is neither, returns None.
        """
        msg = self.receive_msg()
        if msg and msg.get("TYPE") == "STATUS":
            if msg.get("STATE") == "IDLE":
                print("Test has ended.")
                return {"state": "IDLE", "msg": "No test running."}
            return {"state": "TESTING", "msg": (msg["TIME"], msg["MV"], msg["MA"])}
        return None
