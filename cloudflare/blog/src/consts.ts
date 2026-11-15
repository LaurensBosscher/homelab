import type { Site, Metadata, Socials } from "@types";

export const SITE: Site = {
  NAME: "Bosscher",
  EMAIL: "laurens@laurensbosscher.nl",
  NUM_POSTS_ON_HOMEPAGE: 3,
  NUM_WORKS_ON_HOMEPAGE: 0,
  NUM_PROJECTS_ON_HOMEPAGE: 2,
};

export const HOME: Metadata = {
  TITLE: "Home",
  DESCRIPTION: "Notes from Laurens Bosscher.",
};

export const BLOG: Metadata = {
  TITLE: "Blog",
  DESCRIPTION: "Notes on homelab, DNS, and low-power tinkering.",
};

export const WORK: Metadata = {
  TITLE: "Resume",
  DESCRIPTION: "Resume and background — hosted at bosscher.ch.",
};

export const PROJECTS: Metadata = {
  TITLE: "Projects",
  DESCRIPTION: "Selected open-source projects.",
};

export const SOCIALS: Socials = [
  {
    NAME: "github",
    HREF: "https://github.com/LaurensBosscher",
  },
  {
    NAME: "linkedin",
    HREF: "https://linkedin.com/in/laurensbosscher",
  },
];

export const RESUME_URL = "https://bosscher.ch";
