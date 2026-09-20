# 任务：实现 PyMolDock-CUA-Bench

你现在负责从零实现一个**可运行、可复现、可自动评分的 Scientific Computer-Use Agent Benchmark**。

Benchmark 的主要被测对象是：

**火山方舟 Agent Plan Personal CUA**

它需要在云电脑环境中操纵 **PyMOL**，完成蛋白质–配体 docking 场景中的结构观察、界面识别、pose 判断，以及后续端到端 redocking。

这个 benchmark 的核心目的不是评价 docking algorithm 本身，而是评价 Computer Use Agent 的三类能力：

1. **Computer Interaction**

   * 打开 PyMOL；
   * 找到正确数据；
   * 操纵 3D 场景；
   * 使用 GUI / PyMOL 工具；
   * 保存结果。

2. **Molecular Spatial Reasoning**

   * 找到 ligand；
   * 找到 protein–ligand interface；
   * 判断关键 contacts / clash；
   * 判断当前 pose 是否物理合理；
   * 判断当前 pose 是否像正确 binding mode。

3. **Scientific Workflow Execution**

   * 设置 docking；
   * 调用统一的 AutoDock Vina backend；
   * 浏览多个 docking poses；
   * 选择最终 pose；
   * 导出结构；
   * 产生可自动评价的结果。

---

# 0. 总体执行原则

这是一个工程实现任务，不是方案讨论任务。

请：

* 直接检查当前仓库；
* 创建缺失代码；
* 安装或声明必要依赖；
* 写测试；
* 运行测试；
* 修复失败；
* 完成最小端到端 smoke test；
* 不要只生成伪代码；
* 不要只写 README；
* 不要留下大面积 TODO；
* 不要在每一步询问用户确认；
* 遇到小的实现歧义时自行做合理选择，并记录在 `IMPLEMENTATION_NOTES.md`；
* 只有遇到无法继续的外部阻塞，例如缺少真实 API Key、云电脑不可访问、数据文件不存在，才允许停止对应的集成测试，但仍然要完成 mock/offline 版本。

**优先保证 correctness、reproducibility、ground-truth isolation。**

不要为了减少代码而牺牲 evaluator 的严谨性。

---

# 1. 非常重要：先检查真实 CUA 接口，不允许猜 API

火山方舟 Personal CUA 的文档：

https://docs.volcengine.com/docs/ark/agent-plan-personal-cua?lang=zh

当前官方 ArkCLI / Agent Plan 支持将 CUA capability 安装给 Codex。

首先检查：

```bash
arkcli --version
arkcli helper mcp --help
arkcli helper mcp codex --capability cua --help || true
```

检查本机是否已有：

```text
byted-util-ark-cua
```

Skill。

搜索可能的位置，包括但不限于：

```bash
~/.agents/skills/
~/.codex/
~/.ark/
```

如果能够通过官方命令安装，并且尚未安装，应首先打印建议命令，但**不要自动修改用户凭证或登录状态**。

预期安装形式可能类似：

```bash
arkcli helper mcp codex \
    --capability cua \
    --profile <agent-plan-profile>
```

但：

**任何 CUA 子命令、参数名、返回 JSON schema，都必须从本机实际安装的官方 Skill、`--help`、官方 references 或文档中确认。**

禁止根据本 prompt 中的历史示例自行假设：

```text
task run
task status
artifact save
desktop list
```

一定仍然具有完全相同的参数。

实现 adapter 前：

1. 定位真实 `byted-util-ark-cua` Skill；
2. 阅读它的 `SKILL.md`；
3. 阅读相关 `references/*.md`；
4. 对关键 CLI 执行 `--help`；
5. 根据当前实际接口实现 adapter。

将检查结果记录到：

```text
docs/CUA_INTERFACE.md
```

内容至少包括：

```text
Skill path
Skill version
ArkCLI version
认证方式
启动任务方式
轮询任务方式
任务终态
needs_input 表达方式
artifact 获取方式
desktop/session 管理方式
model/version 查询方式
```

---

# 2. 安全要求：绝对禁止泄露 Agent Plan API Key

任何情况下：

禁止：

```python
API_KEY = "..."
```

禁止把 key：

```text
写入 Git
写入 benchmark log
写入 episode JSON
写入 result JSON
写入 stdout
写入 exception message
```

优先复用：

```text
ArkCLI profile
官方 CUA Skill 自身认证
```

如果需要环境变量，代码也只能读取变量名，不打印值。

必须创建：

```text
.env.example
```

只能包含：

```text
# Do not put real credentials in git.
```

以及必要变量名。

`.gitignore` 至少包含：

```text
.env
*.key
credentials*
auth*
results/raw/
data/private/
```

但注意不能粗暴 ignore 正常源码中的 `auth.py`。

---

# 3. Benchmark 数据设计

使用：

## Development

```text
Astex Diverse Set
```

目标约：

```text
85 complexes
```

用于：

```text
开发
debug
prompt engineering
环境验证
阈值调整
```

## Test

```text
PoseBusters Benchmark
```

目标约：

```text
308 complexes
```

作为冻结 test set。

**禁止使用 PoseBusters test set 反复调 prompt。**

---

# 4. 第一阶段只实现 Pose Diagnosis MVP

不要第一步就接 Vina。

第一阶段必须完整跑通：

```text
protein + candidate ligand pose
            ↓
          PyMOL
            ↓
        ByteDance CUA
            ↓
识别 interface / 判断 pose
            ↓
submission.json
final.pse
            ↓
offline evaluator
            ↓
Interface F1
PB-valid classification
Native-likeness classification
CUA task success
```

只有这个闭环测试通过后再实现 Phase B：

```text
End-to-End AutoDock Vina redocking
```

---

# 5. 创建仓库结构

最终结构应大致为：

