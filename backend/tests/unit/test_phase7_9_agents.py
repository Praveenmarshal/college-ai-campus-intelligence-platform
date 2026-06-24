"""
tests/unit/test_phase7_9_agents.py
Phase 7 (Smart Router), Phase 8 (Multi-Agent), Phase 9 (Resume Analyzer) — unit tests.
"""

import pytest


class TestQueryRouterKeywordClassification:

    def test_classify_placement_query(self):
        from services.query_router import QueryRouter
        agent, confidence = QueryRouter.classify_keyword("What is the highest placement package this year?")
        assert agent == "placement_agent"
        assert confidence > 0

    def test_classify_library_query(self):
        from services.query_router import QueryRouter
        agent, confidence = QueryRouter.classify_keyword("Is the book Clean Code available in the library?")
        assert agent == "library_agent"

    def test_classify_hostel_query(self):
        from services.query_router import QueryRouter
        agent, confidence = QueryRouter.classify_keyword("How many rooms are vacant in hostel block B?")
        assert agent == "hostel_agent"

    def test_classify_no_match_returns_none(self):
        from services.query_router import QueryRouter
        agent, confidence = QueryRouter.classify_keyword("xyzabc qwerty random gibberish")
        assert agent is None
        assert confidence == 0.0

    def test_classify_academic_query(self):
        from services.query_router import QueryRouter
        agent, confidence = QueryRouter.classify_keyword("What is the average CGPA in semester result?")
        assert agent == "academic_agent"

    def test_classify_prediction_query(self):
        from services.query_router import QueryRouter
        agent, confidence = QueryRouter.classify_keyword("Predict the risk of this student failing")
        assert agent == "prediction_agent"


class TestAgentOrchestrator:

    def test_list_agents_returns_all_nine(self):
        from agents.orchestrator import AgentOrchestrator
        agents = AgentOrchestrator.list_agents()
        assert len(agents) == 11
        names = [a["name"] for a in agents]
        assert "document_agent" in names
        assert "placement_agent" in names
        assert "resume_agent" in names

    def test_dispatch_unknown_agent_returns_error_response(self, app):
        with app.app_context():
            from agents.orchestrator import AgentOrchestrator
            result = AgentOrchestrator.dispatch("nonexistent_agent", "test query")
            assert "error" in result
            assert result["agent"] == "orchestrator"

    def test_get_agent_unknown_raises(self):
        from agents.orchestrator import AgentOrchestrator
        with pytest.raises(ValueError, match="Unknown agent"):
            AgentOrchestrator.get_agent("fake_agent_xyz")


class TestBaseAgentContract:

    def test_response_shape(self):
        from agents.base_agent import BaseAgent

        class DummyAgent(BaseAgent):
            name = "dummy"
            def handle(self, query, context=None):
                return self._response("test answer", sources=[{"x": 1}])

        agent = DummyAgent()
        result = agent.handle("test")
        assert result["answer"] == "test answer"
        assert result["agent"] == "dummy"
        assert result["sources"] == [{"x": 1}]

    def test_error_response_shape(self):
        from agents.base_agent import BaseAgent

        class DummyAgent(BaseAgent):
            name = "dummy"
            def handle(self, query, context=None):
                return self._error_response("something broke")

        agent = DummyAgent()
        result = agent.handle("test")
        assert "error" in result
        assert "something broke" in result["answer"]


class TestResumeAnalyzerFallback:

    def test_fallback_skill_extraction(self):
        from services.resume.resume_analyzer import ResumeAnalyzer
        text = "Experienced in Python, React, and AWS. Strong communication skills."
        skills = ResumeAnalyzer._fallback_skill_extraction(text)
        assert "python" in skills
        assert "react" in skills
        assert "aws" in skills

    def test_fallback_skill_extraction_case_insensitive(self):
        from services.resume.resume_analyzer import ResumeAnalyzer
        text = "PYTHON and JavaScript developer"
        skills = ResumeAnalyzer._fallback_skill_extraction(text)
        assert "python" in skills
        assert "javascript" in skills

    def test_cache_and_retrieve_analysis(self):
        from services.resume.resume_analyzer import ResumeAnalyzer
        analysis = {"ats_score": 75, "extracted_skills": ["python"]}
        ResumeAnalyzer.cache_analysis("test_resume_123", analysis)
        retrieved = ResumeAnalyzer.get_cached_analysis("test_resume_123")
        assert retrieved["ats_score"] == 75

    def test_get_uncached_returns_none(self):
        from services.resume.resume_analyzer import ResumeAnalyzer
        result = ResumeAnalyzer.get_cached_analysis("nonexistent_id_xyz")
        assert result is None


class TestRouterRouteHybridFallback:

    def test_route_hybrid_single_candidate_uses_normal_route(self, app, monkeypatch):
        with app.app_context():
            from services.query_router import QueryRouter
            from agents.orchestrator import AgentOrchestrator

            # Mock dispatch to avoid needing a live LLM/DB
            monkeypatch.setattr(
                AgentOrchestrator, "dispatch",
                lambda agent_name, query, context=None: {
                    "answer": "mocked", "sources": [], "agent": agent_name, "data": None
                }
            )
            result = QueryRouter.route_hybrid("What book is available in the library?")
            assert "answer" in result
