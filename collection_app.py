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

def extract_balances(pdf):
    balances = {}
    with pdfplumber.open(pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
            for line in text.split("\n"):
                match = re.match(r"([A-Z\-', ]+)\s+\$?(-?\d+\.\d+)", line)
                if match:
                    name = normalize(match.group(1))
                    bal = float(match.group(2))
                    if bal > 0:
                        balances[name] = bal
    return balances

def extract_schedule(pdf):
    names = []
    with pdfplumber.open(pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
            for line in text.split("\n"):
                parts = line.split()
                if len(parts) > 2:
                    name = " ".join(parts[-2:])
                    names.append(normalize(name))
    return names

if st.button("Generate Report"):
    if schedule_file and balance_file:
        balances = extract_balances(balance_file)
        schedule = extract_schedule(schedule_file)

        results = []
        for name in schedule:
            if name in balances:
                results.append((name.title(), balances[name]))

        results = sorted(results, key=lambda x: x[1], reverse=True)

        st.subheader("Patients to Collect From")
        for r in results:
            st.write(f"{r[0]} — ${r[1]:.2f}")
