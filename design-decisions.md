# Design decisions

- Positioning is the user-provided line 以算法与数据测量内容，以视听与审美理解用户. Earlier drafts (creator-centred, capability checklist, "turn data back into film", "taste for AI") were rejected for losing the data side, reading defensive, or pointing at film jobs.
- Profile README with animated SVGs rather than a separate website: it is what a recruiter sees at github.com/Baixue-Wu, and SVG keeps motion without JavaScript.
- Hero is a film strip passing a scanner: frames from her own works on the right (watched), their k-means palettes on the left (measured). The scanner line splits the slogan into its two halves, so the layout itself states the positioning.
- The page is organised by the slogan's halves: 01 测量内容 (three papers, NextHook) and 02 理解用户 (MoCoCo, CineAtlas, InkMuse, AI videos, 寂寞花芳).
- Only her own works and the public-domain Sherlock Jr. are shown. Commentary videos built on Marvel footage are excluded for copyright.
- All text is converted to outlines because fonts do not load inside <img> SVGs; LXGW WenKai Lite replaces the full WenKai because fontTools cannot read the full font's cmap.
