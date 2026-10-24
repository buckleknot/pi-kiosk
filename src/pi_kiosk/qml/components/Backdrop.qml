import QtQuick
import QtQuick.Controls.Material

// Full-bleed photo behind the UI (see display.py). When `source` changes, the new
// image loads off-screen and then crossfades over the old one.
Rectangle {
    id: backdrop
    property url source
    property real wash: 0.35  // pale/dark cover (by day) so text stays readable
    property int fadeDuration: 1200

    property Image front: layerA
    readonly property Image back: front === layerA ? layerB : layerA

    color: Material.backgroundColor

    component Layer: Image {
        id: layer
        anchors.fill: parent
        sourceSize: Qt.size(backdrop.width, backdrop.height)  // decode at screen size
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        opacity: 0
        onStatusChanged: if (status === Image.Ready && layer === backdrop.back) fade.start()
    }

    Layer { id: layerA }
    Layer { id: layerB }

    onSourceChanged: {
        fade.complete()
        fadeOut.stop()
        if (source == "") {  // no picture: fade the current one out to the plain colour
            fadeOut.target = front
            fadeOut.start()
            return
        }
        back.z = 1
        front.z = 0
        back.opacity = 0
        back.source = source
        if (back.status === Image.Ready)  // already cached: no statusChanged will come
            fade.start()
    }

    NumberAnimation {
        id: fadeOut
        property: "opacity"
        to: 0
        duration: backdrop.fadeDuration
    }

    NumberAnimation {
        id: fade
        target: backdrop.back
        property: "opacity"
        to: 1
        duration: backdrop.fadeDuration
        easing.type: Easing.InOutQuad
        onFinished: {
            const old = backdrop.front
            backdrop.front = backdrop.back
            old.source = ""  // free the old image
            old.opacity = 0
        }
    }

    Rectangle {
        anchors.fill: parent
        z: 2
        color: backdrop.color
        opacity: Theme.night ? 0 : backdrop.wash
    }
}
