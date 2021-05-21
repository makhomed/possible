
__all__ = ['insert_line', 'prepend_line', 'append_line', 'delete_line', 'replace_line', 'substitute_line', 'strip_line',
           'edit_ini_section', 'strip', 'istrip', 'edit', '_apply_editors', 'edit_line', 'append_word', 'remove_word']

import re
import sys

from possible.engine.exceptions import PossibleRuntimeError
from possible.engine.utils import debug


def _full_line(pattern):
    if pattern[0] != '^':
        pattern = '^' + pattern
    if pattern[-1] != '$':
        pattern = pattern + '$'
    return pattern


def insert_line(line_to_insert, **kwargs):
    """Insert line editor.

    Inserts ``line_to_insert`` before or after specified line.
    One and only one keyword argument expected: ``before`` or ``after``

    Args:
        line_to_insert: Line to insert in text.
        before: Anchor pattern, before which text should be inserted.
        after: Anchor pattern, after which text should be inserted.

    Returns:
        closure function, which acts as text editor, parameterized by :func:`~insert_line` arguments.

    Raises:
        :class:`~exceptions.SystemExit`: When error occurred.
    """
    insert_type = None
    anchor_pattern = None
    for name in sorted(kwargs):
        if insert_type is None:
            if name == 'before' or name == 'after':
                insert_type = name
                anchor_pattern = _full_line(kwargs[name])
            else:
                raise PossibleRuntimeError("insert_line: unknown insert_type '%s'" % name)
        else:
            raise PossibleRuntimeError("insert_line: already defined insert_type '%s', unexpected '%s'" % (insert_type, name))
    if insert_type is None:
        raise PossibleRuntimeError("insert_line: must be defined 'before' or 'after' argument.")

    def insert_line_editor(text):
        regex = re.compile(anchor_pattern)
        text_lines = text.split('\n')
        line_already_inserted = False
        anchor_lines = 0
        for line in text_lines:
            match = regex.match(line)
            if match:
                anchor_lines += 1
            if line == line_to_insert:
                line_already_inserted = True
        if anchor_lines == 0:
            raise PossibleRuntimeError("insert_line: anchor pattern '%s' not found." % anchor_pattern)
        elif anchor_lines > 1:
            raise PossibleRuntimeError("insert_line: anchor pattern '%s' found %d times, must be only one." % (anchor_pattern, anchor_lines))
        out = list()
        for line in text_lines:
            match = regex.match(line)
            if match and not line_already_inserted:
                if insert_type == 'before':
                    out.append(line_to_insert)
                    out.append(line)
                    continue
                else:  # insert_type == 'after':
                    out.append(line)
                    out.append(line_to_insert)
                    continue
            else:
                out.append(line)
        return '\n'.join(out)
    return insert_line_editor


def prepend_line(line_to_prepend, insert_empty_line_after=False):
    """Prepend line editor.

    Prepends ``line_to_prepend`` before first line of text.
    If ``line_to_prepend`` already presend in text in any line position - do nothing.

    Args:
        line_to_prepend: Line to prepend before first line of text.
        insert_empty_line_after: If True add empty line after prepended line.

    Returns:
        closure function, which acts as text editor, parameterized by :func:`~prepend_line` arguments.
    """

    def prepend_line_editor(text):
        text_lines = text.split('\n')
        if line_to_prepend in text_lines:
            return text
        if insert_empty_line_after:
            text_lines.insert(0, '')
        text_lines.insert(0, line_to_prepend)
        return '\n'.join(text_lines)
    return prepend_line_editor


