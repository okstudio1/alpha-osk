import QtQuick 2.15
import QtQuick.Layouts 1.15

Item {
    id: numpadPanel
    
    property real keyW: 48
    property real keyH: 44
    property real keySpacing: 2
    property bool numLockOn: true
    
    implicitWidth: numGrid.implicitWidth
    implicitHeight: numGrid.implicitHeight
    
    signal numLockToggled()
    
    GridLayout {
        id: numGrid
        columns: 4
        rowSpacing: numpadPanel.keySpacing
        columnSpacing: numpadPanel.keySpacing
        
        // Row 1: NumLock, /, *, -
        KeyButton {
            keyText: "numlock"
            displayText: "Num"
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH
            fontSize: 10
            isSpecial: true
            isActive: numpadPanel.numLockOn
            keyColor: "#333333"
            onKeyPressed: numpadPanel.numLockToggled()
        }
        KeyButton {
            keyText: "/"
            displayText: "/"
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH
            fontSize: 14
            keyColor: "#3a3a3a"
            onKeyPressed: keyboard.pressKey("/")
        }
        KeyButton {
            keyText: "*"
            displayText: "*"
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH
            fontSize: 14
            keyColor: "#3a3a3a"
            onKeyPressed: keyboard.pressKey("*")
        }
        KeyButton {
            keyText: "-"
            displayText: "-"
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH
            fontSize: 14
            keyColor: "#3a3a3a"
            onKeyPressed: keyboard.pressKey("-")
        }
        
        // Row 2: 7, 8, 9, +
        KeyButton {
            keyText: "7"
            displayText: "7"
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH
            fontSize: 14
            onKeyPressed: keyboard.pressKey("7")
        }
        KeyButton {
            keyText: "8"
            displayText: "8"
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH
            fontSize: 14
            onKeyPressed: keyboard.pressKey("8")
        }
        KeyButton {
            keyText: "9"
            displayText: "9"
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH
            fontSize: 14
            onKeyPressed: keyboard.pressKey("9")
        }
        KeyButton {
            keyText: "+"
            displayText: "+"
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH * 2 + numpadPanel.keySpacing
            fontSize: 14
            keyColor: "#3a3a3a"
            Layout.rowSpan: 2
            onKeyPressed: keyboard.pressKey("+")
        }
        
        // Row 3: 4, 5, 6
        KeyButton {
            keyText: "4"
            displayText: "4"
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH
            fontSize: 14
            onKeyPressed: keyboard.pressKey("4")
        }
        KeyButton {
            keyText: "5"
            displayText: "5"
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH
            fontSize: 14
            onKeyPressed: keyboard.pressKey("5")
        }
        KeyButton {
            keyText: "6"
            displayText: "6"
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH
            fontSize: 14
            onKeyPressed: keyboard.pressKey("6")
        }
        
        // Row 4: 1, 2, 3, Enter
        KeyButton {
            keyText: "1"
            displayText: "1"
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH
            fontSize: 14
            onKeyPressed: keyboard.pressKey("1")
        }
        KeyButton {
            keyText: "2"
            displayText: "2"
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH
            fontSize: 14
            onKeyPressed: keyboard.pressKey("2")
        }
        KeyButton {
            keyText: "3"
            displayText: "3"
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH
            fontSize: 14
            onKeyPressed: keyboard.pressKey("3")
        }
        KeyButton {
            keyText: "return"
            displayText: "⏎"
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH * 2 + numpadPanel.keySpacing
            fontSize: 16
            isSpecial: true
            keyColor: "#2a5a2a"
            Layout.rowSpan: 2
            onKeyPressed: keyboard.pressSpecialKey("return")
        }
        
        // Row 5: 0 (wide), .
        KeyButton {
            keyText: "0"
            displayText: "0"
            keyWidth: numpadPanel.keyW * 2 + numpadPanel.keySpacing
            keyHeight: numpadPanel.keyH
            fontSize: 14
            Layout.columnSpan: 2
            onKeyPressed: keyboard.pressKey("0")
        }
        KeyButton {
            keyText: "."
            displayText: "."
            keyWidth: numpadPanel.keyW
            keyHeight: numpadPanel.keyH
            fontSize: 14
            onKeyPressed: keyboard.pressKey(".")
        }
    }
}
