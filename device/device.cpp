// Required libraries
#include <iostream>
#include <string>
#include <sstream>
#include <map>
#include <thread>
#include <chrono>
#include <unistd.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <atomic>

// Device class represents a simulated device with a model, serial number, and idle state.
class Device
{
public:
    // Constructor: initializes the device with the given model and serial number
    Device(std::string model, int serial_number)
        : model_(model), serial_number_(serial_number) {}

    // Member variables
    std::string model_;
    int serial_number_;
    bool is_idle_ = true;

    // Accessor functions
    std::string get_model() const { return this->model_; }
    int get_serial_number() const { return this->serial_number_; }
    bool get_is_idle() const { return this->is_idle_; }

    // Mutator functions
    void set_is_idle(bool state) { this->is_idle_ = state; }

    // Simulated functions for millivolts and milliamps readings
    int get_millivolts()
    {
        // simulate by returning a random value between 1800 and 5000
        return rand() % 3200 + 1800;
    }

    int get_milliamps()
    {
        // simulate by returning a return a random value between 0 and 100
        return rand() % 100;
    }
};

// DeviceServer class represents a UDP server that communicates with clients to control and monitor the Device
class DeviceServer
{
public:
    // Constructor: initializes the server with the given port number and a reference to a device
    DeviceServer(int port, Device &device)
        : port_(port), device_(device)
    {
        this->server_addr_.sin_family = AF_INET;
        this->server_addr_.sin_addr.s_addr = htonl(INADDR_ANY);
        this->server_addr_.sin_port = htons(port);
    }

    // Starts the server and listens for incoming requests
    void start()
    {
        this->server_fd_ = socket(AF_INET, SOCK_DGRAM, 0);
        if (server_fd_ < 0)
        {
            std::cerr << "Error creating socket." << std::endl;
        }
        else if (bind(server_fd_, (sockaddr *)&this->server_addr_, sizeof(this->server_addr_)) < 0)
        {
            std::cerr << "Error binding socket to address." << std::endl;
        }
        else
        {
            std::cout << "Server running and listening on port " << this->port_ << std::endl;
            listen();
        }
        close(this->server_fd_);
    }

private:
    // Member variables
    int port_;
    Device &device_;
    sockaddr_in server_addr_;
    int server_fd_;
    std::atomic<bool> test_running_{false};

    // Continuously listens for incoming requests
    void listen()
    {
        while (true)
        {
            char buffer[1024];
            sockaddr_in client_addr;
            socklen_t client_addr_len = sizeof(client_addr);

            ssize_t received_bytes = recvfrom(server_fd_, buffer, sizeof(buffer), 0, (sockaddr *)&client_addr, &client_addr_len);
            if (received_bytes < 0)
            {
                std::cerr << "Error receiving data." << std::endl;
                return;
            }

            std::string received_request(buffer, received_bytes);
            std::cout << "Received message: " << received_request << std::endl;

            std::map<std::string, std::string> request = parse_request(received_request);
            if (request.size() != 0)
            {
                fulfill_request(request, client_addr);
            }
        }
    }

    // Sends a response message to the client
    void send_message(const std::map<std::string, std::string> &message, const sockaddr_in &client_addr)
    {
        std::string frmt_msg;

        for (const auto &kv : message)
        {
            if (kv.first == "TYPE")
            {
                frmt_msg.insert(0, kv.second + ";");
            }
            else
            {
                frmt_msg += kv.first + "=" + kv.second + ";";
            }
        }

        std::cout << "Sending message: " << frmt_msg << std::endl;

        ssize_t sent_bytes = sendto(server_fd_, to_iso_8859_1(frmt_msg).c_str(), frmt_msg.length(), 0, (const sockaddr *)&client_addr, sizeof(client_addr));
        if (sent_bytes < 0)
        {
            std::cerr << "Error sending data." << std::endl;
            return;
        }
        else if (static_cast<size_t>(sent_bytes) != frmt_msg.length())
        {
            std::cerr << "Warning: Partial data sent." << std::endl;
        }
    }

    // Parses a received request into a key-value map
    std::map<std::string, std::string> parse_request(const std::string &message)
    {
        std::map<std::string, std::string> data;
        std::stringstream ss(message);
        std::string segment;
        bool first_segment = true;

        while (std::getline(ss, segment, ';'))
        {
            if (first_segment)
            {
                data["TYPE"] = segment;
                first_segment = false;
                continue;
            }

            std::size_t delimiter_position = segment.find('=');

            if (delimiter_position != std::string::npos)
            {
                std::string key = segment.substr(0, delimiter_position);
                std::string value = segment.substr(delimiter_position + 1);

                data[key] = value;
            }
            else
            {
                std::cerr << "Invalid message format: Missing \"=\" in a segment." << std::endl;
                data.clear();
                return data;
            }
        }

        return data;
    }

