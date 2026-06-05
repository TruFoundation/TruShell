# Built-in command registry for TruShell.
# Each entry is one line and must include {cmd: name}, "function()", and [path].

{cmd: help}; "run_help()"; [trushell/commands/core.py];
{cmd: exit}; "run_exit()"; [trushell/commands/core.py];
{cmd: edit}; "run_edit_command()"; [trushell/commands/editor.py];
{cmd: settings}; "run_settings()"; [trushell/commands/core.py];
{cmd: task}; "run_task_command()"; [trushell/commands/tasks.py];
{cmd: joke}; "run_joke_command()"; [trushell/commands/joke.py];
{cmd: joke-trex}; "run_joke_trex_command()"; [trushell/commands/joke.py];
{cmd: now}; "run_now()"; [trushell/commands/chronoterm.py];
{cmd: time}; "run_time()"; [trushell/commands/chronoterm.py];
{cmd: world}; "run_world()"; [trushell/commands/chronoterm.py];
{cmd: tz}; "run_tz()"; [trushell/commands/chronoterm.py];
{cmd: alarm}; "run_alarm()"; [trushell/commands/chronoterm.py];
{cmd: sw}; "run_sw()"; [trushell/commands/chronoterm.py];
{cmd: csv-view}; "run_csv_view()"; [trushell/commands/data.py];
{cmd: j}; "run_jump()"; [trushell/commands/nav.py];

