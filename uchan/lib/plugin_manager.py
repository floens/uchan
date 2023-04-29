import importlib

modules = []


def load_plugins(plugins):
    for plugin in plugins:
        loaded_module = importlib.import_module("uchan.plugins.{}".format(plugin))
        add_module(loaded_module, plugin)


def add_module(module, name):
    # info = execute_module_method(module, "describe_plugin", False)
    execute_module_method(module, "on_enable", False)
    # print('Loaded plugin {}: {}'.format(info['name'], info['description']))

    modules.append(module)


def execute_hook(hook, *args, **kwargs):
    for module in modules:
        execute_module_method(module, hook, True, *args, **kwargs)


def execute_module_method(module, method_name, silent, *args, **kwargs):
    try:
        attr = getattr(module, method_name)
        return attr(*args, **kwargs)
    except AttributeError as e:
        if not silent:
            raise RuntimeError(
                "The plugin {} must have the method {}".format(module, method_name)
            ) from e
