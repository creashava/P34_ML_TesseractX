"""
Explainable AI (XAI) Engine — Generates human-readable insights for predictions.
Provides feature importance and natural language explanations.
"""

from typing import Optional

# Thresholds for feature analysis
FEATURE_THRESHOLDS = {
    "Attendance": {"low": 75, "critical": 60, "unit": "%", "label": "Attendance"},
    "StudyHours": {"low": 15, "critical": 8, "unit": "hrs/week", "label": "Study Hours"},
    "AssignmentCompletion": {"low": 70, "critical": 50, "unit": "%", "label": "Assignment Completion"},
    "ExamScore": {"low": 60, "critical": 40, "unit": "%", "label": "Exam Score"},
    "IA1": {"low": 60, "critical": 40, "unit": "%", "label": "IA1 Score"},
    "IA2": {"low": 60, "critical": 40, "unit": "%", "label": "IA2 Score"},
    "IA3": {"low": 60, "critical": 40, "unit": "%", "label": "IA3 Score"},
    "Assessments": {"low": 60, "critical": 40, "unit": "%", "label": "Assessments"},
    "ABA": {"low": 60, "critical": 40, "unit": "%", "label": "ABA Score"},
    "ProjectsDone": {"low": 60, "critical": 40, "unit": "%", "label": "ProjectsDone"},
    "Motivation": {"low": 3, "critical": 1, "unit": "/5", "label": "Motivation Level"},
    "StressLevel": {"high_bad": 4, "critical_bad": 5, "unit": "/5", "label": "Stress Level"},
}


def generate_xai_insights(student_data: dict, prediction: dict) -> dict:
    """
    Generate explainable AI insights for a student prediction.
    
    Returns:
        Dict with risk_factors, strengths, recommendations, narrative, and feature_importance
    """
    risk_factors = []
    strengths = []
    recommendations = []
    feature_importance = []

    # Analyze each feature
    for feature, thresholds in FEATURE_THRESHOLDS.items():
        value = student_data.get(feature, None)
        if value is None:
            continue
        value = float(value)
        label = thresholds["label"]
        unit = thresholds["unit"]

        if "high_bad" in thresholds:
            # Higher is worse (e.g., stress)
            if value >= thresholds.get("critical_bad", 999):
                severity = "critical"
                risk_factors.append({
                    "feature": label,
                    "value": f"{value}{unit}",
                    "severity": "critical",
                    "message": f"🔴 {label} is critically high at {value}{unit}",
                })
                feature_importance.append({"feature": label, "impact": "negative", "weight": 0.9})
            elif value >= thresholds["high_bad"]:
                risk_factors.append({
                    "feature": label,
                    "value": f"{value}{unit}",
                    "severity": "warning",
                    "message": f"🟡 {label} is elevated at {value}{unit}",
                })
                feature_importance.append({"feature": label, "impact": "negative", "weight": 0.6})
            else:
                strengths.append({
                    "feature": label,
                    "value": f"{value}{unit}",
                    "message": f"🟢 {label} is manageable at {value}{unit}",
                })
                feature_importance.append({"feature": label, "impact": "positive", "weight": 0.3})
        else:
            # Lower is worse
            if value <= thresholds.get("critical", 0):
                risk_factors.append({
                    "feature": label,
                    "value": f"{value}{unit}",
                    "severity": "critical",
                    "message": f"🔴 {label} is critically low at {value}{unit}",
                })
                feature_importance.append({"feature": label, "impact": "negative", "weight": 0.9})
            elif value <= thresholds["low"]:
                risk_factors.append({
                    "feature": label,
                    "value": f"{value}{unit}",
                    "severity": "warning",
                    "message": f"🟡 {label} is below average at {value}{unit}",
                })
                feature_importance.append({"feature": label, "impact": "negative", "weight": 0.5})
            else:
                strengths.append({
                    "feature": label,
                    "value": f"{value}{unit}",
                    "message": f"🟢 {label} is good at {value}{unit}",
                })
                feature_importance.append({"feature": label, "impact": "positive", "weight": 0.3})

    # Semester trend analysis
    sem_marks = []
    for i in range(1, 9):
        val = student_data.get(f"Sem{i}_Marks")
        if val is not None:
            sem_marks.append(float(val))
    
    if len(sem_marks) >= 2:
        trend = sem_marks[-1] - sem_marks[0]
        if trend < -10:
            risk_factors.append({
                "feature": "Semester Trend",
                "value": f"{trend:+.1f}",
                "severity": "critical" if trend < -20 else "warning",
                "message": f"🔴 Performance declining: {trend:+.1f} points from Sem1 to Sem{len(sem_marks)}",
            })
        elif trend > 10:
            strengths.append({
                "feature": "Semester Trend",
                "value": f"{trend:+.1f}",
                "message": f"🟢 Performance improving: {trend:+.1f} points across semesters",
            })

    # Generate recommendations based on risk factors
    for rf in risk_factors:
        feat = rf["feature"]
        if feat == "Attendance":
            recommendations.append({
                "type": "attendance",
                "priority": "high" if rf["severity"] == "critical" else "medium",
                "action": "Schedule mandatory attendance check-ins with faculty advisor",
                "expected_impact": "Improving attendance by 20% correlates with 15% grade improvement",
            })
        elif feat == "Study Hours":
            recommendations.append({
                "type": "study_plan",
                "priority": "high" if rf["severity"] == "critical" else "medium",
                "action": "Create a structured daily study schedule with timed sessions",
                "expected_impact": "Adding 5hrs/week of focused study can improve exam scores by 10-15%",
            })
        elif feat == "Assignment Completion":
            recommendations.append({
                "type": "assignments",
                "priority": "high",
                "action": "Implement deadline tracking system with weekly assignment reviews",
                "expected_impact": "Regular assignment completion is the #1 predictor of course success",
            })
        elif feat == "Stress Level":
            recommendations.append({
                "type": "counseling",
                "priority": "high" if rf["severity"] == "critical" else "medium",
                "action": "Refer student to academic counseling services for stress management",
                "expected_impact": "Stress reduction programs show 25% improvement in focus and retention",
            })
        elif feat == "Exam Score":
            recommendations.append({
                "type": "tutoring",
                "priority": "high",
                "action": "Assign peer tutor for exam preparation and concept reinforcement",
                "expected_impact": "Peer tutoring can improve exam scores by 10-20%",
            })

    # Generate narrative summary
    narrative = _generate_narrative(student_data, prediction, risk_factors, strengths)

    # Sort feature importance by weight
    feature_importance.sort(key=lambda x: x["weight"], reverse=True)

    return {
        "risk_factors": risk_factors,
        "strengths": strengths,
        "recommendations": recommendations,
        "narrative": narrative,
        "feature_importance": feature_importance,
        "risk_summary": {
            "critical_count": sum(1 for r in risk_factors if r["severity"] == "critical"),
            "warning_count": sum(1 for r in risk_factors if r["severity"] == "warning"),
            "strength_count": len(strengths),
        }
    }


