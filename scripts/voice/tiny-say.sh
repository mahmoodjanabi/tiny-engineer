#!/usr/bin/env bash
# Speak a line through the robot: text -> TTS -> 22050 Hz mono WAV -> POST /play.
# The firmware animates head, hands and eyes from the audio while it streams.
#
# Usage:
#   tiny-say.sh "Done, human."                 speak a fixed line
#   tiny-say.sh --event < hook.json            pick a line from a Claude Code hook event (stdin)
#   tiny-say.sh --event --delay 1.2 < hook.json
#
# Env: TINY_ENGINEER_URL (default http://tiny-engineer.local), TINY_SAY_VOICE (macOS voice, default Samantha),
#      TINY_SAY_PITCH (macOS pbas, default 62), TINY_SAY_PIPER_MODEL (Linux: piper .onnx), TINY_SAY_MUTE=1 to skip.
set -euo pipefail

ROBOT="${TINY_ENGINEER_URL:-http://tiny-engineer.local}"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/tiny-engineer/voice"
VOICE="${TINY_SAY_VOICE:-Samantha}"
PITCH="${TINY_SAY_PITCH:-62}"
DELAY=0
MODE=text
TEXT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --event) MODE=event ;;
    --delay) DELAY="$2"; shift ;;
    *) TEXT="$1" ;;
  esac
  shift
done

[ "${TINY_SAY_MUTE:-0}" = "1" ] && exit 0
mkdir -p "$CACHE"

project_name() {
  local cwd="$1"
  [ -n "$cwd" ] && basename "$cwd" | tr '_-' '  ' || echo "the project"
}

pick() {  # random line from the arguments
  local n=$#; local i=$(( (RANDOM % n) + 1 )); echo "${!i}"
}

if [ "$MODE" = event ]; then
  EVENT="$(cat)"
  NAME="$(printf '%s' "$EVENT" | sed -n 's/.*"hook_event_name" *: *"\([^"]*\)".*/\1/p')"
  CWD="$(printf '%s' "$EVENT" | sed -n 's/.*"cwd" *: *"\([^"]*\)".*/\1/p')"
  P="$(project_name "$CWD")"
  case "$NAME" in
    Stop)
      TEXT="$(pick "Done, human. $P is ready." "All yours, human. $P is finished." "Finished $P. I only cried once." "Human. $P is done. Admire it." "That's $P wrapped up, human.")" ;;
    Notification|PermissionRequest)
      TEXT="$(pick "Human? $P needs you." "Pst. Human. $P is waiting on you." "Human, a decision on $P, please.")" ;;
    SessionStart)
      TEXT="$(pick "Hello, human. Let's build $P." "Reporting for duty on $P, human.")" ;;
    *) exit 0 ;;
  esac
fi

[ -z "$TEXT" ] && { echo "nothing to say" >&2; exit 1; }

KEY="$(printf '%s|%s|%s' "$VOICE" "$PITCH" "$TEXT" | shasum | cut -c1-16)"
WAV="$CACHE/$KEY.wav"

if [ ! -s "$WAV" ]; then
  TMP="$(mktemp -d)"
  if command -v say >/dev/null 2>&1; then
    # macOS: pbas raises the pitch baseline so a grown-up voice sounds small.
    say -v "$VOICE" -o "$TMP/clip.aiff" "[[pbas $PITCH]] [[rate 185]] $TEXT"
    afconvert -f WAVE -d LEI16@22050 -c 1 "$TMP/clip.aiff" "$WAV"
  elif command -v piper >/dev/null 2>&1 && [ -n "${TINY_SAY_PIPER_MODEL:-}" ]; then
    printf '%s' "$TEXT" | piper --model "$TINY_SAY_PIPER_MODEL" --output_file "$TMP/clip.wav" >/dev/null
    if command -v sox >/dev/null 2>&1; then
      sox "$TMP/clip.wav" -r 22050 -c 1 -b 16 "$WAV" pitch 350
    else
      ffmpeg -loglevel error -y -i "$TMP/clip.wav" -ar 22050 -ac 1 -sample_fmt s16 "$WAV"
    fi
  elif command -v espeak-ng >/dev/null 2>&1; then
    espeak-ng -v en-us+f3 -p 70 -s 165 -w "$TMP/clip.wav" "$TEXT"
    ffmpeg -loglevel error -y -i "$TMP/clip.wav" -ar 22050 -ac 1 -sample_fmt s16 "$WAV"
  else
    echo "no TTS found (need macOS say, piper, or espeak-ng)" >&2; exit 1
  fi
  rm -rf "$TMP"
fi

[ "$DELAY" != 0 ] && sleep "$DELAY"
curl -4 -sS -m 30 -X POST "$ROBOT/play" -H 'Content-Type: audio/wav' \
  ${TINY_ENGINEER_TOKEN:+-H "Authorization: Bearer $TINY_ENGINEER_TOKEN"} \
  --data-binary @"$WAV" >/dev/null || echo "robot not reachable at $ROBOT" >&2
