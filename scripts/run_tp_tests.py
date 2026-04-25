from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class TestCaseSpec:
    case_id: str
    description: str


TP_TEST_CASES: dict[str, list[TestCaseSpec]] = {
    "TP-E4-01": [
        TestCaseSpec(
            case_id="tests.test_document_parser.DocumentParserTests.test_parser_extracts_section_table_code_and_figure_blocks",
            description="文档解析应产出 section/table/code/figure 结构证据。",
        ),
        TestCaseSpec(
            case_id="tests.test_document_parser.DocumentParserTests.test_text_adapter_emits_structured_document_evidence",
            description="TextAdapter 需输出结构化文档 evidence。",
        ),
        TestCaseSpec(
            case_id="tests.test_document_parser_fixtures.DocumentParserFixtureTests.test_docx_fixture_preserves_toc_table_code_and_figure",
            description="docx 实际样本需保留 TOC/table/code/figure。",
        ),
    ],
    "TP-E4-02": [
        TestCaseSpec(
            case_id="tests.test_audio_parser.AudioSemanticParserTests.test_parser_distinguishes_question_decision_action_and_context",
            description="音频语义分类需区分 question/decision/action_item/context。",
        ),
        TestCaseSpec(
            case_id="tests.test_audio_parser.AudioSemanticParserTests.test_audio_adapter_emits_semantic_tags_and_counts",
            description="AudioAdapter 需附带 utterance act/speaker role 计数。",
        ),
    ],
    "TP-E4-03": [
        TestCaseSpec(
            case_id="tests.test_image_parser.ImageParserTests.test_parser_groups_ocr_into_regions_with_layout_roles",
            description="图片解析需输出 region 分组与 layout role。",
        ),
        TestCaseSpec(
            case_id="tests.test_image_parser.ImageParserTests.test_parser_emits_layout_summary_block",
            description="图片 scene summary 需生成 layout 证据块。",
        ),
    ],
    "TP-E4-04": [
        TestCaseSpec(
            case_id="tests.test_video_parser.VideoParserTests.test_video_parser_emits_scene_cluster_frame_event_and_subtitle_alignment",
            description="视频解析需输出 scene cluster + frame event + subtitle-frame alignment。",
        ),
        TestCaseSpec(
            case_id="tests.test_media_provider.MediaProcessorTests.test_parse_showinfo_scene_scores_extracts_numeric_scores",
            description="ffmpeg showinfo 中 scene score 应可解析。",
        ),
        TestCaseSpec(
            case_id="tests.test_mvp.PipelineTests.test_video_distillation_merges_audio_and_keyframe_evidence",
            description="端到端视频蒸馏需包含 speech/ocr/scene/event 与对齐元数据。",
        ),
        TestCaseSpec(
            case_id="tests.test_v2_models.V2ModelTests.test_evidence_builder_creates_video_frame_lineage",
            description="video frame lineage 需关联 ocr/scene/event/subtitle 子证据。",
        ),
    ],
    "TP-E4-05": [
        TestCaseSpec(
            case_id="tests.test_timeseries_parser.TimeSeriesParserTests.test_parser_extracts_baseline_change_points_and_drift",
            description="时序解析需抽取 baseline/change point/drift 语义。",
        ),
        TestCaseSpec(
            case_id="tests.test_mvp.PipelineTests.test_tabular_distillation_emits_baseline_change_point_and_drift_evidence",
            description="端到端表格蒸馏需包含 baseline/drift/change point/anomaly interval 证据。",
        ),
        TestCaseSpec(
            case_id="tests.test_v2_models.V2ModelTests.test_evidence_builder_links_timeseries_event_to_metric",
            description="timeseries event 需维持与 metric 节点的 lineage 链接。",
        ),
    ],
    "TP-E5-02": [
        TestCaseSpec(
            case_id="tests.test_heuristic_atom_extractor.HeuristicAtomExtractorTests.test_extractor_is_atom_extractor_protocol_compatible",
            description="HeuristicAtomExtractor 需符合 AtomExtractor 协议。",
        ),
        TestCaseSpec(
            case_id="tests.test_heuristic_atom_extractor.HeuristicAtomExtractorTests.test_extractor_emits_procedure_rule_verification_and_anti_pattern",
            description="需基于 EvidenceNode 稳定产出 procedure/rule/verification/anti-pattern。",
        ),
        TestCaseSpec(
            case_id="tests.test_heuristic_atom_extractor.HeuristicAtomExtractorTests.test_extractor_fallbacks_to_claim_when_no_pattern_matches",
            description="无规则命中时需回退 claim atom，确保抽取链不空。",
        ),
    ],
    "TP-E5-03": [
        TestCaseSpec(
            case_id="tests.test_modality_atom_strategy.ModalityAtomStrategyTests.test_audio_prioritizes_question_and_event_atoms",
            description="音频 evidence 优先产出 question/event atom。",
        ),
        TestCaseSpec(
            case_id="tests.test_modality_atom_strategy.ModalityAtomStrategyTests.test_video_prioritizes_event_atom",
            description="视频 evidence 优先产出 event atom。",
        ),
        TestCaseSpec(
            case_id="tests.test_modality_atom_strategy.ModalityAtomStrategyTests.test_tabular_prioritizes_metric_guardrail_atom",
            description="时序 evidence 优先产出 metric_guardrail atom。",
        ),
    ],
    "TP-E5-04": [
        TestCaseSpec(
            case_id="tests.test_llm_atom_extractor.LLMAtomExtractorTests.test_fallback_to_base_atoms_when_llm_fails",
            description="LLM 失败时必须回退到基础 heuristic atom 输出。",
        ),
        TestCaseSpec(
            case_id="tests.test_llm_atom_extractor.LLMAtomExtractorTests.test_merge_llm_atoms_without_overwriting_base_truth",
            description="LLM 成功时只做增量增强，不覆盖基础真相链。",
        ),
        TestCaseSpec(
            case_id="tests.test_openai_atom_enhancer.OpenAIAtomEnhancerTests.test_sanitize_evidence_refs_filters_unknown_and_dedupes",
            description="OpenAI atom 增强需过滤非法 evidence_refs 并去重。",
        ),
    ],
    "TP-E6-01": [
        TestCaseSpec(
            case_id="tests.test_skill_graph_models.SkillGraphModelTests.test_skill_graph_validate_and_serialize_with_all_min_nodes_and_edges",
            description="SkillGraph node/edge 模型需支持完整结构与序列化。",
        ),
        TestCaseSpec(
            case_id="tests.test_skill_graph_models.SkillGraphModelTests.test_skill_graph_validate_rejects_missing_edge_target",
            description="edge 引用缺失 node 时应被校验拦截。",
        ),
        TestCaseSpec(
            case_id="tests.test_skill_graph_models.SkillGraphModelTests.test_skill_graph_validate_rejects_duplicate_node_ids",
            description="node_id 冲突时应被校验拦截。",
        ),
    ],
    "TP-E6-02": [
        TestCaseSpec(
            case_id="tests.test_skill_graph_builder.SkillGraphBuilderTests.test_builder_constructs_graph_from_minimal_atoms",
            description="最小 atom 集应可构建 SkillGraph，且 step 可追到 atom/evidence。",
        ),
        TestCaseSpec(
            case_id="tests.test_skill_graph_builder.SkillGraphBuilderTests.test_builder_fallback_step_traces_to_atoms_when_no_procedure",
            description="无 procedure 时应从其他 atom 回退生成可追溯 step。",
        ),
        TestCaseSpec(
            case_id="tests.test_skill_graph_builder.SkillGraphBuilderTests.test_builder_fallback_step_traces_to_evidence_when_no_atoms",
            description="无 atom 时应从 evidence 回退生成可追溯 step。",
        ),
    ],
    "TP-E6-03": [
        TestCaseSpec(
            case_id="tests.test_publication_builder.PublicationBuilderTests.test_builder_default_emits_markdown_and_json",
            description="PublicationBuilder 默认应输出 SKILL.md 与 skill.json。",
        ),
        TestCaseSpec(
            case_id="tests.test_publication_builder.PublicationBuilderTests.test_builder_emits_checklist_and_decision_tree",
            description="PublicationBuilder 应支持输出 checklist.json 与 decision_tree.json。",
        ),
        TestCaseSpec(
            case_id="tests.test_publication_builder.PublicationBuilderTests.test_builder_emits_default_decision_tree_when_graph_has_no_decisions",
            description="无决策节点时 decision_tree 需回退到 default branch。",
        ),
        TestCaseSpec(
            case_id="tests.test_publication_orchestrator_split.PublicationOrchestratorTests.test_orchestrator_chooses_goal_specific_publication_types",
            description="编排层应按 goal_type 选择 checklist/decision_tree publication。",
        ),
        TestCaseSpec(
            case_id="tests.test_v2_schema_and_corpus.CorpusServiceTests.test_distill_corpus_keeps_single_asset_paths_compatible",
            description="service/repository 应落盘 publication 与 manifest。",
        ),
    ],
    "TP-E6-04": [
        TestCaseSpec(
            case_id="tests.test_render_compat.RenderCompatibilityTests.test_render_skill_markdown_compat_prefers_publication_payload",
            description="compat renderer 应优先返回 publication 中的 markdown。",
        ),
        TestCaseSpec(
            case_id="tests.test_render_compat.RenderCompatibilityTests.test_render_skill_markdown_compat_falls_back_to_skill_document",
            description="缺失 markdown publication 时应回退到 SkillDocument 渲染。",
        ),
        TestCaseSpec(
            case_id="tests.test_v2_schema_and_corpus.CorpusServiceTests.test_distill_corpus_keeps_single_asset_paths_compatible",
            description="外部接口应继续可获取 skill_markdown。",
        ),
    ],
    "TP-E7-01": [
        TestCaseSpec(
            case_id="tests.test_quality_scoring.QualityScorerTests.test_scorer_outputs_all_required_metrics",
            description="质量评分器应输出 traceability/actionability/coverage/consistency/noise/novelty 六分项。",
        ),
        TestCaseSpec(
            case_id="tests.test_quality_scoring.QualityScorerTests.test_traceability_drops_when_step_lacks_evidence_refs",
            description="traceability 分应对缺失证据追溯的 step 降分。",
        ),
        TestCaseSpec(
            case_id="tests.test_v2_schema_and_corpus.CorpusServiceTests.test_distill_corpus_keeps_single_asset_paths_compatible",
            description="每次蒸馏都应落 quality_score 并回写到 adapter_metadata。",
        ),
    ],
    "TP-E7-02": [
        TestCaseSpec(
            case_id="tests.test_review_policy.ReviewPolicyTests.test_auto_publish_when_all_scores_high",
            description="ReviewPolicy 应在高分时输出 auto_publish。",
        ),
        TestCaseSpec(
            case_id="tests.test_review_policy.ReviewPolicyTests.test_reject_when_scores_are_critical",
            description="ReviewPolicy 应在关键低分时输出 reject 与理由码。",
        ),
        TestCaseSpec(
            case_id="tests.test_review_policy.ReviewPolicyTests.test_review_required_when_between_auto_and_reject",
            description="ReviewPolicy 应在中间区间输出 review_required 与理由码。",
        ),
        TestCaseSpec(
            case_id="tests.test_v2_schema_and_corpus.CorpusServiceTests.test_distill_corpus_keeps_single_asset_paths_compatible",
            description="每次蒸馏都应输出 review_policy 决策与原因码。",
        ),
    ],
    "TP-E7-03": [
        TestCaseSpec(
            case_id="tests.test_v2_models.V2ModelTests.test_review_task_from_policy_keeps_reason_codes_and_revision_suggestions",
            description="ReviewTask 必须结构化保存 reason_codes 与 revision_suggestions。",
        ),
        TestCaseSpec(
            case_id="tests.test_v2_models.V2ModelTests.test_review_task_auto_publish_is_marked_published",
            description="auto_publish 决策应生成已发布状态的结构化 ReviewTask。",
        ),
        TestCaseSpec(
            case_id="tests.test_v2_models.V2ModelTests.test_review_task_reject_is_marked_rejected",
            description="reject 决策应生成 rejected 状态并保留修正建议。",
        ),
        TestCaseSpec(
            case_id="tests.test_v2_schema_and_corpus.CorpusServiceTests.test_distill_corpus_keeps_single_asset_paths_compatible",
            description="repository 应将结构化 review_task 落盘并与 review_policy 保持一致。",
        ),
    ],
    "TP-E7-04": [
        TestCaseSpec(
            case_id="tests.test_review_feedback.ReviewFeedbackEngineTests.test_feedback_maps_traceability_and_actionability_to_structured_actions",
            description="review feedback 需能回流出 evidence/step 修订动作。",
        ),
        TestCaseSpec(
            case_id="tests.test_review_feedback.ReviewFeedbackEngineTests.test_feedback_maps_reject_to_noise_and_consistency_remediation",
            description="reject 场景需输出 noise/consistency 的结构化修订动作。",
        ),
        TestCaseSpec(
            case_id="tests.test_review_feedback.ReviewFeedbackEngineTests.test_feedback_auto_publish_generates_publish_ready_signal",
            description="auto_publish 场景需保留可复用的 publish-ready 回流信号。",
        ),
        TestCaseSpec(
            case_id="tests.test_v2_schema_and_corpus.CorpusServiceTests.test_distill_corpus_keeps_single_asset_paths_compatible",
            description="service/repository 应落盘 review_feedback 并可用于后续修订链路。",
        ),
    ],
    "TP-E8-02": [
        TestCaseSpec(
            case_id="tests.test_postgres_repository.PostgresRepositoryTests.test_save_bundle_writes_skill_review_and_publication_rows",
            description="PostgresRepository 需写入 skills/skill_versions/review_tasks/publications 核心表。",
        ),
        TestCaseSpec(
            case_id="tests.test_postgres_repository.PostgresRepositoryTests.test_save_bundle_rolls_back_on_database_failure",
            description="写库失败时必须触发 rollback，避免脏事务。",
        ),
        TestCaseSpec(
            case_id="tests.test_postgres_repository_integration.PostgresRepositoryIntegrationTests.test_save_bundle_persists_rows_into_postgres",
            description="真实 Postgres 集成脚本：校验技能、review task、publication 均成功落库。",
        ),
    ],
    "TP-E8-03": [
        TestCaseSpec(
            case_id="tests.test_dual_write_repository.DualWriteRepositoryTests.test_dual_write_secondary_failure_does_not_break_primary_file_artifacts",
            description="dual-write 发生 secondary 失败时，不应破坏 file artifact 输出。",
        ),
        TestCaseSpec(
            case_id="tests.test_dual_write_repository.DualWriteRepositoryTests.test_dual_write_success_adds_prefixed_secondary_artifacts",
            description="dual-write 成功时应保留 primary keys，并附带 secondary 前缀工件引用。",
        ),
        TestCaseSpec(
            case_id="tests.test_dual_write_repository_integration.DualWriteRepositoryIntegrationTests.test_file_and_postgres_dual_write_persists_both_targets",
            description="真实 Postgres 集成脚本：校验 file + postgres 双写均成功。",
        ),
    ],
    "TP-E9-01": [
        TestCaseSpec(
            case_id="tests.test_similarity_retrieval.SimilarityRetrievalTests.test_inmemory_backend_returns_relevant_skill_first",
            description="相似技能检索应优先返回语义最接近的 skill。",
        ),
        TestCaseSpec(
            case_id="tests.test_similarity_retrieval.SimilarityRetrievalTests.test_domain_and_tag_boost_breaks_lexical_tie",
            description="domain/tag 信号应在词面近似时提供稳定排序基线。",
        ),
        TestCaseSpec(
            case_id="tests.test_similarity_retrieval.SimilarityRetrievalTests.test_retriever_indexes_skill_document_smoke",
            description="统一检索接口应支持从 SkillDocument 建索并执行 smoke 检索。",
        ),
        TestCaseSpec(
            case_id="tests.test_similarity_retrieval.SimilarityRetrievalTests.test_backend_factory_exposes_pgvector_placeholder",
            description="backend factory 应暴露 pgvector placeholder，保持接口前向兼容。",
        ),
    ],
    "TP-E9-02": [
        TestCaseSpec(
            case_id="tests.test_lifecycle_decision_engine.LifecycleDecisionEngineTests.test_engine_returns_new_when_no_similar_candidates",
            description="无相似候选时应输出 lifecycle=new。",
        ),
        TestCaseSpec(
            case_id="tests.test_lifecycle_decision_engine.LifecycleDecisionEngineTests.test_engine_returns_revise_for_single_high_similarity_match",
            description="单高相似候选应输出 lifecycle=revise。",
        ),
        TestCaseSpec(
            case_id="tests.test_lifecycle_decision_engine.LifecycleDecisionEngineTests.test_engine_returns_merge_for_multiple_high_similarity_matches",
            description="多高相似候选应输出 lifecycle=merge。",
        ),
        TestCaseSpec(
            case_id="tests.test_lifecycle_decision_engine.LifecycleDecisionEngineTests.test_engine_returns_supersede_for_near_identical_high_quality_match",
            description="近同构高质量候选应输出 lifecycle=supersede。",
        ),
        TestCaseSpec(
            case_id="tests.test_lifecycle_decision_engine.LifecycleDecisionEngineTests.test_engine_returns_reject_for_noisy_or_conflicting_signal",
            description="高噪声或证据冲突时应输出 lifecycle=reject。",
        ),
    ],
    "TP-E9-03": [
        TestCaseSpec(
            case_id="tests.test_v2_models.V2ModelTests.test_skill_lineage_link_can_be_derived_from_lifecycle_decision",
            description="supersede lifecycle decision 应可转换为结构化 lineage link。",
        ),
        TestCaseSpec(
            case_id="tests.test_postgres_repository.PostgresRepositoryTests.test_save_bundle_writes_lineage_links_for_supersede_decision",
            description="PostgresRepository 应将 supersede lineage_links 持久化并返回 artifact 引用。",
        ),
        TestCaseSpec(
            case_id="tests.test_postgres_repository_integration.PostgresRepositoryIntegrationTests.test_save_bundle_persists_lineage_links_into_postgres",
            description="真实 Postgres 集成场景应能查询到写入的 lineage_links 记录。",
        ),
    ],
    "TP-E10-01": [
        TestCaseSpec(
            case_id="tests.test_cli.CliCorpusCommandTests.test_distill_corpus_accepts_multiple_asset_args",
            description="CLI distill-corpus 应支持多次 --asset 的 corpus 蒸馏输入。",
        ),
        TestCaseSpec(
            case_id="tests.test_cli.CliCorpusCommandTests.test_distill_corpus_supports_publication_selection_and_review_status_output",
            description="CLI 应支持 --publication 选择输出视图，并展示 review status。",
        ),
        TestCaseSpec(
            case_id="tests.test_cli.CliCorpusCommandTests.test_distill_corpus_accepts_publication_artifact_key_style",
            description="CLI --publication 应兼容 publication_* artifact key 风格输入。",
        ),
    ],
    "TP-E10-02": [
        TestCaseSpec(
            case_id="tests.test_api_app.ApiAppV2OutputContractTests.test_corpus_endpoint_returns_v2_summary_fields_and_keeps_legacy_markdown",
            description="API 应输出 graph metadata、available publications、review status，并保留 skill_markdown。",
        ),
        TestCaseSpec(
            case_id="tests.test_api_app.ApiAppV2OutputContractTests.test_review_status_falls_back_to_skill_review_status_when_review_task_missing",
            description="当 review_task 缺失时，review_status 应回退到 skill.review_status。",
        ),
    ],
    "TP-E10-03": [
        TestCaseSpec(
            case_id="tests.test_worker.WorkerTaskTypeUpgradeTests.test_review_queue_claim_job_is_supported",
            description="worker 应支持 review_queue claim 任务并消费 pending review task。",
        ),
        TestCaseSpec(
            case_id="tests.test_worker.WorkerTaskTypeUpgradeTests.test_rebuild_publication_job_replays_text_request",
            description="worker 应支持 rebuild_publication 并重放 distill request。",
        ),
        TestCaseSpec(
            case_id="tests.test_worker.WorkerTaskTypeUpgradeTests.test_rebuild_publication_can_load_request_payload_from_bundle",
            description="worker rebuild_publication 应支持从 bundle.json 读取 request_payload。",
        ),
        TestCaseSpec(
            case_id="tests.test_worker.WorkerTaskTypeUpgradeTests.test_revise_skill_requires_existing_skill_id",
            description="worker revise_skill 缺失 existing_skill_id 时应失败并落 failed job。",
        ),
        TestCaseSpec(
            case_id="tests.test_worker.WorkerTaskTypeUpgradeTests.test_revise_skill_injects_existing_skill_id_into_corpus_metadata",
            description="worker revise_skill 应将 existing_skill_id 注入 corpus metadata 后重放。",
        ),
    ],
    "TP-E11-01": [
        TestCaseSpec(
            case_id="tests.test_v2_models.V2ModelTests.test_v2_core_models_are_json_serializable",
            description="V2 core models 应保持可序列化，避免 graph/document 契约回归。",
        ),
        TestCaseSpec(
            case_id="tests.test_v2_models.V2ModelTests.test_evidence_unit_to_node_transforms_legacy_fields",
            description="legacy EvidenceUnit -> EvidenceNode 转换应保留关键字段。",
        ),
        TestCaseSpec(
            case_id="tests.test_v2_models.V2ModelTests.test_skill_graph_to_document_builds_skill_document",
            description="SkillGraph -> SkillDocument 转换应可稳定回归。",
        ),
        TestCaseSpec(
            case_id="tests.test_transformers_regression.TransformersRegressionTests.test_skill_graph_to_document_selects_skill_type_branches",
            description="skill_graph_to_document 应覆盖 decision/diagnostic/analysis 分支。",
        ),
        TestCaseSpec(
            case_id="tests.test_transformers_regression.TransformersRegressionTests.test_skill_graph_to_document_dedupes_evidence_refs_from_all_nodes",
            description="转换器应对 graph/node evidence_refs 进行顺序去重汇总。",
        ),
        TestCaseSpec(
            case_id="tests.test_transformers_regression.TransformersRegressionTests.test_legacy_insight_atom_extractor_uses_payload_legacy_content_when_text_missing",
            description="legacy atom bridge 在 text 为空时应回退 payload.legacy_content。",
        ),
    ],
    "TP-E11-04": [
        TestCaseSpec(
            case_id="tests.test_benchmark_dual_write.BenchmarkDualWriteScriptTests.test_script_smoke_runs_file_only_and_writes_report",
            description="benchmark harness 烟测：生成 file-only 时延报告。",
        ),
        TestCaseSpec(
            case_id="tests.test_benchmark_dual_write.BenchmarkDualWriteScriptTests.test_script_rejects_non_positive_iterations",
            description="benchmark harness 参数保护：iterations<=0 必须报错。",
        ),
    ],
}


