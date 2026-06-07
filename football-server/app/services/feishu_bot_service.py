"""Feishu interactive bot service.

Receives inbound ``im.message.receive_v1`` events, parses the user's
natural-language intent, and dispatches to the appropriate handler:

- ``today_matches``  → query ``MatchService`` for today's schedule
- ``match_analysis`` → AI-powered head-to-head analysis
- ``champion_predict`` → Monte Carlo championship prediction
- ``match_query``    → look up a specific team's matches
- ``general_chat``   → fallback to AI general conversation

AI responses are collected in full (not streamed) before being sent as
a single Feishu interactive card — this avoids the complexity of partial
message edits in a chat context.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas.ai_schema import ChampionshipAnalysisRequest
from app.schemas.feishu_schema import FeishuIntent, FeishuIntentResult, FeishuWebhookEvent
from app.schemas.match_schema import MatchQueryParams
from app.services.ai_service import AIService
from app.services.feishu_card_builder import (
    build_ai_analysis_card,
    build_error_card,
    build_today_matches_card,
)
from app.services.feishu_client import FeishuClient
from app.services.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

# ── Intent keywords ─────────────────────────────────────────────────────────

_INTENT_KEYWORDS: Dict[FeishuIntent, Dict[str, List[str]]] = {
    FeishuIntent.TODAY_MATCHES: {
        "zh": ["今天", "今日", "赛程", "比赛日"],
        "en": ["today", "schedule", "matches today", "today's matches"],
    },
    FeishuIntent.CHAMPION_PREDICT: {
        "zh": ["冠军", "预测冠军", "谁会赢", "夺冠", "夺冠预测"],
        "en": ["champion", "predict winner", "who will win", "title prediction"],
    },
}

# Pattern: "分析XvsY" or "analyze X vs Y" (team names separated by vs/对/对战/against)
_ANALYSIS_PATTERN = re.compile(
    r"(?:分析|预测|分析一下|评估|analyze|analysis|predict)\s+"
    r"(.+?)\s*(?:vs\.?|对战|对|against|VS)\s*(.+)",
    re.IGNORECASE,
)

# Pattern: "定制版分析XvsY" — flexible spacing for custom round-strategy analysis
# Matches "定制版" prefix with optional analysis keyword, relaxed whitespace
_CUSTOM_ANALYSIS_PATTERN = re.compile(
    r"定制版\s*"
    r"(?:分析|预测|分析一下|评估)?\s*"
    r"(.+?)\s*(?:vs\.?|对战|对|against|VS)\s*(.+)",
    re.IGNORECASE,
)


class FeishuBotService:
    """Process inbound Feishu bot commands and generate responses."""

    def __init__(
        self,
        feishu_client: FeishuClient,
        ai_service: AIService,
        match_service: Any = None,
    ) -> None:
        self._client = feishu_client
        self._ai_service = ai_service
        self._match_service = match_service

    # ── Public entry point ──────────────────────────────────────────────

    async def handle_message(self, event: FeishuWebhookEvent) -> None:
        """Parse message, determine intent, respond with a card."""
        if event.event is None:
            return

        chat_id = event.event.message.chat_id
        message_id = event.event.message.message_id
        text = self._extract_text(event.event.message.content)
        if not text.strip():
            return

        lang = self._detect_language(text)
        intent_result = self._parse_intent(text)

        logger.info(
            "Feishu bot: intent=%s text=%r chat=%s",
            intent_result.intent.value,
            text[:80],
            chat_id,
        )

        try:
            if intent_result.intent == FeishuIntent.TODAY_MATCHES:
                await self._handle_today_matches(chat_id, lang)
            elif intent_result.intent == FeishuIntent.MATCH_ANALYSIS:
                await self._handle_match_analysis(
                    intent_result.team1 or "",
                    intent_result.team2 or "",
                    chat_id,
                    message_id,
                    lang,
                    custom_strategy=intent_result.custom_strategy,
                )
            elif intent_result.intent == FeishuIntent.CHAMPION_PREDICT:
                await self._handle_champion_predict(chat_id, message_id, lang)
            elif intent_result.intent == FeishuIntent.MATCH_QUERY:
                await self._handle_match_query(
                    intent_result.team_name or "",
                    chat_id,
                    lang,
                )
            else:
                await self._handle_general_chat(text, chat_id, message_id, lang)
        except Exception:
            logger.warning("Feishu bot handler failed", exc_info=True)
            card = build_error_card(
                "AI 服务暂时不可用，请稍后重试" if lang == "zh-CN"
                else "AI service temporarily unavailable. Please try again later.",
                lang=lang,
            )
            await self._safe_reply(message_id, card)

    # ── Intent parsing ──────────────────────────────────────────────────

    def _parse_intent(self, text: str) -> FeishuIntentResult:
        """Parse natural language text into a structured intent."""
        lower = text.lower().strip()

        # Check for custom "定制版" analysis pattern first (highest specificity)
        custom_match = _CUSTOM_ANALYSIS_PATTERN.search(text)
        if custom_match:
            return FeishuIntentResult(
                intent=FeishuIntent.MATCH_ANALYSIS,
                team1=custom_match.group(1).strip(),
                team2=custom_match.group(2).strip(),
                raw_text=text,
                custom_strategy=True,
            )

        # Check standard match analysis pattern
        match = _ANALYSIS_PATTERN.search(text)
        if match:
            return FeishuIntentResult(
                intent=FeishuIntent.MATCH_ANALYSIS,
                team1=match.group(1).strip(),
                team2=match.group(2).strip(),
                raw_text=text,
            )

        # Check keyword-based intents
        for intent, keywords in _INTENT_KEYWORDS.items():
            for kw_list in keywords.values():
                if any(kw in lower for kw in kw_list):
                    return FeishuIntentResult(intent=intent, raw_text=text)

        # Default to general chat
        return FeishuIntentResult(intent=FeishuIntent.GENERAL_CHAT, raw_text=text)

    @staticmethod
    def _detect_language(text: str) -> str:
        """Simple heuristic: CJK characters → zh-CN, else en-US."""
        cjk_count = sum(
            1 for ch in text
            if "CJK" in unicodedata.name(ch, "")
        )
        return "zh-CN" if cjk_count > 0 else "en-US"

    @staticmethod
    def _extract_text(content: str) -> str:
        """Extract plain text from Feishu message content JSON.

        The content may be ``{"text":"@_user_1 分析..."} `` — strip the
        @-mention prefix and return the remainder.
        """
        try:
            import json
            data = json.loads(content) if isinstance(content, str) else content
            text = data.get("text", "")
        except Exception:
            text = content

        # Strip @-mention prefix like "@_user_1 "
        text = re.sub(r"@_user_\d+\s*", "", text)
        return text.strip()

    # ── Handlers ────────────────────────────────────────────────────────

    async def _handle_today_matches(self, chat_id: str, lang: str) -> None:
        """Query today's matches and send a card."""
        if self._match_service is None:
            await self._send_no_service_reply(chat_id, lang=lang)
            return

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        params = MatchQueryParams(date=today_str)
        matches, _ = await self._match_service.get_matches(params=params, lang="zh" if lang == "zh-CN" else "en")
        card = build_today_matches_card(matches, lang=lang)
        await self._client.send_card_message(chat_id, card)

    async def _handle_match_analysis(
        self,
        team1: str,
        team2: str,
        chat_id: str,
        message_id: str,
        lang: str,
        *,
        custom_strategy: bool = False,
    ) -> None:
        """Build analysis prompt with full skill reasoning chain, stream AI, reply with card.

        Queries the database for real match context (group, round, rankings)
        before building the prompt, so the AI uses factual data instead of
        hallucinating.
        """
        # Enrich with real match data from the database
        match_context = None
        if self._match_service is not None:
            try:
                match_context = await self._match_service.find_match_context(
                    team1, team2,
                    lang="zh" if lang == "zh-CN" else "en",
                )
            except Exception:
                logger.warning("Failed to lookup match context", exc_info=True)

        if custom_strategy:
            messages = PromptBuilder.build_custom_match_analysis_prompt(
                match_id="feishu_auto",
                team1=team1,
                team2=team2,
                lang=lang,
                match_context=match_context,
            )
        else:
            messages = PromptBuilder.build_match_analysis_prompt(
                match_id="feishu_auto",
                team1=team1,
                team2=team2,
                lang=lang,
            )
        answer = await self._collect_ai_answer(messages, lang)
        query = f"{team1} vs {team2}"
        card = build_ai_analysis_card(answer, query=query, lang=lang)
        await self._safe_reply(message_id, card)

    async def _handle_champion_predict(
        self,
        chat_id: str,
        message_id: str,
        lang: str,
    ) -> None:
        """Build championship prompt, stream AI, reply with card."""
        request = ChampionshipAnalysisRequest(
            simulation_count=1000,
            lang=lang,
        )
        messages = PromptBuilder.build_championship_prompt(request)
        answer = await self._collect_ai_answer(messages, lang)
        card = build_ai_analysis_card(answer, query="", lang=lang)
        await self._safe_reply(message_id, card)

    async def _handle_match_query(
        self,
        team_name: str,
        chat_id: str,
        lang: str,
    ) -> None:
        """Query matches for a specific team."""
        if self._match_service is None:
            await self._send_no_service_reply(chat_id, lang=lang)
            return

        params = MatchQueryParams(team=team_name[:3].upper())
        matches, _ = await self._match_service.get_matches(params=params, lang="zh" if lang == "zh-CN" else "en")
        card = build_today_matches_card(matches, lang=lang)
        await self._client.send_card_message(chat_id, card)

    async def _handle_general_chat(
        self,
        text: str,
        chat_id: str,
        message_id: str,
        lang: str,
    ) -> None:
        """Pass to AI as a general conversation."""
        messages = PromptBuilder.build_system_prompt(lang=lang)
        messages.append({"role": "user", "content": text})
        answer = await self._collect_ai_answer(messages, lang)
        card = build_ai_analysis_card(answer, query=text[:100], lang=lang)
        await self._safe_reply(message_id, card)

    # ── AI collection helper ────────────────────────────────────────────

    async def _collect_ai_answer(
        self,
        messages: List[Dict[str, str]],
        lang: str,
    ) -> str:
        """Stream AI response and collect the full answer text."""
        buffer: list[str] = []
        try:
            async for sse_event in self._ai_service.stream_chat(
                messages, lang=lang
            ):
                if sse_event.type == "answer" and sse_event.content:
                    buffer.append(sse_event.content)
                elif sse_event.type == "error":
                    logger.warning("AI stream error: %s", sse_event.content)
                    break
        except Exception:
            logger.warning("AI stream failed", exc_info=True)

        return "".join(buffer) if buffer else (
            "AI 分析暂时不可用" if lang == "zh-CN" else "AI analysis temporarily unavailable"
        )

    # ── Helpers ─────────────────────────────────────────────────────────

    async def _safe_reply(self, message_id: str, card: Dict[str, Any]) -> None:
        """Reply with a card, catching and logging any send failures."""
        try:
            await self._client.reply_message(message_id, card)
        except Exception:
            logger.warning("Feishu reply failed (msg=%s)", message_id, exc_info=True)

    async def _send_no_service_reply(self, chat_id: str, lang: str = "zh-CN") -> None:
        """Send an error card when MatchService is not available."""
        message = (
            "比赛数据服务暂时不可用，请稍后重试"
            if lang == "zh-CN"
            else "Match data service temporarily unavailable. Please try again later."
        )
        card = build_error_card(message, lang=lang)
        await self._client.send_card_message(chat_id, card)
