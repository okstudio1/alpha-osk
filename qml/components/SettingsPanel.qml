import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15

Item {
    id: settingsPanel
    
    property bool showFunctionRow: true
    property bool showNavigation: false
    property bool showNumpad: false
    property bool compactMode: false
    
    signal settingChanged(string setting, bool value)
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
            
            Item { Layout.fillHeight: true }
        }
    }
}
