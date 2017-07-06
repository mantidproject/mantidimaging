class BasePlotWindow(object):
    """The Subclass MUST during construction initialize self.canvas as its canvas.

    The canvas.figure MUST be a matplotlib figure
    SLOTS
    Keep button: self._report_as_kept_to_manager
    Make Current button: self._report_as_current_to_manager
    Dump to console button : self._dump_script_to_console

    IMPLEMENT
    self._display_status """

    def __init__(self, number, manager):
        self.number = number
        self._manager = manager
        self.canvas = None
        self._script_log = []
        # the aliases used in script generation
        self._import_aliases = {'plotting.pyplot': 'plt'}

    def set_as_kept(self):
        self._display_status("kept")

    def set_as_current(self):
        self._display_status("current")

    def display_status(self, status):
        if status == "kept":
            self._display_status('kept')
        elif status == "current":
            self._display_status("current")
        else:
            raise ValueError("Invalid status %s" % status)

    def _display_status(self, status):
        pass

    def _report_as_kept_to_manager(self):
        self._manager.set_figure_as_kept(self.number)

    def _report_as_current_to_manager(self):
        self._manager.set_figure_as_current(self.number)

    def get_figure(self):
        return self.canvas.figure

    def script_log(self, source_module, function_name, call_args, call_kwargs):
        self._script_log.append(
            (source_module, function_name, call_args, call_kwargs))

    def get_script(self):
        script = ""
        for library, alias in self._import_aliases.items():
            script += "import " + library + " as " + alias + "\n"
        for log in self._script_log:
            script += self._format_command(log) + "\n"
        return script

    def _format_command(self, command):
        """Return a line of python code for a tuple in the log"""
        output = ""
        source_module, function_name, call_args, call_kwargs = command
        if source_module in self._import_aliases.keys():
            source_module = self._import_aliases[source_module]

        if source_module:
            output += source_module + "."

        output += function_name + '('

        formatted_call_args = ", ".join(call_args)
        output += formatted_call_args

        call_kwargs = map(lambda x: "=".join(x), call_kwargs.items())
        formatted_call_kwargs = ", ".join(call_kwargs)

        if formatted_call_kwargs:
            if formatted_call_args:
                output += ", "
            output += formatted_call_kwargs
        output += ")"

        return output

    def _dump_script_to_console(self):
        print self.get_script()
