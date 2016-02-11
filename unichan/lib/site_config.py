from unichan.lib.dynamic_config import DynamicConfig, DynamicConfigItem


class SiteConfig(DynamicConfig):
    def __init__(self):
        super().__init__()

        self.configs.append(DynamicConfigItem('motd', 'MOTD', '', str, maximum=500))
