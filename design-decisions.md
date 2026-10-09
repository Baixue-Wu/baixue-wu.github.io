# Design decisions

- The homepage is a GitHub Pages site (baixue-wu.github.io), not a profile README. A first version was built as a profile README by mistake and rebuilt as this site.
- Positioning is the user-provided line 以算法与数据测量内容，以视听与审美理解用户, expressed only through visuals. Content is grouped by type (projects, videos, research) because sorting by the slogan's halves was unclear to interviewers.
- Hero: frames from her works run past a scanner that follows the pointer. Right of it the frame is watched (image), left of it measured (k-means palette with hex and HSV). The slogan sits in two halves on either side.
- Every video has its own film barcode (mean colour of evenly spaced moments) as the scrubber, so the measuring idea is something visitors use, not only look at.
- Dark projection-room look with film grain, a projector light cone and flicker; data elements in cyan, film elements in amber.
- Self-hosted subset fonts and no CDN, for access from mainland China.
- UCL status is written Visitor (研究访问), as on her UCL ID card.

- Host the three project demos under the existing portfolio GitHub Pages site, with separate demo and source links. Ship only built static assets and licenses, plus source revision and file hashes; no backend, private configuration or runtime data.

- Project contribution descriptions cover product direction, requirements, interaction design and prototype iteration, as confirmed by the user on 2026-10-09. Name the concrete workflow for each project. Omit tool usage from these descriptions at the user's request.
- All project website links use the label 网址, as requested by the user on 2026-10-09, for consistent navigation beside the code links.
