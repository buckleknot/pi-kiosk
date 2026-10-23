import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

// Root window. Properties marked `required` are injected from Python via
// QQmlApplicationEngine.setInitialProperties() in app.py.
ApplicationWindow {
    id: root

    required property var backend
    required property bool kioskFullscreen

    visible: true
    title: "pi-kiosk"
    visibility: kioskFullscreen ? Window.FullScreen : Window.Windowed
    color: Theme.background

    // In windowed (dev) mode lock the size so the layout matches the Pi panel.
    minimumWidth: kioskFullscreen ? 0 : width
    maximumWidth: kioskFullscreen ? 100000 : width
    minimumHeight: kioskFullscreen ? 0 : height
    maximumHeight: kioskFullscreen ? 100000 : height

    header: ToolBar {
        height: 56
        background: Rectangle { color: Theme.surface }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            Label {
                text: "pi-kiosk"
                font.pixelSize: 24
                font.bold: true
                color: Theme.text
            }
            Item { Layout.fillWidth: true }
            Label {
                text: root.backend.memoryMb.toFixed(0) + " MB"
                font.pixelSize: 16
                color: Theme.muted
            }
            Label {
                text: root.backend.time
                font.pixelSize: 24
                color: Theme.text
                Layout.leftMargin: 16
            }
        }
    }

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 24

        Label {
            Layout.alignment: Qt.AlignHCenter
            text: root.backend.counter
            font.pixelSize: 96
            color: Theme.text
        }

        RowLayout {
            spacing: 24
            Layout.alignment: Qt.AlignHCenter
            BigButton {
                text: "Tap me"
                onClicked: root.backend.increment()
            }
            BigButton {
                text: "Reset"
                accent: false
                onClicked: root.backend.reset()
            }
        }
    }

    // Escape quits in dev; on the Pi there is no keyboard so this is harmless.
    Shortcut {
        sequence: "Esc"
        onActivated: Qt.quit()
    }
}
