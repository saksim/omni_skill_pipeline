# Skill Distillation V2 Implementation Backlog

## 鍒よ瘝

杩欎笉鏄璁虹锛岃€屾槸闈㈠悜鍚庣画 `gpt-5.3-codex` 鐩存帴鏂藉伐鐨勫叏閲忓紑鍙戞媶瑙ｅ彴璐︺€傜洰鏍囨槸鎶?V2 浠庢蹇靛浘绾告媶鍒板彲鎵ц浠诲姟鍖咃紝閬垮厤鍚庣画瀹炵幇闃舵缁х画鍦ㄢ€滃畾涔夐棶棰樷€濅笂鑰楄銆?
## 1. 鏂囨。鐢ㄩ€?
鏈枃浠剁敤浜庡洖绛斾簲浠朵簨锛?
- V2 鍒板簳瑕佸紑鍙戝摢浜涘姛鑳?- 杩欎簺鍔熻兘灞炰簬鍝釜宸ヤ綔娴佷笌妯″潡
- 搴旇鎸変粈涔堥『搴忓仛
- 姣忎釜浠诲姟鍖呭缓璁Е杈惧摢浜涙枃浠?- 姣忎釜浠诲姟鍖呭畬鎴愬悗濡備綍楠屾敹

鏈枃浠堕粯璁よ鑰咃細

- 鍚庣画鏂藉伐妯″瀷锛歚gpt-5.3-codex`
- 浜虹被瑙掕壊锛氳祫娣辩爺鍙?/ 鏋舵瀯 owner / reviewer

## 2. 浣跨敤鏂瑰紡

鎺ㄨ崘鏂藉伐鑺傚锛?
1. 鍏堜粠鏈枃浠堕€夋嫨涓€涓?`Task Package`
2. 鍐嶆牳瀵?[skill-distillation-v2.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\architecture\skill-distillation-v2.md) 涓殑鏋舵瀯绾︽潫
3. 鍐嶆牳瀵?[skill-distillation-v2-roadmap.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\architecture\skill-distillation-v2-roadmap.md) 涓殑闃舵杈圭晫
4. 姣忔鍙疄鐜颁竴涓换鍔″寘鎴栧悓涓€ Epic 涓嬬殑绱ч偦浠诲姟鍖?5. 姣忓畬鎴愪竴鍖咃紝灏辫ˉ娴嬭瘯銆佽窇鍥炲綊銆佹洿鏂版枃妗?
涓ョ锛?
- 璺宠繃棰嗗煙妯″瀷锛岀洿鎺ュぇ鏀?prompt
- 璺宠繃璐ㄩ噺闂ㄧ锛岀洿鎺ユ墿澶ц嚜鍔ㄥ彂甯?- 鍏堜笂澶嶆潅鍩虹璁炬柦锛屽啀琛ユ牳蹇冭涔夋ā鍨?- 鎶婃墍鏈夋ā鎬佺户缁帇鎴愮函鏂囨湰鍚庡啀鍋氫簩娆℃娊鍙?
## 3. 鎬讳綋浜や粯鍦板浘

```text
E0  鍩虹嚎涓庢柦宸ュ湴鍩?E1  棰嗗煙妯″瀷涓庡吋瀹瑰眰
E2  Corpus 涓庡璧勪骇钂搁
E3  EvidenceNode 璇佹嵁褰掍竴灞?E4  妯℃€佷笓鐢ㄨВ鏋愬櫒涓庡寮?E5  SemanticAtom 鎶藉彇灞?E6  SkillGraph 缁勮涓庡彂甯冨眰
E7  Quality Gate 涓?Review Queue
E8  PostgreSQL / pgvector 鎸佷箙鍖?E9  妫€绱€佸閲忔洿鏂般€乻upersede
E10 澶栭儴鎺ュ彛鍗囩骇锛欳LI / API / Worker
E11 娴嬭瘯璧勪骇銆佽瘎浼般€佸熀鍑嗕笌鍥炲綊
E12 鍙娴嬫€с€佸畨鍏ㄣ€佽繍琛屾不鐞?E13 鏂囨。銆佽縼绉汇€佹敹鍙ｄ笌鍙戝竷
```

## 4. 渚濊禆鍘熷垯

鍏抽敭渚濊禆閾撅細

```text
E0 -> E1 -> E3 -> E5 -> E6 -> E7 -> E8 -> E9 -> E10 -> E13
E2 渚濊禆 E1
E4 渚濊禆 E3
E11 鍏ㄧ▼骞惰锛屼絾姣忎釜 Epic 瀹屾垚閮借琛?E12 寤鸿浠?E7 鍚庡紑濮嬫寔缁ˉ
```

骞惰鍘熷垯锛?
- 鍚屼竴鏃舵湡鍏佽骞惰鐨勪换鍔″寘蹇呴』娌℃湁鏂囦欢鍐欏叆鍐茬獊
- 闇€瑕佹敼 `models.py`銆乣service.py`銆乣repository.py` 鐨勪换鍔″敖閲忎覆琛?- 娴嬭瘯涓庢枃妗ｈˉ榻愬彲鍦ㄤ富鍔熻兘绋冲畾鍚庡苟琛岃ˉ榻?
## 5. DoD

姣忎釜浠诲姟鍖呭畬鎴愮殑鏈€浣?Definition of Done锛?
- 浠ｇ爜宸插疄鐜?- 绫诲瀷/搴忓垪鍖?鎺ュ彛琛屼负鑷唇
- 鏂板鎴栨洿鏂版祴璇?- 鍥炲綊鐜版湁 CLI / API / 鏍稿績鏍锋湰
- 鏇存柊鐩稿叧鏂囨。
- 杈撳嚭涓病鏈夋湭瑙ｉ噴鐨勪复鏃剁粨鏋勬垨 TODO 鍗犱綅

## 6. Epic 绾ф媶瑙?
## E0 鍩虹嚎涓庢柦宸ュ湴鍩?
### 鐩爣

鍐荤粨 V1 琛屼负锛屽缓绔嬩箣鍚庢墍鏈夋敼閫犵殑瀵圭収鍩虹嚎銆?
### 鑼冨洿

- 鍥哄畾鏍锋湰闆?- 褰撳墠杈撳嚭蹇収
- 璐ㄩ噺璇勪及缁村害
- 鏂藉伐瑙勫垯涓庝换鍔℃ā鏉?
### Task Packages

#### TP-E0-01 寤虹珛 V1 鍩虹嚎鏍锋湰闆?
- 鐩爣锛氫负鏂囨湰銆侀煶棰戙€佸浘鐗囥€佽棰戙€佽〃鏍?鏃跺簭鍒嗗埆寤虹珛浠ｈ〃鎬ф牱鏈€?- 瑙﹁揪鐩綍锛?  - `examples/`
  - `tests/fixtures/` 鎴栨柊寤轰笓鐢ㄦ牱鏈洰褰?  - `docs/current/status/`
- 浜や粯锛?  - 鏍锋湰娓呭崟
  - 姣忎釜鏍锋湰鐨勭敤閫旇鏄?  - 椋庨櫓鏍囩
- 楠屾敹锛?  - 鑷冲皯瑕嗙洊 5 绫绘ā鎬?  - 姣忕被鑷冲皯 2 鍒?3 涓牱鏈?
#### TP-E0-02 鍥哄寲褰撳墠 V1 杈撳嚭蹇収

- 鐩爣锛氬鏍锋湰闆嗚窇鍑哄綋鍓?`bundle.json / skill.json / SKILL.md`銆?- 瑙﹁揪鐩綍锛?  - `skills/drafts/`
  - 鏂板缓 `docs/current/status/baselines/` 鎴栫瓑鏁堢洰褰?- 楠屾敹锛?  - 姣忎釜鏍锋湰閮芥湁鍙拷婧緭鍑?  - 鍚庣画鍙汉宸ュ姣?edit distance

#### TP-E0-03 瀹氫箟璇勪及鎸囨爣

- 鐩爣锛氬畾涔?V2 鍏ㄩ摼楠屾敹鎸囨爣銆?- 鎺ㄨ崘鎸囨爣锛?  - `traceability_rate`
  - `actionability_score`
  - `noise_penalty`
  - `reviewer_edit_distance`
  - `duplicate_skill_rate`
  - `false_procedure_rate`
- 楠屾敹锛?  - 鎸囨爣瀹氫箟鍐欏叆 docs
  - 鎸囨爣鍚叕寮忔垨鏄庣‘璁＄畻瑙勫垯

## E1 棰嗗煙妯″瀷涓庡吋瀹瑰眰

### 鐩爣

寮曞叆 V2 棰嗗煙妯″瀷锛屼絾涓嶇牬鍧忕幇鏈夊閮ㄥ叆鍙ｃ€?
### 鑼冨洿

- 鏂版ā鍨?- 鏂?enum
- compatibility transformer
- 搴忓垪鍖?contract

### 鍏抽敭瀵硅薄

- `Corpus`
- `CorpusAssetRef`
- `EvidenceNode`
- `SemanticAtom`
- `SkillGraph`
- `SkillGraphNode`
- `SkillGraphEdge`
- `Publication`
- `LifecycleDecision`

### Task Packages

#### TP-E1-01 鏂板 V2 鍩虹鏋氫妇涓?dataclass

- 鐩爣锛氬湪鐜版湁妯″瀷灞傚缓绔?V2 绫诲瀷绯荤粺銆?- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/models.py`
- 鏂板寤鸿锛?  - `AtomType`
  - `GraphNodeType`
  - `GraphEdgeType`
  - `PublicationType`
  - `LifecycleDecisionType`
- 楠屾敹锛?  - 鎵€鏈夋柊妯″瀷鍙?`to_dict()` / `to_json()`
  - 涓嶇牬鍧忕幇鏈?`SkillDocument`

#### TP-E1-02 寤虹珛鍏煎杞崲鍣?
- 鐩爣锛氳 V2 妯″瀷鍙覆鏌撳洖 V1 瑙嗗浘銆?- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/transformers.py`
  - `src/omni_skill_pipeline/render.py`
- 闇€瑕佽兘鍔涳細
  - `EvidenceUnit -> EvidenceNode`
  - `SkillGraph -> SkillDocument`
- 楠屾敹锛?  - 缁欏畾鏈€灏?`SkillGraph` 鍙互浜у嚭鍚堟硶 `SkillDocument`

#### TP-E1-03 澧炲姞 schema v2 鑽夋

- 鐩爣锛氳缁撴瀯鍖?contract 鍏堣銆?- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/schema.py`
  - `docs/current/contracts/`
- 楠屾敹锛?  - 鑷冲皯鏈?`skill-graph.schema.json` 鎴栫瓑鏁堢粨鏋?  - schema 涓?dataclass 瀛楁瀵归綈

## E2 Corpus 涓庡璧勪骇钂搁

### 鐩爣

浠庘€滃崟 asset 钂搁鈥濆崌绾т负鈥滃璧勪骇鑱斿悎钂搁鈥濄€?
### 鑼冨洿

