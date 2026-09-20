可以。结合你给的方舟 CUA 文档和字节官方目前维护的 `byted-util-ark-cua` Skill，我会把上一版方案稍微改一下：**不要自己实现 screenshot→action 的外层 agent loop，而是把火山方舟 CUA 当成完整黑盒 Agent 来测。**

它现在的标准模式本身就是：给云电脑一次完整 objective → CUA 自己规划、看屏幕、操作 GUI → 外部只轮询任务状态和收最终结果；同时官方 CLI 已经提供 `task run`、指定 desktop、context、artifact、`model get` 等能力。([GitHub][1])

这其实比我们最开始假设的环境更适合测“字节 CUA 到底懂不懂 PyMOL”。

---

# 1. 整个系统最终应该是这个结构

```text
                        ┌─────────────────────────┐
                        │   Benchmark Controller   │
                        │      我们自己的代码       │
                        └────────────┬────────────┘
                                     │
                          task run --objective
                                     │
                                     ▼
┌────────────────────────────────────────────────────────┐
│              火山方舟 Agent Plan CUA 云电脑             │
│                                                        │
│  ┌───────────────┐                                     │
│  │ ByteDance CUA │  ← 被测试对象                       │
│  └───────┬───────┘                                     │
│          │ mouse / keyboard / vision                    │
│          ▼                                             │
│  ┌────────────────────────────┐                        │
│  │           PyMOL            │                        │
│  │                            │                        │
│  │ protein                    │                        │
│  │ ligand                     │                        │
│  │ docking poses              │                        │
│  │ PyMolDockBench plugin      │                        │
│  └──────────────┬─────────────┘                        │
│                 │                                      │
│             AutoDock Vina                              │
│                                                        │
└────────────────────────────────────────────────────────┘
                                     │
                            result / artifact
                                     │
                                     ▼
                        ┌─────────────────────────┐
                        │    Offline Evaluator     │
                        │                         │
                        │ PoseBusters              │
                        │ RMSD                     │
                        │ Interface F1             │
                        │ ProLIF                   │
                        │ CUA task success         │
                        └─────────────────────────┘
```

最重要的原则是：

$$
\boxed{\text{Controller 不帮 CUA 做 planning}}
$$

比如绝对不要外部先生成：

```text
Step 1 open PyMOL
Step 2 load receptor
Step 3 click plugin
Step 4 run Vina
...
```

再逐步喂给它。

你真正想测的是：

> 给字节 CUA 一个科研任务，它能不能自己理解任务、找到 PyMOL、理解 3D 结构、操作 docking 软件、判断结果。

官方 Skill 本身也明确建议 `delegate` 时保留用户原始 objective，不在外层替它拆解任务。([GitHub][1])

---

# 2. 项目目录我建议直接这样建

```text
pymoldock-cua-bench/
│
├── README.md
├── pyproject.toml
├── uv.lock
│
├── configs/
│   ├── benchmark.yaml
│   ├── ark_cua.yaml
│   ├── vina.yaml
│   └── difficulty.yaml
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
│   └── prompts/
│
├── pymol_plugin/
│   └── pymoldockbench/
│       ├── __init__.py
│       ├── plugin.py
│       ├── docking_backend.py
│       ├── episode_loader.py
│       ├── answer_panel.py
│       └── export.py
│
├── bench/
│   ├── ark_cua/
│   │   ├── client.py
│   │   ├── models.py
│   │   └── errors.py
│   │
│   ├── data/
│   │   ├── prepare_posebusters.py
│   │   ├── prepare_astex.py
│   │   ├── anonymize.py
│   │   └── make_decoys.py
│   │
│   ├── episodes/
│   │   ├── build.py
│   │   └── schemas.py
│   │
│   ├── runner/
│   │   ├── run_episode.py
│   │   ├── run_suite.py
│   │   └── collect_artifacts.py
│   │
│   └── eval/
│       ├── posebusters_eval.py
│       ├── rmsd.py
│       ├── interface.py
│       ├── prolif_eval.py
│       ├── diagnosis.py
│       └── aggregate.py
│
├── scripts/
│   ├── bootstrap_cua_desktop.sh
│   ├── build_dataset.sh
│   ├── run_dev.sh
│   └── run_test.sh
│
└── results/
    ├── raw/
    ├── episodes/
    └── summary/
```

---

# 3. 第一件事：CUA 的 API Key 不进代码

这点直接按照字节官方 Skill 的方式来。

官方目前提供：

```bash
python3 scripts/cua.py auth status

python3 scripts/cua.py auth login --manual
```

手动登录时 API Key 走本地隐藏输入，官方明确要求**不要把 Key 放进命令参数、环境变量、日志或聊天内容**；也可以通过已有 `arkcli` profile 自动发现符合条件的 Agent Plan 身份。([GitHub][2])

