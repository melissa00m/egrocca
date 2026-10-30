# ShopDroid XOD Firmware & Motor Controller

This directory contains the completed visual XOD firmware deliverables for **GitHub Issue #2: "Build XOD patches for motor control and steering logic"**.

---

## 📁 Deliverables Included

| File / Folder | Format | Description |
| :--- | :--- | :--- |
| **[`shopdroid-motor-controller/`](./shopdroid-motor-controller)** | Multi-file XOD Project | Git-friendly project directory with `project.xod` and `main/patch.xodp`. |
| **[`shopdroid-motor-controller.xodball`](./shopdroid-motor-controller.xodball)** | Packed `.xodball` Archive | Single-file portable bundle. Importable via **Project &rarr; Add Library / Open Project** in XOD IDE. |
| **[`firmware_arduino/shopdroid_firmware.ino`](./firmware_arduino/shopdroid_firmware.ino)** | Arduino C++ Sketch | Equivalent native C++ firmware matching the exact pinouts and logic. |
| **[`index.html`](./index.html)** | Interactive Web Guide | Standalone visual architecture explanation with live interactive node simulator. |

---

## 📌 Hardware Pin Mapping

| Component | Function | MCU Pin | Notes |
| :--- | :--- | :--- | :--- |
| **HC-SR04 Sonar** | `TRIG` | `D2` | Sends ultrasonic ping |
| **HC-SR04 Sonar** | `ECHO` | `D3` | Reads echo duration |
| **Left Motor (L298N)** | `DIR` (IN1/IN2) | `D4` | Direction switch (HIGH: Forward, LOW: Reverse) |
| **Left Motor (L298N)** | `PWM` (ENA) | `D5` | Speed control via analog duty cycle (`0` to `255`) |
| **Right Motor (L298N)** | `PWM` (ENB) | `D6` | Speed control via analog duty cycle (`0` to `255`) |
| **Right Motor (L298N)** | `DIR` (IN3/IN4) | `D7` | Direction switch (HIGH: Forward, LOW: Reverse) |

---

## ⚙️ How the Logic Works

1. **Differential Steering Mixer:**
   - Linear speed input $V$ (`-1.0` to `1.0`) and angular turn input $W$ (`-1.0` to `1.0`).
   - Left Motor Speed $= V - W$ (clipped to $[-1.0, 1.0]$).
   - Right Motor Speed $= V + W$ (clipped to $[-1.0, 1.0]$).

2. **Automatic Hardware Emergency Stop (E-Stop):**
   - The `hc-sr04-ultrasonic-range` node pings continuously.
   - If distance $< 0.30\text{ m}$ ($30\text{ cm}$), the comparator node triggers an immediate override.
   - The `if-else(number)` nodes cut Left and Right motor throttle to **`0.0`**, instantly stopping the droid before a collision.

---

## 🚀 How to Open & Run in XOD IDE

1. Launch XOD IDE from the terminal:
   ```bash
   xod
   ```
2. Open the project:
   - Click **File &rarr; Open Project...** and select `/home/nust/Desktop/egrocca/xod/shopdroid-motor-controller/`.
   - *Or* click **Project &rarr; Import .xodball...** and pick `shopdroid-motor-controller.xodball`.
3. To test in simulation: Click **Deploy &rarr; Simulate**.
4. To flash to your board: Connect your Arduino / ESP32 via USB and click **Deploy &rarr; Flash to Arduino**.