- `Corpus` 鍒涘缓
- asset bundle 杈撳叆
- corpus metadata
- 璺?asset 杩芥函

### Task Packages

#### TP-E2-01 寤虹珛 Corpus 璇锋眰妯″瀷

- 鐩爣锛氭敮鎸佷竴杞捀棣忕粦瀹氬涓緭鍏ヨ祫婧愩€?- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/models.py`
  - `src/omni_skill_pipeline/interfaces.py`
- 鑳藉姏锛?  - `CorpusDistillRequest`
  - 澶?asset metadata
  - goal 绾ч厤缃?- 楠屾敹锛?  - 鑳借〃杈炬枃妗?闊抽+鍥剧墖鑱斿悎杈撳叆

#### TP-E2-02 Service 鏀寔澶氳祫浜?load

- 鐩爣锛氳 service 鍙互娑堣垂澶氫釜 adapter 杈撳嚭銆?- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/service.py`
- 楠屾敹锛?  - 鍗曡祫浜ц矾寰勪繚鎸佸吋瀹?  - 澶氳祫浜ц矾寰勫彲缁勮鎴愪竴涓?`Corpus`

#### TP-E2-03 缁熶竴 corpus artifact 杈撳嚭

- 鐩爣锛氬皢褰撳墠 bundle 鎵╁睍鎴?corpus 绾?bundle銆?- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/repository.py`
- 楠屾敹锛?  - 涓€娆?corpus 钂搁鑳戒繚瀛樿祫浜ф竻鍗曚笌 cross-asset 寮曠敤

## E3 EvidenceNode 璇佹嵁褰掍竴灞?
### 鐩爣

鏇挎崲 V1 骞抽潰 `EvidenceUnit` 鐨勫崟钖勭粨鏋勶紝寤虹珛甯﹀畾浣嶃€佺粨鏋勩€乴ineage 鐨勮瘉鎹妭鐐广€?
### 鑼冨洿

- time range
- spatial ref
- structural ref
- payload
- parent/child lineage

### Task Packages

#### TP-E3-01 瀹氫箟 EvidenceNode 鏁版嵁缁撴瀯

- 鐩爣锛氳ˉ榻愭墍鏈夋ā鎬佸叡鐢ㄥ瓧娈点€?- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/models.py`
- 瀛楁寤鸿锛?  - `text_content`
  - `payload`
  - `time_range`
  - `spatial_ref`
  - `structural_ref`
  - `parents`
  - `children`
  - `derived_from`
- 楠屾敹锛?  - 鑳借鐩栨枃妗ｃ€佸浘鐗囥€佽棰戙€佽〃鏍笺€佹椂搴忎簲绫诲畾浣嶉渶姹?
#### TP-E3-02 寤虹珛 EvidenceBuilder

- 鐩爣锛氭妸鍚?adapter 鐨勮緭鍑虹粺涓€鏋勯€犳垚 `EvidenceNode`銆?- 涓昏鏂囦欢锛?  - 鏂板缓 `src/omni_skill_pipeline/extraction/evidence_builder.py`
- 楠屾敹锛?  - 鐜版湁 adapter 杈撳嚭鍙槧灏勫埌 `EvidenceNode`

#### TP-E3-03 鏀寔 evidence lineage

- 鐩爣锛氳〃杈?derived evidence銆?- 渚嬪瓙锛?  - 瑙嗛 OCR node 鏉ヨ嚜 frame node
  - 寮傚父 event node 鏉ヨ嚜 timeseries metric node
- 楠屾敹锛?  - 鏀寔 parent/child/derived_from 鍩虹閾捐矾

## E4 妯℃€佷笓鐢ㄨВ鏋愬櫒涓庡寮?
### 鐩爣

鎸夋ā鎬佽ˉ瓒?V2 鐪熸闇€瑕佺殑缁撴瀯淇″彿銆?
### 鑼冨洿

- 鏂囨。缁撴瀯
- 闊抽璇箟
- 鍥剧墖甯冨眬
- 瑙嗛鏃堕棿璇箟
- 琛ㄦ牸/鏃跺簭缁熻璇箟

### Task Packages

#### TP-E4-01 鏂囨。缁撴瀯瑙ｆ瀽澧炲己

- 鐩爣锛氭娊 section銆乼able銆乧ode block銆乫igure銆?- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/adapters/text.py`
  - 鏂板缓 `src/omni_skill_pipeline/extraction/modality/document_parser.py`
- 楠屾敹锛?  - 鏂囨。璇佹嵁涓嶅啀鍙寜 paragraph
  - section hierarchy 鍙拷婧?
#### TP-E4-02 闊抽澧炲己锛歶tterance act 涓?speaker role

- 鐩爣锛氫粠 transcript 鍗囩骇鍒?decision/action/question 灞傘€?- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/adapters/audio.py`
  - 鏂板缓 `src/omni_skill_pipeline/extraction/modality/audio_parser.py`
- 楠屾敹锛?  - 鑷冲皯鍖哄垎 `question / decision / action_item / context`

#### TP-E4-03 鍥剧墖澧炲己锛歭ayout / region / OCR grouping

- 鐩爣锛氳鍥剧墖涓嶆杈撳嚭 OCR 鏂囨湰銆?- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/adapters/image.py`
  - 鏂板缓 `src/omni_skill_pipeline/extraction/modality/image_parser.py`
- 楠屾敹锛?  - 鑷冲皯鏀寔 region 鍒嗙粍涓?layout role

#### TP-E4-04 瑙嗛澧炲己锛歴cene timeline / frame event / subtitle alignment

- 鐩爣锛氳瑙嗛璇佹嵁鍏峰鏃堕棿缁撴瀯銆?- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/adapters/video.py`
  - `src/omni_skill_pipeline/providers/media.py`
  - 鏂板缓 `src/omni_skill_pipeline/extraction/modality/video_parser.py`
- 楠屾敹锛?  - 鍙緭鍑?scene cluster
  - 鍙緭鍑?frame-level event
  - transcript 涓?frame 鍏峰鏈€灏忓榻?
#### TP-E4-05 琛ㄦ牸/鏃跺簭澧炲己锛歜aseline / change point / drift

- 鐩爣锛氳鏃跺簭浠?heuristic profile 鍗囩骇鍒?guardrail-ready 璇箟銆?- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/adapters/tabular.py`
  - 鏂板缓 `src/omni_skill_pipeline/extraction/modality/timeseries_parser.py`
- 楠屾敹锛?  - 鑷冲皯澧炲姞 change point 涓?baseline 姒傚康
  - 鑳芥妸寮傚父鍖洪棿鏄庣‘鎴?`Event` 绫昏瘉鎹?
## E5 SemanticAtom 鎶藉彇灞?
### 鐩爣

鐢?`SemanticAtom` 鏇夸唬瀹芥硾 `Insight`锛屽缓绔嬬粺涓€璇箟鍘熷瓙灞傘€?
### 鍘熷瓙鏈€灏忛泦鍚?
- `ClaimAtom`
- `ProcedureAtom`
- `RuleAtom`
- `VerificationAtom`
- `AntiPatternAtom`
- `EntityAtom`
- `EventAtom`
- `ExampleAtom`
- `MetricGuardrailAtom`
- `QuestionAtom`

### Task Packages

#### TP-E5-01 鏂板缓 AtomExtractor 涓绘帴鍙?
- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/interfaces.py`
  - 鏂板缓 `src/omni_skill_pipeline/extraction/atom_extractor.py`
- 楠屾敹锛?  - 鍙浛浠ｇ幇鏈?`InsightExtractor`

#### TP-E5-02 瀹炵幇 HeuristicAtomExtractor

- 鐩爣锛氬厛鐢ㄥ彲瑙ｉ噴瑙勫垯璧锋銆?- 涓昏鏂囦欢锛?  - 鏂板缓 `src/omni_skill_pipeline/extraction/heuristic_atom_extractor.py`
- 楠屾敹锛?  - 鍩轰簬 `EvidenceNode` 鑷冲皯鑳戒骇鍑?procedure/rule/verification/anti-pattern

#### TP-E5-03 妯℃€佷笓鐢?atom 绛栫暐

