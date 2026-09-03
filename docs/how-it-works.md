# How it works

This doc captures the whole story: what broke, why upstream shipped it in a way that could break, what this wrapper does about it, and when the pin should come off. If you're a customer setting up the LinkedIn MCP, you probably don't need to read this — the README's setup guide is enough. If you're extending or debugging the wrapper, or hitting the same "silent breakage from an unpinned transitive dep" pattern on some other MCP server, read on.

## The failure mode

On **2026-08-31**, [FastMCP](https://pypi.org/project/fastmcp/) shipped version **4.0.0** — the first stable release in the 4.x series, following a month of alpha/beta releases. Among the API changes, 4.0.0 removed the `exclude_args` keyword argument from `@FastMCP.tool()`.

That morning, every Claude Desktop user who had the LinkedIn MCP configured saw the same thing: their LinkedIn MCP server disconnected simultaneously with no config change on their side. Restarting Claude Desktop didn't help — the server crashed at import time on every launch. The `mcp-server-linkedin.log` had this traceback:

```
Traceback (most recent call last):
  File ".../linkedin_mcp_server/cli_main.py", line 563, in main
    mcp = create_mcp_server(tool_timeout=config.server.tool_timeout_seconds)
  File ".../linkedin_mcp_server/server.py", line 273, in create_mcp_server
    register_person_tools(mcp, tool_timeout=tool_timeout)
  File ".../linkedin_mcp_server/tools/person.py", line 31, in register_person_tools
    @mcp.tool(
        timeout=tool_timeout,
        ...
        exclude_args=["extractor"],
    )
TypeError: FastMCP.tool() got an unexpected keyword argument 'exclude_args'
```

The root cause is textbook and boring. It also strikes at random.

## Root cause

`mcp-server-linkedin` declares its FastMCP dependency in `pyproject.toml` as:

```toml
dependencies = [
    ...
    "fastmcp>=3.4.4",
    ...
]
```

Note the **absence of an upper bound**. When `uvx` builds an ephemeral environment on each cold launch, it uses "the latest compatible version" of every dependency. Before 2026-08-31, that was FastMCP 3.4.7. After, that was 4.0.0. The wrapper had no way to know that "the next FastMCP release will break me."

That's not the maintainer's fault, exactly. Python's packaging ecosystem doesn't have a strong culture of upper bounds — pip's docs discourage them, and library maintainers routinely omit them under the assumption that "SDKs are supposed to follow semver, so `>=3.4.4` is fine." SDKs often *don't* follow semver strictly, and even when they do, a major-version bump is exactly the moment your users all get broken.

This exact pattern also hit `mcp-salesforce-connector` on **2026-07-28** when the `mcp` SDK shipped 2.0.0 and removed `Server.list_tools()`. Same shape, same fix. See lesson #6 in [`kugamon/salesforce-mcp-auto-auth-chrome`'s docs](https://github.com/kugamon/salesforce-mcp-auto-auth-chrome/blob/main/docs/how-it-works.md#what-we-learned-thats-generally-useful-for-mcp-wrappers) for the full "pin transitive SDKs" lesson.

## The user-side workaround

The immediate fix any user could apply: change their Claude Desktop config from

```json
"args": ["mcp-server-linkedin@latest"]
```

to

```json
"args": ["--with", "fastmcp<4", "mcp-server-linkedin@latest"]
```

`uvx --with` adds a resolver constraint to the ephemeral environment, forcing `fastmcp` to stay on 3.x.

That works, but it requires:

1. Every user to know the workaround exists
2. Every user to edit their `claude_desktop_config.json`
3. Every user to restart Claude Desktop
4. Users to remember to remove the pin later, when upstream ports to FastMCP 4

Not great UX for people who just want a LinkedIn MCP that works.

## What this wrapper does about it

This package (`linkedin-mcp-chrome`) exists to move the workaround from *the user's config* to *the package metadata*. Instead of every user typing `--with "fastmcp<4"`, they type `uvx linkedin-mcp-chrome`, and the pin lives in *our* `pyproject.toml`:

```toml
dependencies = [
    "mcp-server-linkedin>=4.23.1",
    "fastmcp>=3.4.4,<4.0",
]
```

At install time, `uvx` merges the constraints from both packages (`mcp-server-linkedin`'s `fastmcp>=3.4.4` and ours `<4.0`), picks the intersection (`>=3.4.4,<4.0`), and installs a FastMCP 3.x that both packages agree with.

At runtime, `__main__.py` is a two-line entry point that just calls `linkedin_mcp_server.cli_main:main`. **No monkey-patching, no wrappers around any tool, no override of any upstream behavior.** The wrapper is a pure dependency-resolution shim.

## Why this is different from the Salesforce wrapper pattern

`kugamon/salesforce-mcp-auto-auth-chrome` also fixes a similar dep-pin issue as part of its v0.1.1 release, but its **primary** value is the Chrome-cookie-based auth-refresh mechanism (a runtime patch of `simple_salesforce._call_salesforce`). It's a full wrapper that adds real behavior.

`linkedin-mcp-chrome` is a **pure dep-pin wrapper**. It adds nothing at runtime. Its sole value is that it lets `uvx linkedin-mcp-chrome` be a stable, no-config-required install for as long as FastMCP 4.x is broken with upstream's code.

There's an argument for making this wrapper do more — add cookie-based auth via `pycookiecheat` (LinkedIn's session cookies are just as extractable as Salesforce's), or bypass the Chromium download, or provide a fallback authentication path. We chose not to for v0.1.0 because upstream already handles LinkedIn auth well with a persistent browser profile, and adding more would mean maintaining more surface area. Future versions can layer in more if it becomes useful.

## When the pin comes off

The moment `mcp-server-linkedin` ships a version that works with FastMCP 4.x, we release a new version of this wrapper that either:

- Bumps the upper bound to `<5.0` (defensive posture — still pin, but pin the *next* major)
- Or drops the pin entirely (`fastmcp>=3.4.4`) if we trust upstream to have upper-bounded it themselves

We prefer option 1 as a matter of policy — pinning to the current major-version-you-know-works is cheap insurance and imposes zero cost on users. See the "pin transitive SDKs" lesson.

Track: [stickerdaniel/linkedin-mcp-server issues](https://github.com/stickerdaniel/linkedin-mcp-server/issues) for the FastMCP 4 port PR. When it lands and a compatible mcp-server-linkedin version ships, we'll release the next `linkedin-mcp-chrome` version within a few days.

## What we tried first and discarded

| Attempt | Why we didn't |
|---|---|
| PR the pin directly to `stickerdaniel/linkedin-mcp-server` and wait | We should also do this (and did — see the issue we opened). But merging + release takes time; users need a fix *today*. |
| Fork `mcp-server-linkedin` outright | Maintenance burden. We'd be tracking upstream's features, tests, and browser-profile changes forever. The whole point is to *stay* on upstream. |
| Ship a Cloudflare Worker like `kugamon/hubspot-mcp` | LinkedIn auth requires a real browser session with cookies stored locally. A remote MCP can't do that. |
| Bundle a `--with "fastmcp<4"` flag into the config with our other Claude Desktop customization | That's the user-side workaround. Same problem — users have to know about it and manually add it. |
| Write a wrapper that adds `--with "fastmcp<4"` invisibly via a shell script that calls `uvx` | Fragile, needs the shell script installed somewhere on PATH, doesn't survive `uvx` cache refresh cleanly. A Python package with a proper `pyproject.toml` pin is the right primitive. |

## What we learned that's generally useful

1. **Any MCP server whose Python dependencies aren't upper-bounded is a landmine waiting to blow up.** SDK maintainers ship breaking changes on major-version bumps as a matter of policy. If your wrapper doesn't upper-bound the SDKs your imports reach, `uvx` will eventually surface the breakage on every user's machine at the same moment.
2. **Fixing it at the package level is 100x better UX than fixing it at the user config level.** Users don't know or care which of their MCPs is affected by which SDK breakage. A pin in your package's metadata is invisible to them.
3. **A "pure dep-pin wrapper" is a legitimate package.** It doesn't need to add runtime behavior to be useful. Its value is *making the install command shorter and less fragile* for the customer.
4. **When you file the upstream issue, offer the PR.** A one-line pin PR is trivial for the maintainer to review and merge. The offer of a PR removes the friction from their side and often accelerates the fix by weeks.
5. **Same pattern will happen again.** `mcp` 2.0 broke `mcp-salesforce-connector`. `fastmcp` 4.0 broke `mcp-server-linkedin`. Any MCP wrapper you build should upper-bound `mcp` and `fastmcp` at the current-major-you-tested-against, and bump both explicitly when you re-test.
