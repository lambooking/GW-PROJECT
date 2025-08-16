# RAG智能评分系统代码工作流说明

## 1. 系统概述

本系统是一个基于RAG（Retrieval-Augmented Generation）架构的文档智能评分系统。它通过调用一个大型语言模型（LLM）服务（由VLLM部署），结合内部知识库，对输入的文档（如作业指导书）进行多维度、标准化的质量评估和评分。

脚本 `run_complete_rag_scoring.py` 是整个系统的入口点，提供了一个命令行界面来执行不同的任务，包括系统测试、单个文档评分、批量文档评分以及报告格式转换。

## 2. 核心组件

系统主要由 `run_complete_rag_scoring.py` 中的 `RAGScoringSystem` 类进行编排，该类初始化并管理以下核心组件：

-   **`RAGScoringSystem`**: 主控制类，负责协调所有组件完成评分任务。
-   **`VLLMInferenceClient` (`src.inference.vllm_client`)**: VLLM服务的客户端，封装了与LLM的HTTP通信，用于执行文本分析和内容生成任务。
-   **`RAGKnowledgeBase` (`src.inference.rag_knowledge_base`)**: RAG知识库，底层通常是向量数据库（如ChromaDB）。它存储了预处理后的文档片段（chunks），用于在评分时提供相关的背景知识（检索）。
-   **`PreprocessingPipeline` (`src.data_processing.preprocessing_pipeline`)**: 预处理流水线，负责将原始输入文件（如PDF）解析、清洗、切片，并转换为标准化的 `StandardizedDocument` 对象，为后续处理做准备。
-   **`RAGScoringEngine` (`src.inference.rag_scoring_engine`)**: 核心评分引擎。它接收一个 `StandardizedDocument` 对象，设计并执行一系列Prompts，通过 `VLLMInferenceClient` 与LLM交互。在评分过程中，它会查询 `RAGKnowledgeBase` 以获取相关信息，从而实现更精准的RAG评分。
-   **`HTMLReportGenerator` (`src.utils.html_report_generator`)**: 报告生成器，负责将评分结果（JSON格式）转换为人类可读的HTML格式报告。

## 3. 启动依赖

在运行评分系统之前，必须启动后端的VLLM服务。这可以通过执行 `scripts/start_vllm.sh` 脚本来完成。

```bash
#!/bin/bash
# ...
python -m vllm.entrypoints.openai.api_server \
    --model /home/wyr/AgiBot-World-Project/agi_iros/models/Qwen2.5-VL-7B-Instruct  \
    --served-model-name qwen2.5-vl-3b \
    --host 0.0.0.0 \
    --port 8000 \
    # ...
```

该脚本会启动一个兼容OpenAI API的服务器，监听在 `8000` 端口。评分系统默认会连接到 `http://localhost:8000/v1`。

## 4. 命令行接口与执行流程

系统通过 `main` 函数提供命令行功能。

```
用法:
  python run_complete_rag_scoring.py <command> [options]

命令:
  test              - 测试系统连接
  score <file>      - 评分指定文件
  score-kb [name]   - 评分知识库中的文档
  batch <dir>       - 批量评分目录中的PDF文件
  html-convert      - 将现有JSON报告转换为HTML格式
```

### 4.1. 初始化流程

无论执行哪个命令（`html-convert`除外），系统都会首先执行 `RAGScoringSystem.initialize_components()` 方法：
1.  **初始化知识库**: 创建 `RAGKnowledgeBase` 实例，并检查其中是否已有文档。
2.  **初始化VLLM客户端**: 创建 `VLLMInferenceClient` 实例，并发送一个测试请求以验证与VLLM服务的连接。
3.  **初始化评分引擎**: 创建 `RAGScoringEngine` 实例，并传入VLLM客户端和知识库。
4.  **初始化预处理管线**: 创建 `PreprocessingPipeline` 实例。

### 4.2. `score <file>`: 单文件评分流程

这是最核心的功能。
`python run_complete_rag_scoring.py score data/raw/场景1(1).pdf`

