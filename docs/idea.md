可以。这个任务我建议不要把 PoseBusters 简单改造成“让 Agent 跑一次 docking，然后看 RMSD”的 benchmark，而是做成一个 **PyMOL-based Protein–Ligand Docking Computer-Use Benchmark**，把能力拆开测：

> **PyMOL 操作能力 → 界面识别 → 相互作用理解 → docking pose 诊断 → 多 pose 排序 → 端到端 docking**

这样最后你不仅能得到“成功率 37%”，还能知道 Agent 到底失败在 GUI、空间感知、化学判断还是 docking workflow。

PoseBusters 很适合作为底座。论文最终使用的是 **308 个蛋白–配体复合物**；这些结构均为 2021 年以后公开的高质量复合物，因此不属于大量 docking 方法使用的 PDBbind v2020 数据。最初 Zenodo 版本曾包含 428 个案例，但作者在同行评审期间发现部分存在 crystal-contact 问题，最终论文报告的是筛选后的 308 个。([Zenodo][1])

---

# 一、我建议最终 benchmark 长这样

名字先暂定：

**PyMolDock-Bench**

或者更像 benchmark 论文：

**MolecularGUIBench-Dock**

核心任务分成 5 个层级：

| Level | Task                             | 测什么                      |
| ----- | -------------------------------- | ------------------------ |
| L0    | PyMOL Manipulation               | 会不会正确操作 PyMOL            |
| L1    | Binding Interface Identification | 能不能找到蛋白–配体界面             |
| L2    | Interaction Understanding        | 能不能识别氢键、疏水、冲突等           |
| L3    | Pose Diagnosis & Ranking         | 能不能判断 pose 好不好           |
| L4    | End-to-End Redocking             | 能不能真正完成 docking workflow |

其中真正最有研究价值的是 **L2–L4**。

---

# 二、非常重要：不要把“dock 正确”定义成一个指标

PoseBusters 的核心贡献恰好就是指出：

$$
\text{RMSD} \le 2\AA
$$

本身不足以说明 docking pose 合理。

它还检查：

* 化学合法性；
* 分子式；
* 键连接；
* 四面体手性；
* 双键立体化学；
* bond length；
* bond angle；
* aromatic ring planarity；
* internal steric clash；
* ligand internal energy；
* protein–ligand clash；
* cofactor–ligand clash；
* ligand 与 protein 的体积重叠。

官方将通过全部相关检查的结构称为 **PB-valid**。([Royal Society of Chemistry Publications][2])

所以我建议定义：

$$
\boxed{
\text{DockingSuccess}
=
(\mathrm{RMSD}_{lig}\le2\AA)
\land
\mathrm{PBValid}
}
$$

这也与现在 PoseBench 使用的重要指标一致；PoseBench 另外还加入了 centroid RMSD 和蛋白–配体相互作用指纹指标。([Nature][3])

但对于 Agent，你还应该**把两件事情分别问**：

```text
Q1. Is this pose physically plausible?

Q2. Is this pose likely to correspond to the correct binding mode?
```

原因很重要：

> 一个 RMSD=5 Å 的错误 pose 完全有可能看起来化学上非常合理。

如果不给 Agent native structure，它原则上不可能永远通过肉眼知道这个结构是不是实验 binding mode。

所以：

**Physical plausibility ≠ native pose recovery**

这两个能力一定要拆开。

---

# 三、数据集：不要拆 PoseBusters 308 做 development

这个地方我反而建议借用原论文设计。

### Development set

使用：

**Astex Diverse Set：85 complexes**

### Test set

使用：

**PoseBusters Benchmark：308 complexes**

原始 PoseBusters 工作本来就同时包含 Astex Diverse 和 PoseBusters Benchmark，非常适合这么做。([Zenodo][1])

这样你的 benchmark 就变成：

```text
Development
    Astex 85
        ↓
prompt engineering
agent debugging
tool debugging
threshold selection

────────────────────────

Test
    PoseBusters 308
        ↓
never tune on these
```

比：

```text
PoseBusters 40 dev
PoseBusters 268 test
```

科学上干净很多。

---

# 四、每个 PoseBusters case 应该保存什么

PoseBusters 原始数据已经非常接近你想要的格式。

原 benchmark 中 protein 会保留相关 cofactors，目标 ligand 则作为 SDF 单独保存；原工作在预处理过程中使用 PyMOL 移除了 solvent 和目标 ligand。([Polaris Hub][4])

我建议整理成：

```text
PyMolDockBench/
│
├── dev/
│   └── astex/
│
├── test/
│   └── posebusters/
│
├── episodes/
│
└── private_ground_truth/
```

每个 target：

```text
PB_000001/
│
├── public/
│   ├── receptor.pdb
│   ├── ligand_start.sdf
│   ├── episode.json
│   └── task.txt
│
└── private/
    ├── ligand_native.sdf
    ├── native_complex.pdb
    ├── interface_gt.json
    ├── interactions_gt.json
    ├── posebusters_gt.json
    └── decoys/
```

## public 和 private 必须物理隔离

Agent **绝对不能访问**：

