import QtQuick
import QtQuick.Controls

// Large, finger-friendly button (min 64px tall for a 7" touchscreen).
Button {
    id: control
    property bool accent: true

    implicitWidth: 200
    implicitHeight: 80
    font.pixelSize: 26

    contentItem: Text {
        text: control.text
        font: control.font
        color: Theme.text
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        radius: 12
        color: control.down
               ? Qt.darker(control.accent ? Theme.accent : Theme.surface, 1.3)
               : (control.accent ? Theme.accent : Theme.surface)
    }
}
