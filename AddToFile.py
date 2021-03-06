import os

import sublime
import sublime_plugin


class AddToCommand(sublime_plugin.TextCommand):
    """main AddToFile command which handles display and selection
    of views and runs command to insert text
    contains various methods to help separate functions provided"""
    def get_preview(self, view):
        """get the actual preview lines to be shown in file selection
        returns list of strings"""
        if isinstance(view, sublime.View):
            return view.settings().get('preview_lines',
                                       self.get_contents(view))
        else:
            return self.get_contents(self, view)
            # send the invald view to this method as it handles
            # non-view arguements passed

    def get_items(self):
        """return list of active view objects except the current view"""
        return [view for view in self.view.window().views()
                # if view.file_name()
                if view != self.view]

    def get_view_path(self, view):
        """return the full file path of the view passed"""
        try:
            return view.file_name()
            # return a the 'unsplit' file path
        except (AttributeError, TypeError):
            return os.path.join('untitled', 'untitled')
            # use os.path.join() to use the correct backslash
            # or forward slash depending on platform

    def get_contents(self, view):
        """get the content of the first 3 lines of a view
        returns a list of strings"""
        length = 0
        if isinstance(view, sublime.View):
            items = []
            for _ in range(3):
                items.append(view.substr(view.line(length)))
                # add the line contents to list
                length += len(view.substr(view.line(length))) + 1
                # record the cumulative character count to get each line
                # and make up +1 for newline character
        else:
            items = ['' for _ in range(3)]
            # return empty values if the view parameter isnt a view object
        return items

    def split_view_path(self, view):
        """return the split view path of the passed view"""
        try:
            return list(os.path.split(view.file_name()))
            # return a list containing [path, file]
        except (AttributeError, TypeError):
            return ['untitled', 'untitled']
            # handling non-view values

    def get_split_view_paths(self, views):
        """call split_view_path on a list of views"""
        return [self.split_view_path(view) for view in views]
        # returnlist = []
        # for item in views:
        #     returnlist.append(self.split_view_path(item))
        # return returnlist

    def get_view_paths(self, views):
        """return the full file path for a list of views"""
        return [view.file_name() for view in views]

    def on_done(self, val):
        """handles inserting text, status bar messages, creation
        of new files and view switching/scrolling"""
        settings = sublime.load_settings('AddToFile.sublime-settings')
        v = self.view  # save the starting view
        if val == -1:
            return  # end if called with -1 value
        elif val == 'New File':
            f = self.view.window().new_file()
            self.items = self.get_items()
            # do the same as below, but it will not have to get and item from
            # the list with a string index which would have raised an error
        elif self.items[val] == 'New File':  # support for
            # AddToNewFileCommand invocation;
            # if the selected option is 'New File',
            # create a new file
            f = self.view.window().new_file()
            self.items = self.get_items()
        else:  # selected item isn't a file so must be 'new file'
            f = self.items[val]
        f.run_command('insert_to_end',
                      {"lines": [self.view.substr(s)
                                 for s in self.view.sel()]})
        self.view.window().focus_view(v)  # use the starting view
        # override when new file is created to stop focus switching
        # run insert command to add text
        string = settings.get('status_message')
        string = string.format(name=self.split_view_path(f)[1],
                               path=self.get_view_path(f),
                               dir=self.split_view_path(f)[0],
                               # substitute values from destination file
                               sourcename=self.split_view_path(
                               self.view.file_name())[1],
                               sourcepath=self.get_view_path(
                               self.view.file_name()),
                               sourcedir=self.split_view_path(
                               self.view.file_name())[0])
        # substitute values from source file
        # set string using template from settings, substituting
        # values accordingly
        if not settings.get('keep_focus', True):
            self.view.window().focus_view(f)
            # switch focus to destination file if specified in settings
            if settings.get('scroll_view', False):
                f.show(f.size())
        if settings.get('show_status_message', False):
            # run status bar message command if value specified
            # in settings
            self.view.window().run_command('add_status_bar_msg',
                                           {"msg": string})

    def run(self, edit, new_file=False, smart=False):
        """handles display of popup with correct data specified in settings"""
        settings = sublime.load_settings('AddToFile.sublime-settings')
        # load settings file
        # if not ''.join(self.view.substr(s) for s in self.view.sel()):
        #     return
        if all(s.empty() for s in self.view.sel()):
            return  # end if the selection is empty

        self.items = self.get_items()
        # add list of views, excluding the current view
        # self.view.run_command('change_preview')

        if smart is True or settings.get('auto_smart', False):
            self.paths = SmartDisplay.run(self.items)
            # self.paths = [os.path.join(*path) for path in self.paths]
            # get path names given by the SmartDisplay class
            for i, p in enumerate(self.paths):
                if len(p) > 1:
                    self.paths[i] = '({}) {}'.format(p[-1], p[0])
                else:
                    self.paths[i] = p[0]
            # replace the paths

            if settings.get('suggest_new_file', False):
                self.items.append('New File')
                if (settings.get('show_file_path', False)
                   or settings.get('show_containing_folder', False)):
                    self.paths.append('New File')
                else:
                    # self.paths.append(['New File', 'New File'])
                    self.paths.append('New File')

            if settings.get('show_popup', False):
                # show popup with file path - ignores file preview
                # as popup cannot have multiple lines per item
                print(self.paths)
                self.view.show_popup_menu(self.paths, self.on_done)

            else:
                if settings.get('show_preview', False):
                    # get a list of starting content of the open views
                    # excluding the current view
                    self.view_content = [self.get_preview(view)
                                         for view in self.view.window().views()
                                         if view != self.view]

                    self.popup = [[path] + content
                                  for path, content in zip(self.paths,
                                                           self.view_content)]
                    # get a list with the path and the view content to the file
                    # at the path using zip()
                    if settings.get('suggest_new_file', False):
                        self.popup.append(['New File', '', '', ''])
                        # and 'New File' to popup list with blank lines

                    self.view.window().show_quick_panel(self.popup,
                                                        self.on_done)
                    # show panel with file path and preview
                else:
                    # otherwise show the panel with just the file paths
                    self.view.window().show_quick_panel(self.paths,
                                                        self.on_done)
            return  # end function as it has already inserted text

        if new_file is True:
            self.on_done('New File')  # automatically run on_done with value
            # New File to override method
            return  # end the command when it has finished

        if settings.get('show_file_path', False):
            self.paths = self.get_view_paths(self.items)
            # get the 'unsplit' paths

        elif settings.get('show_containing_folder', False):
            self.paths = [os.path.join(
                          str(os.path.split(os.path.split(path)[0])[1]),
                          # this returns the folder containing the file:
                          # 1 - split the path
                          # 2 - get the head [0]
                          # 3 - split the head
                          # 4 - get the tail [1]
                          str(os.path.split(path)[1]))
                          # this returns the file itself
                          for path in self.get_view_paths(self.items)]
            # split the directory to the containing folder
            # and select the folder itself;
            # join to the file name returned from
            # get_split_view_paths

        else:
            self.paths = self.get_split_view_paths(self.items)
            # make a list of the view paths

        if settings.get('add_to_single_view', False) and len(self.items) == 1:
            self.on_done(0)
            # auto-run on_done if there's only 1 other view and if specified
            # in settings

        if settings.get('show_preview', False):
            # self.view_content = [self.get_contents(view)
            #                      for view in self.view.window().views()
            #                      if view != self.view]
            # # get a list of starting content of the open views
            # # excluding the current view
            self.view_content = [self.get_preview(view)
                                 for view in self.view.window().views()
                                 if view != self.view]

            self.popup = []
            for path, content in zip(self.paths, self.view_content):
                if (settings.get('show_file_path', False)
                   or settings.get('show_containing_folder', False)):
                    a = [path]  # add path to list since it's not a list

                else:
                    a = path[:]  # copy 'split' path list to temp variable
                    a.pop(0)
                a.extend(content)
                self.popup.append(a)
            # create popup list of strings which contains the file name and
            # content

            if settings.get('suggest_new_file', False):
                self.popup.append(['New File', '', '', ''])
                # and 'New File' to popup list with blank lines

        if settings.get('suggest_new_file', False):
            self.items.append('New File')
            if (settings.get('show_file_path', False)
               or settings.get('show_containing_folder', False)):
                self.paths.append('New File')
            else:
                self.paths.append(['New File', 'New File'])
                # self.paths.append('New File')
            # add 'new file' option if specified settings
            # 'override' addition of a path to self.paths by creating
            # a mock path called 'New File / New File'

        if settings.get('show_popup', False):
            # continue if the simple popup option is specified
            # (file previews ignored)
            if (settings.get('show_file_path', False)
               or settings.get('show_containing_folder', False)):
                self.view.show_popup_menu([path
                                           for path in self.paths],
                                          self.on_done)
                # create popup with the *file paths* if specified in settings
            else:
                # create popup with the *file names* if specified in settings
                self.view.show_popup_menu([path[1]
                                           for path in self.paths],
                                          self.on_done)
        else:
            if settings.get('show_preview', False):
                self.view.window().show_quick_panel(self.popup,
                                                    self.on_done)
                # create popup with the *file name + preview* if
                # specified in settings
            elif (settings.get('show_file_path', False)
                  or settings.get('show_containing_folder', False)):
                self.view.window().show_quick_panel([path
                                                     for path in self.paths],
                                                    self.on_done)
                # create popup with the *file paths* if specified in settings
            else:
                self.view.window().show_quick_panel([path[1]
                                                     for path in self.paths],
                                                    self.on_done)
                # create popup with the *file names* if specified in settings


