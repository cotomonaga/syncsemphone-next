# HPSGの状態爆発抑制手法を LH/RHマージ＋素性照合へ適用する検討レポート

更新日: 2026-02-27  
対象: `syncsemphone-next` の `LH/RHマージ＋素性照合` エンジン

## 1. 目的と前提
- 目的: `Grammar適用` 段階で起きる状態爆発を、研究用途の厳密性を落とさずに抑える。
- 条件:
  - Perl正本との整合を維持する（到達可能性を落とさない）。
  - 「簡易版」は採用しない。
  - 実装対象は現行Pythonコード（`DerivationState`, `list_merge_candidates`, `execute_*`）に接続可能であること。

## 2. 比較対象（上位3手法）
以下を、HPSG系の一次資料で実績がある順に比較した。

1. 局所曖昧性パッキング（subsumption）＋選択的アンパック  
2. Supertagging＋CFG-filtering（coarse-to-fine）  
3. Unification filtering / quick-check（＋必要ならchunk併用）

## 3. 手法1: 局所曖昧性パッキング＋選択的アンパック
### 3.1 根拠
- 局所曖昧性パッキングなしでは探索空間が組合せ爆発することを明示（Crysmann 2007）。
- subsumptionベースのパッキング（Oepen & Carroll系）で高い圧縮効果。
- selective unpacking で、`n-best` をほぼ線形コストで展開可能（Zhang et al. 2007）。

### 3.2 代表的な実績
- German HPSG で約2倍高速化（Crysmann 2007）。
- selective unpacking は `n` 増加に対し処理時間がほぼ線形（Zhang et al. 2007）。

### 3.3 長所
- 厳密性を保ちやすい（本質は「共有表現」であり、探索空間削減のための破壊的近似ではない）。
- 既存の「意味比較」「n-best比較」に自然接続。
- `history` や `base` の構造を保持したまま、共有ノード化できる。

### 3.4 リスク
- restrictor 設計を誤ると、過剰一般化でアンパック失敗や再計算増が起きる。
- HPSG文献でも、非局所依存（例: SLASH相当）に対する restrictor 設計は慎重さが必要（Crysmann 2007）。

## 4. 手法2: Supertagging＋CFG-filtering
### 4.1 根拠
- HPSG近似CFGを先に使って maybe-parsable な列だけ通し、重い処理を後段へ回す方式。
- Torisawa et al. (2000), Matsuzaki et al. (IJCAI 2007), 近年の再検証（Zamaraeva & Gómez-Rodríguez 2024）で有効性が再確認。

### 4.2 代表的な実績
- IJCAI 2007: 同一文法条件で約6倍高速化を報告。
- EMNLP 2024: no-tagging比で約3倍高速化を報告。

### 4.3 長所
- 入口で候補を大きく減らせるため、平均時間に効く。
- 文単位UI（Step1）との相性が良い。

### 4.4 リスク
- 主に「語彙割当て段階」の削減手法であり、`Step2` の派生爆発そのものには直接効きにくい。
- coarseフィルタ設計が強すぎると、研究上必要な枝を捨てる危険がある。

## 5. 手法3: Unification filtering / quick-check
### 5.1 根拠
- 深い unification を行う前に、軽量判定で不成立候補を落とす。
- Ninomiya et al. (IWPT 2005) で quick-check の寄与が大きいことを報告。

### 5.2 長所
- 既存エンジンに比較的挿入しやすい。
- `execute_*` 前の早期失敗判定として実装可能。

### 5.3 リスク
- 状態数自体は減らしにくく、「1状態あたりの計算を軽くする」性質が強い。
- 状態爆発の主因（同型・近同型の大量分岐）への直接効果は手法1より弱い。

## 6. 総合比較（今回の用途）
評価軸は 5 つ:
- 厳密性維持
- 爆発抑制効果（状態数）
- 既存コードへの適用容易性
- 意味比較（同値群）との親和性
- 長文での安定性

