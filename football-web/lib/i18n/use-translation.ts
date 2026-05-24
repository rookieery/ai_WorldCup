import { useI18n } from "./context"

/**
 * Provides the `t()` function for looking up i18n keys.
 * Must be used within an I18nProvider.
 *
 * @example
 * const { t } = useTranslation()
 * <h1>{t("header.title")}</h1>
 */
export function useTranslation() {
  const { t, locale, setLocale } = useI18n()
  return { t, locale, setLocale }
}