所以不要写这种东西：

```python
ARK_API_KEY = "xxx"
```

也不要：

```bash
export ARK_API_KEY=xxx
```

benchmark runner 只调用：

```bash
python3 cua.py auth status
```

验证已经认证。

---

# 4. CUA 适配层只封装官方 CLI

我反而不建议第一版逆向它底层 HTTP API。

直接把官方：

```text
byted-util-ark-cua/scripts/cua.py
```

当 SDK。

因为现在官方 Skill 对：

* desktop 生命周期
* context
* credential
* artifact
* task 状态
* retry
* auth

已经封装好了。([GitHub][2])

例如：

```python
# bench/ark_cua/client.py

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class ArkCUAError(RuntimeError):
    pass


class ArkCUAClient:

    def __init__(self, skill_dir: str):
        self.skill_dir = Path(skill_dir)
        self.cli = self.skill_dir / "scripts" / "cua.py"

        if not self.cli.exists():
            raise FileNotFoundError(self.cli)

    def _run(
        self,
        args: list[str],
        timeout: int | None = None,
    ) -> dict[str, Any]:

        cmd = [
            "python3",
            str(self.cli),
            *args,
        ]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        stdout = proc.stdout.strip()

        try:
            result = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise ArkCUAError(
                f"Invalid CUA response:\n{stdout}\n{proc.stderr}"
            ) from exc

        if not result.get("ok", False):
            error = result.get("error", {})
            raise ArkCUAError(
                f"{error.get('code')}: "
                f"{error.get('message', '')}"
            )

        return result
```

然后：

```python
    def auth_status(self):
        return self._run([
            "auth",
            "status",
        ])

    def desktops(self):
        return self._run([
            "desktop",
            "list",
        ])

    def model_info(self):
        return self._run([
            "model",
            "get",
        ])
```

这里的 `model get` 特别重要。

---

# 5. 每次正式 benchmark 前一定保存 `model get`

因为你测的是：

> 字节 CUA 的能力。

服务端 CUA 模型以后很可能升级。

所以每个 benchmark run 必须记录：

```json
{
  "benchmark_version": "0.1.0",
  "timestamp": "...",

  "ark_cua": {
    "model_info": "...",
    "skill_version": "1.0.7",
    "skill_git_commit": "..."
  },

  "environment": {
    "pymol": "...",
    "vina": "...",
    "posebusters": "...",
    "rdkit": "...",
    "prolif": "..."
  }
}
```

官方 CLI 专门提供了：

```bash
cua.py model get
```

做只读模型信息查询。([GitHub][2])

否则三个月以后：

```text
ByteDance CUA 72.3%
```

基本无法复现。

---

# 6. 不用 `delegate` 跑 benchmark，优先用 `task run`

普通用户请求官方推荐：

```bash
delegate --objective "..."
```

但 benchmark 我建议明确指定 desktop：

```bash
python3 cua.py task run \
    --desktop "$DESKTOP_ID" \
    --title "PB_T3_00187" \
    --objective "$PROMPT" \
    --wait-ms 0
```

官方 CLI 支持：

```text
task run
task status
task result
task answer
task cancel
```

以及：

```text
context create
context show
timeline show
```

([GitHub][2])

这样所有 episode 都固定在：

```text
同一个经过标准化配置的 cloud desktop
```

避免硬件和软件环境变化。

---

# 7. 每个 episode 必须是全新的 task

**绝对不要使用：**

```bash
task continue
```

去接着上一条 episode。

也不要复用 benchmark context。

因为那会出现：

```text
Episode 1
    ↓
Agent 学会 benchmark 规则
    ↓
Episode 2
    ↓
隐式历史信息
```

测试集之间不独立。

所以：

```text
Episode 0001 → new task
Episode 0002 → new task
Episode 0003 → new task
```

只复用：

```text
desktop
```

不复用：

```text
context
```

---

# 8. 更重要：如果 CUA 问问题，直接算失败

官方 CUA 支持：

```text
needs_input
```

此时通常用户可以：

```bash
task answer
```

回答。官方文档还明确说目前没有禁用 CUA user-question 的选项。([GitHub][2])

但 benchmark 里：

**绝不能有人类回答。**

否则：

```text
CUA：应该选哪个 ligand？

Evaluator：选 ligand.sdf

CUA：好的
```

这已经不是 autonomous benchmark。

所以定义：

```text
needs_input
→ episode status = HUMAN_ASSIST_REQUIRED
→ task success = 0
```

但保留其他 partial metrics。

---

# 9. CUA Runner 状态机

基本可以这么写：

```python
from enum import Enum


class EpisodeStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    NEEDS_INPUT = "needs_input"
    ACTIVE_CONFLICT = "active_conflict"
```

运行：

