# tests/test_connector_tools.py
"""Tests for connector tools — wraps marketing-skills/scripts/connectors/*.py."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.connectors.youtube_tools import youtube_channel_stats, youtube_videos
from tools.connectors.bluesky_tools import bluesky_profile
from tools.connectors.tavily_tools import tavily_search, tavily_extract
from tools.connectors.firecrawl_tools import firecrawl_search
from tools.connectors.gdelt_tools import gdelt_news_mentions
from tools.connectors.pageviews_tools import wikipedia_pageviews
from tools.connectors.hn_tools import hn_search
from tools.connectors.rss_tools import rss_monitor_feed
from tools.connectors.doh_tools import dns_auth_records
from tools.connectors.wayback_tools import wayback_history
from tools.connectors.appstore_tools import appstore_lookup
from tools.connectors.kg_tools import wikidata_reconcile
from tools.connectors.ledger_tools import ledger_record, ledger_diff
from tools.connectors.experiment_tools import experiment_proportion
from tools.connectors.psi_tools import pagespeed_insights
from tools.connectors.fediverse_tools import mastodon_trends
from tools.connectors.discourse_tools import discourse_latest


def _mock_subprocess(stdout: str = "", returncode: int = 0, stderr: str = ""):
    m = MagicMock()
    m.stdout = stdout
    m.stderr = stderr
    m.returncode = returncode
    return m


class TestYoutubeTools:
    def test_channel_stats_returns_dict(self):
        with patch("tools.connectors.youtube_tools.subprocess.run",
                   return_value=_mock_subprocess('{"subscriber_count": 47000, "video_count": 120}')):
            result = youtube_channel_stats("@testhandle")
        assert isinstance(result, dict)
        assert result["subscriber_count"] == 47000

    def test_channel_stats_returns_error_on_timeout(self):
        import subprocess
        with patch("tools.connectors.youtube_tools.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(cmd="python", timeout=30)):
            result = youtube_channel_stats("@testhandle")
        assert "error" in result

    def test_videos_returns_list(self):
        with patch("tools.connectors.youtube_tools.subprocess.run",
                   return_value=_mock_subprocess('[{"title": "v1", "views": 1000}]')):
            result = youtube_videos("@testhandle", limit=5)
        assert isinstance(result, list)
        assert len(result) == 1


class TestBlueskyTools:
    def test_profile_returns_dict(self):
        with patch("tools.connectors.bluesky_tools.subprocess.run",
                   return_value=_mock_subprocess('{"handle": "test.bsky.social", "followers": 1000}')):
            result = bluesky_profile("test.bsky.social")
        assert result["handle"] == "test.bsky.social"


class TestTavilyTools:
    def test_search_returns_dict(self):
        with patch("tools.connectors.tavily_tools.subprocess.run",
                   return_value=_mock_subprocess('{"results": [{"title": "x"}], "answer": "yes"}')):
            result = tavily_search("test query", max_results=5)
        assert "results" in result

    def test_extract_returns_dict(self):
        with patch("tools.connectors.tavily_tools.subprocess.run",
                   return_value=_mock_subprocess('{"content": "page text"}')):
            result = tavily_extract("https://example.com")
        assert "content" in result


class TestFirecrawlTools:
    def test_search_returns_list(self):
        with patch("tools.connectors.firecrawl_tools.subprocess.run",
                   return_value=_mock_subprocess('[{"url": "https://x.com", "content": "..."}]')):
            result = firecrawl_search("test", limit=10)
        assert isinstance(result, list)


class TestGdeltTools:
    def test_news_mentions_returns_dict(self):
        with patch("tools.connectors.gdelt_tools.subprocess.run",
                   return_value=_mock_subprocess('{"articles": [{"url": "x"}]}')):
            result = gdelt_news_mentions("test brand", days=30)
        assert "articles" in result


class TestPageviewsTools:
    def test_pageviews_returns_dict(self):
        with patch("tools.connectors.pageviews_tools.subprocess.run",
                   return_value=_mock_subprocess('{"monthly_views": [100, 200, 300]}')):
            result = wikipedia_pageviews("Test Article", months=12)
        assert "monthly_views" in result


class TestHnTools:
    def test_search_returns_dict(self):
        with patch("tools.connectors.hn_tools.subprocess.run",
                   return_value=_mock_subprocess('{"hits": [{"title": "x", "points": 50}]}')):
            result = hn_search("test brand")
        assert "hits" in result


class TestRssTools:
    def test_monitor_returns_dict(self):
        with patch("tools.connectors.rss_tools.subprocess.run",
                   return_value=_mock_subprocess('{"entries": [{"title": "x", "link": "y"}]}')):
            result = rss_monitor_feed("https://example.com/feed.xml")
        assert "entries" in result


class TestDohTools:
    def test_auth_records_returns_dict(self):
        with patch("tools.connectors.doh_tools.subprocess.run",
                   return_value=_mock_subprocess('{"spf": "v=spf1 ...", "dmarc": "v=DMARC1; ..."}')):
            result = dns_auth_records("example.com")
        assert "spf" in result


class TestWaybackTools:
    def test_history_returns_list(self):
        with patch("tools.connectors.wayback_tools.subprocess.run",
                   return_value=_mock_subprocess('[{"timestamp": "20240101", "url": "x"}]')):
            result = wayback_history("https://example.com")
        assert isinstance(result, list)


class TestAppstoreTools:
    def test_lookup_returns_dict(self):
        with patch("tools.connectors.appstore_tools.subprocess.run",
                   return_value=_mock_subprocess('{"trackName": "TestApp", "userRatingCount": 1000}')):
            result = appstore_lookup("123456789")
        assert "trackName" in result


class TestKgTools:
    def test_reconcile_returns_dict(self):
        with patch("tools.connectors.kg_tools.subprocess.run",
                   return_value=_mock_subprocess('{"qid": "Q123", "label": "Test"}')):
            result = wikidata_reconcile("Test Entity")
        assert "qid" in result


class TestLedgerTools:
    def test_record_returns_dict(self):
        with patch("tools.connectors.ledger_tools.subprocess.run",
                   return_value=_mock_subprocess('{"status": "recorded"}')):
            result = ledger_record("test-target", "test-source", '{"metric": 42}')
        assert result["status"] == "recorded"

    def test_diff_returns_dict(self):
        with patch("tools.connectors.ledger_tools.subprocess.run",
                   return_value=_mock_subprocess('{"delta": 10.5}')):
            result = ledger_diff("test-target", "test-source")
        assert "delta" in result


class TestExperimentTools:
    def test_proportion_returns_dict(self):
        with patch("tools.connectors.experiment_tools.subprocess.run",
                   return_value=_mock_subprocess('{"z_stat": 1.96, "p_value": 0.05}')):
            result = experiment_proportion(10, 100, 15, 100)
        assert "z_stat" in result


class TestPsiTools:
    def test_pagespeed_returns_dict(self):
        with patch("tools.connectors.psi_tools.subprocess.run",
                   return_value=_mock_subprocess('{"lighthouse_score": 85, "fcp": 1200}')):
            result = pagespeed_insights("https://example.com")
        assert "lighthouse_score" in result


class TestFediverseTools:
    def test_mastodon_trends_returns_dict(self):
        with patch("tools.connectors.fediverse_tools.subprocess.run",
                   return_value=_mock_subprocess('{"tags": [{"name": "test", "url": "x"}]}')):
            result = mastodon_trends("mastodon.social")
        assert "tags" in result


class TestDiscourseTools:
    def test_latest_returns_dict(self):
        with patch("tools.connectors.discourse_tools.subprocess.run",
                   return_value=_mock_subprocess('{"topics": [{"id": 1, "title": "x"}]}')):
            result = discourse_latest("https://forum.example.com")
        assert "topics" in result
