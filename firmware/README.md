\# LIMA Firmware — STM32



\- UART: Interrupt-driven (HAL\_UART\_Receive\_IT), 9600 baud

\- Packet: 8-byte \[0xAA | CMD | DATA(4) | CHECKSUM | 0x55]

\- Axes: MLX, MLY, MLZ, MRX, MRY, MRZ, SX, SY, SZ, Theta

\- GPIO: 7 pneumatic valve output, 6 limit switch input



> Note: Motor drive stubs (TODO) are placeholders. The full stepper

> driver integration was implemented on the production hardware.