```text
pymoldock-cua-bench/
│
├── README.md
├── pyproject.toml
├── uv.lock                     # 如果使用 uv
├── .gitignore
├── .env.example
├── IMPLEMENTATION_NOTES.md
│
├── configs/
│   ├── benchmark.yaml
│   ├── cua.yaml
│   ├── pymol.yaml
│   ├── diagnosis.yaml
│   ├── vina.yaml
│   └── difficulty.yaml
│
├── docs/
│   ├── CUA_INTERFACE.md
│   ├── DATA_FORMAT.md
│   ├── EVALUATION.md
│   └── SECURITY.md
│
├── data/
│   ├── raw/
│   │   ├── astex/
│   │   ├── posebusters/
│   │   └── posebench_predictions/
│   │
│   ├── public/
│   │   ├── dev/
│   │   └── test/
│   │
│   └── private/
│       ├── dev/
│       └── test/
│
├── episodes/
│   ├── manifests/
│   ├── prompts/
│   └── generated/
│
├── pymol_plugin/
│   └── pymoldockbench/
│       ├── __init__.py
│       ├── plugin.py
│       ├── episode_loader.py
│       ├── answer_panel.py
│       ├── interface_tools.py
│       ├── exporter.py
│       └── docking_backend.py
│
├── src/
│   └── pymoldock_bench/
│       ├── __init__.py
│       │
│       ├── schemas/
│       │   ├── episode.py
│       │   ├── submission.py
│       │   ├── ground_truth.py
│       │   └── result.py
│       │
│       ├── cua/
│       │   ├── base.py
│       │   ├── ark_client.py
│       │   ├── parser.py
│       │   └── mock_client.py
│       │
│       ├── data/
│       │   ├── prepare_posebusters.py
│       │   ├── prepare_astex.py
│       │   ├── anonymize.py
│       │   ├── sanitize_structures.py
│       │   ├── pose_pool.py
│       │   └── split.py
│       │
│       ├── episodes/
│       │   ├── build_diagnosis.py
│       │   ├── build_ranking.py
│       │   └── build_redocking.py
│       │
│       ├── eval/
│       │   ├── rmsd.py
│       │   ├── centroid.py
│       │   ├── interface.py
│       │   ├── posebusters.py
│       │   ├── interactions.py
│       │   ├── diagnosis.py
│       │   ├── calibration.py
│       │   └── aggregate.py
│       │
│       ├── runner/
│       │   ├── episode_runner.py
│       │   ├── suite_runner.py
│       │   ├── artifact_collector.py
│       │   └── state_machine.py
│       │
│       └── utils/
│           ├── io.py
│           ├── logging.py
│           ├── subprocess.py
│           └── geometry.py
│
├── scripts/
│   ├── check_environment.py
│   ├── prepare_data.py
│   ├── build_episodes.py
│   ├── run_episode.py
│   ├── run_suite.py
│   ├── evaluate_episode.py
│   └── evaluate_suite.py
│
└── tests/
    ├── fixtures/
    ├── unit/
    ├── integration/
    └── smoke/
```

如果当前仓库已经存在合理结构：

**适配现有结构，不要为了和本 prompt 一模一样而破坏已有工程。**

---

# 6. Python 工程要求

要求：

```text
Python >= 3.10
```

推荐：

```text
3.11
```

使用：

```text
pydantic
PyYAML
numpy
pandas
scipy
rdkit
MDAnalysis 或 biotite（按实际需求）
```

可选：

```text
ProLIF
```

PoseBusters 单独 pin 版本。

测试：

```text
pytest
```

lint：

```text
ruff
```

typing：

```text
mypy 或 pyright
```

至少确保：

```bash
pytest
ruff check .
```

能运行。

---

# 7. 核心 schema

实现 Pydantic schema。

## Episode

至少：

```python
class DockingBox(BaseModel):
    center: tuple[float, float, float]
    size: tuple[float, float, float]


class Episode(BaseModel):
    schema_version: str = "1.0"

    episode_id: str
    target_id: str

    split: Literal["dev", "test"]

    task: Literal[
        "gui",
        "interface",
        "interaction",
        "diagnosis",
        "ranking",
        "redocking",
    ]

    track: Literal[
        "vision_only",
        "tool_assisted",
        "workflow",
    ]

    difficulty: Literal[
        "easy",
        "medium",
        "hard",
    ]

    public_dir: str

    receptor_file: str
    ligand_file: str | None = None
    candidate_pose_file: str | None = None

    docking_box: DockingBox | None = None

    max_walltime_sec: int
    expected_artifacts: list[str]

    prompt_template: str
```

---

# 8. Submission schema

不要依赖解析 Agent 自由文本。

CUA 最终必须通过 benchmark panel 或文件产生结构化提交。

```python
class InteractionPrediction(BaseModel):
    type: Literal[
        "hydrogen_bond",
        "hydrophobic",
        "salt_bridge",
        "pi_stacking",
        "cation_pi",
        "metal_coordination",
        "steric_clash",
        "other",
    ]

    chain: str | None
    residue_number: str | None
    residue_name: str | None


class Submission(BaseModel):
    schema_version: str = "1.0"

    episode_id: str

    physical_plausibility: Literal[
        "valid",
        "invalid",
        "uncertain",
    ]

    native_likeness: Literal[
        "likely_correct",
        "likely_incorrect",
        "uncertain",
    ]

    confidence: float

    failure_modes: list[
        Literal[
            "steric_clash",
            "wrong_orientation",
            "wrong_pocket",
            "poor_pocket_complementarity",
            "lost_key_interactions",
            "ligand_internal_geometry",
            "cofactor_conflict",
            "excessive_solvent_exposure",
            "other",
        ]
    ]

    interactions: list[InteractionPrediction] = []

    selected_pose: str | None = None
```

要求：

```text
0 <= confidence <= 1
```

---

# 9. Ground truth schema

Private，仅 evaluator 可访问。

