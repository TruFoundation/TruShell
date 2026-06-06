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
        self.dirty_settings = dict(self.settings)
        self.selected_category = "General"

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

    def action_save_settings(self) -> None:
        self._save_settings()

    def action_quit_app(self) -> None:
        self.exit()

    def _update_dirty_setting(self, key: str, value: object) -> None:
        self.dirty_settings[key] = value
        self.settings[key] = value

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "prompt_symbol":
            self._update_dirty_setting("prompt_symbol", event.value)
        elif event.input.id == "csv_max_rows":
            self._update_dirty_setting("csv_max_rows", event.value)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "theme_selector":
            self._update_dirty_setting("theme", event.value)
            self._apply_theme(str(event.value))

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id == "show_git_status":
            self._update_dirty_setting("show_git_status", bool(event.value))
        elif event.switch.id == "auto_complete":
            self._update_dirty_setting("auto_complete", bool(event.value))

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
            add_field(
                "Prompt symbol:",
                Input(value=str(self.dirty_settings.get("prompt_symbol", self.settings.get("prompt_symbol", "➜"))), id="prompt_symbol"),
            )
        elif current_cat == "Appearance":
            add_field(
                "Theme:",
                Select(
                    options=self.THEME_OPTIONS,
                    value=str(self.dirty_settings.get("theme", self.settings.get("theme", "dark"))),
                    id="theme_selector",
                ),
            )
        elif current_cat == "Navigation":
            add_field(
                "Show git status:",
                Switch(value=bool(self.dirty_settings.get("show_git_status", self.settings.get("show_git_status", True))), id="show_git_status"),
            )
            add_field(
                "Auto complete:",
                Switch(value=bool(self.dirty_settings.get("auto_complete", self.settings.get("auto_complete", True))), id="auto_complete"),
            )
        elif current_cat == "Data":
            add_field(
                "CSV max rows:",
                Input(value=str(self.dirty_settings.get("csv_max_rows", self.settings.get("csv_max_rows", 50))), id="csv_max_rows"),
            )

    def _save_settings(self) -> None:
        theme = str(self.dirty_settings.get("theme", self.settings.get("theme", "dark")))
        prompt_symbol = str(self.dirty_settings.get("prompt_symbol", self.settings.get("prompt_symbol", "➜")))
        show_git_status = bool(self.dirty_settings.get("show_git_status", self.settings.get("show_git_status", True)))
        auto_complete = bool(self.dirty_settings.get("auto_complete", self.settings.get("auto_complete", True)))
        csv_max_rows_value = self.dirty_settings.get("csv_max_rows", self.settings.get("csv_max_rows", 50))

        try:
            csv_max_rows = int(csv_max_rows_value)
        except (TypeError, ValueError):
            self.notify("CSV max rows must be an integer.", severity="error")
            return

        self.dirty_settings.update(
            {
                "theme": theme,
                "prompt_symbol": prompt_symbol,
                "show_git_status": show_git_status,
                "auto_complete": auto_complete,
                "csv_max_rows": csv_max_rows,
            }
        )
        self.settings.update(self.dirty_settings)

        for key, value in self.dirty_settings.items():
            self.manager.set(key, value)
        self.manager.save()

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
