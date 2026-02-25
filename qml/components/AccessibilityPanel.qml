import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15

Item {
    id: accessibilityPanel
    
    property string currentProfile: "normal"
    property var profiles: []
    
    signal profileChanged(string profileName)
    signal closeRequested()
    
    implicitWidth: 280
    implicitHeight: contentColumn.implicitHeight + 20
    
    Component.onCompleted: {
        // Load profiles from keyboard bridge
        profiles = keyboard.getAccessibilityProfiles()
        currentProfile = keyboard.getCurrentProfile()
    }
    
    Rectangle {
        anchors.fill: parent
        color: "#252525"
        radius: 8
        border.color: "#444444"
        border.width: 1
        
        ColumnLayout {
            id: contentColumn
            anchors.fill: parent
            anchors.margins: 10
            spacing: 8
            
            // Header
            RowLayout {
                Layout.fillWidth: true
                
                Text {
                    text: "♿ Accessibility"
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
                        onClicked: accessibilityPanel.closeRequested()
                    }
                }
            }
            
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#444444"
            }
            
            // Description
            Text {
                Layout.fillWidth: true
                text: "Select a profile that matches your motor control abilities. Higher uncertainty profiles are more forgiving of misclicks."
                color: "#888888"
                font.pixelSize: 11
                wrapMode: Text.WordWrap
            }
            
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#444444"
            }
            
            // Profile selection
            Text {
                text: "Motor Control Profile"
                color: "#888888"
                font.pixelSize: 11
            }
            
            // Profile buttons
            Repeater {
                model: [
                    { name: "precise", label: "Precise", desc: "Tight tolerance, minimal correction", icon: "🎯" },
                    { name: "normal", label: "Normal", desc: "Balanced correction", icon: "✓" },
                    { name: "mild_tremor", label: "Mild Tremor", desc: "1.5x error tolerance", icon: "〰" },
                    { name: "moderate_tremor", label: "Moderate Tremor", desc: "2x error tolerance", icon: "≋" },
                    { name: "severe_tremor", label: "Severe Tremor", desc: "2.5x error tolerance", icon: "⚡" },
                    { name: "limited_mobility", label: "Limited Mobility", desc: "Optimized for limited range", icon: "♿" }
                ]
                
                Rectangle {
                    Layout.fillWidth: true
                    height: 50
                    radius: 6
                    color: currentProfile === modelData.name ? "#3d5a3d" : 
                           profileArea.containsMouse ? "#353535" : "#2a2a2a"
                    border.color: currentProfile === modelData.name ? "#5a8a5a" : "#444444"
                    border.width: currentProfile === modelData.name ? 2 : 1
                    
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 8
                        
                        Text {
                            text: modelData.icon
                            font.pixelSize: 18
                            color: "#e0e0e0"
                        }
                        
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            
                            Text {
                                text: modelData.label
                                color: currentProfile === modelData.name ? "#a0d0a0" : "#e0e0e0"
                                font.pixelSize: 12
                                font.bold: currentProfile === modelData.name
                            }
                            
                            Text {
                                text: modelData.desc
                                color: "#888888"
                                font.pixelSize: 10
                            }
                        }
                        
                        Text {
                            text: currentProfile === modelData.name ? "✓" : ""
                            color: "#5a8a5a"
                            font.pixelSize: 16
                            font.bold: true
                        }
                    }
                    
                    MouseArea {
                        id: profileArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            if (keyboard.setAccessibilityProfile(modelData.name)) {
                                currentProfile = modelData.name
                                accessibilityPanel.profileChanged(modelData.name)
                            }
                        }
                    }
                }
            }
            
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#444444"
            }
            
            // Current profile info
            Rectangle {
                Layout.fillWidth: true
                height: 40
                radius: 4
                color: "#1a1a2a"
                border.color: "#333355"
                border.width: 1
                
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    
                    Text {
                        text: "ℹ"
                        color: "#6688cc"
                        font.pixelSize: 14
                    }
                    
                    Text {
                        Layout.fillWidth: true
                        text: "Profile affects how strictly key presses are interpreted"
                        color: "#8888aa"
                        font.pixelSize: 10
                        wrapMode: Text.WordWrap
                    }
                }
            }
            
            Item { Layout.fillHeight: true }
        }
    }
}