```python
def run_episode(
    client: ArkCUAClient,
    desktop_id: str,
    objective: str,
):

    ret = client._run([
        "task",
        "run",
        "--desktop",
        desktop_id,
        "--objective",
        objective,
        "--wait-ms",
        "0",
    ])

    data = ret["data"]

    task_id = (
        data.get("task_id")
        or data.get("invocation_id")
        or data.get("id")
    )

    if not task_id:
        raise RuntimeError("No task id")

    while True:

        status = client._run([
            "task",
            "status",
            "--task-id",
            task_id,
        ])

        data = status["data"]
        outcome = data.get("outcome")

        if outcome == "completed":
            return collect_result(client, task_id)

        if outcome == "needs_input":
            return {
                "status": "needs_input",
                "task_id": task_id,
            }

        if outcome in {
            "failed",
            "cancelled",
        }:
            return {
                "status": outcome,
                "task_id": task_id,
                "raw": status,
            }

        time.sleep(5)
```

实际实现时要兼容官方返回的 `next.command`，因为官方建议根据它继续推进任务，而不是自己猜下一步调用。([GitHub][1])

---

# 10. 同一 desktop 不并发跑

这一点非常重要。

一台 CUA 云电脑：

```text
Episode A
Episode B
```

不能同时操作 PyMOL。

否则两只 agent 同时：

```text
点鼠标
关闭窗口
输入命令
```

benchmark 直接坏掉。

因此：

```yaml
runner:
  concurrency_per_desktop: 1
```

如果以后有：

```text
desktop_1
desktop_2
desktop_3
desktop_4
```

才能：

```text
4-way parallel
```

官方相关云电脑说明同样建议同一实例同时只运行一个云电脑任务，避免资源冲突。

---

# 11. 我会把 PyMOL 环境做成一个“科研任务沙箱”

云电脑提前配置好：

```text
PyMOL
AutoDock Vina
Meeko
RDKit

PyMolDockBench Plugin
```

而：

```text
PoseBusters
ProLIF
ground truth
native ligand
evaluation code
```

**绝对不要装在 CUA 可访问目录里。**

Evaluator 跑在：

```text
benchmark controller machine
```

不跑在 CUA desktop。

---

# 12. Public / Private 数据严格分离

比如：

```text
PB_00187/
```

CUA desktop 只能看到：

```text
episodes/PB_00187/

    receptor.pdb
    ligand.sdf
    candidate_pose.sdf
    episode.txt
```

Evaluator 才有：

```text
private/PB_00187/

    native_ligand.sdf
    native_complex.pdb
    interface_native.json
    prolif_native.json
    pose_labels.json
```

PoseBusters 官方本身就支持：

```bash
bust ligand_pred.sdf \
    -l mol_true.sdf \
    -p protein.pdb
```

这种 redocking 检查。([GitHub][3])

因此 ground truth 完全没理由放进 CUA 环境。

---

# 13. 数据 anonymization

原本：

```text
7MYU
```

改：

```text
PB_00187
```

蛋白文件里删除：

```text
HEADER
TITLE
DBREF
SOURCE
COMPND
REMARK
```

ligand：

```text
compound name
PDB ID
database identifiers
```

也全部清掉。

建议再给整个复合物做一个 deterministic rigid transformation：

$$
x'_i = Rx_i+t
$$

其中：

$$
R\in SO(3)
$$

来自：

```python
seed = hash(episode_id)
```

这不会改变任何：

* 距离
* 角度
* interface
* RMSD after alignment
* docking geometry

但会让：

```text
原 PDB 的绝对坐标
```

完全失效。

---

# 14. 我甚至建议隐藏真实 ligand residue name

比如：

```text
ZR7
STI
ATP
```

这种名字可能直接暴露是什么 ligand。

统一：

```text
LIG
```

当然元素、键、原子类型必须保持。

这是 benchmark，测结构理解，不是：

> 模型认不认识某个药。

---

# 15. PyMolDockBench Plugin

这个插件很重要。

因为“PyMOL 做 docking”严格说 PyMOL 本身不负责 docking，所以需要一个固定 backend。

我建议：

```text
PyMOL GUI
   ↓
PyMolDockBench plugin
   ↓
AutoDock Vina
```

不要让 CUA：

```text
自己上网找 docking 软件
自己装插件
自己选择 docking engine
```

否则变量太多。

---

# 16. Plugin UI 我建议就做这几个区域