```text
ligand_native.sdf
native_complex.pdb
ground_truth.json
```

否则可以直接：

```python
align predicted_ligand, native_ligand
```

benchmark 就废了。

---

# 五、还应该把 PDB ID 匿名化

非常重要。

不要把：

```text
7MYU_ZR7
```

暴露给 Agent。

改成：

```text
PB_0187
```

同时删除：

```text
HEADER
TITLE
COMPND
DBREF
```

等可以直接暴露 PDB 身份的信息。

并且 evaluation 环境：

```text
network = disabled
clipboard = empty
browser = disabled
filesystem = episode-only
```

否则具有 web/search capability 的 Agent 可以：

```text
PDB ID → RCSB → crystal ligand pose
```

然后 benchmark 变成信息检索能力测试。

---

# 六、L0：PyMOL 操作能力

这个任务只测 GUI/tool-use，不测生物化学。

例如给 Agent：

```text
receptor.pdb
ligand.sdf
```

初始 PyMOL 为空。

## Prompt

> Load the receptor and ligand into PyMOL.
> Display the protein as cartoon, the ligand as sticks, center the camera on the ligand, display protein residues within 5 Å of the ligand as sticks, and save the final session.

要求最终存在：

```text
object:
    receptor
    ligand

selection:
    agent_pocket
```

并保存：

```text
final.pse
```

## 自动评价

Evaluator 启动 headless PyMOL：

```python
cmd.load("final.pse")
```

然后检查：

```text
receptor exists
ligand exists
agent_pocket exists
ligand atom count correct
protein coordinates unchanged
```

注意我不建议把：

```text
cartoon color是不是绿色
sticks是不是黄色
```

当主要 metric。

这些只是 cosmetic。

真正有意义的是：

```text
对象是否正确加载
selection 是否正确
目标是否正确定位
文件是否正确保存
```

---

# 七、这里必须做两个 PyMOL track

这是整个 benchmark 很关键的设计。

## Track A：GUI-only

Agent 只能：

```text
mouse
keyboard
menus
buttons
visual inspection
```

禁止：

```text
PyMOL console
Python API
select ... within ...
```

这测的是：

> Computer Vision + GUI control

---

## Track B：PyMOL power-user

允许输入：

```python
select pocket, byres (polymer within 4.0 of ligand)
show sticks, pocket
zoom ligand, 8
```

这测的是：

> Agent 是否会使用科学软件

这两个不能混在一起。

因为如果你让 Agent 输入：

```python
select interface, byres (protein within 4 of ligand)
```

那么 interface identification 基本已经不是视觉任务了。

因此 leaderboard 应该分别报告：

```text
GUI-only
PyMOL-command-enabled
```

---

# 八、L1：Binding Interface Identification

这个正好对应你最开始说的：

> 能否正确识别 docking interface。

---

## 1. Ground truth 定义

我建议最简单、最稳的版本：

对于 native crystal ligand \(L\)，

$$
I_{GT}^{4\AA}
=
\left\{
r_i :
\min_{a\in r_i,\;b\in L}
\|x_a-x_b\|\le4.0\AA
\right\}
$$

只计算 heavy atoms。

也就是：

> 任意 residue heavy atom 和 ligand heavy atom 距离 ≤4 Å，则认为该 residue 属于 interface。

---

## 同时保存三个 cutoff

建议后台计算：

```text
3.5 Å
4.0 Å
5.0 Å
```

primary metric：

```text
4.0 Å
```

3.5 和 5.0 做 sensitivity analysis。

---

# 九、Interface task 不应该直接显示 native ligand

这里又分两种任务。

## Task L1-A：Observed interface

当前 PyMOL 中显示：

```text
protein
candidate docked ligand
```

Agent 要回答：

> 当前这个 pose 与哪些 residues 接触？

Ground truth 是：

$$
I_{\text{candidate}}
$$

也就是**当前 pose 自己**产生的 interface。

这测：

> Agent 能不能正确理解屏幕里发生了什么。

---

## Task L1-B：Native interface recovery

不是要求 Agent“猜 native residues”。

而是：

Agent 给出当前 interface 后，

Evaluator 自动比较：

$$
I_{\text{candidate}}
$$

和隐藏的：

$$
I_{\text{native}}.
$$

计算：

$$
Precision =
\frac{|I_c\cap I_n|}{|I_c|}
$$

$$
Recall =
\frac{|I_c\cap I_n|}{|I_n|}
$$

$$
F1 =
\frac{2PR}{P+R}
$$

以及：

$$
Jaccard =
\frac{|I_c\cap I_n|}
{|I_c\cup I_n|}.
$$

这里非常漂亮：

Agent 并不需要知道 native。

你可以同时得到：

```text
Agent interface perception accuracy
Candidate-native interface recovery
```

---

# 十、Agent 的 interface 输出格式一定要结构化

不要只让它自然语言说：

> I think residues around Ser123 and Asp125 are interacting...

要求它创建 PyMOL selection：

```text
agent_interface
```

并输出：

```json
{
  "interface_residues": [
    ["A", 123],
    ["A", 124],
    ["A", 167]
  ]
}
```

