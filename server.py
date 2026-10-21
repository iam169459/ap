import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

UPLOAD_DIR = "uploads"

def main():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    app = tk.Tk()
    app.title("Simple GUI Server")
    app.geometry("420x320")

    label = tk.Label(app, text="Simple GUI", font=("Arial", 12, "bold"))
    label.pack(pady=10)

    text_area = scrolledtext.ScrolledText(app, wrap=tk.WORD, width=48, height=12)
    text_area.pack(padx=10, pady=5)

    def pick_file():
        path = filedialog.askopenfilename()
        if path:
            text_area.insert(tk.END, f"Selected: {path}\n")

    def save_note():
        note = text_area.get("1.0", tk.END).strip()
        with open(os.path.join(UPLOAD_DIR, "note.txt"), "w") as f:
            f.write(note)
        messagebox.showinfo("Saved", "Note saved to uploads/note.txt")

    btn_frame = tk.Frame(app)
    btn_frame.pack(pady=5)
    tk.Button(btn_frame, text="Pick File", command=pick_file, width=12).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Save Note", command=save_note, width=12).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Close", command=app.quit, width=12).pack(side=tk.LEFT, padx=5)

    app.mainloop()

if __name__ == "__main__":
    main()
