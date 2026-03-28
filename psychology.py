"""
Psychology Factor Analysis — Generates Death Note-style hexagon profiles.
Maps student data to 6 psychological dimensions for radar chart visualization.
"""


# The 6 dimensions of the hexagon profile (inspired by Death Note character profiles)
HEXAGON_DIMENSIONS = [
    "Academic Score",
    "Consistency (Attendance)",
    "Continuous Evaluation (IA)",
    "Practical Application (Projects/ABA)",
    "Engagement",
    "Stress Management",
]


def compute_psychology_profile(student_data: dict) -> dict:
    """
    Compute a 6-axis psychology profile for a student.
    Each axis is scored 0-10 (like Death Note character stats).
    
    Maps academic data to psychological dimensions:
    - Intelligence: ExamScore + StudyHours efficiency
    - Creativity: Online courses + diverse learning
    - Social Life: Discussions + Extracurricular
    - Motivation: Motivation score + Assignment completion consistency
    - Willingness to Act: Attendance + Study Hours regularity
    - Stress Resilience: Inverse of stress level + performance under stress
    """
    
    # Extract values with defaults
    exam = float(student_data.get("ExamScore", 50))
    study = float(student_data.get("StudyHours", 10))
    attend = float(student_data.get("Attendance", 50))
    assign = float(student_data.get("AssignmentCompletion", 50))
    online = float(student_data.get("OnlineCourses", 0))
    discuss = float(student_data.get("Discussions", 0))
    extra = float(student_data.get("Extracurricular", 0))
    motivation = float(student_data.get("Motivation", 3))
    stress = float(student_data.get("StressLevel", 3))
    resources = float(student_data.get("Resources", 3))
    edu_tech = float(student_data.get("EduTech", 0))
    
    # Semester marks for trend analysis
    sem_marks = []
    for i in range(1, 9):
        val = student_data.get(f"Sem{i}_Marks")
        if val is not None:
            sem_marks.append(float(val))
    
    # Calculate each dimension (0-10 scale)
    
    # 1. Academic Score: Exam performance + Sem marks
    avg_sem = sum(sem_marks) / len(sem_marks) if sem_marks else 50
    academic_score = min(10, (exam / 100 * 5) + (avg_sem / 100 * 5))
    
    # 2. Consistency: Attendance
    consistency = min(10, attend / 10)
    
    # 3. Continuous Evaluation: IA scores
    ia1 = float(student_data.get("IA1", 0))
    ia2 = float(student_data.get("IA2", 0))
    ia3 = float(student_data.get("IA3", 0))
    avg_ia = (ia1 + ia2 + ia3) / 3
    continuous_eval = min(10, avg_ia / 10)
    
    # 4. Practical Application: Projects + ABA
    aba = float(student_data.get("ABA", 0))
    projects = float(student_data.get("ProjectsDone", 0))
    practical = min(10, (aba / 10) * 0.5 + (projects / 10) * 0.5)
    
    # 5. Engagement: Study Hours + Discussions + Online Courses
    engagement = min(10, (study / 40 * 4) + (discuss / 5 * 3) + (online / 5 * 3))
    
    # 6. Stress Management: Stress Level (Inverted)
    stress_mgmt = min(10, max(0, (5 - stress) * 2))
    
    profile = {
        "Academic Score": round(academic_score, 1),
        "Consistency (Attendance)": round(consistency, 1),
        "Continuous Evaluation (IA)": round(continuous_eval, 1),
        "Practical Application (Projects/ABA)": round(practical, 1),
        "Engagement": round(engagement, 1),
        "Stress Management": round(stress_mgmt, 1),
    }
    
    # Compute overall personality type
    personality_type = _classify_personality(profile)
    
    # Generate psychology insight
    insight = _generate_psychology_insight(student_data, profile, personality_type)
    
    return {
        "hexagon": profile,
        "dimensions": HEXAGON_DIMENSIONS,
        "personality_type": personality_type,
        "insight": insight,
        "overall_score": round(sum(profile.values()) / len(profile), 1),
    }


def _classify_personality(profile: dict) -> dict:
    """Classify student into a personality archetype based on their hexagon profile."""
    scores = profile
    
    # Find dominant and weak dimensions
    sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    dominant = sorted_dims[0]
    secondary = sorted_dims[1]
    weakest = sorted_dims[-1]
    
    # Determine archetype
    archetypes = {
        "The Scholar": lambda: scores["Intelligence"] >= 7 and scores["Motivation"] >= 6,
        "The Leader": lambda: scores["Social Life"] >= 7 and scores["Willingness to Act"] >= 6,
        "The Innovator": lambda: scores["Creativity"] >= 7 and scores["Intelligence"] >= 5,
        "The Resilient": lambda: scores["Stress Resilience"] >= 7 and scores["Motivation"] >= 5,
        "The Social Butterfly": lambda: scores["Social Life"] >= 7 and scores["Creativity"] >= 5,
        "The Determined": lambda: scores["Willingness to Act"] >= 7 and scores["Motivation"] >= 6,
        "The Balanced": lambda: all(v >= 4 for v in scores.values()),
        "The Struggler": lambda: sum(1 for v in scores.values() if v < 4) >= 3,
    }
    
    archetype = "The Learner"  # default
    for name, check in archetypes.items():
        if check():
            archetype = name
            break
    
    return {
        "archetype": archetype,
        "dominant_trait": dominant[0],
        "dominant_score": dominant[1],
        "secondary_trait": secondary[0],
        "growth_area": weakest[0],
        "growth_score": weakest[1],
    }


def _generate_psychology_insight(student_data: dict, profile: dict, personality: dict) -> str:
    """Generate a psychological insight narrative."""
    name = student_data.get("Name", student_data.get("RollNo", "This student"))
    archetype = personality["archetype"]
    dominant = personality["dominant_trait"]
    growth = personality["growth_area"]
    
    insight = f"**{name}** fits the **\"{archetype}\"** profile. "
    insight += f"Their strongest dimension is **{dominant}** ({profile[dominant]}/10), "
    insight += f"while **{growth}** ({profile[growth]}/10) presents the greatest opportunity for development. "
    
    # Specific psychological observations
    if profile.get("Stress Resilience", 5) < 4:
        insight += "⚠️ Low stress resilience suggests this student may benefit from mindfulness or counseling support. "
    if profile.get("Social Life", 5) < 3:
        insight += "This student appears socially disengaged — group activities or peer mentoring could help. "
    if profile.get("Motivation", 5) >= 7:
        insight += "High motivation is a great asset — channel this energy with clear goals and challenges. "
    
    return insight


def batch_psychology_profiles(students: list[dict]) -> list[dict]:
    """Generate psychology profiles for a batch of students."""
    return [
        {
            "student_data": s,
            "psychology": compute_psychology_profile(s),
        }
        for s in students
    ]
