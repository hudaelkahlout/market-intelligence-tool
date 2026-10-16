# Technical Proposal

## Google Play Market Intelligence & Competitor Analysis Tool

**Prepared by:** Mahmoud Alshukri\
**Project:** Market Intelligence & Competitor Scraping Tool

------------------------------------------------------------------------

## 1. Project Understanding

The objective is to build an end-to-end Python web application that
helps a product team evaluate competing mobile applications before
starting product development.

The tool allows stakeholders to search Google Play by application name,
niche keyword, or market category, select multiple competitors, collect
recent customer reviews, analyze sentiment, compare competitors
visually, and identify market gaps using AI.

The final solution provides an interactive Streamlit dashboard and a
downloadable Excel report.

## 2. Proposed Technical Architecture

``` text
Streamlit Web Interface
        |
        v
Google Play Search
        |
        v
Multi-App Selection (2–4 apps)
        |
        v
Google Play Review Scraping
        |
        v
Data Cleaning & Normalization
        |
        v
Sentiment Segmentation
        |
        +-------------------+
        |                   |
        v                   v
SQLite Storage       Plotly Analytics
        |                   |
        +---------+---------+
                  |
                  v
        Gemini Market Gap Analysis
                  |
                  v
          Excel Report Export
```

### Technology Stack

-   **Python 3.10+** --- core application language
-   **Streamlit** --- interactive web dashboard
-   **google-play-scraper** --- Google Play discovery and review
    collection
-   **pandas** --- data cleaning and analysis
-   **SQLite** --- relational local data storage
-   **Plotly** --- interactive competitor visualizations
-   **Google Gemini API (`google-genai`)** --- strategic market-gap
    analysis
-   **openpyxl** --- multi-sheet Excel reporting
-   **pytest** --- automated testing

## 3. Multi-App Scraping Approach

Users can dynamically search Google Play and select **2--4 competing
applications**. For each application, the system collects approximately
**150--300 recent customer reviews**.

Applications are processed independently using controlled review
collection so that memory usage remains predictable and a failure
affecting one competitor does not unnecessarily terminate the entire
analysis.

The pipeline normalizes app IDs, titles, review text, star ratings,
timestamps, and helpful counts when available. Empty and duplicate
reviews are removed, and incomplete metadata is handled safely.

## 4. Sentiment Segmentation

Feedback is categorized into:

-   **Positive:** 4--5 stars
-   **Neutral:** 3 stars
-   **Negative:** 1--2 stars

This provides a deterministic and transparent sentiment baseline. The
sentiment component remains modular so that a more advanced NLP
classifier could be introduced later.

Special attention is given to **1-star and 2-star reviews**, which
provide the primary evidence for recurring pain points and market
opportunities.

## 5. Data Storage and Processing

Cleaned application and review data is persisted in a relational
**SQLite** database. Application metadata and individual reviews are
stored separately with appropriate uniqueness rules to reduce duplicate
records.

Expected database output:

`database/competitor_intelligence.db`

## 6. Interactive Dashboard

The **Streamlit** dashboard allows stakeholders to:

1.  search for applications or market categories;
2.  inspect matching Google Play applications;
3.  select 2--4 competitors;
4.  run competitor analysis;
5.  inspect KPIs;
6.  compare competitors using Plotly charts;
7.  review low-rating customer feedback;
8.  inspect AI-generated market-gap recommendations;
9.  download the Excel report.

Comparison metrics include review volume, average review rating,
sentiment distribution, negative review volume, and star-rating
distribution.

## 7. AI-Powered Market Gap Analysis

The system uses the **Google Gemini API** to transform competitor
complaints into strategic product intelligence.

Rather than sending every review indiscriminately, the AI pipeline
prioritizes representative **1-star and 2-star feedback**, removes
duplicates, and controls input size.

The analysis identifies:

-   **Top Recurring Problems:** common bugs, usability issues,
    frustrations, and service problems.
-   **Missing or Requested Features:** capabilities customers repeatedly
    request or find inadequate.
-   **Market Gaps:** opportunities where the planned application could
    differentiate itself.
-   **Strategic Recommendations:** concrete recommendations based on
    competitor feedback.
-   **Evidence and Confidence:** separation of strongly supported
    patterns from weaker hypotheses requiring validation.

## 8. Excel Reporting

The application generates a professional multi-sheet Excel workbook
containing:

-   **Executive Summary**
-   **Competitor Comparison**
-   **All Reviews**
-   **Negative Reviews**
-   **AI Market Gaps**

The report is downloadable directly from the Streamlit interface.

## 9. Reliability and Security

The implementation handles Google Play scraping failures, incomplete
metadata, malformed or duplicate reviews, empty datasets, Gemini
failures, missing Gemini credentials, database errors, and
report-generation failures.

The Gemini API key is never hard-coded or committed to GitHub.
Credentials are supplied through environment variables or Streamlit
secrets.

Automated tests cover the core pipeline, sentiment classification,
database operations, AI handling, and Excel reporting.

## 10. Deliverables

The final delivery includes:

-   complete Python source code;
-   modular scraping and analysis pipeline;
-   Streamlit dashboard;
-   Google Play search and multi-app selection;
-   review scraping and normalization;
-   sentiment segmentation;
-   SQLite database;
-   Plotly competitor analytics;
-   Gemini market-gap analysis;
-   downloadable multi-sheet Excel report;
-   automated tests;
-   `requirements.txt`;
-   professional English `README.md`;
-   GitHub repository;
-   Streamlit deployment-ready application.

## 11. Project Links

### GitHub Repository

https://github.com/hudaelkahlout/market-intelligence-tool.git

### Live Streamlit Demo

https://market-intelligence-toolgit-ep4ieqzxjeh67ra9ew3qtd.streamlit.app/

Replace these placeholders with the final URLs after publishing the
repository and deploying the application.

## 12. Closing

This solution turns raw Google Play customer feedback into actionable
competitor intelligence. By combining structured review collection,
transparent sentiment segmentation, relational storage, interactive
analytics, and AI-assisted market-gap analysis, it helps the product
team evaluate competitors and identify recurring user needs before
committing to development decisions.
