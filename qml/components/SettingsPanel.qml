import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15

Item {
    id: settingsPanel
    
    property bool showFunctionRow: true
    property bool showNavigation: false
    property bool showNumpad: false
    property bool compactMode: false
    property string currentTheme: "dark"
    
    signal settingChanged(string setting, var value)
    signal closeRequested()
    
    implicitWidth: 200
    implicitHeight: settingsColumn.implicitHeight + 20
    
    Rectangle {
        anchors.fill: parent
        color: "#252525"
        radius: 8
        border.color: "#444444"
        border.width: 1
        
        ColumnLayout {
            id: settingsColumn
            anchors.fill: parent
            anchors.margins: 10
            spacing: 8
            
            // Header
            RowLayout {
                Layout.fillWidth: true
                
                Text {
                    text: "⚙ Settings"
                    color: "#e0e0e0"
                    font.pixelSize: 14
                    font.bold: true
                }
                
                Item { Layout.fillWidth: true }
                
                Rectangle {
                    width: 24
                    height: 24
                    radius: 4
                    color: closeArea.containsMouse ? "#5a2020" : "transparent"
                    
                    Text {
                        anchors.centerIn: parent
                        text: "✕"
                        color: closeArea.containsMouse ? "#ff6666" : "#888888"
                        font.pixelSize: 12
                    }
                    
                    MouseArea {
                        id: closeArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: settingsPanel.closeRequested()
                    }
                }
            }
            
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#444444"
            }
            
            // Layout toggles
            Text {
                text: "Layout"
                color: "#888888"
                font.pixelSize: 11
            }
            
            SettingsToggle {
                Layout.fillWidth: true
                text: "Function Keys (F1-F12)"
                checked: settingsPanel.showFunctionRow
                onToggled: function(checked) { settingsPanel.settingChanged("functionRow", checked) }
            }
            
            SettingsToggle {
                Layout.fillWidth: true
                text: "Navigation Keys"
                checked: settingsPanel.showNavigation
                onToggled: function(checked) { settingsPanel.settingChanged("navigation", checked) }
            }
            
            SettingsToggle {
                Layout.fillWidth: true
                text: "Number Pad"
                checked: settingsPanel.showNumpad
                onToggled: function(checked) { settingsPanel.settingChanged("numpad", checked) }
            }
            
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#444444"
            }
            
            // Display options
            Text {
                text: "Display"
                color: "#888888"
                font.pixelSize: 11
            }
            
            SettingsToggle {
                Layout.fillWidth: true
                text: "Compact Mode"
                checked: settingsPanel.compactMode
                onToggled: function(checked) { settingsPanel.settingChanged("compact", checked) }
            }
            
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#444444"
            }
            
            // Theme options
            Text {
                text: "Color Theme"
                color: "#888888"
                font.pixelSize: 11
            }
            
            // Theme selector row
            Row {
                Layout.fillWidth: true
                spacing: 6
                
                Repeater {
                    model: [
                        { name: "dark", color: "#1a1a1a", border: "#4a9eff" },
                        { name: "light", color: "#e8e8e8", border: "#0078d4" },
                        { name: "blue", color: "#1a2a3a", border: "#4a9eff" },
                        { name: "green", color: "#1a2a1a", border: "#4aff4a" },
                        { name: "purple", color: "#2a1a3a", border: "#bb66ff" }
                    ]
                    
                    Rectangle {
                        width: 28
                        height: 28
                        radius: 6
                        color: modelData.color
                        border.color: settingsPanel.currentTheme === modelData.name ? modelData.border : "#555"
                        border.width: settingsPanel.currentTheme === modelData.name ? 2 : 1
                        
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: settingsPanel.settingChanged("theme", modelData.name)
                        }
                        
                        // Checkmark for selected theme
                        Text {
                            anchors.centerIn: parent
                            text: settingsPanel.currentTheme === modelData.name ? "✓" : ""
                            color: modelData.name === "light" ? "#333" : "#fff"
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }
                }
            }
            
            Item { Layout.fillHeight: true }
        }
    }
}