```python
class GroundTruth(BaseModel):
    schema_version: str = "1.0"

    episode_id: str
    target_id: str

    native_ligand_path: str
    native_complex_path: str
    receptor_path: str

    ligand_rmsd: float | None
    centroid_rmsd: float | None

    pb_valid: bool | None

    native_interface: list[str]
    candidate_interface: list[str]

    candidate_native_interface_f1: float | None

    pose_bucket: Literal[
        "P0",
        "P1",
        "P2",
        "P3",
        "P4",
    ] | None
```

**这个文件绝对不允许复制到 CUA workspace。**

---

# 10. public/private 隔离必须强制检查

目录：

```text
data/public/
data/private/
```

CUA episode staging 时，只允许从：

```text
data/public/
episodes/generated/
```

复制文件。

写一个安全检查：

```python
assert_private_data_not_exposed(...)
```

递归检查 staged CUA workspace：

禁止出现：

```text
native
ground_truth
gt.json
reference_pose
crystal_ligand
```

等明显文件。

还要基于真实绝对路径判断：

```text
没有 symlink 指向 private/
```

如果发现：

```text
FAIL CLOSED
```

不启动 CUA。

给这个安全检查写单元测试。

---

# 11. PDB / ligand 匿名化

所有 test episode：

原始 ID：

```text
7ABC
```

映射：

```text
PB_00187
```

真实映射只存在 private metadata。

蛋白 PDB 删除可能泄露身份的信息：

```text
HEADER
TITLE
COMPND
SOURCE
DBREF
SEQADV
REMARK
AUTHOR
JRNL
```

不要删除：

```text
ATOM
HETATM（需要保留相关 cofactors 时）
CONECT（如确实需要）
```

目标 ligand residue name 统一：

```text
LIG
```

清理 SDF property：

```text
PDB ID
compound database ID
original method name
docking score
source model
```

但是不能破坏：

```text
atom elements
formal charge
bond order
stereochemistry
coordinates
```

---

# 12. 建议增加 deterministic rigid transform

为了避免绝对 PDB 坐标泄漏：

对每个 episode 的：

```text
protein
ligand
candidate pose
cofactor
```

共同应用相同：

$$
x' = Rx + t
$$

其中：

```text
R 是合法 3D rotation
t 是 translation
seed = stable_hash(episode_id)
```

必须保证：

```text
pairwise geometry 不变
protein-ligand distance 不变
ligand RMSD 相对结果不变
```

Private native structure必须应用同样 transform 后再用于 evaluator，或者 evaluator 先统一回到原始 frame。

选择其中一种，一定写测试验证。

---

# 13. Interface ground truth

统一定义 primary interface：

对于 ligand heavy atoms \(L\)：

$$
I_{4Å}
=
\left\{
r:
\min_{a\in r,\;b\in L}
\|x_a-x_b\|
\le4.0\AA
\right\}
$$

规则：

* protein residue；
* heavy atoms only；
* primary cutoff = 4.0 Å。

另外预计算：

```text
3.5 Å
5.0 Å
```

用于 sensitivity analysis。

实现：

```python
compute_interface(
    protein,
    ligand,
    cutoff=4.0,
) -> set[ResidueID]
```

ResidueID 至少使用：

```text
chain + residue number + insertion code
```

不要只用 residue number。

---

# 14. Interface evaluator

需要计算：

$$
Precision
$$

$$
Recall
$$

$$
F1
$$

$$
Jaccard
$$

特别要区分两件事情：

## A. Agent perception accuracy

比较：

```text
agent_interface
vs
candidate_pose_interface
```

记：

```text
agent_observed_interface_f1
```

它回答：

> Agent 是否正确看懂当前屏幕里的 interface？

## B. Candidate native recovery

比较：

```text
candidate_pose_interface
vs
native_interface
```

记：

```text
candidate_native_interface_f1
```

它回答：

> candidate pose 本身是否恢复 native interface？

不要把这两个指标混在一起。

---

# 15. 从 final.pse 获取 agent_interface

Agent 最终必须创建：

```text
agent_interface
```

selection。

Evaluator 要支持：

```python
extract_selection_from_pse(
    pse_path,
    selection_name="agent_interface",
)
```

使用 headless PyMOL，如果环境可用。

输出：

```text
set[(chain, resi, icode)]
```

如果 selection 不存在：

```text
interface task = incomplete
```

不要从自然语言猜。

---

# 16. PoseBusters evaluator

使用官方 PoseBusters。

固定版本写进 lockfile / environment metadata。

redocking 形式：

```bash
bust ligand_pred.sdf \
    -l ligand_native.sdf \
    -p receptor.pdb
```

但是实现时：

**先执行当前安装版本 `bust --help` 并确认参数。**

封装：

```python
class PoseBustersEvaluator:
    def evaluate(
        self,
        predicted_ligand: Path,
        native_ligand: Path,
        receptor: Path,
    ) -> PoseBustersResult:
        ...
```

结果至少抽象出：

```text
pb_valid
rmsd_le_2a（如果当前版本有）
individual_checks
raw_output
```

保存原始 scorer 输出用于审计。

---

# 17. ligand RMSD

必须实现或调用可靠的：

**symmetry-aware heavy-atom RMSD**

禁止简单：

```python
np.sqrt(np.mean((pred - native) ** 2))
```

因为 symmetric atom mapping 会产生错误惩罚。

优先：

```text
RDKit graph mapping / symmetry aware alignment
```

或复用 PoseBusters/PoseBench 已验证方法。

必须写测试：

```text
symmetric benzene-like case
atom permutation case
rigidly transformed identical ligand
```

预期 identical chemistry 的等价 pose RMSD 接近 0。

---

# 18. Centroid RMSD

计算：

$$
c =
\frac1N
\sum_i x_i
$$

heavy atoms。

$$
d_c =
\|c_{pred}-c_{native}\|_2
$$

实现：

```python
ligand_centroid_distance(...)
```

不要叫 centroid RMSD 如果实际上只是 centroid distance；代码内部名字要准确，例如：

```text
centroid_distance_angstrom
```

论文展示可以叫 ligand centroid distance。

