
<div align="right">

[English](README.en-US.md) | **中文**

</div>

# arXiv 每日论文推送机器人（飞书）

<img src="assets/arxivbot-logo.png" alt="arXiv Bot Logo" width="200">

每天自动帮你抓取 arXiv 上最新发表的论文，用 AI 翻译成中文并提炼要点，然后推送到你的飞书群里。

**适合人群**：对 AI 和编程完全零基础，只想每天收到论文推送的研究者和学生。

**你只需要做三件事**：
1. 有一个 GitHub 账号
2. 申请一个 LLM API Key（以 DeepSeek 为例，本文后面有详细教程）
3. 有一个飞书群，添加一个机器人

---

## 目录

- [功能介绍](#功能介绍)
- [五分钟快速上手（推荐）](#五分钟快速上手推荐)
  - [第一步：准备工作](#第一步准备工作)
  - [第二步：配置 GitHub Secrets](#第二步配置-github-secrets)
  - [第三步：运行测试](#第三步运行测试)
- [如何申请 LLM API Key（DeepSeek 为例）](#如何申请-llm-api-keydeepseek-为例)
- [配置说明](#配置说明)
  - [环境变量一览](#环境变量一览)
  - [自定义论文搜索范围](#自定义论文搜索范围)
- [代码贡献规范](#代码贡献规范)
- [许可证](#许可证)

---

## 功能介绍

- **每日自动推送**：每天早上自动抓取前一天新发表的论文
- **智能筛选**：按学科分类和关键词筛选你感兴趣的论文
- **AI 翻译总结**：用大模型把标题和摘要翻译成中文，并提炼要点
- **飞书卡片推送**：精美的交互式卡片，点击直接跳转到论文原文
- **零服务器成本**：完全运行在 GitHub Actions 上，公开仓库免费使用

---

## 五分钟快速上手（推荐）

> **完全不用写代码，也不用懂编程**，跟着下面的步骤点几下就好了。

### 第一步：准备工作

在开始之前，你需要准备好以下几样东西：

1. **一个 GitHub 账号**（如果没有，去 https://github.com 注册一个，免费的）
2. **一个 LLM API Key**（推荐 DeepSeek，便宜又好用，申请方法见下文）
3. **一个飞书群 + 飞书机器人 Webhook 地址**
   - 在飞书群里点击「群设置」→「群机器人」→「添加机器人」→「自定义机器人」
   - 取个名字（比如「arXiv 论文助手」），然后复制 Webhook 地址保存好

准备好之后，把这个仓库 Fork 到你自己的 GitHub 账号下（点击页面右上角的 Fork 按钮）。

### 第二步：配置 GitHub Secrets

这一步是把你的「密码」告诉机器人，放心，GitHub 会帮你加密保存，别人看不到。

1. 进入你 Fork 后的仓库页面
2. 点击顶部的 **Settings**（设置）
3. 在左侧菜单找到 **Secrets and variables** → 点击 **Actions**
4. 点击右上角的 **New repository secret**（新建仓库密钥）
5. 依次添加下面表格中的每一项：

| Secret 名称 | 必填吗 | 说明 | 示例值 |
|-------------|--------|------|--------|
| `OPENAI_API_KEY` | ✅ 是 | LLM 服务商给你的 API Key | `sk-xxxxxxxxxxxx` |
| `OPENAI_BASE_URL` | ✅ 是 | LLM API 的地址（DeepSeek 需要填） | `https://api.deepseek.com/v1` |
| `OPENAI_MODEL` | ❌ 否 | 模型名称，默认 `gpt-4o` | `deepseek-chat` |
| `FEISHU_WEBHOOK_URL` | ✅ 是 | 飞书机器人的 Webhook 地址 | `https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx` |
| `FEISHU_SECRET` | ❌ 否 | 飞书签名密钥（机器人开了签名校验才要） | 可选 |
| `MAX_PAPERS` | ❌ 否 | 每天最多推送几篇，默认 10 篇 | `5` |
| `ARXIV_CATEGORIES` | ❌ 否 | arXiv 学科分类，默认是计算物理相关 | 见下文说明 |
| `ARXIV_KEYWORDS` | ❌ 否 | 搜索关键词，默认是分子动力学+机器学习相关 | 见下文说明 |
| `USER_AGENT_EMAIL` | ❌ 否 | 你的邮箱，用来标识身份，降低被封概率 | `your@email.com` |

> 💡 **小提示**：每添加完一个，就点 **Add secret** 按钮保存，然后继续添加下一个。

### 第三步：运行测试

配置好之后，我们手动运行一次看看效果：

1. 点击仓库顶部的 **Actions**（动作）
2. 左侧选择 **arXiv Daily Paper Push**
3. 点击右侧的 **Run workflow**（运行工作流）→ 再点一下绿色的 **Run workflow**
4. 等一两分钟，状态变成 ✅ 就说明成功了
5. 去你的飞书群里看看，是不是收到论文卡片了？

如果成功了，以后机器人会在 **每天北京时间 09:37** 自动运行，不用你管。

---

## 如何申请 LLM API Key（DeepSeek 为例）

LLM 就是「大语言模型」的意思，论文翻译和总结都靠它。这里以 DeepSeek 为例，因为它便宜、注册简单，新用户还送额度。

### 1. 注册 DeepSeek 账号

打开 https://platform.deepseek.com ，用手机号注册一个账号。

### 2. 充值（可选，新用户有免费额度）

- 新用户注册后通常会赠送一定的免费额度，够试用很久
- 如果用完了，可以在「充值」页面充值，很便宜，几块钱能用很久
- 每天推送 10 篇论文的话，一个月也就几块钱成本

### 3. 获取 API Key

1. 登录后，点击左侧菜单的 **API Keys**（API 密钥）
2. 点击 **创建新的 API Key** 按钮
3. 给它取个名字，比如「arxiv-bot」，然后点击创建
4. **重要**：Key 只会显示一次！赶紧复制下来保存好，关了页面就看不到了
5. 这个 Key 就是上面配置里要填的 `OPENAI_API_KEY`

### 4. 还要填什么？

用 DeepSeek 的话，GitHub Secrets 里要填这三个：

| Secret 名称 | 填什么 |
|-------------|--------|
| `OPENAI_API_KEY` | 你刚才复制的那串 `sk-` 开头的 Key |
| `OPENAI_BASE_URL` | 固定填：`https://api.deepseek.com/v1` |
| `OPENAI_MODEL` | 固定填：`deepseek-chat` |

> 💡 **其他 LLM 服务商呢？**
> 只要是兼容 OpenAI 格式的 API 都能用，比如智谱 AI、月之暗面、通义千问等等，方法类似，只是 `OPENAI_BASE_URL` 和 `OPENAI_MODEL` 填的值不一样。

---

## 配置说明

### 环境变量一览

所有配置都通过环境变量（GitHub Secrets）设置，不需要改代码。

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `OPENAI_API_KEY` | — | LLM API 密钥，**必填** |
| `OPENAI_BASE_URL` | — | 自定义 LLM API 地址（用 DeepSeek 等第三方时必填） |
| `OPENAI_MODEL` | `gpt-4o` | 模型名称 |
| `FEISHU_WEBHOOK_URL` | — | 飞书机器人 Webhook 地址，**必填** |
| `FEISHU_SECRET` | — | 飞书签名密钥（可选） |
| `MAX_PAPERS` | `10` | 每天最多推送的论文数量 |
| `ARXIV_CATEGORIES` | 计算物理相关 | arXiv 学科分类表达式 |
| `ARXIV_KEYWORDS` | 分子动力学+机器学习 | 关键词搜索表达式 |
| `ARXIV_API_URL` | — | 自定义 arXiv API 地址（可选） |
| `HTTP_PROXY` | — | HTTP 代理（可选） |
| `HTTPS_PROXY` | — | HTTPS 代理（可选） |
| `ENABLE_NETWORK_DIAG` | `false` | 开启网络诊断日志 |

### 自定义论文搜索范围

默认搜索的是**计算物理、材料科学、计算物理**分类下，和**分子动力学、机器学习**相关的论文。

如果你想改成自己的研究方向，可以在 GitHub Secrets 里添加 `ARXIV_CATEGORIES` 和 `ARXIV_KEYWORDS` 来自定义。

#### 学科分类（ARXIV_CATEGORIES）

多个分类之间用 `||` 隔开（表示「或者」的关系），每个分类用双引号括起来。

比如你想加生物物理和统计力学：

```
"physics.chem-ph"||"cond-mat.mtrl-sci"||"physics.comp-ph"||"physics.bio-ph"||"cond-mat.stat-mech"
```

常用的分类代号可以在这里查：https://arxiv.org/category_taxonomy

#### 关键词（ARXIV_KEYWORDS）

- `&&` 表示「而且」
- `||` 表示「或者」
- 可以用括号分组

比如你想搜「分子动力学」并且（「机器学习」或「力场」或「粗粒化」）：

```
"molecular dynamics"&&("machine learning"||"deep learning"||"neural network"||"force field"||"coarse-grained")
```

> 💡 **不会写怎么办？**
> 没关系，先用默认的就好。等熟悉了再慢慢调整。

---

## 代码贡献规范

欢迎贡献代码！请遵循以下规范保持代码质量一致。

### 命名规范

- **变量和函数**：统一使用小写蛇形命名法（snake_case）
- **函数命名**：遵循 `动词_主体_名词` 模式（如 `fetch_papers_from_arxiv`、`build_card_from_papers`、`summarize_paper_via_llm`）
- **避免无意义后缀**：不要用 `info`、`list`、`dict`、`data` 等后缀，用语义本身暗示集合类型（如用 `papers` 而不是 `paper_list`）
- **类和工厂函数**：使用大驼峰命名法（PascalCase，如 `PaperFetcher`、`CardBuilder`）

### 类型注解

- **所有**函数的参数和返回值都必须有类型注解
- 使用 `|` 联合运算符代替 `typing.Union`（PEP 604）
- 可空类型优先使用 `typing.Optional`
- 尽量使用 `typing` 泛型（如 `List[str]`、`Dict[str, Any]`）

```python
# Good
def fetch_papers_from_arxiv() -> List[Dict[str, str]]:
    ...

# Bad
def fetch_papers_from_arxiv():
    ...
```

### 文档字符串风格

- 所有公开函数使用 **NumPy/SciPy 风格**的文档字符串
- 文档字符串用**英文**书写
- 清晰描述每个参数的类型和含义，并记录返回值结构

```python
def summarize_paper_via_llm(
    title: str,
    abstract: str,
) -> Dict[str, str]:
    """Translate and summarize a paper abstract using an LLM.

    Uses standard terminology from computational chemistry and
    theoretical chemistry. Returns Chinese title, abstract, and
    highlight bullet points.

    Parameters
    ----------
    title : str
        Original English paper title.
    abstract : str
        Original English paper abstract.

    Returns
    -------
    Dict[str, str]
        Dictionary with keys: chinese_title, chinese_abstract,
        highlights.
    """
```

### 行长度与格式

- **最大行长度**：79 字符（遵循 PEP 8）
- 使用括号进行隐式换行，优先于反斜杠
- 缩进使用 4 个空格，不要用制表符

### Pythonic 写法

- **推导式**：优先使用列表/字典推导式和生成器表达式，而不是显式 `for` 循环
- **海象运算符**：在推导式和条件中使用 `:=` 赋值表达式来提高可读性
- **字典合并**：使用 `|` 运算符（PEP 604）合并字典，而不是 `.update()`

```python
# Good: comprehension + walrus
authors = [
    name_elem.text
    for author in entry.findall("atom:author", _ATOM_NS)
    if (name_elem := author.find("atom:name", _ATOM_NS))
    is not None
]

# Good: dictionary merge
processed = [
    paper | summarize_paper_via_llm(
        paper["original_title"], paper["abstract"]
    )
    for paper in papers
]
```

---

## 许可证

本项目采用 MIT 许可证，详情见仓库内的 LICENSE 文件。
