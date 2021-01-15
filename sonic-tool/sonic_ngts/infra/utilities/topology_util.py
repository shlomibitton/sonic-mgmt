import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def get_xml_template(template_name):
    p = Path(__file__).parent.parent / 'topology_templates/'
    file_loader = FileSystemLoader(str(p))
    env = Environment(loader=file_loader)
    env.trim_blocks = True
    env.lstrip_blocks = True
    env.rstrip_blocks = True
    template = env.get_template(template_name)
    return template


def create_file(file_path, file_contents, set_permission=''):
    f = open(file_path, "w+")
    f.write(file_contents)
    f.close()
    if set_permission:
        os.system("chmod {} {}".format(set_permission, file_path))
