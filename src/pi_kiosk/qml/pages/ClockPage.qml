import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts
import "../components"

// Home screen: big clock, with Alarm / Relax / Settings along the bottom,
// day/night override + brightness down the left-hand side and volume down the right.
Page {
    id: page
    required property var backend
    signal settingsRequested()

    background: Item {}  // transparent, so the window's Backdrop photo shows through

    // Dev aid: resident memory (see README, "Keeping it inside 512 MB").
    Label {
        anchors { top: parent.top; horizontalCenter: parent.horizontalCenter; topMargin: 8 }
        text: page.backend.memoryMb.toFixed(0) + " MB"
        font.pixelSize: 14
        opacity: 0.4
    }

    // Left: day/night override, then brightness (day and night each keep their own).
    ColumnLayout {
        anchors {
            left: parent.left; top: parent.top; bottom: buttons.top
            leftMargin: 16; topMargin: 16; bottomMargin: 12
        }
        spacing: 2

        RoundButton {
            id: dayNight
            Layout.alignment: Qt.AlignHCenter
            implicitWidth: 72
            implicitHeight: 72
            Material.background: Theme.night ? Theme.nightSurface : Theme.buttonTint
            onClicked: page.backend.toggleNight()
            contentItem: Item {
                DayNightIcon {
                    anchors.centerIn: parent
                    width: 30
                    height: 30
                    night: Theme.night
                    color: dayNight.Material.foreground
                }
            }
        }
        Label {
            Layout.alignment: Qt.AlignHCenter
            text: page.backend.nightOverridden
                  ? "until " + (Theme.night ? page.backend.nightEnd : page.backend.nightStart)
                  : "auto"
            font.pixelSize: 13
            opacity: 0.6
        }

        VerticalSlider {
            id: brightness
            Layout.alignment: Qt.AlignHCenter
            Layout.fillHeight: true
            Layout.topMargin: 8
            from: 5
            value: page.backend.brightness
            onMoved: page.backend.brightness = value
        }
        Label {
            Layout.alignment: Qt.AlignHCenter
            text: Math.round(brightness.value) + "%"
            font.pixelSize: 14
            opacity: 0.6
        }
    }

    // Right: volume.
    ColumnLayout {
        anchors {
            right: parent.right; top: parent.top; bottom: buttons.top
            rightMargin: 16; topMargin: 16; bottomMargin: 12
        }
        spacing: 2

        Item {  // same height as the day/night button opposite, so the sliders line up
            Layout.alignment: Qt.AlignHCenter
            implicitWidth: 72
            implicitHeight: 72
            VolumeIcon {
                anchors.centerIn: parent
                width: 30
                height: 30
                color: page.Material.foreground
                opacity: 0.7
            }
        }
        Label {
            Layout.alignment: Qt.AlignHCenter
            text: "volume"
            font.pixelSize: 13
            opacity: 0.6
        }

        VerticalSlider {
            id: volume
            Layout.alignment: Qt.AlignHCenter
            Layout.fillHeight: true
            Layout.topMargin: 8
            value: page.backend.volume
            onMoved: page.backend.volume = value
        }
        Label {
            Layout.alignment: Qt.AlignHCenter
            text: Math.round(volume.value) + "%"
            font.pixelSize: 14
            opacity: 0.6
        }
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
