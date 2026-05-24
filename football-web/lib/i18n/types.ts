export type Locale = "zh-CN" | "en-US"

export interface LocaleMessages {
  header: {
    title: string
    subtitle: string
    local: string
    hostCity: string
    timeline: string
    bracket: string
  }
  timeline: {
    stageGroup: string
    stageR32: string
    stageR16: string
    stageQF: string
    stageSF: string
    stage3rd: string
    stageFinal: string
    stageRest: string
  }
  match: {
    title: string
    live: string
    bigMatch: string
    upcoming: string
    finished: string
    ft: string
    vs: string
    local: string
    matchActivity: string
    fanSupport: string
    castVote: string
    cheer: string
  }
  bracket: {
    knockoutStage: string
    roadToGlory: string
    quarterFinals: string
    semiFinals: string
    final: string
    vs: string
    liveMatch: string
    winnerAdvances: string
    advancementPath: string
  }
  ai: {
    copilotTitle: string
    analyticsEngine: string
    quickPrompts: string
    placeholder: string
    disclaimer: string
    processing: string
    winProbability: string
    draw: string
    keyInsights: string
    welcomeMessage: string
    demoResponse: string
    quickPrompt1: string
    quickPrompt2: string
    quickPrompt3: string
    quickPrompt4: string
    statATK: string
    statDEF: string
    statPOSS: string
    statFORM: string
  }
  footer: {
    liveUpdates: string
    teamsCitiesMatches: string
    dataRefreshed: string
    fifaBrand: string
  }
  common: {
    weekdayMon: string
    weekdayTue: string
    weekdayWed: string
    weekdayThu: string
    weekdayFri: string
    weekdaySat: string
    weekdaySun: string
    monthJan: string
    monthFeb: string
    monthMar: string
    monthApr: string
    monthMay: string
    monthJun: string
    monthJul: string
    monthAug: string
    monthSep: string
    monthOct: string
    monthNov: string
    monthDec: string
    error: string
    loading: string
    retry: string
    noMatches: string
  }
}
