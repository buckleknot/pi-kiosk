pragma Singleton
import QtQuick

// Central colours. Use as `Theme.nightText` anywhere that imports "components".
// By day the app uses stock Material colours; these are the night palette: dim red
// on black, which is easy on dark-adapted eyes. Main.qml keeps `night` in sync.
QtObject {
    property bool night: false

    readonly property color nightBackground: "#000000"
    readonly property color nightText: "#a31515"
    readonly property color nightSurface: "#1c0404"
    readonly property color nightAccent: "#420808"
}
