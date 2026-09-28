<h1 align="center">Sentock</h1>

<h4 align="center">Quantitative Financial News Sentiment Analysis & Portfolio Management</h4>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.8%2B-blue">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-005571?logo=fastapi">
  <img alt="Machine Learning" src="https://img.shields.io/badge/Machine%20Learning-scikit--learn%20%7C%20HuggingFace-orange">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green">
</p>

---

## 📌 Executive Summary

**Sentock** is an end-to-end financial sentiment analysis pipeline designed to process market-moving news headlines and distill them into actionable, quantitative sentiment signals. 

By aggregating real-time financial news and evaluating it through a weighted ensemble of natural language processing (NLP) models—ranging from custom classical machine learning classifiers to state-of-the-art transformer models—Sentock provides a robust, multi-faceted view of market sentiment for specific equities.

The repository includes a highly concurrent **FastAPI backend**, a lightweight web interface, and the **original quantitative research notebooks** detailing model training, signal generation, and portfolio allocation experiments.

---

## 🏗️ System Architecture

Sentock relies on a decoupled, request-response architecture built for high-throughput inference and easy extensibility.

```mermaid
flowchart TD
    A[Client Request: Stock Ticker] --> B(FastAPI Gateway)
    B --> C{Ticker Validation}
    C -- Valid --> D[RSS / Finviz Scraper]
    D --> E[Data Preprocessing]
    
    E --> F1[FinBERT]
    E --> F2[ReyZer]
    E --> F3[VADER]
    E --> F4[TextBlob]
    
    F1 & F2 & F3 & F4 --> G((Weighted Ensemble Engine))
    G --> H[Normalized Sentiment Signal]
    H --> I[Frontend UI / JSON Response]
