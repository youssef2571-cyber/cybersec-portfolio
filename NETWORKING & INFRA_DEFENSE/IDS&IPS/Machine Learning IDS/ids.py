import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    classification_report
)

# ==========================================================
# 1. Define NSL-KDD dataset column names
# ==========================================================

cols = [
    "duration","protocol_type","service","flag","src_bytes","dst_bytes",
    "land","wrong_fragment","urgent","hot","num_failed_logins",
    "logged_in","num_compromised","root_shell","su_attempted",
    "num_root","num_file_creations","num_shells",
    "num_access_files","num_outbound_cmds","is_host_login",
    "is_guest_login","count","srv_count","serror_rate",
    "srv_serror_rate","rerror_rate","srv_rerror_rate",
    "same_srv_rate","diff_srv_rate","srv_diff_host_rate",
    "dst_host_count","dst_host_srv_count",
    "dst_host_same_srv_rate","dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate",
    "dst_host_srv_serror_rate",
    "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate",
    "label",
    "difficulty"
]

# ==========================================================
# 2. Load training and testing datasets
# ==========================================================

train = pd.read_csv(
    "KDDTrain+.txt",
    names=cols,
    header=None
)

test = pd.read_csv(
    "KDDTest+.txt",
    names=cols,
    header=None
)

train = train.replace('"', '', regex=True)
test = test.replace('"', '', regex=True)

print("Train :", train.shape)
print("Test  :", test.shape)

# ==========================================================
# 3.  Create binary target labels
# ==========================================================

train["target"] = np.where(train["label"] == "normal", 1, -1)
test["target"] = np.where(test["label"] == "normal", 1, -1)

# ==========================================================
# 4. One-Hot encoding
# ==========================================================

combined = pd.concat([train, test], axis=0)

combined = pd.get_dummies(
    combined,
    columns=["protocol_type", "service", "flag"]
)

train = combined.iloc[:len(train)].copy()
test = combined.iloc[len(train):].copy()

# ==========================================================
# 5. Separation X / y
# ==========================================================

X_train = train.drop(columns=["label", "target"])
y_train = train["target"]

X_test = test.drop(columns=["label", "target"])
y_test = test["target"]

# ==========================================================
# 6.keep normal trafic 
# ==========================================================

X_train_normal = X_train[y_train == 1]

print("\nTrafic normal d'entraînement :", len(X_train_normal))

# ==========================================================
# 7. Normalisation
# ==========================================================

scaler = StandardScaler()

X_train_normal = scaler.fit_transform(X_train_normal)

X_test_scaled = scaler.transform(X_test)

# ==========================================================
# 8. modele creation
# ==========================================================

model = IsolationForest(
    n_estimators=150,
    contamination=0.05,
    random_state=42
)

print("\nEntraînement du modèle...")
model.fit(X_train_normal)

# ==========================================================
# 9. Predictions
# ==========================================================

predictions = model.predict(X_test_scaled)

# ==========================================================
# 10. Evaluation
# ==========================================================

accuracy = accuracy_score(y_test, predictions)

print("\n==============================")
print("Accuracy :", round(accuracy,4))
print("==============================")

cm = confusion_matrix(y_test, predictions)

print("\nMatrice de confusion")
print(cm)

print("\nRapport de classification")
print(classification_report(y_test, predictions))

# ==========================================================
# 11.summury
# ==========================================================

normal_detected = np.sum(predictions == 1)
attacks_detected = np.sum(predictions == -1)

print("\n========== RÉSULTATS ==========")
print("Nombre total de connexions :", len(predictions))
print("Connexions normales détectées :", normal_detected)
print("Anomalies détectées :", attacks_detected)

# ==========================================================
# 12. Graphique
# ==========================================================

plt.figure(figsize=(7,5))

plt.bar(
    ["Normal", "Anomalie"],
    [normal_detected, attacks_detected]
)

plt.title("Détection d'anomalies avec Isolation Forest")
plt.ylabel("Nombre de connexions")

plt.show()