1.  **调用**: `RAGScoringSystem.score_document_from_file(file_path)`
2.  **文档预处理**:
    -   调用 `self.pipeline.process(file_path)`。
    -   `PreprocessingPipeline` 对指定路径的PDF文件进行解析，提取文本、表格等信息，生成一个 `StandardizedDocument` 对象。
3.  **RAG智能评分**:
    -   调用 `self.scoring_engine.score_document(document)`。
    -   `RAGScoringEngine` 根据预设的评分标准（如完整性、准确性等），生成不同的Prompt。
    -   对于每个评分项，可能会从 `RAGKnowledgeBase` 检索相关信息，将信息和文档内容一起组合成最终的Prompt。
    -   通过 `VLLMInferenceClient` 将Prompt发送给LLM，获取评分、理由等。
    -   汇总所有评分项，生成最终的结构化评分结果（字典）。
4.  **保存报告**:
    -   将评分结果字典保存为JSON文件，存储在 `output/rag_scoring_reports/` 目录下。
    -   调用 `self.html_generator.generate_html_report()`，将JSON结果渲染成HTML报告，存储在 `output/rag_scoring_reports/html/` 目录下。
5.  **打印摘要**: 在控制台输出评分的简要总结。

### 4.3. `batch <dir>`: 批量评分流程

`python run_complete_rag_scoring.py batch data/raw/`

1.  **调用**: `RAGScoringSystem.batch_score_documents(file_paths)`
2.  **文件查找**: 脚本首先会扫描指定目录下的所有 `.pdf` 文件。
3.  **循环评分**: 遍历找到的PDF文件列表，对每个文件重复执行 **4.2. 单文件评分流程**。
4.  **生成汇总报告**: 所有文件处理完毕后，生成一个批处理的汇总JSON报告（`batch_scoring_summary_...json`），记录每个文件的成功或失败状态。

### 4.4. `score-kb [name]`: 知识库文档评分流程

此功能用于对已经存在于知识库中的文档进行重新评分，而无需重新上传和预处理文件。

1.  **调用**: `RAGScoringSystem.score_existing_document(document_name)`
2.  **文档定位**: 从知识库中确认指定的文档名存在。如果未提供名称，则默认选择第一个文档。
3.  **模拟文档对象**: 创建一个 `StandardizedDocument` 对象，但其 `text_content` 等字段为空。因为评分引擎 `RAGScoringEngine` 被设计为直接从知识库中根据文档名拉取所需内容进行评分。
4.  **评分与报告**: 后续流程与 **4.2. 单文件评分流程** 的第3、4、5步相同。

### 4.5. `test`: 系统测试

`python run_complete_rag_scoring.py test`

-   执行 `RAGScoringSystem.test_vllm_connection()`，向VLLM发送一个简单的测试Prompt，以检查服务是否可用以及网络连接是否正常。

### 4.6. `html-convert`: 报告转换

`python run_complete_rag_scoring.py html-convert`

-   此命令不会初始化完整的 `RAGScoringSystem`。
-   它直接使用 `HTMLReportGenerator.batch_convert_reports()` 方法，扫描 `output/rag_scoring_reports` 目录下的所有JSON报告，并为每个报告生成对应的HTML版本。

## 5. 输入与输出

-   **输入**:
    -   命令行参数（命令、文件路径、目录路径）。
    -   待评分的文档文件（目前主要是 `.pdf`）。
    -   `data/raw/` 目录是示例文件存放位置。
-   **输出**:
    -   **日志文件**: 每次运行都会在 `logs/` 目录下生成一个带时间戳的日志文件，记录详细的执行过程。
    -   **JSON评分报告**: 单个文档的详细评分结果，保存在 `output/rag_scoring_reports/`。
    -   **HTML评分报告**: JSON报告的可视化版本，保存在 `output/rag_scoring_reports/html/`。
    -   **批量处理摘要**: 批量评分任务的总结报告，保存在 `output/rag_scoring_reports/`。
    -   **控制台输出**: 实时日志和最终的评分摘要。
