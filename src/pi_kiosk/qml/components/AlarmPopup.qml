import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Full-screen overlay while the alarm rings; it sits above whichever page is open.
Popup {
    id: popup
    required property var backend

    parent: Overlay.overlay
    width: parent.width
    height: parent.height
    padding: 0
    modal: true
    closePolicy: Popup.NoAutoClose
    visible: popup.backend.alarmRinging
    background: Backdrop { source: popup.backend.backgroundSource }
    Overlay.modal: Item {}  // full screen already; no dimming layer needed

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 16

        Label {
            Layout.alignment: Qt.AlignHCenter
            text: popup.backend.time
            font.pixelSize: 150
            font.weight: Font.Light
        }

        Label {
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 24
            text: "Alarm"
            font.pixelSize: 32
            opacity: 0.7
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 32
            BigButton {
                implicitWidth: 260
                implicitHeight: 104
                accent: false
                text: "Snooze 9 min"
                onClicked: popup.backend.snoozeAlarm()
            }
            BigButton {
                implicitWidth: 260
                implicitHeight: 104
                text: "Stop"
                onClicked: popup.backend.stopAlarm()
            }
        }
    }
}
