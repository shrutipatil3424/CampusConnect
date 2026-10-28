"""Static option lists and labels used across the app."""

APP_NAME = "CampusConnect AI"
APP_TAGLINE = "Personalized College Event Discovery System"

COURSES = ["BCA", "BCS", "MCA", "BE/BTech", "Other"]
ACADEMIC_YEARS = ["1st Year", "2nd Year", "3rd Year", "4th Year"]

EVENT_CATEGORIES = [
    "Workshop",
    "Seminar",
    "Hackathon",
    "Coding Competition",
    "Technical Event",
    "Career Development",
    "Soft Skills",
    "Cultural & Creative",
]
CATEGORY_ICONS = {
    "Workshop": "🛠️",
    "Seminar": "🎤",
    "Hackathon": "🚀",
    "Coding Competition": "💻",
    "Technical Event": "⚙️",
    "Career Development": "💼",
    "Soft Skills": "🗣️",
    "Cultural & Creative": "🎨",
}

EVENT_MODES = ["Online", "Offline", "Hybrid"]
DIFFICULTY_LEVELS = ["Beginner", "Intermediate", "Advanced"]
REGISTRATION_STATUSES = ["Registered", "Attended", "Cancelled"]

TECH_INTERESTS = [
    "Artificial Intelligence", "Machine Learning", "Data Science", "Natural Language Processing",
    "Computer Vision", "Generative AI", "Web Development", "Mobile App Development",
    "Cloud Computing", "DevOps", "Cyber Security", "Blockchain", "Internet of Things",
    "Data Structures and Algorithms", "Competitive Programming", "Database Management",
    "UI/UX Design", "Game Development", "Big Data", "Open Source",
]

NON_TECH_INTERESTS = [
    "Public Speaking", "Leadership", "Communication Skills", "Team Management", "Time Management",
    "Creative Writing", "Content Writing", "Photography", "Video Editing", "Design Thinking",
    "Digital Marketing", "Social Media", "Entrepreneurship", "Music", "Dance", "Drama and Theatre",
    "Volunteering", "Event Management", "Debate", "Personality Development",
]
# Everything a student can pick in the interests field (technical first, then non-technical).
INTERESTS = TECH_INTERESTS + NON_TECH_INTERESTS

SKILLS = [
    "Python", "Java", "C/C++", "JavaScript", "SQL", "HTML/CSS", "Pandas", "Scikit-learn",
    "TensorFlow", "Git", "Linux", "AWS", "Docker", "Power BI", "Figma",
    "Communication", "Problem Solving", "Teamwork",
    "Public Speaking", "Leadership", "Writing", "Photography", "Video Editing", "Event Management",
    "Time Management", "Creativity",
]

CAREER_INTERESTS = [
    "Software Developer", "Data Scientist", "ML Engineer", "Data Analyst", "Full Stack Developer",
    "Cloud Engineer", "DevOps Engineer", "Cyber Security Analyst", "Mobile App Developer",
    "UI/UX Designer", "Product Manager", "Entrepreneur", "Researcher", "Government / PSU Jobs",
]
