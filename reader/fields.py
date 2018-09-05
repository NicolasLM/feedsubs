from io import BytesIO

import atoma
import atoma.opml
from django.core.exceptions import ValidationError
from django.forms.fields import FileField
from django.utils.translation import gettext_lazy as _


class OPMLField(FileField):
    default_error_messages = {
        'invalid_opml': _(
            "Upload a valid OPML file. The file you uploaded was either not an "
            "OPML or a corrupted one."
        ),
        'no_opml_feeds': _(
            "Uploaded OPML file does not contain any feed URL."
        ),
        'too_many_opml_feeds': _(
            "Uploaded OPML file contains too many feed URLs."
        ),
    }

    def to_python(self, data):
        """Check that the file-upload field data contains a valid OPML file."""
        f = super().to_python(data)
        if f is None:
            return None

        # We might have a path or we might have to read the data from memory
        if hasattr(data, 'temporary_file_path'):
            file = data.temporary_file_path()
        else:
            if hasattr(data, 'read'):
                file = BytesIO(data.read())
            else:
                file = BytesIO(data['content'])

        try:
            opml = atoma.opml.parse_opml_file(file)
        except atoma.FeedXMLError as e:
            raise ValidationError(
                self.error_messages['invalid_opml'],
                code='invalid_opml',
            ) from e

        feed_uris = set(atoma.opml.get_feed_list(opml))

        if len(feed_uris) == 0:
            raise ValidationError(
                self.error_messages['no_opml_feeds'], code='no_opml_feeds',
            )

        if len(feed_uris) > 1000:
            raise ValidationError(
                self.error_messages['too_many_opml_feeds'],
                code='too_many_opml_feeds',
            )

        if hasattr(f, 'seek') and callable(f.seek):
            f.seek(0)

        return feed_uris
