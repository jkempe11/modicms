import re
import os
import json
import urllib
import cStringIO

from modicms.base import _Component


class _MarkupComponent(_Component):
    def _morph_path(self, metadata):
        metadata = metadata.copy()
        output_path = metadata['output_path']
        output_root, old_extension = os.path.splitext(output_path)
        metadata['output_path'] = output_root + self.output_extension
        return metadata

    def process_and_return(self, metadata, data):
        morphed = self._morph_path(metadata)
        data = self._process(morphed, data)
        return morphed, data

    def _process(slf, metadata, data):
        raise NotImplementedError()

    def is_invalid(self, metadata, source_mtime):
        morphed = self._morph_path(metadata)
        return super(_MarkupComponent, self).is_invalid(
            morphed,
            source_mtime
        )


try:
    import markdown

    class InterpretMarkdown(_MarkupComponent):
        output_extension = '.html'

        def _process(self, metadata, data):
            md = markdown.Markdown()
            data = md.convert(data)
            return data

except ImportError:
    pass


try:
    import clevercss

    class ConvertCleverCSS(_MarkupComponent):
        output_extension = '.css'

        def _process(self, metadata, data):
            return clevercss.convert(data, minified=True)

except ImportError:
    pass

class IncludeJavascript(_MarkupComponent):
    output_extension = '.js'
    INCLUDE_RE = re.compile(r'#include\s*"([^"]+)"\s*')

    def _process(self, metadata, data):
        output = cStringIO.StringIO()

        for line in data.splitlines():
            m = self.INCLUDE_RE.match(line)
            if m:
                filename = m.group(1)
                with open(filename, 'r') as included:
                    output.write(included.read())
            else:
                output.write(line + "\n")

        return output.getvalue()


class CompressJavascript(_MarkupComponent):
    output_extension = '.js'

    def _process(self, metadata, data):
        params = urllib.urlencode([
            ('js_code', data),
            ('compilation_level', 'SIMPLE_OPTIMIZATIONS'),
            ('output_format', 'json'),
            ('output_info', 'compiled_code'),
            ('output_info', 'errors'),
        ])

        resp = urllib.urlopen(
            'http://closure-compiler.appspot.com/compile',
            params
        )

        response = json.loads(resp.read())

        if 'errors' in response:
            for error in response['errors']:
                print error['error']
            raise Exception("failed to closure-compile javascript")

        return response['compiledCode']
