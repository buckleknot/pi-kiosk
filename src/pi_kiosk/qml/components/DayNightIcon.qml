import QtQuick

// Sun or crescent moon, drawn on a Canvas so it needs no icon font on the Pi.
Canvas {
    id: icon
    property bool night
    property color color: "black"

    implicitWidth: 32
    implicitHeight: 32
    onNightChanged: requestPaint()
    onColorChanged: requestPaint()

    onPaint: {
        const ctx = getContext("2d")
        const cx = width / 2, cy = height / 2, r = Math.min(width, height) / 2
        ctx.reset()
        ctx.fillStyle = icon.color
        ctx.strokeStyle = icon.color
        if (night) {
            ctx.beginPath()
            ctx.arc(cx, cy, r * 0.8, 0, 2 * Math.PI)
            ctx.fill()
            ctx.globalCompositeOperation = "destination-out"  // bite out the crescent
            ctx.beginPath()
            ctx.arc(cx + r * 0.45, cy - r * 0.3, r * 0.68, 0, 2 * Math.PI)
            ctx.fill()
        } else {
            ctx.beginPath()
            ctx.arc(cx, cy, r * 0.42, 0, 2 * Math.PI)
            ctx.fill()
            ctx.lineWidth = Math.max(2, r * 0.14)
            ctx.lineCap = "round"
            for (let i = 0; i < 8; i++) {
                const a = i * Math.PI / 4
                ctx.beginPath()
                ctx.moveTo(cx + Math.cos(a) * r * 0.64, cy + Math.sin(a) * r * 0.64)
                ctx.lineTo(cx + Math.cos(a) * r * 0.94, cy + Math.sin(a) * r * 0.94)
                ctx.stroke()
            }
        }
    }
}
