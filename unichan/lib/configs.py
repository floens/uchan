from unichan.lib.dynamic_config import DynamicConfig, DynamicConfigItem


class BoardConfig(DynamicConfig):
    TYPE = 'board_config'

    def __init__(self):
        super().__init__()

        self.configs.append(
                DynamicConfigItem('pages', 'Number of pages this board has', 10, int, minimum=1, maximum=15))
        self.configs.append(DynamicConfigItem('full_name', 'Full name', '', str, maximum=25))
        self.configs.append(DynamicConfigItem('description', 'Description', 'No description given', str, maximum=100))
        self.configs.append(
                DynamicConfigItem('bump_limit', 'Max count of posts in a thread that will bump', 300, int, minimum=100,
                                  maximum=500))


class SiteConfig(DynamicConfig):
    TYPE = 'site'

    def __init__(self):
        super().__init__()

        self.configs.append(DynamicConfigItem('motd', 'MOTD', '', str, maximum=500))
        self.configs.append(DynamicConfigItem('default_name', 'Default posting name', 'Anonymous', str, maximum=25))
        self.configs.append(DynamicConfigItem('boards_top', 'Show board list at top', True, bool))
        self.configs.append(DynamicConfigItem('footer_text', 'Footer text', 'Page served by µchan', str, maximum=100))
