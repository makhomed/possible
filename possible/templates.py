
from jinja2 import Environment, FileSystemLoader, BaseLoader

from possible.engine import runtime


def render_template(template_filename, *args, **kwargs):
    environment = Environment(loader=FileSystemLoader(runtime.config.files), keep_trailing_newline=True, trim_blocks=True, lstrip_blocks=True)
    template = environment.get_template(template_filename)
    return template.render(*args, **kwargs)


def render(template_string, *args, **kwargs):
    environment = Environment(loader=BaseLoader(), keep_trailing_newline=True, trim_blocks=True, lstrip_blocks=True)
    template = environment.from_string(template_string)
    return template.render(*args, **kwargs)
