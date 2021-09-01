# Standard Library
from typing import Optional

# My stuff
from utilities.spotify import objects


class ExplicitContentSettings:

    __slots__ = 'data', 'filter_enabled', 'filter_locked'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.filter_enabled = data.get('filter_enabled')
        self.filter_locked = data.get('filter_locked')

    def __repr__(self) -> str:
        return f'<spotify.ExplicitContentSettings filter_enabled={self.filter_enabled} filter_locked={self.filter_locked}'


class User(objects.BaseObject):

    __slots__ = 'country', 'email', 'explicit_content_settings', 'external_urls', 'followers', 'images', 'has_premium'

    def __init__(self, data: dict) -> None:
        super().__init__(data)

        self.country: Optional[str] = data.get('country', None)
        self.name: Optional[str] = data.get('display_name', None)
        self.email: Optional[str] = data.get('email', None)
        self.explicit_content_settings: Optional[ExplicitContentSettings] = ExplicitContentSettings(data.get('explicit_content')) if data.get('explicit_content') else None
        self.external_urls: dict[Optional[str], Optional[str]] = data.get('external_urls', {})
        self.followers: objects.Followers = objects.Followers(data.get('followers')) if data.get('followers') else None
        self.images: Optional[list[Optional[objects.Image]]] = [objects.Image(image_data) for image_data in data.get('images')] if data.get('images') else None
        self.has_premium: Optional[bool] = data.get('product') == 'premium' if data.get('product') else None

    def __repr__(self) -> str:
        return f'<spotify.User display_name=\'{self.name}\' id=\'{self.id}\' url=\'<{self.url}>\'>'

    @property
    def url(self):
        return self.external_urls.get('spotify')
