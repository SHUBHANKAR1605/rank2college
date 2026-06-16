#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║        RANK2COLLEGE — JOSAA College Predictor        ║
║  JEE Mains → NIT / IIIT / GFTI  |  Advanced → IIT    ║
╚══════════════════════════════════════════════════════╝
"""

import mysql.connector
from mysql.connector import Error
import pandas as pd

# ─── DB CONFIG ───────────────────────────────────────────────────────────────
DB_CONFIG = dict(host="localhost", user="root", password="Root1234", database="rank2college")

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
MARGIN = 0.10   # 10% stretch margin (+/-)

CATEGORIES = {"1": "OPEN", "2": "EWS", "3": "OBC-NCL", "4": "SC", "5": "ST"}

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def ask(prompt, valid=None, default=None):
    """Simple input with optional validation."""
    while True:
        val = input(f"  {prompt}: ").strip()
        if not val and default is not None:
            return default
        if valid is None or val in valid:
            return val
        print(f"    ⚠  Invalid. Options: {', '.join(valid)}")


def connect_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"\n❌  Cannot connect to MySQL: {e}")
        print("    Make sure MySQL is running and data_loader.py has been run first.\n")
        raise SystemExit(1)


# ─── CORE PREDICTION QUERY ───────────────────────────────────────────────────
def build_query(exam_type, quota, user_category, crl_rank, cat_rank, gender, branch_keyword):
    """
    Build the SQL query using a strict +/- 10% targeted window.
    Filters exclusively for category seats if a reservation category is selected.
    """

    chance_sql = """
        CASE
            WHEN c.seat_type = 'OPEN' AND c.closing_rank >= %s * 1.00 THEN 'SAFE'
            WHEN c.seat_type = 'OPEN' AND c.closing_rank >= %s * 0.97 THEN 'LIKELY'
            WHEN c.seat_type = 'OPEN' AND c.closing_rank >= %s * 0.93 THEN 'MODERATE'
            WHEN c.seat_type = 'OPEN'                                 THEN 'STRETCH'
            WHEN c.seat_type != 'OPEN' AND c.closing_rank >= %s * 1.00 THEN 'SAFE'
            WHEN c.seat_type != 'OPEN' AND c.closing_rank >= %s * 0.97 THEN 'LIKELY'
            WHEN c.seat_type != 'OPEN' AND c.closing_rank >= %s * 0.93 THEN 'MODERATE'
            ELSE 'STRETCH'
        END
    """
    chance_params = (crl_rank, crl_rank, crl_rank, cat_rank, cat_rank, cat_rank)

    if exam_type == "ADVANCED":
        exam_filter = "c.institute_type = 'IIT' AND c.quota = 'AI'"
        exam_params = ()
    else:
        if quota == "HS":
            exam_filter = """(
                (c.institute_type = 'NIT'  AND c.quota = 'HS')
             OR (c.institute_type = 'IIIT' AND c.quota = 'AI')
             OR (c.institute_type = 'GFTI' AND c.quota IN ('AI','HS'))
            )"""
        else:
            exam_filter = """(
                (c.institute_type = 'NIT'  AND c.quota = 'OS')
             OR (c.institute_type = 'IIIT' AND c.quota = 'AI')
             OR (c.institute_type = 'GFTI' AND c.quota IN ('AI','OS'))
            )"""
        exam_params = ()

    if gender == "female":
        gender_filter = "AND c.gender LIKE 'Female%'"
    elif gender == "any":
        gender_filter = ""
    else:
        gender_filter = "AND c.gender = 'Gender-Neutral'"

    # ── FIXED LOGIC: Strict separation between OPEN and Reservation Categories ──
    if user_category == "OPEN":
        cat_filter = "AND c.seat_type = 'OPEN' AND c.closing_rank BETWEEN %s AND %s"
        cat_params = (int(crl_rank * (1 - MARGIN)), int(crl_rank * (1 + MARGIN)))
    else:
        cat_filter = "AND c.seat_type = %s AND c.closing_rank BETWEEN %s AND %s"
        cat_params = (
            user_category,
            int(cat_rank * (1 - MARGIN)), int(cat_rank * (1 + MARGIN)),
        )

    if branch_keyword:
        branch_filter = "AND c.branch_name LIKE %s"
        branch_params = (f"%{branch_keyword}%",)
    else:
        branch_filter = ""
        branch_params = ()

    sql = f"""
        SELECT
            c.institute_name,
            c.branch_name,
            c.institute_type,
            c.quota,
            c.seat_type,
            c.opening_rank,
            c.closing_rank,
            {chance_sql}      AS chance_level

        FROM college_cutoffs c

        WHERE {exam_filter}
          {gender_filter}
          {cat_filter}
          {branch_filter}

        ORDER BY
            FIELD(chance_level, 'SAFE','LIKELY','MODERATE','STRETCH'),
            c.closing_rank ASC
    """

    params = chance_params + exam_params + cat_params + branch_params
    return sql, params


# ─── RUN QUERY ───────────────────────────────────────────────────────────────
def run_query(conn, sql, params):
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    
    if cursor.description:
        cols = [d[0] for d in cursor.description]
    else:
        cols = []
        
    cursor.close()
    return pd.DataFrame(rows, columns=cols)


# ─── DISPLAY ─────────────────────────────────────────────────────────────────
def display(df, crl_rank, user_category, cat_rank):
    W = 145
    if df.empty:
        print("\n❌  No colleges found. Try: different quota, remove branch filter, or check category rank.\n")
        return

    print("\n" + "═" * W)
    print(f"{'🎓  RANK2COLLEGE — JOSAA PREDICTIONS':^{W}}")
    rank_line = f"CRL Rank: {crl_rank:,}"
    if cat_rank != crl_rank:
        rank_line += f"  |  {user_category} Rank: {cat_rank:,}"
    print(f"{rank_line:^{W}}")
    print("═" * W)

    labels = {
        "SAFE":     "🟢 SAFE     — Closing rank is above yours. You will definitely qualify.",
        "LIKELY":   "🟡 LIKELY   — Closing rank is within 3% of yours. Very probable.",
        "MODERATE": "🟠 MODERATE — Closing rank is within 7% of yours. Depends on the round.",
        "STRETCH":  "🔴 STRETCH  — Up to 10% harder. Possible in later rounds.",
    }

    rename = {
        "institute_name": "Institute",
        "branch_name":    "Branch",
        "institute_type": "Type",
        "quota":          "Quota",
        "seat_type":      "Seat",
        "opening_rank":   "Open Rank",
        "closing_rank":   "Close Rank",
    }

    for key, label in labels.items():
        subset = df[df["chance_level"] == key].copy()
        if subset.empty:
            continue
        display_df = subset.drop(columns=["chance_level"]).rename(columns=rename).reset_index(drop=True)
        print(f"\n{label}")
        print("─" * W)
        print(display_df.to_string(index=False, max_colwidth=60))

    print("\n" + "═" * W)
    counts = df["chance_level"].value_counts()
    print(
        f"  📊  Total Options Found: {len(df)}  |  "
        f"🟢 Safe: {counts.get('SAFE',0)}  "
        f"🟡 Likely: {counts.get('LIKELY',0)}  "
        f"🟠 Moderate: {counts.get('MODERATE',0)}  "
        f"🔴 Stretch: {counts.get('STRETCH',0)}"
    )
    print("  📌  Always cross-check at: https://josaa.admissions.nic.in\n")


# ─── MAIN INTERACTIVE LOOP ────────────────────────────────────────────────────
def main():
    print("\n╔══════════════════════════════════════════════════════╗")
    print("║        RANK2COLLEGE — JOSAA College Predictor        ║")
    print("║  JEE Mains → NIT/IIIT/GFTI  |  Advanced → IIT       ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    conn = connect_db()
    print("  ✅  Connected to MySQL database.\n")

    while True:
        print("─" * 50)
        print("  Step 1 — Exam Type")
        print("  1 → JEE Mains   (NITs / IIITs / GFTIs)")
        print("  2 → JEE Advanced (IITs only)")
        exam_inp  = ask("Choice", valid=["1", "2"])
        exam_type = "ADVANCED" if exam_inp == "2" else "MAINS"

        print("\n─" * 25)
        print(f"  Step 2 — Your {'JEE Advanced' if exam_type=='ADVANCED' else 'JEE Mains'} CRL Rank")
        while True:
            try:
                crl_rank = int(ask("CRL Rank"))
                if crl_rank > 0: break
            except ValueError:
                pass
            print("    ⚠  Enter a positive integer.")

        print("\n─" * 25)
        print("  Step 3 — Reservation Category")
        for k, v in CATEGORIES.items():
            print(f"  {k} → {v}")
        cat_inp       = ask("Choice", valid=list(CATEGORIES.keys()))
        user_category = CATEGORIES[cat_inp]

        cat_rank = crl_rank
        if user_category != "OPEN":
            print(f"\n─" * 25)
            print(f"  Step 4 — Your {user_category} Category Rank")
            print("  (Press Enter to use CRL Rank instead)")
            cr_inp = ask(f"{user_category} Rank", default="")
            if cr_inp:
                try:
                    cat_rank = int(cr_inp)
                except ValueError:
                    print("    ⚠  Invalid, using CRL Rank.")

        print("\n─" * 25)
        print("  Step 5 — Seat Gender")
        print("  1 → Gender-Neutral (default)")
        print("  2 → Female-only seats")
        print("  3 → Show both")
        g_inp  = ask("Choice", valid=["1","2","3"], default="1")
        gender = {"1": "neutral", "2": "female", "3": "any"}[g_inp]

        quota = "AI"
        if exam_type == "MAINS":
            print("\n─" * 25)
            print("  Step 6 — Quota")
            print("  1 → Home State (HS)  — your state's NIT + all IIITs/GFTIs")
            print("  2 → Other State (OS) — other NITs + all IIITs/GFTIs")
            q_inp = ask("Choice", valid=["1","2"])
            quota = "HS" if q_inp == "1" else "OS"

        print("\n─" * 25)
        print("  Step 7 — Branch Filter  (optional)")
        print("  e.g. Computer, Electronics, Mechanical, Civil")
        branch_kw = ask("Keyword (Enter to skip)", default="")

        print(f"\n  🔍  Querying database for a +/- {int(MARGIN*100)}% rank window ...")
        try:
            sql, params = build_query(
                exam_type      = exam_type,
                quota          = quota,
                user_category  = user_category,
                crl_rank       = crl_rank,
                cat_rank       = cat_rank,
                gender         = gender,
                branch_keyword = branch_kw
            )
            result_df = run_query(conn, sql, params)
        except Error as e:
            print(f"\n❌  Query failed: {e}\n")
            continue

        display(result_df, crl_rank, user_category, cat_rank)

        if not result_df.empty:
            save = ask("💾  Save to CSV? (y/n)", valid=["y","n","Y","N"], default="n")
            if save.lower() == "y":
                fname = f"results_{crl_rank}_{user_category}_{exam_type}.csv"
                result_df.to_csv(fname, index=False)
                print(f"  ✅  Saved → {fname}\n")

        again = ask("🔁  Search again? (y/n)", valid=["y","n","Y","N"], default="n")
        if again.lower() != "y":
            break

    conn.close()
    print("\n  ✅  Good luck with JOSAA counseling! 🎓\n")


if __name__ == "__main__":
    main()