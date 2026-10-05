---
name: "linkedin-engagement-finder"
description: "Find recent LinkedIn posts worth commenting on — by topic, recency, author's connection degree and employer type, skipping recruiter spam and posts the user already commented on — and draft a specific, non-salesy comment for each, through the LinkedIn MCP server's post search. Never posts: the user publishes comments themselves. Use when the user asks \"find posts I should comment on\", \"LinkedIn engagement\", \"grow my following\", \"what's being discussed about [topic] on LinkedIn\", \"posts from 2nd-degree connections about [topic]\", \"help me engage with [audience] on LinkedIn\", or runs a recurring engagement routine."
---

# LinkedIn engagement finder

Surface a short list of recent, substantive posts where a thoughtful comment from the user would add value and reach
the right people — and draft those comments. **Read `${CLAUDE_PLUGIN_ROOT}/references/guardrails.md` first.** There is
no comment or post tool: everything here is a draft for the user to publish.

## Set the filters (ask once, then reuse)

- **Topics** — 3–6 keyword phrases (product category, problems, platforms). Quote multi-word phrases.
- **Recency** — default the past two weeks (`date_posted="past-week"` or `"past-month"`, then keep posts ≤ 14 days old).
- **Connection degree** — e.g. 2nd-degree only (reach beyond the user's network without being strangers), or any.
- **Author employer type** — include (e.g. partners, agencies, practitioners at customer-type companies) and exclude
  (e.g. competitors, vendors selling to the same audience).
- **Substance** — skip job ads and recruiter posts ("we're hiring", "send your CV", day rates, C2C), pure self-promotion
  and engagement bait.
- **Count** — default 10–20 candidates.

## Steps

1. **Search.** `search_posts` once per topic phrase with the recency filter (default `max_pages`). Collect author name,
   profile link, connection degree (as shown in the post text — if it isn't shown, treat it as unknown rather than
   guessing), date and text. Optionally add the user's own feed (`get_feed`) for posts
   already in their network.
2. **Filter.** Drop posts outside recency, the degree filter, or that fail the substance test. Deduplicate authors.
3. **Verify authors** that pass (within the volume cap): `get_person_profile` with `sections="experience"` — current
   employer, to apply the include/exclude employer rules. Drop mismatches.
4. **Already commented?** The tools can't reliably read the user's comment history. Ask the user to paste or skim their
   recent comments, or mark each candidate "check you haven't already commented".
5. **Rank** by topic fit, author relevance, recency and discussion already happening on the post.
6. **Draft a comment for each** — 2–4 sentences, specific to the post (agree, add a concrete example or data point,
   or ask a real question), in the user's voice if a voice guide is available, no links or product pitches unless the
   user asks, no flattery openers ("Great post!").

## Output

A ranked list: author (name, title, employer, degree) · post date · one-line summary · post link · why it's worth it ·
draft comment. End with the filters used, so the next run can repeat them, and the count of posts dropped by each filter.
