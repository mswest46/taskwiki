# Various utility functions
from __future__ import print_function
import vim  # pylint: disable=F0401
import regexp
import random
import sys
import os

# Detect if command AnsiEsc is available
ANSI_ESC_AVAILABLE = vim.eval('exists(":AnsiEsc")') == '2'


def tw_modstring_to_args(line):
    output = []
    escape_global_chars = ('"', "'")
    line = line.strip()

    current_escape = None
    current_part = ''
    local_escape_pos = None

    for i in range(len(line)):
        char = line[i]
        ignored = False
        process_next_part = False

        # If previous char was \, add to current part no matter what
        if local_escape_pos == i - 1:
            local_escape_pos = None
        # If current char is \, use it as escape mark and ignore it
        elif char == '\\':
            local_escape_pos = i
            ignored = True
        # If current char is ' or ", open or close an escaped seq
        elif char in escape_global_chars:
            # First test if we're finishing an escaped sequence
            if current_escape == char:
                current_escape = None
                ignored = True
            # Do we have ' inside "" or " inside ''?
            elif current_escape is not None:
                pass
            # Opening ' or "
            else:
                current_escape = char
                ignored = True
        elif current_escape is not None:
            pass
        elif char == ' ':
            ignored = True
            process_next_part = True

        if not ignored:
            current_part += char

        if process_next_part:
            output.append(current_part)
            current_part = ''

    if current_part:
        output.append(current_part)

    return output

def tw_modstring_to_kwargs(line):
    output = dict()
    escape_global_chars = ('"', "'")
    line = line.strip()

    args = tw_modstring_to_args(line)

    for arg in args:
        # If the argument contains :, then it's a key/value pair
        if ':' in arg:
            key, value = arg.split(':', 1)
            output[key] = value
        # Tag addition
        elif arg.startswith('+'):
            value = arg[1:]
            output.setdefault('tags', []).append(value)

    return output

def get_input(prompt="Enter: "):
    value = vim.eval('input("%s")' % prompt)
    vim.command('redraw')
    return value

def get_buffer_shortname():
    return vim.eval('expand("%")')

def get_absolute_filepath():
    return vim.eval('expand("%:p")')

def get_current_line_number():
    row, column = vim.current.window.cursor
    return row - 1

def get_valid_tabpage_buffers(tabpage):
    return [win.buffer for win in tabpage.windows if win.buffer.valid]

def buffer_shortname(buffer):
    return os.path.basename(buffer.name)

def selected_line_numbers():
    return range(vim.current.range.start, vim.current.range.end + 1)

def strip_ansi_escape_sequence(string):
    return regexp.ANSI_ESCAPE_SEQ.sub("", string)

def show_in_split(lines, size=None, position="belowright", vertical=False,
                  name="taskwiki", replace_opened=True):
    # If there is no output, bail
    if not lines:
        print("No output.", file=sys.stderr)
        return

    # If the multiple buffers with this name are not desired
    # cloase all the old ones in this tabpage
    if replace_opened:
        for buf in get_valid_tabpage_buffers(vim.current.tabpage):
            shortname = buffer_shortname(buf)
            if shortname.startswith(name):
                vim.command('bwipe {0}'.format(shortname))

    # Generate a random suffix for the buffer name
    # This is needed since AnsiEsc saves the buffer name inside
    # s: scoped variables. Also lowers the probability of clash with
    # a real file.
    random_suffix = random.randint(1,100000)
    name = '{0}.{1}'.format(name, random_suffix)

    # Compute the size of the split
    if size is None:
        if vertical:
            # Maximum number of columns used + small offset
            # Strip the color codes, since they do not show up in the split
            size = max([len(strip_ansi_escape_sequence(l)) for l in lines]) + 5
        else:
            # Number of lines
            size = len(lines)

    # Call 'vsplit' for vertical, otherwise 'split'
    vertical_prefix = 'v' if vertical else ''

    vim.command("{0} {1}{2}split".format(position, size, vertical_prefix))
    vim.command("edit {0}".format(name))

    # For some weird reason, edit does not work for some users, but
    # enew + file <name> does. Use as fallback.
    if get_buffer_shortname() != name:
        vim.command("enew")
        vim.command("file {0}".format(name))

    # If we were still unable to open the buffer, bail out
    if get_buffer_shortname() != name:
        print("Unable to open a new buffer with name: {0}".format(name))
        return

    # We're good to go!
    vim.command("setlocal noswapfile")
    vim.command("setlocal modifiable")
    vim.current.buffer.append(lines, 0)

    vim.command("setlocal readonly")
    vim.command("setlocal nomodifiable")
    vim.command("setlocal buftype=nofile")
    vim.command("setlocal nowrap")
    vim.command("setlocal nonumber")

    # Keep window size fixed despite resizing
    vim.command("setlocal winfixheight")
    vim.command("setlocal winfixwidth")

    # Make the split easily closable
    vim.command("nnoremap <silent> <buffer> q :bwipe<CR>")
    vim.command("nnoremap <silent> <buffer> <enter> :bwipe<CR>")

    if ANSI_ESC_AVAILABLE:
        vim.command("AnsiEsc")

def tw_execute_colorful(tw, *args, **kwargs):
    override = kwargs.setdefault('config_override', {})
    maxwidth = kwargs.pop('maxwidth', False)
    maxheight = kwargs.pop('maxheight', False)

    if ANSI_ESC_AVAILABLE:
        override['_forcecolor'] = "yes"

    if maxheight:
        override['defaultheight'] = vim.current.window.height

    if maxwidth:
        override['defaultwidth'] = vim.current.window.width

    return tw.execute_command(*args, **kwargs)