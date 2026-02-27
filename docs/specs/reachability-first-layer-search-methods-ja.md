# 到達手順探索（第一層）の状態爆発対策レポート

更新日: 2026-02-27  
対象: `syncsemphone-next` の `head-assist` / 到達手順探索

## 1. 目的と前提
- 目的: 「到達手順を探索する第一層」の状態爆発を抑えつつ、到達可能性（completeness）を落とさない方式を選ぶ。
- 前提:
  - Perl正本との整合を維持する。
  - 研究用途として、探索失敗を「未到達」と誤判定しないことを最優先にする。
  - 第二層（状態表現の圧縮: packed/restrictor）とは分けて評価する。

## 2. 選定基準（適格性）
本レポートでは、適格性を次で判定した。

1. 一次資料（査読論文・DOI付き）であること  
2. 被引用数が十分高いこと（本調査では目安 700 以上）  
3. 可能な範囲で h5-index などの会場指標も補助的に確認すること

被引用数は Semantic Scholar API（2026-02-27 取得）を使用した。

## 3. 比較対象（上位3方式）
第一層（遷移探索）として比較した方式は以下。

1. SAT系の記号到達探索（BMC / incremental SAT）
2. 動的部分順序削減（DPOR）
3. 許容ヒューリスティック探索（A* / IDA* 系）

## 4. 手法1: SAT系の記号到達探索（BMC / incremental SAT）
### 4.1 中核アイデア
- 遷移系を深さ `k` まで命題化し、SATで可到達性を判定する。
- UNSAT なら「深さ `k` 以内に到達手順なし」を証明できる。
- incremental SAT で `k` を増やし、同じ制約を再利用する。

### 4.2 根拠（一次資料）
- Biere et al. 1999, *Symbolic Model Checking without BDDs*（TACAS）  
  DOI: `10.1007/3-540-49059-0_14`  
  被引用数: `2609`
- Burch et al. 1992, *Symbolic Model Checking: 10^20 States and Beyond*（Information and Computation）  
  DOI: `10.1016/0890-5401(92)90017-A`  
  被引用数: `1114`

### 4.3 長所
- 状態空間を明示列挙しないため、爆発耐性が高い。
- 「見つからない」を証明付きで返せる（深さ境界内）。

### 4.4 リスク
- `DerivationState` と RH/LH規則をSATへ正確に符号化する実装負荷が高い。
- UIで必要な「次の具体操作候補（left/right/rule）」への復元処理が重い。

## 5. 手法2: 動的部分順序削減（DPOR）
### 5.1 中核アイデア
- 独立な操作（交換可能な規則適用）の順序違いを探索しない。
- 代表順序だけを残し、等価な並べ替え分岐を削る。

### 5.2 根拠（一次資料）
- Flanagan & Godefroid 2005, *Dynamic partial-order reduction for model checking software*（POPL）  
  DOI: `10.1145/1040305.1040315`  
  被引用数: `744`

### 5.3 長所
- 到達可能性を維持したまま、順序爆発（permutation explosion）を直接削減できる。
- 既存の「操作列を返す」UI要件と相性がよい。

### 5.4 リスク
- 独立性判定（何が交換可能か）を誤ると不完全化する。
- RH/LH規則に依存する read/write 集合の設計が必須。

## 6. 手法3: 許容ヒューリスティック探索（A* / IDA*）
### 6.1 中核アイデア
- `h(n)` を使って有望状態を優先探索し、到達までの展開数を抑える。
- IDA* はメモリ使用量を抑えつつ、反復で解を探索できる。

### 6.2 根拠（一次資料）
- Hart et al. 1968, *A Formal Basis for the Heuristic Determination of Minimum Cost Paths*  
  DOI: `10.1109/TSSC.1968.300136`  
  被引用数: `12951`
- Korf 1985, *Depth-First Iterative-Deepening: An Optimal Admissible Tree Search*（Artificial Intelligence）  
  DOI: `10.1016/0004-3702(85)90084-0`  
  被引用数: `1867`

### 6.3 長所
- 現行 `head-assist` 実装へ段階移行しやすい。
- 明示的な到達手順（規則列）を自然に返せる。

### 6.4 リスク
- ヒューリスティックが弱いと状態爆発は残る。
- 単独では順序爆発（同値な手順違い）を根本的に削れない。

## 7. 総合比較（今回用途）
評価軸:
- 完全性（到達性の見落とし回避）
- 状態爆発抑制力
- 現行実装への接続容易性
- UIに返す操作列の説明可能性

改訂結論（断定の見直し）:
- 「第一層の主軸を DPOR-aware IDA* 単独で最適と断定」は現時点では強すぎる。
- 主軸は次の **二系統分離** に改訂する。
  1. 到達性判定コア: **DPOR-aware 深さ制限完全探索**（見落とし禁止）
  2. 提案エンジン: **IDA* / best-first**（高速な候補提示。未到達証明には使わない）