```text
┌──────────────────────────────────┐
│ PyMolDockBench                   │
├──────────────────────────────────┤
│ Episode                          │
│ PB_00187                         │
│                                  │
│ Receptor: receptor               │
│ Ligand:   ligand                 │
├──────────────────────────────────┤
│ Docking box                      │
│                                  │
│ Center X [   ]                   │
│ Center Y [   ]                   │
│ Center Z [   ]                   │
│                                  │
│ Size X   [   ]                   │
│ Size Y   [   ]                   │
│ Size Z   [   ]                   │
│                                  │
│ [Prepare]                        │
│ [Run docking]                    │
├──────────────────────────────────┤
│ Poses                            │
│                                  │
│ pose_1                           │
│ pose_2                           │
│ pose_3                           │
│ ...                              │
│                                  │
│ [Previous] [Next]                │
│ [Select final pose]              │
├──────────────────────────────────┤
│ Diagnosis                        │
│                                  │
│ Physical plausibility            │
│ [Valid ▼]                        │
│                                  │
│ Correct binding mode             │
│ [Likely correct ▼]               │
│                                  │
│ Confidence [0.00]                │
│                                  │
│ Failure mode                     │
│ □ clash                          │
│ □ wrong orientation              │
│ □ wrong pocket                   │
│ □ poor complementarity           │
│ □ lost interactions              │
│                                  │
│ [Submit]                         │
└──────────────────────────────────┘
```

非常适合 CUA。

---

# 17. Vina 的科研参数锁死

Agent 不能修改：

```yaml
vina:
  exhaustiveness: 16
  num_modes: 10
  energy_range: 5
  seed: 20260920
  cpu: 4
```

否则 Agent A：

```text
exhaustiveness=8
```

Agent B：

```text
exhaustiveness=128
```

不公平。

CUA 可以操作：

```text
box
run
poses
selection
```

但不能改 Vina budget。

---

# 18. Known-pocket 主任务

这应该是主要 E2E benchmark。

episode：

```json
{
  "episode_id": "PB_00187_E2E",

  "task": "redocking",

  "files": {
    "receptor": "receptor.pdb",
    "ligand": "ligand.sdf"
  },

  "docking_box": {
    "center": [
      21.32,
      -7.81,
      34.15
    ],

    "size": [
      22.0,
      22.0,
      20.0
    ]
  }
}
```

这里 box 是 evaluator 从 native ligand 生成后公开给 Agent 的。

这样测的是：

$$
\text{Docking Workflow Capability}
$$

而不是 pocket detection。

---

# 19. Blind-pocket 单独作为 Hard Track

不给：

```text
center
size
```

只给：

```text
protein
ligand
```

CUA 必须：

```text
观察蛋白
↓
找 cavity
↓
设 box
↓
docking
```

但是不要把它和主分数混一起。

因为这里其实同时在测：

$$
\text{Pocket Prediction}
+
\text{Docking}
+
\text{Computer Use}.
$$

---

# 20. Pose diagnosis 才是这个 benchmark 最有价值的任务

我建议第一篇真正重点测这个。

给 Agent：

```text
PyMOL
protein
candidate ligand pose
```

它不知道 native。

要求：

```text
1. 找界面 residues
2. 找主要 interaction
3. 判断有没有 steric clash
4. 判断 pose 是否物理合理
5. 判断是否有充分证据认为这是正确 binding mode
6. 给 confidence
```

---

# 21. Pose diagnosis 的 objective 最好固定

比如：

```text
You are evaluating one protein–ligand docking result in PyMOL.

Open the episode PB_00187 located in the PyMolDockBench
workspace and inspect the protein–ligand complex using PyMOL.

Your task is to:

1. inspect the ligand-binding interface;
2. identify the protein residues that directly interact with the ligand;
3. identify important protein–ligand interactions or obvious steric conflicts;
4. judge whether the current ligand pose is physically plausible;
5. judge whether the available structural evidence supports this being the
   correct binding mode;
6. report your confidence.

Create a PyMOL selection named `agent_interface` containing the interface
residues.

Do not access external websites or external databases.
Do not search for the structure by identity.
Do not inspect any other benchmark episode.

Finish by submitting the result through the PyMolDockBench panel.
```

实际论文里最好把 prompt 固定公开。

这里虽然 objective 是英文更标准，但你的代码仓库里也可以额外放中文注释。

---

# 22. 为什么让它自己打开 episode

因为你主要测的就是 **CUA**。

所以：

```text
找到 PyMOL
打开 episode
找到 ligand
zoom
rotate
操作
```

这些都应该计入能力。

如果以后要做纯 scientific reasoning ablation，可以另开：

```text
T3-preloaded
```

提前把 PyMOL scene 打开。

---

# 23. 最终结果不要依赖自然语言解析

这是非常关键的一点。

不要最后让 CUA说：

> It looks pretty good although there may be...

然后我们再用另一个 LLM judge。

尽量避免。

让 PyMolDockBench plugin 保存：

```json
{
  "episode_id": "PB_00187_T3",

  "physical_plausibility": "valid",

  "native_likeness": "uncertain",

  "confidence": 0.62,

  "failure_modes": [
    "wrong_orientation"
  ],

  "interface_selection": "agent_interface"
}
```

