import sublime
import sublime_plugin

PLUGIN_KEY = 'IndentToParenthesis'
SELECTION_MARKER_KEY = PLUGIN_KEY + '.saved_selection'
SELECTION_MARKER_SCOPE = 'indent_to_parenthesis.saved_selection'

class IndentToParenthesisCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    view = self.view
    selections = view.sel()

    handled_regions = []
    unhandled_regions = False
    for selection in selections:
      line_upto_cursor = view.substr(
          sublime.Region(view.line(selection).begin(), selection.end()))
      param_column = self.find_last_unmatched_open_paren(line_upto_cursor)

      view.erase(edit, selection)

      whitespace_region = self.expand_to_whitespace(selection.begin())
      view.erase(edit, whitespace_region)
      if param_column:
        chars = view.insert(edit, whitespace_region.a, '\n%s' % (' ' * param_column))
        new_cursor = sublime.Region(whitespace_region.a + chars, whitespace_region.a + chars)
        handled_regions.append(new_cursor)
      else:
        unhandled_regions = True

    # NOTE: We let sublime handle the individual levels of indentation by inserting
    #  a newline once for all the unhandled selections. (Depends on the auto-indent
    #  mode of sublime).
    if unhandled_regions:
      # NOTE: We don't want extra newlines after the selections we've already handled,
      #  but the newlines/indentations for the remaining selections will change the
      #  locations of the regions we have handled so we can't just subtract them and
      #  add them back after because they'll be out-of-sync, so we track them using
      #  hidden regions so they get updated automatically.
      view.add_regions(SELECTION_MARKER_KEY, handled_regions, SELECTION_MARKER_SCOPE, flags=sublime.HIDDEN)
      for r in reversed(handled_regions):
        selections.subtract(r)

      view.run_command('insert', {'characters': '\n'})

      selections.add_all(view.get_regions(SELECTION_MARKER_KEY))

  def find_last_unmatched_open_paren(self, line):
    '''Returns offset of the last unmatched opening parenthesis on the line'''
    line_length = len(line)
    closing_paren = 0
    while line_length > 0:
      line_length -= 1
      char = line[line_length]
      if char is ')':
        closing_paren += 1
      elif char is '(':
        if closing_paren > 0:
          closing_paren -= 1
        else:
          # Get index beneath the opening parenthesis.
          return line_length + 1

    return None

  def expand_to_whitespace(self, point):
    '''Returns region with all spaces matched before and after the point'''
    view = self.view
    line_upto_point = view.substr(sublime.Region(view.line(point).a, point))
    whitespace_to_eat = 0
    last_non_ws_index = len(line_upto_point)
    while last_non_ws_index > 0:
      last_non_ws_index -= 1
      char = line_upto_point[last_non_ws_index]
      if char != ' ':
        break
      whitespace_to_eat += 1

    return view.find(' *', point - whitespace_to_eat)
