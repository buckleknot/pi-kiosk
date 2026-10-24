import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import "components"
import "pages"

// Root window. Properties marked `required` are injected from Python via
// QQmlApplicationEngine.setInitialProperties() in app.py.
ApplicationWindow {
    id: root

    required property var backend
    required property bool kioskFullscreen

    visible: true
    title: "pi-kiosk"
    visibility: kioskFullscreen ? Window.FullScreen : Window.Windowed

    // In windowed (dev) mode lock the size so the layout matches the Pi panel.
    minimumWidth: kioskFullscreen ? 0 : width
    maximumWidth: kioskFullscreen ? 100000 : width
    minimumHeight: kioskFullscreen ? 0 : height
    maximumHeight: kioskFullscreen ? 100000 : height

    // Day: stock Material. Night: dim red on black. Inherited by every control.
    Binding { target: Theme; property: "night"; value: root.backend.nightMode }
    Material.theme: Theme.night ? Material.Dark : Material.Light
    Material.accent: Theme.night ? Theme.nightText : Material.Blue
    Material.background: Theme.night ? Theme.nightBackground : undefined
    Material.foreground: Theme.night ? Theme.nightText : undefined

    StackView {
        id: stack
        anchors.fill: parent
        initialItem: ClockPage {
            backend: root.backend
            onSettingsRequested: stack.push(configPage)
        }
    }

    Component {
        id: configPage
        ConfigPage {
            backend: root.backend
            onBackRequested: stack.pop()
        }
    }

    AlarmPopup { backend: root.backend }

    // Escape quits in dev; on the Pi there is no keyboard so this is harmless.
    Shortcut {
        sequence: "Esc"
        onActivated: Qt.quit()
    }
}