def append_line(line_to_append, insert_empty_line_before=False):
    """Append line editor.

    Appends ``line_to_append`` after last line of text.
    If ``line_to_append`` already presend in text in any line position - do nothing.

    Args:
        line_to_append: Line to append after last line of text.
        insert_empty_line_before: If True add empty line before appended line.

    Returns:
        closure function, which acts as text editor, parameterized by :func:`~append_line` arguments.
    """

    def append_line_editor(text):
        text_lines = text.split('\n')
        if line_to_append in text_lines:
            return text
        if text_lines[-1] == '':
            if insert_empty_line_before:
                text_lines.append(line_to_append)
            else:
                text_lines[-1] = line_to_append
        else:
            if insert_empty_line_before:
                text_lines.append('')
            text_lines.append(line_to_append)
        text_lines.append('')
        return '\n'.join(text_lines)
    return append_line_editor


def delete_line(pattern):
    """Delete line editor.

    Deletes all lines from text, which match ``pattern``.

    Args:
        pattern: Which lines whould be deleted.

    Returns:
        closure function, which acts as text editor, parameterized by :func:`~delete_line` arguments.
    """
    pattern = _full_line(pattern)

    def delete_line_editor(text):
        regex = re.compile(pattern)
        out = list()
        for line in text.split('\n'):
            match = regex.match(line)
            if match:
                continue
            out.append(line)
        return '\n'.join(out)
    return delete_line_editor


def replace_line(pattern, repl, flags=0):
    r"""Replace line editor.

    Replaces all **whole** lines in text, which match ``pattern`` with `repl`.
    In any case pattern wil start with r'^' and end with r'$' characters.

    .. seealso::
        :func:`~substitute_line`

    Args:
        pattern: Which lines should be replaced.
        repl: repl can be a string or a function; if it is a string, any backslash escapes in it are processed.
            That is, \\n is converted to a single newline character, \\r is converted to a carriage return,
            and so forth. Unknown escapes such as \\j are left alone. Backreferences, such as \\6,
            are replaced with the substring matched by group 6 in the pattern.
            For details see :meth:`re.RegexObject.sub`.
        flags: Any flags allowed in :func:`re.compile`.

    Returns:
        closure function, which acts as text editor, parameterized by :func:`~replace_line` arguments.
    """
    pattern = _full_line(pattern)

    def replace_line_editor(text):
        regex = re.compile(pattern, flags)
        out = list()
        for line in text.split('\n'):
            match = regex.match(line)
            if match:
                line = regex.sub(repl, line)
            out.append(line)
        return '\n'.join(out)
    return replace_line_editor


def substitute_line(pattern, repl, flags=0):
    r"""Substitute line editor.

    Replaces part of lines in text, which match ``pattern`` with ``repl``.

    .. seealso::
        :func:`~replace_line`

    Args:
        pattern: Regular Expression, which part of lines should be substituted.
        repl: ``repl`` can be a string or a function; if it is a string, any backslash escapes in it are processed.
            That is, \\n is converted to a single newline character, \\r is converted to a carriage return,
            and so forth. Unknown escapes such as \\j are left alone. Backreferences, such as \\6,
            are replaced with the substring matched by group 6 in the pattern.
            For details see :meth:`re.RegexObject.sub`.
        flags: Any flags allowed in :func:`re.compile`.

    Returns:
        closure function, which acts as text editor, parameterized by :func:`~substitute_line` arguments.
    """

    def substitute_editor(text):
        regex = re.compile(pattern, flags)
        out = list()
        for line in text.split('\n'):
            found = regex.search(line)
            if found:
                line = regex.sub(repl, line)
            out.append(line)
        return '\n'.join(out)
    return substitute_editor


def strip_line(chars=None):
    """Strip line editor.

    Strip each line of text with :meth:`str.strip` called with argument chars.

    Args:
        chars: The chars argument is a string specifying the set of characters to be removed.
            If omitted or None, the chars argument defaults to removing whitespace.
            The chars argument is not a prefix or suffix;
            rather, all combinations of its values are stripped:

    Returns:
        closure function, which acts as text editor, parameterized by :func:`~strip_line` arguments.

    """

    def strip_editor(text):
        out = list()
        for line in text.split('\n'):
            line = line.strip(chars)
            out.append(line)
        return '\n'.join(out)
    return strip_editor