    // Fulfills a parsed request and sends an appropriate response
    void fulfill_request(std::map<std::string, std::string> request, sockaddr_in client_addr)
    {
        if (request.find("TYPE") != request.end() && request["TYPE"] == "ID")
        {
            send_message({{"TYPE", "ID"},
                          {"MODEL", this->device_.get_model()},
                          {"SERIAL", std::to_string(this->device_.get_serial_number())}},
                         client_addr);
            return;
        }
        else if (request.find("TYPE") != request.end() && request["TYPE"] == "TEST")
        {
            if (request.find("CMD") != request.end() && request["CMD"] == "START")
            {
                if (test_running_)
                {
                    send_message({{"TYPE", "TEST"},
                                  {"RESULT", "ERROR1"},
                                  {"MSG", "Attempting to start testing on a device that is already testing"}},
                                 client_addr);
                    return;
                }
                else
                {
                    std::chrono::milliseconds test_rate{std::stoi(request["RATE"])};
                    std::chrono::seconds test_duration{std::stoi(request["DURATION"])};
                    std::thread([this, test_rate, test_duration, client_addr]
                                { this->start_test(test_rate, test_duration, client_addr); })
                        .detach();
                    return;
                }
            }
            else if (request.find("TYPE") != request.end() && request["CMD"] == "STOP")
            {
                if (!test_running_)
                {
                    send_message({{"TYPE", "TEST"},
                                  {"RESULT", "ERROR2"},
                                  {"MSG", "Attempting to stop testing on a device that is not testing"}},
                                 client_addr);
                    return;
                }
                else
                {
                    this->device_.set_is_idle(true);
                    while (test_running_)
                    {
                        std::this_thread::yield(); // yield the current thread while waiting
                    }
                    send_message({{"TYPE", "TEST"},
                                  {"RESULT", "STOPPED"}},
                                 client_addr);
                    send_message({{"TYPE", "STATUS"}, {"STATE", "IDLE"}}, client_addr);
                    return;
                }
            }
        }
        std::cerr << "Invalid request received" << std::endl;
    }

    // Starts a test, periodically sending device status to the client
    void start_test(std::chrono::milliseconds rate, std::chrono::seconds duration, sockaddr_in client_addr)
    {
        this->device_.set_is_idle(false);
        auto start_time = std::chrono::steady_clock::now();
        auto end_time = start_time + duration;

        send_message({{"TYPE", "TEST"},
                      {"RESULT", "STARTED"}},
                     client_addr);

        test_running_ = true;
        while (this->device_.get_is_idle() == false && std::chrono::steady_clock::now() <= end_time)
        {
            send_message({{"TYPE", "STATUS"},
                          {"TIME", std::to_string(
                                       std::chrono::duration_cast<std::chrono::milliseconds>(
                                           std::chrono::steady_clock::now() - start_time)
                                           .count() /
                                       1000.0)},
                          {"MV", std::to_string(this->device_.get_millivolts())},
                          {"MA", std::to_string(this->device_.get_milliamps())}},
                         client_addr);
            std::this_thread::sleep_for(rate);
        }
        test_running_ = false;
        if (this->device_.get_is_idle() == false) // in the case that the test was stopped early
        {
            this->device_.set_is_idle(true);
            send_message({{"TYPE", "STATUS"}, {"STATE", "IDLE"}}, client_addr);
        }
    }

    // Converts a given string to ISO 8859-1 encoding
    std::string to_iso_8859_1(const std::string &input)
    {
        std::string output;
        output.reserve(input.size());

        for (unsigned char c : input)
        {
            output.push_back(static_cast<char>(c));
        }

        return output;
    }
};

// Main function: creates a DeviceServer and starts it
int main(int argc, char *argv[])
{
    // Check for correct number of command-line arguments
    if (argc != 2 & argc != 4)
    {
        std::cerr << "Usage: " << argv[0] << " <port>";
        std::cerr << " OR: " << argv[0] << " <port> <model> <serial>" << std::endl;
        return 1;
    }

    // Parse the port number from the command line
    int port = std::stoi(argv[1]);

    // Parse the model and serial number from the command line
    std::string model;
    int serial;
    if (argc >= 3)
    {
        model = argv[2];
        serial = std::stoi(argv[3]);
    }
    else
    {
        model = "default_model";
        serial = 12345;
    }

    // Create a device instance and a server instance
    Device device(model, serial);
    DeviceServer server(port, device);

    // Start the server
    server.start();
    return 0;
}