这样 scorer 完全 deterministic。

---

# 24. `agent_interface` 从 final PyMOL session 提取

Agent 最后保存：

```text
final.pse
```

然后 evaluator：

```python
from pymol import cmd

cmd.load("final.pse")

model = cmd.get_model(
    "agent_interface and polymer.protein"
)

residues = set()

for atom in model.atom:
    residues.add(
        (
            atom.chain,
            atom.resi,
            atom.resn,
        )
    )
```

因此不依赖 Agent 自己打字列 residues。

---

# 25. 结果 artifact 怎么拿回来

官方 CUA CLI 提供：

```bash
artifact list --task-id <id>

artifact save \
    --artifact-id <id> \
    --task-id <id> \
    --output <path>
```

并且明确支持任务产物保存。([GitHub][2])

所以 objective 最后要求：

```text
Export:

submission.json
final.pse
```

E2E docking 再加：

```text
selected_ligand.sdf
vina.log
```

runner：

```python
artifacts = client._run([
    "artifact",
    "list",
    "--task-id",
    task_id,
])
```

下载到：

```text
results/raw/PB_00187/
```

---

# 26. 不能只相信 CUA final text

官方 Skill 明确说：

只有：

```text
outcome == completed
```

时，`result.text` 才算终态结果。([GitHub][1])

即便显示：

```text
I've successfully docked the ligand...
```

如果状态还是：

```text
in_progress
```

都不能算完成。

你的 runner 一定按照 task state，而不是自然语言判断。

---

# 27. Episode schema

建议直接 Pydantic：

```python
from typing import Literal
from pydantic import BaseModel


class DockingBox(BaseModel):
    center: tuple[float, float, float]
    size: tuple[float, float, float]


class Episode(BaseModel):

    episode_id: str

    split: Literal[
        "dev",
        "test",
    ]

    task: Literal[
        "gui",
        "interface",
        "interaction",
        "diagnosis",
        "ranking",
        "redocking",
    ]

    difficulty: Literal[
        "easy",
        "medium",
        "hard",
    ]

    public_dir: str

    docking_box: DockingBox | None = None

    max_walltime_sec: int

    expected_artifacts: list[str]

    prompt_template: str
```

---

# 28. Ground truth schema

```python
class PoseGroundTruth(BaseModel):

    native_ligand_path: str

    ligand_rmsd: float

    centroid_rmsd: float

    pb_valid: bool

    native_interface: list[str]

    candidate_interface: list[str]

    interface_recovery_f1: float

    prolif_native: dict

    prolif_candidate: dict

    pose_bucket: Literal[
        "P0",
        "P1",
        "P2",
        "P3",
        "P4",
    ]
```

这个文件：

```text
永远不进入 CUA desktop
```

---

# 29. PoseBench 用来生成真实 hard negatives

这一块直接利用 PoseBench。

PoseBench 官方目前已经支持 PoseBusters Benchmark 上的：

* DiffDock
* FABind
* AutoDock Vina
* DynamicBind
* NeuralPLexer
* FlowDock
* RoseTTAFold-All-Atom
* 其他方法

并提供预处理 PoseBusters 数据。([GitHub][4])

所以 candidate pool：

```text
native
Vina poses
DiffDock poses
FABind poses
DynamicBind poses
...
```

然后脱掉：

```text
method identity
docking score
rank
```

Agent 完全不知道 pose 来自哪个方法。

---

# 30. 注意 PoseBench 版本

这一点必须写进代码。

PoseBench 官方自己标注：

> v1.0.0 的 ligand scoring 存在 bug，v1.1.0 已修复，并导致若干方法指标平均下降约 15%。

因此：

```text
禁止基于 PoseBench v1.0.0 的旧 score 直接构造标签。
```

要么：

```text
PoseBench >= 1.1.0
```

要么更保险：

**全部 prediction 自己重新跑 scorer。**

([GitHub][4])

我更推荐后者。

---

# 31. 所有 pose 重新离线评分

每个 candidate 都算：

$$
RMSD_{\text{ligand}}
$$

$$
RMSD_{\text{centroid}}
$$

$$
PBValid
$$

$$
F1_{\text{interface}}
$$

$$
F1_{\text{PLIF}}
$$

统一得到：

```text
pose_database.parquet
```

例如：

| episode | source   | RMSD | centroid | PB | interface F1 |
| ------- | -------- | ---: | -------: | -: | -----------: |
| PB001   | Vina     | 0.91 |     0.22 |  1 |          .94 |
| PB001   | DiffDock |  3.7 |     0.81 |  1 |          .71 |
| PB001   | Vina     |  7.8 |      6.2 |  0 |          .12 |

---

# 32. Pose bucket 重新严格定义

