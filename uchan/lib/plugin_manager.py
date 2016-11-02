import importlib

modules = []


def load_plugins(plugins, config_parser):
    for plugin in plugins:
        loaded_module = importlib.import_module('uchan.plugins.{}'.format(plugin))
        add_module(loaded_module, plugin, config_parser)


def add_module(module, name, config_parser):
    configuration = config_parser[name] if name in config_parser else None
    info = execute_module_method(module, 'describe_plugin', False)
    execute_module_method(module, 'on_enable', False, configuration)
    # print('Loaded plugin {}: {}'.format(info['name'], info['description']))

    modules.append(module)


def execute_hook(hook, *args, **kwargs):
    for module in modules:
        execute_module_method(module, hook, True, *args, **kwargs)


def execute_module_method(module, method_name, silent, *args, **kwargs):
    try:
        attr = getattr(module, method_name)
        return attr(*args, **kwargs)
    except AttributeError:
        if not silent:
            raise RuntimeError('The plugin {} must have the method {}'.format(module, method_name))