結論:
- 最適解は **手法1（局所曖昧性パッキング＋選択的アンパック）**。
- 理由:
  - 状態数そのものを減らせる。
  - 解析の完全性を維持しやすい。
  - `n-best` / 意味グルーピング機能と直接つながる。
- 手法2と3は補助として有効だが、主軸にするのは不適切。

## 7. 採用手法（今回実装に使う1案）
採用: **Subsumptionベース局所曖昧性パッキング + 選択的アンパック（完全版）**

### 7.1 方式の要点
1. `DerivationState` をそのまま列挙せず、パックノードへ集約する。  
2. 集約条件は「restrictorで正規化した署名」による subsumption/equivalence。  
3. 各パックノードは複数の導出履歴を保持し、展開は必要時（n-best/比較時）のみ行う。  
4. 先に forest（共有DAG）を構築し、後で selective unpacking する。  

### 7.2 現行コードへの接続点
- 候補生成: `packages/domain/src/domain/derivation/candidates.py`
- 状態遷移: `packages/domain/src/domain/derivation/execute.py`
- grammatical判定: `apps/api/app/api/v1/derivation.py`（`_count_uninterpretable_like_perl`）
- 状態型: `packages/domain/src/domain/common/types.py`

### 7.3 パック署名（restrictor）設計案
保持する情報（落としてはいけない）:
- 各ノードの `ca`
- 未解釈素性の核（`sy/se/pr/sl` のうち combinability に効く番号・方向・役割）
- 親子構造の最低限（`wo` の骨格）

落とす情報（共有化してよい）:
- `history` 全文
- 語形表示専用情報
- 既に解消済みで combinability に寄与しない詳細値

注意:
- 文献上、非局所依存特徴の過剰制限は逆効果があり得るため、restrictor は段階導入する。

### 7.4 selective unpacking
- 既定は `n-best`（例: 10 または 50）だけ展開。
- 研究用途では「意味同値群」を先にまとめ、群代表のみ展開可能にする。
- UIでは「全展開」ではなく「段階展開」を標準にする。

### 7.5 計算量試算（実測ベース）
ここでは、現行Python実装の遷移生成 (`list_merge_candidates` + `execute_*`) を使い、次を比較した。
- `raw`: 履歴込み状態署名（現行探索に近い）
- `packed`: restrictor署名（`ca + 未解釈素性核 + wo骨格`）

前提:
- 文法: `imi03`
- 比較対象 `.num`:
  - `imi03/set-numeration/04.num`（ジョンがメアリを追いかけた）
  - `imi03/set-numeration/1606324760.num`（ジョンがメアリをスケートボードで追いかけた）
- 2段目までは全列挙、3段目は時間上限20秒で比較

#### 7.5.1 2段目までの全列挙（状態数）
| ケース | depth=1 raw | depth=1 packed | depth=2 raw | depth=2 packed | depth=2削減率 |
|---|---:|---:|---:|---:|---:|
| `04.num` | 61 | 57 | 2511 | 1371 | **45.40%** |
| `1606324760.num` | 114 | 106 | 9817 | 4835 | **50.75%** |

#### 7.5.2 depth=3（時間上限20秒）
| ケース | raw | packed | 備考 |
|---|---|---|---|
| `04.num` | 20秒で停止（`seen=35970`, `expanded=1355`, timeout） | 16.818秒で完走（`seen=19056`, `expanded=1429`） | rawは時間内に完走不可 |
| `1606324760.num` | 20秒で停止（`seen=43335`, `expanded=652`, timeout） | 20秒で停止（`seen=23658`, `expanded=644`, timeout） | 同一時間で `seen` は **45.40%** 減 |

#### 7.5.3 試算の読み方（Xが求まらない場合）
- `04.num` の depth=3 では、**X（rawの完走コスト）は状態爆発で求められなかった**。  
  ただし同一条件で本方式（packed）は **Y=19056状態** に抑えて完走した。
