"""
tests/unit/test_phase4_6_analytics.py
Phase 4 (Excel), Phase 5 (CSV), Phase 6 (MongoDB NL Query) — unit tests.
"""

import pytest
import pandas as pd


class TestExcelProcessor:

    def test_detect_sheet_type_attendance(self):
        from services.excel.excel_processor import ExcelProcessor
        df = pd.DataFrame({"student_id": ["S1", "S2"], "date": ["2024-01-01"] * 2, "status": ["present", "absent"], "course": ["CS101"] * 2})
        assert ExcelProcessor.detect_sheet_type(df) == "attendance"

    def test_detect_sheet_type_placements(self):
        from services.excel.excel_processor import ExcelProcessor
        df = pd.DataFrame({"company": ["Google"], "package": [20], "student": ["A"], "placement": ["yes"]})
        assert ExcelProcessor.detect_sheet_type(df) == "placements"

    def test_detect_sheet_type_unknown(self):
        from services.excel.excel_processor import ExcelProcessor
        df = pd.DataFrame({"random_col": [1, 2, 3]})
        assert ExcelProcessor.detect_sheet_type(df) == "unknown"

    def test_summarise_basic_stats(self):
        from services.excel.excel_processor import ExcelProcessor
        df = pd.DataFrame({"score": [80, 90, 70, 60], "name": ["A", "B", "C", "D"]})
        summary = ExcelProcessor.summarise(df)
        assert summary["row_count"] == 4
        assert "score" in summary["numeric_stats"]
        assert summary["numeric_stats"]["score"]["mean"] == 75.0

    def test_analyse_attendance_computes_percentage(self):
        from services.excel.excel_processor import ExcelProcessor
        df = pd.DataFrame({
            "student_id": ["S1", "S1", "S2", "S2"],
            "status": ["present", "absent", "present", "present"],
        })
        result = ExcelProcessor.analyse_attendance(df)
        assert result["overall_attendance_pct"] == 75.0

    def test_analyse_attendance_finds_at_risk(self):
        from services.excel.excel_processor import ExcelProcessor
        df = pd.DataFrame({
            "student_id": ["S1"] * 10,
            "status": ["present"] * 5 + ["absent"] * 5,  # 50% — at risk
        })
        result = ExcelProcessor.analyse_attendance(df)
        assert "S1" in result["at_risk_students"]

    def test_analyse_placements_finds_highest_package(self):
        from services.excel.excel_processor import ExcelProcessor
        df = pd.DataFrame({"company": ["A", "B"], "package": [10, 25]})
        result = ExcelProcessor.analyse_placements(df)
        assert result["highest_package"] == 25.0

    def test_analyse_results_finds_top_performers(self):
        from services.excel.excel_processor import ExcelProcessor
        df = pd.DataFrame({"student": ["A", "B", "C"], "cgpa": [8.5, 9.2, 7.1]})
        result = ExcelProcessor.analyse_results(df)
        assert result["highest_cgpa"] == 9.2

    def test_find_columns_matches_variants(self):
        from services.excel.excel_processor import ExcelProcessor
        df = pd.DataFrame({"Student_ID": [1], "Attendance_Status": ["present"]})
        df.columns = [c.lower() for c in df.columns]
        result = ExcelProcessor._find_columns(df, {"student_id": ["student_id"], "status": ["status"]})
        assert result["student_id"] == "student_id"


class TestCSVProcessor:

    def test_infer_column_types_integer(self):
        from services.csv_engine.csv_processor import CSVProcessor
        df = pd.DataFrame({"age": [20, 21, 22]})
        types = CSVProcessor.infer_column_types(df)
        assert types["age"] == "integer"

    def test_infer_column_types_float(self):
        from services.csv_engine.csv_processor import CSVProcessor
        df = pd.DataFrame({"gpa": [3.5, 3.8, 3.2]})
        types = CSVProcessor.infer_column_types(df)
        assert types["gpa"] == "float"

    def test_infer_column_types_categorical(self):
        from services.csv_engine.csv_processor import CSVProcessor
        df = pd.DataFrame({"dept": ["CS", "CS", "EE", "CS", "EE"] * 5})
        types = CSVProcessor.infer_column_types(df)
        assert types["dept"] == "categorical"

    def test_profile_completeness(self):
        from services.csv_engine.csv_processor import CSVProcessor
        df = pd.DataFrame({"a": [1, 2, None], "b": [1, 2, 3]})
        profile = CSVProcessor.profile(df)
        assert profile["completeness_pct"] < 100

    def test_profile_duplicate_detection(self):
        from services.csv_engine.csv_processor import CSVProcessor
        df = pd.DataFrame({"a": [1, 1, 2], "b": [1, 1, 2]})
        profile = CSVProcessor.profile(df)
        assert profile["duplicate_rows"] == 1


