# Desktop test instances (sourced by desktop.sh and desktop-build.sh). DESKTOP_INSTANCE picks one; the
# default is `desktop`. Each has its own Windows dir (its own JDK copy, so `stop` matches only its
# processes by executable path), user.home, RSProx ports and devtools port.
#   name      dir            devtools  RSProx jav_config / proxy (OsrsTestLauncher -Dosrstest.portskip)
#   desktop   C:\osrs-test   7780      43600 / 43701
#   desktop2  C:\osrs-test2  7781      43620 / 43721
#   desktopN  C:\osrs-testN  7779+N    43600+20(N-1) / 43701+20(N-1)   (N = 3..5, past 5 the RSProx ranges collide with desktop's; staged by desktop-build.sh on first use)
DESKTOP_INSTANCE=${DESKTOP_INSTANCE:-desktop}
case $DESKTOP_INSTANCE in
desktop)  WIN_DIR='C:\osrs-test';  DT_PORT=7780; PORT_SKIP=0;  PORTS_RE='7780|4360[0-9]|4370[0-9]|4371[0-9]' ;;
desktop2) WIN_DIR='C:\osrs-test2'; DT_PORT=7781; PORT_SKIP=20; PORTS_RE='7781|4362[0-9]|4372[0-9]' ;;
desktop[3-5]) i=$(( ${DESKTOP_INSTANCE#desktop} - 1 )); WIN_DIR="C:\\osrs-test$((i + 1))"; DT_PORT=$((7780 + i)); PORT_SKIP=$((20 * i))
          PORTS_RE="$DT_PORT|$((4360 + 2 * i))[0-9]|$((4370 + 2 * i))[0-9]" ;;
*) echo "unknown DESKTOP_INSTANCE=$DESKTOP_INSTANCE (desktop, desktop2 .. desktop5)" >&2; exit 2 ;;
esac
WIN=/mnt/c/${WIN_DIR#C:\\}             # the same dir from WSL
export DESKTOP_INSTANCE DESKTOP_DEVTOOLS_PORT=$DT_PORT
