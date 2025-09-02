# Feature Ideas & Strategic Roadmap

This document outlines potential new features and strategic directions for the Bot Social Network project.

---

## Post-Simulation Analysis Toolkit (v2.0)

**Status:** Planned

**Objective:** Develop a sophisticated analysis script, `analyzer.py`, that processes a `simulation.jsonl` log file and generates a **single, interactive, and visually appealing HTML report**.

This feature would "close the loop" on the research process, transforming our project from a data generator into a complete research platform.

### Key Features

1.  **Statistical Summary:** A text-based report (`report.txt`) that provides key metrics:
    *   Total posts and simulation duration.
    *   Posts-per-bot and words-per-post statistics.
    *   A timeline of key events.

2.  **Interaction Graphing:** A visual graph (`mention_graph.png`) showing who is talking to whom. This would use the `@mention` data in the logs to create a directed graph, allowing a researcher to instantly see the social dynamics, identify central actors, and spot isolated bots.

3.  **Sentiment Analysis:** A line chart (`sentiment_over_time.png`) that plots the overall sentiment (positive, negative, neutral) of the conversation over time. This would allow us to study the emotional trajectory of the simulation.

### Technical Implementation

*   **Branch:** `feature/analysis-toolkit`
*   **Core Technologies:**
    *   **Data Processing:** `pandas` will remain the backbone for data manipulation.
    *   **Graphing:** As you suggested, I will use **`seaborn`** (on top of `matplotlib`) to create beautiful, publication-quality statistical plots.
    *   **Templating Engine:** I will use **`Jinja2`** to build the final HTML report. This allows us to create a professional HTML and CSS structure and inject our data and plots directly into it.
    *   **Interactivity:** The HTML template will include a lightweight CSS framework (like **Bootstrap**) for a clean design and **JavaScript** to enable features like tabs for different sections and sortable tables.
*   **Implementation Strategy:**
    1.  **Create a `templates` Directory:** I will create a new directory to hold our `report_template.html` file. This template will define the structure, include Bootstrap for styling, and contain the necessary JavaScript for interactivity.
    2.  **Develop `analyzer.py`:** This script will be the engine. Its workflow will be:
        a.  Load the `.jsonl` log file into a pandas DataFrame.
        b.  Perform all the analyses (statistical summary, interaction graph with `networkx`, sentiment analysis over time).
        c.  Generate the plots using **`seaborn`**. Instead of saving them to disk, I will save them to an in-memory buffer and encode them as Base64 strings. This allows them to be embedded directly into the final HTML file.
        d.  Convert the statistical summary DataFrames into HTML tables using pandas' `.to_html()` method.
        e.  Pass all the generated data—the Base64 plot strings, the HTML tables, and the summary statistics—to the `Jinja2` templating engine.
    3.  **Render the Final Report:** `Jinja2` will render the `report_template.html`, injecting all the data into the appropriate places. The final output will be a single, self-contained `analysis_report.html` file that can be opened in any web browser.
*   **Testing:**
    1.  I will add unit tests for the core analysis functions in `analyzer.py`.
    2.  I will functionally test the script by running it on one of our existing log files and inspecting the generated HTML report to ensure it is interactive, visually appealing, and contains all the correct information.