- `1606324760.num` は両方式とも20秒上限で完走しない。  
  それでも同一予算下で packed は `seen` を約45%削減できた。

この結果から、探索深さを1段増やすごとに差が拡大する条件では、パッキング導入の効果は「定数倍高速化」より「探索可能深さの延伸」として現れる。

### 7.6 API実装反映（比較可能な運用）
`/v1/derivation/head-assist` に `search_signature_mode` を追加し、次の2方式を切替可能にした。

- `structural`: `history` を除いた構造署名で探索
- `packed`（既定）: restrictor署名 + Pareto優越管理で探索

これにより、同一入力・同一予算で `structural` と `packed` を直接比較できる。  
回帰テストでは次を固定した。

1. `search_signature_mode` の受理 (`packed` / `structural`)
2. 不正値の 400 応答
3. 署名の期待挙動（history差分の無視）
4. level2 で `packed` が `structural` より状態数を削減すること

### 7.7 現時点の評価（到達性）
- `packed` は状態削減には有効だが、到達手順探索の解決には不十分。
- 具体的には `ジョンがメアリをスケートボードで追いかけた` で、`depth=3 / 20秒` 条件では `packed` でも到達性判定を完了できない。
- したがって、第二層（状態圧縮）は必要条件だが十分条件ではない。

## 8. 実装計画（高精度版）
1. `PackedState` ドメイン導入（DAGノード、支配辺、候補遷移）  
2. restrictor v1 実装（保守的）  
3. subsumptionパッキング（等価/包含）  
4. selective unpacking（`n-best`, 意味同値群）  
5. 回帰テスト（Perl整合 + 到達可能性 + 性能）  

## 9. テスト方針（厳密性担保）
- 正しさ:
  - パッキングあり/なしで到達可能 grammatical 集合が一致すること。
  - 手動導出列（既存手順書）を再現できること。
- 互換:
  - Perl正本差分テストで、既存goldenを壊さないこと。
- 性能:
  - 長文ケースで `max frontier size`, `expanded states`, `time to first grammatical` を記録。

## 10. 今回の結論
- 上位3手法の比較の結果、今回の実装主軸は  
  **「局所曖昧性パッキング（subsumption）＋選択的アンパック」** を採用する。
- これは簡易版ではなく、HPSGの実運用系で実績がある完全系に相当する。
- `LH/RHマージ＋素性照合` には、`DerivationState` を共有DAGへ持ち上げる形で適用する。
- ただし現時点の実測では、第二層単独では到達問題を解決できない（第一層の改善が必須）。

## 参考文献（一次資料）
- Crysmann, B. 2007. *Local ambiguity packing and discontinuity in German*.  
  https://aclanthology.org/W07-1219.pdf
- Zhang, Y., Oepen, S., Carroll, J. 2007. *Efficiency in Unification-Based N-Best Parsing*.  
  https://aclanthology.org/W07-2207.pdf
- Matsuzaki, T., Miyao, Y., Tsujii, J. 2007. *Efficient HPSG Parsing with Supertagging and CFG-Filtering*.  
  https://ijcai.org/Proceedings/07/Papers/270.pdf
- Torisawa, K., Nishida, K., Miyao, Y., Tsujii, J. 2000. *An HPSG parser with CFG filtering*.  
  https://doi.org/10.1017/S1351324900002412
- Ninomiya, T., Tsuruoka, Y., Miyao, Y., Tsujii, J. 2005. *Efficacy of Beam Thresholding, Unification Filtering and Hybrid Parsing in Probabilistic HPSG Parsing*.  
  https://aclanthology.org/W05-1511.pdf
- Miyao, Y., Tsujii, J. 2008. *Feature Forest Models for Probabilistic HPSG Parsing*.  
  https://aclanthology.org/J08-1002.pdf
- Zamaraeva, O., Gómez-Rodríguez, C. 2024. *Revisiting Supertagging for Faster HPSG Parsing*.  
  https://aclanthology.org/2024.emnlp-main.635.pdf
