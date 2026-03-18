import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15

Item {
    id: unifiedSettings
    
    // Layout properties
    property bool showFunctionRow: true
    property bool showNavigation: false
    property bool showNumpad: false
    property bool compactMode: false
    property string currentTheme: "dark"
    
    // Prediction properties
    property bool llmEnabled: true
    property bool llmAvailable: false
    property int predictionCount: 5
    property int totalWords: 0
    property int uniqueWords: 0
    property int userWords: 0
    property bool debugMode: false
    
    // Accessibility properties
    property string currentProfile: "normal"
    property var profiles: []
    
    signal settingChanged(string setting, var value)
    signal closeRequested()
    
    implicitWidth: 320
    implicitHeight: Math.min(450, contentColumn.implicitHeight + 40)
    
    Component.onCompleted: {
        if (keyboard) {
            profiles = keyboard.getAccessibilityProfiles()
            currentProfile = keyboard.getCurrentProfile()
        }
    }
    
    Rectangle {
        anchors.fill: parent
        color: "#1e1e1e"
        radius: 10
        border.color: "#444"
        border.width: 1
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 0
            
            // Header
            RowLayout {
                Layout.fillWidth: true
                Layout.bottomMargin: 8
                
                Text {
                    text: "⚙ Settings"
                    color: "#fff"
                    font.pixelSize: 16
                    font.bold: true
                }
                
                Item { Layout.fillWidth: true }
                
                Rectangle {
                    width: 26
                    height: 26
                    radius: 5
                    color: closeArea.containsMouse ? "#5a2020" : "transparent"
                    
                    Text {
                        anchors.centerIn: parent
                        text: "✕"
                        color: closeArea.containsMouse ? "#ff6666" : "#888"
                        font.pixelSize: 14
                    }
                    
                    MouseArea {
                        id: closeArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: unifiedSettings.closeRequested()
                    }
                }
            }
            
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#444"
            }
            
            // Scrollable content
            ScrollView {
                id: scrollArea
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                
                ScrollBar.vertical.policy: ScrollBar.AsNeeded
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                
                ColumnLayout {
                    id: contentColumn
                    width: scrollArea.availableWidth
                    spacing: 12
                    
                    // ===== LAYOUT SECTION =====
                    SettingsSection {
                        title: "Layout"
                        Layout.fillWidth: true
                        
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            
                            SettingsToggle {
                                Layout.fillWidth: true
                                text: "Function Keys (F1-F12)"
                                checked: unifiedSettings.showFunctionRow
                                onToggled: function(c) { unifiedSettings.settingChanged("functionRow", c) }
                            }
                            
                            SettingsToggle {
                                Layout.fillWidth: true
                                text: "Navigation Keys"
                                checked: unifiedSettings.showNavigation
                                onToggled: function(c) { unifiedSettings.settingChanged("navigation", c) }
                            }
                            
                            SettingsToggle {
                                Layout.fillWidth: true
                                text: "Number Pad"
                                checked: unifiedSettings.showNumpad
                                onToggled: function(c) { unifiedSettings.settingChanged("numpad", c) }
                            }
                            
                            SettingsToggle {
                                Layout.fillWidth: true
                                text: "Compact Mode"
                                checked: unifiedSettings.compactMode
                                onToggled: function(c) { unifiedSettings.settingChanged("compact", c) }
                            }
                        }
                    }
                    
                    // ===== THEME SECTION =====
                    SettingsSection {
                        title: "Theme"
                        Layout.fillWidth: true
                        
                        Row {
                            spacing: 8
                            
                            Repeater {
                                model: [
                                    { name: "dark", color: "#1a1a1a", border: "#4a9eff" },
                                    { name: "light", color: "#e8e8e8", border: "#0078d4" },
                                    { name: "blue", color: "#1a2a3a", border: "#4a9eff" },
                                    { name: "green", color: "#1a2a1a", border: "#4aff4a" },
                                    { name: "purple", color: "#2a1a3a", border: "#bb66ff" }
                                ]
                                
                                Rectangle {
                                    width: 32
                                    height: 32
                                    radius: 6
                                    color: modelData.color
                                    border.color: unifiedSettings.currentTheme === modelData.name ? modelData.border : "#555"
                                    border.width: unifiedSettings.currentTheme === modelData.name ? 2 : 1
                                    
                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: unifiedSettings.settingChanged("theme", modelData.name)
                                    }
                                    
                                    Text {
                                        anchors.centerIn: parent
                                        text: unifiedSettings.currentTheme === modelData.name ? "✓" : ""
                                        color: modelData.name === "light" ? "#333" : "#fff"
                                        font.pixelSize: 14
                                        font.bold: true
                                    }
                                }
                            }
                        }
                    }
                    
                    // ===== PREDICTION SECTION =====
                    SettingsSection {
                        title: "Prediction"
                        Layout.fillWidth: true
                        
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            
                            SettingsToggle {
                                Layout.fillWidth: true
                                text: "Use AI (DistilGPT-2)"
                                checked: unifiedSettings.llmEnabled
                                enabled: unifiedSettings.llmAvailable
                                onToggled: function(c) { unifiedSettings.settingChanged("llmEnabled", c) }
                            }
                            
                            Text {
                                text: unifiedSettings.llmAvailable 
                                    ? "✓ Model loaded" 
                                    : "⚠ Model not available"
                                color: unifiedSettings.llmAvailable ? "#4a9eff" : "#666"
                                font.pixelSize: 10
                            }
                            
                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: "#333"
                            }
                            
                            // Stats
                            Text {
                                text: "Vocabulary: " + unifiedSettings.totalWords.toLocaleString() + " words"
                                color: "#888"
                                font.pixelSize: 11
                            }
                            
                            Text {
                                text: "Unique: " + unifiedSettings.uniqueWords.toLocaleString() + " · User: " + unifiedSettings.userWords
                                color: "#666"
                                font.pixelSize: 10
                            }
                            
                            SettingsToggle {
                                Layout.fillWidth: true
                                text: "Debug Mode"
                                checked: unifiedSettings.debugMode
                                onToggled: function(c) { unifiedSettings.settingChanged("debugMode", c) }
                            }
                        }
                    }
                    
                    // ===== ACCESSIBILITY SECTION =====
                    SettingsSection {
                        title: "Accessibility"
                        Layout.fillWidth: true
                        
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            
                            Text {
                                Layout.fillWidth: true
                                text: "Motor control profile for fuzzy key detection"
                                color: "#888"
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                            }
                            
                            Repeater {
                                model: unifiedSettings.profiles
                                
                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 36
                                    radius: 6
                                    color: modelData && unifiedSettings.currentProfile === modelData.name ? "#2a4a6a" : "#2a2a2a"
                                    border.color: modelData && unifiedSettings.currentProfile === modelData.name ? "#4a9eff" : "#444"
                                    border.width: 1
                                    
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 8
                                        
                                        Text {
                                            text: modelData && modelData.name ? modelData.name.charAt(0).toUpperCase() + modelData.name.slice(1) : ""
                                            color: "#e0e0e0"
                                            font.pixelSize: 12
                                            font.bold: modelData && unifiedSettings.currentProfile === modelData.name
                                        }
                                        
                                        Item { Layout.fillWidth: true }
                                        
                                        Text {
                                            text: modelData && modelData.uncertainty !== undefined ? "σ=" + modelData.uncertainty.toFixed(1) : ""
                                            color: "#888"
                                            font.pixelSize: 10
                                        }
                                    }
                                    
                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            if (modelData && modelData.name) {
                                                unifiedSettings.currentProfile = modelData.name
                                                unifiedSettings.settingChanged("profile", modelData.name)
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    // Bottom spacer
                    Item { height: 8 }
                }
            }
        }
    }
}
