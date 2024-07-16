# VS Code Power User

## The Command Palette and Keyboard Shortcuts

Mac vs. Windows:

See <https://code.visualstudio.com/docs/getstarted/keybindings#_keyboard-shortcuts-reference> for more details.

Open the command pallette, they type the action you want to do. No reason to memorize all the keyboard shortcuts!

<kbd>⇧ Shift</kbd> + <kbd>⌘ Command</kbd> + <kbd>P</kbd>

Open a specific file:

<kbd>⌘ Command</kbd> + <kbd>P</kbd>

Open/close the terminal:

<kbd>⌘ Command</kbd> + <kbd>J</kbd>

Go to a specific line:

<kbd>⌘ Command</kbd> + <kbd>P</kbd> then type:

 ```
 :<line number>
 ```

Go to a specific symbol:

<kbd>⌘ Command</kbd> + <kbd>P</kbd> then type

```
@<symbol>
```

Trigger quick fix:

<kbd>⌘ Command</kbd> + <kbd>.</kbd>

Trigger suggestion:

<kbd>⌃ Control</kbd> + <kbd>Space</kbd>

## Multiple cursors

Use multiple cursors in VS Code to easily edit many lines at the same time (<https://code.visualstudio.com/docs/getstarted/tips-and-tricks#_column-box-selection>).

## Treat scripts like notebooks

Use `# %%` to execute chunks of a script. Great for development!

```python
# %%
print('hello world')

# %%
print('how are you?')
print('doing well I hope?')
```

## Format your Python code with Ruff

Open the command pallette:

<kbd>⇧ Shift</kbd> + <kbd>⌘ Command</kbd> + <kbd>P</kbd>

Then type:

```
Ruff: Format document
```

or:

```
Ruff: Format imports
```

You can also use Ruff from the terminal:

```bash
# Format everything
ruff format .

# Fix imports
ruff check --select I --fix .

# Link to check for other issues
ruff .
```

## Extensions

See [.vscode/extensions.json](../../../.vscode/extensions.json) for a list of recommended extensions.

## LLM Code Generation

- GitHub Copilot
- Code AI
- AWS Code Whisperer
- Google Gemini