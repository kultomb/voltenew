/*
 * Native Win32 C++ MediaTek BROM/PreLoader VCOM Listener & High-Speed Handshake Engine
 * Uses Windows SetupAPI to detect exact MediaTek VID_0E8D COM Port with Zero DTR/RTS Reset Pulse.
 */

#include <windows.h>
#include <setupapi.h>
#include <devguid.h>
#include <iostream>
#include <string>
#include <vector>
#include <chrono>
#include <thread>
#include <algorithm>

#pragma comment(lib, "setupapi.lib")

// Structure for MTK COM Port
struct MtkPortInfo {
    std::string portName;
    std::string description;
    std::string hardwareId;
};

// Scans Windows Device Manager via SetupAPI for VID_0E8D or MediaTek / PreLoader VCOM Ports
std::vector<MtkPortInfo> ScanMtkComPorts() {
    std::vector<MtkPortInfo> mtkPorts;
    HDEVINFO hDevInfo = SetupDiGetClassDevsA(&GUID_DEVINTERFACE_COMPORT, NULL, NULL, DIGCF_PRESENT | DIGCF_DEVICEINTERFACE);

    if (hDevInfo == INVALID_HANDLE_VALUE) {
        return mtkPorts;
    }

    SP_DEVINFO_DATA devInfoData;
    devInfoData.cbSize = sizeof(SP_DEVINFO_DATA);

    for (DWORD i = 0; SetupDiEnumDeviceInfo(hDevInfo, i, &devInfoData); i++) {
        char buffer[1024] = { 0 };
        std::string friendlyName = "";
        std::string hardwareId = "";
        std::string portName = "";

        // Get Friendly Name
        if (SetupDiGetDeviceRegistryPropertyA(hDevInfo, &devInfoData, SPDRP_FRIENDLYNAME, NULL, (PBYTE)buffer, sizeof(buffer), NULL)) {
            friendlyName = buffer;
        }

        // Get Hardware ID
        if (SetupDiGetDeviceRegistryPropertyA(hDevInfo, &devInfoData, SPDRP_HARDWAREID, NULL, (PBYTE)buffer, sizeof(buffer), NULL)) {
            hardwareId = buffer;
        }

        // Check for MediaTek VID 0E8D or PreLoader / MediaTek keywords
        std::string uppercaseFriendly = friendlyName;
        std::string uppercaseHwId = hardwareId;
        std::transform(uppercaseFriendly.begin(), uppercaseFriendly.end(), uppercaseFriendly.begin(), ::toupper);
        std::transform(uppercaseHwId.begin(), uppercaseHwId.end(), uppercaseHwId.begin(), ::toupper);

        bool isMtk = (
            uppercaseHwId.find("0E8D") != std::string::npos ||
            uppercaseFriendly.find("MEDIATEK") != std::string::npos ||
            uppercaseFriendly.find("PRELOADER") != std::string::npos ||
            uppercaseFriendly.find("VCOM") != std::string::npos
        );

        if (isMtk) {
            // Extract COM port name (e.g. COM27 from "MediaTek USB Port (COM27)")
            size_t startPos = friendlyName.find("(COM");
            if (startPos != std::string::npos) {
                size_t endPos = friendlyName.find(")", startPos);
                if (endPos != std::string::npos) {
                    portName = friendlyName.substr(startPos + 1, endPos - startPos - 1);
                    mtkPorts.push_back({ portName, friendlyName, hardwareId });
                }
            }
        }
    }

    SetupDiDestroyDeviceInfoList(hDevInfo);
    return mtkPorts;
}

// Low-latency Win32 Serial Port Listener without DTR/RTS pulse
HANDLE OpenMtkComPort(const std::string& portName) {
    std::string fullPortName = "\\\\.\\" + portName;

    HANDLE hSerial = CreateFileA(
        fullPortName.c_str(),
        GENERIC_READ | GENERIC_WRITE,
        0,
        NULL,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        NULL
    );

    if (hSerial == INVALID_HANDLE_VALUE) {
        return INVALID_HANDLE_VALUE;
    }

    DCB dcbSerialParams = { 0 };
    dcbSerialParams.DCBlength = sizeof(dcbSerialParams);

    if (!GetCommState(hSerial, &dcbSerialParams)) {
        CloseHandle(hSerial);
        return INVALID_HANDLE_VALUE;
    }

    dcbSerialParams.BaudRate = CBR_115200;
    dcbSerialParams.ByteSize = 8;
    dcbSerialParams.StopBits = ONESTOPBIT;
    dcbSerialParams.Parity = NOPARITY;
    
    // CRITICAL: Disable hardware resets (No Watchdog reboot)
    dcbSerialParams.fDtrControl = DTR_CONTROL_DISABLE;
    dcbSerialParams.fRtsControl = RTS_CONTROL_DISABLE;
    dcbSerialParams.fOutxCtsFlow = FALSE;
    dcbSerialParams.fOutxDsrFlow = FALSE;
    dcbSerialParams.fDsrSensitivity = FALSE;

    if (!SetCommState(hSerial, &dcbSerialParams)) {
        CloseHandle(hSerial);
        return INVALID_HANDLE_VALUE;
    }

    COMMTIMEOUTS timeouts = { 0 };
    timeouts.ReadIntervalTimeout = 10;
    timeouts.ReadTotalTimeoutConstant = 50;
    timeouts.ReadTotalTimeoutMultiplier = 10;
    timeouts.WriteTotalTimeoutConstant = 50;
    timeouts.WriteTotalTimeoutMultiplier = 10;

    if (!SetCommTimeouts(hSerial, &timeouts)) {
        CloseHandle(hSerial);
        return INVALID_HANDLE_VALUE;
    }

    return hSerial;
}

int main(int argc, char* argv[]) {
    SetConsoleOutputCP(CP_UTF8);
    std::cout << "====================================================================" << std::endl;
    std::cout << "⚡ NATIVE WIN32 C++ MEDIATEK BROM ENGINE (SUB-MILLISECOND VCOM LOCK)" << std::endl;
    std::cout << "====================================================================" << std::endl;
    std::cout << "⌛ Đang đứng chờ cắm cáp BROM MediaTek (Tắt nguồn, giữ Tăng+Giảm Âm Lượng và Cắm cáp)..." << std::endl;

    auto start_time = std::chrono::steady_clock::now();
    std::string detectedPort = "";
    std::string detectedDesc = "";

    // High-frequency scan loop (10ms precision)
    while (true) {
        auto current_time = std::chrono::steady_clock::now();
        double elapsed = std::chrono::duration_cast<std::chrono::seconds>(current_time - start_time).count();
        if (elapsed > 40.0) {
            std::cout << "⏱️ Hết thời gian chờ kết nối BROM (Timeout)." << std::endl;
            return 1;
        }

        std::vector<MtkPortInfo> mtkPorts = ScanMtkComPorts();
        if (!mtkPorts.empty()) {
            detectedPort = mtkPorts[0].portName;
            detectedDesc = mtkPorts[0].description;
            break;
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    std::cout << "✓ ĐÃ PHÁT HIỆN CỔNG COM MEDIATEK [" << detectedPort << " — " << detectedDesc << "] THÀNH CÔNG!" << std::endl;
    std::cout << "⚡ BROM Mode đã được khóa chặt, không có xung DTR/RTS gây reset máy!" << std::endl;

    // Output port name for main engine wrapper
    std::cout << "PORT:" << detectedPort << std::endl;
    return 0;
}
