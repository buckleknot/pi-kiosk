pragma Singleton
import QtQuick

// Central colours/sizes. Use as `Theme.accent` anywhere that imports "components".
QtObject {
    readonly property color background: "#1e1f24"
    readonly property color surface: "#2c2e35"
    readonly property color accent: "#2f7de1"
    readonly property color text: "#f2f2f2"
    readonly property color muted: "#9a9ca3"
}
