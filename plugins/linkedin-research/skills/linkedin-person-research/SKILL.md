---
name: "linkedin-person-research"
description: "Research one person on LinkedIn through the LinkedIn MCP server — find the right profile, then their current role and tenure from the Experience section, career path, education, recent posts and conversation hooks — and return a sourced brief. Also checks how a name is spelled and what someone's role is before a meeting. Use when the user asks \"who is [name] at [company]\", \"look up [person] on LinkedIn\", \"research [person] before my call\", \"pre-call research\", \"what does [name] do now\", \"find their LinkedIn\", \"background on the attendees\", \"enrich this contact\", or gives a LinkedIn profile URL and wants a summary. Read-only. For many people at once use linkedin-contact-verification; for the company use linkedin-company-signals."
---

# LinkedIn person research

Find the right person on LinkedIn and turn their profile into a short, sourced brief the user can act on — before a call,
a meeting, outreach, or a record update. **Read `${CLAUDE_PLUGIN_ROOT}/references/guardrails.md` first.** The short
version: stop and ask the user to log in on an auth error, never scrape another way, read-only, human-scale volume, the
Experience section decides the current role, never fabricate.

## Inputs

Ask only for what's missing: the person's name and company (or a LinkedIn profile URL), and what the research is for
(a sales call, a meeting, hiring, a partnership, updating a record). The purpose decides which sections to pull.

## Steps

1. **Find the profile.**
   - Have a URL or username? Use it.
   - Otherwise `search_people` with `keywords` = "name company" (add `location` when the name is common). To restrict to
     one employer, look up the company's numeric id with `get_company_profile` (`references["about"]`) and pass it as
     `current_company` — a plain company name is ignored by that filter.
   - More than one plausible match: compare company, title and location; if two remain, show both and ask.
2. **Read the profile** with `get_person_profile`. Request only the sections the purpose needs:
   - Always `experience` (the source of truth for the current role and tenure).
   - Meeting or call prep: add `posts` for recent activity.
   - Background depth: `education`, `skills`, `certifications`.
   - `contact_info` only when the user needs a way to reach the person.
3. **Work out the facts:**
   - Current role = the position ending "Present"; tenure from its start date (flag under six months — new in role).
   - Previous employers and roles, especially prior companies the user's business has worked with or competed with.
   - If the headline disagrees with Experience, report Experience and note the difference.
4. **Find conversation hooks** from what they publish: recent posts and the topics they care about, things they
   announced, shared context with the user (`get_my_profile` only if the user wants shared background compared).
5. **Optional company context:** for one or two lines on the employer, `get_company_profile`; for anything deeper, hand
   off to `linkedin-company-signals`.

## Output

- **Person** — name (spelled as on LinkedIn), current title and company, location, profile URL
- **Role and tenure** — start date, time in role, "new in role" flag
- **Career path** — 2–4 lines of relevant prior roles
- **What they talk about** — recent post themes with dates (if posts were read)
- **Conversation hooks** — 2–3 specific, non-creepy openers grounded in what they published
- **Gaps and confidence** — what couldn't be found or confirmed, and any name/title discrepancies the user should fix
  in their own records
- Every fact carries its URL and the date it was read.

## Variant: meeting attendees

For a list of attendees, run steps 1–3 per person (respecting the volume cap), lead with **name spellings and current
titles** — transcription tools and email signatures get these wrong — and flag anyone whose role changed recently.