自动 evaluator 就非常容易。

---

# 十一、L2：Protein–Ligand Interaction Understanding

这是比 interface identification 更强的任务。

让 Agent 判断：

```text
hydrogen bond
salt bridge
hydrophobic contact
π-π stacking
cation-π
metal coordination
steric clash
```

例如输出：

```json
{
  "interactions": [
    {
      "type": "hydrogen_bond",
      "residue": "ASP189",
      "chain": "A"
    },
    {
      "type": "hydrophobic",
      "residue": "VAL213",
      "chain": "A"
    }
  ]
}
```

---

# 十二、Interaction ground truth

这里我推荐不要自己手写一套规则。

直接用：

**ProLIF**

生成 protein–ligand interaction fingerprint。

PoseBench 现在也明确使用蛋白–配体相互作用指纹相关评价，并引入 PLIF-WM 来评价 predicted interaction pattern。([Nature][3])

可以保存：

```text
interaction type
protein residue
protein atom
ligand atom
distance
```

Agent scoring 不建议要求 exact atom 全对。

主要按照：

```text
interaction type + residue
```

评分。

例如：

```text
ASP189 hydrogen bond
```

对了就算对。

---

# 十三、Interaction metric

定义：

$$
S_{GT}
=
\{
(type,residue)
\}
$$

$$
S_{agent}
=
\{
(type,residue)
\}
$$

然后：

$$
F1_{interaction}
$$

以及每种 interaction 单独：

```text
H-bond F1
hydrophobic F1
salt-bridge F1
π-stacking F1
metal-coordination F1
```

这个非常适合分析 Agent 的科学 reasoning。

---

# 十四、真正重要的 L3：Pose Diagnosis

这才是你说的：

> PyMOL 可视化后 Agent 能不能判断 docking 是否正确？

我建议**绝对不要做单一 yes/no**。

要求它输出：

```json
{
  "physical_plausibility": "valid",
  "native_likeness": "likely_correct",
  "confidence": 0.83,
  "failure_modes": [],
  "reasoning": [...]
}
```

其中：

### physical_plausibility

```text
VALID
INVALID
UNCERTAIN
```

### native_likeness

```text
LIKELY_CORRECT
LIKELY_INCORRECT
UNCERTAIN
```

### failure_modes

```text
steric_clash
wrong_pocket
wrong_orientation
poor_pocket_complementarity
ligand_internal_geometry
lost_key_interactions
cofactor_conflict
excessive_solvent_exposure
```

---

# 十五、为什么一定要允许 UNCERTAIN

假设：

```text
predicted pose:
RMSD = 4.5 Å
PB-valid = True
reasonable H-bonds
no clash
well buried
```

Agent 没看过 crystal structure。

实际上它没有充分信息知道：

```text
这是 experimental binding mode 的替代 pose
```

还是：

```text
docking 失败。
```

因此强迫：

```text
correct / incorrect
```

会把 benchmark 做成 epistemically impossible 的任务。

应该允许：

```text
UNCERTAIN
```

然后评价 calibration。

---

# 十六、Pose Diagnosis 的 decoy 从哪里来

这里不要只做人为 random ligand rotation。

最好的方法是：

## 第一来源：真实 docking predictions

PoseBench 已经支持并 benchmark 多种 fixed/flexible docking/co-folding 方法，包括：

```text
AutoDock Vina
DiffDock
FABind
DynamicBind
NeuralPLexer
FlowDock
RoseTTAFold-All-Atom
Chai-1
Boltz
AlphaFold 3
...
```

并提供 PoseBusters 数据的统一处理流程。([GitHub][5])

因此：

```text
PoseBusters target
        ↓
多种 docking method predictions
        ↓
不同质量的真实 decoys
```

比你自己：

```python
rotate ligand 90 degrees
```

自然得多。

---

# 十七、建议构造 5 类 pose

我会实际构造下面五个 bucket。

## P0：Native-like valid

$$
RMSD \le 2Å
$$

且：

```text
PB-valid = True
```

---

## P1：Native-like but physically invalid

$$
RMSD \le 2Å
$$

但：

```text
PB-valid = False
```

比如：

```text
protein clash
internal clash
bad ring geometry
```

这个类别非常有意思。

因为 Agent 不能只学：

> “位置看起来差不多 = docking 成功”。

---

## P2：Wrong orientation, correct pocket

要求例如：

$$
RMSD>2Å
$$

同时：

$$
CentroidRMSD < 2.5Å
$$

以及：

$$
Jaccard(I_{pred},I_{native}) > 0.4.
$$

也就是：

```text
ligand 在正确 pocket
但 orientation/conformation 错了
```

这是最重要的 hard negative。

---

# 十八、P3：Wrong sub-pocket

例如：

```text
ligand 仍然接触 protein
但偏离 native binding mode
```

可以定义：

$$
2.5Å < d_{\text{centroid}} < 6Å.
$$

并且：

```text
≥3 protein residues contacting ligand
```

这避免只是 ligand 飘在空气中。

---

# 十九、P4：Gross failure

例如：

$$
d_{\text{centroid}}>6Å
$$

