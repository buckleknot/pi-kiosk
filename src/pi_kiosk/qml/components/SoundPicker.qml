import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

// One settings row: label, drop-down of sounds and a Preview/Stop button.
// `sounds` is the backend's list of {id, name}; `kind` is "ambient" or "alarm".
RowLayout {
    id: row
    required property var backend
    property string label
    property string kind
    property var sounds: []
    property string current
    signal picked(string id)

    spacing: 16

    Label {
        Layout.preferredWidth: 150
        text: row.label
        font.pixelSize: 20
    }

    ComboBox {
        id: combo
        Layout.fillWidth: true
        Layout.preferredHeight: 60
        font.pixelSize: 20
        model: row.sounds
        textRole: "name"
        valueRole: "id"
        // ComboBox ignores the inherited foreground, so its text would be white at night.
        Material.foreground: Theme.night ? Theme.nightText : undefined
        Component.onCompleted: currentIndex = indexOfValue(row.current)
        onActivated: row.picked(currentValue)

        // Finger-sized rows. At night bold marks the current row: Material's grey
        // highlight would be the brightest thing on screen.
        delegate: ItemDelegate {
            required property int index
            width: ListView.view.width
            height: 60
            text: combo.textAt(index)
            font.pixelSize: 20
            font.bold: Theme.night && combo.highlightedIndex === index
            highlighted: !Theme.night && combo.highlightedIndex === index
        }
    }

    BigButton {
        readonly property bool playing: row.backend.previewing === row.kind + "/" + combo.currentValue
        implicitWidth: 150
        implicitHeight: 72
        font.pixelSize: 22
        accent: false
        text: playing ? "Stop" : "Preview"
        onClicked: playing ? row.backend.stopPreview()
                           : row.backend.previewSound(row.kind, combo.currentValue)
    }
}
