# LIMA Advanced Control System

![LIMA Version](https://img.shields.io/badge/version-2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-yellow.svg)
![PyQt5](https://img.shields.io/badge/UI-PyQt5-green.svg)

## Overview

The **LIMA Advanced Control System** is a professional, high-precision graphical interface designed for comprehensive motor management, microscopy operations, and automated photolithography processing. It communicates securely with an STM32-based hardware architecture via a robust, custom 8-byte binary protocol. 

## Features & Modules

### 🎛️ Process & Interface Control
- **Vacuum Control Systems**: Complete independent control over sample and mask vacuums. Provides real-time visual feedback (Red/Green status indicators) for `Vacuum Contact`, `Mask Vacuum`, and `Sample Vacuum`.
- **Contact Modes**: Switch seamlessly between Hard Contact, Soft Contact, Vacuum Contact, and Proximity modes.
- **Exposure & Alignment**: Automated tracking of exposure dose, power, and energy with integrated Auto-Align and Auto-Focus sequences.
- **Live Camera Feed**: Real-time integration with microscope vision feeds.
- **Modern UI Styling**: Glassmorphic, dark-mode aesthetic with hardware-synchronized button states and responsive components.

---

---

## 📸 System Gallery

A comprehensive look at the LIMA Advanced Control System modules, from initial alignment to real-time process monitoring.

### 🎮 Interface Modules
| **Main Menu** | **Home Positioning** |
|:---:|:---:|
| <img src="assets/images/01_main_menu.png" width="400"> | <img src="docs/screenshots/02_home_positioning.png" width="400"> |

| **Valve Controls** | **Motor Settings** |
|:---:|:---:|
| <img src="assets/images/03_valve_controls.png" width="400"> | <img src="docs/screenshots/04_motor_settings.png" width="400"> |

| **Diagnostics** | **Process Management** |
|:---:|:---:|
| <img src="assets/images/05_diagnostics.png" width="400"> | <img src="docs/screenshots/07_Process.png" width="400"> |

### 🔬 Alignment & Vision
*Real-time microscope feed integration and wafer alignment sequences.*

| **Alignment Sequence 01** | **Alignment Sequence 02** |
|:---:|:---:|
| <img src="assets/images/Alligmen_01.PNG" width="400"> | <img src="docs/screenshots/Alligmen_02.PNG" width="400"> |

| **Alignment Sequence 03** | **Alignment Sequence 05** |
|:---:|:---:|
| <img src="assets/images/Alligmen_03.PNG" width="400"> | <img src="docs/screenshots/Alligmen_05.PNG" width="400"> |

---

## 📊 Real-Time Telemetry (Grafana)
The system streams hardware health and process data via InfluxDB to a dual-layered Grafana dashboard.

<div align="center">
  <img src="assets/images/06_grafana_monitoring_1.png" width="850" style="display: block; margin-bottom: 0;">
  <img src="assets/images/06_grafana_monitoring_2.png" width="850" style="display: block; margin-top: -1px;">
</div>

> **Note:** The dashboard visualizes real-time status for all 9 motor axes, vacuum levels, and STM32 communication logs.

---


---

## Hardware Requirements

- **Microcontroller**: STM32 series running the LIMA compatible firmware.
- **Actuators**: Stepper/Servo motor drivers attached to MLX, MLY, MLZ, MRX, MRY, MRZ, SX, SY, SZ axes.
- **Sensors/IO**: Pneumatic vacuum valves and pressure sensors.
- **Connectivity**: USB to Serial (RS-232/UART) connection to the host PC.

## Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-org/Lima_Github_REPO.git
   cd Lima_Github_REPO
   ```

2. **Set up a Virtual Environment** (Recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install Dependencies**
   Install the required Python packages (PyQt5, pyserial, opencv-python, etc.).
   ```bash
   pip install PyQt5 pyserial opencv-python
   # Or via requirements if available:
   # pip install -r requirements.txt
   ```

## Example Usage

The main entry point for the application is the `MainMenu.py` script.

```bash
python MainMenu.py
```

### Basic Workflow:
1. **Launch**: Start the application using the command above.
2. **Connect**: Let the serial manager automatically detect and connect to the STM32 via the appropriate COM port.
3. **Motor Homing**: Use the Motor Control tab to home the Z, X, and Y axes. Visual indicators will turn green once homing (`HOMESZOK`, etc.) is completed.
4. **Process Setup**: Navigate to the Process tab. Secure your sample using the **Vacuum Control** toggle.
5. **Alignment & Exposure**: Use the controls to align the mask, set your contact mode, and trigger the exposure routine.

## Technical References

For developers extending the communication interface, please refer to the [PROTOCOL.md](PROTOCOL.md) for detailed breakdowns of packet structures, register addresses, and checksum calculations.