- 鐩爣锛氫笉鍚屾ā鎬佽蛋涓嶅悓 atom 绛栫暐銆?- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/extraction/modality/*.py`
- 楠屾敹锛?  - 瑙嗛浼樺厛浜?`EventAtom`
  - 鏃跺簭浼樺厛浜?`MetricGuardrailAtom`
  - 闊抽浼樺厛浜?`QuestionAtom / EventAtom`

#### TP-E5-04 LLM AtomExtractor 浣滀负澧炲己鑰岄潪鐪熺浉婧?
- 鐩爣锛氬湪 heuristic 涔嬪悗寮曞叆澧炲己鎶藉彇銆?- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/providers/openai_provider.py`
  - 鏂板缓 `src/omni_skill_pipeline/extraction/llm_atom_extractor.py`
- 楠屾敹锛?  - LLM 澶辫触鏃朵笉褰卞搷鍩虹鍘熷瓙杈撳嚭

## E6 SkillGraph 缁勮涓庡彂甯冨眰

### 鐩爣

璁?`SkillGraph` 鎴愪负鐪熺浉婧愶紝`SKILL.md` 閫€鍖栦负鍙戝竷瑙嗗浘銆?
### 鑼冨洿

- graph node
- graph edge
- graph builder
- publication builder
- renderer

### Task Packages

#### TP-E6-01 瀹氫箟 SkillGraph node/edge 妯″瀷

- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/models.py`
- 鏈€灏?node锛?  - `StepNode`
  - `DecisionNode`
  - `VerificationNode`
  - `RiskNode`
  - `ExampleNode`
  - `VariableNode`
- 鏈€灏?edge锛?  - `depends_on`
  - `justified_by`
  - `verified_by`
  - `parameterizes`
  - `supersedes`
- 楠屾敹锛?  - graph 鍙畬鏁村簭鍒楀寲

#### TP-E6-02 瀹炵幇 SkillGraphBuilder

- 涓昏鏂囦欢锛?  - 鏂板缓 `src/omni_skill_pipeline/assembly/skill_graph_builder.py`
- 杈撳叆锛?  - `Corpus`
  - `EvidenceNode[]`
  - `SemanticAtom[]`
- 杈撳嚭锛?  - `SkillGraph`
- 楠屾敹锛?  - 鍙粠鏈€灏?atom 闆嗘瀯鍥?  - step 鍙拷鍒?atom/evidence

#### TP-E6-03 瀹炵幇 PublicationBuilder

- 涓昏鏂囦欢锛?  - 鏂板缓 `src/omni_skill_pipeline/assembly/publication_builder.py`
- 鍙戝竷瑙嗗浘锛?  - `SKILL.md`
  - `skill.json`
  - `checklist.json`
  - `decision_tree.json`
- 楠屾敹锛?  - 鑷冲皯涓や釜瑙嗗浘鍙緭鍑?
#### TP-E6-04 鍏煎 V1 renderer

- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/render.py`
- 楠屾敹锛?  - 鐜版湁澶栭儴鎺ュ彛浠嶅彲鎷垮埌 `skill_markdown`

## E7 Quality Gate 涓?Review Queue

### 鐩爣

璁╃郴缁熺湡姝ｅ叿澶団€滀笉鍙戝竷浣庤川閲忔妧鑳解€濈殑鑳藉姏銆?
### 鑼冨洿

- scoring
- review policy
- review task
- feedback loop

### Task Packages

#### TP-E7-01 瀹炵幇璐ㄩ噺璇勫垎鍣?
- 涓昏鏂囦欢锛?  - 鏂板缓 `src/omni_skill_pipeline/quality/scoring.py`
- 鏈€浣庡垎椤癸細
  - `traceability_score`
  - `actionability_score`
  - `coverage_score`
  - `consistency_score`
  - `noise_score`
  - `novelty_score`
- 楠屾敹锛?  - 姣忔钂搁閮借兘鐢熸垚璇勫垎缁撴灉

#### TP-E7-02 瀹炵幇 ReviewPolicy

- 涓昏鏂囦欢锛?  - 鏂板缓 `src/omni_skill_pipeline/quality/review_policy.py`
- 杈撳嚭锛?  - `auto_publish`
  - `review_required`
  - `reject`
- 楠屾敹锛?  - 鏈夋槑纭槇鍊间笌鐞嗙敱鐮?
#### TP-E7-03 ReviewTask 缁撴瀯鍖栬惤鍦?
- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/models.py`
  - `src/omni_skill_pipeline/repository.py`
- 楠屾敹锛?  - review 涓嶆槸鍙湁澶囨敞鏂囨湰
  - 鍘熷洜鐮佷笌淇寤鸿鍙繚瀛?
#### TP-E7-04 鍙嶉鍥炴祦

- 鐩爣锛歳eview 鑳藉弽鍝?atom / graph / policy銆?- 涓昏鏂囦欢锛?  - 鏂板缓 `src/omni_skill_pipeline/quality/feedback.py`
- 楠屾敹锛?  - review feedback 鍙敤浜庡悗缁慨璁?
## E8 PostgreSQL / pgvector 鎸佷箙鍖?
### 鐩爣

浠?file-based artifact store 鍗囩骇涓烘寮忔寔涔呭眰銆?
### 鑼冨洿

- SQL migrations
- PG repository
- dual-write
- vector search storage

### Task Packages

#### TP-E8-01 璁捐 SQL V2 鍒濆琛ㄧ粨鏋?
- 涓昏鏂囦欢锛?  - `infra/sql/`
- 鎺ㄨ崘琛細
  - `corpora`
  - `corpus_assets`
  - `evidence_nodes`
  - `semantic_atoms`
  - `skill_graphs`
  - `skill_graph_nodes`
  - `skill_graph_edges`
  - `publications`
  - `review_tasks`
  - `lineage_links`
- 楠屾敹锛?  - 鑳芥壙杞?corpus銆乬raph銆乸ublication銆乺eview

#### TP-E8-02 瀹炵幇 PostgresRepository

- 涓昏鏂囦欢锛?  - 鏂板缓 `src/omni_skill_pipeline/persistence/postgres_repository.py`
- 楠屾敹锛?  - 鍙繚瀛樺苟閲嶅缓 graph/publication

#### TP-E8-03 Dual-write 绛栫暐

- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/service.py`
  - `src/omni_skill_pipeline/repository.py`
- 楠屾敹锛?  - 鏂囦欢浜х墿涓?PG 鍙悓鏃跺啓鍏?
#### TP-E8-04 鎺?pgvector

- 鐩爣锛氫负 publication 涓?atom 鍑嗗鍚戦噺妫€绱€?- 楠屾敹锛?  - 鑷冲皯鏀寔瀛樹笌鏌?
## E9 妫€绱€佸閲忔洿鏂般€乻upersede

### 鐩爣

璁╂柊璇佹嵁鑳借繘鍏ユ棫鐭ヨ瘑锛岃€屼笉鏄棤闄愬鍒舵柊 skill銆?
### 鑼冨洿

- similarity
- lifecycle decision
- revise / merge / supersede
- lineage

### Task Packages

#### TP-E9-01 鐩镐技鎶€鑳芥绱?
- 涓昏鏂囦欢锛?  - 鏂板缓 `src/omni_skill_pipeline/retrieval/similarity.py`
- 鐩镐技搴︽潵婧愶細
  - embedding
  - domain/tag
  - graph overlap
  - step overlap
- 楠屾敹锛?  - 鑳芥壘鍑虹浉杩?skill

#### TP-E9-02 LifecycleDecisionEngine

- 涓昏鏂囦欢锛?  - 鏂板缓 `src/omni_skill_pipeline/assembly/lifecycle.py`
- 鍐崇瓥锛?  - `new`
  - `revise`
  - `merge`
  - `supersede`
  - `reject`
- 楠屾敹锛?  - 鑳界粰鍑烘槑纭喅绛栦笌鐞嗙敱

#### TP-E9-03 瀹炵幇 supersede / lineage link

- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/models.py`
  - `src/omni_skill_pipeline/persistence/postgres_repository.py`
- 楠屾敹锛?  - 鏂版棫 skill 鍏崇郴鍙拷婧?
## E10 澶栭儴鎺ュ彛鍗囩骇锛欳LI / API / Worker

### 鐩爣

鍦ㄤ笉鐮村潖鐜版湁鍏ュ彛鐨勫墠鎻愪笅锛岃澶栭儴鎺ュ彛璁よ瘑 V2銆?
### 鑼冨洿

- corpus 杈撳叆
- graph 杈撳嚭
- review 鐘舵€佹煡璇?- publication 閫夋嫨

### Task Packages

#### TP-E10-01 CLI 鏀寔 corpus distill

- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/cli.py`
- 鑳藉姏锛?  - 澶氳祫浜ц緭鍏?  - 杈撳嚭瑙嗗浘閫夋嫨
  - review 鐘舵€佸睍绀?- 楠屾敹锛?  - CLI 淇濈暀鍘熷懡浠ゅ苟鏂板 corpus 妯″紡

#### TP-E10-02 API 鏀寔 V2 杈撳嚭缁撴瀯

- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/api_app.py`
- 鏂板寤鸿锛?  - graph metadata
  - available publications
  - review status
  - lifecycle decision
- 楠屾敹锛?  - 鑰佹帴鍙ｄ粛鍙繑鍥?`skill_markdown`

#### TP-E10-03 Worker 浠诲姟绫诲瀷鍗囩骇

- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/worker.py`
  - `apps/worker/main.py`
- 楠屾敹锛?  - 鏀寔 review queue / rebuild publication / revise existing skill

## E11 娴嬭瘯璧勪骇銆佽瘎浼般€佸熀鍑嗕笌鍥炲綊

### 鐩爣

鎶娾€滃ソ鍧忊€濆彉鎴愬彲浠ユ寔缁瘮杈冪殑涓滆タ銆?
### 鑼冨洿

- unit tests
- integration tests
- golden samples
- regression dashboard

### Task Packages

#### TP-E11-01 妯″瀷涓庤浆鎹㈠櫒娴嬭瘯

- 涓昏鏂囦欢锛?  - `tests/`
- 瑕嗙洊锛?  - 鏂版ā鍨嬪簭鍒楀寲
  - graph -> document
  - evidence -> atom -> graph

#### TP-E11-02 妯℃€侀泦鎴愭祴璇?
- 瑕嗙洊锛?  - document -> graph
  - audio -> atom
  - image -> layout/ocr
  - video -> scene timeline
  - timeseries -> guardrail

#### TP-E11-03 璐ㄩ噺鍥炲綊娴嬭瘯

- 鐩爣锛氬浐瀹氭牱鏈泦锛屾瘮杈冭緭鍑鸿川閲忓彉鍖栥€?- 楠屾敹锛?  - 鑷冲皯鑳芥瘮杈?traceability 涓?reviewer edit distance

#### TP-E11-04 鎬ц兘涓庢垚鏈熀绾?
- 鐩爣锛氶伩鍏?V2 璇箟澧炲己瀵艰嚧鎴愭湰澶辨帶銆?- 楠屾敹锛?  - 璁板綍鑰楁椂銆乼oken銆佸叧閿?provider 璋冪敤娆℃暟

## E12 鍙娴嬫€с€佸畨鍏ㄣ€佽繍琛屾不鐞?
### 鐩爣

璁?V2 鍦ㄥ伐绋嬩笂鍙繍琛屻€佸彲璇婃柇銆佸彲鎺с€?
### 鑼冨洿

- structured logs
- metrics
- audit trail
- secret handling
- temp file hygiene

### Task Packages

#### TP-E12-01 缁撴瀯鍖栨棩蹇椾笌 trace id

- 涓昏鏂囦欢锛?  - `src/omni_skill_pipeline/service.py`
  - `src/omni_skill_pipeline/worker.py`
- 楠屾敹锛?  - 姣忚疆钂搁鍏峰 trace id
  - 鍙拷韪?asset -> graph -> publication

#### TP-E12-02 Provider 璋冪敤瀹¤

- 鐩爣锛氳褰?ASR/OCR/LLM/Vision 璋冪敤鎽樿銆?- 楠屾敹锛?  - 鑳芥寜 corpus 鏌ョ湅 provider footprint

#### TP-E12-03 瀹夊叏涓庢晱鎰熶俊鎭帶鍒?
- 鐩爣锛氫繚璇佹棩蹇椾笌 artifacts 涓嶆硠婕忓瘑閽ヤ笌鏁忔劅瀛楁銆?- 楠屾敹锛?  - token銆乻ecret銆乧redential 涓嶈惤鐩?
#### TP-E12-04 涓存椂宸ヤ欢娌荤悊

- 鐩爣锛氭暣鐞?`.tmp_omni_media/` 涓庝腑闂存枃浠剁敓鍛藉懆鏈熴€?- 楠屾敹锛?  - 鏈夋竻鐞嗙瓥鐣ヤ笌澶辫触鍥炴敹绛栫暐

## E13 鏂囨。銆佽縼绉汇€佹敹鍙ｄ笌鍙戝竷

### 鐩爣

璁?V2 鏈€缁堣兘浜ゆ帴銆佽兘杩佺Щ銆佽兘鍙戝竷銆?
### 鑼冨洿

- docs
- migration plan
- V1 deprecation
- release notes

### Task Packages

#### TP-E13-01 鏂囨。鎸佺画鍚屾

- 鑼冨洿锛?  - README
  - architecture
  - contracts
  - operations
  - status
- 楠屾敹锛?  - 澶栭儴鍏ュ彛鏂囨。涓庝唬鐮佷竴鑷?
#### TP-E13-02 V1 -> V2 杩佺Щ鎸囧崡

- 鐩爣锛氬憡璇夌淮鎶よ€呬綍鏃惰蛋鍏煎灞傘€佷綍鏃跺垏鎹富閾俱€?- 楠屾敹锛?  - 杩佺Щ姝ラ銆佸洖閫€绛栫暐銆侀闄╁垪琛ㄩ綈鍏?
#### TP-E13-03 鍙戝竷涓庡垏鎹㈡爣鍑?
- 鐩爣锛氬畾涔変粈涔堟椂鍊欏彲浠ュ甯?V2 鎴愪负涓婚摼銆?- 鏍囧噯鑷冲皯鍖呮嫭锛?  - graph 涓虹湡鐩告簮
  - review queue 宸茶惤鍦?  - 鑷冲皯涓や釜 publication 鍙敤
  - PG repository 绋冲畾
  - 鍩虹嚎鏍锋湰鍥炲綊浼樹簬 V1

#### TP-E13-04 Linux 缁熶竴楠屽案缂栨帓鑴氭湰

- 鐩爣锛氬皢 Linux 鎵归噺楠屾敹鍏ュ彛鏀舵暃涓哄崟涓€鍛戒护鍖咃紝閬垮厤鎵嬪伐涓插懡浠ゆ紡椤广€?- 涓昏鏂囦欢锛?  - `scripts/run_linux_validation_suite.py`
  - `tests/test_linux_validation_suite_script.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 楠屾敹锛?  - 鏀寔闃舵绛涢€夛紙`ci/doc_sync/quality_regression/perf_cost_baseline`锛?  - 鏀寔 dry-run 杈撳嚭璁″垝骞惰惤鐩?JSON
  - 鍙€夊叧闂洖褰?fail gate锛堢敤浜庢紨缁冨満鏅級

#### TP-E13-05 Postgres 闀跨ǔ楠屽案鑴氭湰

- 鐩爣锛氬皢 Postgres 闀跨ǔ楠岃瘉锛堜粨鍌ㄩ摼璺?+ review queue + dual-write benchmark锛夋敹鏁涗负 Linux 鍙洿鎺ユ墽琛岀殑鍗曞懡浠ゅ寘銆?- 涓昏鏂囦欢锛?  - `scripts/run_postgres_soak_validation.py`
  - `tests/test_postgres_soak_validation_script.py`
  - `scripts/run_linux_validation_suite.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 楠屾敹锛?  - 鏀寔闃舵绛涢€夛紙`tp_postgres/review_queue/dual_write_benchmark`锛?  - 鏀寔 dry-run 杈撳嚭璁″垝骞惰惤鐩?JSON
  - 瀵?runtime 闃舵缂哄け Postgres DSN 鏃?fail-fast锛岄伩鍏嶁€滃亣閫氳繃鈥?
#### TP-E13-06 Worker GA 楠岃瘉鑴氭湰

- 鐩爣锛氭妸 worker GA 纭寲楠岃瘉鏀舵暃涓?Linux 鍙洿鎺ユ墽琛岀殑鍗曞懡浠ゅ寘銆?- 涓昏鏂囦欢锛?  - `scripts/run_worker_ga_validation.py`
  - `tests/test_worker_ga_validation_script.py`
  - `scripts/run_linux_validation_suite.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 楠屾敹锛?  - 鏀寔闃舵绛涢€夛紙`worker_corpus/worker_retry/worker_idempotency/worker_claim_lock/worker_task_types`锛?  - 鏀寔 dry-run 杈撳嚭璁″垝骞惰惤鐩?JSON
  - 鍙€氳繃 Linux 缁熶竴缂栨帓鑴氭湰鐨?`worker_ga` stage 鐩存帴璋冪敤

#### TP-E13-07 Provider GA 楠岃瘉鑴氭湰

- 鐩爣锛氭妸 provider GA 纭寲楠岃瘉鏀舵暃涓?Linux 鍙洿鎺ユ墽琛岀殑鍗曞懡浠ゅ寘銆?- 涓昏鏂囦欢锛?  - `scripts/run_provider_ga_validation.py`
  - `tests/test_provider_ga_validation_script.py`
  - `scripts/run_linux_validation_suite.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 楠屾敹锛?  - 鏀寔闃舵绛涢€夛紙`provider_retry/provider_circuit_breaker/provider_failure_budget/provider_config_contract/provider_call_audit/provider_footprint`锛?  - 鏀寔 dry-run 杈撳嚭璁″垝骞惰惤鐩?JSON
  - 鍙€氳繃 Linux 缁熶竴缂栨帓鑴氭湰鐨?`provider_ga` stage 鐩存帴璋冪敤

#### TP-E13-08 Review Queue GA 楠岃瘉鑴氭湰

- 鐩爣锛氭妸 review queue GA 纭寲楠岃瘉鏀舵暃涓?Linux 鍙洿鎺ユ墽琛岀殑鍗曞懡浠ゅ寘銆?- 涓昏鏂囦欢锛?  - `scripts/run_review_queue_ga_validation.py`
  - `tests/test_review_queue_ga_validation_script.py`
  - `scripts/run_linux_validation_suite.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 楠屾敹锛?  - 鏀寔闃舵绛涢€夛紙`review_queue_repository/review_queue_service/review_queue_api/review_feedback/review_feedback_consumer`锛?  - 鏀寔 dry-run 杈撳嚭璁″垝骞惰惤鐩?JSON
  - 鍙€氳繃 Linux 缁熶竴缂栨帓鑴氭湰鐨?`review_queue_ga` stage 鐩存帴璋冪敤

#### TP-E13-09 Calibration GA 楠岃瘉鑴氭湰

- 鐩爣锛氭妸 calibration GA 楠岃瘉鏀舵暃涓?Linux 鍙洿鎺ユ墽琛岀殑鍗曞懡浠ゅ寘銆?- 涓昏鏂囦欢锛?  - `scripts/run_calibration_ga_validation.py`
  - `tests/test_calibration_ga_validation_script.py`
  - `scripts/run_linux_validation_suite.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 楠屾敹锛?  - 鏀寔闃舵绛涢€夛紙`calibration_contract/review_policy_contract/calibration_report`锛?  - 鏀寔 `manifest/calibration-report-output/margin/fail-on-mismatch` 鍙傛暟閫忎紶
  - 鏀寔 dry-run 杈撳嚭璁″垝骞惰惤鐩?JSON
  - 鍙€氳繃 Linux 缁熶竴缂栨帓鑴氭湰鐨?`calibration_ga` stage 鐩存帴璋冪敤

#### TP-E13-10 Postgres GA 楠岃瘉鑴氭湰

- 鐩爣锛氭妸 LC-L2-32/33 鐨?Postgres repository + dual-write GA 楠岃瘉鏀舵暃涓?Linux 鍙洿鎺ユ墽琛岀殑鍗曞懡浠ゅ寘銆?- 涓昏鏂囦欢锛?  - `scripts/run_postgres_ga_validation.py`
  - `tests/test_postgres_ga_validation_script.py`
  - `scripts/run_linux_validation_suite.py`
  - `tests/test_linux_validation_suite_script.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 楠屾敹锛?  - 鏀寔闃舵绛涢€夛紙`postgres_repository_contract/postgres_repository_integration/dual_write_contract/dual_write_integration/dual_write_benchmark`锛?  - 鏀寔 `postgres-dsn/benchmark-iterations/benchmark-output/allow-secondary-failures` 鍙傛暟閫忎紶
  - 瀵?runtime 闃舵缂哄け Postgres DSN 鏃?fail-fast
  - 鏀寔 dry-run 杈撳嚭璁″垝骞惰惤鐩?JSON
  - 鍙€氳繃 Linux 缁熶竴缂栨帓鑴氭湰鐨?`postgres_ga` stage 鐩存帴璋冪敤

#### TP-E13-11 Roadmap 鎵╁睍楠岃瘉鑴氭湰

- 鐩爣锛氭妸 LC-R-34~37锛坮etrieval/lifecycle/publication/review queue surface锛夐獙璇佹敹鏁涗负 Linux 鍙洿鎺ユ墽琛岀殑鍗曞懡浠ゅ寘銆?- 涓昏鏂囦欢锛?  - `scripts/run_roadmap_extension_validation.py`
  - `tests/test_roadmap_extension_validation_script.py`
  - `scripts/run_linux_validation_suite.py`
  - `tests/test_linux_validation_suite_script.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 楠屾敹锛?  - 鏀寔闃舵绛涢€夛紙`retrieval_layer/lifecycle_engine/publication_expansion/review_queue_surface`锛?  - 鏀寔 dry-run 杈撳嚭璁″垝骞惰惤鐩?JSON
  - 鍙€氳繃 Linux 缁熶竴缂栨帓鑴氭湰鐨?`roadmap_extension` stage 鐩存帴璋冪敤



#### TP-E13-12 Release gate 聚合脚本

- 目标：将 beta/ga/roadmap 三个 gate 的 Linux 验证入口聚合为单命令编排，统一 dry-run 计划与参数透传。
- 主要文件：
  - `scripts/run_release_gate_validation.py`
  - `tests/test_release_gate_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 支持阶段筛选（`beta_gate/ga_gate/roadmap_gate`）
  - 支持 coverage/container/postgres/calibration 参数透传到下游 Linux suite
  - 支持 dry-run 输出 `e13-release-gate-validation-plan.json` 与 nested suite 计划

#### TP-E13-13 Release switch 判定脚本

- 目标：将 release gate、TP 合同校验、doc-sync 与证据判定收敛成 Linux 单命令入口，输出 `GO/HOLD` 判定报告。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 支持阶段筛选（`release_gate/release_contract/doc_sync`）
  - 支持 `--decision-only` 直接基于已落盘报告输出判定
  - 支持输出 `e13-release-switch-decision-report.json`，并在 HOLD 时默认返回非零退出码

#### TP-E13-14 Release switch 证据闭环加固

- 目标：将 release switch 的判定门槛升级为必须包含 release-gate 顶层计划与 beta/ga/roadmap 子计划的完整证据包，避免缺包误判 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - decision 评估纳入 `release-gate-output`、`beta-suite-output`、`ga-suite-output`、`roadmap-suite-output`
  - 证据包缺失或阶段不完整时，判定强制 `HOLD`
  - 完整证据包场景可稳定输出 `GO`

#### TP-E13-15 Release switch 证据时效门禁

- 目标：在 release switch 判定中加入 evidence freshness 守门，避免复用陈旧报告误判 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 支持 `--max-evidence-age-hours`（默认开启 freshness 门禁）
  - evidence 文件超时效窗口时，判定强制 `HOLD`
  - 支持 `--max-evidence-age-hours 0` 显式关闭 freshness 门禁

#### TP-E13-16 Release switch 未来时间偏移门禁

- 目标：在 release switch 判定中加入 future timestamp skew 守门，防止证据文件时间被调到未来导致 freshness 绕过。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 支持 `--max-evidence-future-skew-hours`（默认开启 future-skew 门禁）
  - evidence 文件未来偏移超过阈值时，判定强制 `HOLD`
  - 支持 `--max-evidence-future-skew-hours 0` 显式关闭 future-skew 门禁

#### TP-E13-17 Release switch 证据批次一致性门禁

- 目标：在 release switch 判定中加入 evidence cohort skew 守门，避免混用跨批次报告导致 `GO` 误判。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 支持 `--max-evidence-cohort-skew-hours`（默认开启 cohort-skew 门禁）
  - evidence 文件时间跨度超过阈值时，判定强制 `HOLD`
  - 支持 `--max-evidence-cohort-skew-hours 0` 显式关闭 cohort-skew 门禁

#### TP-E13-18 Release switch 证据绑定一致性门禁

- 目标：在 release switch 判定中加入 release-gate 证据绑定守门，确保 `release-gate-output` 内部 beta/ga/roadmap stage 的 `--output` 指向与本次判定传入证据路径一致，避免混包误判 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage `--output` 与 `--beta-suite-output/--ga-suite-output/--roadmap-suite-output` 一致性
  - 任一 stage 输出绑定错配时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-output-binding-check` 显式关闭绑定门禁

#### TP-E13-19 Release switch stage 合同一致性门禁

- 目标：在 release switch 判定中加入 release-gate stage 合同守门，确保 `beta_gate/ga_gate/roadmap_gate` 命令持续指向 `scripts/run_linux_validation_suite.py` 且 `--stages` 组合保持约定，防止“路径一致但执行计划漂移”误判 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage 命令必须匹配 `scripts/run_linux_validation_suite.py + --stages` 合同
  - 任一 stage 命令或 `--stages` 漂移时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-stage-contract-check` 显式关闭 stage 合同门禁

#### TP-E13-20 Release switch 参数覆盖歧义门禁

- 目标：在 release switch 判定中加入 release-gate 参数覆盖歧义守门，确保 `beta_gate/ga_gate/roadmap_gate` 命令中的 `--stages` 与 `--output` 仅出现一次，防止重复参数覆盖绕过合同校验误判 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate 各 stage 命令 `--stages/--output` 参数出现次数必须为 `1`
  - 任一 stage 存在重复参数覆盖歧义时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-option-override-check` 显式关闭参数覆盖门禁

#### TP-E13-21 Release switch 宽松开关绕过门禁

- 目标：在 release switch 判定中加入 release-gate 宽松开关守门，阻断通过 `--allow-regression/--no-coverage/--container-skip-build/--container-skip-run/--allow-secondary-failures` 等降级参数“带病放行”的 `GO` 误判。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage 命令不得包含宽松开关参数
  - 任一 stage 命中宽松开关时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-relaxed-flags-check` 显式关闭宽松开关门禁

#### TP-E13-22 Release switch dry-run 绕过门禁

- 目标：在 release switch 判定中加入 release-gate dry-run 守门，阻断通过 `--dry-run` 伪执行 stage 命令导致“证据看似完整但未真实执行”的 `GO` 误判。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage 命令不得包含 `--dry-run`
  - 任一 stage 命中 `--dry-run` 时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-dry-run-check` 显式关闭 dry-run 门禁

#### TP-E13-23 Release switch 脚本定位伪装门禁

- 目标：在 release switch 判定中加入 release-gate 脚本定位守门，确保 `beta_gate/ga_gate/roadmap_gate` 命令真正执行的是 `scripts/run_linux_validation_suite.py`，而不是“命令中仅携带同名 token”的伪装路径。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage 命令中第一个 script token 必须是 `scripts/run_linux_validation_suite.py`
  - 若预期脚本仅作为附带 token 出现（未实际执行）时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-script-position-check` 显式关闭脚本定位门禁

#### TP-E13-24 Release switch inline-exec 绕过门禁

- 目标：在 release switch 判定中加入 release-gate inline-dispatch 守门，阻断通过 `-c/-m/-` 让 python 在预期 linux-suite script token 前切换执行模式的绕过路径。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage 命令在 `scripts/run_linux_validation_suite.py` token 之前不得出现 `-c/-m/-`
  - 任一 stage 命中 inline-dispatch 绕过模式时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-inline-exec-check` 显式关闭 inline-dispatch 门禁

#### TP-E13-25 Release switch 脚本路径锚定门禁

- 目标：在 release switch 判定中加入 release-gate script anchor 守门，确保 stage 命令解析后的执行脚本必须锚定仓库内 canonical `scripts/run_linux_validation_suite.py`，阻断同名外部路径伪装绕过。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage 首个 script token 解析后的 canonical path 必须等于仓库内 `scripts/run_linux_validation_suite.py`
  - 任一 stage 命中同名外部路径伪装时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-script-anchor-check` 显式关闭 script-anchor 门禁

#### TP-E13-26 Release switch Python 绑定一致性门禁

- 目标：在 release switch 判定中加入 release-gate python-binding 守门，确保 stage 命令的 `--python` 与实际 launcher 前缀、以及 release-switch 输入值三方一致，阻断执行器覆盖或漂移导致的伪 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage 命令 `--python` 仅出现一次，且值必须等于 release-switch 输入 `--python`
  - 默认校验 release-gate stage 命令脚本前 launcher token 串必须与 `--python` 值绑定一致
  - 任一 stage 命中 python-binding 漂移时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-binding-check` 显式关闭 python-binding 门禁

#### TP-E13-27 Release switch 覆盖率阈值绑定门禁

- 目标：在 release switch 判定中加入 release-gate coverage-floor 守门，确保 beta stage 的 `--coverage-fail-under` 既与 release-switch 输入绑定一致，也不低于最低发布阈值，阻断“降阈值放行”导致的伪 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate` 命令 `--coverage-fail-under` 仅出现一次且为可解析浮点值
  - 默认校验该值必须等于 release-switch 输入 `--coverage-fail-under` 且不低于 `50`
  - 任一命中 coverage 阈值漂移或降级时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-coverage-floor-check` 显式关闭 coverage-floor 门禁

#### TP-E13-28 Release switch Python 优化旗标门禁

- 目标：在 release switch 判定中加入 release-gate python-optimization 守门，禁止 stage launcher 使用 `-O/-OO` 优化旗标，避免 assert 校验被跳过导致伪 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `-O/-OO`
  - 任一 stage 命中 python 优化旗标时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-optimization-check` 显式关闭 python-optimization 门禁

#### TP-E13-29 Release switch Python 传递链优化旗标门禁

- 目标：在 release switch 判定中加入 release-gate `--python` 传递链 optimization 守门，禁止 stage `--python` 值携带 `-O/-OO`，避免下游执行链被隐式优化导致 assert 合同被绕过。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令 `--python` 仅出现一次且可解析
  - 默认校验 `--python` 传递值中不允许出现 `-O/-OO`
  - 任一 stage 命中 `--python` 传递优化旗标时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-option-optimization-check` 显式关闭该门禁

#### TP-E13-30 Release switch PYTHONOPTIMIZE 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONOPTIMIZE` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 env 赋值绕过 assert 合同校验。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONOPTIMIZE=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONOPTIMIZE=*`
  - 任一 stage 命中 `PYTHONOPTIMIZE` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-optimize-env-check` 显式关闭该门禁

#### TP-E13-31 Release switch Python 传递链 inline-exec 门禁

- 目标：在 release switch 判定中加入 release-gate `--python` 传递链 inline-dispatch 守门，禁止 stage `--python` 值携带 `-c/-m/-`，避免下游执行链切换成 inline 模式绕过脚本合同。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令 `--python` 仅出现一次且可解析
  - 默认校验 `--python` 传递值中不允许出现 `-c/-m/-`
  - 任一 stage 命中 `--python` 传递 inline-dispatch 旗标时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-option-inline-exec-check` 显式关闭该门禁

#### TP-E13-32 Release switch PYTHONPATH 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONPATH` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 path 注入重定向模块解析，避免绕过预期 runtime 合同。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONPATH=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONPATH=*`
  - 任一 stage 命中 `PYTHONPATH` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-path-env-check` 显式关闭该门禁

#### TP-E13-33 Release switch PYTHONHOME 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONHOME` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 home 注入重定向解释器运行时根路径，避免绕过预期 runtime 合同。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONHOME=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONHOME=*`
  - 任一 stage 命中 `PYTHONHOME` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-home-env-check` 显式关闭该门禁

#### TP-E13-34 Release switch PYTHONUSERBASE 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONUSERBASE` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 user-base 注入重定向 user-site 包解析路径，避免绕过预期 runtime 合同。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONUSERBASE=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONUSERBASE=*`
  - 任一 stage 命中 `PYTHONUSERBASE` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-user-base-env-check` 显式关闭该门禁

#### TP-E13-35 Release switch PYTHONBREAKPOINT 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONBREAKPOINT` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 breakpoint hook 注入改变调试分发行为，避免绕过预期 runtime 合同。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONBREAKPOINT=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONBREAKPOINT=*`
  - 任一 stage 命中 `PYTHONBREAKPOINT` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-breakpoint-env-check` 显式关闭该门禁

#### TP-E13-36 Release switch PYTHONSTARTUP 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONSTARTUP` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 startup hook 注入启动脚本，避免绕过预期 runtime 合同。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONSTARTUP=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONSTARTUP=*`
  - 任一 stage 命中 `PYTHONSTARTUP` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-startup-env-check` 显式关闭该门禁

#### TP-E13-37 Release switch PYTHONINSPECT 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONINSPECT` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 inspect hook 切入交互模式，避免执行链漂移误判 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONINSPECT=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONINSPECT=*`
  - 任一 stage 命中 `PYTHONINSPECT` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-inspect-env-check` 显式关闭该门禁

#### TP-E13-38 Release switch PYTHONWARNINGS 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONWARNINGS` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 warning filter 注入掩盖发布期间的告警契约漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONWARNINGS=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONWARNINGS=*`
  - 任一 stage 命中 `PYTHONWARNINGS` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-warnings-env-check` 显式关闭该门禁

#### TP-E13-39 Release switch 未登记 PYTHON* 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate 未登记 `PYTHON*` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过未纳入显式门禁名单的 `PYTHON*` 赋值漂移运行时契约。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现未知 `PYTHON*` 赋值（已登记门禁键除外）
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现未知 `PYTHON*` 赋值（已登记门禁键除外）
  - 任一 stage 命中未知 `PYTHON*` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-env-wildcard-check` 显式关闭该门禁

#### TP-E13-40 Release switch PATH 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PATH` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `PATH=*` 赋值重定向解释器解析路径，避免命中非预期 Python runtime 导致伪 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PATH=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PATH=*`
  - 任一 stage 命中 `PATH` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-path-env-check` 显式关闭该门禁

#### TP-E13-41 Release switch LD_PRELOAD 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `LD_PRELOAD` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `LD_PRELOAD=*` 注入动态加载器 hook，避免运行时被旁路导致伪 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `LD_PRELOAD=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `LD_PRELOAD=*`
  - 任一 stage 命中 `LD_PRELOAD` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-ld-preload-env-check` 显式关闭该门禁

#### TP-E13-42 Release switch LD_LIBRARY_PATH 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `LD_LIBRARY_PATH` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `LD_LIBRARY_PATH=*` 重定向动态链接器查找路径，避免运行时库解析漂移导致伪 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `LD_LIBRARY_PATH=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `LD_LIBRARY_PATH=*`
  - 任一 stage 命中 `LD_LIBRARY_PATH` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-ld-library-path-env-check` 显式关闭该门禁

#### TP-E13-43 Release switch LD_AUDIT 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `LD_AUDIT` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `LD_AUDIT=*` 注入动态链接器审计 hook，避免运行时旁路导致伪 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `LD_AUDIT=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `LD_AUDIT=*`
  - 任一 stage 命中 `LD_AUDIT` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-ld-audit-env-check` 显式关闭该门禁

#### TP-E13-44 Release switch 未登记 LD_* 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate 未登记 `LD_*` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过未纳入显式门禁名单的 `LD_*` 赋值漂移动态链接器运行时契约。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现未知 `LD_*` 赋值（已登记门禁键除外）
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现未知 `LD_*` 赋值（已登记门禁键除外）
  - 任一 stage 命中未知 `LD_*` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-ld-env-wildcard-check` 显式关闭该门禁

#### TP-E13-45 Release switch GLIBC_TUNABLES 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `GLIBC_TUNABLES` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `GLIBC_TUNABLES=*` 漂移 glibc 动态链接器 tunables 契约。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `GLIBC_TUNABLES=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `GLIBC_TUNABLES=*`
  - 任一 stage 命中 `GLIBC_TUNABLES` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-glibc-tunables-env-check` 显式关闭该门禁

#### TP-E13-46 Release switch 未登记 GLIBC_* 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate 未登记 `GLIBC_*` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过未纳入显式门禁名单的 `GLIBC_*` 赋值漂移 glibc 运行时契约。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现未知 `GLIBC_*` 赋值（已登记门禁键除外）
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现未知 `GLIBC_*` 赋值（已登记门禁键除外）
  - 任一 stage 命中未知 `GLIBC_*` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-glibc-env-wildcard-check` 显式关闭该门禁

#### TP-E13-47 Release switch 未登记 MALLOC_* 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate 未登记 `MALLOC_*` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过未纳入显式门禁名单的 `MALLOC_*` 赋值漂移内存分配器运行时契约。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现未知 `MALLOC_*` 赋值（已登记门禁键除外）
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现未知 `MALLOC_*` 赋值（已登记门禁键除外）
  - 任一 stage 命中未知 `MALLOC_*` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-env-wildcard-check` 显式关闭该门禁

#### TP-E13-48 Release switch MALLOC_TRACE 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_TRACE` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_TRACE=*` 注入分配器追踪输出与侧信道痕迹。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_TRACE=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_TRACE=*`
  - 任一 stage 命中 `MALLOC_TRACE` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-trace-env-check` 显式关闭该门禁

#### TP-E13-49 Release switch MALLOC_CHECK_ 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_CHECK_` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_CHECK_=*` 改写 glibc 分配器检查策略。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_CHECK_=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_CHECK_=*`
  - 任一 stage 命中 `MALLOC_CHECK_` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-check-env-check` 显式关闭该门禁

#### TP-E13-50 Release switch MALLOC_PERTURB_ 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_PERTURB_` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_PERTURB_=*` 注入内存扰动策略，避免运行时行为与基线判定出现漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_PERTURB_=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_PERTURB_=*`
  - 任一 stage 命中 `MALLOC_PERTURB_` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-perturb-env-check` 显式关闭该门禁

#### TP-E13-51 Release switch MALLOC_ARENA_MAX 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_ARENA_MAX` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_ARENA_MAX=*` 改写 allocator arena 并发扩展策略，避免运行时资源行为与基线判定漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_ARENA_MAX=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_ARENA_MAX=*`
  - 任一 stage 命中 `MALLOC_ARENA_MAX` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-arena-max-env-check` 显式关闭该门禁

#### TP-E13-52 Release switch MALLOC_MMAP_THRESHOLD_ 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_MMAP_THRESHOLD_` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_MMAP_THRESHOLD_=*` 改写 allocator mmap 阈值策略，避免运行时内存分配路径与基线判定漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_MMAP_THRESHOLD_=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_MMAP_THRESHOLD_=*`
  - 任一 stage 命中 `MALLOC_MMAP_THRESHOLD_` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-mmap-threshold-env-check` 显式关闭该门禁

#### TP-E13-53 Release switch MALLOC_MMAP_MAX_ 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_MMAP_MAX_` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_MMAP_MAX_=*` 改写 allocator mmap 数量阈值策略，避免运行时分配形态与基线判定漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_MMAP_MAX_=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_MMAP_MAX_=*`
  - 任一 stage 命中 `MALLOC_MMAP_MAX_` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-mmap-max-env-check` 显式关闭该门禁

#### TP-E13-54 Release switch MALLOC_TOP_PAD_ 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_TOP_PAD_` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_TOP_PAD_=*` 改写 allocator top chunk padding 策略，避免运行时堆增长行为与基线判定漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_TOP_PAD_=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_TOP_PAD_=*`
  - 任一 stage 命中 `MALLOC_TOP_PAD_` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-top-pad-env-check` 显式关闭该门禁

#### TP-E13-55 Release switch MALLOC_TRIM_THRESHOLD_ 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_TRIM_THRESHOLD_` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_TRIM_THRESHOLD_=*` 改写 allocator trim threshold 策略，避免运行时内存回收行为与基线判定漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_TRIM_THRESHOLD_=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_TRIM_THRESHOLD_=*`
  - 任一 stage 命中 `MALLOC_TRIM_THRESHOLD_` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-trim-threshold-env-check` 显式关闭该门禁

#### TP-E13-56 Release switch MALLOC_ARENA_TEST 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_ARENA_TEST` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_ARENA_TEST=*` 改写 allocator arena probing 策略，避免运行时 arena 扩展行为与基线判定漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_ARENA_TEST=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_ARENA_TEST=*`
  - 任一 stage 命中 `MALLOC_ARENA_TEST` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-arena-test-env-check` 显式关闭该门禁

#### TP-E13-57 Release switch MALLOC_PER_THREAD 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_PER_THREAD` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_PER_THREAD=*` 改写 allocator per-thread arena pooling 策略，避免运行时线程内存分配行为与基线判定漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_PER_THREAD=*`
- 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_PER_THREAD=*`
- 任一 stage 命中 `MALLOC_PER_THREAD` 赋值时，判定强制 `HOLD`
- 支持 `--skip-release-gate-malloc-per-thread-env-check` 显式关闭该门禁

#### TP-E13-58 Release switch 决策 JSON 批量测算视图

- 目标：在保持现有 `decision/evidence_summary/gates` 兼容前提下，新增 `bulk_strategy_view` 结构化视图，避免每次新增 gate 都要求下游测算器改 schema，支持海量批处理的稳定解析。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 新增 `bulk_strategy_view`，包含固定骨架：`schema_version/decision/gate_count/pass_count/hold_count/gate_status_bitmap/gate_status_index/gate_rows/check_enablement/evidence_status_counts/evidence_freshness_counts`
  - `bulk_strategy_view` 中 gate 汇总与原始 `gates` 一致（计数、通过/阻断结果、门禁名映射）
  - `bulk_strategy_view` 同时适用于 `GO` 与 `HOLD` 决策样本
  - 保持旧字段不删除，避免破坏既有消费者

#### TP-E13-59 Release switch 批量测算域聚合签名

- 目标：在 `bulk_strategy_view` 上增加 domain 级聚合与签名字段，支持海量测算直接按域统计、按 hold 签名分桶，而无需二次遍历长 gate 明细。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - `bulk_strategy_view` 升级为 `schema_version=release_switch_bulk_strategy.v2`
  - 新增 `decision_code/hold_signature/pass_gate_indices/hold_gate_indices/gate_domain_index/domain_rollup`
  - `domain_rollup` 需给出每个 domain 的 `gate_count/pass_count/hold_count/pass_ratio`
  - `GO` 样本 `hold_signature` 固定为 `GO`；`HOLD` 样本 `hold_signature` 必须包含关键阻断 gate 名

#### TP-E13-60 Release switch 批量测算签名哈希固化

- 目标：在 `bulk_strategy_view` 上补齐固定宽度哈希签名字段，支撑海量聚合作业在不依赖长字符串索引的情况下完成分桶与去重，同时保持 `decision/gates/evidence_summary` 兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `hold_signature_sha256`
  - 决策 JSON 的 `bulk_strategy_view` 新增 `strategy_signature_sha256`
  - 两个签名字段均为 64 位十六进制字符串，且可由稳定规则重算
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-61 Release switch 批量测算域聚合哈希固化

- 目标：在 `bulk_strategy_view` 上补齐 domain 聚合轮廓的固定宽度签名字段，支撑海量策略作业按域聚合画像做快速索引与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `domain_rollup_sha256`
  - `domain_rollup_sha256` 必须由稳定 canonical payload 重算：`decision/domain_rollup/gate_domain_index`
  - `domain_rollup_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-62 Release switch 批量测算证据轮廓哈希固化

- 目标：在 `bulk_strategy_view` 上补齐 evidence 轮廓的固定宽度签名字段，支撑海量策略作业按证据状态画像快速分桶、去重与回放，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `evidence_profile_sha256`
  - `evidence_profile_sha256` 必须由稳定 canonical payload 重算：`decision/evidence_file_count/evidence_status_counts/evidence_freshness_counts`
  - `evidence_profile_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-63 Release switch 批量测算门阵索引哈希固化

- 目标：在 `bulk_strategy_view` 上补齐 gate 状态索引轮廓的固定宽度签名字段，支撑海量策略作业按门阵状态向量快速分桶、去重与回放，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `gate_status_index_sha256`
  - `gate_status_index_sha256` 必须由稳定 canonical payload 重算：`decision/gate_names/gate_status_bitmap/gate_status_index`
  - `gate_status_index_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-64 Release switch 批量测算组合轮廓哈希固化

- 目标：在 `bulk_strategy_view` 上补齐跨维度组合轮廓的固定宽度签名字段，把现有多维哈希收敛为单一主索引，支撑海量策略作业快速分桶、去重与回放，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `composite_profile_sha256`
  - `composite_profile_sha256` 必须由稳定 canonical payload 重算：`decision/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256`
  - `composite_profile_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-65 Release switch 批量测算策略包络哈希固化

- 目标：在 `bulk_strategy_view` 上补齐策略包络级固定宽度签名字段，将决策码、门阵计数、证据计数与既有多维哈希绑定为统一索引，支撑跨批次快速对账、分桶与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `strategy_envelope_sha256`
  - `strategy_envelope_sha256` 必须由稳定 canonical payload 重算：`decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `strategy_envelope_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-66 Release switch 批量测算合同签名哈希固化

- 目标：在 `bulk_strategy_view` 上补齐合同级固定宽度签名字段，将 schema 版本、门阵域索引、门禁启停键与策略包络哈希绑定为统一合同签名，支撑跨批次合同漂移检测与快速对账，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `contract_signature_sha256`
  - `contract_signature_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/gate_names/gate_domain_index/check_enablement.enabled_keys/check_enablement.disabled_keys/strategy_envelope_sha256`
  - `contract_signature_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-67 Release switch 批量测算合同包络哈希固化

- 目标：在 `bulk_strategy_view` 上补齐合同包络级固定宽度签名字段，将合同签名与批次门阵/证据计数绑定为统一包络索引，支撑跨批次合同+姿态快速对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `contract_envelope_sha256`
  - `contract_envelope_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/contract_signature_sha256/strategy_envelope_sha256/composite_profile_sha256`
  - `contract_envelope_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-68 Release switch 批量测算发布指纹哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布级固定宽度指纹字段，将合同签名、合同包络、姿态轮廓与门禁启停键绑定为统一发布指纹，支撑跨批次一键发布对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_fingerprint_sha256`
  - `release_fingerprint_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/hold_signature_sha256/strategy_envelope_sha256/contract_signature_sha256/contract_envelope_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_fingerprint_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-69 Release switch 批量测算发布清单哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布清单级固定宽度哈希字段，将发布指纹与门阵状态、域索引、证据轮廓绑定为统一发布清单索引，支撑跨批次发布面快速回放、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_manifest_sha256`
  - `release_manifest_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/gate_names/gate_status_bitmap/gate_domain_index/domain_rollup_sha256/evidence_profile_sha256/release_fingerprint_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_manifest_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-70 Release switch 批量测算发布根签名哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布根级固定宽度哈希字段，将发布清单哈希与核心姿态签名绑定统一根索引，支撑跨批次快速对账、去重与回放，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_root_sha256`
  - `release_root_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256/composite_profile_sha256/strategy_envelope_sha256/contract_signature_sha256/contract_envelope_sha256/release_fingerprint_sha256/release_manifest_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_root_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-71 Release switch 批量测算发布见证哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布见证级固定宽度哈希字段，将发布根签名与发布清单、发布指纹及核心姿态索引绑定为统一见证键，支撑跨批次发布产物快速验签、对账与追踪，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_attestation_sha256`
  - `release_attestation_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/hold_signature_sha256/strategy_signature_sha256/gate_status_bitmap/gate_status_index_sha256/domain_rollup_sha256/evidence_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_attestation_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-72 Release switch 批量测算发布裁决哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布裁决级固定宽度哈希字段，将发布见证、发布根、发布清单、发布指纹与合同姿态包络绑定为统一裁决键，支撑跨批次一键发布对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_verdict_sha256`
  - `release_verdict_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/strategy_envelope_sha256/contract_envelope_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_verdict_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-73 Release switch 批量测算发布谱系哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布谱系级固定宽度哈希字段，将发布裁决、发布见证、发布根签名、发布清单与核心姿态签名索引绑定为统一谱系键，支撑跨批次发布链路回放、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_lineage_sha256`
  - `release_lineage_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_lineage_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-74 Release switch 批量测算发布胶囊哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布胶囊级固定宽度哈希字段，将发布谱系签名与核心判定计数收敛为紧凑统一索引，支撑跨批次快速对账、分桶与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_capsule_sha256`
  - `release_capsule_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_capsule_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-75 Release switch 批量测算发布锚点哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布锚点级固定宽度哈希字段，将发布胶囊签名与发布清单/发布指纹以及合同策略包络收敛为统一锚点索引，支撑跨批次极速对账、分桶与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_anchor_sha256`
  - `release_anchor_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_anchor_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-76 Release switch 批量测算发布信标哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布信标级固定宽度哈希字段，将发布锚点与门阵索引/组合轮廓及合同策略包络收敛为统一信标索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_beacon_sha256`
  - `release_beacon_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_beacon_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-77 Release switch 批量测算发布星图哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布星图级固定宽度哈希字段，将发布信标与谱系姿态签名收敛为统一星图索引，支撑跨批次极速路由、对账与回放，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_constellation_sha256`
  - `release_constellation_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_constellation_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-78 Release switch 批量测算发布星系哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布星系级固定宽度哈希字段，将发布星图与双签姿态收敛为统一星系索引，支撑跨批次极速路由、对账与回放，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_galaxy_sha256`
  - `release_galaxy_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_galaxy_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-79 Release switch 批量测算发布宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布宇宙级固定宽度哈希字段，将发布星系哈希与多维姿态签名收敛为统一宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_universe_sha256`
  - `release_universe_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_universe_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-80 Release switch 批量测算发布多元宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布多元宇宙级固定宽度哈希字段，将发布宇宙哈希与多维姿态签名收敛为统一多元宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_multiverse_sha256`
  - `release_multiverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_multiverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-81 Release switch 批量测算发布超宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布超宇宙级固定宽度哈希字段，将发布多元宇宙哈希与多维姿态签名收敛为统一超宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_omniverse_sha256`
  - `release_omniverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_omniverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-82 Release switch 批量测算发布极宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布极宇宙级固定宽度哈希字段，将发布超宇宙哈希与多维姿态签名收敛为统一极宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_hyperverse_sha256`
  - `release_hyperverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_hyperverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-83 Release switch 批量测算发布巨宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布巨宇宙级固定宽度哈希字段，将发布极宇宙哈希与多维姿态签名收敛为统一巨宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_megaverse_sha256`
  - `release_megaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_megaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-84 Release switch 批量测算发布十亿宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布十亿宇宙级固定宽度哈希字段，将发布巨宇宙哈希与多维姿态签名收敛为统一十亿宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_gigaverse_sha256`
  - `release_gigaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_gigaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-85 Release switch 批量测算发布万亿宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布万亿宇宙级固定宽度哈希字段，将发布十亿宇宙哈希与多维姿态签名收敛为统一万亿宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_teraverse_sha256`
  - `release_teraverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_teraverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-86 Release switch 批量测算发布千万亿宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布千万亿宇宙级固定宽度哈希字段，将发布万亿宇宙哈希与多维姿态签名收敛为统一千万亿宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_petaverse_sha256`
  - `release_petaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_petaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-87 Release switch 批量测算发布百京宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布百京宇宙级固定宽度哈希字段，将发布千万亿宇宙哈希与多维姿态签名收敛为统一百京宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_exaverse_sha256`
  - `release_exaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_exaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-88 Release switch 批量测算发布十垓宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布十垓宇宙级固定宽度哈希字段，将发布百京宇宙哈希与多维姿态签名收敛为统一十垓宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_zettaverse_sha256`
  - `release_zettaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_zettaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-89 Release switch 批量测算发布尧它宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布尧它宇宙级固定宽度哈希字段，将发布十垓宇宙哈希与多维姿态签名收敛为统一尧它宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_yottaverse_sha256`
  - `release_yottaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_yottaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-90 Release switch 批量测算发布罗纳宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布罗纳宇宙级固定宽度哈希字段，将发布秭宇宙哈希与多维姿态签名收敛为统一罗纳宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_ronnaverse_sha256`
  - `release_ronnaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_ronnaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-91 Release switch 批量测算发布昆塔宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布昆塔宇宙级固定宽度哈希字段，将发布罗纳宇宙哈希与多维姿态签名收敛为统一昆塔宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_quettaverse_sha256`
  - `release_quettaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_quettaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-92 Release switch 批量测算发布极巅宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布极巅宇宙级固定宽度哈希字段，将发布昆塔宇宙哈希与多维姿态签名收敛为统一极巅宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_apexverse_sha256`
  - `release_apexverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_apexverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-93 Release switch 批量测算发布终极宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布终极宇宙级固定宽度哈希字段，将发布极巅宇宙哈希与多维姿态签名收敛为统一终极宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_ultimaverse_sha256`
  - `release_ultimaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_ultimaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-94 Release switch 批量测算发布超越宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布超越宇宙级固定宽度哈希字段，将发布终极宇宙哈希与多维姿态签名收敛为统一超越宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_transcendaverse_sha256`
  - `release_transcendaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_transcendaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-95 Release switch 批量测算发布无限宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布无限宇宙级固定宽度哈希字段，将发布超越宇宙哈希与多维姿态签名收敛为统一无限宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_infinitaverse_sha256`
  - `release_infinitaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_infinitaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-96 Release switch 批量测算发布永恒宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布永恒宇宙级固定宽度哈希字段，将发布无限宇宙哈希与多维姿态签名收敛为统一永恒宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_eternaverse_sha256`
  - `release_eternaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_eternaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-97 Release switch 批量测算发布永序宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布永序宇宙级固定宽度哈希字段，将发布永恒宇宙哈希与多维姿态签名收敛为统一永序宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_timelessverse_sha256`
  - `release_timelessverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_timelessverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-98 Release switch 批量测算发布纪元宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布纪元宇宙级固定宽度哈希字段，将发布永序宇宙哈希与多维姿态签名收敛为统一纪元宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_aeonverse_sha256`
  - `release_aeonverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_aeonverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-99 Release switch 批量测算发布世代宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布世代宇宙级固定宽度哈希字段，将发布纪元宇宙哈希与多维姿态签名收敛为统一世代宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_epochverse_sha256`
  - `release_epochverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_epochverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-100 Release switch 批量测算发布元宇宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布元宇宇宙级固定宽度哈希字段，将发布世代宇宙哈希与多维姿态签名收敛为统一元宇宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_eraverse_sha256`
- `release_eraverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
- `release_eraverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
- 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-101 Release switch 批量测算发布超元宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布超元宇宙级固定宽度哈希字段，将发布元宇宇宙哈希与多维姿态签名收敛为统一超元宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_metaverse_sha256`
  - `release_metaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_metaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-102 Release switch 批量测算发布平行宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布平行宇宙级固定宽度哈希字段，将发布超元宇宙哈希与多维姿态签名收敛为统一平行宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_paraverse_sha256`
  - `release_paraverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_paraverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-103 Release switch 批量测算发布多维宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布多维宇宙级固定宽度哈希字段，将发布平行宇宙哈希与多维姿态签名收敛为统一多维宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_polyverse_sha256`
  - `release_polyverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_polyverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-104 Release switch 批量测算发布泛宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布泛宇宙级固定宽度哈希字段，将发布多维宇宙哈希与多维姿态签名收敛为统一泛宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_panverse_sha256`
  - `release_panverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_panverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-105 Release switch 批量测算发布全息宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布全息宇宙级固定宽度哈希字段，将发布泛宇宙哈希与多维姿态签名收敛为统一全息宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_holoverse_sha256`
  - `release_holoverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_holoverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-106 Release switch 批量测算发布新宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布新宇宙级固定宽度哈希字段，将发布全息宇宙哈希与多维姿态签名收敛为统一新宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_neoverse_sha256`
  - `release_neoverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_neoverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-107 Release switch 批量测算发布新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布新星宇宙级固定宽度哈希字段，将发布新宇宙哈希与多维姿态签名收敛为统一新星宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_novaverse_sha256`
  - `release_novaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_novaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-108 Release switch 批量测算发布超新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布超新星宇宙级固定宽度哈希字段，将发布新星宇宙哈希与前序发布签名收敛为统一超新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_supernovaverse_sha256`
  - `release_supernovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_supernovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-109 Release switch 批量测算发布超极新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布超极新星宇宙级固定宽度哈希字段，将发布超新星宇宙哈希与前序发布签名收敛为统一超极新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_hypernovaverse_sha256`
  - `release_hypernovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_hypernovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-110 Release switch 批量测算发布极耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布极耀新星宇宙级固定宽度哈希字段，将发布超极新星宇宙哈希与前序发布签名收敛为统一极耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_ultranovaverse_sha256`
  - `release_ultranovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_ultranovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-111 Release switch 批量测算发布终耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布终耀新星宇宙级固定宽度哈希字段，将发布极耀新星宇宙哈希与前序发布签名收敛为统一终耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_omeganovaverse_sha256`
  - `release_omeganovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_omeganovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-112 Release switch 批量测算发布始耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布始耀新星宇宙级固定宽度哈希字段，将发布终耀新星宇宙哈希与前序发布签名收敛为统一始耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_alphanovaverse_sha256`
  - `release_alphanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_alphanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-113 Release switch 批量测算发布次耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布次耀新星宇宙级固定宽度哈希字段，将发布始耀新星宇宙哈希与前序发布签名收敛为统一次耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_betanovaverse_sha256`
  - `release_betanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_betanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-114 Release switch 批量测算发布叁耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布叁耀新星宇宙级固定宽度哈希字段，将发布次耀新星宇宙哈希与前序发布签名收敛为统一叁耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_gammanovaverse_sha256`
  - `release_gammanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_gammanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-115 Release switch 批量测算发布肆耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布肆耀新星宇宙级固定宽度哈希字段，将发布叁耀新星宇宙哈希与前序发布签名收敛为统一肆耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_deltanovaverse_sha256`
  - `release_deltanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_deltanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-116 Release switch 批量测算发布伍耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布伍耀新星宇宙级固定宽度哈希字段，将发布肆耀新星宇宙哈希与前序发布签名收敛为统一伍耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_epsilonnovaverse_sha256`
  - `release_epsilonnovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_epsilonnovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-117 Release switch 批量测算发布陆耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布陆耀新星宇宙级固定宽度哈希字段，将发布伍耀新星宇宙哈希与前序发布签名收敛为统一陆耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_zetanovaverse_sha256`
  - `release_zetanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_zetanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-118 Release switch 批量测算发布柒耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布柒耀新星宇宙级固定宽度哈希字段，将发布陆耀新星宇宙哈希与前序发布签名收敛为统一柒耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_etanovaverse_sha256`
  - `release_etanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_etanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-119 Release switch 批量测算发布捌耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布捌耀新星宇宙级固定宽度哈希字段，将发布柒耀新星宇宙哈希与前序发布签名收敛为统一捌耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_thetanovaverse_sha256`
  - `release_thetanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_thetanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-120 Release switch 批量测算发布玖耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布玖耀新星宇宙级固定宽度哈希字段，将发布捌耀新星宇宙哈希与前序发布签名收敛为统一玖耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_iotanovaverse_sha256`
  - `release_iotanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_iotanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-121 Release switch 批量测算发布拾耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾耀新星宇宙级固定宽度哈希字段，将发布玖耀新星宇宙哈希与前序发布签名收敛为统一拾耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_kappanovaverse_sha256`
  - `release_kappanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_kappanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-122 Release switch 批量测算发布拾壹耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾壹耀新星宇宙级固定宽度哈希字段，将发布拾耀新星宇宙哈希与前序发布签名收敛为统一拾壹耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_lambdanovaverse_sha256`
  - `release_lambdanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_lambdanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-123 Release switch 批量测算发布拾贰耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾贰耀新星宇宙级固定宽度哈希字段，将发布拾壹耀新星宇宙哈希与前序发布签名收敛为统一拾贰耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_munovaverse_sha256`
  - `release_munovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_munovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-124 Release switch 批量测算发布拾叁耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾叁耀新星宇宙级固定宽度哈希字段，将发布拾贰耀新星宇宙哈希与前序发布签名收敛为统一拾叁耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_nunovaverse_sha256`
  - `release_nunovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_nunovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-125 Release switch 批量测算发布拾肆耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾肆耀新星宇宙级固定宽度哈希字段，将发布拾叁耀新星宇宙哈希与前序发布签名收敛为统一拾肆耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_xinovaverse_sha256`
  - `release_xinovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_nunovaverse_sha256/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_xinovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-126 Release switch 批量测算发布拾伍耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾伍耀新星宇宙级固定宽度哈希字段，将发布拾肆耀新星宇宙哈希与前序发布签名收敛为统一拾伍耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_omicronovaverse_sha256`
  - `release_omicronovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_xinovaverse_sha256/release_nunovaverse_sha256/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_omicronovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-127 Release switch 批量测算发布拾陆耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾陆耀新星宇宙级固定宽度哈希字段，将发布拾伍耀新星宇宙哈希与前序发布签名收敛为统一拾陆耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_pinovaverse_sha256`
  - `release_pinovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_omicronovaverse_sha256/release_xinovaverse_sha256/release_nunovaverse_sha256/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_pinovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

鎸変唬鐮佺洰褰曠殑寮€鍙戞竻鍗?
### `src/omni_skill_pipeline/models.py`

- 鏂板 V2 dataclass 涓?enum
- 淇濈暀 `SkillDocument` 鍏煎
- 澧炲姞 graph / review / lifecycle 妯″瀷

### `src/omni_skill_pipeline/service.py`

- 鏀寔 corpus
- 鏀寔 dual-path: V1 / V2 shadow
- 鎺?quality gate / review policy / dual-write

### `src/omni_skill_pipeline/repository.py`

- 杩囨浮鏈熶繚鐣?file artifact
- 鎶借薄 repository 鎺ュ彛
- 鍑嗗 PG repository 鍒囨崲

### `src/omni_skill_pipeline/render.py`

- 鏀寔 `SkillGraph -> SkillDocument -> SKILL.md`
- 鏀寔鏂?publication renderer

### `src/omni_skill_pipeline/adapters/`

- 鍗囩骇涓鸿緭鍑虹粨鏋勫寲 evidence 鎵€闇€瀛楁
- 閫愭ā鎬佽ˉ寮虹粨鏋勪俊鎭?
### `src/omni_skill_pipeline/providers/`

- 鏂板 LLM atom extraction 鏀寔
- 淇濇寔 provider 涓鸿兘鍔涘眰锛屼笉鍚炰笟鍔¤鍒?
### 鏂板鐩綍寤鸿

```text
src/omni_skill_pipeline/
  extraction/
  assembly/
  quality/
  retrieval/
  persistence/
  routing/
```

## 8. 鎺ㄨ崘鏂藉伐鎵规

鎺ㄨ崘鎶婃墍鏈夊伐浣滄媶鎴愪互涓嬩竷鎵癸紝鑰屼笉鏄竴娆℃€уぇ鏀癸細

### 鎵规 A

- `TP-E0-01`
- `TP-E0-02`
- `TP-E0-03`
- `TP-E1-01`
- `TP-E1-02`

### 鎵规 B

- `TP-E1-03`
- `TP-E3-01`
- `TP-E3-02`
- `TP-E3-03`

### 鎵规 C

- `TP-E4-01`
- `TP-E4-02`
- `TP-E4-03`
- `TP-E4-04`
- `TP-E4-05`

### 鎵规 D

- `TP-E5-01`
- `TP-E5-02`
- `TP-E5-03`
- `TP-E6-01`
- `TP-E6-02`

### 鎵规 E

- `TP-E6-03`
- `TP-E6-04`
- `TP-E7-01`
- `TP-E7-02`
- `TP-E7-03`
- `TP-E7-04`

### 鎵规 F

- `TP-E8-01`
- `TP-E8-02`
- `TP-E8-03`
- `TP-E8-04`
- `TP-E9-01`
- `TP-E9-02`
- `TP-E9-03`

### 鎵规 G

- `TP-E10-01`
- `TP-E10-02`
- `TP-E10-03`
- `TP-E11-*`
- `TP-E12-*`
- `TP-E13-*`

## 9. 浜ょ粰 gpt-5.3-codex 鐨勪换鍔℃ā鏉?
鍚庣画姣忔鍙互鐢ㄥ涓嬫牸寮忎笅鍙戜换鍔★細

```text
浣犵幇鍦ㄨ礋璐ｅ疄鐜?Task Package: TP-EX-YY

蹇呰鏂囨。锛?- docs/current/architecture/skill-distillation-v2.md
- docs/current/architecture/skill-distillation-v2-roadmap.md
- docs/current/architecture/skill-distillation-v2-implementation-backlog.md

浠诲姟鐩爣锛?- <澶嶅埗璇ヤ换鍔″寘鐩爣>

鏈鍏佽淇敼鐨勬枃浠讹細
- <鍒楀嚭鏂囦欢>

蹇呴』瀹屾垚锛?- 浠ｇ爜瀹炵幇
- 娴嬭瘯琛ラ綈
- 鏂囨。鍚屾

楠屾敹鏍囧噯锛?- <澶嶅埗璇ヤ换鍔″寘楠屾敹鏍囧噯>

绂佹浜嬮」锛?- 涓嶈鎵╁ぇ鑼冨洿鍒板叾浠?Epic
- 涓嶈鐮村潖鐜版湁 CLI / API 鍏煎
- 涓嶈寮曞叆鏈惤鍦扮殑鏂板熀纭€璁炬柦渚濊禆
```

## 10. 褰撳墠鏈€鍊煎緱鍏堝仛鐨勪簲鍖?
濡傛灉榄斿皧瑕佹渶蹇繘鍏ユ柦宸ユ€侊紝鏈€浼樺厛鐨勬槸锛?
1. `TP-E0-01` 寤虹珛鏍锋湰闆?2. `TP-E1-01` 鏂板 V2 鍩虹妯″瀷
3. `TP-E1-02` 寤虹珛鍏煎杞崲鍣?4. `TP-E3-01` 瀹氫箟 `EvidenceNode`
5. `TP-E5-01` 寤虹珛 `AtomExtractor` 鎺ュ彛

鍋氬畬杩欎簲鍖咃紝V2 鎵嶇湡姝ｆ嫢鏈夐鏋讹紱鍚庨潰鐨?provider銆乺eview銆佸瓨鍌ㄣ€佹绱㈡墠涓嶄細缁х画鎼湪娌欏湴涓娿€?