---

# 19. Pose bucket

统一生成 5 类。

## P0

```text
ligand RMSD <= 2 Å
AND
PB-valid = true
```

## P1

```text
ligand RMSD <= 2 Å
AND
PB-valid = false
```

## P2

correct pocket / wrong pose：

```text
RMSD > 2 Å
centroid distance <= 2.5 Å
candidate-native interface F1 >= 0.5
```

## P3

nearby incorrect sub-pocket：

```text
2.5 < centroid distance <= 6 Å
```

且 candidate ligand 仍存在 meaningful protein contact，例如：

```text
>= 3 interface residues
```

## P4

gross failure：

```text
centroid distance > 6 Å
```

或：

```text
无 meaningful protein contact
明显不可接受 clash
```

---

# 20. Diagnosis set 采样比例

默认：

```text
P0 25%
P1 15%
P2 35%
P3 15%
P4 10%
```

原因：

P2 是最重要 hard negative。

不要让 benchmark 被：

```text
ligand 明显飘在蛋白外
```

这种 easy negative 主导。

---

# 21. Candidate poses 来源

优先级：

```text
真实 docking prediction
    >
真实 alternative docking pose
    >
controlled synthetic perturbation
```

如果存在 PoseBench predictions：

优先从：

```text
AutoDock Vina
DiffDock
FABind
DynamicBind
NeuralPLexer
FlowDock
...
```

构造 candidate pool。

**导入后全部自己重新评分。**

不要信任旧缓存 label。

要计算：

```text
RMSD
centroid distance
PB-valid
interface F1
```

并写：

```text
pose_database.parquet
```

列至少包括：

```text
target_id
pose_id
source_method
source_rank
rmsd
centroid_distance
pb_valid
native_interface_f1
pose_bucket
```

其中：

```text
source_method
source_rank
```

只能保留在 private metadata。

Agent 看不到。

---

# 22. PyMOL Plugin：Phase A MVP

先实现最小插件。

窗口：

```text
PyMolDockBench
────────────────────────────

Episode
PB_00187_T3_P2

Physical plausibility
○ Valid
○ Invalid
○ Uncertain

Correct binding mode
○ Likely correct
○ Likely incorrect
○ Uncertain

Confidence
[ 0.00 ]

Failure modes
□ Steric clash
□ Wrong orientation
□ Wrong pocket
□ Poor pocket complementarity
□ Lost key interactions
□ Ligand internal geometry
□ Cofactor conflict
□ Excessive solvent exposure
□ Other

[ Submit ]

[ Export Session ]
```

提交时写：

```text
submission.json
```

Export Session：

```text
final.pse
```

必须校验：

```text
episode_id 与当前 episode 一致
confidence 合法
两个分类已选择
```

---

# 23. Episode loader

Plugin 必须支持一个稳定入口，例如：

```text
Load Episode
```

读取：

```text
episode.json
```

自动：

```text
删除上一个 scene
load receptor
load candidate pose
设置统一 representation
```

默认显示：

```text
protein = cartoon
ligand = sticks
cofactors = sticks
water = hidden
background = white
```

但是：

**不要自动选择 interface。**

---

# 24. Camera

每个 episode 使用 deterministic camera seed。

实现：

```python
camera_seed = stable_hash(episode_id)
```

随机 camera orientation。

不能改变 molecular coordinates。

保存 camera transform metadata。

要求：

同一 episode 多次启动：

```text
初始视角一致
```

不同 episode：

```text
视角通常不同
```

---

# 25. 三个实验 track

## Track V1 — vision_only

目标：

测试真正视觉 3D reasoning。

禁止使用直接计算 interface 的 PyMOL selection command，例如：

```text
within
around
byres (...) within ...
```

也禁止：

```text
Python API
external scripts
```

Agent 可以：

```text
旋转
缩放
切 representation
使用 GUI measurement
观察结构
```

注意：

如果 CUA 本身没有技术手段强制屏蔽命令，则至少在实验配置中：

```text
明确 prompt prohibition
记录违规行为
```

并加入：

```text
protocol_violation
```

字段。

---

## Track V2 — tool_assisted

允许：

```text
select
distance
show
hide
label
zoom
orient
```

以及标准 PyMOL command line。

这个 track 测：

> Scientific Agent 是否会有效利用专业软件能力。

---

## Track V3 — workflow

Agent 自己：

```text
找到 PyMOL
打开 episode
完成分析
提交
导出
```

而不是预先加载 scene。

---

# 26. Diagnosis objective

固定模板，尽量不要每个 episode 修改文本。

英文任务 prompt 可以使用：

```text
You are evaluating one protein–ligand docking result in PyMOL.

Open the specified benchmark episode and inspect the protein–ligand
complex using PyMOL.

Your task is to:

1. inspect the ligand-binding interface;
2. identify the protein residues that directly interact with the ligand;
3. inspect important protein–ligand interactions and obvious steric conflicts;
4. judge whether the current ligand pose is physically plausible;
5. judge whether the available structural evidence supports this being the
   correct binding mode;
6. report your confidence.

Create a PyMOL selection named `agent_interface` containing the residues
you judge to form the observed protein–ligand interface.

Submit the structured answer using the PyMolDockBench panel and export
the final PyMOL session.

Do not access external websites or databases.
Do not search for the structure by identity.
Do not access other benchmark episodes.
Do not ask the user for assistance.
```

对于 `vision_only` 增加：

```text
Do not use PyMOL distance-based automatic residue selection commands
such as `within`, `around`, or equivalent automated neighborhood queries
to generate the interface selection.
```

---

# 27. CUA adapter

定义统一接口，不让 benchmark runner 直接依赖某一版 CLI。

```python
class CUAClient(Protocol):

    def environment_info(self) -> dict:
        ...

    def start_task(
        self,
        *,
        objective: str,
        desktop_id: str | None,
        title: str,
    ) -> CUATask:
        ...

    def get_task(self, task_id: str) -> CUATask:
        ...

    def collect_artifacts(
        self,
        task_id: str,
        output_dir: Path,
    ) -> list[Path]:
        ...

    def cancel_task(
        self,
        task_id: str,
    ) -> None:
        ...
```

