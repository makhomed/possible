
__version__ = '0.1.0'

from possible.context import Context, local_run         # noqa: F401
from possible.decorators import task, group, allow      # noqa: F401
from possible.templates import render, render_template  # noqa: F401
from possible.editors import insert_line, prepend_line, append_line, delete_line, replace_line, substitute_line, strip_line, edit_ini_section, strip, istrip, edit  # noqa: F401
from possible.editors import edit_line, append_word, remove_word  # noqa: F401
from possible.engine import runtime                     # noqa: F401
