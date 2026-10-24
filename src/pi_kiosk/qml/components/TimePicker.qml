import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// HH:MM picker made of two finger-sized wheels. `value` is "HH:MM". `picked` fires
// once the wheels settle, so spinning doesn't save settings on every step.
ColumnLayout {
    id: picker
    property string label
    property string value: "00:00"
    signal picked(string value)

    spacing: 0

    function pad(n) { return n < 10 ? "0" + n : "" + n }

    function sync() {
        const parts = value.split(":")
        hours.currentIndex = parseInt(parts[0])
        minutes.currentIndex = parseInt(parts[1])
    }

    Component.onCompleted: sync()
    onValueChanged: if (!settle.running) sync()

    Label {
        Layout.alignment: Qt.AlignHCenter
        text: picker.label
        font.pixelSize: 18
        opacity: 0.8
    }

    RowLayout {
        Layout.alignment: Qt.AlignHCenter
        spacing: 0

        component Wheel: Tumbler {
            Layout.preferredWidth: 72
            Layout.preferredHeight: 150
            visibleItemCount: 3
            onCurrentIndexChanged: settle.restart()
            delegate: Label {
                required property int index
                text: picker.pad(index)
                font.pixelSize: 32
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                opacity: 1.0 - Math.abs(Tumbler.displacement) / 2
            }
        }

        Wheel { id: hours; model: 24 }
        Label { text: ":"; font.pixelSize: 32 }
        Wheel { id: minutes; model: 60 }
    }

    Timer {
        id: settle
        interval: 400
        onTriggered: {
            if (hours.moving || minutes.moving)
                return restart()
            const v = picker.pad(hours.currentIndex) + ":" + picker.pad(minutes.currentIndex)
            if (v !== picker.value)
                picker.picked(v)
        }
    }
}