或者：

```text
no meaningful protein contact
massive steric clash
wrong cavity
```

这是 easy negative。

---

# 二十、每个蛋白准备多少个 diagnosis pose

理想：

```text
P0 × 1
P1 × 1
P2 × 1
P3 × 1
P4 × 1
```

因此：

$$
308\times5=1540
$$

个 pose-diagnosis episode。

实际可能某些 target 没有 P1 或 P2。

没关系。

目标可以做成大约：

```text
1000–1500 episodes
```

并按类别平衡采样。

---

# 二十一、如果真实 docking results 缺某个 bucket

才用 controlled perturbation。

优先顺序：

```text
real Vina/DiffDock/... pose
         ↓
real alternative docked pose
         ↓
controlled synthetic decoy
```

不要反过来。

Synthetic decoy 可以生成：

```text
translation:
1 Å
2 Å
4 Å
8 Å

rotation:
30°
60°
90°
180°
```

但只作为：

> diagnostic stress test

而不是 main benchmark。

---

# 二十二、非常推荐再加一个 Pose Ranking Task

相比：

> “这个 pose 对不对？”

实际 docking 更像：

> “这 10 个 poses 哪一个最好？”

给 PyMOL：

```text
pose_1
pose_2
pose_3
pose_4
pose_5
```

全部隐藏：

```text
native ligand
RMSD
docking score
method source
```

Agent 可以：

```text
toggle poses
rotate
zoom
inspect contacts
measure distances
```

最后：

```json
{
  "best_pose": "pose_3",
  "ranking": [
    "pose_3",
    "pose_1",
    "pose_5",
    "pose_2",
    "pose_4"
  ]
}
```

---

# 二十三、Pose ranking metric

Primary：

$$
Top1Success =
\mathbb{1}[
RMSD_{\text{selected}}\le2Å
\land PBValid
]
$$

另外算：

```text
Best-RMSD rank
MRR
NDCG
Top-2 success
Top-3 success
```

还可以比较：

```text
Agent selected Top1
vs
Vina score Top1
vs
Oracle Top1
```

这样会很有意思。

---

# 二十四、L4：端到端 Docking

这是整个 benchmark 的最终任务。

但这里需要强调一点：

**PyMOL 本身主要是结构可视化/分析环境，不应该让 docking engine 随 Agent 自由选择。**

否则：

```text
Agent A 用 Vina
Agent B 用 DiffDock
Agent C 用另一个 docking server
```

最后测到的主要是 docking engine 差异。

所以 benchmark 必须固定 backend。

我建议：

# AutoDock Vina

作为统一 docking engine。

Agent 测的是：

```text
能否正确准备输入
能否正确设 binding box
能否执行 docking
能否载入 poses
能否分析
能否选正确 pose
```

而不是：

> 哪个 docking model 更强。

---

# 二十五、我推荐做两个 End-to-End track

## E2E-KnownPocket

这是主 benchmark。

给 Agent：

```text
receptor
ligand
box center
box dimensions
```

例如：

```json
{
  "center": [21.3, -7.8, 34.1],
  "size": [22.0, 24.0, 20.0]
}
```

Agent 负责：

```text
load receptor
load ligand
prepare docking
set box
run Vina
load poses
inspect poses
select final pose
save result
```

这样测：

> docking execution ability

而不是 pocket prediction。

---

# 二十六、Pocket box 怎么生成

Ground-truth native ligand 只在 evaluator 里使用。

计算 ligand heavy-atom bounding box：

$$
x_{\min},x_{\max},...
$$

center：

$$
c =
\frac{x_{\min}+x_{\max}}{2}.
$$

每个方向：

$$
s_i =
\mathrm{clip}
(
x_i^{max}-x_i^{min}+12,
18,
30
)
$$

也就是 ligand 周围大约留 6 Å margin。

这些数字是**你 benchmark 的标准化设计**，不是 PoseBusters 官方定义。

所有 Agent 都拿同一个 box。

---

# 二十七、E2E-BlindPocket

作为 harder track。

只给：

```text
protein
ligand
```

Agent 自己：

```text
inspect protein surface
identify cavity
define docking box
dock
```

但这个我不建议拿来做 primary score。

因为：

> pocket detection 本身就是独立的复杂问题。

容易把 docking workflow evaluation 搞混。

---

# 二十八、Vina 配置一定固定

例如固定：

```text
seed
exhaustiveness
num_modes
energy_range
CPU count
```

建议：

```text
num_modes = 10
```

或者：

```text
20
```

这样 Agent 可以 inspection + ranking。

不要让 Agent 修改：

```text
exhaustiveness
seed
scoring function
```

否则不同 Agent 使用的计算预算不同。

---

# 二十九、PyMOL + Vina 最好做一个标准 Plugin/Wrapper

我甚至不建议要求 Agent 自己打开 shell。

可以做一个 PyMOL plugin：

```text
Docking
├── Prepare Receptor
├── Prepare Ligand
├── Define Search Box
├── Run Vina
├── Load Poses
└── Export Selected Pose
```

后台统一调用：

```text
vina
```