改訂理由:
1. DPORは有効だが、効果と安全性は独立性定義に強く依存する。  
2. 到達性判定に `dominance` を混ぜると不完全化の危険が高い。  
3. IDA* は許容ヒューリスティックが強く定義できる場合に有効で、一般には利点が限定される。  
4. 「見つからない」を「存在しない」と誤判定しないためには、判定系と提案系の責務分離が必要。

## 8. 採用方式（改訂）
採用: **DPOR-aware 完全探索（判定コア） + ヒューリスティック探索（提案）**

### 8.1 判定コア（completeness優先）
1. 深さ制限付き完全探索（DLS/IDDFS系）を基礎にする。  
2. 重複排除は **等価状態の transposition のみ**を使う。  
3. DPOR の persistent/sleep を保守的独立性で適用する。  
4. **dominance pruning は判定コアでは使わない**。  
5. 返答は三値: `到達あり / 未到達（探索上限内で証明） / 予算切れで不明`。

### 8.2 提案エンジン（UX優先）
1. IDA* / best-first を利用して「次の一手」を高速提示する。  
2. IDA* を使う場合は `h` の許容性（過大評価しない）を満たすときだけ判定補助に使用する。  
3. `h` の許容性が保証できない場合、提案用途に限定し、未到達判定には使わない。

### 8.3 完全性条件（改訂）
- 独立性判定が保守的であること（誤って独立と判定しない）。
- 判定コアでは `dominance` を排除し、到達集合包含が証明できる削減のみ使うこと。
- 予算切れを「未到達」と表示しないこと。

### 8.4 本リポジトリへの接続点
- 判定コア入口: `apps/api/app/api/v1/derivation.py` (`/head-assist` 内の reachability 判定経路)
- 候補列挙: `packages/domain/src/domain/derivation/candidates.py`
- 規則実行: `packages/domain/src/domain/derivation/execute.py`
- 到達判定: `_count_uninterpretable_like_perl`

## 9. 実装上の注意（第一層のみ）
1. `independence(a,b)` を RH/LH規則単位で定義する。  
   - 例: 共有ノードを読み書きする操作同士は独立にしない。  
2. 判定コアでは、削減規則ごとに「到達集合を落とさない根拠」を明記する。  
3. `到達手順なし` を返す条件は、深さ上限内での探索完了時に限定する。  
4. packed は第二層として維持し、第一層（DPOR-aware 完全探索）と直交に併用する。

## 10. 結論（改訂）
- 状態爆発の主戦場は第一層（到達手順探索）であり、`structural/packed` 切替だけでは不十分。
- 第一層の主軸は、**DPOR-aware 完全探索（判定）**に置く。
- **IDA* は提案側の加速器**として扱い、到達不能判定の主証拠にはしない。
- この分離により、「到達可能なのに到達不能」と誤判定するリスクを最小化しつつ、UIの操作支援速度を維持できる。

## 参考文献（一次資料）
- Hart, Nilsson, Raphael (1968).  
  *A Formal Basis for the Heuristic Determination of Minimum Cost Paths*.  
  DOI: https://doi.org/10.1109/TSSC.1968.300136
- Korf (1985).  
  *Depth-First Iterative-Deepening: An Optimal Admissible Tree Search*.  
  DOI: https://doi.org/10.1016/0004-3702(85)90084-0
- Burch et al. (1992).  
  *Symbolic Model Checking: 10^20 States and Beyond*.  
  DOI: https://doi.org/10.1016/0890-5401(92)90017-A
- Biere et al. (1999).  
  *Symbolic Model Checking without BDDs*.  
  DOI: https://doi.org/10.1007/3-540-49059-0_14
- Flanagan & Godefroid (2005).  
  *Dynamic partial-order reduction for model checking software*.  
  DOI: https://doi.org/10.1145/1040305.1040315

## 参考指標（取得元）
- Semantic Scholar Graph API（被引用数; 2026-02-27 取得）  
  https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/TSSC.1968.300136?fields=title,year,citationCount,venue,url,externalIds  
  https://api.semanticscholar.org/graph/v1/paper/DOI:10.1016/0004-3702(85)90084-0?fields=title,year,citationCount,venue,url,externalIds  
  https://api.semanticscholar.org/graph/v1/paper/DOI:10.1016/0890-5401(92)90017-A?fields=title,year,citationCount,venue,url,externalIds  
  https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/3-540-49059-0_14?fields=title,year,citationCount,venue,url,externalIds  
  https://api.semanticscholar.org/graph/v1/paper/DOI:10.1145/1040305.1040315?fields=title,year,citationCount,venue,url,externalIds
- Google Scholar Metrics（h5-index の補助確認; 2025版ページを 2026-02-27 参照）  
  Software Systems: https://scholar.google.com/citations?view_op=top_venues&hl=en&vq=eng_softwaresystems  
  Artificial Intelligence: https://scholar.google.com/citations?view_op=top_venues&hl=en&vq=eng_artificialintelligence
