import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: predictionSettings
    width: 340
    height: 550
    radius: 10
    color: "#1e1e1e"
    border.color: "#444444"
    border.width: 1

    // Properties bound to keyboard bridge
    property bool llmEnabled: true
    property bool llmAvailable: false
    property int predictionCount: 5
    property int totalWords: 0
    property int uniqueWords: 0
    property int userWords: 0
    property bool debugMode: false

    // Signals
    signal settingChanged(string setting, var value)
    signal closeRequested()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        // Header
        RowLayout {
            Layout.fillWidth: true
            
            Text {
                text: "⚡ Prediction Settings"
                color: "#ffffff"
                font.pixelSize: 14
                font.bold: true
            }
            
            Item { Layout.fillWidth: true }
            
            Rectangle {
                width: 24
                height: 24
                radius: 4
                color: closeBtn.containsMouse ? "#444" : "transparent"
                
                Text {
                    anchors.centerIn: parent
                    text: "✕"
                    color: closeBtn.containsMouse ? "#ff6666" : "#888"
                    font.pixelSize: 12
                }
                
                MouseArea {
                    id: closeBtn
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: predictionSettings.closeRequested()
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: "#333333"
        }

        // LLM Settings
        Text {
            text: "AI Model"
            color: "#888888"
            font.pixelSize: 11
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Text {
                    text: "Use LLM (DistilGPT-2)"
                    color: "#e0e0e0"
                    font.pixelSize: 12
                }
                
                Text {
                    text: predictionSettings.llmAvailable 
                        ? "✓ Model loaded" 
                        : "⚠ Model not available"
                    color: predictionSettings.llmAvailable ? "#4a9eff" : "#ffaa44"
                    font.pixelSize: 10
                }
            }

            Switch {
                id: llmSwitch
                checked: predictionSettings.llmEnabled
                onToggled: predictionSettings.settingChanged("llmEnabled", checked)
                
                indicator: Rectangle {
                    implicitWidth: 44
                    implicitHeight: 22
                    radius: 11
                    color: llmSwitch.checked ? "#4a9eff" : "#444444"
                    border.color: llmSwitch.checked ? "#6ab4ff" : "#555555"

                    Rectangle {
                        x: llmSwitch.checked ? parent.width - width - 2 : 2
                        anchors.verticalCenter: parent.verticalCenter
                        width: 18
                        height: 18
                        radius: 9
                        color: "#ffffff"
                        
                        Behavior on x { NumberAnimation { duration: 100 } }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: "#333333"
        }

        // Prediction Count
        Text {
            text: "Display Options"
            color: "#888888"
            font.pixelSize: 11
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Text {
                text: "Suggestions to show:"
                color: "#e0e0e0"
                font.pixelSize: 12
            }

            Item { Layout.fillWidth: true }

            SpinBox {
                id: countSpinBox
                from: 1
                to: 10
                value: predictionSettings.predictionCount
                onValueModified: predictionSettings.settingChanged("predictionCount", value)
                
                contentItem: Text {
                    text: countSpinBox.value
                    color: "#e0e0e0"
                    font.pixelSize: 12
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    implicitWidth: 70
                    implicitHeight: 28
                    radius: 4
                    color: "#2a2a2a"
                    border.color: "#444444"
                }

                up.indicator: Rectangle {
                    x: parent.width - width
                    height: parent.height / 2
                    width: 20
                    color: countSpinBox.up.pressed ? "#444" : "#333"
                    radius: 2
                    Text {
                        anchors.centerIn: parent
                        text: "+"
                        color: "#888"
                        font.pixelSize: 10
                    }
                }

                down.indicator: Rectangle {
                    x: parent.width - width
                    y: parent.height / 2
                    height: parent.height / 2
                    width: 20
                    color: countSpinBox.down.pressed ? "#444" : "#333"
                    radius: 2
                    Text {
                        anchors.centerIn: parent
                        text: "-"
                        color: "#888"
                        font.pixelSize: 10
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: "#333333"
        }

        // Statistics
        Text {
            text: "Dictionary Statistics"
            color: "#888888"
            font.pixelSize: 10
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 2
            rowSpacing: 2
            columnSpacing: 8

            Text { text: "Total words:"; color: "#888"; font.pixelSize: 10 }
            Text { text: predictionSettings.totalWords.toLocaleString(); color: "#e0e0e0"; font.pixelSize: 10 }

            Text { text: "Unique words:"; color: "#888"; font.pixelSize: 10 }
            Text { text: predictionSettings.uniqueWords.toLocaleString(); color: "#e0e0e0"; font.pixelSize: 10 }

            Text { text: "Your words:"; color: "#888"; font.pixelSize: 10 }
            Text { text: predictionSettings.userWords.toLocaleString(); color: "#4a9eff"; font.pixelSize: 10 }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: "#333333"
        }

        // Import Training Data
        Text {
            text: "Import Training Data"
            color: "#888888"
            font.pixelSize: 10
        }

        Rectangle {
            Layout.fillWidth: true
            height: 52
            radius: 5
            color: "#252525"
            border.color: "#444"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 3

                TextInput {
                    id: importPathInput
                    Layout.fillWidth: true
                    color: "#e0e0e0"
                    font.pixelSize: 10
                    clip: true
                    text: "~/Documents"
                    
                    Rectangle {
                        anchors.fill: parent
                        anchors.margins: -3
                        color: "transparent"
                        border.color: importPathInput.activeFocus ? "#4a9eff" : "#333"
                        radius: 3
                        z: -1
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 3

                    Rectangle {
                        Layout.fillWidth: true
                        height: 22
                        radius: 4
                        color: importFileBtn.containsMouse ? "#3a3a3a" : "#2a2a2a"
                        border.color: "#444"

                        Text {
                            anchors.centerIn: parent
                            text: "📄 File"
                            color: "#e0e0e0"
                            font.pixelSize: 9
                        }

                        MouseArea {
                            id: importFileBtn
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: predictionSettings.settingChanged("importFile", importPathInput.text)
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 22
                        radius: 4
                        color: importFolderBtn.containsMouse ? "#3a3a3a" : "#2a2a2a"
                        border.color: "#444"

                        Text {
                            anchors.centerIn: parent
                            text: "📁 Folder"
                            color: "#e0e0e0"
                            font.pixelSize: 9
                        }

                        MouseArea {
                            id: importFolderBtn
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: predictionSettings.settingChanged("importFolder", importPathInput.text)
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: "#333333"
        }

        // Actions
        Text {
            text: "Actions"
            color: "#888888"
            font.pixelSize: 10
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 4

            Rectangle {
                Layout.fillWidth: true
                height: 26
                radius: 4
                color: saveBtn.containsMouse ? "#3a3a3a" : "#2a2a2a"
                border.color: "#444"

                Text {
                    anchors.centerIn: parent
                    text: "💾 Save"
                    color: "#e0e0e0"
                    font.pixelSize: 9
                }

                MouseArea {
                    id: saveBtn
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: predictionSettings.settingChanged("save", true)
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 26
                radius: 4
                color: reloadBtn.containsMouse ? "#3a3a3a" : "#2a2a2a"
                border.color: "#444"

                Text {
                    anchors.centerIn: parent
                    text: "🔄 Reload"
                    color: "#e0e0e0"
                    font.pixelSize: 9
                }

                MouseArea {
                    id: reloadBtn
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: predictionSettings.settingChanged("reload", true)
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 26
                radius: 4
                color: debugBtn.containsMouse ? "#3a3a3a" : "#2a2a2a"
                border.color: predictionSettings.debugMode ? "#4a9eff" : "#444"

                Text {
                    anchors.centerIn: parent
                    text: "🐛 Debug"
                    color: predictionSettings.debugMode ? "#4a9eff" : "#e0e0e0"
                    font.pixelSize: 9
                }

                MouseArea {
                    id: debugBtn
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: predictionSettings.settingChanged("debug", !predictionSettings.debugMode)
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 26
            radius: 4
            color: clearBtn.containsMouse ? "#5a2020" : "#2a2a2a"
            border.color: clearBtn.containsMouse ? "#ff6666" : "#444"

            Text {
                anchors.centerIn: parent
                text: "🗑️ Clear User Data"
                color: clearBtn.containsMouse ? "#ff6666" : "#e0e0e0"
                font.pixelSize: 9
            }

            MouseArea {
                id: clearBtn
                anchors.fill: parent
                hoverEnabled: true
                onClicked: predictionSettings.settingChanged("clearUserData", true)
            }
        }

        Item { Layout.fillHeight: true }
    }
}
