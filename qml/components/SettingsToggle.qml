import QtQuick 2.15
import QtQuick.Layouts 1.15

Item {
    id: toggle
    
    property string text: ""
    property bool checked: false
    
    signal toggled(bool checked)
    
    implicitHeight: 28
    
    Rectangle {
        anchors.fill: parent
        radius: 4
        color: toggleArea.containsMouse ? "#333333" : "transparent"
        
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 4
            anchors.rightMargin: 4
            spacing: 8
            
            Text {
                text: toggle.text
                color: "#c0c0c0"
                font.pixelSize: 12
                Layout.fillWidth: true
            }
            
            Rectangle {
                width: 36
                height: 18
                radius: 9
                color: toggle.checked ? "#4a9eff" : "#555555"
                
                Rectangle {
                    width: 14
                    height: 14
                    radius: 7
                    x: toggle.checked ? parent.width - width - 2 : 2
                    anchors.verticalCenter: parent.verticalCenter
                    color: "#ffffff"
                    
                    Behavior on x {
                        NumberAnimation { duration: 100 }
                    }
                }
                
                Behavior on color {
                    ColorAnimation { duration: 100 }
                }
            }
        }
        
        MouseArea {
            id: toggleArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: {
                toggle.checked = !toggle.checked
                toggle.toggled(toggle.checked)
            }
        }
    }
}