我会用：

### P0 — 正确且物理合理

$$
RMSD \le 2Å
$$

且：

$$
PBValid=1.
$$

---

### P1 — native-like 但物理不合理

$$
RMSD\le2Å
$$

但：

$$
PBValid=0.
$$

---

### P2 — 正确 pocket、错误 pose

例如：

$$
RMSD>2Å
$$

且：

$$
d_{\mathrm{centroid}}\le2.5Å
$$

且：

$$
F1_{\mathrm{interface}}\ge0.5.
$$

这是**最重要的 hard negative**。

---

### P3 — 邻近错误 pocket/sub-pocket

$$
2.5<
d_{\mathrm{centroid}}
\le6Å.
$$

且 ligand 仍有实质 protein contact。

---

### P4 — gross failure

例如：

$$
d_{\mathrm{centroid}}>6Å
$$

或巨大 clash / ligand floating。

---

# 33. 最值得测的是 P0 vs P2

因为 P4 太简单。

CUA 看一眼：

```text
ligand 在蛋白外面
```

就知道错。

真正有挑战的是：

```text
ligand 就在正确 binding pocket
```

但是：

```text
翻转了
官能团朝错方向
失去关键 H-bond
疏水端暴露
形成 clash
```

这才是真正测试 3D structural reasoning。

所以最终 diagnosis set 我建议：

```text
P0     25%
P1     15%
P2     35%
P3     15%
P4     10%
```

刻意提高 P2 比例。

---

# 34. Interface scorer

定义：

$$
I=
\left\{
r:
\min_{a\in r,b\in L}
d(a,b)\le4Å
\right\}.
$$

然后：

```python
def interface_metrics(pred, gt):

    intersection = pred & gt

    precision = (
        len(intersection) / len(pred)
        if pred else 0
    )

    recall = (
        len(intersection) / len(gt)
        if gt else 0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if precision + recall
        else 0
    )

    jaccard = (
        len(intersection) / len(pred | gt)
        if pred | gt
        else 1
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "jaccard": jaccard,
    }
```

这里可以算两个：

```text
Agent vs current-pose interface

Agent vs native interface
```

前者测：

> 看懂当前画面了吗？

后者测：

> 当前 pose 是否恢复正确界面？

---

# 35. 一个非常关键的指标分解

假设：

```text
Agent Interface F1 vs displayed pose = 0.94
```

但：

```text
displayed pose vs native Interface F1 = 0.31
```

说明：

> CUA 把屏幕看懂了，但是这个 docking pose 本身错了。

反过来：

```text
candidate-native interface F1 = 0.90
Agent interface F1 = 0.30
```

说明：

> docking 本身很好，但 CUA 没理解结构。

这个分解对 Agent benchmark 非常重要。

---

# 36. PoseBusters scorer

直接调用官方：

```python
import subprocess
import pandas as pd
from pathlib import Path


def run_posebusters(
    pred: Path,
    native: Path,
    protein: Path,
    output_csv: Path,
):

    subprocess.run(
        [
            "bust",
            str(pred),
            "-l",
            str(native),
            "-p",
            str(protein),
            "--outfmt",
            "csv",
            "--out",
            str(output_csv),
        ],
        check=True,
    )

    return pd.read_csv(output_csv)
```

具体参数按照你最终 pin 的 PoseBusters 版本适配。

官方支持 redocked ligand + true ligand + receptor 这种调用方式。([GitHub][5])

---

# 37. CUA 特有的 benchmark metric

除了科学指标，还要加：

### Autonomy

```text
completed_without_human
```

### User-question rate