class InsertToEndCommand(sublime_plugin.TextCommand):
    """insert text to the end of the given view
    'lines' parameter is a list of strings to be added"""
    def run(self, edit, lines):
        for line in lines:
            # insert lines to end of file
            self.view.insert(edit, self.view.size(), line)
            self.view.insert(edit, self.view.size(), '\n')


class AddStatusBarMsg(sublime_plugin.WindowCommand):
    """set the status bar message to the given string"""
    def run(self, msg):
        # set the status bar message
        sublime.status_message(msg)


class AddToNewFileCommand(sublime_plugin.TextCommand):
    """runs add_to command with parameter new_file as true to override
    behaviour and directly copy selection to a new file instead of having
    to manually select it from the selection panel"""
    def run(self, edit):
        self.view.run_command('add_to', {"new_file": True})
        # called by command: "add_to_new_file", but theoretically could also be
        # caled by  command: "add_to", args: {"new_file": true}
        # in JSON


class ChangePreviewCommand(sublime_plugin.TextCommand):
    """set the lines to be previewed to the 3 lines from the lines
    where the first selection begins
    sets the setting 'preview_lines' of the view's individual settings"""
    def run(self, edit):
        settings = self.view.settings()
        length = self.view.line(self.view.sel()[0]).begin()
        # sets the start length to the begin point of the line
        # in which the first cursor is
        items = []
        for _ in range(3):
            items.append(self.view.substr(self.view.line(length)))
            # add the line contents to list
            length += len(self.view.substr(self.view.line(length))) + 1
            # record the cumulative character count to get each line
        settings.set('preview_lines', items)
        # set the view-specific preview to the lines at the first cursor


