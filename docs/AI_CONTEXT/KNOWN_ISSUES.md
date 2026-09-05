# KNOWN_ISSUES.md — BUG HISTORY & RESOLVED CAUSES

## BUG #001: MediaTek SoC Watchdog Reboot on BROM Connection
- **Problem**: Phone rebooted after ~4 seconds when holding Vol Up + Down and plugging in USB.
- **Root Cause**: `pyserial.Serial()` defaulted DTR/RTS voltage high during open, sending hardware reset pulse to SoC.
- **Fix**: Created Native C++ SetupAPI BROM engine with `DTR_CONTROL_DISABLE` and monkey-patched `serialwin32` driver in `seriallib.py`.
- **Prevention**: Always use patched `seriallib.py` and C++ engine for BROM connection.

---

## BUG #002: Log Panel Console Width Shift
- **Problem**: Log panel resized horizontally when action button text length changed.
- **Root Cause**: Dynamic `pack(side=...)` recalculation on `split_body`.
- **Fix**: Replaced `pack()` with 50/50 uniform grid `columnconfigure(0, weight=1, uniform="col_split")`.
- **Prevention**: Never use dynamic packing for main container splits.

---

## BUG #003: VID Matching Failure on Windows MediaTek COM Ports
- **Problem**: `mtkclient` printed `DeviceClass - [LIB]: Couldn't get device configuration` and fell back to `libusb`.
- **Root Cause**: `port.vid` returned `None` on Windows COM driver list.
- **Fix**: Updated `detectdevices()` in `seriallib.py` to match explicit port name (`COM27`) and `COM` prefix directly.
- **Prevention**: Always match explicit port names on Windows before checking VID/PID.
