"""
Peer Tutoring Matcher — The X-Factor Feature.
Pairs at-risk students with high-performing students based on complementary strengths.
"""

import numpy as np
from typing import Optional


# Define subject/skill dimensions for matching
SKILL_DIMENSIONS = [
    "StudyHours", "Attendance", "AssignmentCompletion", 
    "ExamScore", "OnlineCourses", "Discussions"
]

DIMENSION_LABELS = {
    "StudyHours": "Study Discipline",
    "Attendance": "Class Engagement",
    "AssignmentCompletion": "Task Completion",
    "ExamScore": "Exam Performance",
    "OnlineCourses": "Self-Learning",
    "Discussions": "Collaborative Learning",
}


def _compute_skill_profile(student: dict) -> dict:
    """Compute a normalized skill profile for a student."""
    profile = {}
    for dim in SKILL_DIMENSIONS:
        val = float(student.get(dim, 0))
        # Normalize to 0-100 scale
        if dim == "StudyHours":
            profile[dim] = min(val / 40 * 100, 100)   # Max 40hrs
        elif dim == "Attendance":
            profile[dim] = min(val, 100)                # Already percentage
        elif dim == "AssignmentCompletion":
            profile[dim] = min(val, 100)
        elif dim == "ExamScore":
            profile[dim] = min(val, 100)
        elif dim == "OnlineCourses":
            profile[dim] = min(val / 5 * 100, 100)     # Max 5 courses
        elif dim == "Discussions":
            profile[dim] = min(val / 5 * 100, 100)     # Max 5 discussions
        else:
            profile[dim] = min(val, 100)
    return profile


def _complementarity_score(weak_profile: dict, strong_profile: dict) -> tuple[float, list[str]]:
    """
    Calculate how well a strong student complements a weak student.
    Higher score = better match.
    Returns (score, list_of_complementary_areas).
    """
    complement_areas = []
    total_complement = 0
    count = 0

    for dim in SKILL_DIMENSIONS:
        weak_val = weak_profile.get(dim, 0)
        strong_val = strong_profile.get(dim, 0)
        gap = strong_val - weak_val
        
        if gap > 20:  # Significant strength gap
            complement_areas.append({
                "skill": DIMENSION_LABELS.get(dim, dim),
                "weak_score": round(weak_val, 1),
                "tutor_score": round(strong_val, 1),
                "gap": round(gap, 1),
            })
            total_complement += gap
            count += 1

    match_score = round(total_complement / max(count, 1), 1)
    return match_score, complement_areas


def find_peer_matches(
    students_with_predictions: list[dict],
    max_matches_per_student: int = 3,
    risk_threshold: float = 40.0,
) -> list[dict]:
    """
    Find optimal peer tutoring pairs.
    
    Args:
        students_with_predictions: List of dicts with student data + prediction results
        max_matches_per_student: Max tutors to suggest per at-risk student
        risk_threshold: Min risk_score to be considered at-risk
    
    Returns:
        List of match objects with tutor/tutee info and match rationale
    """
    # Separate at-risk and high-performing students
    at_risk = []
    toppers = []
    
    for s in students_with_predictions:
        data = s.get("student_data", s)
        risk = s.get("risk_score", 0)
        name = data.get("Name", data.get("RollNo", "Unknown"))
        
        profile = _compute_skill_profile(data)
        entry = {
            "name": name,
            "roll_no": data.get("RollNo", "N/A"),
            "risk_score": risk,
            "risk_level": s.get("risk_level", "LOW"),
            "predicted_grade": s.get("predicted_grade", "N/A"),
            "profile": profile,
            "data": data,
        }
        
        if risk >= risk_threshold:
            at_risk.append(entry)
        elif risk < 25 and s.get("pass_fail", s.get("pass_probability", 0)):
            # High performers with low risk
            toppers.append(entry)
    
    # Sort at-risk by risk (highest first), toppers by risk (lowest first)
    at_risk.sort(key=lambda x: x["risk_score"], reverse=True)
    toppers.sort(key=lambda x: x["risk_score"])
    
    matches = []
    tutor_load = {}  # Track how many tutees each tutor is assigned
    
    for weak in at_risk:
        student_matches = []
        
        for strong in toppers:
            tutor_key = strong["roll_no"]
            if tutor_load.get(tutor_key, 0) >= 3:
                continue  # Don't overload a tutor
            
            match_score, areas = _complementarity_score(weak["profile"], strong["profile"])
            
            if match_score > 15 and len(areas) > 0:
                student_matches.append({
                    "match_score": match_score,
                    "tutor": {
                        "name": strong["name"],
                        "roll_no": strong["roll_no"],
                        "predicted_grade": strong["predicted_grade"],
                        "risk_score": strong["risk_score"],
                    },
                    "tutee": {
                        "name": weak["name"],
                        "roll_no": weak["roll_no"],
                        "predicted_grade": weak["predicted_grade"],
                        "risk_score": weak["risk_score"],
                        "risk_level": weak["risk_level"],
                    },
                    "complementary_areas": areas,
                    "rationale": _generate_rationale(weak, strong, areas),
                })
        
        # Sort by match score and take top N
        student_matches.sort(key=lambda x: x["match_score"], reverse=True)
        for m in student_matches[:max_matches_per_student]:
            tutor_load[m["tutor"]["roll_no"]] = tutor_load.get(m["tutor"]["roll_no"], 0) + 1
            matches.append(m)
    
    return matches


def _generate_rationale(weak: dict, strong: dict, areas: list[dict]) -> str:
    """Generate a human-readable rationale for the peer match."""
    if not areas:
        return "General academic support recommended."
    
    top_area = areas[0]
    rationale = (
        f"{strong['name']} excels in {top_area['skill']} "
        f"(score: {top_area['tutor_score']}%) and can help {weak['name']} "
        f"who scores {top_area['weak_score']}% in this area. "
    )
    
    if len(areas) > 1:
        other_areas = ", ".join(a["skill"] for a in areas[1:])
        rationale += f"Additional support areas: {other_areas}."
    
    return rationale
