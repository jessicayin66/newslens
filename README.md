# 🗞️ NewsLens - AI-Powered News Aggregator

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-19-blue.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)

**NewsLens** is an intelligent news aggregation platform that combines traditional news consumption with AI-powered analysis to provide users with bias-aware, summarized news content. Built with modern web technologies and cutting-edge NLP models, it helps users navigate the complex media landscape with transparency and efficiency.

## ✨ Features

### 🎯 **Core Capabilities**
- **📰 News Aggregation**: Real-time news via NewsAPI
- **🤖 AI Bias Analysis**: Multi-method political bias detection using transformers
- **📝 Smart Summarization**: Hybrid extractive/abstractive article summarization
- **🔍 Topic Clustering**: Automatic grouping of related articles by semantic similarity
- **⚡ TL;DR Generation**: Quick overviews of trending topics and news clusters

### 🧠 **AI/ML Features**
- **Multi-Method Bias Detection**: Combines keyword analysis, sentiment analysis, and transformer models
- **Semantic Article Clustering**: Uses sentence transformers for intelligent topic grouping
- **Hybrid Summarization**: TextRank, LSA, and BART transformer models
- **Confidence Scoring**: Provides reliability metrics for all AI predictions
- **Real-time Processing**: Fast inference with optimized models

### 🎨 **User Experience**
- **Interactive Bias Visualization**: Visual bias distribution meters
- **Category Filtering**: Business, Technology, Health, Science, Sports, Entertainment
- **Real-time Updates**: Live news with intelligent caching

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **Node.js 16+**
- **NewsAPI Key** (free at [newsapi.org](https://newsapi.org))

### 1. Clone the Repository
```bash
git clone https://github.com/jessicayin66/news-analyzer.git
cd news-analyzer
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd ../frontend/vite-project

# Install dependencies
npm install

```

### 4. Run the Application
```bash
# Terminal 1: Start backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd frontend/vite-project
npm run dev
```

### 5. Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000

## 📖 Usage Guide

### **Browsing News**
1. **Select Category**: Choose from All, Business, Technology, Health, Science, Sports, or Entertainment
2. **View Articles**: Browse articles with AI-generated summaries and bias analysis
3. **Filter by Bias**: Click on bias distribution segments to filter articles by political leaning
4. **Read Full Articles**: Click "Read full article" to view original content

### **Understanding Bias Analysis**
- **Left-leaning**: Articles with progressive/liberal political indicators
- **Neutral**: Articles with balanced or non-political content
- **Right-leaning**: Articles with conservative/traditional political indicators
- **Confidence**: Percentage indicating reliability of bias prediction

### **TL;DR Summaries**
- **Automatic Generation**: AI creates summaries of trending topics
- **Topic Clustering**: Related articles grouped by semantic similarity
- **Key Entities**: Important people, organizations, and concepts highlighted
- **Refresh**: Click refresh to get latest summaries

## 🙏 Acknowledgments

- **NewsAPI** for providing news data
- **Hugging Face** for transformer models
- **FastAPI** for the excellent web framework
- **React** and **Vite** for the frontend stack
- **Open source community** for various libraries and tools

*NewsLens - Making news consumption transparent, efficient, and balanced*
