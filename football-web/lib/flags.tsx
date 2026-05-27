"use client"

import Image from "next/image"

/**
 * FIFA 3-letter code → ISO 2-letter code mapping for all 48 World Cup 2026 teams.
 * Used to resolve flag image URLs from flagcdn.com.
 */
const FIFA_TO_ISO: Record<string, string> = {
  MEX: "mx",
  RSA: "za",
  KOR: "kr",
  CZE: "cz",
  CAN: "ca",
  BIH: "ba",
  QAT: "qa",
  SUI: "ch",
  BRA: "br",
  MAR: "ma",
  HAI: "ht",
  SCO: "gb-sct",
  USA: "us",
  PAR: "py",
  AUS: "au",
  TUR: "tr",
  GER: "de",
  CUW: "cw",
  CIV: "ci",
  ECU: "ec",
  NED: "nl",
  JPN: "jp",
  SWE: "se",
  TUN: "tn",
  BEL: "be",
  EGY: "eg",
  IRN: "ir",
  NZL: "nz",
  ESP: "es",
  CPV: "cv",
  KSA: "sa",
  URU: "uy",
  FRA: "fr",
  SEN: "sn",
  IRQ: "iq",
  NOR: "no",
  ARG: "ar",
  ALG: "dz",
  AUT: "at",
  JOR: "jo",
  POR: "pt",
  COD: "cd",
  UZB: "uz",
  COL: "co",
  ENG: "gb-eng",
  CRO: "hr",
  GHA: "gh",
  PAN: "pa",
}

const NAME_TO_ISO: Record<string, string> = {
  mexico: "mx",
  "south africa": "za",
  "south korea": "kr",
  "czech republic": "cz",
  canada: "ca",
  "bosnia and herzegovina": "ba",
  qatar: "qa",
  switzerland: "ch",
  brazil: "br",
  morocco: "ma",
  haiti: "ht",
  scotland: "gb-sct",
  "united states": "us",
  paraguay: "py",
  australia: "au",
  turkey: "tr",
  germany: "de",
  curacao: "cw",
  "cote d'ivoire": "ci",
  ecuador: "ec",
  netherlands: "nl",
  japan: "jp",
  sweden: "se",
  tunisia: "tn",
  belgium: "be",
  egypt: "eg",
  iran: "ir",
  "new zealand": "nz",
  spain: "es",
  "cape verde": "cv",
  "saudi arabia": "sa",
  uruguay: "uy",
  france: "fr",
  senegal: "sn",
  iraq: "iq",
  norway: "no",
  argentina: "ar",
  algeria: "dz",
  austria: "at",
  jordan: "jo",
  portugal: "pt",
  "dr congo": "cd",
  uzbekistan: "uz",
  colombia: "co",
  england: "gb-eng",
  croatia: "hr",
  ghana: "gh",
  panama: "pa",
}

/** flagcdn.com only serves these specific widths. */
const VALID_WIDTHS = [20, 40, 80, 160, 320, 640, 1280]

function snapToValidWidth(px: number): number {
  for (const w of VALID_WIDTHS) {
    if (w >= px) return w
  }
  return VALID_WIDTHS[VALID_WIDTHS.length - 1]
}

function resolveIso(codeOrName: string): string | undefined {
  const upper = codeOrName.toUpperCase()
  if (FIFA_TO_ISO[upper]) return FIFA_TO_ISO[upper]
  return NAME_TO_ISO[codeOrName.toLowerCase()]
}

interface TeamFlagProps {
  code: string
  size?: number
  className?: string
}

export function TeamFlag({ code, size = 48, className }: TeamFlagProps) {
  const iso = resolveIso(code)
  if (!iso) {
    return (
      <div className={className} style={{ width: size, height: size }} />
    )
  }

  const cdnWidth = snapToValidWidth(size * 2)

  return (
    <Image
      src={`https://flagcdn.com/w${cdnWidth}/${iso}.webp`}
      alt={`${code} flag`}
      width={size}
      height={size}
      className={className}
      unoptimized
    />
  )
}
