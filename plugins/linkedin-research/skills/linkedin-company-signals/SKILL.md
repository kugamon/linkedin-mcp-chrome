---
name: "linkedin-company-signals"
description: "Read a company's LinkedIn presence for buying and change signals through the LinkedIn MCP server — profile basics, leadership changes (new or departed executives), headcount and function mix, hiring signals from job posts and \"we're hiring\" posts, and recent company posts — or evaluate a firm as a potential partner (practice areas, reach, relevance, readiness). Use when the user asks \"what's happening at [company]\", \"any leadership changes at [company]\", \"is [company] hiring\", \"how big is [company]\", \"who runs sales at [company]\", \"account signals\", \"company research on LinkedIn\", \"should we partner with [firm]\", \"evaluate this consulting partner\", or gives a LinkedIn company URL. Read-only. For one person use linkedin-person-research."
---

# LinkedIn company signals

Turn a company's LinkedIn presence into signals the user can act on: who leads it now, what changed, whether it is
growing, what it is hiring for, and what it is saying. A partner-fit mode evaluates a firm as a potential partner.
**Read `${CLAUDE_PLUGIN_ROOT}/references/guardrails.md` first** (auth errors → ask to log in; read-only; human-scale
volume; no bulk harvesting of employee lists).

## Steps

1. **Find the company.** Slugs are not display names — use `search_companies` and pick the slug from the results,
   unless the user gave a URL. Then `get_company_profile` (add `sections="jobs"` for hiring, `"posts"` for activity).
   Note the numeric company id in `references["about"]`; people searches need it.
2. **Leadership.** `search_people` with `current_company` = the numeric id and keywords for the roles that matter
   (e.g. "CEO", "CFO", "VP Sales", "Head of Revenue Operations"; one search per role family). For each leader found,
   confirm with `get_person_profile` (`sections="experience"`): start date in role (flag new in the last 6–12 months),
   and the previous holder if visible. For a departure, check the person's profile for a newer employer.
3. **Size and shape.** `get_company_employees` returns the employee list plus a demographics breakdown (functions,
   locations, schools). Report the function mix and the employee count LinkedIn shows — **don't** page through or copy
   the employee list.
4. **Hiring.** Open roles from the profile's `jobs` section or `search_jobs` (keywords + company name); informal hiring
   from `search_posts` (e.g. "[company] hiring", past month). Hiring for a function is a signal about investment there.
5. **What they're saying.** `get_company_posts` — product launches, funding, partnerships, events, executive
   announcements. Date each one.
6. **Interpret, briefly.** For each signal, one line on why it matters for the user's purpose (a new CRO often reviews
   the sales stack; a hiring wave in finance may mean new systems). Separate fact from inference.

## Partner-fit mode

When the user is evaluating a firm (consultancy, agency, software partner) as a partner:
- **Practice:** services and practice areas from the About page and posts; the industries and company sizes it serves;
  certifications or partner badges it mentions.
- **Reach:** follower count, size, the visibility of its key people (their posts and followings), events it speaks at.
- **Relevance:** overlap between its clients and practice and the user's own market — ask the user for their ideal
  customer profile if it isn't known.
- **Readiness:** whether it already promotes a competing or complementary product, who would own a partnership (alliances
  or practice lead), and how reachable they are.
- Score **Reach, Relevance and Readiness 1–5** with one line of evidence each, and name the best first contact.

## Output

- **Snapshot** — name, URL, industry, HQ, size band, follower count, read date
- **Leadership** — current leaders by role with start dates; changes in the last 12 months
- **Headcount and function mix** — as LinkedIn shows it, with the date
- **Hiring** — open roles by function, notable informal hiring posts
- **Recent activity** — dated posts worth knowing about
- **What it means** — 3–5 lines tying signals to the user's purpose (or the partner scorecard)
- **Gaps** — what LinkedIn didn't show; every item carries its URL
