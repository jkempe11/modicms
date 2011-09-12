import gzip
import cStringIO

from modicms.base import _Component


class GzipContent(_Component):
    def process(self, metadata, data):
        metadata['was_gzipped'] = True

        zipped = cStringIO.StringIO()
        with gzip.GzipFile(fileobj=zipped, mode='wb') as zipper:
            zipper.write(data)
        super(GzipContent, self).process(metadata, zipped.getvalue())
