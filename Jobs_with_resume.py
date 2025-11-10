import customtkinter as ctk
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import webbrowser
from tkinter import filedialog, messagebox

# === INTERFACE CONFIGURATION ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("💼 Job Finder & CV Optimizer")
root.geometry("1000x700")

# === FUNCTIONS ===

def search_jobs():
    role = entry_role.get()
    country = dropdown_country.get()
    easy_apply = var_easy_apply.get()
    work_type = dropdown_type.get()

    if not role:
        messagebox.showwarning("Error", "Please enter a role to search!")
        return

    label_status.configure(text="🔍 Searching for jobs...")

    url = f"https://www.linkedin.com/jobs/search?keywords={role}&location={country.replace(' ', '%20')}"
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text
    soup = BeautifulSoup(html, "html.parser")

    results = []
    for job_card in soup.find_all("div", class_="base-card"):
        title_elem = job_card.find("h3", class_="base-search-card__title")
        company_elem = job_card.find("h4", class_="base-search-card__subtitle")
        link_elem = job_card.find("a", class_="base-card__full-link")

        if not (title_elem and company_elem and link_elem):
            continue

        title = title_elem.text.strip()
        company = company_elem.text.strip()
        link = link_elem["href"].split("?")[0]

        results.append({"Title": title, "Company": company, "Link": link})

    if easy_apply:
        results = [r for r in results if "easyapply" in r["Link"].lower()]

    excel_path = "job_results.xlsx"
    if os.path.exists(excel_path):
        df_existing = pd.read_excel(excel_path)
        df_existing = df_existing.rename(columns={"Titlu": "Title", "Companie": "Company"})
        existing_links = df_existing["Link"].tolist()
    else:
        df_existing = pd.DataFrame(columns=["Title", "Company", "Link"])
        existing_links = []

    new_jobs = [r for r in results if r["Link"] not in existing_links]

    if new_jobs:
        df_new = pd.DataFrame(new_jobs)
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
        df_final.to_excel(excel_path, index=False)
        display_jobs(new_jobs)
        label_status.configure(text=f"✅ {len(new_jobs)} new jobs found and saved.")
    else:
        if not df_existing.empty:
            display_jobs(df_existing.to_dict(orient="records"))
            warning_label = ctk.CTkLabel(frame_results, text="⚠️ No new jobs found. Showing previously saved jobs.", text_color="yellow")
            warning_label.pack(pady=10)
        else:
            display_jobs([])
            label_status.configure(text="✅ No jobs match the filters.")

def display_jobs(jobs):
    for widget in frame_results.winfo_children():
        widget.destroy()

    if not jobs:
        ctk.CTkLabel(frame_results, text="✅ No jobs match the filters.").pack(pady=10)
        return

    for job in jobs:
        frame_job = ctk.CTkFrame(frame_results)
        frame_job.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_job, text=job["Title"], font=("Arial", 14, "bold")).pack(anchor="w", padx=10)
        ctk.CTkLabel(frame_job, text=job["Company"], font=("Arial", 12)).pack(anchor="w", padx=10)

        def open_link(url=job["Link"]):
            webbrowser.open_new_tab(url)

        ctk.CTkButton(frame_job, text="🔗 Open link", fg_color="#0A66C2", hover_color="#004182",
                      text_color="white", command=open_link).pack(anchor="e", padx=10, pady=5)

def choose_cv():
    global cv_path
    cv_path = filedialog.askopenfilename(filetypes=[("Documents", "*.pdf *.docx")])
    if cv_path:
        label_cv.configure(text=f"📄 Selected file: {os.path.basename(cv_path)}")

def optimize_cv():
    from openai import OpenAI
    name = entry_name.get()
    position = entry_position.get()

    if not os.getenv("OPENROUTER_API_KEY"):
        messagebox.showerror("Error", "OPENROUTER_API_KEY is not set in environment variables.")
        return

    if not cv_path:
        messagebox.showerror("Error", "Please select a CV to optimize.")
        return

    label_status.configure(text="🤖 Optimizing CV...")

    client = OpenAI(base_url="https://openrouter.ai/api/v1")
    client.api_key = os.getenv("OPENROUTER_API_KEY")

    with open(cv_path, "rb") as f:
        content = f.read()

    prompt = f"""
    Improve this CV to be ATS (Applicant Tracking System) compatible
    and tailor it for the position "{position}".
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an HR expert optimizing CVs for ATS."},
                {"role": "user", "content": prompt},
            ],
        )
        result = completion.choices[0].message.content

        out_path = f"{name} - {position}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result)

        label_status.configure(text=f"✅ Optimized CV saved as: {out_path}")
        messagebox.showinfo("Success", f"The CV has been optimized and saved as:\n{out_path}")

    except Exception as e:
        label_status.configure(text="❌ Error processing CV.")
        messagebox.showerror("Error", str(e))


# === GUI ELEMENTS ===

frame_input = ctk.CTkFrame(root)
frame_input.pack(pady=20)

ctk.CTkLabel(frame_input, text="Role / Position:").grid(row=0, column=0, padx=5, pady=5)
entry_role = ctk.CTkEntry(frame_input, width=200)
entry_role.grid(row=0, column=1, padx=5, pady=5)

ctk.CTkLabel(frame_input, text="Country:").grid(row=0, column=2, padx=5, pady=5)
dropdown_country = ctk.CTkOptionMenu(frame_input, values=["Romania", "Germany", "France", "United Kingdom", "Spain", "Italy", "Poland", "Netherlands"])
dropdown_country.grid(row=0, column=3, padx=5, pady=5)

var_easy_apply = ctk.BooleanVar()
ctk.CTkCheckBox(frame_input, text="Easy Apply only", variable=var_easy_apply).grid(row=1, column=0, padx=5, pady=5)

ctk.CTkLabel(frame_input, text="Work type:").grid(row=1, column=2, padx=5, pady=5)
dropdown_type = ctk.CTkOptionMenu(frame_input, values=["Any", "Remote", "Hybrid", "On-site"])
dropdown_type.grid(row=1, column=3, padx=5, pady=5)

ctk.CTkButton(frame_input, text="🔍 Search jobs", command=search_jobs).grid(row=2, column=0, columnspan=4, pady=10)

frame_results = ctk.CTkScrollableFrame(root, width=900, height=400)
frame_results.pack(pady=10)

# === CV AI Section ===
frame_cv = ctk.CTkFrame(root)
frame_cv.pack(pady=20)

entry_name = ctk.CTkEntry(frame_cv, placeholder_text="Full name", width=200)
entry_name.grid(row=0, column=0, padx=5, pady=5)
entry_position = ctk.CTkEntry(frame_cv, placeholder_text="Desired position", width=200)
entry_position.grid(row=0, column=1, padx=5, pady=5)

ctk.CTkButton(frame_cv, text="📂 Choose CV", command=choose_cv).grid(row=0, column=2, padx=5, pady=5)
label_cv = ctk.CTkLabel(frame_cv, text="No file selected.")
label_cv.grid(row=1, column=0, columnspan=3, pady=5)

ctk.CTkButton(frame_cv, text="🤖 Generate ATS CV (OpenRouter)", command=optimize_cv, fg_color="#00A67E").grid(row=2, column=0, columnspan=3, pady=10)

label_status = ctk.CTkLabel(root, text="")
label_status.pack(pady=10)

root.mainloop()