class GetPreviewCommand(sublime_plugin.TextCommand):
    """scroll the view to show the lines which will be previewed
    returns the 3 lines as a list of strings"""
    def run(self, edit):
        # 'user interface' style command which scrolls the view
        # to show the lines which are previewed
        # sublime.message_dialog(', '.join(self.view.settings().get(
        #                                 'preview_lines', [])))
        self.view.show(
            self.view.find(
                self.view.settings().get('preview_lines', [])[0],
                0).begin())
        # scroll the view to the begin point of the first line that
        # will be previewed
        return self.view.settings().get('preview_lines',
                                        AddToCommand.get_contents(self,
                                                                  self.view))
        # return the individual view's settings of what 3 lines to preview,
        # if there is no preview set, use the standard preview from line 1


class SmartDisplay:
    """return a list to display in the file selection panel which
    accounts for duplicate names and untitled files
    returns list of strings to display"""
    @staticmethod
    def path_split(view):
        """return the individual parts of the file path"""
        try:
            return os.path.normpath(view.file_name()).split(os.path.sep)
        # try and return the path split into it's individual
        # parts without the slashes
        # 1. normalise the path
        # 2. split path by separator
        except (AttributeError, TypeError):
            # if encountered an error - untitled file,
            # then return it as untitled
            return ['untitled']

    @staticmethod
    def run(views):
        sections = [SmartDisplay.path_split(view)
                    for view in views]
        # get a list of the split file paths
        ends = [[path[-1]] for path in sections]
        # get a list of the file ends - file names
        prev = []
        count = -1
        while ends != prev:
            count -= 1
            # used for getting items from end of list - e.g. list[-1]
            found = []
            prev = ends.copy()
            # set the starting value to be compared to on the next loop
            # create a copy using full list slice

            for n, file in enumerate(ends):
                if file == 'untitled':
                    continue
                if ends.count(file) > 1:
                    # if the file name occurs more than once:
                    # then add the position it occurs in to the found list
                    found.append(n)
            for i in found:
                # for each position that was a duplicate name
                try:
                    ends[i] = ends[i] + [sections[i][count]]
                # change the path name to what is was before and add on the
                # part of the file path that came before - uses the counter to
                # keep track of how far back into the file path the loop is
                except IndexError:
                    print(ends[i])
                    pass
                # if the file path has reached its maximum depth then leave it
                # as it is

        return ends


class SmartAddToCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command('add_to', {"smart": True})
