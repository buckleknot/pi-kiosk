import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

// Settings: night-mode window, alarm time and sounds. Changes apply immediately.
Page {
    id: page
    required property var backend
    signal backRequested()

    // A preview shouldn't keep playing once you leave the page.
    Component.onDestruction: page.backend.stopPreview()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 8

        RowLayout {
            spacing: 16
            BigButton {
                implicitWidth: 140
                implicitHeight: 72
                accent: false
                text: "Back"
                onClicked: page.backRequested()
            }
            Label {
                text: "Settings"
                font.pixelSize: 28
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 48
            TimePicker {
                label: "Night starts"
                value: page.backend.nightStart
                onPicked: v => page.backend.nightStart = v
            }
            TimePicker {
                label: "Night ends"
                value: page.backend.nightEnd
                onPicked: v => page.backend.nightEnd = v
            }
            TimePicker {
                label: "Alarm"
                value: page.backend.alarmTime
                onPicked: v => page.backend.alarmTime = v
            }
        }

        SoundPicker {
            backend: page.backend
            label: "Relax sound"
            kind: "ambient"
            sounds: page.backend.ambientSounds
            current: page.backend.ambientSound
            onPicked: id => page.backend.ambientSound = id
        }

        SoundPicker {
            backend: page.backend
            label: "Alarm sound"
            kind: "alarm"
            sounds: page.backend.alarmSounds
            current: page.backend.alarmSound
            onPicked: id => page.backend.alarmSound = id
        }

        Item { Layout.fillHeight: true }
    }
}
