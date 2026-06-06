from __future__ import annotations

from rich.console import Console
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, Select, Static, Switch

from trushell.core.settings import SettingsManager


class SettingsApp(App):
    """Terminal settings manager for TruShell."""

    CSS = """
    Screen {
        padding: 0;
    }

    # Theme styles
    Screen.theme-dark {
        background: rgb(18, 18, 18);
        color: white;
    }
    Screen.theme-light {
        background: rgb(245, 245, 245);
        color: black;
    }
    Screen.theme-monokai {
        background: rgb(39, 40, 34);
        color: rgb(248, 248, 242);
    }

    # Panel layout
    #category_panel {
        border: solid green;
        padding: 1 1;
        width: 28%;
        min-width: 22;
    }
    #content_panel {
        border: solid cyan;
        padding: 1 1;
        width: 72%;
    }
    #button_row {
        padding-top: 1;
    }
    Button {
        margin-right: 1;
    }
    .panel_title {
        text-style: bold;
        padding-bottom: 1;
    }
    .field_row {
        padding: 1 0;
    }
    .field_label {
        width: 24;
        text-style: bold;
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("ctrl+s", "save_settings", "Save"),
        ("ctrl+q", "quit_app", "Quit"),
    ]

    CATEGORIES = ["General", "Appearance", "Navigation", "Data"]
    THEME_OPTIONS = [("dark", "Dark"), ("light", "Light"), ("monokai", "Monokai")]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = SettingsManager()
        self.settings = self.manager.load()
        self.selected_category = "General"
        # Track changes to settings without losing data when switching categories
        self.dirty_settings: dict = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal():
            with Vertical(id="category_panel"):
                yield Static("Categories", classes="panel_title")
                yield ListView(
                    *[ListItem(Label(category), name=category) for category in self.CATEGORIES],
                    id="category_list",
                )
            with Vertical(id="content_panel"):
                yield Static("Settings", classes="panel_title")
                yield Vertical(id="form_container")
                with Horizontal(id="button_row"):
                    yield Button("Save", id="save_button", variant="success")
                    yield Button("Exit", id="exit_button", variant="error")
        yield Footer()

    def on_mount(self) -> None:
        category_list = self.query_one("#category_list", ListView)
        category_list.focus()
        self._apply_theme(self.settings.get("theme", "dark"))
        self._refresh_form()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected = event.item.name
        if selected:
            self.selected_category = selected
            self._refresh_form()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_button":
            self._save_settings()
        elif event.button.id == "exit_button":
            self.exit()

    def _track_change(self, key: str, value) -> None:
        """Track changes to settings without losing data when switching categories."""
        self.dirty_settings[key] = value

    def action_save_settings(self) -> None:
        self._save_settings()

    def action_quit_app(self) -> None:
        self.exit()

    def _refresh_form(self) -> None:
        form_container = self.query_one("#form_container", Vertical)

        # Remove existing widgets manually for modern Textual compatibility
        for widget in list(form_container.children):
            widget.remove()

        def add_field(label_text: str, widget: Static | Input | Select | Switch) -> None:
            # Mount row first, then add children to it
            row = Horizontal(classes="field_row")
            form_container.mount(row)
            row.mount(Label(label_text, classes="field_label"))
            row.mount(widget)

        current_cat = self.selected_category

        if current_cat == "General":
            input_widget = Input(value=str(self.settings.get("prompt_symbol", "➜")), id="prompt_symbol")
            input_widget.watch_value(lambda value: self._track_change("prompt_symbol", value))
            add_field("Prompt symbol:", input_widget)
        elif current_cat == "Appearance":
            select_widget = Select(
                options=self.THEME_OPTIONS,
                value=str(self.settings.get("theme", "dark")),
                id="theme_selector",
            )
            select_widget.watch_value(lambda value: self._track_change("theme", value))
            add_field("Theme:", select_widget)
        elif current_cat == "Navigation":
            git_switch = Switch(value=bool(self.settings.get("show_git_status", True)), id="show_git_status")
            git_switch.watch_value(lambda value: self._track_change("show_git_status", value))
            add_field("Show git status:", git_switch)
            
            complete_switch = Switch(value=bool(self.settings.get("auto_complete", True)), id="auto_complete")
            complete_switch.watch_value(lambda value: self._track_change("auto_complete", value))
            add_field("Auto complete:", complete_switch)
        elif current_cat == "Data":
            csv_input = Input(value=str(self.settings.get("csv_max_rows", 50)), id="csv_max_rows")
            csv_input.watch_value(lambda value: self._track_change("csv_max_rows", value))
            add_field("CSV max rows:", csv_input)

    def _save_settings(self) -> None:
        # Collect all values from dirty_settings and current widgets
        theme = self.dirty_settings.get("theme") or self.settings.get("theme", "dark")
        prompt_symbol = self.dirty_settings.get("prompt_symbol") or self.settings.get("prompt_symbol", "➜")
        show_git_status = self.dirty_settings.get("show_git_status")
        if show_git_status is None:
            show_git_status = self.settings.get("show_git_status", True)
        auto_complete = self.dirty_settings.get("auto_complete")
        if auto_complete is None:
            auto_complete = self.settings.get("auto_complete", True)
        csv_max_rows_value = self.dirty_settings.get("csv_max_rows") or str(self.settings.get("csv_max_rows", 50))

        try:
            csv_max_rows = int(csv_max_rows_value)
        except ValueError:
            self.notify("CSV max rows must be an integer.", severity="error")
            return

        # Update settings dict with all collected values
        self.settings["theme"] = theme
        self.settings["prompt_symbol"] = prompt_symbol
        self.settings["show_git_status"] = show_git_status
        self.settings["auto_complete"] = auto_complete
        self.settings["csv_max_rows"] = csv_max_rows

        # Persist to disk via manager
        self.manager.set("theme", theme)
        self.manager.set("prompt_symbol", prompt_symbol)
        self.manager.set("show_git_status", show_git_status)
        self.manager.set("auto_complete", auto_complete)
        self.manager.set("csv_max_rows", csv_max_rows)
        self.manager.save()

        # Clear dirty settings after save
        self.dirty_settings.clear()
        self._apply_theme(theme)
        self.notify("Settings saved.", severity="success")

    def _apply_theme(self, theme: str) -> None:
        for option, _ in self.THEME_OPTIONS:
            self.set_class(option == theme, f"theme-{option}")


def run_settings(args: str) -> None:
    """Launch the TruShell settings TUI."""
    try:
        app = SettingsApp()
        try:
            app.run(inline=True)
        except TypeError:
            app.run()
    except Exception as error:
        Console().print(f"[red]Unable to launch settings: {error}[/red]")