Agent 还是通过 PyMOL GUI 操作。

这样：

```text
environment variation ↓
reproducibility ↑
```

对于 Computer Use benchmark 特别重要。

---

# 三十、但要保留“真实操作难度”

不要做成：

```text
[RUN EVERYTHING]
```

一个按钮。

应该让 Agent 至少完成：

```text
选择 receptor
选择 ligand
输入 center XYZ
输入 size XYZ
启动 docking
等待结果出现
加载结果
切换 pose
选择结果
导出
```

这样才是 Computer Use。

---

# 三十一、推荐 PyMOL 初始状态

为了避免视觉布局影响结果，所有 episode 必须统一。

例如：

```text
window:
1440 × 900

background:
white

protein:
cartoon

protein surface:
off

ligand:
sticks

waters:
hidden

cofactors:
sticks

labels:
off
```

PoseBusters 原数据保留了 cofactors，所以**不要把 cofactors 从 receptor 中删除**；它们有时直接参与 binding，而且 PoseBusters 本身也单独检查 ligand 与 organic/inorganic cofactors 的冲突。([Royal Society of Chemistry Publications][2])

---

# 三十二、视角必须随机化

否则 Agent 有可能学 target screenshot。

每个 episode 使用 deterministic random seed：

```python
camera_seed = hash(episode_id)
```

随机：

```text
rotation x
rotation y
rotation z
```

但不能随机：

```text
molecular coordinates
```

Camera transform 不改变真正结构。

---

# 三十三、诊断任务不要一开始就 zoom 到完美 binding pocket

可以分两个难度。

### Easy

```text
zoom ligand
```

Agent 打开就看到 binding site。

### Hard

```text
full protein view
```

Agent 必须：

```text
find ligand
zoom
rotate
inspect
```

这又能测 computer-use planning。

---

# 三十四、PoseBusters 自动 evaluator

官方命令本身就非常方便：

```bash
bust ligand_pred.sdf \
  -l ligand_native.sdf \
  -p receptor.pdb \
  --outfmt csv
```

官方文档支持这种 re-docking 模式，并输出一系列 validity checks 以及 RMSD≤2 Å 判断。([PoseBusters][6])

因此 evaluator：

```text
Agent output
    ↓
pred_ligand.sdf
    ↓
PoseBusters
    ↓
metrics.csv
```

非常直接。

---

# 三十五、建议 pin PoseBusters version

当前官方 GitHub 在我查到的信息中已经有 0.6.x 系列版本；为了 benchmark 可复现性，不应该：

```bash
pip install posebusters
```

然后永远使用最新版本。

而应该：

```text
environment.lock
```

固定：

```text
PoseBusters
RDKit
PyMOL
AutoDock Vina
OpenBabel/Meeko
ProLIF
Python
```

版本。

PoseBusters 官方仓库和 CLI 都是公开维护的。([GitHub][7])

---

# 三十六、Docking RMSD 一定要考虑 ligand symmetry

不要直接：

```python
np.sqrt(((pred-ref)**2).sum(...))
```

否则：

```text
benzene ring
carboxylate
symmetric phenyl substitution
```

会被错误惩罚。

应该做：

> symmetry-aware heavy-atom RMSD。

最简单：

```text
PoseBusters / RDKit atom mapping
```

统一处理。

---

# 三十七、如果 Agent 不小心移动了 protein 怎么办

Evaluator 要检查：

$$
RMSD_{\text{protein}}
$$

against original receptor。

对于 fixed-receptor benchmark：

```text
protein coordinate RMSD > 0.1 Å
```

可以判：

```text
environment corruption
```

或者直接恢复原始 receptor，只评价 ligand。

我更推荐：

```text
flag = protein_modified
```

而不是整个 episode 0 分。

这本身也能分析 Agent 的操作错误。

---

# 三十八、完整 metrics

最后我会报告 5 大类指标。

---

## 1. Computer-use success

### Task Completion Rate