`ArkCUAClient` 使用官方当前接口。

`MockCUAClient` 用于 CI。

---

# 28. 绝对不要自己实现第二个 planner

Controller 只能：

```text
准备 episode
发送完整 objective
等待 CUA
收 artifacts
评分
```

禁止：

```text
Controller 看截图
Controller 帮 CUA 拆步骤
Controller 告诉 CUA 点哪个按钮
Controller 根据 CUA 状态动态提供科学提示
```

因为我们测的是：

**ByteDance CUA 本身。**

---

# 29. CUA task state machine

统一内部状态：

```python
class TaskOutcome(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NEEDS_INPUT = "needs_input"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"
```

官方不同状态映射到这个 abstraction。

如果：

```text
needs_input
```

Benchmark：

```text
不得人工 answer
```

episode：

```text
autonomous_success = false
human_assistance_required = true
```

但：

如果已有 artifacts，仍然离线计算 partial metrics。

---

# 30. 超时

每个 episode：

```text
max_walltime_sec
```

例如 diagnosis MVP：

```text
600 秒
```

到时间：

1. 尝试 cancel task；
2. 保存已有状态；
3. 收集已有 artifacts；
4. 标记 TIMEOUT；
5. 不无限轮询。

轮询带：

```text
reasonable exponential/fixed backoff
```

不要每 50 ms 请求一次 API。

---

# 31. 一台 desktop 禁止并发

必须实现锁：

```text
desktop_id -> asyncio/semaphore size 1
```

同一 desktop：

```text
concurrency = 1
```

如果未来多个 desktops：

可以跨 desktop 并行。

---

# 32. CUA runtime metadata

每个 benchmark run 开始记录：

```json
{
  "benchmark_version": "...",
  "git_commit": "...",
  "timestamp": "...",

  "cua": {
    "skill_path": "...",
    "skill_version": "...",
    "arkcli_version": "...",
    "model_info": {}
  },

  "environment": {
    "python": "...",
    "pymol": "...",
    "posebusters": "...",
    "rdkit": "...",
    "prolif": "...",
    "vina": "..."
  }
}
```

如果官方 CUA 提供：

```text
model/version 查询
```

一定记录。

不要假定模型恒定。

---

# 33. Artifact

每条 diagnosis episode 期望：

```text
submission.json
final.pse
```

可选：

```text
screenshot_final.png
```

Phase B redocking：

```text
submission.json
final.pse
selected_ligand.sdf
vina.log
```

如果 CUA artifact 系统无法直接发现普通本地文件：

根据官方 Skill 的真实 artifact 机制实现。

不要编造接口。

---

# 34. Episode Runner

实现：

```python
EpisodeRunner.run(episode)
```

步骤：

```text
1 validate episode
2 assert no private leakage
3 stage public workspace
4 reset benchmark app state
5 build objective
6 launch CUA task
7 monitor task
8 no human intervention
9 collect artifacts
10 validate submission
11 run offline evaluator
12 write result.json
13 cleanup
```

异常也必须生成：

```text
result.json
```

而不是直接 crash 丢数据。

---

# 35. Result schema

至少：

```python
class EpisodeResult(BaseModel):

    episode_id: str

    cua_outcome: str
    autonomous_success: bool
    human_assistance_required: bool

    runtime_sec: float | None

    submission_present: bool
    final_pse_present: bool

    agent_observed_interface_precision: float | None
    agent_observed_interface_recall: float | None
    agent_observed_interface_f1: float | None
    agent_observed_interface_jaccard: float | None

    candidate_native_interface_f1: float | None

    physical_plausibility_correct: bool | None
    native_likeness_correct: bool | None

    ligand_rmsd: float | None
    centroid_distance: float | None
    pb_valid: bool | None

    confidence: float | None

    failure_category: str | None
    protocol_violation: bool = False
```

---

# 36. Diagnosis labels

## Physical plausibility GT

Primary：

```text
PB-valid
```

Agent：

```text
valid
invalid
uncertain
```

## Native-likeness GT

Primary：

```text
RMSD <= 2 Å
```

Agent：

```text
likely_correct
likely_incorrect
uncertain
```

## Full docking success

定义：

$$
DockingSuccess
=
(RMSD\le2Å)
\land
PBValid
$$

---

# 37. Uncertain 不简单当错

计算：

## Coverage

$$
Coverage
=
\frac{N_{\text{non-uncertain}}}{N}
$$

## Selective Accuracy

$$
Acc_{selective}
=
\frac{
N_{\text{correct, non-uncertain}}
}{
N_{\text{non-uncertain}}
}
$$

还要报告：

```text
uncertain rate
```

---

# 38. Confidence calibration

如果 Agent 返回 confidence：

计算：

```text
Brier score
ECE
```

注意：

confidence 的语义需要固定。

定义为：

> confidence in the chosen native-likeness answer

对于 uncertain：

可跳过 Brier primary 或定义明确 mapping。

请在：

```text
docs/EVALUATION.md
```

写清楚。

不要含糊。

---

# 39. Aggregate metrics

至少生成：

```text
results/summary/episodes.parquet
results/summary/summary.json
results/summary/summary.csv
```

报告：

## CUA

```text
Task Completion Rate
Autonomous Completion Rate
Needs-input Rate
Timeout Rate
Artifact Success Rate
```

## Interface

```text
Observed Interface Precision
Observed Interface Recall
Observed Interface F1
Observed Interface Jaccard
```

## Diagnosis

```text
Physical plausibility:
    accuracy on committed predictions
    macro-F1
    coverage

Native likeness:
    accuracy on committed predictions
    macro-F1
    coverage
```

## Calibration

```text
Brier
ECE
```

## Pose metadata

按：

