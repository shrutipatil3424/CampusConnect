"""Offline evaluation of the recommender with ranking metrics (run: python tests/evaluate_recommender.py).

There is no 'accuracy' for a TF-IDF recommender because nothing is trained. Instead we measure how well the top
of the ranked list matches events a student would actually want. Ground truth here is a hand-labelled set of
10 student personas against the 20 sample events, so treat the numbers as a small synthetic benchmark, not as
results from real users.
"""
import math
import random
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from database.seed_data import non_technical_events, sample_events  # noqa: E402
from services.recommendation_service import recommend  # noqa: E402

EVENTS = pd.DataFrame([{**e, "id": i + 1} for i, e in enumerate(sample_events() + non_technical_events())])

# (name, profile, set of event ids a student like this would genuinely want)
PERSONAS = [
    ("ML student (MCA)", dict(course="MCA", technical_interests="Machine Learning, Data Science, Artificial Intelligence",
     skills="Python, Pandas", preferred_categories="Workshop, Hackathon", career_interests="Data Scientist, ML Engineer"),
     {1, 2, 9, 15, 19}),
    ("Web developer (BCA)", dict(course="BCA", technical_interests="Web Development, UI/UX Design",
     skills="JavaScript, HTML/CSS", preferred_categories="Workshop", career_interests="Full Stack Developer"),
     {3, 13, 17}),
    ("Cyber security (BE)", dict(course="BE/BTech", technical_interests="Cyber Security, Blockchain",
     skills="Linux, Python", preferred_categories="Seminar", career_interests="Cyber Security Analyst"),
     {4, 14}),
    ("Competitive programmer (BCA)", dict(course="BCA", technical_interests="Data Structures and Algorithms, Competitive Programming",
     skills="C/C++, Java, Problem Solving", preferred_categories="Coding Competition", career_interests="Software Developer"),
     {5, 20, 11}),
    ("Cloud / DevOps (MCA)", dict(course="MCA", technical_interests="Cloud Computing, DevOps",
     skills="AWS, Docker, Linux", preferred_categories="Workshop", career_interests="Cloud Engineer, DevOps Engineer"),
     {6, 17}),
    ("Placement focused (BCS)", dict(course="BCS", technical_interests="Data Structures and Algorithms",
     skills="Communication, Problem Solving", preferred_categories="Career Development", career_interests="Software Developer"),
     {7, 8, 20, 18}),
    ("Mobile developer (BCA)", dict(course="BCA", technical_interests="Mobile App Development, UI/UX Design",
     skills="Java, Figma", preferred_categories="Workshop", career_interests="Mobile App Developer"),
     {12, 13}),
    ("Data analyst (BCA)", dict(course="BCA", technical_interests="Data Science, Big Data, Database Management",
     skills="SQL, Power BI, Pandas", preferred_categories="Workshop", career_interests="Data Analyst"),
     {19, 11, 9}),
    ("IoT engineer (BE)", dict(course="BE/BTech", technical_interests="Internet of Things",
     skills="C/C++", preferred_categories="Technical Event", career_interests="Researcher"),
     {16, 10}),
    ("Entrepreneur (MCA)", dict(course="MCA", technical_interests="Open Source",
     skills="Communication, Teamwork", preferred_categories="Hackathon, Career Development", career_interests="Entrepreneur, Product Manager"),
     {18, 10, 2}),
    # ---- non-technical students (event ids 21-29 = non-technical sample events)
    ("Public speaker / debater (BCA)", dict(course="BCA", technical_interests="Public Speaking, Debate, Communication Skills",
     skills="Communication, Public Speaking", preferred_categories="Soft Skills", career_interests="Entrepreneur"),
     {21, 22, 25}),
    ("Creative writer / photographer (BCS)", dict(course="BCS", technical_interests="Creative Writing, Photography, Video Editing",
     skills="Writing, Photography", preferred_categories="Cultural & Creative", career_interests="Entrepreneur"),
     {23, 24, 28}),
    ("Performer & volunteer (BCA)", dict(course="BCA", technical_interests="Music, Dance, Volunteering, Event Management",
     skills="Teamwork, Event Management", preferred_categories="Cultural & Creative", career_interests="Entrepreneur"),
     {27, 29, 22}),
]


def metrics(ranked_ids, relevant, k_p=3, k_r=5):
    top_p, top_r = ranked_ids[:k_p], ranked_ids[:k_r]
    precision = sum(i in relevant for i in top_p) / k_p
    recall = sum(i in relevant for i in top_r) / len(relevant)
    hit = float(any(i in relevant for i in top_p))
    mrr = next((1 / (r + 1) for r, i in enumerate(ranked_ids) if i in relevant), 0.0)
    dcg = sum(1 / math.log2(r + 2) for r, i in enumerate(top_r) if i in relevant)
    idcg = sum(1 / math.log2(r + 2) for r in range(min(len(relevant), k_r)))
    return precision, recall, hit, mrr, dcg / idcg


def rank_model(profile):
    return [int(i) for i in recommend(profile, EVENTS, top_n=len(EVENTS))["id"]]


def rank_category_only(profile):
    prefs = {c.strip() for c in profile["preferred_categories"].split(",")}
    return list(EVENTS.assign(m=EVENTS["category"].isin(prefs))
                .sort_values(["m", "id"], ascending=[False, True])["id"])


def rank_random(_profile, rng=random.Random(42)):
    ids = list(EVENTS["id"])
    rng.shuffle(ids)
    return ids


def evaluate(name, ranker, repeats=1):
    rows = []
    for _ in range(repeats):
        for _, profile, relevant in PERSONAS:
            rows.append(metrics(ranker(profile), relevant))
    return [name] + [round(sum(col) / len(col), 3) for col in zip(*rows)]


if __name__ == "__main__":
    table = pd.DataFrame(
        [evaluate("TF-IDF + cosine (this project)", rank_model),
         evaluate("Category match only", rank_category_only),
         evaluate("Random order (avg of 500 runs)", rank_random, repeats=500)],
        columns=["Method", "Precision@3", "Recall@5", "HitRate@3", "MRR", "NDCG@5"])
    print(table.to_string(index=False))
    print("\nPer persona (this project): top-3 recommended titles")
    for name, profile, relevant in PERSONAS:
        top = recommend(profile, EVENTS, top_n=3)
        marks = ["✔" if int(i) in relevant else "✘" for i in top["id"]]
        print(f"- {name}: " + "; ".join(f"{m} {t[:34]}" for m, t in zip(marks, top["title"])))
