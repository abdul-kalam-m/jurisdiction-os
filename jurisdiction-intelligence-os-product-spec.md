# Jurisdiction Intelligence OS — One-Page Product Spec

## Product Summary
Jurisdiction Intelligence OS is a B2B proptech platform for developers, AEC firms, lenders, and permit expediters that predicts permitting and entitlement friction before a project team commits time and capital to a site or jurisdiction [cite:38][cite:41]. The product combines permit records, zoning data, planning-board intelligence, and workflow benchmarks into a single decision-support layer that helps teams answer a simple question: how difficult will it be to get approved here, for this project, under current conditions [cite:35][cite:37][cite:40].

## Problem
Real estate teams often make early site and jurisdiction decisions with incomplete information about local approval timelines, hidden submission requirements, planning-board risk, and resubmittal friction [cite:37][cite:40]. Permitting and planning data is usually public in theory but fragmented across municipal portals, PDFs, open-data sites, scanned documents, and inconsistent local processes, making it hard to compare jurisdictions at scale or predict approval risk reliably [cite:29][cite:37].

## Users
Primary users are developers, acquisition teams, architects, civil engineers, land-use attorneys, permit expediters, and lenders evaluating project feasibility and execution risk across markets [cite:38][cite:41]. These users need faster go/no-go decisions, clearer requirements, and a way to benchmark one jurisdiction against another before a filing is made [cite:35][cite:40].

## Value Proposition
The platform acts like a permitting and entitlement intelligence layer for site selection and predevelopment, giving teams a faster way to assess approval complexity, identify required steps, and avoid predictable delays [cite:38][cite:37]. Instead of manually researching every city and county, users receive a jurisdiction scorecard, project-specific permit path, zoning-fit context, and alerts on recent planning or policy changes that may affect risk [cite:41][cite:29][cite:38].

## MVP Scope
The first release should focus on five modules [cite:35][cite:38]:
- Jurisdiction scorecards with median permit-cycle benchmarks, review-stage visibility, and confidence scores derived from available records [cite:35][cite:37].
- Project fit checker where a user enters parcel, use type, size, and scope to receive likely permits, hearings, and review dependencies [cite:41][cite:40].
- Dynamic submission checklist by jurisdiction, permit type, and project class using local rules and observed workflow steps [cite:29][cite:40].
- Planning and zoning signal feed that tracks board actions, zoning changes, and local government decision intelligence [cite:38].
- Delay alerts for monitored jurisdictions when similar projects or reviews appear to be moving slower than normal [cite:35][cite:37].

## Data Sources
The initial data stack should blend third-party APIs with direct public-record collection because speed to market matters more than building full raw-data coverage on day one [cite:35][cite:37]. Strong starting inputs include nationwide permit data from BatchData, local government and planning intelligence from Shovels.ai, zoning and parcel-rule data from Zoneomics, and municipal open-data portals where workflow datasets are available [cite:35][cite:38][cite:41][cite:29]. Over time, the core moat should come from normalization, historical benchmarking, hearing-decision extraction, and structured records recovered from fragmented local systems [cite:37][cite:38].

## Business Model
The primary business model should be B2B SaaS sold on annual subscriptions, with pricing based on seats, jurisdictions covered, and workflow depth [cite:35][cite:41]. A second revenue layer can come from API access, bulk data exports, custom market studies, and enterprise benchmarking for larger developers, lenders, and proptech partners that want the intelligence embedded in internal workflows [cite:35][cite:37].

## Pricing Structure
| Tier | Target buyer | Pricing logic | Included value |
|---|---|---|---|
| Starter | Small developer, expediter | Per-seat monthly or annual plan [cite:41] | Limited jurisdictions, scorecards, checklists, basic AI assistant [cite:40][cite:41] |
| Pro | Regional developer, AEC firm | Team subscription [cite:35][cite:38] | More markets, alerts, exports, collaboration features [cite:35][cite:38] |
| Enterprise | National developers, lenders, platforms | Custom contract [cite:35][cite:41] | API access, SSO, custom models, dedicated onboarding [cite:35][cite:41] |
| Data Services | Consultants, investors, research teams | Add-on or project fee [cite:35][cite:37] | Historical extracts, white-label feeds, benchmark reports [cite:35][cite:37] |

## Go-to-Market
The best initial wedge is a narrow geography and asset type, such as multifamily or small commercial development in regions with fragmented municipal processes and visible approval pain [cite:29][cite:37]. Early sales should target developers and expediters first, because they feel the pain immediately and can adopt faster than public-sector buyers, even though the same data foundation may later support government-facing products [cite:16][cite:39].

## Success Metrics
The MVP should be measured on three outcomes: time saved during jurisdiction research, accuracy of permit-path recommendations, and customer-reported reduction in unexpected approval delays [cite:37][cite:40]. Commercial traction should be tracked through paid pilots, renewal rates, monitored jurisdictions per account, and attach rate for data exports or enterprise integrations [cite:35][cite:38].

## Product Positioning
A concise positioning statement is: **Bloomberg Terminal for local permitting and entitlement risk** [cite:37][cite:38]. The product wins if it becomes the default system developers open before land is tied up, consultants are engaged, or a permit package is assembled [cite:38][cite:40].
