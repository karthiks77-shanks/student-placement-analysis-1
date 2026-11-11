import random
from database import init_db, get_db

DEPARTMENTS = ['Computer Science', 'Information Technology', 'Electronics & Comm', 'Mechanical', 'Civil', 'Electrical']
SKILLS = ['Python', 'SQL', 'Java', 'React', 'Machine Learning', 'AWS', 'Docker', 'Embedded Systems', 'Data Structures', 'Git']
COMPANIES = [
    ('Google', 24.5, 'Software Engineer'),
    ('Microsoft', 22.0, 'Cloud Engineer'),
    ('Amazon', 19.5, 'SDE-1'),
    ('TCS Digital', 7.5, 'Systems Engineer'),
    ('Infosys SP', 9.0, 'Specialist Programmer'),
    ('Deloitte', 8.5, 'Analyst'),
    ('Texas Instruments', 16.0, 'Hardware Engineer'),
    ('L&T', 6.5, 'Graduate Trainee')
]

def seed():
    init_db()
    with get_db() as (conn, engine):
        cursor = conn.cursor()
        
        # 1. Insert Skills
        for sk in SKILLS:
            try:
                if engine == "mysql":
                    cursor.execute("INSERT IGNORE INTO skills (skill_name) VALUES (%s)", (sk,))
                else:
                    cursor.execute("INSERT OR IGNORE INTO skills (skill_name) VALUES (?)", (sk,))
            except Exception:
                pass
        conn.commit()

        # Retrieve skill IDs
        cursor.execute("SELECT skill_id, skill_name FROM skills")
        rows = cursor.fetchall()
        skill_ids = [r['skill_id'] if isinstance(r, dict) else (r[0] if isinstance(r, tuple) else r['skill_id']) for r in rows]

        # 2. Insert 60 Students
        for i in range(1, 61):
            roll = f"2024CS{i:03d}"
            name = f"Candidate {i}"
            dept = random.choice(DEPARTMENTS)
            year = random.choice([2024, 2025])
            cgpa = round(random.uniform(5.5, 9.8), 2)
            backlogs = random.choices([0, 1, 2], weights=[0.85, 0.1, 0.05])[0]
            is_eligible = 1 if (cgpa >= 6.0 and backlogs == 0) else 0

            try:
                if engine == "mysql":
                    cursor.execute("""
                        INSERT IGNORE INTO students (roll_number, full_name, department, graduation_year, cgpa, active_backlogs, is_eligible)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (roll, name, dept, year, cgpa, backlogs, is_eligible))
                else:
                    cursor.execute("""
                        INSERT OR IGNORE INTO students (roll_number, full_name, department, graduation_year, cgpa, active_backlogs, is_eligible)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (roll, name, dept, year, cgpa, backlogs, is_eligible))
                
                sid = cursor.lastrowid or i

                # Tag 2-4 skills
                assigned = random.sample(skill_ids, random.randint(2, min(4, len(skill_ids))))
                for sk_id in assigned:
                    try:
                        if engine == "mysql":
                            cursor.execute("INSERT IGNORE INTO student_skills (student_id, skill_id) VALUES (%s, %s)", (sid, sk_id))
                        else:
                            cursor.execute("INSERT OR IGNORE INTO student_skills (student_id, skill_id) VALUES (?, ?)", (sid, sk_id))
                    except Exception:
                        pass

                # Placements for eligible students (approx 78% placement rate)
                if is_eligible and random.random() < 0.78:
                    comp, base_pkg, role = random.choice(COMPANIES)
                    pkg = round(base_pkg + random.uniform(-1.5, 2.5), 2)
                    st = random.choice(['Offer Accepted', 'Offer Accepted', 'Placed'])
                    if engine == "mysql":
                        cursor.execute("""
                            INSERT INTO placements (student_id, company_name, role, package_lpa, placement_date, status)
                            VALUES (%s, %s, %s, %s, '2024-03-20', %s)
                        """, (sid, comp, role, pkg, st))
                    else:
                        cursor.execute("""
                            INSERT INTO placements (student_id, company_name, role, package_lpa, placement_date, status)
                            VALUES (?, ?, ?, ?, '2024-03-20', ?)
                        """, (sid, comp, role, pkg, st))
            except Exception as e:
                print(f"Skipping student {i}: {e}")

        conn.commit()
    print("Database successfully seeded with realistic students, skills, and placement records!")

if __name__ == "__main__":
    seed()
