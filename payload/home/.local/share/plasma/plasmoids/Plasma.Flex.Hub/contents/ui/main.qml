import QtQuick
import QtQuick.Layouts
import "components" as Components
import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    property var elements: Plasmoid.configuration.elements
    property var yElements: Plasmoid.configuration.yElements
    property var xElements: Plasmoid.configuration.xElements

    property bool activeWeather: false

    property var weatherData: if (weatherLoader.item) weatherLoader.item

    Loader {
        id: weatherLoader
        active: activeWeather
        sourceComponent:  weatherDataRob
    }

    Component { id: weatherDataRob;    Components.WeatherData {} }

    compactRepresentation: MouseArea {
        Layout.minimumWidth: 28
        Layout.preferredWidth: 28
        Layout.maximumWidth: 28
        Layout.minimumHeight: 18
        implicitHeight: 28
        property bool wasExpanded
        onPressed: wasExpanded = root.expanded
        onClicked: root.expanded = !wasExpanded
        Kirigami.Icon {
            width: 18
            height: 18
            source: Plasmoid.icon
            color: Kirigami.Theme.textColor
            anchors.centerIn: parent
        }
    }
    fullRepresentation: FullRepresentation {
    }
}

