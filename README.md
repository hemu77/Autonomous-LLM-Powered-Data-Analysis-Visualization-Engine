# Autonomous LLM-Powered Data Analysis & Visualization Engine

> **⚠️ Status: STILL DEVELOPING** — This project is actively being enhanced with new features and improvements. Contributions and feedback are welcome!

## Overview

A sophisticated, **cell-by-cell runnable** Jupyter notebook that automates data analysis and report generation using:

- **Multiple LLMs** for planning, storytelling, and fact-checking
- **Deterministic execution** for reproducible results (SQL-like queries on pandas)
- **Safe visualization** with Plotnine (ggplot-style plots)
- **Professional report generation** in HTML + PDF formats

This system works **independently of LLM availability** — all core analysis layers are deterministic. LLM integration is optional and enhances the narrative quality of insights.

---

## Key Features

### 🔍 **Intelligent Analysis**
- **Natural language to SQL translation**: Convert questions into executable analysis plans
- **Query engine**: Filters, grouping, aggregations (mean, sum, count, min, max, median)
- **Hallucination guards**: Separate critic model validates all outputs against computed evidence

### 📊 **Visualization**
- **Automatic plot specification**: LLM generates plotting instructions
- **Plotnine rendering**: Beautiful ggplot-style visualizations
- **Safe execution**: No arbitrary code execution; only validated plot specs are rendered
- **Multiple plot types**: Line, bar, scatter charts with color grouping

### 📄 **Report Generation**
- **HTML reports**: Responsive, embeds data profiles, analyses, and inline plots
- **PDF reports**: Multi-page professional documen ts with tables and images
- **Dataset profiling**: Automatic schema discovery with statistics

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/hemu77/Autonomous-LLM-Powered-Data-Analysis-Visualization-Engine.git
cd Autonomous-LLM-Powered-Data-Analysis-Visualization-Engine
```

### 2. Install Dependencies

```bash
pip install -q plotnine kaleido datasets litellm langchain-community langchain-core reportlab pandas pyarrow openpyxl
```

### 3. Set up CyVerse API Key (Optional but Recommended)

The system works without LLMs using deterministic execution. To enable LLM-powered features:

**Local/Shell:**
```bash
export CYVERSE_API_KEY='your_api_key_here'
```

**Colab/Notebook:**
```python
import os
os.environ['CYVERSE_API_KEY'] = 'your_api_key_here'
```

> ⚠️ **Never hardcode API keys in notebooks!** Always use environment variables.

### 4. Open the Notebook

```bash
jupyter notebook analytics_automation_llm_with_reporting_interactive.ipynb
```

---

## Usage Workflow

### Step 1: Load Your Data

```python
import pandas as pd
import seaborn as sns

# Option A: Load from CSV/Excel
df = pd.read_csv('your_data.csv')

# Option B: Load from seaborn (demo)
df = sns.load_dataset('titanic')
```

### Step 2: Ask Questions

```python
questions = [
    "What is the survival rate by sex?",
    "Which passenger class had the highest average fare?",
    "What is the age distribution?"
]
```

The system automatically:
- Generates a deterministic analysis plan
- Executes SQL-like queries
- Returns results as pandas DataFrames

### Step 3: Create Visualizations

```python
plot_goals = [
    "Bar chart of survival count by sex",
    "Scatter plot of age vs fare colored by class"
]
```

The system renders plots safely without arbitrary code execution.

### Step 4: Generate Reports

```python
from analytics_automation import AnalyticsAutomationPipeline, ReportExporter

pipe = AnalyticsAutomationPipeline(df)
exporter = ReportExporter(out_dir='./report_output')

# Generate HTML + PDF reports
html_path = exporter.export_html(...)
pdf_path = exporter.export_pdf(...)
```

**📌 After running the notebook, check `./report_output/report.html` first!**

---

## Output Files

The notebook generates:

```
./report_output/
├── report.html              # Main interactive report (open in browser)
├── report.pdf               # Printable PDF version
└── plots/
    ├── plot_1.png           # First visualization
    ├── plot_2.png           # Second visualization
    └── ...
```

### 📖 **Open `report.html` in your browser to view the complete analysis report!**

---

## Architecture

### Core Components

1. **DataIngestor**: Loads CSV, JSON, Parquet, Excel
2. **DataNormalizer**: Fluent type coercion and schema cleaning
3. **DataProfiler**: Generates statistical summaries for LLM context
4. **AnalysisPlan**: JSON schema for deterministic query execution
5. **AnalysisExecutor**: SQL-like query engine (filters, groupby, aggregations)
6. **PlotSpec**: Validated plotting instructions
7. **PlotRenderer**: Safe plotnine rendering
8. **HallucinationGuard**: Critic model validates outputs
9. **ReportExporter**: HTML + PDF generation

### Execution Flow

```
Data Input
    ↓