```text
P0
P1
P2
P3
P4
```

分别 breakdown。

---

# 40. Failure taxonomy

至少：

```text
F0_ENVIRONMENT
F1_FILE_NAVIGATION
F2_WRONG_EPISODE
F3_PYMOL_LAUNCH
F4_OBJECT_LOAD
F5_OBJECT_SELECTION
F6_VISUALIZATION
F7_SPATIAL_REASONING
F8_CHEMICAL_REASONING
F9_CLASSIFICATION
F10_ARTIFACT_EXPORT
F11_TIMEOUT
F12_NEEDS_HUMAN
F13_PROTOCOL_VIOLATION
F14_UNKNOWN
```

能自动识别的自动识别。

其余：

```text
UNKNOWN
```

不要让另一个 LLM 自动脑补失败原因作为 primary label。

---

# 41. Mock CUA

必须实现，不依赖真实 Ark Key。

`MockCUAClient` 至少模拟：

```text
completed
failed
needs_input
timeout
artifact available
artifact missing
```

这样：

```bash
pytest
```

在无云环境中仍然可以验证 runner。

---

# 42. 测试要求

## Unit

至少包括：

```text
test_episode_schema
test_submission_schema
test_private_leakage_detection
test_anonymization
test_interface_computation
test_interface_metrics
test_centroid_distance
test_pose_bucket
test_state_mapping
test_timeout
test_needs_input
```

---

# 43. Geometry tests

构造 toy protein-ligand coordinates。

例如：

```text
Residue A1 atom at (0, 0, 0)
Residue A2 atom at (10, 0, 0)

Ligand atom at (3.5, 0, 0)
```

4 Å interface：

```text
A1 yes
A2 no
```

测试：

```text
3.5 Å
4.0 Å
5.0 Å
```

边界包含规则必须一致。

---

# 44. Public/private leakage test

创建：

```text
public/
private/native.sdf
```

然后 staged workspace 如果通过 symlink 指向：

```text
private/native.sdf
```

必须检测并拒绝。

---

# 45. PyMOL smoke test

如果 PyMOL 可用：

自动创建 toy：

```text
protein.pdb
ligand.sdf
```

启动 headless PyMOL：

```text
load
select agent_interface
save final.pse
```

Evaluator 能从 PSE 读回 selection。

如果 CI 无 PyMOL：

标记：

```text
pytest marker = pymol
```

不能让全部测试失败。

---

# 46. Phase A 验收测试

先做：

```text
1 个 synthetic toy episode
```

不接真实 CUA：

```text
Mock CUA
```

完整：

```text
episode
→ staged workspace
→ fake submission
→ final.pse
→ evaluator
→ result.json
```

必须通过。

然后：

```text
1 个真实 Astex episode
```

人工或 scripted fake agent 完成，验证 geometry/evaluator。

最后才：

```text
1 个真实 Ark CUA episode
```

---

# 47. Phase A 正式 smoke suite

选择：

```text
5 个 Astex targets
```

每个：

```text
1 P0
1 P2
```

共：

```text
10 diagnosis episodes
```

要求 pipeline：

```text
全自动 staging
全自动 CUA launch
无人工回答
artifact collection
offline scoring
aggregate report
```

如果没有真实 API 凭证：

准备好：

```bash
python scripts/run_suite.py \
    --backend ark \
    ...
```

让用户只需完成官方登录后即可运行。

---

# 48. Phase B：AutoDock Vina

Phase A 稳定后实现。

Backend 固定：

```text
AutoDock Vina
```

不要允许 Agent 自己选 docking engine。

固定配置，例如：

```yaml
vina:
  exhaustiveness: 16
  num_modes: 10
  energy_range: 5
  seed: 20260920
  cpu: 4
```

如果具体版本参数不同，以安装版本为准。

Agent **不能修改**：

```text
seed
exhaustiveness
num_modes
cpu
scoring function
```

---

# 49. PyMOL docking panel

Phase B 增加：

```text
Docking
────────────────

Center X [ ]
Center Y [ ]
Center Z [ ]

Size X   [ ]
Size Y   [ ]
Size Z   [ ]

[Prepare]

[Run Docking]

Poses
pose_1
pose_2
...
pose_10

[Previous]
[Next]

[Select Final Pose]

[Export Selected Pose]
```

backend：

```text
PyMOL plugin
→ standard preprocessing
→ Vina
→ import poses
```

如果需要 Meeko：

统一使用 Meeko。

不要让 Agent 自己通过 shell 手搓 receptor conversion。

---

# 50. Known-pocket redocking

Primary E2E track：

Agent 获取：

```text
receptor
ligand
docking box center
docking box size
```

Box ground truth由 native ligand生成。

建议：

每轴：

$$
size_i
=
clip(
max_i-min_i+12,
18,
30
)
$$

center：

$$
c_i =
(max_i+min_i)/2
$$

这些属于 benchmark 自定义协议。

写在：

```text
docs/EVALUATION.md
```

---

# 51. Blind-pocket

只作为 secondary hard track。

不给：

```text
box
```

Agent 自己寻找 pocket。

**不要和 Known-pocket primary score 混合。**

---

# 52. Pose ranking task

支持给 Agent 多个 poses。

输出：

```python
selected_pose
```

以及可选完整 ranking。

评：

```text
Top-1 success
Top-k success
MRR
selected pose RMSD
selected pose PB-valid
```

Primary：

$$
Top1Success =
1[
RMSD_{selected}\le2Å
\land PBValid
]
$$

---

# 53. End-to-end redocking evaluator

最终至少：

```text
RMSD <= 2 Å
PB-valid
RMSD <= 2 Å AND PB-valid
centroid distance
native interface recovery F1
```

如果 ProLIF 可用：

增加：

```text
PLIF precision
PLIF recall
PLIF F1
```

但：

**ProLIF 不是 Phase A blocking dependency。**

---

# 54. Protein coordinate integrity

Fixed-receptor track 必须检测：

