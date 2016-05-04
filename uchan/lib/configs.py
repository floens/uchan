from uchan.lib.dynamic_config import DynamicConfig, DynamicConfigItem


class BoardConfig(DynamicConfig):
    TYPE = 'board_config'

    def __init__(self):
        super().__init__()

        self.configs += [
            DynamicConfigItem('pages', 'Number of pages this board has', 10, int, minimum=1, maximum=15),
            DynamicConfigItem('per_page', 'Threads per page', 15, int, minimum=10, maximum=15),
            DynamicConfigItem('full_name', 'Full name', '', str, maximum=25,
                              access_roles=[]),
            DynamicConfigItem('description', 'Description', 'No description given', str, maximum=100,
                              access_roles=[]),
            DynamicConfigItem('bump_limit', 'Max count of posts in a thread that will bump', 300, int, minimum=100,
                              maximum=500),
            DynamicConfigItem('file_posting_enabled', 'File posting enabled', True, bool),
            DynamicConfigItem('posting_verification_required', 'Posting requires verification', False, bool)
        ]


class SiteConfig(DynamicConfig):
    TYPE = 'site'

    def __init__(self):
        super().__init__()

        self.configs += [
            DynamicConfigItem('motd', 'MOTD', '', str, maximum=500),
            DynamicConfigItem('footer_text', 'Footer text', 'Page served by [µchan](https://github.com/Floens/uchan)',
                              str, maximum=100),
            DynamicConfigItem('boards_top', 'Show board list at top', True, bool),
            DynamicConfigItem('default_name', 'Default posting name', 'Anonymous', str, maximum=25),
            DynamicConfigItem('posting_enabled', 'Posting enabled', True, bool),
            DynamicConfigItem('file_posting_enabled', 'File posting enabled', True, bool)
        ]
