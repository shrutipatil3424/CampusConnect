"""Sample data: default admin, a demo student and 20 upcoming events.

Run manually with:  python -m database.seed_data
The app also calls seed_if_empty() on first start (only when no admin account exists yet).
"""
import os
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from database.db_connection import execute, fetch_one, init_db


def _event(days, hour, title, category, organizer, venue, mode, difficulty, fee, capacity, tags, courses,
           description):
    start = (datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=days))
    return {
        "title": title, "category": category, "organizer": organizer, "venue": venue, "mode": mode,
        "difficulty": difficulty, "fee": fee, "capacity": capacity, "tags": tags, "target_courses": courses,
        "description": description, "event_date": start,
        "registration_deadline": start - timedelta(days=2),
    }


def sample_events() -> list:
    return [
        _event(6, 10, "Machine Learning with Scikit-learn Bootcamp", "Workshop", "Department of Computer Applications",
               "Zoom (link shared after registration)", "Online", "Beginner", 0, 120,
               "machine learning, python, scikit-learn, data science, pandas", "MCA, BCA, BE/BTech",
               "A hands-on bootcamp covering supervised learning, TF-IDF text features, model evaluation and "
               "building your first recommender system with scikit-learn and pandas."),
        _event(12, 9, "National 24-Hour AI Innovation Hackathon", "Hackathon", "Innovation Cell",
               "Main Auditorium and Labs", "Offline", "Intermediate", 200, 150,
               "artificial intelligence, hackathon, python, innovation, machine learning", "All",
               "Build an AI-powered solution to a real campus or social problem in 24 hours. Mentors from "
               "industry will guide teams and the top three teams win cash prizes and internship interviews."),
        _event(9, 11, "Full Stack Web Development Masterclass", "Workshop", "Web Developers Club",
               "Computer Lab 3", "Hybrid", "Beginner", 150, 80,
               "web development, javascript, html, css, apis, full stack", "BCA, BCS, MCA, BE/BTech",
               "Learn how modern web apps are built end to end: responsive front ends, REST APIs, databases and "
               "deployment. Includes a mini project that you will finish during the session."),
        _event(15, 14, "Cyber Security & Ethical Hacking Seminar", "Seminar", "Cyber Security Forum",
               "Seminar Hall B", "Offline", "Beginner", 0, 200,
               "cyber security, ethical hacking, networking, penetration testing, linux", "All",
               "An industry expert explains how attackers think, common web vulnerabilities and how to start a "
               "career in cyber security, with a live demonstration of defensive techniques."),
        _event(8, 10, "CodeSprint: Competitive Programming Contest", "Coding Competition", "Coding Club",
               "HackerRank (online)", "Online", "Intermediate", 0, 300,
               "data structures, algorithms, competitive programming, c++, java, problem solving", "All",
               "A 3-hour contest with 6 algorithmic problems ranging from easy to hard. Rankings are published "
               "live and the top 10 participants receive certificates and goodies."),
        _event(18, 10, "Cloud Computing with AWS Workshop", "Workshop", "Cloud Computing Society",
               "Zoom (link shared after registration)", "Online", "Intermediate", 100, 100,
               "cloud computing, aws, devops, docker, deployment", "MCA, BE/BTech",
               "Deploy a real application on AWS: launch servers, configure storage and databases, and set up "
               "a simple CI/CD pipeline. Covers cost control and certification pathways."),
        _event(5, 16, "Resume Building & LinkedIn Branding Session", "Career Development", "Training & Placement Cell",
               "Google Meet", "Online", "Beginner", 0, 250,
               "resume, linkedin, career, placement, personal branding", "All",
               "Learn how recruiters shortlist profiles. Build an ATS-friendly resume, write a strong LinkedIn "
               "headline and showcase projects so that you stand out in campus placements."),
        _event(21, 9, "Mock Interviews & Group Discussion Drive", "Career Development", "Training & Placement Cell",
               "Placement Cell, Block A", "Offline", "Intermediate", 0, 90,
               "interview, group discussion, placement, communication, career", "All",
               "Face real interview panels from partner companies and receive written feedback on technical, "
               "HR and group discussion rounds to improve before the actual placement season."),
        _event(10, 15, "Data Science Career Roadmap Seminar", "Seminar", "Data Science Club",
               "Zoom (link shared after registration)", "Online", "Beginner", 0, 300,
               "data science, data analyst, python, sql, career, machine learning", "MCA, BCA, BE/BTech",
               "A senior data scientist maps out the skills, projects and certifications needed to become a "
               "data analyst, data scientist or ML engineer, and answers your career questions."),
        _event(30, 9, "Open Innovation Hackathon: Smart Campus", "Hackathon", "Innovation Cell & Industry Partners",
               "Innovation Centre", "Offline", "Advanced", 300, 100,
               "hackathon, iot, innovation, web development, artificial intelligence, startup", "All",
               "A 36-hour open innovation hackathon where teams design smart-campus solutions using AI, IoT or "
               "web technologies. Winning ideas are incubated by the college innovation centre."),
        _event(7, 11, "SQL & Database Design Challenge", "Coding Competition", "Database Systems Group",
               "Computer Lab 1", "Offline", "Beginner", 0, 60,
               "sql, mysql, database management, query optimization, data modelling", "BCA, BCS, MCA",
               "Solve timed SQL puzzles and design a normalised schema for a real-world case study. Covers joins, "
               "indexing and query optimisation with MySQL."),
        _event(25, 10, "Android App Development Workshop", "Workshop", "Mobile Dev Community",
               "Computer Lab 2", "Offline", "Intermediate", 250, 50,
               "mobile app development, android, kotlin, java, ui design", "BCA, MCA, BE/BTech",
               "Build and run a complete Android application using Kotlin: layouts, navigation, local storage "
               "and calling a REST API. Bring your laptop with Android Studio installed."),
        _event(13, 13, "UI/UX Design Sprint", "Technical Event", "Design Club",
               "Seminar Hall A and Figma", "Hybrid", "Beginner", 100, 70,
               "ui/ux design, figma, prototyping, user research, design thinking", "All",
               "A one-day design sprint: research users, sketch flows, build a clickable Figma prototype and "
               "present it to a panel of designers and product managers."),
        _event(17, 15, "Blockchain & Web3 Fundamentals Seminar", "Seminar", "Blockchain Club",
               "Zoom (link shared after registration)", "Online", "Beginner", 0, 250,
               "blockchain, web3, cryptography, smart contracts, security", "All",
               "Understand how blockchains work, what smart contracts are and where Web3 is used in industry, "
               "with a simple demo of deploying a contract on a test network."),
        _event(23, 10, "NLP & Generative AI Workshop", "Workshop", "AI Research Lab",
               "AI Lab, Block C", "Hybrid", "Advanced", 200, 60,
               "natural language processing, generative ai, llm, python, gemini, machine learning", "MCA, BE/BTech",
               "Work with text data and large language models: tokenisation, embeddings, TF-IDF versus "
               "transformers, prompt design and building a small chatbot using the Gemini API."),
        _event(35, 10, "IoT & Embedded Systems Expo", "Technical Event", "Electronics & IoT Club",
               "Exhibition Ground", "Offline", "Intermediate", 0, 300,
               "internet of things, embedded systems, arduino, sensors, automation", "BE/BTech, MCA",
               "Student teams showcase working IoT prototypes, from smart irrigation to health monitors, with "
               "live demos, expert talks and a best-project award."),
        _event(11, 14, "Open Source Contribution Day (Git & GitHub)", "Technical Event", "Open Source Community",
               "Google Meet", "Online", "Beginner", 0, 200,
               "open source, git, github, collaboration, python, web development", "All",
               "Make your first open-source pull request. Learn Git workflows, how to find beginner-friendly "
               "issues and how to write good commit messages with guidance from maintainers."),
        _event(28, 11, "Startup Pitch & Entrepreneurship Summit", "Career Development", "E-Cell",
               "Main Auditorium", "Offline", "Beginner", 50, 200,
               "entrepreneurship, startup, pitching, product management, innovation", "All",
               "Hear founders share their journeys, pitch your own startup idea to investors and learn about "
               "incubation support, funding schemes and building a minimum viable product."),
        _event(14, 10, "Data Visualization with Pandas & Power BI", "Workshop", "Analytics Club",
               "Computer Lab 4", "Offline", "Intermediate", 0, 70,
               "data visualization, pandas, power bi, data analyst, python, sql", "MCA, BCA, BCS",
               "Turn raw data into dashboards: clean data with pandas, create charts, build an interactive "
               "Power BI report and learn storytelling with data."),
        _event(19, 16, "Placement Prep: Aptitude & DSA Crash Course", "Career Development", "Training & Placement Cell",
               "Lecture Hall 5 and Zoom", "Hybrid", "Intermediate", 0, 250,
               "placement, aptitude, data structures, algorithms, interview, problem solving", "All",
               "A focused crash course on quantitative aptitude, logical reasoning and the data structures and "
               "algorithms topics that appear most often in campus placement tests."),
    ]