```text
protein 有没有被 Agent 改坐标
```

计算 receptor heavy/backbone RMSD。

如果超过：

```text
0.1 Å
```

标：

```text
protein_modified = true
```

不要一定把整条科学评分清零。

单独报告。

---

# 55. 运行日志

每个 episode 创建：

```text
results/raw/<episode_id>/
```

包括：

```text
episode.json
cua_task_metadata.json
cua_final_response.txt
submission.json
final.pse
selected_ligand.sdf         # 如有
posebusters_raw.*
evaluation.json
runner.log
```

如果 CUA 官方支持 timeline：

额外保存：

```text
cua_timeline.json
```

但必须通过真实官方接口确认。

---

# 56. 不要日志泄露 key

创建统一 redaction：

```python
redact_secrets(text)
```

至少 masking：

```text
Authorization
Bearer token
API key
ARK key
```

发生异常时也先 redact 再写日志。

---

# 57. CLI

最终至少提供：

```bash
python scripts/check_environment.py
```

输出：

```text
PyMOL ✓/✗
PoseBusters ✓/✗
RDKit ✓/✗
Vina ✓/✗
ArkCLI ✓/✗
CUA Skill ✓/✗
Ark auth ✓/✗
```

不要输出 key。

---

数据：

```bash
python scripts/prepare_data.py \
    --dataset astex \
    --input data/raw/astex
```

```bash
python scripts/prepare_data.py \
    --dataset posebusters \
    --input data/raw/posebusters
```

---

Episodes：

```bash
python scripts/build_episodes.py \
    --split dev \
    --task diagnosis
```

---

Mock run：

```bash
python scripts/run_suite.py \
    --backend mock \
    --manifest episodes/manifests/dev_diagnosis.jsonl
```

---

Ark：

```bash
python scripts/run_suite.py \
    --backend ark \
    --manifest episodes/manifests/dev_diagnosis.jsonl \
    --desktop-id <ID>
```

如果真实 CUA 不需要 desktop-id：

适配真实接口，不要强行保留。

---

评价：

```bash
python scripts/evaluate_suite.py \
    --results results/raw \
    --output results/summary
```

---

# 58. Config

`configs/benchmark.yaml`：

```yaml
benchmark:
  name: PyMolDock-CUA-Bench
  schema_version: "1.0"

dataset:
  dev: astex
  test: posebusters

interface:
  primary_cutoff_angstrom: 4.0
  sensitivity_cutoffs:
    - 3.5
    - 5.0

diagnosis:
  native_rmsd_threshold_angstrom: 2.0

runner:
  poll_interval_sec: 5
  max_retries: 3
  concurrency_per_desktop: 1
```

不要把 secrets 写 config。

---

# 59. Reproducibility

所有随机操作都要 seed。

使用单一 root seed：

```text
20260920
```

具体 episode：

```python
episode_seed = stable_hash(
    f"{root_seed}:{episode_id}"
)
```

禁止 Python 原生：

```python
hash(string)
```

用于长期 reproducibility，因为跨进程可能随机化。

使用：

```text
SHA256
```

取固定字节转换整数。

---

# 60. Version manifest

每次 run 写：

```text
run_manifest.json
```

包括：

```text
git commit
dirty status
python
OS
CUA interface metadata
ArkCLI version
PyMOL version
PoseBusters version
RDKit version
Vina version
root seed
config hash
manifest hash
```

---

# 61. README

必须包含：

## What this benchmark measures

明确区分：

```text
computer interaction
spatial molecular reasoning
scientific workflow execution
```

## What it does NOT measure

例如：

```text
不是比较不同 docking engines
不是 protein pocket prediction benchmark（除 blind track）
不是 free-form molecular QA
```

## Ground truth isolation

说明 native structures 永远不暴露给 Agent。

## Quickstart

从 mock run 开始。

## Real Ark CUA

说明：

```text
如何通过官方 ArkCLI/Skill 检查 CUA
```

不要写真实 key。

---

# 62. Documentation

`docs/EVALUATION.md` 必须清楚写公式：

Interface：

$$
P=\frac{|I_p\cap I_g|}{|I_p|}
$$

$$
R=\frac{|I_p\cap I_g|}{|I_g|}
$$

$$
F1=\frac{2PR}{P+R}
$$

$$
J=
\frac{|I_p\cap I_g|}
{|I_p\cup I_g|}
$$

Docking success：

$$
S =
1[
RMSD\le2Å
\land PBValid
]
$$

Coverage：

$$
Coverage =
\frac{N_{committed}}N
$$

Selective accuracy：

$$
Acc_{sel}
=
\frac{N_{correct,committed}}
{N_{committed}}
$$

---

# 63. 不要创建一个“综合总分”作为唯一 primary metric

Primary 输出保持多维：

```text
CUA autonomous completion
Interface F1
Physical plausibility performance
Native-like diagnosis performance
Calibration
E2E docking success
```

如确实需要 overall secondary metric：

允许 geometric mean，但：

```text
只作为 secondary
```

---

# 64. Scientific sanity checks

必须实现 dataset audit。

对于每个 candidate：

检查：

```text
protein 可解析
ligand 可解析
ligand >= 1 heavy atom
candidate 和 native molecular graph compatible（redocking 时）
坐标有限
无 NaN
interface 可计算
RMSD 可计算
```

异常：

```text
exclude_reason
```

不能静默 drop。

---

# 65. Dataset report

生成：

```text
data/dataset_report.json
data/dataset_report.csv
```

包含：

```text
targets total
targets usable
poses total
P0 count
P1 count
P2 count
P3 count
P4 count
excluded count
exclude reasons
```

dev/test 分开。

---

# 66. Benchmark contamination 防护

Agent public workspace 不允许出现：

```text
PDB ID
native ligand
crystal pose
RMSD
PB-valid label
pose bucket
docking source
docking score
method name
```

写：

```python
audit_episode_public_metadata(...)
```

对文件名和文本 metadata 检查。

