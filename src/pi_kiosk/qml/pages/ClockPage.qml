import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

// Home screen: big clock, with Alarm / Relax / Settings along the bottom.
Page {
    id: page
    required property var backend
    signal settingsRequested()

    // Dev aid: resident memory (see README, "Keeping it inside 512 MB").
    Label {
        anchors { top: parent.top; right: parent.right; margins: 12 }
        text: page.backend.memoryMb.toFixed(0) + " MB"
        font.pixelSize: 14
        opacity: 0.4
    }

    ColumnLayout {
        anchors { left: parent.left; right: parent.right; top: parent.top; bottom: buttons.top }
        spacing: 0

        Item { Layout.fillHeight: true }
        Label {
            Layout.alignment: Qt.AlignHCenter
            text: page.backend.time
            font.pixelSize: 190
            font.weight: Font.Light
        }
        Label {
            Layout.alignment: Qt.AlignHCenter
            text: page.backend.date
            font.pixelSize: 28
            opacity: 0.7
        }
        Item { Layout.fillHeight: true }
    }

    RowLayout {
        id: buttons
        anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter; bottomMargin: 24 }
        spacing: 24

        BigButton {
            accent: page.backend.alarmEnabled
            text: page.backend.alarmEnabled ? "Alarm " + page.backend.alarmTime : "Alarm off"
            onClicked: page.backend.alarmEnabled = !page.backend.alarmEnabled
        }
        BigButton {
            implicitWidth: 280
            implicitHeight: 104
            font.pixelSize: 34
            text: page.backend.relaxing ? "Stop" : "Relax"
            onClicked: page.backend.toggleRelax()
        }
        BigButton {
            accent: false
            text: "Settings"
            onClicked: page.settingsRequested()
        }
    }
}