def non_technical_events() -> list:
    """Events for non-technical interests (public speaking, leadership, creative arts, volunteering...)."""
    return [
        _event(8, 11, "Public Speaking & Confidence Building Workshop", "Soft Skills", "Communication Club",
               "Seminar Hall A", "Offline", "Beginner", 0, 80,
               "public speaking, communication skills, confidence, presentation skills, debate, personality development",
               "All",
               "Overcome stage fear and learn to speak clearly and confidently. Practise short speeches, voice "
               "control and body language with live feedback from trainers and fellow students."),
        _event(11, 10, "Leadership & Team Management Bootcamp", "Soft Skills", "Student Council",
               "Conference Room, Admin Block", "Offline", "Intermediate", 100, 60,
               "leadership, team management, teamwork, decision making, event management, personality development",
               "All",
               "A practical bootcamp on leading teams, delegating work, resolving conflicts and making decisions. "
               "Includes team challenges and a case study led by an industry manager."),
        _event(13, 15, "Creative & Content Writing Workshop", "Cultural & Creative", "Literary Society",
               "Library Seminar Room", "Hybrid", "Beginner", 0, 70,
               "creative writing, content writing, blogging, storytelling, writing, social media",
               "All",
               "Learn to write stories, blogs and social media content that people enjoy reading. Covers "
               "storytelling, editing your own work and building a writing portfolio."),
        _event(16, 10, "Photography & Video Editing Masterclass", "Cultural & Creative", "Photography Club",
               "Media Lab", "Offline", "Beginner", 150, 50,
               "photography, video editing, content creation, social media, creativity, design",
               "All",
               "Learn composition, lighting and mobile photography, then edit a short video using free tools. "
               "Bring a phone or camera; the best work is featured on the college page."),
        _event(19, 14, "Design Thinking & Innovation Workshop", "Soft Skills", "Innovation Cell",
               "Innovation Centre", "Hybrid", "Beginner", 0, 90,
               "design thinking, innovation, creativity, problem solving, entrepreneurship, teamwork",
               "All",
               "Solve a real problem with the design thinking process: empathise, define, ideate, prototype and "
               "test. Open to every course, no technical background needed."),
        _event(22, 11, "Time Management & Productivity Workshop", "Soft Skills", "Student Wellness Cell",
               "Zoom (link shared after registration)", "Online", "Beginner", 0, 200,
               "time management, productivity, study skills, personality development, stress management",
               "All",
               "Plan your semester, beat procrastination and balance studies with activities. Includes a "
               "personal planner template and simple habits that work during exam season."),
        _event(26, 17, "Inter-College Cultural Fest: Music, Dance & Drama Auditions", "Cultural & Creative",
               "Cultural Committee", "Open Air Theatre", "Offline", "Beginner", 0, 250,
               "music, dance, drama and theatre, performing arts, cultural fest, event management",
               "All",
               "Auditions for the inter-college cultural fest in music, dance and drama. Solo and group "
               "performances are welcome, and volunteers are needed for stage and event management."),
        _event(29, 10, "Digital Marketing & Social Media Branding Workshop", "Workshop", "Entrepreneurship Cell",
               "Computer Lab 2", "Hybrid", "Beginner", 100, 80,
               "digital marketing, social media, content creation, entrepreneurship, branding, content writing",
               "All",
               "Learn how brands grow online: social media strategy, content calendars, simple ads and analytics. "
               "Build a marketing plan for a small business idea during the session."),
        _event(33, 9, "Volunteering & Social Impact Drive", "Cultural & Creative", "NSS Unit",
               "College Main Gate", "Offline", "Beginner", 0, 150,
               "volunteering, social work, community service, leadership, teamwork, event management",
               "All",
               "Join a day of community service: a clean-up drive, a literacy session for school children and a "
               "blood donation camp. Earn volunteering hours and a participation certificate."),
    ]