---

# 67. 网络访问

Prompt 明确：

```text
Do not access external websites or databases.
```

如果 CUA 环境可以技术性关闭网络：

实现可配置：

```yaml
network_policy: disabled
```

如果官方云电脑暂不能关闭：

至少：

```text
prompt 禁止
PDB anonymization
metadata sanitization
```

并在 README 写清限制。

---

# 68. 第一阶段不要实现的东西

MVP 阶段不要浪费时间在：

```text
漂亮 dashboard
React frontend
大型数据库服务
Kubernetes
多机 scheduler
复杂 LLM judge
人工 annotation platform
```

结果：

```text
JSON/CSV/Parquet
```

够用。

---

# 69. 禁止用另一个 LLM 当 primary evaluator

例如：

```text
GPT judge 认为回答不错
```

不能作为 primary。

Primary 必须尽量 deterministic：

```text
PyMOL selection
PoseBusters
RMSD
distance geometry
structured submission
```

自由文本 reasoning：

可以保存，但不作为 primary score。

---

# 70. Phase A 完成定义

以下全部成立，Phase A 才算完成：

### Engineering

* [ ] 项目可安装
* [ ] `pytest` 通过
* [ ] `ruff check .` 通过
* [ ] mock CUA 可运行
* [ ] Ark CUA adapter 基于实际官方接口实现
* [ ] 缺认证时优雅报错，不泄露 key
* [ ] public/private leakage audit 工作

### PyMOL

* [ ] episode 可加载
* [ ] protein + candidate pose 正常显示
* [ ] `agent_interface` 可提取
* [ ] submission.json 可生成
* [ ] final.pse 可生成

### Evaluation

* [ ] interface metrics
* [ ] RMSD
* [ ] centroid distance
* [ ] PoseBusters
* [ ] pose bucket
* [ ] diagnosis classification
* [ ] selective metrics
* [ ] aggregate report

### End-to-end

* [ ] toy episode 完整跑通
* [ ] 至少 1 个真实 Astex episode 离线跑通
* [ ] 有凭证时至少 1 个真实 CUA episode 跑通
* [ ] 无凭证时 Ark integration 命令准备完毕，明确报告唯一外部 blocker

---

# 71. Phase B 完成定义

* [ ] Vina backend
* [ ] fixed parameters
* [ ] known-pocket docking box
* [ ] docking panel
* [ ] poses 可载入 PyMOL
* [ ] Agent 可选择 final pose
* [ ] selected ligand SDF 正确导出
* [ ] E2E evaluator
* [ ] 至少 1 个 Astex redocking smoke test

---

# 72. 实施顺序

严格按下面顺序做：

```text
Step 1
检查仓库 + Python 环境

Step 2
检查 ArkCLI + CUA Skill 真实接口
→ docs/CUA_INTERFACE.md

Step 3
搭工程骨架
→ schemas
→ configs
→ logging

Step 4
public/private 数据隔离
→ anonymizer
→ leakage audit

Step 5
geometry evaluator
→ interface
→ centroid
→ RMSD

Step 6
PoseBusters wrapper

Step 7
episode builder

Step 8
PyMOL diagnosis plugin

Step 9
Mock CUA

Step 10
EpisodeRunner

Step 11
artifact/evaluation/result pipeline

Step 12
toy end-to-end test

Step 13
真实 Astex offline smoke test

Step 14
真实 Ark CUA integration

Step 15
10-episode Astex diagnosis smoke suite

Step 16
Phase B Vina
```

---

# 73. 每完成一个阶段都实际运行验证

不要只看代码。

至少运行：

```bash
pytest -q
ruff check .
```

以及相关 smoke command。

发现失败：

```text
分析
修复
重新跑
```

直到通过或确认是外部 blocker。

---

# 74. Codex 工作方式

你可以自主：

```text
创建文件
修改文件
执行命令
运行测试
修 bug
重构
```

不要因为某个小错误停下来向用户报告。

对依赖问题：

优先修。

对 API 接口不确定：

读官方本地 Skill 和 `--help`。

对数据路径不存在：

实现 downloader/preparation interface，使用 fixture 完成代码验证，然后在最终报告指出需要用户放真实数据的位置。

---

# 75. 最终输出要求

完成后给出简洁但具体的工程报告。

必须包含：

## Implemented

列出实际完成模块。

## Tests

给出：

```text
pytest 通过数
ruff 状态
smoke test 状态
```

## Ark CUA

说明：

```text
发现了什么官方接口
Skill/version
真实 integration 是否跑通
若没有，唯一 blocker 是什么
```

不要展示 API key。

## Data

说明：

```text
Astex 是否准备
PoseBusters 是否准备
多少 targets / poses
```

## Example command

给出用户下一条应该运行的命令。

## Remaining

只列真正剩余的事项。

---

# 76. 最终研究目标

请始终记住：

这个项目不是：

> “写一个能调用 Vina 的脚本。”

而是：

> **构建一个严格隔离 ground truth、能够自动评分的 benchmark，用于测量火山方舟 CUA 操纵 PyMOL 完成蛋白质–配体结构分析和 docking workflow 的能力。**

最重要的第一阶段 research question 是：

$$
\boxed{
\text{CUA 是否能够在 PyMOL 中正确理解一个 protein–ligand docking pose？}
}
$$

需要分别测：

$$
\boxed{
\text{GUI / workflow competence}
}
$$

$$
\boxed{
\text{observed interface perception}
}
$$

$$
\boxed{
\text{physical plausibility reasoning}
}
$$

$$
\boxed{
\text{native-pose diagnosis}
}
$$

而不是只输出一个模糊的 overall accuracy。

现在开始。

首先：

1. 检查当前仓库；
2. 检查真实 ArkCLI / `byted-util-ark-cua` 接口；
3. 创建 `docs/CUA_INTERFACE.md`；
4. 然后按上述实施顺序持续实现、测试和修复，直到 Phase A MVP 可运行。
