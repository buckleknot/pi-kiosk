import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material

// Large, finger-friendly Material button (min 64px tall for a 7" touchscreen).
Button {
    id: control
    property bool accent: true

    implicitWidth: 200
    implicitHeight: 80
    font.pixelSize: 26

    highlighted: accent
    Material.background: accent ? Theme.accent : Theme.surface
    Material.foreground: Theme.text
}
