# Makefile

CXX = g++
CXXFLAGS = -Wall -Wextra -std=c++11
TARGET = device

all: $(TARGET)

$(TARGET): device.o
	$(CXX) $(CXXFLAGS) -o $(TARGET) device.o

device.o: device.cpp
	$(CXX) $(CXXFLAGS) -c device.cpp

clean:
	rm -f *.o $(TARGET)
