# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os
import web

from sympy.parsing.latex import parse_latex
from sympy.parsing.latex.errors import LaTeXParsingError
from sympy import simplify

from inginious.common.tasks_problems import Problem
from inginious.frontend.task_problems import DisplayableProblem

__version__ = "0.1.dev0"

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))


class StaticMockPage(object):
    # TODO: Replace by shared static middleware and let webserver serve the files
    def GET(self, path):
        if not os.path.abspath(PATH_TO_PLUGIN) in os.path.abspath(os.path.join(PATH_TO_PLUGIN, path)):
            raise web.notfound()

        try:
            with open(os.path.join(PATH_TO_PLUGIN, "static", path), 'rb') as file:
                return file.read()
        except:
            raise web.notfound()

    def POST(self, path):
        return self.GET(path)


class MathProblem(Problem):
    """Display an input box and check that the content is correct"""

    def __init__(self, task, problemid, content):
        Problem.__init__(self, task, problemid, content)
        self._answer = str(content.get("answer", ""))

    @classmethod
    def get_type(cls):
        return "math"

    def input_is_consistent(self, task_input, default_allowed_extension, default_max_size):
        return self.get_id() in task_input

    def input_type(self):
        return str

    def check_answer(self, task_input, language):
        if not self._answer:
            return None, None, None, 0

        if not task_input[self.get_id()]:
            return False, None, ["_wrong_answer"], 1

        try:
            student_answer = parse_latex(task_input[self.get_id()])
            correct_answer = parse_latex(self._answer)
        except LaTeXParsingError as e:
            return False, None, ["_wrong_answer", "Parsing error: " + str(e)], 1

        if simplify(student_answer-correct_answer) == 0:
            return True, None, ["_correct_answer"], 0
        else:
            return False, None, ["_wrong_answer"], 1

    @classmethod
    def parse_problem(self, problem_content):
        return Problem.parse_problem(problem_content)

    @classmethod
    def get_text_fields(cls):
        return Problem.get_text_fields()


class DisplayableMathProblem(MathProblem, DisplayableProblem):
    """ A displayable match problem """

    def __init__(self, task, problemid, content):
        MathProblem.__init__(self, task, problemid, content)

    @classmethod
    def get_type_name(self, language):
        return "math"

    @classmethod
    def get_renderer(cls, template_helper):
        """ Get the renderer for this class problem """
        return template_helper.get_custom_renderer(os.path.join(PATH_TO_PLUGIN, "templates"), False)

    def show_input(self, template_helper, language, seed):
        """ Show MatchProblem """
        return str(DisplayableMathProblem.get_renderer(template_helper).math(self.get_id()))

    @classmethod
    def show_editbox(cls, template_helper, key, language):
        return DisplayableMathProblem.get_renderer(template_helper).math_edit(key)

    @classmethod
    def show_editbox_templates(cls, template_helper, key, language):
        return ""


def init(plugin_manager, course_factory, client, plugin_config):
    # TODO: Replace by shared static middleware and let webserver serve the files
    plugin_manager.add_page('/plugins/math/static/(.+)', StaticMockPage)
    plugin_manager.add_hook("css", lambda: "/plugins/math/static/mathquill.css")
    plugin_manager.add_hook("css", lambda: "/plugins/math/static/matheditor.css")
    plugin_manager.add_hook("javascript_header", lambda: "/plugins/math/static/mathquill.min.js")
    plugin_manager.add_hook("javascript_header", lambda: "/plugins/math/static/math.js")
    plugin_manager.add_hook("javascript_header", lambda: "/plugins/math/static/matheditor.js")
    course_factory.get_task_factory().add_problem_type(DisplayableMathProblem)