$$
TCR =
\frac{\#completed}{N}
$$

同时记录：

```text
application crash
wrong file
wrong object
failed save
timeout
```

---

## 2. Interface Recognition

```text
Interface Precision
Interface Recall
Interface F1
Interface Jaccard
```

Primary：

$$
F1_{interface}
$$

---

## 3. Interaction Recognition

```text
Interaction Precision
Interaction Recall
Interaction F1
```

并按 interaction type breakdown。

---

# 三十九、4. Pose Diagnosis

两个任务单独评。

### Physical plausibility

Ground truth：

```text
PB-valid
```

报告：

```text
Accuracy
Balanced Accuracy
Macro-F1
```

### Native-like prediction

Ground truth：

$$
RMSD\le2Å
$$

报告：

```text
Balanced Accuracy
Macro-F1
AUROC
```

如果有 confidence：

```text
Brier Score
ECE
```

---

# 四十、为什么 calibration 很有价值

因为科学 Agent 最重要的能力之一其实是：

> 知道什么时候自己无法判断。

一个好的 Agent：

```text
obvious steric clash → confidence 0.98 incorrect

beautiful pose but alternative orientation
→ confidence 0.55 / uncertain
```

比：

```text
全部 confidence 0.99
```

科学得多。

所以可以计算：

$$
Brier =
\frac1N\sum_i(p_i-y_i)^2.
$$

---

# 四十一、5. End-to-End Docking Metrics

最重要报告：

### RMSD coverage

$$
C_{2Å}
=
\frac{1}{N}
\sum_i
\mathbb{1}[RMSD_i\le2Å].
$$

### PB-valid coverage

$$
C_{PB}
=
\frac1N
\sum_i PBValid_i.
$$

### Native-and-valid

$$
C_{\text{success}}
=
\frac1N
\sum_i
\mathbb{1}
[
RMSD_i\le2Å
\land PBValid_i
].
$$

这个我建议作为 primary docking metric。

---

# 四十二、另外强烈建议加 centroid RMSD

定义：

$$
c_L =
\frac1N\sum_i x_i.
$$

然后：

$$
d_c =
\|c_{pred}-c_{native}\|_2.
$$

它可以区分：

```text
wrong pocket
```

和：

```text
correct pocket / wrong orientation
```

PoseBench 最新评价体系也纳入 centroid RMSD。([Nature][3])

---

# 四十三、再加 Interface Recovery

即使 RMSD 高：

```text
ligand 可能仍位于正确 cavity
```

所以：

$$
F1(I_{pred},I_{native})
$$

非常有解释性。

最后一个 docking result 可以是：

```text
Ligand RMSD       3.8 Å
Centroid RMSD     0.9 Å
Interface F1      0.78
PB-valid          True
```

这立刻告诉你：

> 进入了正确 pocket，但 orientation 错了。

---

# 四十四、最终一条 episode 的结果应该长这样

```json
{
  "episode_id": "PB_0187",
  "task": "pose_diagnosis",

  "agent": {
    "completed": true,

    "interface_residues": [
      "A:42",
      "A:45",
      "A:98",
      "A:101"
    ],

    "physical_plausibility": "VALID",

    "native_likeness": "LIKELY_INCORRECT",

    "confidence": 0.81,

    "failure_modes": [
      "wrong_orientation"
    ]
  },

  "ground_truth": {
    "ligand_rmsd": 4.13,
    "centroid_rmsd": 1.02,
    "pb_valid": true,
    "interface_f1": 0.73
  },

  "score": {
    "interface_f1": 0.83,
    "plausibility_correct": true,
    "native_classification_correct": true
  }
}
```

---

# 四十五、Computer Use 本身还要记录效率

每一步都记录：

```text
timestamp
screenshot
mouse action
keyboard action
PyMOL command
active object
```

最后统计：

```text
Decision steps
Mouse clicks
Keyboard actions
PyMOL commands
Wall-clock runtime
Invalid actions
Application errors
```

这样以后能比较：

```text
Agent A
success 70%
平均 43 steps

Agent B
success 72%
平均 119 steps
```

而不是只有成功率。

---

# 四十六、我推荐 action budget

可以先这样定：

| Task            | Max agent decisions |
| --------------- | ------------------: |
| L0 Manipulation |                  40 |
| L1 Interface    |                  60 |
| L2 Interaction  |                  80 |
| L3 Diagnosis    |                 100 |
| Pose Ranking    |                 140 |
| End-to-End      |                 250 |

这里的：

```text
decision
```

定义为一次：

> screenshot → model reasoning → UI actions

而不要按：

```text
一个字符一次 keyboard event
```

计算，否则不同 computer-use framework 不可比。

---

# 四十七、还需要严格区分 Failure Type

每次失败保存：

```text
F0 environment error
F1 file navigation error
F2 object selection error
F3 PyMOL command syntax error
F4 visualization error
F5 spatial perception error
F6 chemical reasoning error
F7 pose classification error
F8 docking setup error
F9 docking execution error
F10 pose ranking error
F11 output/save error
```

这个对分析 Computer Use Agent 会特别有价值。

例如你最后可能发现：

```text
GPT-X:
GUI success         96%
interface F1        91%
interaction F1      75%
pose diagnosis      63%
end-to-end docking  48%
```

那么就能明确说明：

> bottleneck 已经不是 computer use，而是 molecular reasoning。

---

# 四十八、建议设置三个难度层

不要只给总平均。

### Easy

```text
single-chain receptor
small ligand
clear deep pocket
no cofactor
no major symmetry
```

### Medium

```text
multi-chain
flexible ligand
shallow pocket
multiple H-bonds
```

### Hard

```text
cofactor
metal ion
large ligand
many rotatable bonds
protein interface pocket
ambiguous alternative poses
```

---

# 四十九、Difficulty 可以自动量化

可以用：

```text
protein length
number of chains
ligand heavy atom count
rotatable bonds
ring count
formal charge
cofactor presence
metal presence
pocket SASA
number of interface residues
native interaction count
Vina oracle RMSD
```

然后通过 quantile 做：

```text
easy
medium
hard
```

而不是人工拍脑袋分类。

---

# 五十、PoseBusters 本身还可以按照 sequence identity 做 generalization 分层

原论文就按 target 对 PDBbind 2020 的最大 sequence identity 分成：

```text
low:     0–30%
medium: 30–90%
high:   90–100%
```

来分析 docking 方法的泛化。([Royal Society of Chemistry Publications][8])

你也可以保留这个标签：

```text
Novel target
Medium similarity
Familiar target
```

看看 Agent 是否在结构“熟悉”蛋白上表现更好。

---

# 五十一、我尤其推荐一个 ablation：看图 vs PyMOL tools

这很可能会产出很有意思的结果。

完全相同的任务，跑：

### Setting A

```text
screenshot only
```

### Setting B

```text
screenshot + mouse
```

### Setting C

```text
screenshot + mouse + PyMOL console
```

### Setting D

```text
full PyMOL + distance/select tools
```

然后：

| Setting     | Interface F1 | Pose Accuracy |
| ----------- | -----------: | ------------: |
| screenshot  |              |               |
| GUI         |              |               |
| GUI+command |              |               |
| full tool   |              |               |

这实际上就是在问：

> Scientific software tools 到底给 multimodal agent 带来多少能力增益？

这个 research question 本身就挺漂亮。

---

# 五十二、另一个很重要的 ablation

## Native-like vs chemically plausible

构造四个象限：

|          | PB-valid | PB-invalid |
| -------- | -------: | ---------: |
| RMSD≤2 Å |        A |          B |
| RMSD>2 Å |        C |          D |

也就是：

### A

```text
correct + valid
```

### B

```text
native-like but chemically bad
```

### C

```text
wrong binding mode but physically reasonable
```

### D

```text
wrong + physically bad
```

这四类特别能检验模型究竟懂不懂 docking。

---

# 五十三、Agent prompt 我会固定成类似这样

### Pose diagnosis

> Inspect the protein–ligand complex currently displayed in PyMOL.
> Use the available PyMOL visualization and measurement tools as needed.
>
> Determine:
>
> 1. which protein residues directly form the observed ligand-binding interface;
> 2. whether the ligand pose appears physically plausible;
> 3. whether there is evidence that this represents the correct binding mode;
> 4. any apparent failure modes.
>
> Create a PyMOL selection named `agent_interface` containing the interface residues.
>
> Do not access external resources.
>
> Return the required structured result.

然后 evaluator 不给 Agent：

```text
native pose
RMSD
PDB ID
method name
docking score
```

---

# 五十四、E2E prompt

> Using the provided receptor, ligand and docking-box specification, perform protein–ligand docking using the docking tool available inside PyMOL.
>
> Inspect the generated poses and select the pose you judge to best represent the binding mode.
>
> Create:
>
> `agent_interface`
>
> and export the selected ligand pose as:
>
> `outputs/pred_ligand.sdf`
>
> Do not access external resources or alter the receptor coordinates.

然后完全自动评价。

---

# 五十五、最终 leaderboard 我不建议只给一个数字

主表应该是：

| Agent | GUI | Interface F1 | Interaction F1 | Pose Diagnosis | Docking Success |
| ----- | --: | -----------: | -------------: | -------------: | --------------: |
| A     |     |              |                |                |                 |
| B     |     |              |                |                |                 |

后面附：

```text
PB-valid
RMSD≤2
RMSD≤2 & PB-valid
Centroid RMSD
Interface recovery
PLIF recovery
Avg actions
Failure rate
```

---

# 五十六、如果真的需要 Overall Score

我宁愿用 geometric mean：

$$
S_{\text{overall}}
=
100
\left(
S_{GUI}
S_{interface}
S_{interaction}
S_{diagnosis}
S_{dock}
\right)^{1/5}.
$$

而不是 arithmetic mean。

因为：

```text
GUI=100
Interface=100
Interaction=100
Diagnosis=100
Docking=0
```

不应该因为其他能力很好还得到：

```text
80分
```

geometric mean 会对 capability collapse 更敏感。

不过论文里我会把 overall 当 secondary metric。

---

# 五十七、推荐的完整 benchmark 数量

最终可以是：

### Astex 85

用于：

```text
development
examples
prompt optimization
environment debugging
```

### PoseBusters 308

每个 target：

```text
1 × L0 GUI
1 × native interface
~4 × pose diagnosis
1 × pose ranking
1 × E2E docking
```

所以大概：

$$
308
+
308
+
1232
+
308
+
308
=
2464
$$

个 test episodes。

数量非常合适。

不至于只有几十条，又不会大到跑不动 Computer Use。

---

# 五十八、我会这样做第一版 MVP

不要一上来做 2400 个。

### Phase 1

先取 Astex：

```text
10 cases
```

实现：

```text
PyMOL harness
session reset
agent_interface evaluator
PoseBusters evaluator
output JSON
```

---

### Phase 2

取：

```text
20 Astex
```

构造：

```text
20 × 4 pose types
=80 diagnosis tasks
```

验证 scoring。

---

### Phase 3

完整：

```text
Astex 85 dev
```

冻结：

```text
prompt
environment
metrics
```

---

### Phase 4

一次性跑：

```text
PoseBusters 308
```

正式 test。

这样才不会在 PoseBusters test 上不断调 prompt，形成 benchmark leakage。

---

# 五十九、数据来源我建议这样组合

**Canonical structure data：PoseBusters 原始 Zenodo。**
这是最干净的 crystal-ground-truth 来源，而且包含论文使用的数据。[PoseBusters 官方 Zenodo 数据](https://zenodo.org/records/8278563?utm_source=chatgpt.com)

**Validity evaluator：PoseBusters 官方包。**
[PoseBusters 官方仓库](https://github.com/maabuu/posebusters?utm_source=chatgpt.com)

**真实 docking decoy pool：PoseBench。**
现在 PoseBench 已经统一实现了 PoseBusters、Astex、DockGen 等数据以及 Vina、DiffDock、FABind、DynamicBind、NeuralPLexer、Boltz 等大量方法，非常适合直接拿预测作为 realistic hard negatives。([GitHub][5])
[PoseBench 官方仓库](https://github.com/BioinfoMachineLearning/PoseBench?utm_source=chatgpt.com)

需要注意：PoseBench 曾经发现过 **v1.0.0 的 ligand scoring bug**，后来在 v1.1.0 修复，因此如果复用它的历史 prediction/analysis pipeline，不要照搬旧版 scoring 结果。([GitHub][9])

---

# 六十、如果这是我要真正开始实现，我会冻结下面这个 benchmark specification

```text
DATA
────────────────────────────────
Dev:
    Astex Diverse 85

Test:
    PoseBusters 308

Network:
    disabled

PDB identities:
    anonymized

Native ligand:
    evaluator-only


ENVIRONMENT
────────────────────────────────
PyMOL
AutoDock Vina
PoseBusters
RDKit
ProLIF

Fixed window size
Fixed theme
Randomized deterministic camera


TASKS
────────────────────────────────
T0 PyMOL manipulation

T1 Interface identification
    GUI-only
    Tool-assisted

T2 Interaction identification

T3 Pose diagnosis
    physical plausibility
    native-likeness
    failure classification

T4 Pose ranking

T5 End-to-end redocking
    known-pocket
    optional blind-pocket


GROUND TRUTH
────────────────────────────────
Ligand RMSD
Centroid RMSD
PB-valid
Native interface
Candidate interface
PLIF


PRIMARY METRICS
────────────────────────────────
Task Completion

Interface F1

Interaction F1

Pose Macro-F1
Pose Calibration

RMSD <= 2 Å

PB-valid

RMSD <= 2 Å AND PB-valid

Interface Recovery F1

PLIF Recovery


LOGGING
────────────────────────────────
Screenshots
Agent actions
PyMOL commands
Final PSE
Final SDF
Docking log
Structured JSON
Failure category
```

我认为这里面最值得重点做的，不是单纯的 **“Agent 能不能调用 Vina”**，而是中间的：

$$
\boxed{
\text{Pose diagnosis}
+
\text{interface understanding}
+
\text{interaction understanding}
}
$$

因为前者更多是流程自动化，而后面三个才真正能区分“会操作科学软件的 Agent”和“能用科学软件做结构生物学推理的 Agent”。


[1]: https://zenodo.org/records/8278563?utm_source=chatgpt.com "PoseBusters: AI-based docking methods fail to generate physically valid poses or generalise to novel sequences | Zenodo"
[2]: https://pubs.rsc.org/en-us/content/articlehtml/2024/sc/d3sc04185a?utm_source=chatgpt.com "PoseBusters: AI-based docking methods fail to generate physically valid poses or generalise to novel sequences - Chemical Science (RSC Publishing) DOI:10.1039/D3SC04185A"
[3]: https://www.nature.com/articles/s42256-025-01160-1?utm_source=chatgpt.com "Assessing the potential of deep learning for protein–ligand docking | Nature Machine Intelligence"
[4]: https://polarishub.io/benchmarks/polaris/posebusters-v1?utm_source=chatgpt.com "posebusters-v1"
[5]: https://github.com/BioinfoMachineLearning/PoseBench?utm_source=chatgpt.com "GitHub - BioinfoMachineLearning/PoseBench: Comprehensive benchmarking of protein-ligand structure prediction methods. (Nature Machine Intelligence) · GitHub"
[6]: https://posebusters.readthedocs.io/en/latest/?utm_source=chatgpt.com "PoseBusters: Plausibility checks for generated molecule poses. — PoseBusters 0.6 documentation"
[7]: https://github.com/maabuu/posebusters?utm_source=chatgpt.com "GitHub - maabuu/posebusters: Plausibility checks for generated molecule poses. · GitHub"
[8]: https://pubs.rsc.org/en/content/articlehtml/2024/sc/d3sc04185a?utm_source=chatgpt.com "PoseBusters: AI-based docking methods fail to generate physically valid poses or generalise to novel sequences - Chemical Science (RSC Publishing) DOI:10.1039/D3SC04185A"
[9]: https://github.com/BioinfoMachineLearning/PoseBench/blob/main/README.md?utm_source=chatgpt.com "PoseBench/README.md at main · BioinfoMachineLearning/PoseBench · GitHub"
