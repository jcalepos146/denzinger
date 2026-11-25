# The collection as an MCP server

`server.py` lets an AI assistant that speaks the [Model Context Protocol](https://modelcontextprotocol.io) (Claude Desktop, Claude Code and others) look up the texts, quote them exactly and cite them by number, instead of working from memory. It runs on your own computer, needs only Python's standard library, and only reads the data.

## Connect it

**Claude Code.** The repository's `.mcp.json` already lists the server: open Claude Code in this folder and approve `eodem-sensu` when it asks. Or add it by hand:

```sh
claude mcp add eodem-sensu -- python tools/mcp/server.py
```

**Claude Desktop.** Add the server to `claude_desktop_config.json` (on Windows `%APPDATA%\Claude\`, on a Mac `~/Library/Application Support/Claude/`), with the full path to `server.py`, and restart the app:

```json
{
  "mcpServers": {
    "eodem-sensu": {
      "command": "python",
      "args": ["C:\\path\\to\\denzinger\\tools\\mcp\\server.py"]
    }
  }
}
```

Use `python3` where that is the name of Python 3.

## Where the data comes from

With `--data DIR` it reads that folder. Otherwise it reads `dist/data` when the site has been built in this checkout, and if not, downloads the published open data (about 8 MB) once into a cache folder (`%LOCALAPPDATA%\eodem-sensu` or `~/.cache/eodem-sensu`) and refreshes it after a week. `--refresh` downloads it again now. A change to the site therefore reaches the server by itself.

## What it offers

| Tool | What it returns |
|---|---|
| `search` | Entries matching words, "exact phrases" or a number, filtered by kind of document, grade or years, with a snippet |
| `get_entry` | The full text by any number people cite (`1839`, `n. 1839`, `DS 3074`, `LG 25`, `CCC 2267`, `S1`), with its kind of document, grade and the reason, censure, source record, cross-references, page link, and the Latin on request |
| `related` | Cross-references both ways, documented relations with their quotations, doctrinal threads and continuity cases that use the entry |
| `cite` | Short form, Chicago and Turabian for the older Denzinger numbers (Deferrari 1957); the document and article after 1958; the online reader |
| `list_cases`, `get_case` | The continuity cases: verdict, confidence, hypothesis, objection and reply, texts, propositions (formal object, assent, binding force, evidence), comparisons and the evidence still needed |
| `reading_rules` | The ten principles of hermeneutics and the continuity protocol (P1-P8 and its labels) |

Two prompts start common tasks: **test_continuity** (two numbers: compare them under the protocol) and **check_statement** (a sentence: check it against the texts). The reading rules are also served as resources.

The server tells the assistant to quote what the tools return, cite by number, give each text's weight, and treat grades as a reading aid and the cases as research, not Church teaching.

## Examples

- *Does Lumen Gentium 25 go beyond Pastor aeternus on infallibility? Use the continuity protocol.*
- *What does DS 3074 define, and with what authority? Give me the Latin.*
- *What is still missing for case C3, and what would settle it?*
- *Check this statement: "The Church once taught that slavery was acceptable."*

## Cost

The server costs nothing to run: it is a local program started by the app. Using it counts toward your Claude plan like any other conversation. A hosted version that anyone could add by address would need a small server; the data is static, so a free tier would likely do.

## Tests

`python3 -m unittest tests.test_mcp` (or the whole suite) checks the protocol, every tool and the references on a small sample, without the network.
