"""
TesseractX — FastAPI Backend Server
Student Performance Prediction & Monitoring System

Endpoints:
  POST /api/auth/login          — Email-based role auth
  POST /api/students/predict    — Predict single student
  POST /api/students/batch      — Predict batch of students
  POST /api/students/peer-match — Find peer tutoring pairs
  POST /api/analytics/xai       — Get XAI insights for a student
  POST /api/analytics/psychology — Get psychology hexagon profile
  POST /api/analytics/class-summary — Get class-level analytics
  POST /api/analytics/narrative  — Get storytelling narrative
  GET  /api/health              — Health check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import json
import datetime

# Import our modules
from ml_engine import predict_student, predict_batch
from peer_matcher import find_peer_matches
from xai_engine import generate_xai_insights, generate_class_narrative
from psychology import compute_psychology_profile, batch_psychology_profiles

app = FastAPI(
    title="TesseractX API",
    description="Student Performance Prediction & Monitoring System",
    version="1.0.0",
)

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Pydantic Models ─────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: Optional[str] = None

class LoginResponse(BaseModel):
    success: bool
    role: Optional[str] = None
    name: Optional[str] = None
    message: str

class StudentData(BaseModel):
    RollNo: Optional[str] = None
    Name: Optional[str] = None
    Gender: Optional[str] = "Male"
    Age: Optional[int] = 20
    StudyHours: float = 0
    Attendance: float = 0
    Resources: float = 0
    Extracurricular: float = 0
    Motivation: float = 0
    Internet: float = 0
    LearningStyle: float = 0
    OnlineCourses: float = 0
    Discussions: float = 0
    AssignmentCompletion: float = 0
    ExamScore: float = 0
    EduTech: float = 0
    StressLevel: float = 0
    Sem1_Marks: Optional[float] = None
    Sem2_Marks: Optional[float] = None
    Sem3_Marks: Optional[float] = None
    Sem4_Marks: Optional[float] = None
    Sem5_Marks: Optional[float] = None
    Sem6_Marks: Optional[float] = None
    Sem7_Marks: Optional[float] = None
    Sem8_Marks: Optional[float] = None
    IA1: Optional[float] = 0
    IA2: Optional[float] = 0
    IA3: Optional[float] = 0
    Assessments: Optional[float] = 0
    ABA: Optional[float] = 0
    ProjectsDone: Optional[float] = 0

class BatchPredictRequest(BaseModel):
    students: list[StudentData]
    course: Optional[str] = None
    semester: Optional[str] = None
    section: Optional[str] = None
    subject: Optional[str] = None

class PeerMatchRequest(BaseModel):
    students: list[StudentData]

class XAIRequest(BaseModel):
    student: StudentData
    prediction: Optional[dict] = None

class PsychologyRequest(BaseModel):
    student: StudentData

class ClassSummaryRequest(BaseModel):
    students: list[StudentData]

class NarrativeRequest(BaseModel):
    students: list[StudentData]

class LMSRecommendation(BaseModel):
    student_id: str
    insight: str
    resource_link: str
    student_email: Optional[str] = None
    risk_explanation: Optional[str] = None

# Admin Models
class AdminTeacher(BaseModel):
    name: str
    email: str
    department: str

class AdminCourse(BaseModel):
    id: str
    name: str
    department: str

class AdminMeeting(BaseModel):
    link: str
    title: str = "Staff Meeting"
    timestamp: Optional[str] = None

class AdminSettings(BaseModel):
    institution_name: str = "VVCE Institution"
    system_status: str = "Active"
    maintenance_mode: bool = False
    public_registrations: bool = True
    ai_intensity: str = "ULTRA"
    total_students: int = 1250


# ─── Auth Endpoint ────────────────────────────────────────────────────────────

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """Validate email suffix and return role."""
    email = req.email.strip().lower()
    
    if email.endswith("@admin.ac.in"):
        name = email.split("@")[0].replace(".", " ").title()
        return LoginResponse(success=True, role="admin", name=name, message="Welcome, Administrator!")
    elif email.endswith("@vvce.ac.in"):
        name = email.split("@")[0].replace(".", " ").title()
        return LoginResponse(success=True, role="teacher", name=name, message=f"Welcome, {name}!")
    else:
        return LoginResponse(success=False, role=None, name=None, message="Invalid email domain. Use @admin.ac.in or @vvce.ac.in")


# ─── Student Prediction Endpoints ────────────────────────────────────────────

@app.post("/api/students/predict")
async def predict_single(student: StudentData):
    """Predict a single student's performance."""
    try:
        data = student.model_dump(exclude_none=False)
        prediction = predict_student(data)
        
        # Also generate XAI insights
        xai = generate_xai_insights(data, prediction)
        
        # Also generate psychology profile
        psych = compute_psychology_profile(data)
        
        return {
            "success": True,
            "prediction": prediction,
            "xai_insights": xai,
            "psychology": psych,
            "student_data": data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/api/students/batch")
async def predict_batch_endpoint(req: BatchPredictRequest):
    """Predict performance for a batch of students."""
    try:
        students_data = [s.model_dump(exclude_none=False) for s in req.students]
        
        # Predict all students and include XAI insights
        predictions = []
        for s_data in students_data:
            p = predict_student(s_data)
            p["xai_insights"] = generate_xai_insights(s_data, p)
            p["student_data"] = s_data
            predictions.append(p)
        
        # Compute risk distribution
        risk_dist = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        grade_dist = {}
        total_risk = 0
        
        for p in predictions:
            risk_dist[p.get("risk_level", "LOW")] += 1
            grade = p.get("predicted_grade", "N/A")
            grade_dist[grade] = grade_dist.get(grade, 0) + 1
            total_risk += p.get("risk_score", 0)
        
        avg_risk = round(total_risk / len(predictions), 1) if predictions else 0
        
        # Sort by risk — highest risk first
        predictions.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
        
        return {
            "success": True,
            "predictions": predictions,
            "summary": {
                "total_students": len(predictions),
                "risk_distribution": risk_dist,
                "grade_distribution": grade_dist,
                "average_risk_score": avg_risk,
                "class_health": round(100 - avg_risk, 1),
                "critical_alert_count": risk_dist.get("HIGH", 0),
            },
            "metadata": {
                "course": req.course,
                "semester": req.semester,
                "section": req.section,
                "subject": req.subject,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")


# ─── Peer Matching Endpoint ──────────────────────────────────────────────────

@app.post("/api/students/peer-match")
async def peer_match(req: PeerMatchRequest):
    """Find peer tutoring pairs based on complementary strengths."""
    try:
        students_data = [s.model_dump(exclude_none=False) for s in req.students]
        # First predict all students
        predictions = predict_batch(students_data)
        
        # Find matches
        matches = find_peer_matches(predictions)
        
        return {
            "success": True,
            "matches": matches,
            "total_matches": len(matches),
            "at_risk_count": sum(1 for p in predictions if p.get("risk_level") == "HIGH"),
            "available_tutors": sum(1 for p in predictions if p.get("risk_level") == "LOW"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Peer matching failed: {str(e)}")


# ─── Analytics Endpoints ─────────────────────────────────────────────────────

@app.post("/api/analytics/xai")
async def xai_insights(req: XAIRequest):
    """Get explainable AI insights for a student."""
    try:
        data = req.student.model_dump(exclude_none=False)
        
        # Get prediction if not provided
        prediction = req.prediction or predict_student(data)
        
        insights = generate_xai_insights(data, prediction)
        
        return {
            "success": True,
            "student": data.get("Name", data.get("RollNo", "Unknown")),
            "prediction": prediction,
            "insights": insights,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"XAI analysis failed: {str(e)}")


@app.post("/api/analytics/psychology")
async def psychology_profile(req: PsychologyRequest):
    """Get Death Note-style hexagon psychology profile."""
    try:
        data = req.student.model_dump(exclude_none=False)
        profile = compute_psychology_profile(data)
        
        return {
            "success": True,
            "student": data.get("Name", data.get("RollNo", "Unknown")),
            "profile": profile,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Psychology analysis failed: {str(e)}")


@app.post("/api/analytics/class-summary")
async def class_summary(req: ClassSummaryRequest):
    """Get class-level analytics summary."""
    try:
        students_data = [s.model_dump(exclude_none=False) for s in req.students]
        predictions = predict_batch(students_data)
        
        # Compute comprehensive summary
        risk_dist = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        grade_dist = {}
        total_risk = 0
        attendance_sum = 0
        study_hours_sum = 0
        stress_sum = 0
        
        high_risk_students = []
        
        for p in predictions:
            data = p.get("student_data", {})
            risk_dist[p.get("risk_level", "LOW")] += 1
            grade = p.get("predicted_grade", "N/A")
            grade_dist[grade] = grade_dist.get(grade, 0) + 1
            total_risk += p.get("risk_score", 0)
            attendance_sum += float(data.get("Attendance", 0))
            study_hours_sum += float(data.get("StudyHours", 0))
            stress_sum += float(data.get("StressLevel", 0))
            
            if p.get("risk_level") == "HIGH":
                high_risk_students.append({
                    "name": data.get("Name", data.get("RollNo", "Unknown")),
                    "roll_no": data.get("RollNo", "N/A"),
                    "risk_score": p.get("risk_score", 0),
                    "predicted_grade": p.get("predicted_grade", "N/A"),
                })
        
        n = len(predictions) or 1
        
        return {
            "success": True,
            "summary": {
                "total_students": len(predictions),
                "risk_distribution": risk_dist,
                "grade_distribution": grade_dist,
                "average_risk_score": round(total_risk / n, 1),
                "class_health": round(100 - total_risk / n, 1),
                "average_attendance": round(attendance_sum / n, 1),
                "average_study_hours": round(study_hours_sum / n, 1),
                "average_stress": round(stress_sum / n, 1),
            },
            "high_risk_alerts": high_risk_students,
            "predictions": predictions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Class summary failed: {str(e)}")


@app.post("/api/analytics/narrative")
async def narrative(req: NarrativeRequest):
    """Get AI-generated storytelling narrative about the class."""
    try:
        students_data = [s.model_dump(exclude_none=False) for s in req.students]
        predictions = predict_batch(students_data)
        
        class_story = generate_class_narrative(predictions)
        
        # Also generate individual snapshots for top 5 at-risk
        high_risk = [p for p in predictions if p.get("risk_level") == "HIGH"][:5]
        individual_stories = []
        for p in high_risk:
            data = p.get("student_data", {})
            insights = generate_xai_insights(data, p)
            individual_stories.append({
                "student": data.get("Name", data.get("RollNo", "Unknown")),
                "risk_score": p.get("risk_score", 0),
                "narrative": insights["narrative"],
                "risk_factors": insights["risk_factors"][:3],
                "top_recommendation": insights["recommendations"][0] if insights["recommendations"] else None,
            })
        
        return {
            "success": True,
            "class_narrative": class_story,
            "individual_spotlights": individual_stories,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Narrative generation failed: {str(e)}")


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "TesseractX API", "ml_loaded": True}


# ─── LMS & Recommendations (Hackathon Mode) ──────────────────────────────────

LMS_DB_FILE = "lms_database.json"

def get_lms_db():
    if not os.path.exists(LMS_DB_FILE):
        return {}
    with open(LMS_DB_FILE, "r") as f:
        return json.load(f)

def save_lms_db(data):
    with open(LMS_DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.post("/api/lms/recommend")
async def recommend_resource(req: LMSRecommendation):
    """Store recommendation and notify student."""
    db = get_lms_db()
    
    student_id = req.student_id
    if student_id not in db:
        db[student_id] = []
    
    new_entry = {
        "insight": req.insight,
        "link": req.resource_link,
        "timestamp": str(json.dumps(None)), # Placeholder for simplistic hackathon timestamp
    }
    # Using a simple datetime placeholder
    from datetime import datetime
    new_entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    db[student_id].append(new_entry)
    save_lms_db(db)
    
    # Email Notification
    if req.student_email:
        send_student_email(
            req.student_email,
            req.insight,
            req.resource_link,
            req.risk_explanation or "High Risk Alert"
        )
    
    return {"success": True, "message": "Recommendation saved and student notified."}

@app.get("/api/lms/resources/{student_id}")
async def get_resources(student_id: str):
    """Get resources for a specific student."""
    db = get_lms_db()
    return {"success": True, "resources": db.get(student_id, [])}


# ─── Email Notification System ───────────────────────────────────────────────

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_student_email(student_email: str, insight: str, link: str, risk_explanation: str):
    """Send automated recommendation email to student."""
    # USER CONFIG (To be provided by user, using placeholders for now)
    SENDER_EMAIL = "your-hackathon-email@gmail.com" 
    APP_PASSWORD = "your-app-password"
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = student_email
        msg['Subject'] = "TesseractX: Academic Support & Resources"
        
        body = f"""
        Hello,

        Your teacher has provided a new insight and resource to help you improve your academic performance.

        Teacher's Insight:
        {insight}

        Recommended Resource:
        {link}

        AI Risk Analysis:
        {risk_explanation}

        Stay focused and keep learning!
        - TesseractX Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        # server.login(SENDER_EMAIL, APP_PASSWORD) # Commented out until user provides creds
        # server.send_message(msg)
        # server.quit()
        print(f"[EMAIL] Logic triggered for {student_email} (Login commented out for safety)")
        
    except Exception as e:
        print(f"[EMAIL ERROR] {str(e)}")


# ─── Admin Management (Hackathon Mode) ───────────────────────────────────────

ADMIN_DB_FILE = "admins_database.json"

def get_admin_db():
    if not os.path.exists(ADMIN_DB_FILE):
        return {
            "teachers": [
                {"name": "Dr. Ramesh Kumar", "email": "ramesh@vvce.ac.in", "department": "Computer Science"},
                {"name": "Prof. Sunita Verma", "email": "sunita@vvce.ac.in", "department": "Information Science"},
            ],
            "courses": [
                {"id": "CS101", "name": "Computer Science", "department": "CSE"},
                {"id": "IS101", "name": "Information Science", "department": "ISE"}
            ],
            "meeting": {"link": "https://meet.google.com/abc-defg-hij", "title": "Main Faculty Meeting"},
            "settings": {"institution_name": "TesseractX Academy", "system_status": "Operational"}
        }
    with open(ADMIN_DB_FILE, "r") as f:
        return json.load(f)

def save_admin_db(data):
    with open(ADMIN_DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.get("/api/admin/teachers")
async def get_teachers():
    db = get_admin_db()
    return {"success": True, "teachers": db.get("teachers", [])}

@app.post("/api/admin/teachers")
async def add_teacher(teacher: AdminTeacher):
    db = get_admin_db()
    db["teachers"].append(teacher.model_dump())
    save_admin_db(db)
    return {"success": True, "message": "Teacher added."}

@app.delete("/api/admin/teachers")
async def remove_teacher(email: str):
    try:
        db = get_admin_db()
        db["teachers"] = [t for t in db["teachers"] if t["email"] != email]
        save_admin_db(db)
        return {"success": True, "message": "Teacher removed."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/courses")
async def get_courses():
    db = get_admin_db()
    return {"success": True, "courses": db.get("courses", [])}

@app.post("/api/admin/courses")
async def add_course(course: AdminCourse):
    db = get_admin_db()
    db["courses"].append(course.model_dump())
    save_admin_db(db)
    return {"success": True, "message": "Course added."}

@app.delete("/api/admin/courses")
async def remove_course(course_id: str):
    try:
        db = get_admin_db()
        db["courses"] = [c for c in db["courses"] if c["id"] != course_id]
        save_admin_db(db)
        return {"success": True, "message": "Course removed."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/meeting")
async def get_meeting():
    db = get_admin_db()
    return {"success": True, "meeting": db.get("meeting", {})}

@app.post("/api/admin/meeting")
async def set_meeting(meeting: AdminMeeting):
    db = get_admin_db()
    db["meeting"] = meeting.model_dump()
    from datetime import datetime
    db["meeting"]["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_admin_db(db)
    return {"success": True, "message": "Meeting link updated."}

@app.get("/api/admin/institution-summary")
async def get_institution_summary():
    """Mock institution-wide summary for hackathon demo."""
    try:
        db = get_admin_db()
        settings = db.get("settings", {})
        return {
            "success": True,
            "total_teachers": len(db.get("teachers", [])),
            "total_courses": len(db.get("courses", [])),
            "total_students": settings.get("total_students", 1250),
            "risk_rate": "12.5%",
            "institution_name": settings.get("institution_name", "TesseractX Academy")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/settings")
async def get_settings():
    try:
        db = get_admin_db()
        defaults = {
            "institution_name": "TesseractX Academy",
            "system_status": "Operational",
            "maintenance_mode": False,
            "public_registrations": True,
            "ai_intensity": "ULTRA",
            "total_students": 1250
        }
        current_settings = db.get("settings", {})
        merged = {**defaults, **current_settings}
        return {"success": True, "settings": merged}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/settings")
async def update_settings(settings: AdminSettings):
    try:
        db = get_admin_db()
        db["settings"] = settings.model_dump() if hasattr(settings, "model_dump") else settings.dict()
        save_admin_db(db)
        return {"success": True, "message": "Settings updated."}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Run Server ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
