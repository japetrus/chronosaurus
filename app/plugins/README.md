# Creating plugins

1. Create a folder prefixed with "importer_" or "view_" depending on the type of plugin you are creating.
2. Define essential parameters in `__init__.py`. For an importer these are `start_import` and `action_name`. For a view these are `action_name`, `view_name` and `create_view`.
3. Place this folder somewhere that Chronosaurus will find it on start up. This path can be configured in the preferences.

## Importers

When the user selects an action in the import menu it will call that plugin's `start_import` function. You can do whatever you need to in that function to get the data, but ultimately it should end up in the datasets global, which is just a dict of pandas data frames.

## Views

When the user selects an action in the view menu it will call whatever is assigned to that plugin's `create_view`. Usually this is a subclass of QWidget so that it can be inserted as a tab. There are some useful widgets included in Chronosaurus you may want to subclass, such as `ARViewWidget`, which will be a view containing a plot with a locked aspect ratio. Your view class should also have members `addDataset`, `createControlWidget`, `saveState` and `restoreState`. See some of the built-in plugins for how each of these works, but essentially `addDataset` is called when the user double clicks a dataset while the view is displayed, `createControlWidget` should return a widget that can configure the view, and `saveState`/`restoreState` are used to save/restore the state of a view.