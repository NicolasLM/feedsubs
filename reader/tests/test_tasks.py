import pytest

from .. import models, tasks


@pytest.mark.django_db
def test_create_or_update_if_needed():
    assert list(models.CachedImage.objects.all()) == []
    created_obj, created, modified = tasks.create_or_update_if_needed(
        models.CachedImage,
        [],
        uri='https://foo.bar/image.jpg',
        defaults={
            'format': 'JPEG'
        }
    )
    assert isinstance(created_obj, models.CachedImage)
    assert created_obj.size_in_bytes == 0
    assert created
    assert not modified

    updated_obj, created, modified = tasks.create_or_update_if_needed(
        models.CachedImage,
        [created_obj],
        uri='https://foo.bar/image.jpg',
        defaults={
            'format': 'JPEG',
            'size_in_bytes': 1024
        }
    )
    assert isinstance(updated_obj, models.CachedImage)
    assert updated_obj.size_in_bytes == 1024
    assert not created
    assert modified

    not_updated_obj, created, modified = tasks.create_or_update_if_needed(
        models.CachedImage,
        [updated_obj],
        uri='https://foo.bar/image.jpg',
        defaults={
            'format': 'JPEG',
            'size_in_bytes': 1024
        }
    )
    assert not_updated_obj is updated_obj
    assert not_updated_obj.size_in_bytes == 1024
    assert not created
    assert not modified


def test_is_object_equivalent():
    attachment = models.Attachment(
        uri='https://foo.bar/image.jpg',
        title='Foo image',
        mime_type='image/jpeg',
        size_in_bytes=1024
    )

    assert tasks._is_object_equivalent(attachment, {
        'uri': 'https://foo.bar/image.jpg'
    })
    assert tasks._is_object_equivalent(attachment, {
        'uri': 'https://foo.bar/image.jpg',
        'title': 'Foo image',
    })
    assert tasks._is_object_equivalent(attachment, {
        'mime_type': 'image/jpeg',
        'size_in_bytes': 1024
    })
    assert tasks._is_object_equivalent(attachment, {})

    assert not tasks._is_object_equivalent(attachment, {
        'uri': 'https://foo.bar/image.gif'
    })
    assert not tasks._is_object_equivalent(attachment, {
        'mime_type': 'image/jpeg',
        'size_in_bytes': 1025
    })
    assert not tasks._is_object_equivalent(attachment, {
        'non_existant': None
    })