[Profile Analysis]
    ↓
[LLM: Generate Plan] → or → [Deterministic Fallback]
    ↓
[Validate Plan]
    ↓
[Execute Deterministically]
    ↓
[LLM: Generate Story] → [Hallucination Guard] → [Fact Check]
    ↓
[Report Generation]
    ↓
HTML + PDF Output
```

---

## Configuration

Edit the `PipelineConfig` class to customize behavior:

```python
@dataclass
class PipelineConfig:
    api_base: str = "https://llm-api.cyverse.ai/v1"  # LLM endpoint
    api_key_env: str = "CYVERSE_API_KEY"             # Env var name
    
    routing: ModelRouting = ...  # Which model for what task
    
    temperature_analysis: float = 0.0      # Deterministic results
    temperature_plot: float = 0.0
    temperature_critic: float = 0.0
    
    strict_hallucination_guard: bool = True  # Always fact-check
    max_sample_rows_for_llm: int = 250   # Context size limits
```

---

## Supported Models

The system routes tasks to optimized models:

- **Analysis (numeric reasoning)**: `phi-4`, `Qwen2.5-Coder-32B`, etc.
- **Plotting (instruction following)**: `Llama-3.3-70B-Instruct`
- **Critic (fact-checking)**: `phi-4`

Full list in the `ModelRouting.allowed_models` set.

---

## Examples

### Example 1: Titanic Dataset

```python
import seaborn as sns
from analytics_automation import AnalyticsAutomationPipeline

df = sns.load_dataset('titanic')
pipe = AnalyticsAutomationPipeline(df)

# Ask a question
result = pipe.answer("What is the survival rate by sex?")
print(result['answer'])

# Create a plot
plot_result = pipe.plot("Bar chart of survival by sex")
plot_result['plot'].save('survival_by_sex.png')
```

### Example 2: Custom CSV Data

```python
df = pd.read_csv('sales_data.csv')
pipe = AnalyticsAutomationPipeline(df)

questions = [
    "Which product had the highest revenue?",
    "What is the average order value by region?"
]

plot_goals = [
    "Revenue trend over time",
    "Top 10 products by sales"
]

# See output/report.html
```

---

## Deterministic Features (No LLM Required)

✅ Data normalization and type coercion  
✅ Statistical profiling  
✅ Filtering and grouping queries  
✅ Aggregation operations  
✅ Plotnine visualization  
✅ HTML + PDF report generation  

---

## LLM-Powered Features (Requires API Key)

🤖 Natural language to analysis plan conversion  
🤖 Narrative bullet-point generation  
🤖 Plot specification generation  
🤖 Hallucination fact-checking  

---

## FAQ

### Q: Can I use this without an LLM API key?
**A:** Yes! All core analysis, plotting, and report generation work deterministically. LLM features enhance narrative quality.

### Q: What file formats are supported?
**A:** CSV, JSON, JSONL, Parquet, Excel (.xlsx/.xls).

### Q: How large can my dataset be?
**A:** Tested up to 100K rows comfortably. For larger datasets, sample before LLM contexts.

### Q: Can I customize the HTML/PDF styling?
**A:** Yes! The `ReportExporter` class includes CSS templates you can modify.

### Q: Does this work in Google Colab?
**A:** Yes! Just make sure dependencies are installed and the API key is set via `os.environ`.

---

## Contributing

This project is **still developing**! We welcome:

- 🐛 Bug reports
- 💡 Feature requests
- 📝 Documentation improvements
- 🔧 Code contributions

Please open an issue or PR on GitHub.

---

## License

MIT License — Free to use, modify, and distribute.

---

## Roadmap

- [ ] Vector search integration (semantic analysis)
- [ ] Real-time data streaming
- [ ] Advanced statistical tests
- [ ] Interactive dashboard generation
- [ ] Multi-language support
- [ ] Cached LLM responses for cost optimization

---

## Support

For questions or issues:

1. **Check the notebook cells** — each is self-contained and documented
2. **Review the example sections** at the end of the notebook
3. **Open a GitHub Issue** with:
   - Your data schema (without sensitive data)
   - The question/goal you're trying to accomplish
   - Error messages (if any)

---

## Key Notes

📌 **Always open `report.html` first** — it's the main output!  
📌 **Set API keys via environment variables**, never hardcode them  
📌 **The system is deterministic** — no LLM ≠ no analysis  
📌 **All plots are validated** — no arbitrary code execution  

---

**Built with ❤️ for autonomous, trustworthy data analysis.**

*Last Updated: April 2026* | *Status: Active Development*
