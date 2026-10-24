import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material

// Vertical 0-100 slider with a thick rounded track and a finger-sized handle.
// Colours come from the Material accent, so it turns dim red at night.
Slider {
    id: control

    implicitWidth: 64  // touch target; the drawn track is much thinner
    orientation: Qt.Vertical
    from: 0
    to: 100
    stepSize: 1

    background: Rectangle {
        x: control.leftPadding + (control.availableWidth - width) / 2
        y: control.topPadding + control.handle.height / 2
        width: 10
        height: control.availableHeight - control.handle.height
        radius: width / 2
        color: Qt.alpha(control.Material.accentColor, 0.25)

        Rectangle {  // filled part, from the bottom up to the handle
            anchors.bottom: parent.bottom
            width: parent.width
            height: control.position * parent.height
            radius: parent.radius
            color: control.Material.accentColor
        }
    }

    handle: Rectangle {
        x: control.leftPadding + (control.availableWidth - width) / 2
        y: control.topPadding + control.visualPosition * (control.availableHeight - height)
        width: control.pressed ? 34 : 28
        height: width
        radius: width / 2
        color: control.Material.accentColor
        border.width: 3
        border.color: control.Material.backgroundColor

        Behavior on width { NumberAnimation { duration: 100 } }
    }
}