def _apply_editors(old_text, *editors):
    if not editors:
        raise PossibleRuntimeError("editors can't be empty.")
    text = old_text
    for editor in editors:
        text = editor(text)
    text_after_first_pass = text
    for editor in editors:
        text = editor(text)
    text_after_second_pass = text
    if text_after_first_pass != text_after_second_pass:
        debug.print("="*80)
        debug.print(f"0 run: >>>{old_text}<<<")
        debug.print("="*80)
        debug.print(f"1 run: >>>{text_after_first_pass}<<<")
        debug.print("="*80)
        debug.print(f"2 run: >>>{text_after_second_pass}<<<")
        debug.print("="*80)
        raise PossibleRuntimeError("editors is not idempotent.")
    new_text = text_after_second_pass
    changed = new_text != old_text
    return changed, new_text


def removeprefix(self, prefix):
    # https://www.python.org/dev/peps/pep-0616/
    if self.startswith(prefix):
        return self[len(prefix):]
    else:
        return self[:]

def removesuffix(self, suffix):
    # https://www.python.org/dev/peps/pep-0616/
    # suffix='' should not call self[:-0].
    if suffix and self.endswith(suffix):
        return self[:-len(suffix)]
    else:
        return self[:]

def edit_line(prefix, suffix, *editors):
    """Edit one text line text editor"""
    def line_editor(text):
        pattern = _full_line(prefix + '.*' + suffix)
        regex = re.compile(pattern)
        lines = list()
        selected_lines = list()
        for line in text.split('\n'):
            match = regex.match(line)
            if match:
                selected_lines.append(line)
                assert line.startswith(prefix)
                assert line.endswith(suffix)
                line = removeprefix(line, prefix)
                line = removesuffix(line, suffix)
                changed, line = _apply_editors(line, *editors)
                assert '\n' not in line
                lines.append(prefix + line + suffix)
            else:
                lines.append(line)
        return '\n'.join(lines)
    return line_editor


def append_word(word_to_append):
    """Append word editor.

    Appends ``word_to_append`` after last char of text.
    If ``line_to_append`` already presend in text in any line position - do nothing.

    Args:
        word_to_append: Line to append after last line of text.

    Returns:
        closure function, which acts as text editor, parameterized by :func:`~append_line` arguments.
    """

    def append_word_editor(text):
        text_words = text.split()
        if word_to_append in text_words:
            return text
        else:
            return text + ' ' + word_to_append
    return append_word_editor


def remove_word(word_to_remove):
    """Remove word editor."""
    def remove_word_editor(text):
        text_words = text.split()
        if word_to_remove not in text_words:
            return text
        else:
            words = list()
            in_word = text[0] != ' ' and text[0] != '\t'
            buf = ''
            for char in text:
                if char == ' ' or char == '\t':
                    if in_word:
                        words.append(buf)
                        in_word = False
                        buf=char
                    else:
                        buf+=char
                else:
                    if in_word:
                        buf+=char
                    else:
                        words.append(buf)
                        in_word = True
                        buf=char
            if buf:
                words.append(buf)
            out = list()
            for word in words:
                if word == word_to_remove:
                    continue
                else:
                    out.append(word)
            return ''.join(out)
    return remove_word_editor