def seed_non_technical_events() -> int:
    """Add the non-technical sample events to an existing database (only if none of them exist yet)."""
    new = non_technical_events()
    marks = ",".join(["%s"] * len(new))
    if fetch_one(f"SELECT id FROM events WHERE title IN ({marks}) LIMIT 1", [e["title"] for e in new]):
        return 0
    admin = fetch_one("SELECT id FROM students WHERE role='admin' ORDER BY id LIMIT 1")
    for e in new:
        _insert_event(e, admin["id"] if admin else None)
    return len(new)


def seed_admin() -> None:
    email = os.getenv("ADMIN_EMAIL", "admin@campusconnect.ai").strip().lower()
    if fetch_one("SELECT id FROM students WHERE email=%s", (email,)):
        return
    execute(
        """INSERT INTO students (full_name, email, password_hash, college_name, course, academic_year,
           technical_interests, skills, preferred_categories, career_interests, role)
           VALUES (%s,%s,%s,%s,'Other','4th Year','Administration','Event Management',
                   'Workshop, Seminar, Hackathon','Administrator','admin')""",
        (os.getenv("ADMIN_NAME", "CampusConnect Admin"), email,
         generate_password_hash(os.getenv("ADMIN_PASSWORD", "Admin@12345")), "CampusConnect College"),
    )


