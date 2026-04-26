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