def edit_ini_section(section_name_to_edit, *editors):
    """Edit ini section text editor.

    Apply all editors from list ``editors`` to section named ``section_name_to_edit``.
    ``editors`` is any combination of **line** editors: :func:`~insert_line`, :func:`~delete_line`, :func:`~replace_line` and so on.

    Args:
        section_name_to_edit: Name of section to edit, must be in form '[section_name]'.
        editors: List of editors to apply for selected ini section.

    Returns:
        closure function, which acts as text editor, parameterized by :func:`~edit_ini_section` arguments.

    Raises:
        :class:`~exceptions.SystemExit`: When error occurred.
    """
    if section_name_to_edit is not None:
        if section_name_to_edit[0] != '[' or section_name_to_edit[-1] != ']':
            raise PossibleRuntimeError("edit_ini_section: section name must be in form [section_name]")
        section_name_to_edit = section_name_to_edit[1:-1]

    def ini_section_editor(text):  # pylint: disable=too-many-locals
        pattern = r'^\s*\[(.*)\]\s*$'
        regex = re.compile(pattern)
        current_section_name = None
        current_section_text = list()
        section_content = dict()
        section_order = list()
        for line in text.split('\n'):
            match = regex.match(line)
            if match:
                new_section_name = match.group(1)
                if new_section_name in section_content or new_section_name == current_section_name:
                    raise PossibleRuntimeError("edit_ini_section: bad ini file, section '[%s]' duplicated in file." % new_section_name)
                section_content[current_section_name] = current_section_text
                section_order.append(current_section_name)
                current_section_name = new_section_name
                current_section_text = list()
            else:
                current_section_text.append(line)
        section_content[current_section_name] = current_section_text
        section_order.append(current_section_name)
        if section_name_to_edit in section_content:
            old_text = '\n'.join(section_content[section_name_to_edit])
            changed, new_text = _apply_editors(old_text, *editors)
            if changed:
                section_content[section_name_to_edit] = new_text.split('\n')
        else:
            raise PossibleRuntimeError("edit_ini_section: section '[%s]' not found." % section_name_to_edit)
        out = list()
        for section_name in section_order:
            if section_name is not None:
                out.append('[' + section_name + ']')
            section_text = section_content[section_name]
            out.extend(section_text)
        return '\n'.join(out)
    return ini_section_editor


def edit(text, *editors):
    """Edit text editor.

    Apply all editors from list ``editors`` to given text.
    ``editors`` is any combination of editors: :func:`~insert_line`, :func:`~delete_line`, :func:`~replace_line` and so on.

    Args:
        text: Text to edit, must be string.
        editors: List of editors to apply for text of file ``remote_filename``.

    Returns:
        Text after applying all editors.

    Raises:
        :class:`~exceptions.SystemExit`: When error occurred.
    """
    dummy_changed, text = _apply_editors(text, *editors)
    return text


def strip(text):
    r"""Strip text helper function.

    Strip all empty lines from begin and end of text. Also strip all whitespace characters from begin and end of each line.
    Preserves '\\n' character at last line of text. Not preservers indent whitespaces characters at the begin on each line.

    Args:
        text: Text to strip, must be string or None.

    Returns:
        Text after strip. It is always string even if argument was None.

    Raises:
        :class:`~exceptions.PossibleRuntimeError`: When error occurred.
    """
    if text is None:
        text = ''
    if not isinstance(text, str):
        raise PossibleRuntimeError('strip: string expected')
    if not text:
        return text
    lines = list()
    text = text.strip() + '\n'
    for line in text.split('\n'):
        line = line.strip()
        lines.append(line)
    text = '\n'.join(lines)
    return text

def istrip(text):
    r"""Strip text helper function.

    Strip all empty lines from begin and end of text. Also strip all whitespace characters from begin and end of each line.
    Preserves '\\n' character at last line of text. Preservers indent whitespaces characters at the begin on each line.

    Args:
        text: Text to strip, must be string or None.

    Returns:
        Text after strip. It is always string even if argument was None.

    Raises:
        :class:`~exceptions.PossibleRuntimeError`: When error occurred.
    """
    if text is None:
        text = ''
    if not isinstance(text, str):
        raise PossibleRuntimeError('istrip: string expected')
    if not text:
        return text
    lines = list()

    for line in text.split('\n'):
        if line.strip() == '':
            continue
        lines.append(line)
    text = '\n'.join(lines)

    lines = list()
    spaces = sys.maxsize
    for line in text.split('\n'):
        line_spaces = len(line) - len(line.lstrip(' '))
        if line_spaces < spaces:
            spaces = line_spaces

    for line in text.split('\n'):
        line = line[spaces:]
        line = line.rstrip()
        lines.append(line)
    text = '\n'.join(lines) + '\n'
    return text
