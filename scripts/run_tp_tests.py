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
