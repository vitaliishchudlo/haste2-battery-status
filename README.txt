Haste2 Battery 1.4.0 — Windows 11

NORMAL UPDATE (no cleanup needed)
1. Right-click the old tray icon and choose Exit (Вийти).
2. Extract the entire new ZIP into a new folder in Downloads or Desktop.
   Do not extract into %LOCALAPPDATA%\Haste2Battery.
3. Double-click INSTALL.cmd. Wait for the Windows executable build to finish.
   Internet and the previously installed Python are needed for building.
4. App starts automatically. Default polling: once per 3 minutes.
5. Startup is enabled after installation, as requested.

POLLING MENU
Right-click > Частота оновлення > 1 / 3 / 5 minutes.
The choice is saved in %LOCALAPPDATA%\Haste2Battery\settings.json.
Default on first v1.4 launch: 3 minutes. Normal updates preserve this setting.
The timer is recalculated from the last attempt when changing intervals.
There is no continual hardware polling between scheduled queries.
Refresh now (Оновити зараз) or double-click requests an immediate update.
Manual refresh is limited to one accepted request per 5 seconds; requests
while another query is in progress are ignored. No overlapping hardware reads.

QUESTION MARK POLICY
- If there has never been a valid reading: show grey ?.
- After a temporary failure, retain the last valid percentage with a grey dot.
  Tooltip shows its original time and the consecutive failure count.
- Show ? after at least 3 consecutive failures AND at least 3 minutes since
  the last successful reading, OR after 15 minutes without a valid reading
  while failures are occurring. A quick series of manual retries cannot
  immediately discard a fresh value.
- One successful reading resets the failure counter and clears the grey dot.
- Cached value is held only in memory, not restored on program launch.

TRAY AND STARTUP
80–100 green; 50–79 yellow; 20–49 orange; 0–19 red.
Hover for reading time. If hidden, drag icon out of Windows' ^ overflow.
Right-click also has Start with Windows and Exit (Ukrainian labels).
Checkbox reads both Run registration and Windows StartupApproved state.
Normal app launch and battery polling do NOT override a disabled startup state.
Only explicit Enable or the installer enables startup.
StartupApproved is an internal Windows format, not a stable public API;
blocked writes show an error. Reopen Task Manager to refresh its startup list.

OPTIONAL CLEAN REINSTALL / UNINSTALL
CLEAN_OLD.cmd removes only this utility's installed files, scoped running
processes, desktop shortcut and exact startup entries. It does NOT uninstall
Python, alter NGENUITY, or remove other apps' startup registrations.
Run it only from an extracted folder outside the installed application folder.
For a clean reinstall, then run INSTALL.cmd. Cleanup resets saved intervals.
Old download archives/source folders are not removed; delete them yourself.
After successful install, the extracted download folder may be deleted.
Keep %LOCALAPPDATA%\Haste2Battery while using the app.

FILES
Executable: %LOCALAPPDATA%\Haste2Battery\app-1.4.0\Haste2Battery.exe
Errors: %LOCALAPPDATA%\Haste2Battery\monitor.log / startup-error.txt
Each app launch logs the version, to distinguish new errors from older entries.
HID read failure logs include packet lengths and four-byte headers.

PARSER FIX FROM 1.3
Accept individual 64-byte battery replies at frame boundaries; do not require
a preceding unrelated 64-byte report. Supports a zero-ID prefix too. Ignore
unrelated reports until the 3-second deadline. Never search arbitrary payload
substrings for the battery marker.

VALIDATION
HID packet variations, noise rejection, timeout logs, refresh cooldown,
three-failure/elapsed-time policy, interval persistence/scheduling, Windows
startup states and scoped cleanup tested with simulated inputs. Syntax and ZIP
checked. Actual Windows build, mouse behavior and startup need live verification
on your PC; the development host here is Linux.

Unofficial utility, not an official HyperX product.
Protocol: https://github.com/czQery/waybar-hyperx-haste2
Only 50 02 battery query sent to USB 03f0:0f98 interface 2.
No DPI, firmware, profile or button-setting commands. No NGENUITY dependency.
