# User-installed plugins are registered here.
# Plugins can optionally run immediately with {lifecycle: on_load}.

{cmd: gstatus}; "plugin_init()"; [trushell/plugins/git_enhancer/main.py]; {lifecycle: on_load};
