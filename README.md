# LinkedIn MCP Server — Auto-Auth From Chrome

[![PyPI](https://img.shields.io/pypi/v/linkedin-mcp-chrome?label=pypi&color=blue)](https://pypi.org/project/linkedin-mcp-chrome/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](#)

A **defensive thin wrapper** around the upstream [`mcp-server-linkedin`](https://pypi.org/project/mcp-server-linkedin/) package (formerly `linkedin-scraper-mcp`) that pins `fastmcp<4.0` so `uvx` doesn't silently upgrade users into the FastMCP 4.0 API removal that took every install down on **2026-08-31**. Same 17 LinkedIn tools, same Chromium-based auth flow, same behavior — zero-risk crash guard on top.

**Use this instead of the upstream package unless you know you want to track the latest FastMCP release.**

> ### A note on the `-chrome` in the name
>
> This package is part of a family of Kugamon MCP wrappers — [`salesforce-mcp-auto-auth-chrome`](https://github.com/kugamon/salesforce-mcp-auto-auth-chrome) and [`reddit-mcp-chrome`](https://github.com/kugamon/reddit-mcp-chrome) — and shares their naming convention. **But `-chrome` means something different here, and we want to be upfront about it.**
>
> | Package | What `-chrome` means |
> | --- | --- |
> | `salesforce-mcp-auto-auth-chrome` | Reads the session cookie from **your real Chrome profile** |
> | `reddit-mcp-chrome` | Reads session cookies from **your real Chrome profile** |
> | **`linkedin-mcp-chrome`** (this one) | Drives a **separate bundled Chromium** browser (via upstream's Patchright), with its own saved login |
>
> Practically, that means: you log into LinkedIn **once, inside a browser window this server opens** — not in your everyday Chrome. That session is saved to `~/.linkedin-mcp/profile/` and reused. Being logged into LinkedIn in your normal Chrome does *not* carry over.
>
> This is inherited from upstream, not a choice we made. If a future version adds real Chrome-profile cookie reuse (killing the separate login and the ~40 MB Chromium download), we'll note it here.

---

## How it fits together

```
Claude Desktop ── stdio ──▶ this package (Python) ── hands off to ──▶ mcp-server-linkedin
       │                            │                                    (unmodified)
       │                            └── pins fastmcp<4 in metadata,      │
       │                                so uvx never resolves 4.0+       │
       │                                                                 ▼
       │                                                       Patchright Chromium
       │                                                       (headless browser
       │                                                        with saved profile)
       │                                                                 │
       │                                                                 ▼
       └── one entry in claude_desktop_config.json          LinkedIn (web scrape)
```

The package adds nothing at runtime — no monkey-patching, no cookie extraction, no wrappers around the actual tools. It exists purely so that when `uvx` resolves the dependency graph, it can never pick up a FastMCP version that upstream's code hasn't been ported to yet. When upstream releases a FastMCP 4-compatible version, this wrapper drops the pin and moves on.

---

## Files in this repo

- **`src/linkedin_mcp_chrome/__main__.py`** — entry point. Prints a version banner, then calls `linkedin_mcp_server.cli_main:main` unchanged.
- **`src/linkedin_mcp_chrome/__init__.py`** — package version.
- **`pyproject.toml`** — the actual work happens here. Declares `mcp-server-linkedin>=4.23.1` and `fastmcp>=3.4.4,<4.0` as dependencies.
- **`examples/claude_desktop_config.example.json`** — copy-paste-ready Claude Desktop config snippet.
- **`docs/how-it-works.md`** — the full story: what broke on 2026-08-31, why upstream shipped it unpinned, what this wrapper does about it, and when the pin should come off.
- **`.claude-plugin/marketplace.json`** + **`plugins/linkedin-research/`** — the optional Claude plugin: four research skills and a shared guardrails file (see [Claude skills](#claude-skills--the-linkedin-research-plugin)).

---

## Setup — Part 1: Add to Claude Desktop (~1 min, one-time)

### Fastest path — have Claude do it for you

If Claude Desktop already has filesystem access to your home directory (Cowork mode users do by default), paste the following into a fresh Claude chat:

```
Add a LinkedIn MCP entry to my Claude Desktop config named `linkedin`.
The MCP command should be `uvx linkedin-mcp-chrome` (it's on PyPI).
Set env var UV_HTTP_TIMEOUT to "300" so the first-run Chromium
download doesn't time out. Make a backup of my existing config first.
```

Claude reads your existing `claude_desktop_config.json`, adds the entry alongside anything already there, backs up the original, and tells you when to restart. When Claude confirms it's done, skip to **Restart Claude Desktop** below.

### Alternate route — edit `claude_desktop_config.json` yourself

If you'd rather edit JSON by hand:

**1. Open your Claude Desktop config.** On macOS the file lives at:

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**2. Add this entry to `mcpServers`.**

```jsonc
{
  "mcpServers": {
    "linkedin": {
      "command": "uvx",
      "args": ["linkedin-mcp-chrome"],
      "env": {
        "UV_HTTP_TIMEOUT": "300"
      }
    }
  }
}
```

The `UV_HTTP_TIMEOUT` env var gives `uvx` time to download the ~40 MB Patchright Chromium binary the first time the wrapper runs.

### Restart Claude Desktop

Cmd+Q (a full quit — not just closing the window) and reopen. Claude Desktop reads the config at startup.

### Sanity check

Ask Claude something the LinkedIn MCP can answer: *"using the linkedin MCP, look up Marc Benioff's profile and summarize his recent posts."* First call will pause while the server downloads Chromium and opens a browser window asking you to log into LinkedIn. Sign in once and the session is saved for future calls.

---

## Setup — Part 2: LinkedIn login (once, then persistent)

The wrapper doesn't touch auth at all — it inherits the exact flow from `mcp-server-linkedin`. On the first tool call that needs auth:

1. A browser window opens to LinkedIn's login page.
2. Sign in normally (LinkedIn's 2FA and CAPTCHA prompts work).
3. The session cookie is saved to `~/.linkedin-mcp/profile/` on your Mac and reused on every subsequent call.

If you want to sign in *before* the first tool call — or re-authenticate after LinkedIn logged you out — run this once in Terminal:

```bash
uvx linkedin-mcp-chrome --login
```

---

## Claude skills — the linkedin-research plugin

This repo is also a Claude Desktop / Cowork **plugin marketplace**. It ships one plugin, `linkedin-research`, with four
generic skills that teach Claude how to use this server's tools well — and safely. The skills are optional; the server
works without them.

| Skill | Use it for |
| --- | --- |
| `linkedin-person-research` | One person: find the right profile, current role and tenure from Experience, career path, recent posts, conversation hooks. Also name spellings and roles before a meeting. |
| `linkedin-company-signals` | One company: leadership changes, headcount and function mix, hiring signals, recent posts — plus a partner-fit mode that scores a firm on reach, relevance and readiness. |
| `linkedin-contact-verification` | A list of contacts: still there, title changed, left (and where to), not found, or not checked — before outreach or after a list import. |
| `linkedin-engagement-finder` | Recent posts worth commenting on, filtered by topic, recency, connection degree and author employer, with a drafted comment for each. Never posts. |

All four read `plugins/linkedin-research/references/guardrails.md` first:

- **Session:** on a login, checkpoint or CAPTCHA error, stop and ask you to sign in (`uvx linkedin-mcp-chrome --login`).
  Never fall back to scraping LinkedIn some other way, and never infer employment from other sources.
- **Read-only by default:** `send_message` and `connect_with_person` are used only when you ask, after you approve the
  exact recipient and text — one at a time. There is no posting tool; comments are drafts.
- **Human-scale volume:** targeted lookups, one call at a time, 25 profile lookups per run unless you approve more, no
  harvesting of employee lists.
- **Accuracy:** the Experience section decides someone's current role; every finding carries its URL and read date;
  "not found" beats a guess.

### Install the skills

The plugin **does not bundle the server** — set the server up first (Part 1 and Part 2 above). Two copies of the
server would compete for the same saved browser profile (`~/.linkedin-mcp/profile/`).

1. Claude Desktop → **Customize** → **Marketplace** → **+ Add marketplace** → `kugamon/linkedin-mcp-chrome`.
2. **Sync** → install `linkedin-research` → quit Claude fully (Cmd+Q) and reopen.

Or clone the repo and add `plugins/linkedin-research/` as a local plugin folder. Installed plugins are snapshots: after
a new release, Sync and update the plugin, then restart.

**Verify:** *"Who is the current VP of Sales at Docker, and how long have they been in the role?"* — Claude should find
the company slug, search people at that company, confirm the role from the Experience section, and cite the profile URL
and read date.

---

## The 17 tools

All 17 come from the underlying [`mcp-server-linkedin`](https://pypi.org/project/mcp-server-linkedin/) — this wrapper adds nothing to the surface area.

### Profiles (3)

| Tool | Purpose |
| --- | --- |
| `get_person_profile` | Get a person's profile (experience, education, interests, posts, contact info — selectable sections) |
| `get_my_profile` | Get the authenticated user's own profile |
| `get_sidebar_profiles` | Extract "People you may know" and similar recommendation blocks |

### Companies (3)

| Tool | Purpose |
| --- | --- |
| `get_company_profile` | Get a company's overview + selectable sections |
| `get_company_posts` | Recent posts from a company's feed |
| `get_company_employees` | Employees listed on the company page |

### Search (3)

| Tool | Purpose |
| --- | --- |
| `search_people` | People search with keyword + location filters |
| `search_companies` | Company search |
| `search_jobs` | Job listings search |

### Jobs (2)

| Tool | Purpose |
| --- | --- |
| `get_job_details` | Full detail on a specific posting |
| `get_saved_jobs` | Your saved jobs |

### Messaging (4)

| Tool | Purpose |
| --- | --- |
| `get_inbox` | List recent conversations |
| `get_conversation` | Read one conversation |
| `search_conversations` | Keyword search across messages |
| `send_message` | Send a message (requires explicit confirmation) |

### Connections + feed (2)

| Tool | Purpose |
| --- | --- |
| `connect_with_person` | Send or accept a connection request |
| `get_feed` | Get your home feed |

*(Plus `close_session`, `search_posts` — depending on the exact upstream version.)*

Each tool's full schema is advertised through the MCP `tools/list` method — Claude reads it automatically.

---

## Why a pinned wrapper (vs. just using the upstream directly)

On **2026-08-31**, FastMCP shipped `4.0.0`. It removed the `exclude_args` keyword argument from `@FastMCP.tool()`, which `mcp-server-linkedin` uses in [`tools/person.py`](https://github.com/stickerdaniel/linkedin-mcp-server/blob/main/src/linkedin_mcp_server/tools/person.py). Because upstream's `pyproject.toml` declared `fastmcp>=3.4.4` with no upper bound, every fresh `uvx mcp-server-linkedin@latest` resolution installed FastMCP 4.0 and crashed at import time with:

```
TypeError: FastMCP.tool() got an unexpected keyword argument 'exclude_args'
```

Every Claude Desktop user who had the LinkedIn MCP configured saw it disconnect simultaneously with no config change. This is the same class of bug that hit `mcp-salesforce-connector` when `mcp` 2.0 removed `Server.list_tools()` (see [kugamon/salesforce-mcp-auto-auth-chrome](https://github.com/kugamon/salesforce-mcp-auto-auth-chrome)'s v0.1.1 release notes for that story).

The user-side workaround is `uvx --with "fastmcp<4" mcp-server-linkedin@latest`, but that requires every user to edit their `claude_desktop_config.json`. This wrapper builds the pin into the package metadata so **no user has to know about the workaround** — `uvx linkedin-mcp-chrome` just works, forever, until we drop the pin.

The full write-up — including why upstream ships without upper bounds, the general "pin transitive SDKs" lesson, and how to spot this pattern early — is in [`docs/how-it-works.md`](docs/how-it-works.md).

---

## Local development

If you want to test changes before pushing:

```bash
# Install Python 3.12+ and uv if you don't have them
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and run from source
git clone https://github.com/kugamon/linkedin-mcp-chrome.git
cd linkedin-mcp-chrome
uv sync

# Smoke-test — should print version banner then start the MCP server
uv run python -m linkedin_mcp_chrome --help
```

To point your local Claude Desktop config at the working copy instead of the published version, change the args to:

```jsonc
"args": ["run", "--directory", "/absolute/path/to/your/checkout", "python", "-m", "linkedin_mcp_chrome"]
```

---

## When will the pin come off?

When upstream `mcp-server-linkedin` releases a version compatible with FastMCP 4.x. At that point this wrapper's next release will:

1. Bump the `fastmcp` upper bound (either to `<5.0` or drop it entirely, depending on how upstream chooses to handle it)
2. Note it in the version history
3. Users get the update automatically the next time `uvx` refreshes its cache

Track: [stickerdaniel/linkedin-mcp-server issues](https://github.com/stickerdaniel/linkedin-mcp-server/issues) for the port PR.

---

## LinkedIn TOS + ban risk (from the upstream author)

LinkedIn's TOS prohibits automated tools. Per the upstream README: *"With normal usage (not bulk scraping!) you're not risking a ban. So far, no users have been banned for using this MCP."* Prompt your Claude agents to make targeted, human-scale requests — a profile lookup here, a search there — not a script that pulls 500 profiles in an hour.

If LinkedIn does throttle you, back off and reduce your usage. This wrapper doesn't change any of that — it inherits everything from upstream, including the browser-based session, the persistent profile, and the per-tool rate limiting.

---

## Troubleshooting

**Claude shows "Server disconnected" at startup**: Look at `~/Library/Logs/Claude/mcp-server-linkedin.log` for the actual Python traceback. If you see `TypeError: FastMCP.tool() got an unexpected keyword argument 'exclude_args'` — you're not using this wrapper, you're using the raw `mcp-server-linkedin`. Switch your config to `uvx linkedin-mcp-chrome` and the pin will prevent the crash.

**First tool call hangs for ~90 seconds**: The upstream MCP server downloads Patchright Chromium (~40 MB) the first time it needs to authenticate. Once. After that, calls are fast. `UV_HTTP_TIMEOUT=300` in your config gives it the runway.

**Every tool call returns an auth error**: Your LinkedIn session expired. Run `uvx linkedin-mcp-chrome --login` in Terminal, sign in via the browser window that pops up, and retry.

**Chromium won't launch on my Mac**: This is an upstream `mcp-server-linkedin` issue. Check `~/.linkedin-mcp/patchright-browsers/` — if it's empty or corrupt, delete it and let the next tool call re-download. Also check that macOS Gatekeeper hasn't quarantined the Chromium binary.

**I want to opt out of the pin and track the latest FastMCP**: Then use the upstream package directly (`uvx mcp-server-linkedin@latest`). You're back to being exposed to the next major-version bump.

---

## Version history

- **v0.2.0** — adds the `linkedin-research` Claude plugin (four skills + guardrails) and makes the repo a plugin marketplace. The Python package is unchanged apart from the version number.
- **v0.1.0** — initial release on PyPI. Wraps `mcp-server-linkedin>=4.23.1`, pins `fastmcp>=3.4.4,<4.0`. macOS + Chromium (Patchright) via upstream — no direct browser interaction from this wrapper.

---

## License

MIT — see [LICENSE](LICENSE). This project is not affiliated with or endorsed by LinkedIn, Microsoft or Anthropic. LinkedIn is a trademark of LinkedIn Corporation.
