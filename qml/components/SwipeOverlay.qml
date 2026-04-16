import QtQuick 2.15

/*
 * SwipeOverlay
 * ============
 * Transparent input layer that sits on top of the main keyboard rows.
 * When `enabled` (driven by the user's swipe-typing setting), it
 * intercepts all mouse activity in the keyboard area and decides per
 * gesture whether it was a tap or a swipe:
 *
 *   • Tap   → distance < swipeThreshold → look up the KeyButton at the
 *             release point and call its keyPressed signal directly
 *             (delayed activation — fires on release, not press).
 *   • Swipe → distance ≥ swipeThreshold → forward the entire path to
 *             the Python bridge for shape-matching against the dictionary.
 *
 * When `enabled` is false the MouseArea is invisible to events
 * (visible:false → no hit testing) so KeyButtons handle their own
 * presses normally.
 */

Item {
    id: swipeRoot
    anchors.fill: parent
    visible: enabled        // hides AND disables hit testing when off
    z: 50                   // above KeyButtons but below dialogs/popups

    property bool enabled: false
    property real swipeThreshold: 60   // pixels — below this, treat as tap
    property var keyboardBridge: null   // injected by Main.qml
    property var keyRegistry: []        // [{ item, kd }] — populated by Main.qml

    // Recorded points for the current gesture, in overlay-local coords.
    property var _points: []
    property bool _isSwipe: false

    signal swipeStarted()
    signal swipeEnded()

    // Ribbon overlay — light trail of the user's swipe path
    Canvas {
        id: trail
        anchors.fill: parent
        visible: swipeRoot._isSwipe
        opacity: 0.6

        property var pts: []

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            if (pts.length < 2) return
            ctx.lineCap = "round"
            ctx.lineJoin = "round"
            ctx.lineWidth = 4
            ctx.strokeStyle = "#4a9eff"
            ctx.beginPath()
            ctx.moveTo(pts[0].x, pts[0].y)
            for (var i = 1; i < pts.length; i++) {
                ctx.lineTo(pts[i].x, pts[i].y)
            }
            ctx.stroke()
        }
    }

    MouseArea {
        id: ma
        anchors.fill: parent
        hoverEnabled: false
        preventStealing: true        // hold the gesture across the full swipe

        onPressed: function(mouse) {
            swipeRoot._points = [{ x: mouse.x, y: mouse.y }]
            swipeRoot._isSwipe = false
            trail.pts = swipeRoot._points
            trail.requestPaint()
        }

        onPositionChanged: function(mouse) {
            swipeRoot._points.push({ x: mouse.x, y: mouse.y })
            // Promote to swipe once total movement exceeds the threshold.
            if (!swipeRoot._isSwipe) {
                var first = swipeRoot._points[0]
                var dx = mouse.x - first.x
                var dy = mouse.y - first.y
                if (Math.sqrt(dx * dx + dy * dy) > swipeRoot.swipeThreshold) {
                    swipeRoot._isSwipe = true
                    swipeRoot.swipeStarted()
                }
            }
            if (swipeRoot._isSwipe) {
                trail.pts = swipeRoot._points
                trail.requestPaint()
            }
        }

        onReleased: function(mouse) {
            if (swipeRoot._isSwipe) {
                if (swipeRoot.keyboardBridge) {
                    var raw = swipeRoot._points.map(function(p) { return [p.x, p.y] })
                    swipeRoot.keyboardBridge.processSwipe(raw)
                }
                swipeRoot.swipeEnded()
            } else {
                // Treat as a tap — find the KeyButton under the release point
                // and trigger its keyPressed signal.
                var hit = swipeRoot._findKeyAt(mouse.x, mouse.y)
                if (hit && hit.item && hit.item.keyPressed) {
                    hit.item.keyPressed()
                }
            }
            swipeRoot._isSwipe = false
            swipeRoot._points = []
            trail.pts = []
            trail.requestPaint()
        }

        onCanceled: {
            swipeRoot._isSwipe = false
            swipeRoot._points = []
            trail.pts = []
            trail.requestPaint()
        }
    }

    function _findKeyAt(x, y) {
        for (var i = 0; i < keyRegistry.length; i++) {
            var entry = keyRegistry[i]
            if (!entry || !entry.item) continue
            var p = swipeRoot.mapFromItem(entry.item, 0, 0)
            if (x >= p.x && x <= p.x + entry.item.width
                && y >= p.y && y <= p.y + entry.item.height) {
                return entry
            }
        }
        return null
    }
}
