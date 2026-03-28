"""
ML Engine — Loads PyTorch StudentNet models and runs inference.
Adapted from the original ml_module.py trained in Google Colab.
"""

import os
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import pickle
from pathlib import Path

MODELS_DIR = Path(__file__).parent / "models"

# ── Load artifacts ──
with open(MODELS_DIR / "scaler.pkl", "rb") as f:
    scaler = pickle.load(f)
with open(MODELS_DIR / "encoders.pkl", "rb") as f:
    le_dict = pickle.load(f)
with open(MODELS_DIR / "feature_cols.pkl", "rb") as f:
    feature_cols = pickle.load(f)


class StudentNet(nn.Module):
    """PyTorch neural network for student performance prediction."""
    def __init__(self, input_dim, num_classes, dropout_rate=0.3):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(dropout_rate),
            nn.Linear(256, 128),       nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(dropout_rate),
            nn.Linear(128, 64),        nn.BatchNorm1d(64),  nn.ReLU(), nn.Dropout(dropout_rate),
            nn.Linear(64, 32),         nn.ReLU(),
            nn.Linear(32, num_classes)
        )

    def forward(self, x):
        return self.network(x)


# ── Load trained models ──
input_dim = len(feature_cols)
num_grade_classes = len(le_dict["Grade"].classes_)

model_bin = StudentNet(input_dim, 2)
model_bin.load_state_dict(torch.load(MODELS_DIR / "model_pass_fail.pth", map_location="cpu"))
model_bin.eval()

model_grade = StudentNet(input_dim, num_grade_classes)
model_grade.load_state_dict(torch.load(MODELS_DIR / "model_grade.pth", map_location="cpu"))
model_grade.eval()

print(f"[ML Engine] Models loaded. Features: {len(feature_cols)}, Grade classes: {list(le_dict['Grade'].classes_)}")


def _engineer_features(row: pd.DataFrame) -> pd.DataFrame:
    """Add engineered features that the model expects."""
    # Dynamic Semester Marks Logic
    sem_cols = [f"Sem{i}_Marks" for i in range(1, 9)]
    available_sems = [c for c in sem_cols if c in row.columns and row[c].notna().all()]
    
    if len(available_sems) >= 2:
        row["Mark_Consistency"] = row[available_sems].std(axis=1)
        # Trend based on first and last available semester
        row["Improvement_Trend"] = row[available_sems[-1]] - row[available_sems[0]]
    else:
        row["Mark_Consistency"] = 0
        row["Improvement_Trend"] = 0

    study = row.get("StudyHours", pd.Series([0]))[0] if "StudyHours" in row.columns else 0
    attend = row.get("Attendance", pd.Series([0]))[0] if "Attendance" in row.columns else 0
    online = row.get("OnlineCourses", pd.Series([0]))[0] if "OnlineCourses" in row.columns else 0
    discuss = row.get("Discussions", pd.Series([5]))[0] if "Discussions" in row.columns else 5 # Default to 5
    
    row["Engagement_Score"] = (float(study) * 0.3 + float(attend) * 0.3 +
                                float(online) * 0.2 + float(discuss) * 0.2)
    return row


def predict_student(data: dict) -> dict:
    """
    Predict a single student's pass/fail status and grade.
    """
    row = pd.DataFrame([data])
    
    # ── Check for Low Marks Override (User Requirement) ──
    # If any mark is < 40, it's HIGH risk (Benchmark shifted from 30 to 40)
    marks_to_check = ["ExamScore", "Sem1_Marks", "Sem2_Marks", "Sem3_Marks", "Sem4_Marks", 
                      "Sem5_Marks", "Sem6_Marks", "Sem7_Marks", "Sem8_Marks",
                      "IA1", "IA2", "IA3", "Assessments", "ABA", "ProjectsDone"]
    has_low_marks = False
    for m in marks_to_check:
        val = data.get(m)
        if val is not None and float(val) < 40:
            has_low_marks = True
            break
            
    row = _engineer_features(row)
    
    # Defaults for removed features (Motivation, Stress, etc.)
    defaults = {
        "Motivation": 3,
        "StressLevel": 2,
        "Resources": 3,
        "Internet": 1,
        "LearningStyle": 1,
        "EduTech": 1,
        "Discussions": 5,
        "Extracurricular": 1,
    }

    # Encode categorical features
    if "Gender" in row.columns and "Gender" in le_dict:
        try:
            row["Gender"] = le_dict["Gender"].transform(row["Gender"])
        except (ValueError, KeyError):
            row["Gender"] = 0

    # Ensure all feature columns exist, use defaults for missing
    for col in feature_cols:
        if col not in row.columns:
            row[col] = defaults.get(col, 0)

    X = scaler.transform(row[feature_cols].fillna(0).values)
    t = torch.tensor(X, dtype=torch.float32)

    with torch.no_grad():
        pf_prob = torch.softmax(model_bin(t), dim=1)[0].numpy()
        grade_prob = torch.softmax(model_grade(t), dim=1)[0].numpy()

    pass_probability = float(pf_prob[1])
    risk_score = round((1 - pass_probability) * 100, 1)
    
    # ── Apply Override ──
    if has_low_marks:
        risk_level = "HIGH"
        risk_score = max(risk_score, 85.0) # Ensure it shows as high risk
    elif risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # ── Calculate Estimated SGPA (Hackathon Logic) ──
    # Strategy: Average of all available marks / 10
    marks_vals = [data.get(m) for m in marks_to_check if data.get(m) is not None]
    if marks_vals:
        avg_marks = sum(marks_vals) / len(marks_vals)
        sgpa = round(avg_marks / 10, 2)
    else:
        sgpa = 0.0

    return {
        "pass_fail": "Pass" if (np.argmax(pf_prob) == 1 and not has_low_marks) else "Fail",
        "pass_probability": 0.01 if has_low_marks else round(pass_probability, 4),
        "predicted_grade": "F" if has_low_marks else le_dict["Grade"].inverse_transform([np.argmax(grade_prob)])[0],
        "grade_probabilities": {
            le_dict["Grade"].inverse_transform([i])[0]: round(float(p), 4)
            for i, p in enumerate(grade_prob)
        },
        "risk_score": risk_score,
        "risk_level": risk_level,
        "sgpa": sgpa,
    }


def predict_batch(students: list[dict]) -> list[dict]:
    """Predict for a batch of students."""
    results = []
    for student in students:
        result = predict_student(student)
        result["student_data"] = student
        results.append(result)
    return results
