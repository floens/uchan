class PluginManager:
    def __init__(self):
        self.modules = []

    def add_module(self, module):
        info = self.execute_module_method(module, 'describe_plugin', False)
        self.execute_module_method(module, 'on_enable', False)
        print('Loaded plugin {}: {}'.format(info['name'], info['description']))

        self.modules.append(module)

    def execute_hook(self, hook, *args, **kwargs):
        for module in self.modules:
            self.execute_module_method(module, hook, True, *args, **kwargs)

    def execute_module_method(self, module, method_name, silent, *args, **kwargs):
        try:
            attr = getattr(module, method_name)
            return attr(*args, **kwargs)
        except AttributeError:
            if not silent:
                raise RuntimeError('The plugin {} must have the method {}'.format(module, method_name))
