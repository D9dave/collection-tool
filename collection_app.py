import streamlit as st
import pdfplumber
import re
import streamlit.components.v1 as components

st.title("Daily Collection Tool")

schedule_file = st.file_uploader("Upload Schedule PDF")
balance_file = st.file_uploader("Upload Balance PDF")


# -----------------------------
# Normalize names
# -----------------------------
def normalize(name):
    name = name.lower().strip()

    # convert LAST, FIRST → FIRST LAST
    if "," in name:
        last, first = name.split(",", 1)
        name = first.strip() + " " + last.strip()

    parts = name.split()

    # keep only first + last
    if len(parts) >= 2:
        name = parts[0] + " " + parts[-1]

    return name


# -----------------------------
# Extract BALANCES
# -----------------------------
def extract_balances(file):
    balances = {}

    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                for line in text.split("\n"):
                    match = re.match(r"([A-Z\-', ]+)\s+\$?(-?\d+\.\d+)", line)
                    if match:
                        name = normalize(match.group(1))
                        bal = float(match.group(2))

                        if bal > 0:
                            balances[name] = bal

    except:
        st.error("Error reading balance PDF.")
        return {}

    return balances


# -----------------------------
# Extract SCHEDULE
# -----------------------------
def extract_schedule(file):
    names = []

    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split("\n")

                for line in lines:
                    parts = line.split()

                    for i, word in enumerate(parts):
                        if word.lower() in ["confirmed", "scheduled", "cancelled", "rescheduled", "roomed"]:
                            try:
                                name_parts = parts[i+1:i+4]

                                # remove phone numbers / parentheses
                                clean_parts = [
                                    p for p in name_parts
                                    if "(" not in p and ")" not in p
                                ]

                                if len(clean_parts) >= 2:
                                    name = clean_parts[0] + " " + clean_parts[-1]
                                    names.append(normalize(name))

                            except:
                                continue

    except:
        st.error("Error reading schedule PDF.")
        return []

    return names


# -----------------------------
# MAIN BUTTON
# -----------------------------
if st.button("Generate Report"):
    if schedule_file and balance_file:

        balances = extract_balances(balance_file)
        schedule = extract_schedule(schedule_file)

        results = []

        for name in schedule:
            if name in balances:
                results.append((name.title(), balances[name]))

        # sort highest balance first
        results = sorted(results, key=lambda x: x[1], reverse=True)

        st.subheader("Patients to Collect From")

        if results:
            for r in results:
                st.write(f"{r[0]} — ${r[1]:.2f}")

            # -----------------------------
            # PRINT BUTTON (FIXED VERSION)
            # -----------------------------
            if st.button("🖨️ Print Report"):
                html = "<h2>Daily Collection List</h2><hr>"

                for r in results:
                    html += f"<p>{r[0]} — ${r[1]:.2f}</p>"

                components.html(f"""
                <script>
                var w = window.open('', '', 'height=600,width=800');
                w.document.write('<html><head><title>Print</title></head><body>');
                w.document.write(`{html}`);
                w.document.write('</body></html>');
                w.document.close();
                w.print();
                </script>
                """, height=0)

        else:
            st.write("No matches found")