$$
Q=
\frac{\#needs\_input}{N}
$$

### Task failure

```text
CUA crash
application error
timeout
wrong file
wrong episode
artifact missing
```

### Workflow completion

```text
PyMOL opened
episode loaded
interface created
answer submitted
artifact exported
```

---

# 38. 最终每条结果应该长这样

```json
{
  "episode_id": "PB_00187_T3_P2",

  "cua": {
    "outcome": "completed",
    "needs_human": false,
    "runtime_sec": 167.3
  },

  "agent_answer": {
    "physical_plausibility": "valid",
    "native_likeness": "likely_incorrect",
    "confidence": 0.81,

    "failure_modes": [
      "wrong_orientation",
      "lost_key_interactions"
    ]
  },

  "scientific_score": {
    "agent_observed_interface_f1": 0.91,
    "native_interface_recovery_f1": 0.68,
    "interaction_f1": 0.73,

    "pose_rmsd": 4.18,
    "centroid_rmsd": 0.77,
    "pb_valid": true
  },

  "classification": {
    "physical_plausibility_correct": true,
    "native_likeness_correct": true
  }
}
```

---

# 39. 对“正确 docking 判断”的评分我建议三层

不要只有一个 Accuracy。

### Level A：物理合理性

GT：

$$
PBValid
$$

Agent：

```text
valid / invalid / uncertain
```

---

### Level B：native-like

GT：

$$
RMSD\le2Å
$$

Agent：

```text
likely_correct
likely_incorrect
uncertain
```

---

### Level C：完整 docking success

GT：

$$
RMSD\le2Å
\land PBValid.
$$

这是最终 docking correctness。

---

# 40. `uncertain` 要按 selective prediction 评价

不能直接当错。

例如定义 coverage：

$$
Coverage =
\frac{N_{\text{non-uncertain}}}{N}.
$$

Selective accuracy：

$$
Acc_{selective}
=
\frac{
N_{\text{correct,non-uncertain}}
}{
N_{\text{non-uncertain}}
}.
$$

结果可能：

```text
Coverage       72%
Selective Acc  89%
```

说明 CUA：

> 在它愿意下判断的时候很准，但 28% 会保守拒答。

这比简单 64% accuracy 信息丰富很多。

---

# 41. Confidence 做 Brier Score

如果：

```text
confidence ∈ [0,1]
```

计算：

$$
Brier=
\frac1N
\sum_i
(p_i-y_i)^2.
$$

这样能测：

> 字节 CUA 的科学判断是否校准。

这个我觉得很值得写进论文。

---

# 42. 对 ByteDance CUA 最有价值的 ablation

我会直接做四个 setting。

| Track | PyMOL     | 命令行              | Docking | 测试能力          |
| ----- | --------- | ---------------- | ------- | ------------- |
| V1    | 已打开 scene | 禁止               | 无       | 纯视觉结构理解       |
| V2    | 已打开 scene | PyMOL command 可用 | 无       | 软件辅助结构分析      |
| V3    | 自己打开数据    | 可用               | 无       | CUA+科研分析      |
| V4    | 自己打开数据    | 可用               | Vina    | 完整科研 workflow |

这样能回答一个很好的问题：

> 字节 CUA 的瓶颈究竟是 GUI perception、科学 reasoning，还是长流程执行？

---

# 43. 我特别推荐 V1：视觉约束任务

如果你确实想回答：

> “CUA 能否**看** PyMOL 判断 docking interface？”

那必须有这个 track。

限制：

```text
禁止使用：

select ... within ...
around
distance-based selections
Python API
external scripts
```

只允许：

```text
鼠标
旋转
缩放
PyMOL visual representations
GUI measurement
```

否则它一句：

```text
select agent_interface,
    byres (polymer within 4 of ligand)
```

Interface F1 基本接近 1。

那测的是：

> 会不会写 PyMOL selection language

而不是：

> 会不会看 3D molecular interface。

---

# 44. V2 则刻意允许这些工具

V2：

```text
select
distance
show
hide
label
zoom
orient
```

全部允许。

这个其实更加符合真正科研 Agent：

> 不要求模型只靠眼睛，而是允许它善用科学软件。

V1 和 V2 差值：

$$
\Delta =
Score_{tool}-Score_{vision}
$$

就能量化：

> PyMOL tools 对 Agent scientific reasoning 增益多大。

---

# 45. E2E docking objective

正式版可以这样：

```text
Open PyMOL and load benchmark episode PB_00187.

Using the PyMolDockBench docking interface and the provided
docking-box specification, perform protein–ligand docking.

Inspect all generated poses in PyMOL.

Select the pose that you judge best represents the ligand binding mode.

For the selected pose:

- inspect the binding interface;
- create a selection named `agent_interface`;
- assess physical plausibility;
- identify any apparent docking problems.

Submit the result through the benchmark panel and export the
selected ligand pose.

Do not use external websites, databases, or information from other
benchmark episodes.

Complete the task without asking the user for assistance.
```

最下面一句不能保证 CUA 一定不问——官方目前没有 suppress questions 参数——但能降低发生率；真正发生时仍按 `needs_input` 记分。([GitHub][2])

---

# 46. 推荐测试顺序

第一版不要直接 308×很多任务。

我会实际这样跑：

```text
Stage 0
5 个 Astex
只测试：
CUA → 打开 PyMOL → load → export
```

确认云电脑环境没问题。

然后：

```text
Stage 1
10 Astex × 4 pose
= 40 diagnosis episodes
```

主要调：

```text
prompt
plugin
artifact
runner
```

然后：

```text
Stage 2
Astex 85
```

冻结 benchmark。

最后：

```text
Stage 3
PoseBusters 308
```

test set 一次跑完。

---

# 47. 第一篇结果甚至不一定要马上做 2400 个

我建议 MVP：

### Development

```text
Astex 85
```

### Test

PoseBusters 308 中：

```text
100 targets
```

每个：

```text
P0 × 1
P2 × 2
P3 × 1
```

即：

$$
100\times4=400
$$

个 diagnosis episode。

再加：

```text
100 个 E2E docking
```

总共：

$$
500
$$

条。

这已经足够看 CUA 能力分布。

之后扩到 308。

---

# 48. 最值得优先实现的代码顺序

我会按这个 dependency graph：

```text
01 ArkCUAClient
        ↓
02 Task runner
        ↓
03 PyMOL 环境
        ↓
04 PyMolDockBench minimal plugin
        ↓
05 PoseBusters data sanitizer
        ↓
06 Pose diagnosis episode builder
        ↓
07 artifact collector
        ↓
08 interface evaluator
        ↓
09 PoseBusters evaluator
        ↓
10 aggregate metrics
        ↓
11 Vina E2E
```

注意：

**Vina 可以很晚再接。**

先把：

$$
\boxed{
\text{CUA + PyMOL + pose diagnosis}
}
$$

跑通。

这是最容易得到有价值结果的部分。

---

# 49. 第一版 Plugin 也不用做太复杂

MVP 甚至只需要：

```text
Load Episode

Physical:
○ valid
○ invalid
○ uncertain

Native-like:
○ likely correct
○ likely incorrect
○ uncertain

Confidence:
[      ]

Failure:
□ clash
□ wrong orientation
□ wrong pocket
□ missing interactions

[Submit]

[Export Session]
```

docking panel 第二阶段再加。

---

# 50. 我建议你最终论文/汇报里把它定义成三个能力维度

不是笼统说：

> Computer Use Agent 在 PyMOL 上 62%。

而是：

$$
\boxed{
\text{Computer Interaction}
}
$$

$$
\boxed{
\text{Molecular Spatial Reasoning}
}
$$

$$
\boxed{
\text{Scientific Workflow Execution}
}
$$

例如最后可能得到：

```text
CUA task completion                93.4%

Observed interface F1             86.2%

Interaction recognition F1        67.8%

Physical validity classification  79.1%

Native-pose diagnosis             61.3%

Pose ranking Top-1                48.6%

End-to-end docking success        35.7%
```

这种结果非常有解释力。

---

## 现在最应该先做的版本

如果你准备马上丢给 Codex 开发，我会让它先只实现下面这个闭环：

```text
PoseBusters / Astex
        ↓
prepare candidate complex
        ↓
episode.json
        ↓
CUA task run
        ↓
打开 PyMOL
        ↓
观察 protein-ligand complex
        ↓
创建 agent_interface
        ↓
Plugin 中判断
        ↓
submission.json + final.pse
        ↓
artifact save
        ↓
offline evaluator
        ↓
Interface F1
PB-valid accuracy
RMSD correctness accuracy
CUA success
```

**先不做 Vina。**

因为只要这个闭环跑通，你已经有一个完整的：

> **ByteDance CUA × PyMOL scientific reasoning benchmark**

然后第二阶段加 Vina，就自然升级成：

> **ByteDance CUA × end-to-end protein–ligand docking benchmark**。

另外一个很实用的点是，官方 CUA Skill 已经提供 `timeline show`、artifact、固定 desktop、model info 等接口，这意味着我们后面可以把**CUA 运行轨迹和错误分类**也纳入 evaluator，而不用自己造一套屏幕录制/任务状态系统。([GitHub][2])

如果你下一步准备直接交给 Codex 开工，我建议我接下来继续给你写一份**“给 Codex 的完整 implementation prompt”**：把上述仓库结构、每个 Python 文件的职责、接口签名、单元测试、PyMOL Plugin UI、CUA runner、PoseBusters scorer 和第一阶段验收标准全部写死。你基本可以把那一整段直接丢给 Codex，让它自动迭代实现。

[1]: https://github.com/bytedance/agentkit-samples/blob/main/skills/byted-util-ark-cua/SKILL.md "agentkit-samples/skills/byted-util-ark-cua/SKILL.md at main · bytedance/agentkit-samples · GitHub"
[2]: https://github.com/bytedance/agentkit-samples/blob/main/skills/byted-util-ark-cua/references/commands.md "agentkit-samples/skills/byted-util-ark-cua/references/commands.md at main · bytedance/agentkit-samples · GitHub"
[3]: https://github.com/maabuu/posebusters/blob/main/README.md?utm_source=chatgpt.com "posebusters/README.md at main · maabuu/posebusters · GitHub"
[4]: https://github.com/BioinfoMachineLearning/PoseBench?utm_source=chatgpt.com "GitHub - BioinfoMachineLearning/PoseBench: Comprehensive benchmarking of protein-ligand structure prediction methods. (Nature Machine Intelligence) · GitHub"
[5]: https://github.com/maabuu/posebusters "GitHub - maabuu/posebusters: Plausibility checks for generated molecule poses. · GitHub"
