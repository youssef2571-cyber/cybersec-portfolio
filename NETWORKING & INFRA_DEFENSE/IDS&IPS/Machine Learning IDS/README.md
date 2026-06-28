# Network Intrusion Detection using Isolation Forest

## Overview

This project implements an anomaly-based Intrusion Detection System (IDS) using the Isolation Forest algorithm from Scikit-learn.

Unlike signature-based IDS solutions, this approach learns the behavior of legitimate network traffic and identifies abnormal connections that may correspond to cyber attacks.

The project is trained and evaluated using the NSL-KDD dataset.

---

## Features

- Anomaly-based intrusion detection
- Machine Learning with Isolation Forest
- NSL-KDD dataset support
- Automatic preprocessing
- One-Hot Encoding
- Feature Scaling
- Performance evaluation
- Confusion Matrix
- Classification Report
- Accuracy calculation
- Result visualization

---

## Dataset

This project uses the NSL-KDD dataset.

Required files:

```
KDDTrain+.txt
KDDTest+.txt
```

Download:

https://www.unb.ca/cic/datasets/nsl.html

---

## Project Structure

```
.
├── KDDTrain+.txt
├── KDDTest+.txt
├── isolation_forest.py
├── requirements.txt
└── README.md
```

---

## Installation

```bash
git clone https://github.com/yourusername/network-ids-isolationforest.git

cd network-ids-isolationforest
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Requirements

```
pandas
numpy
scikit-learn
matplotlib
```

---

## Running

```bash
python isolation_forest.py
```

---

## Workflow

```
Training Dataset
        │
        ▼
Data Preprocessing
        │
        ▼
One-Hot Encoding
        │
        ▼
StandardScaler
        │
        ▼
Isolation Forest Training
        │
        ▼
Testing Dataset
        │
        ▼
Anomaly Detection
        │
        ▼
Evaluation
```

---

## Output

The program displays:

- Accuracy
- Confusion Matrix
- Precision
- Recall
- F1-score
- Number of detected anomalies
- Visualization chart

---

## Technologies

- Python
- Pandas
- NumPy
- Scikit-learn
- Matplotlib

---

## Future Improvements

- Hyperparameter optimization
- Autoencoder implementation
- One-Class SVM comparison
- Local Outlier Factor comparison
- Real-time packet analysis
- Streamlit dashboard

---

## License

MIT License
