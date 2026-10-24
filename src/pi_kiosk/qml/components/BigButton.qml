import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material

// Large, finger-friendly Material button (min 64px tall for a 7" touchscreen).
// Stock Material by day, with plain buttons tinted to the background; dim red at night.
Button {
    id: control
    property bool accent: true

    implicitWidth: 200
    implicitHeight: 80
    font.pixelSize: 26

    // Material always draws highlighted text bright white, too harsh at night.
    highlighted: accent && !Theme.night
    Material.background: Theme.night ? (accent ? Theme.nightAccent : Theme.nightSurface)
                                     : (accent ? undefined : Theme.buttonTint)
    Material.foreground: Theme.night ? Theme.nightText : undefined
}
