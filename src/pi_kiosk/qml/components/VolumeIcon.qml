import QtQuick

// Speaker with sound waves, drawn on a Canvas like DayNightIcon.
Canvas {
    id: icon
    property color color: "black"

    implicitWidth: 32
    implicitHeight: 32
    onColorChanged: requestPaint()

    onPaint: {
        const ctx = getContext("2d")
        const s = Math.min(width, height)
        ctx.reset()
        ctx.fillStyle = icon.color
        ctx.strokeStyle = icon.color
        ctx.beginPath()  // speaker body and cone
        ctx.moveTo(s * 0.08, s * 0.38)
        ctx.lineTo(s * 0.28, s * 0.38)
        ctx.lineTo(s * 0.52, s * 0.16)
        ctx.lineTo(s * 0.52, s * 0.84)
        ctx.lineTo(s * 0.28, s * 0.62)
        ctx.lineTo(s * 0.08, s * 0.62)
        ctx.closePath()
        ctx.fill()
        ctx.lineWidth = Math.max(2, s * 0.08)
        ctx.lineCap = "round"
        for (const r of [0.2, 0.36]) {  // two waves
            ctx.beginPath()
            ctx.arc(s * 0.52, s * 0.5, s * r, -Math.PI / 4, Math.PI / 4)
            ctx.stroke()
        }
    }
}
