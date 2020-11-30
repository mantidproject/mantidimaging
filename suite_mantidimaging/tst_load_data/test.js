import * as names from 'names.js';

function main() {
    startApplication("python3.7 -m mantidimaging");
    activateItem(waitForObjectItem(names.mainWindowMenubarQMenuBar, "File"));
    activateItem(waitForObjectItem(names.mainWindowMenuFileQMenu, "Load"));
    clickButton(waitForObject(names.treeSelectQPushButton));
    clickButton(waitForObject(names.qFileDialogToParentButtonQToolButton));
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 183, 198, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 183, 198, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 183, 199, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 184, 203, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 184, 204, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 184, 209, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 184, 209, -120, 0, 2);
    doubleClick(waitForObjectItem(names.stackedWidgetTreeViewQTreeView, "Tilt 1 \\_pre reco"), 125, 8, Qt.NoModifier, Qt.LeftButton);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 128, 176, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 128, 176, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 128, 176, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 128, 178, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 127, 181, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 127, 184, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 126, 186, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 127, 189, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 115, 174, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 115, 174, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 115, 174, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(names.stackedWidgetTreeViewQTreeView), 115, 174, -120, 0, 2);
    doubleClick(waitForObjectItem(names.stackedWidgetTreeViewQTreeView, "Tomo\\_0000\\.tif"), 120, 3, Qt.NoModifier, Qt.LeftButton);
    clickButton(waitForObject(names.dialogOKQPushButton));
    waitForObject(names.mainWindowTomo0000QDockWidget);
    test.vp("VP5");
    sendEvent("QMouseEvent", waitForObject(names.mainWindowTomo0000QTabBar), QEvent.MouseButtonPress, 168, 15, Qt.LeftButton, 1, 0);
    sendEvent("QMouseEvent", waitForObject(names.mainWindowFlat0000QTabBar), QEvent.MouseButtonRelease, 168, 15, Qt.LeftButton, 0, 0);
    test.vp("VP6");
    sendEvent("QMouseEvent", waitForObject(names.mainWindowFlat0000QTabBar), QEvent.MouseButtonPress, 222, 15, Qt.LeftButton, 1, 0);
    sendEvent("QMouseEvent", waitForObject(names.mainWindowDark0000QTabBar), QEvent.MouseButtonRelease, 222, 15, Qt.LeftButton, 0, 0);
    test.vp("VP7");
}