def _generate_narrative(student_data: dict, prediction: dict, risks: list, strengths: list) -> str:
    """Generate a precise, data-driven narrative about the student risk."""
    name = student_data.get("Name", student_data.get("RollNo", "Student"))
    risk_level = prediction.get("risk_level", "UNKNOWN")
    
    # Precise Risk Explanation (Hackathon Requirement)
    if risk_level == "HIGH":
        critical_items = [r for r in risks if r["severity"] == "critical"]
        if critical_items:
            reasons = " and ".join([f"{r['feature']} is {r['value']}" for r in critical_items[:2]])
            narrative = f"Risk is HIGH because {reasons} (below 40% threshold)."
        else:
            narrative = f"Risk is HIGH due to overall low academic performance and predicted failure."
    elif risk_level == "MEDIUM":
        warning_items = [r for r in risks if r["severity"] == "warning"]
        if warning_items:
            reasons = " and ".join([f"{r['feature']} is {r['value']}" for r in warning_items[:2]])
            narrative = f"Risk is MEDIUM because {reasons} are below standard levels."
        else:
            narrative = f"Risk is MEDIUM. Student shows inconsistent performance across metrics."
    else:
        narrative = f"Risk is LOW. Student is performing well above benchmarks."

    return narrative


def generate_class_narrative(students_with_predictions: list[dict]) -> str:
    """Generate a storytelling narrative about the entire class."""
    total = len(students_with_predictions)
    if total == 0:
        return "No student data available for analysis."

    high_risk = [s for s in students_with_predictions if s.get("risk_level") == "HIGH"]
    medium_risk = [s for s in students_with_predictions if s.get("risk_level") == "MEDIUM"]
    low_risk = [s for s in students_with_predictions if s.get("risk_level") == "LOW"]

    narrative = f"# 📖 Class Performance Story\n\n"
    narrative += f"In this class of **{total}** students, the AI has identified distinct performance clusters:\n\n"
    
    # The Crisis Zone
    if high_risk:
        narrative += f"## 🔴 The Critical Zone ({len(high_risk)} students)\n\n"
        narrative += f"**{len(high_risk)}** students are at high risk of academic failure. "
        if len(high_risk) <= 5:
            names = [s.get("student_data", {}).get("Name", s.get("student_data", {}).get("RollNo", "Unknown")) for s in high_risk]
            narrative += f"They are: **{', '.join(names)}**. "
        narrative += "These students require immediate intervention — the window for recovery is narrowing. "
        
        # Find common risk patterns
        common_issues = {}
        for s in high_risk:
            data = s.get("student_data", {})
            if float(data.get("Attendance", 100)) < 60:
                common_issues["low attendance"] = common_issues.get("low attendance", 0) + 1
            if float(data.get("StudyHours", 100)) < 10:
                common_issues["insufficient study hours"] = common_issues.get("insufficient study hours", 0) + 1
            if float(data.get("StressLevel", 0)) > 3:
                common_issues["high stress"] = common_issues.get("high stress", 0) + 1
        
        if common_issues:
            top_issue = max(common_issues.items(), key=lambda x: x[1])
            narrative += f"The most common issue among them is **{top_issue[0]}** ({top_issue[1]} students).\n\n"
    
    # The Watch Zone
    if medium_risk:
        narrative += f"## 🟡 The Watch Zone ({len(medium_risk)} students)\n\n"
        narrative += f"**{len(medium_risk)}** students are on the borderline. "
        narrative += "With targeted support, they can move to the safe zone. Without it, they may slip into critical territory.\n\n"
    
    # The Safe Zone
    if low_risk:
        narrative += f"## 🟢 The Achievers ({len(low_risk)} students)\n\n"
        narrative += f"**{len(low_risk)}** students are performing well. "
        narrative += "Some of them are excellent candidates for peer tutoring roles, helping at-risk classmates.\n\n"

    # Overall health
    health_pct = round(len(low_risk) / total * 100) if total > 0 else 0
    narrative += f"## 📈 Class Health Score: **{health_pct}%**\n\n"
    narrative += f"_{health_pct}% of students are in the safe zone. Target: >80%._"

    return narrative
