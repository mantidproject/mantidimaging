Using Savu from Mantid Imaging
==============================

The Savu integration is currently done via the Savu Filters GUI. This can be accessed via "Workflow > Savu Image Operations" or by pressing :code:`Ctrl+Shift+F`.

Once that is open, it connects to the already running (on IDaaS) backend.

The GUI offers the following features:

- Displays all plugins available on Savu. Loaders and Savers are not shown. All other plugins are shown together - both pre-processing and reconstruction.
- Each plugin's properties are displayed on selection.
    - The "Description" area shows documentation available in Savu for that plugin.
    - Hovering over each property shows the documentation available in Savu for that property.

- Button functionality:
    - Add To Process List: Adds to the process list on the side.
    - Apply Filter to Stack: This will apply the current plugin to the FULL stack. This does NOT apply the process list steps on the side.
    - Apply List to Stack: This will apply ALL the plugins in the process list on the side to the stack.