# LIMA System Communication Protocol

This document provides a technical reference for the binary communication protocol used between the LIMA Python interface and the STM32 microcontroller. 

## 1. Packet Structure

All communications use a fixed 8-byte binary packet structure.

| Byte Offset | Field | Size (Bytes) | Description |
|---|---|---|---|
| 0 | **START** | 1 | Start byte, always `0xAA` |
| 1 | **CMD_ID** | 1 | Command or Register ID |
| 2-5 | **DATA** | 4 | 32-bit Integer Data (Big-Endian) |
| 6 | **CHECKSUM** | 1 | Checksum byte |
| 7 | **END** | 1 | End byte, always `0x55` |

## 2. Data Transmission

- **Byte Order:** The 4-byte `DATA` payload is transmitted in **Big-Endian** format.
- **Signed Values:** Negative values are handled using Two's Complement (32-bit unsigned conversion).
- **Checksum Calculation:** The checksum is calculated as the sum of the command byte and all 4 data bytes, modulo 256.
  - `Checksum = (CMD_ID + DATA[0] + DATA[1] + DATA[2] + DATA[3]) & 0xFF`

## 3. Register Addresses (Command IDs)

Below are the mapped register addresses (Hex) used for the `CMD_ID` byte. These must exactly match the definitions in the STM32 `main.c` firmware.

### 3.1. System Commands
| Command | Hex | Direction | Description |
|---|---|---|---|
| STOP | `0x01` | TX | Emergency Stop |
| COMCHECK | `0x02` | TX | Communication Check |
| TESTMODE | `0x03` | TX | Enable Test Mode |
| TESTMODEBACK | `0x04` | TX | Disable Test Mode |
| JOYMODE | `0x05` | TX | Enable Joystick Mode |
| JOYMODEBACK | `0x06` | TX | Disable Joystick Mode |
| HOMESYSTM | `0xF0` | TX | Home Entire System |

### 3.2. Motor Controls

**Micro Left Z (MLZ)**
| Command | Hex | Direction | Description |
|---|---|---|---|
| MOVEMLZ | `0x10` | TX | Move to Position |
| MLZPOS | `0x11` | RX | Position Feedback |
| HOMEMLZ | `0x14` | TX | Home Command |
| GOMLZ | `0xAB` | TX | Move Distance |

**Micro Right Z (MRZ)**
| Command | Hex | Direction | Description |
|---|---|---|---|
| HOMEMRZ | `0x19` | TX | Home Command |
| HOMEMRZOK | `0x1A` | RX | Home OK Feedback |
| MRZPOS | `0xB3` | RX | Position Feedback |
| MOVEMRZ | `0xBC` | TX | Move to Position |

**Sample Z (SZ)**
| Command | Hex | Direction | Description |
|---|---|---|---|
| SZPOS | `0x32` | RX | Position Feedback |
| MOVESZ | `0x39` | TX | Move to Position |
| GOSZ | `0x3A` | TX | Move Distance |
| HOMESZ | `0x84` | TX | Home Command |
| HOMESZOK | `0x85` | RX | Home OK Feedback |

*(Note: Other motors like Theta, Sample X/Y, Micro Left X/Y, and Micro Right X/Y follow similar logical grouping and hex allocations. Refer to `protocol.py` for an exhaustive list.)*

### 3.3. Speed & Light
| Command | Hex | Direction | Description |
|---|---|---|---|
| SXYSPEED | `0x96` | TX | Sample XY Speed |
| MICSPEED | `0x97` | TX | Microscope Speed |
| MICLIGHT | `0x98` | TX | Microscope Light Intensity |
| FOCUSSPEED | `0x99` | TX | Focus Speed |

### 3.4. Contact Modes & Process
| Command | Hex | Direction | Description |
|---|---|---|---|
| CONTMODE | `0xB0` | TX | Select Contact Mode |
| PROXCONT | `0x9C` | TX | Proximity Contact Value |
| ALIGN | `0xC0` | TX | Alignment Control |
| AUTOALIGN | `0xC5` | TX | Auto Align Sequence |
| EXPOSURE | `0xD0` | TX | Exposure Control |
| GAP | `0xE0` | TX | Gap Control |

## 4. Developer Guidelines

1. **Firmware Synchronization:** Any changes to `CMD_ID`s in the Python backend must be exactly mirrored in the STM32 firmware header definitions.
2. **Tx/Rx Processing:** The backend uses async serial loops to process incoming 8-byte packets continually without blocking the UI.
3. **Invalid Packets:** Packets missing `0xAA` or `0x55` terminators or failing checksum verification will be discarded to prevent erratic hardware behavior.
