import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import "components" as Comp

Window {
    id: root
    visible: true
    width: mainLayout.implicitWidth + 24
    height: mainLayout.implicitHeight + 24
    x: (Screen.width - width) / 2
    y: Screen.height - height - 40
    color: "transparent"
    title: "Alpha-OSK"

    // Keyboard state from Python bridge
    property bool shiftOn: keyboard ? keyboard.shiftActive : false
    property bool capsOn: keyboard ? keyboard.capsLockActive : false
    property bool ctrlOn: keyboard ? keyboard.ctrlActive : false
    property bool altOn: keyboard ? keyboard.altActive : false
    property bool winOn: keyboard ? keyboard.winActive : false
    property string layer: keyboard ? keyboard.currentLayer : "lower"
    property bool showNumbers: layer === "numbers"
    property bool showSymbols: layer === "symbols"
    
    // Predictions from hybrid engine
    property var predictions: []
    property bool predictionsLoading: false
    
    // Layout toggles (modular panels)
    property bool showFunctionRow: false
    property bool showNavigation: false
    property bool showNumpad: false
    property bool compactMode: false
    property bool showSettings: false
    property bool showPredictionSettings: false
    property bool showAccessibility: false
    
    // Prediction settings
    property bool llmEnabled: keyboard ? keyboard.llmEnabled : true
    property bool llmAvailable: keyboard ? keyboard.llmAvailable : false
    property int predictionCount: keyboard ? keyboard.predictionCount : 5
    property var predictionStats: ({totalWords: 0, uniqueWords: 0, userWords: 0})
    
    // Debug
    property bool showDebugPanel: false
    property var debugLog: []
    property string debugContext: ""

    // Sizing
    property real keyW: compactMode ? 50 : 56
    property real keyH: compactMode ? 44 : 50
    property real keySpacing: 3
    
    // ===== Color Theme System =====
    property string currentTheme: "dark"  // "dark", "light", "blue", "green", "purple"
    
    // Theme colors (computed based on currentTheme)
    property color themeBackground: {
        switch(currentTheme) {
            case "light": return "#e8e8e8"
            case "blue": return "#1a2a3a"
            case "green": return "#1a2a1a"
            case "purple": return "#2a1a3a"
            default: return "#1a1a1a"  // dark
        }
    }
    property color themeKeyColor: {
        switch(currentTheme) {
            case "light": return "#ffffff"
            case "blue": return "#2a4a6a"
            case "green": return "#2a4a2a"
            case "purple": return "#4a2a5a"
            default: return "#3a3a3a"
        }
    }
    property color themeKeyPressed: {
        switch(currentTheme) {
            case "light": return "#d0d0d0"
            case "blue": return "#3a6a9a"
            case "green": return "#3a6a3a"
            case "purple": return "#6a3a7a"
            default: return "#5a5a5a"
        }
    }
    property color themeTextColor: {
        switch(currentTheme) {
            case "light": return "#1a1a1a"
            default: return "#e0e0e0"
        }
    }
    property color themeAccent: {
        switch(currentTheme) {
            case "light": return "#0078d4"
            case "blue": return "#4a9eff"
            case "green": return "#4aff4a"
            case "purple": return "#bb66ff"
            default: return "#4a9eff"
        }
    }
    property color themeBorder: {
        switch(currentTheme) {
            case "light": return "#c0c0c0"
            default: return "#505050"
        }
    }

    // Update state when bridge emits signals
    Connections {
        target: keyboard
        function onShiftActiveChanged(active) { root.shiftOn = active }
        function onCapsLockActiveChanged(active) { root.capsOn = active }
        function onCtrlActiveChanged(active) { root.ctrlOn = active }
        function onAltActiveChanged(active) { root.altOn = active }
        function onWinActiveChanged(active) { root.winOn = active }
        function onCurrentLayerChanged(newLayer) { root.layer = newLayer }
        
        // Prediction updates
        function onPredictionsChanged(preds) { root.predictions = preds }
        function onPredictionsRefined(preds) { root.predictions = preds }
        function onPredictionLoading(loading) { root.predictionsLoading = loading }
        function onLlmAvailableChanged(available) { root.llmAvailable = available }
        function onLlmEnabledChanged(enabled) { root.llmEnabled = enabled }
        
        // Debug updates
        function onDebugLogChanged(log) { root.debugLog = log }
    }

    // Main background
    Rectangle {
        id: background
        anchors.fill: parent
        radius: 10
        color: root.themeBackground
        border.color: root.themeBorder
        border.width: 1
        
        Behavior on color { ColorAnimation { duration: 200 } }

        // Shadow
        Rectangle {
            anchors.fill: parent
            anchors.margins: -1
            radius: 11
            color: "transparent"
            border.color: Qt.rgba(0, 0, 0, 0.5)
            border.width: 1
            z: -1
        }

        // Drag handle
        MouseArea {
            id: dragArea
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 8
            cursorShape: Qt.SizeAllCursor
            
            property point dragStartPos
            property point windowStartPos
            
            onPressed: function(mouse) {
                dragStartPos = Qt.point(mouse.x, mouse.y)
                windowStartPos = Qt.point(root.x, root.y)
            }
            
            onPositionChanged: function(mouse) {
                if (pressed) {
                    var dx = mouse.x - dragStartPos.x
                    var dy = mouse.y - dragStartPos.y
                    root.x = windowStartPos.x + dx
                    root.y = windowStartPos.y + dy
                }
            }
            
            Row {
                anchors.centerIn: parent
                spacing: 4
                Repeater {
                    model: 5
                    Rectangle { width: 3; height: 3; radius: 1.5; color: "#444" }
                }
            }
        }

        RowLayout {
            id: mainLayout
            anchors.fill: parent
            anchors.margins: 8
            anchors.topMargin: 12
            spacing: 6

            // ===== Main Keyboard Section =====
            ColumnLayout {
                id: mainKeyboard
                spacing: 2

                // ===== Function Row (F1-F12) =====
                Comp.FunctionRow {
                    visible: root.showFunctionRow
                    Layout.alignment: Qt.AlignHCenter
                    keyW: root.keyW * 0.85
                    keyH: root.keyH * 0.7
                }

                // ===== Prediction Bar =====
                Row {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.bottomMargin: 4
                    spacing: 8

                    Repeater {
                        model: root.predictions.length > 0 ? root.predictions.slice(0, 5) : []
                        delegate: Rectangle {
                            width: Math.max(80, predText.implicitWidth + 28)
                            height: 36
                            radius: 8
                            color: predMouse.containsMouse ? "#3d4d5d" : "#2a3a4a"
                            border.color: predMouse.containsMouse ? "#6ab4ff" : "#4a9eff"
                            border.width: predMouse.containsMouse ? 2 : 1
                            
                            // Subtle gradient for depth
                            Rectangle {
                                anchors.fill: parent
                                anchors.margins: 1
                                radius: parent.radius - 1
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, 0.08) }
                                    GradientStop { position: 1.0; color: Qt.rgba(0, 0, 0, 0.05) }
                                }
                            }

                            Text {
                                id: predText
                                anchors.centerIn: parent
                                text: modelData
                                color: predMouse.containsMouse ? "#ffffff" : "#f0f0f0"
                                font.pixelSize: 15
                                font.weight: Font.Medium
                                font.family: "Ubuntu, Noto Sans, sans-serif"
                            }

                            MouseArea {
                                id: predMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: keyboard.pressPrediction(modelData)
                            }
                            
                            // Smooth hover animation
                            Behavior on color { ColorAnimation { duration: 100 } }
                            Behavior on border.color { ColorAnimation { duration: 100 } }
                        }
                    }
                    
                    // Prediction settings button
                    Rectangle {
                        width: 28
                        height: 28
                        radius: 5
                        color: predSettingsMouse.containsMouse ? "#3a3a3a" : "#252525"
                        border.color: root.showPredictionSettings ? "#4a9eff" : "#444"
                        
                        Text {
                            anchors.centerIn: parent
                            text: "⚡"
                            color: root.showPredictionSettings ? "#4a9eff" : "#888"
                            font.pixelSize: 14
                        }
                        
                        MouseArea {
                            id: predSettingsMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: {
                                root.showPredictionSettings = !root.showPredictionSettings
                                if (root.showPredictionSettings) {
                                    background.refreshPredictionStats()
                                }
                            }
                        }
                    }

                    // Accessibility settings button
                    Rectangle {
                        width: 28
                        height: 28
                        radius: 5
                        color: accessMouse.containsMouse ? "#3a3a3a" : "#252525"
                        border.color: root.showAccessibility ? "#5a8a5a" : "#444"
                        
                        Text {
                            anchors.centerIn: parent
                            text: "♿"
                            color: root.showAccessibility ? "#5a8a5a" : "#888"
                            font.pixelSize: 14
                        }
                        
                        MouseArea {
                            id: accessMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: root.showAccessibility = !root.showAccessibility
                        }
                    }

                    // Layout settings button
                    Rectangle {
                        width: 28
                        height: 28
                        radius: 5
                        color: settingsMouse.containsMouse ? "#3a3a3a" : "#252525"
                        border.color: root.showSettings ? "#4a9eff" : "#444"
                        
                        Text {
                            anchors.centerIn: parent
                            text: "⚙"
                            color: root.showSettings ? "#4a9eff" : "#888"
                            font.pixelSize: 14
                        }
                        
                        MouseArea {
                            id: settingsMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: root.showSettings = !root.showSettings
                        }
                    }

                    // Close button
                    Rectangle {
                        width: 28
                        height: 28
                        radius: 5
                        color: closeMouse.containsMouse ? "#5a2020" : "#252525"
                        border.color: "#444"

                        Text {
                            anchors.centerIn: parent
                            text: "✕"
                            color: closeMouse.containsMouse ? "#ff6666" : "#888"
                            font.pixelSize: 12
                        }

                        MouseArea {
                            id: closeMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: Qt.quit()
                        }
                    }
                }

                // ===== Number Row =====
                Row {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: root.keySpacing

                    // Backtick/Tilde
                    Comp.KeyButton {
                        keyText: "`"
                        displayText: root.shiftOn ? "~" : "`"
                        keyWidth: root.keyW
                        keyHeight: root.keyH - 4
                        fontSize: 14
                        keyColor: "#2a2a2a"
                        onKeyPressed: keyboard.pressKey(root.shiftOn ? "~" : "`")
                    }

                    Repeater {
                        model: root.shiftOn
                            ? ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")"]
                            : ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
                        Comp.KeyButton {
                            keyText: modelData
                            displayText: modelData
                            keyWidth: root.keyW
                            keyHeight: root.keyH - 4
                            fontSize: 13
                            keyColor: "#2a2a2a"
                            onKeyPressed: keyboard.pressKey(modelData)
                        }
                    }

                    // Minus/Underscore
                    Comp.KeyButton {
                        keyText: "-"
                        displayText: root.shiftOn ? "_" : "-"
                        keyWidth: root.keyW
                        keyHeight: root.keyH - 4
                        fontSize: 14
                        keyColor: "#2a2a2a"
                        onKeyPressed: keyboard.pressKey(root.shiftOn ? "_" : "-")
                    }

                    // Backspace
                    Comp.KeyButton {
                        keyText: "backspace"
                        displayText: "⌫"
                        keyWidth: root.keyW * 1.5
                        keyHeight: root.keyH - 4
                        fontSize: 16
                        isSpecial: true
                        keyColor: "#333"
                        onKeyPressed: keyboard.pressSpecialKey("backspace")
                    }
                }

                // ===== QWERTY Row =====
                Row {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: root.keySpacing

                    Comp.KeyButton {
                        keyText: "tab"
                        displayText: "Tab"
                        keyWidth: root.keyW * 1.3
                        keyHeight: root.keyH
                        fontSize: 11
                        isSpecial: true
                        keyColor: "#333"
                        onKeyPressed: keyboard.pressSpecialKey("tab")
                    }

                    Repeater {
                        model: ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"]
                        Comp.KeyButton {
                            keyText: modelData
                            displayText: root.shiftOn ? modelData.toUpperCase() : modelData
                            keyWidth: root.keyW
                            keyHeight: root.keyH
                            onKeyPressed: keyboard.pressKey(modelData)
                        }
                    }

                    // Brackets
                    Comp.KeyButton {
                        keyText: "["
                        displayText: root.shiftOn ? "{" : "["
                        keyWidth: root.keyW
                        keyHeight: root.keyH
                        fontSize: 14
                        keyColor: "#2a2a2a"
                        onKeyPressed: keyboard.pressKey(root.shiftOn ? "{" : "[")
                    }
                    Comp.KeyButton {
                        keyText: "]"
                        displayText: root.shiftOn ? "}" : "]"
                        keyWidth: root.keyW
                        keyHeight: root.keyH
                        fontSize: 14
                        keyColor: "#2a2a2a"
                        onKeyPressed: keyboard.pressKey(root.shiftOn ? "}" : "]")
                    }
                    Comp.KeyButton {
                        keyText: "\\"
                        displayText: root.shiftOn ? "|" : "\\"
                        keyWidth: root.keyW
                        keyHeight: root.keyH
                        fontSize: 14
                        keyColor: "#2a2a2a"
                        onKeyPressed: keyboard.pressKey(root.shiftOn ? "|" : "\\")
                    }
                }

                // ===== Home Row =====
                Row {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: root.keySpacing

                    Comp.KeyButton {
                        keyText: "caps"
                        displayText: "Caps"
                        keyWidth: root.keyW * 1.6
                        keyHeight: root.keyH
                        fontSize: 11
                        isSpecial: true
                        isActive: root.capsOn
                        keyColor: "#333"
                        onKeyPressed: keyboard.toggleCapsLock()
                    }

                    Repeater {
                        model: ["a", "s", "d", "f", "g", "h", "j", "k", "l"]
                        Comp.KeyButton {
                            keyText: modelData
                            displayText: root.shiftOn ? modelData.toUpperCase() : modelData
                            keyWidth: root.keyW
                            keyHeight: root.keyH
                            onKeyPressed: keyboard.pressKey(modelData)
                        }
                    }

                    // Semicolon, Quote
                    Comp.KeyButton {
                        keyText: ";"
                        displayText: root.shiftOn ? ":" : ";"
                        keyWidth: root.keyW
                        keyHeight: root.keyH
                        fontSize: 14
                        keyColor: "#2a2a2a"
                        onKeyPressed: keyboard.pressKey(root.shiftOn ? ":" : ";")
                    }
                    Comp.KeyButton {
                        keyText: "'"
                        displayText: root.shiftOn ? "\"" : "'"
                        keyWidth: root.keyW
                        keyHeight: root.keyH
                        fontSize: 14
                        keyColor: "#2a2a2a"
                        onKeyPressed: keyboard.pressKey(root.shiftOn ? "\"" : "'")
                    }

                    Comp.KeyButton {
                        keyText: "return"
                        displayText: "Enter"
                        keyWidth: root.keyW * 1.8
                        keyHeight: root.keyH
                        fontSize: 11
                        isSpecial: true
                        keyColor: "#2a5a2a"
                        onKeyPressed: keyboard.pressSpecialKey("return")
                    }
                }

                // ===== Bottom Alpha Row =====
                Row {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: root.keySpacing

                    Comp.KeyButton {
                        keyText: "shift"
                        displayText: "⇧ Shift"
                        keyWidth: root.keyW * 2
                        keyHeight: root.keyH
                        fontSize: 11
                        isSpecial: true
                        isActive: root.shiftOn
                        keyColor: "#333"
                        onKeyPressed: keyboard.toggleShift()
                    }

                    Repeater {
                        model: ["z", "x", "c", "v", "b", "n", "m"]
                        Comp.KeyButton {
                            keyText: modelData
                            displayText: root.shiftOn ? modelData.toUpperCase() : modelData
                            keyWidth: root.keyW
                            keyHeight: root.keyH
                            onKeyPressed: keyboard.pressKey(modelData)
                        }
                    }

                    // Comma, Period, Slash
                    Comp.KeyButton {
                        keyText: ","
                        displayText: root.shiftOn ? "<" : ","
                        keyWidth: root.keyW
                        keyHeight: root.keyH
                        fontSize: 14
                        keyColor: "#2a2a2a"
                        onKeyPressed: keyboard.pressKey(root.shiftOn ? "<" : ",")
                    }
                    Comp.KeyButton {
                        keyText: "."
                        displayText: root.shiftOn ? ">" : "."
                        keyWidth: root.keyW
                        keyHeight: root.keyH
                        fontSize: 14
                        keyColor: "#2a2a2a"
                        onKeyPressed: keyboard.pressKey(root.shiftOn ? ">" : ".")
                    }
                    Comp.KeyButton {
                        keyText: "/"
                        displayText: root.shiftOn ? "?" : "/"
                        keyWidth: root.keyW
                        keyHeight: root.keyH
                        fontSize: 14
                        keyColor: "#2a2a2a"
                        onKeyPressed: keyboard.pressKey(root.shiftOn ? "?" : "/")
                    }

                    Comp.KeyButton {
                        keyText: "shift"
                        displayText: "⇧ Shift"
                        keyWidth: root.keyW * 2.3
                        keyHeight: root.keyH
                        fontSize: 11
                        isSpecial: true
                        isActive: root.shiftOn
                        keyColor: "#333"
                        onKeyPressed: keyboard.toggleShift()
                    }
                }

                // ===== Space Bar Row =====
                Row {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: root.keySpacing

                    Comp.KeyButton {
                        keyText: "ctrl"
                        displayText: "Ctrl"
                        keyWidth: root.keyW * 1.2
                        keyHeight: root.keyH
                        fontSize: 11
                        isSpecial: true
                        isActive: root.ctrlOn
                        keyColor: "#333"
                        onKeyPressed: keyboard.toggleCtrl()
                    }

                    Comp.KeyButton {
                        keyText: "win"
                        displayText: "⊞"
                        keyWidth: root.keyW
                        keyHeight: root.keyH
                        fontSize: 16
                        isSpecial: true
                        isActive: root.winOn
                        keyColor: "#333"
                        onKeyPressed: keyboard.toggleWin()
                    }

                    Comp.KeyButton {
                        keyText: "alt"
                        displayText: "Alt"
                        keyWidth: root.keyW * 1.1
                        keyHeight: root.keyH
                        fontSize: 11
                        isSpecial: true
                        isActive: root.altOn
                        keyColor: "#333"
                        onKeyPressed: keyboard.toggleAlt()
                    }

                    // Space bar
                    Comp.KeyButton {
                        keyText: "space"
                        displayText: ""
                        keyWidth: root.keyW * 6
                        keyHeight: root.keyH
                        keyColor: "#3a3a3a"
                        onKeyPressed: keyboard.pressSpecialKey("space")
                    }

                    Comp.KeyButton {
                        keyText: "alt"
                        displayText: "Alt"
                        keyWidth: root.keyW * 1.1
                        keyHeight: root.keyH
                        fontSize: 11
                        isSpecial: true
                        isActive: root.altOn
                        keyColor: "#333"
                        onKeyPressed: keyboard.toggleAlt()
                    }

                    Comp.KeyButton {
                        keyText: "ctrl"
                        displayText: "Ctrl"
                        keyWidth: root.keyW * 1.2
                        keyHeight: root.keyH
                        fontSize: 11
                        isSpecial: true
                        isActive: root.ctrlOn
                        keyColor: "#333"
                        onKeyPressed: keyboard.toggleCtrl()
                    }

                    // Compact arrow keys
                    Row {
                        spacing: 1
                        Comp.KeyButton {
                            keyText: "left"
                            displayText: "◀"
                            keyWidth: root.keyW * 0.8
                            keyHeight: root.keyH
                            fontSize: 12
                            isSpecial: true
                            keyColor: "#333"
                            onKeyPressed: keyboard.pressSpecialKey("left")
                        }
                        Column {
                            spacing: 1
                            Comp.KeyButton {
                                keyText: "up"
                                displayText: "▲"
                                keyWidth: root.keyW * 0.8
                                keyHeight: root.keyH / 2 - 1
                                fontSize: 10
                                isSpecial: true
                                keyColor: "#333"
                                onKeyPressed: keyboard.pressSpecialKey("up")
                            }
                            Comp.KeyButton {
                                keyText: "down"
                                displayText: "▼"
                                keyWidth: root.keyW * 0.8
                                keyHeight: root.keyH / 2 - 1
                                fontSize: 10
                                isSpecial: true
                                keyColor: "#333"
                                onKeyPressed: keyboard.pressSpecialKey("down")
                            }
                        }
                        Comp.KeyButton {
                            keyText: "right"
                            displayText: "▶"
                            keyWidth: root.keyW * 0.8
                            keyHeight: root.keyH
                            fontSize: 12
                            isSpecial: true
                            keyColor: "#333"
                            onKeyPressed: keyboard.pressSpecialKey("right")
                        }
                    }
                }
            }

            // ===== Navigation Panel (toggleable) =====
            Rectangle {
                visible: root.showNavigation
                Layout.fillHeight: true
                width: 1
                color: "#333"
            }
            
            Comp.NavigationPanel {
                visible: root.showNavigation
                keyW: root.keyW * 0.9
                keyH: root.keyH * 0.9
            }

            // ===== Numpad (toggleable) =====
            Rectangle {
                visible: root.showNumpad
                Layout.fillHeight: true
                width: 1
                color: "#333"
            }
            
            Comp.NumpadPanel {
                visible: root.showNumpad
                keyW: root.keyW * 0.9
                keyH: root.keyH * 0.9
            }
        }

        // Settings Panel (overlay)
        Comp.SettingsPanel {
            id: settingsPanel
            visible: root.showSettings
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 8
            
            showFunctionRow: root.showFunctionRow
            showNavigation: root.showNavigation
            showNumpad: root.showNumpad
            compactMode: root.compactMode
            currentTheme: root.currentTheme
            
            onSettingChanged: function(setting, value) {
                if (setting === "functionRow") root.showFunctionRow = value
                else if (setting === "navigation") root.showNavigation = value
                else if (setting === "numpad") root.showNumpad = value
                else if (setting === "compact") root.compactMode = value
                else if (setting === "theme") root.currentTheme = value
            }
            
            onCloseRequested: root.showSettings = false
        }
        
        // Prediction Settings Panel (overlay)
        Comp.PredictionSettingsPanel {
            id: predictionSettingsPanel
            visible: root.showPredictionSettings
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.margins: 8
            
            llmEnabled: root.llmEnabled
            llmAvailable: root.llmAvailable
            predictionCount: root.predictionCount
            totalWords: root.predictionStats.total_words || 0
            uniqueWords: root.predictionStats.unique_words || 0
            userWords: root.predictionStats.user_words || 0
            debugMode: root.showDebugPanel
            
            onSettingChanged: function(setting, value) {
                if (setting === "llmEnabled" && keyboard) {
                    keyboard.setLlmEnabled(value)
                    root.llmEnabled = value
                } else if (setting === "predictionCount" && keyboard) {
                    keyboard.setPredictionCount(value)
                    root.predictionCount = value
                } else if (setting === "save" && keyboard) {
                    keyboard.savePredictionModel()
                } else if (setting === "reload" && keyboard) {
                    keyboard.reloadDictionary()
                    background.refreshPredictionStats()
                } else if (setting === "clearUserData" && keyboard) {
                    keyboard.clearUserData()
                    background.refreshPredictionStats()
                } else if (setting === "importFile" && keyboard) {
                    var path = value.replace("~", "/home/owen")
                    keyboard.importTextFile(path)
                    background.refreshPredictionStats()
                } else if (setting === "importFolder" && keyboard) {
                    var folderPath = value.replace("~", "/home/owen")
                    keyboard.importFolder(folderPath)
                    background.refreshPredictionStats()
                } else if (setting === "debug") {
                    root.showDebugPanel = value
                    if (keyboard) keyboard.setDebugMode(value)
                }
            }
            
            onCloseRequested: root.showPredictionSettings = false
        }
        
        // Accessibility Panel (overlay)
        Comp.AccessibilityPanel {
            id: accessibilityPanel
            visible: root.showAccessibility
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.margins: 8
            
            onProfileChanged: function(profileName) {
                console.log("Accessibility profile changed to:", profileName)
            }
            
            onCloseRequested: root.showAccessibility = false
        }
        
        // Debug Panel
        Comp.DebugPanel {
            id: debugPanelComp
            visible: root.showDebugPanel
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.margins: 8
            
            logEntries: root.debugLog
            currentContext: root.debugContext
            currentPredictions: root.predictions
            
            onCloseRequested: {
                root.showDebugPanel = false
                if (keyboard) keyboard.setDebugMode(false)
            }
            
            onClearLog: {
                if (keyboard) keyboard.clearDebugLog()
            }
        }
        
        // Function to refresh prediction stats
        function refreshPredictionStats() {
            if (keyboard) {
                root.predictionStats = keyboard.getPredictionStats()
            }
        }

        // No synth tool warning
        Rectangle {
            visible: keyboard ? !keyboard.synthAvailable : true
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottomMargin: 2
            width: warningText.width + 12
            height: 18
            radius: 3
            color: "#442200"
            border.color: "#664400"

            Text {
                id: warningText
                anchors.centerIn: parent
                text: "xdotool not found"
                color: "#ffaa44"
                font.pixelSize: 9
            }
        }
    }
}
