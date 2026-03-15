#!/usr/bin/env python3
"""
M4B GUI - Graphical interface for creating M4B audiobook files from audio chapters.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
from typing import List, Optional

from m4b_creator import M4BCreator


class M4BCreatorApp(tk.Tk):
    """Main application window for M4B creation."""

    def __init__(self):
        super().__init__()
        self.title("M4B Audiobook Creator")
        self.minsize(900, 600)

        self.audio_files: List[str] = []
        self.cover_file: Optional[str] = None

        try:
            self.creator = M4BCreator()
        except RuntimeError as e:
            messagebox.showerror("ffmpeg Required", str(e))
            self.destroy()
            return

        self._build_ui()
        self._center_window(1000, 650)

    # ── UI construction ─────────────────────────────────────────────

    def _build_ui(self):
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        left = ttk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        right = ttk.Frame(main)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # ── Left: Audio chapter list ─────────────────────────────────
        ch_frame = ttk.LabelFrame(left, text="Audio Chapters (one per chapter)", padding=10)
        ch_frame.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.Frame(ch_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=18, selectmode=tk.EXTENDED)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        btn_frame = ttk.Frame(ch_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Add Audio Files", command=self._add_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove", command=self._remove_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Move Up", command=self._move_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Move Down", command=self._move_down).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear All", command=self._clear_all).pack(side=tk.LEFT, padx=2)

        self.use_tags_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(ch_frame, text="Use audio title tags as chapter names",
                         variable=self.use_tags_var).pack(anchor=tk.W, pady=(5, 0))

        # ── Right: metadata + cover + actions ───────────────────────
        info_frame = ttk.LabelFrame(right, text="Book Metadata", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 5))
        info_frame.columnconfigure(1, weight=1)

        labels = ["Title:", "Author:", "Narrator:", "Year:", "Comment:"]
        self.title_entry = self._add_field(info_frame, "Title:", 0)
        self.author_entry = self._add_field(info_frame, "Author:", 1)
        self.narrator_entry = self._add_field(info_frame, "Narrator:", 2)
        self.year_entry = self._add_field(info_frame, "Year:", 3)

        ttk.Label(info_frame, text="Comment:").grid(row=4, column=0, sticky=tk.NW, pady=2)
        self.comment_text = tk.Text(info_frame, width=40, height=3)
        self.comment_text.grid(row=4, column=1, pady=2, padx=5, sticky=tk.EW)

        # Cover art
        cover_frame = ttk.LabelFrame(right, text="Cover Art (optional)", padding=10)
        cover_frame.pack(fill=tk.X, pady=(0, 5))

        self.cover_preview_label = tk.Label(cover_frame, text="No cover")
        self.cover_preview_label.pack(side=tk.LEFT, padx=5)

        cover_right = ttk.Frame(cover_frame)
        cover_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.cover_label = ttk.Label(cover_right, text="No cover selected")
        self.cover_label.pack(anchor=tk.W, pady=2)

        cover_btn_frame = ttk.Frame(cover_right)
        cover_btn_frame.pack(anchor=tk.W, pady=2)
        ttk.Button(cover_btn_frame, text="Select Image", command=self._select_cover).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(cover_btn_frame, text="Extract from Audio", command=self._extract_cover).pack(side=tk.LEFT)

        # Encoding options
        enc_frame = ttk.LabelFrame(right, text="Encoding", padding=10)
        enc_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(enc_frame, text="AAC Bitrate:").pack(side=tk.LEFT)
        self.bitrate_var = tk.StringVar(value="128k")
        bitrate_combo = ttk.Combobox(enc_frame, textvariable=self.bitrate_var, width=8,
                                      values=["64k", "96k", "128k", "192k", "256k"], state="readonly")
        bitrate_combo.pack(side=tk.LEFT, padx=5)

        # Create button
        ttk.Button(right, text="Create M4B", command=self._create_m4b).pack(anchor=tk.E, pady=(5, 0))

    def _add_field(self, parent, label: str, row: int) -> ttk.Entry:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
        entry = ttk.Entry(parent, width=40)
        entry.grid(row=row, column=1, pady=2, padx=5, sticky=tk.EW)
        return entry

    def _center_window(self, w: int, h: int):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── File list actions ───────────────────────────────────────────

    def _add_files(self):
        files = filedialog.askopenfilenames(
            title="Select Audio Files",
            filetypes=[
                ("Audio files", "*.mp3 *.flac *.m4a *.m4b *.aac *.ogg *.opus *.wav"),
                ("All files", "*.*"),
            ]
        )
        first_add = len(self.audio_files) == 0
        for f in files:
            self.audio_files.append(f)
            self.listbox.insert(tk.END, Path(f).name)

        if first_add and self.audio_files:
            self._auto_populate_metadata()

    def _remove_selected(self):
        sel = list(self.listbox.curselection())
        for idx in reversed(sel):
            self.listbox.delete(idx)
            del self.audio_files[idx]

    def _move_up(self):
        sel = self.listbox.curselection()
        if sel and sel[0] > 0:
            idx = sel[0]
            self.audio_files[idx], self.audio_files[idx - 1] = self.audio_files[idx - 1], self.audio_files[idx]
            item = self.listbox.get(idx)
            self.listbox.delete(idx)
            self.listbox.insert(idx - 1, item)
            self.listbox.selection_set(idx - 1)

    def _move_down(self):
        sel = self.listbox.curselection()
        if sel and sel[0] < len(self.audio_files) - 1:
            idx = sel[0]
            self.audio_files[idx], self.audio_files[idx + 1] = self.audio_files[idx + 1], self.audio_files[idx]
            item = self.listbox.get(idx)
            self.listbox.delete(idx)
            self.listbox.insert(idx + 1, item)
            self.listbox.selection_set(idx + 1)

    def _clear_all(self):
        self.listbox.delete(0, tk.END)
        self.audio_files.clear()

    # ── Metadata helpers ────────────────────────────────────────────

    def _auto_populate_metadata(self):
        """Silently populate metadata from the first audio file's tags."""
        try:
            tags = self.creator.extract_metadata(self.audio_files[0])
            if not tags:
                return

            if 'album' in tags:
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, tags['album'])
            elif 'title' in tags:
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, tags['title'])

            if 'artist' in tags:
                self.author_entry.delete(0, tk.END)
                self.author_entry.insert(0, tags['artist'])
            elif 'albumartist' in tags:
                self.author_entry.delete(0, tk.END)
                self.author_entry.insert(0, tags['albumartist'])

            if 'date' in tags:
                self.year_entry.delete(0, tk.END)
                self.year_entry.insert(0, tags['date'])

            if 'comment' in tags:
                self.comment_text.delete("1.0", tk.END)
                self.comment_text.insert("1.0", tags['comment'])

            # Try to auto-extract cover
            self._extract_cover(silent=True)

        except Exception:
            pass

    def _extract_cover(self, silent: bool = False):
        """Extract cover art from the first audio file."""
        if not self.audio_files:
            if not silent:
                messagebox.showwarning("Warning", "Add audio files first")
            return

        try:
            data = self.creator.extract_cover(self.audio_files[0])
            if data is None:
                if not silent:
                    messagebox.showinfo("Info", "No embedded cover art found in the first audio file")
                return

            import tempfile
            # Detect format from header bytes
            ext = ".jpg"
            if data[:8] == b'\x89PNG\r\n\x1a\n':
                ext = ".png"

            tmp = os.path.join(tempfile.gettempdir(), f"m4b_cover{ext}")
            with open(tmp, "wb") as f:
                f.write(data)

            self.cover_file = tmp
            self.cover_label.config(text=f"Extracted from audio ({Path(tmp).name})")
            self._update_cover_preview(tmp)

            if not silent:
                messagebox.showinfo("Success", "Cover art extracted from audio file")

        except Exception as e:
            if not silent:
                messagebox.showerror("Error", f"Failed to extract cover:\n{e}")

    def _select_cover(self):
        filename = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
        )
        if filename:
            self.cover_file = filename
            self.cover_label.config(text=Path(filename).name)
            self._update_cover_preview(filename)

    def _update_cover_preview(self, image_path: str):
        try:
            from PIL import Image
            import io, base64
            img = Image.open(image_path)
            img.load()
            img.thumbnail((120, 120), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64_data = base64.b64encode(buf.getvalue()).decode("ascii")
            photo = tk.PhotoImage(data=b64_data)
            self.cover_preview_label.configure(image=photo)
            self.cover_preview_label.configure(text="")
            self.cover_preview_label.image = photo
        except ImportError:
            self.cover_preview_label.config(text="[Cover]")
        except Exception:
            import traceback
            traceback.print_exc()
            self.cover_preview_label.config(text="[Error]")

    # ── M4B creation ────────────────────────────────────────────────

    def _create_m4b(self):
        if not self.audio_files:
            messagebox.showerror("Error", "Add at least one audio file")
            return

        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Error", "Enter a book title")
            return

        # Build safe filename from title
        safe = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        if not safe:
            safe = "audiobook"

        initial_dir = os.path.dirname(os.path.abspath(self.audio_files[0]))
        output_path = filedialog.asksaveasfilename(
            title="Save M4B File",
            initialdir=initial_dir,
            initialfile=f"{safe}.m4b",
            defaultextension=".m4b",
            filetypes=[("M4B Audiobook", "*.m4b"), ("All files", "*.*")]
        )
        if not output_path:
            return

        # Gather chapter titles
        chapter_titles = None
        if self.use_tags_var.get():
            chapter_titles = []
            for af in self.audio_files:
                try:
                    tags = self.creator.extract_metadata(af)
                    chapter_titles.append(tags.get('title', Path(af).stem))
                except Exception:
                    chapter_titles.append(Path(af).stem)

        # Read values from widgets now (main thread), not from the background thread
        author = self.author_entry.get().strip() or None
        narrator = self.narrator_entry.get().strip() or None
        year = self.year_entry.get().strip() or None
        comment_text = self.comment_text.get("1.0", tk.END).strip() or None
        cover = self.cover_file
        bitrate = self.bitrate_var.get()
        audio_files = list(self.audio_files)  # snapshot the list

        # Create progress overlay dialog
        progress = tk.Toplevel(self)
        progress.title("Creating M4B")
        progress.geometry("450x180")
        progress.transient(self)
        progress.grab_set()
        progress.resizable(False, False)
        progress.protocol("WM_DELETE_WINDOW", lambda: None)  # prevent closing

        # Center on parent
        progress.update_idletasks()
        px = self.winfo_x() + (self.winfo_width() // 2) - 225
        py = self.winfo_y() + (self.winfo_height() // 2) - 90
        progress.geometry(f"450x180+{px}+{py}")

        ttk.Label(progress, text="Creating M4B File...",
                  font=('TkDefaultFont', 13, 'bold')).pack(pady=(20, 10))

        prog_status = ttk.Label(progress, text="Starting...")
        prog_status.pack(pady=(0, 8))

        prog_bar = ttk.Progressbar(progress, mode='determinate', length=380)
        prog_bar.pack(pady=(0, 10))

        prog_detail = ttk.Label(progress, text="", foreground="gray")
        prog_detail.pack()

        # Use a shared result variable and polling instead of self.after from threads
        result_holder = {"done": False, "error": None}

        def on_progress(msg: str, frac: float):
            result_holder["progress"] = (msg, frac)

        def poll_progress():
            """Poll for updates from the background thread."""
            if "progress" in result_holder:
                msg, frac = result_holder.pop("progress")
                prog_status.config(text=msg)
                prog_bar["value"] = frac * 100
                prog_detail.config(text=f"{int(frac * 100)}% complete")

            if result_holder["done"]:
                progress.destroy()
                if result_holder["error"]:
                    messagebox.showerror("Error", f"Failed:\n{result_holder['error']}")
                else:
                    messagebox.showinfo("Success", f"M4B created!\n\n{output_path}")
                return

            progress.after(100, poll_progress)

        def run():
            try:
                self.creator.create(
                    audio_files=audio_files,
                    output_path=output_path,
                    chapter_titles=chapter_titles,
                    title=title,
                    author=author,
                    narrator=narrator,
                    year=year,
                    comment=comment_text,
                    cover_path=cover,
                    bitrate=bitrate,
                    progress_callback=on_progress,
                )
            except Exception as e:
                import traceback
                result_holder["error"] = traceback.format_exc()
            finally:
                result_holder["done"] = True

        threading.Thread(target=run, daemon=True).start()
        progress.after(100, poll_progress)


def main():
    app = M4BCreatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