def _normalize_tp_id(value: str) -> str:
    return value.strip().upper().replace("_", "-")


def _dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def _collect_case_ids(tp_ids: list[str]) -> list[str]:
    requested = [_normalize_tp_id(item) for item in tp_ids]
    case_ids: list[str] = []
    for tp_id in requested:
        specs = TP_TEST_CASES.get(tp_id)
        if not specs:
            continue
        case_ids.extend(spec.case_id for spec in specs)
    return _dedupe_preserve_order(case_ids)


def _print_registry() -> None:
    for tp_id in sorted(TP_TEST_CASES.keys()):
        print(tp_id)
        for spec in TP_TEST_CASES[tp_id]:
            print("  - %s" % spec.case_id)
            print("    %s" % spec.description)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run unittest cases mapped to Task Package IDs (TP-EX-YY).",
    )
    parser.add_argument("tp_ids", nargs="*", help="Task Package IDs, e.g. TP-E4-04 TP-E4-03")
    parser.add_argument("--all", action="store_true", help="Run all mapped TP test cases.")
    parser.add_argument("--list", action="store_true", help="List all TP IDs and bound test cases.")
    parser.add_argument("--dry-run", action="store_true", help="Print the final command without running it.")
    parser.add_argument(
        "--python",
        default=sys.executable,
        help='Python command used to run unittest. Supports args, e.g. --python "py -3.11".',
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.list:
        _print_registry()
        return 0

    if args.all:
        tp_ids = list(sorted(TP_TEST_CASES.keys()))
    else:
        tp_ids = args.tp_ids

    if not tp_ids:
        print("No TP IDs provided. Use --list to inspect mapped cases.", file=sys.stderr)
        return 2

    normalized_tp_ids = [_normalize_tp_id(item) for item in tp_ids]
    unknown = [item for item in normalized_tp_ids if item not in TP_TEST_CASES]
    if unknown:
        print("Unknown TP IDs: %s" % ", ".join(unknown), file=sys.stderr)
        print("Use --list to view available mappings.", file=sys.stderr)
        return 2

    case_ids = _collect_case_ids(normalized_tp_ids)
    if not case_ids:
        print("No test cases mapped for: %s" % ", ".join(normalized_tp_ids), file=sys.stderr)
        return 2

    print("Selected TP IDs: %s" % ", ".join(normalized_tp_ids))
    print("Case count: %s" % len(case_ids))
    for case_id in case_ids:
        print("  - %s" % case_id)

    python_cmd = shlex.split(args.python, posix=os.name != "nt")
    if not python_cmd:
        print("Empty --python command.", file=sys.stderr)
        return 2
    command = [*python_cmd, "-m", "unittest", *case_ids]
    print("Command: %s" % " ".join(command))
    if args.dry_run:
        return 0

    completed = subprocess.run(command, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
