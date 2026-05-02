import streamlit as st
import pdfplumber
import re

st.title("Daily Collection Tool")

schedule_file = st.file_uploader("Upload Schedule PDF")
balance_file = st.file_uploader("Upload Balance PDF")

def normalize(name):
    name = name.lower().strip()
    if "," in name:
        last, first = name.split(",",1)
        name = first.strip() + " " + last.strip()
    name = re.sub(r"\b[a-z]\b","",name)
    return " ".join(name.split())

def extract_balances(file):
    balances = {}

    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                try:
                    text = page.extract_text()
                except:
                    continue

                if not text:
                    continue

                lines = text.split("\n")

                for line in lines:
                    match = re.match(r"([A-Z\-', ]+)\s+\$?(-?\d+\.\d+)", line)
                    if match:
                        name = normalize(match.group(1))
                        bal = float(match.group(2))

                        if bal > 0:
                            balances[name] = bal

    except Exception as e:
        st.error("Error reading balance PDF. Try re-uploading.")
        return {}

    return balances

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

                    # We need at least 6+ parts to safely grab patient name
                    if len(parts) > 5:
                        try:
                            # Skip lines that aren't appointment rows
                            if parts[0] == "JENNIFER" and parts[1] == "JONES":
                                # Patient name starts after Status column
                                # Format: Provider Time Status NAME NAME
                                name_parts = parts[4:6]  # grab first + last name

                                name = " ".join(name_parts)
                                names.append(normalize(name))

                        except:
                            continue

    except:
        st.error("Error reading schedule PDF.")
        return []

    return names
if st.button("Generate Report"):
    if schedule_file and balance_file:
        balances = extract_balances(balance_file)
        schedule = extract_schedule(schedule_file)

        st.write("Sample Schedule Names:", schedule[:10])
        st.write("Sample Balance Names:", list(balances.keys())[:10])

        results = []
        for name in schedule:
            if name in balances:
                results.append((name.title(), balances[name]))

        results = sorted(results, key=lambda x: x[1], reverse=True)

        st.subheader("Patients to Collect From")
        for r in results:
            st.write(f"{r[0]} — ${r[1]:.2f}")
