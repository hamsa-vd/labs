# hava timer

A menu bar macOS timer, stopwatch, and current-time display with floating Sora Bold Liquid Glass digits. Requires macOS 13+, with native glass on macOS 26+. No standalone window, Dock icon, or Cmd+Tab entry.

## Build and launch

```sh
bash scripts/build-app.sh
open "dist/hava timer.app"
```

The script falls back to Command Line Tools if selected Xcode is unavailable. Builds are ad-hoc signed for local use. Quit and reopen to load a rebuilt version. If a root `timer.svg` exists, the build copies it into Resources; otherwise it keeps the packaged SVG.

## Modes and controls

Click the menu bar icon for timer presets, a custom duration, stopwatch, Hava Clock, and Quit. These are alternative modes: enabling current time or starting a new timer/stopwatch replaces the active session.

- **Timer:** Enter 1–1,440 minutes. Shows `4:17` or `2:20:00`, with centered colons. Supports pause/resume and reset. Below 10% remaining, the digits use a dark-to-light red gradient. The final ten seconds add a red pulse and glow. At zero, the digits and a white border around that display glow three times, then disappear.
- **Stopwatch:** Counts up from `0:00`, adding hours when needed. Pause/resume preserves elapsed time. Reset returns to a visible paused `0:00`; Stop hides it.
- **Hava Clock:** A checkable menu option displaying local time in 24-hour `HH:mm:ss` format on every connected monitor. Clocks appear only while their monitor’s menu bar is hidden, and hide when it reappears; this rule does not affect timer or stopwatch. These clocks have no icon beside their digits and glow continuously. Each monitor has an independently remembered corner, defaulting to top right. Connecting a monitor adds a clock; disconnecting it removes that clock. This option is remembered across launches. Uncheck it or right-click a clock and select Hide Hava Clock to turn it off.

Timer and stopwatch have an animated SVG icon beside the digits; the menu bar always uses the supplied timer artwork. Drag the numbers to move them and release to glide to the nearest corner. A held drag is never repositioned by timer updates. Current-time clocks remain on their own monitors when snapped. Hover gives a white glow and grab cursor. Reduced Motion disables the movement animations.

Right-click timer/stopwatch numbers for Pause/Resume and Stop. Stop in this contextual menu hides the session. Right-click a current-time clock for Hide Hava Clock and Quit. All displays support double-click to open the menu bar controls.

## Raycast

Commands live in `/Users/liv-extech/repos/local_store/scripts/raycast/commands`, linked into the configured `~/.config/raycast/scripts` folder:

- **Hava Timer:** Blank input opens controls; a number starts that many minutes.
- **Hava Stopwatch:** Starts a new stopwatch.
- **Hava Clock:** Enables current time on each monitor when its menu bar is hidden. Replaces Hava Time.
- **Quit Hava Timer:** Quits the whole app, including every clock and the menu bar icon. Replaces the old Stop Hava Timer command.

Use Reload Script Commands if a new or renamed command is missing. Command icons are light/dark PNGs derived from the SVG because Raycast script metadata requires raster icons.

Supported URLs: `hava-timer://start?minutes=25`, `hava-timer://stopwatch`, `hava-timer://clock`, `hava-timer://menu`, `hava-timer://quit`. The old `/stop` URL remains a quit alias.

## Timing and limitations

Timer and stopwatch use wall-clock dates, catch up after sleep, and are affected by system clock adjustments. Active sessions are not restored after quitting. Current time reads the current calendar/time zone, including changes after launch. Overlay visibility in full-screen apps follows macOS Spaces behavior.

Apple Clock timer mirroring is not implemented. The app runs its own timer and stopwatch.

## Stopwatch mouse activity

The Stopwatch activity submenu enables a one-point mouse movement and immediate return once a minute while the stopwatch is running. This preference starts enabled. macOS input-control permission is required: click Allow mouse activity… in that submenu and approve the app in System Settings if prompted. The app does not request access automatically or grant it itself.

Pulses are skipped when input has occurred in the preceding 55 seconds, while mouse buttons or modifier keys are held, while the main display sleeps, or when the login/screen-saver app is foreground. Pause, Stop, switching modes and Quit cancel the activity timer. No keystrokes or clicks are generated. The events are synthetic; Teams may ignore them and its presence can also follow calendars, calls, locks and other devices. This feature does not guarantee Available status or unlock the Mac. Disable the checkbox to use a stopwatch without mouse activity.
