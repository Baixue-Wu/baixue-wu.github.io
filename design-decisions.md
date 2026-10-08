# Design decisions

- Positioning is the user-provided line 以算法与数据测量内容，以视听与审美理解用户. Earlier drafts (creator-centred, capability checklist, "turn data back into film", "taste for AI") were rejected for losing the data side, reading defensive, or pointing at film jobs.
- Profile README with animated SVGs rather than a separate website: it is what a recruiter sees at github.com/Baixue-Wu, and SVG keeps motion without JavaScript.
- Hero is a film strip passing a scanner: frames from her own works on the right (watched), their k-means palettes on the left (measured). The scanner line splits the slogan into its two halves, so the layout itself states the positioning.
- Content is organised by type, in plain words a recruiter understands: 项目 (four AI product prototypes), 视频作品 (寂寞花芳, AI videos), 论文与课题 (three papers, one funded study). The slogan lives only in form, light and motion: data visuals in cyan, film in amber, the scanner in the hero. An earlier version that sorted content by the slogan's two halves was rejected as unclear to interviewers.
- Only her own works and the public-domain Sherlock Jr. are shown. Commentary videos built on Marvel footage are excluded for copyright.
- All text is converted to outlines because fonts do not load inside <img> SVGs; LXGW WenKai Lite replaces the full WenKai because fontTools cannot read the full font's cmap.