class TestNLQueryEngine:

    def test_execute_query_filter_equals(self):
        from services.excel.nl_query import NLQueryEngine
        df = pd.DataFrame({"dept": ["CS", "EE", "CS"], "score": [80, 70, 90]})
        spec = {"operation": "filter", "filter_column": "dept", "filter_op": "==", "filter_value": "CS"}
        result = NLQueryEngine.execute_query(df, spec)
        assert result["row_count"] == 2

    def test_execute_query_groupby_mean(self):
        from services.excel.nl_query import NLQueryEngine
        df = pd.DataFrame({"dept": ["CS", "CS", "EE"], "score": [80, 90, 70]})
        spec = {"operation": "groupby_agg", "group_by": "dept", "agg_column": "score", "agg_func": "mean"}
        result = NLQueryEngine.execute_query(df, spec)
        assert result["result"]["CS"] == 85.0

    def test_execute_query_top_n(self):
        from services.excel.nl_query import NLQueryEngine
        df = pd.DataFrame({"name": ["A", "B", "C"], "score": [60, 95, 80]})
        spec = {"operation": "top_n", "sort_column": "score", "sort_ascending": False, "limit": 2}
        result = NLQueryEngine.execute_query(df, spec)
        assert result["row_count"] == 2
        assert result["result"][0]["name"] == "B"

    def test_execute_query_value_counts(self):
        from services.excel.nl_query import NLQueryEngine
        df = pd.DataFrame({"dept": ["CS", "CS", "EE", "ME"]})
        spec = {"operation": "value_counts", "column": "dept"}
        result = NLQueryEngine.execute_query(df, spec)
        assert result["result"]["CS"] == 2

    def test_execute_query_filter_numeric_gt(self):
        from services.excel.nl_query import NLQueryEngine
        df = pd.DataFrame({"cgpa": [7.0, 8.5, 9.2, 6.5]})
        spec = {"operation": "filter", "filter_column": "cgpa", "filter_op": ">", "filter_value": "8.0"}
        result = NLQueryEngine.execute_query(df, spec)
        assert result["row_count"] == 2


class TestMongoQueryEngineValidation:

    def test_forbidden_operator_rejected(self):
        from services.mongo_query_service import MongoQueryEngine
        pipeline = [{"$match": {"$where": "this.x > 1"}}]
        is_valid, msg = MongoQueryEngine._validate_pipeline(pipeline)
        assert is_valid is False
        assert "$where" in msg

    def test_safe_pipeline_accepted(self):
        from services.mongo_query_service import MongoQueryEngine
        pipeline = [{"$match": {"department": "CS"}}, {"$limit": 10}]
        is_valid, msg = MongoQueryEngine._validate_pipeline(pipeline)
        assert is_valid is True

    def test_too_many_stages_rejected(self):
        from services.mongo_query_service import MongoQueryEngine
        pipeline = [{"$match": {"x": i}} for i in range(20)]
        is_valid, msg = MongoQueryEngine._validate_pipeline(pipeline)
        assert is_valid is False

    def test_unknown_collection_raises(self, app):
        with app.app_context():
            from services.mongo_query_service import MongoQueryEngine
            with pytest.raises(ValueError, match="not queryable"):
                MongoQueryEngine.parse_query("test", "audit_logs")

    def test_list_collections_returns_allowed_set(self):
        from services.mongo_query_service import MongoQueryEngine
        collections = MongoQueryEngine.list_collections()
        assert "students" in collections
        assert "users" not in collections  # users should never be NL-queryable
        assert "audit_logs" not in collections
