# Voice

`tiny-say.sh` gives the robot a voice: text → TTS → 22050 Hz mono WAV → `POST /play`. The firmware already animates to the audio it streams (head nods on emphasis, hand lifts on phrase starts, eyes lock on the listener while speech energy is high), so no firmware change is needed. Clips are cached by text, so repeated lines play instantly.

## Try it

```bash
scripts/voice/tiny-say.sh "Done, human."
TINY_ENGINEER_URL=http://192.168.1.50 scripts/voice/tiny-say.sh "Human? The backend needs you."
```

## TTS backends (first found wins)

| Platform | Backend | Notes |
| --- | --- | --- |
| macOS | `say` + `afconvert` (built in) | `TINY_SAY_VOICE` picks the voice (default `Samantha`), `TINY_SAY_PITCH` sets the pitch baseline (default 62; 50 is normal, 70 is cartoon) |
| Linux | [piper](https://github.com/rhasspy/piper) | set `TINY_SAY_PIPER_MODEL=/path/voice.onnx`; needs `sox` or `ffmpeg` |
| Linux | `espeak-ng` + `ffmpeg` | fallback, robotic |

`TINY_SAY_MUTE=1` skips everything (quiet hours). `TINY_ENGINEER_TOKEN` adds the bearer header when the robot has an access token.

## Hook it to Claude Code

`--event` reads the hook JSON from stdin and picks a line for the event, naming the project from `cwd`:

| Event | Says |
| --- | --- |
| `Stop` | "Done, human. *project* is ready." (5 variants) |
| `Notification`, `PermissionRequest` | "Human? *project* needs you." (3 variants) |
| `SessionStart` | "Hello, human. Let's build *project*." |

Add it next to the stock hook in `~/.claude/settings.json` (or `.claude/settings.json` in a project). The stock hook plays the bell on `Stop`; `--delay 1.2` lets the bell ring first:

```json
"Stop": [{ "hooks": [
  { "type": "command", "async": true,
    "command": "node \"$CLAUDE_PROJECT_DIR/packages/tiny-engineer-cli/bin/tiny-engineer.js\" hook claude-code" },
  { "type": "command", "async": true,
    "command": "\"$CLAUDE_PROJECT_DIR/scripts/voice/tiny-say.sh\" --event --delay 1.2" }
]}],
"Notification": [{ "hooks": [
  { "type": "command", "async": true,
    "command": "node \"$CLAUDE_PROJECT_DIR/packages/tiny-engineer-cli/bin/tiny-engineer.js\" hook claude-code" },
  { "type": "command", "async": true,
    "command": "\"$CLAUDE_PROJECT_DIR/scripts/voice/tiny-say.sh\" --event --delay 3.5" }
]}]
```

`Notification` already plays the stock "pst… human" clip (~3 s); the `--delay 3.5` lets it finish before the spoken line. Drop the stock hook from `Notification` if you'd rather hear only the spoken line.

Edit the lines in `tiny-say.sh` (the `pick` calls) to change the personality.

## Known gaps

- Two Claude Code sessions finishing at once both speak; the robot plays whichever `/play` arrives first and rejects the other with 409. A host daemon that queues per session is the fix.
- On the round-face head, the eyes react to speech but there is no mouth yet; that comes with the round-face firmware.
