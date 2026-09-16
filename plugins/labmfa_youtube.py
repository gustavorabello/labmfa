# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from docutils import nodes
from docutils.parsers.rst import Directive, directives


class YouTube(Directive):
    """Embed YouTube video in posts and pages."""

    def align(argument):
        """Conversion function for the "align" option."""
        return directives.choice(argument, ("left", "center", "right"))

    def boolean(argument):
        """Conversion function for yes/no True/False."""
        value = directives.choice(argument, ("yes", "True", "no", "False"))
        return value in ("yes", "True")

    required_arguments = 1
    optional_arguments = 8
    option_spec = {
        "class": directives.unchanged,
        "width": directives.positive_int,
        "height": directives.positive_int,
        "allowfullscreen": boolean,
        "seamless": boolean,
        "nocookie": boolean,
        "align": align,
        "comment": directives.unchanged,
    }

    final_argument_whitespace = False
    has_content = False

    def run(self):
        video_id = self.arguments[0].strip()
        youtube_domain = "youtube-nocookie" if "nocookie" in self.options else "youtube"
        url = "https://www.{}.com/embed/{}".format(youtube_domain, video_id)

        width = self.options.get("width", None)
        height = self.options.get("height", None)
        fullscreen = self.options.get("allowfullscreen", True)
        align = self.options.get("align", None)
        comment = self.options.get("comment", None)
        seamless = self.options.get("seamless", True)
        css_classes = "youtube"
        if "class" in self.options:
            css_classes += " {}".format(self.options["class"])
        elif height is None:
            css_classes += " youtube-16x9"

        iframe_arguments = [
            (width, 'width="{}"'),
            (height, 'height="{}"'),
            (fullscreen, "allowfullscreen"),
            (seamless, 'seamless frameBorder="0"'),
        ]

        div_block = '<div class="container"> <div class="{}" '.format(css_classes)
        div_block += 'align="{}">'.format(align)
        embed_block = '<iframe src="{}" '.format(url)
        text_block = "</div>  <p> {}".format(comment)
        text_block += " </p>"

        for value, format_string in iframe_arguments:
            embed_block += (format_string + " ").format(value) if value else ""

        embed_block = embed_block[:-1] + "></iframe>"

        return [
            nodes.raw("", div_block, format="html"),
            nodes.raw("", embed_block, format="html"),
            nodes.raw("", text_block, format="html"),
            nodes.raw("", "</div>", format="html"),
        ]


def register():
    directives.register_directive("youtube", YouTube)
