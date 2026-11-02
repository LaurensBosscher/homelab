import { defineAstroPaperConfig } from "./src/types/config";

export default defineAstroPaperConfig({
  site: {
    url: "https://blog.bosscher.ch/",
    title: "Bosscher",
    description: "Notes from Laurens Bosscher.",
    author: "Laurens Bosscher",
    ogImage: "default-og.jpg",
    lang: "en",
    timezone: "Europe/Zurich",
    dir: "ltr",
  },
  posts: {
    perPage: 5,
    perIndex: 4,
  },
  features: {
    lightAndDarkMode: true,
    dynamicOgImage: true,
    showArchives: true,
    showBackButton: true,
    editPost: {
      enabled: true,
      url: "https://github.com/LaurensBosscher/homelab/edit/main/cloudflare/blog/",
    },
    search: "pagefind",
  },
  socials: [
    { name: "github", url: "https://github.com/LaurensBosscher" },
  ],
  shareLinks: [
    { name: "x", url: "https://x.com/intent/post?url=" },
    { name: "mail", url: "mailto:?subject=See%20this%20post&body=" },
  ],
});