def seed_demo_student() -> None:
    email = "demo@campusconnect.ai"
    if fetch_one("SELECT id FROM students WHERE email=%s", (email,)):
        return
    execute(
        """INSERT INTO students (full_name, email, password_hash, college_name, course, academic_year,
           technical_interests, skills, preferred_categories, career_interests, role)
           VALUES ('Demo Student', %s, %s, 'Sample Institute of Technology', 'MCA', '2nd Year',
                   'Machine Learning, Data Science, Artificial Intelligence', 'Python, Pandas, SQL',
                   'Hackathon, Workshop, Career Development', 'Data Scientist, ML Engineer', 'student')""",
        (email, generate_password_hash("Demo@1234")),
    )


def _insert_event(e: dict, created_by) -> None:
    execute(
        """INSERT INTO events (title, description, category, organizer, venue, mode, difficulty,
           event_date, registration_deadline, capacity, fee, tags, target_courses, created_by)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (e["title"], e["description"], e["category"], e["organizer"], e["venue"], e["mode"],
         e["difficulty"], e["event_date"], e["registration_deadline"], e["capacity"], e["fee"],
         e["tags"], e["target_courses"], created_by),
    )


def seed_events() -> int:
    admin = fetch_one("SELECT id FROM students WHERE role='admin' ORDER BY id LIMIT 1")
    created_by = admin["id"] if admin else None
    events = sample_events() + non_technical_events()
    for e in events:
        _insert_event(e, created_by)
    return len(events)


def seed_if_empty() -> None:
    """First-run setup: only runs when there is no admin account yet."""
    if fetch_one("SELECT id FROM students WHERE role='admin' LIMIT 1"):
        return
    seed_admin()
    seed_demo_student()
    if not fetch_one("SELECT id FROM events LIMIT 1"):
        seed_events()


if __name__ == "__main__":
    init_db()
    seed_admin()
    seed_demo_student()
    if not fetch_one("SELECT id FROM events LIMIT 1"):
        print(f"Inserted {seed_events()} sample events.")
    else:
        print("Events already exist; skipped sample events.")
    added = seed_non_technical_events()
    if added:
        print(f"Added {added} non-technical sample events.")
    print("Admin and demo accounts are ready.")
