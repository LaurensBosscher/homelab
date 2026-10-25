import { R2Explorer } from "r2-explorer";

// files.bosscher.ch is an exact Access app for ACCESS_EMAIL_LAURENS only.
// The team check rejects a request that skipped that app. /share/* stays
// behind the same hostname policy; do not add an Access bypass for it.
export default R2Explorer({
  readonly: false,
  cfAccessTeamName: "laurens-bosscher",
});
