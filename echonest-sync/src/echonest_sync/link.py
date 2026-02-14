"""Tkinter dialog for account linking via 6-character code."""

import json
import logging
import sys
import tkinter as tk
from tkinter import messagebox

import requests

from .config import save_config, set_token

log = logging.getLogger(__name__)


class LinkDialog:
    """Account linking dialog — prompts for 6-char code, exchanges it for a per-user token."""

    def __init__(self, server: str, token: str):
        self.server = server.rstrip("/")
        self.token = token
        self.result = None  # {"email": ..., "user_token": ...} on success

    def show(self):
        self.root = tk.Tk()
        self.root.title("EchoNest — Link Account")
        self.root.geometry("360x180")
        self.root.resizable(False, False)

        tk.Label(self.root, text="Enter the code from echone.st/sync/link",
                 font=("Helvetica", 12)).pack(pady=(20, 10))

        self.code_var = tk.StringVar()
        entry = tk.Entry(self.root, textvariable=self.code_var,
                         font=("Courier", 24), justify=tk.CENTER, width=8)
        entry.pack(pady=(0, 10))
        entry.bind("<Return>", lambda _: self._submit())
        entry.focus_set()

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=(0, 10))

        self.status_label = tk.Label(btn_frame, text="", fg="gray")
        self.status_label.pack(side=tk.LEFT, padx=(10, 10))

        tk.Button(btn_frame, text="Link", command=self._submit).pack(side=tk.RIGHT, padx=(0, 10))

        self.root.mainloop()

    def _submit(self):
        code = self.code_var.get().strip()
        if not code:
            self.status_label.config(text="Enter a code", fg="red")
            return

        self.status_label.config(text="Linking...", fg="gray")
        self.root.update_idletasks()

        try:
            resp = requests.post(
                f"{self.server}/api/sync-link",
                headers={"Authorization": f"Bearer {self.token}",
                         "Content-Type": "application/json"},
                json={"code": code},
                timeout=10,
            )

            if resp.status_code == 404:
                self.status_label.config(text="Invalid or expired code", fg="red")
                return
            if resp.status_code == 429:
                self.status_label.config(text="Too many attempts", fg="red")
                return

            resp.raise_for_status()
            data = resp.json()

            email = data["email"]
            user_token = data["user_token"]

            # Persist the per-user token and email
            set_token(user_token)
            save_config({"email": email})

            self.result = {"email": email, "user_token": user_token}
            messagebox.showinfo("Linked!", f"Account linked as {email}")
            self.root.destroy()

        except requests.exceptions.RequestException as e:
            self.status_label.config(text=f"Error: {e}", fg="red")


def launch_link(server: str, token: str, callback=None) -> None:
    """Launch the link dialog on a background thread."""
    import threading

    def _run():
        dialog = LinkDialog(server, token)
        dialog.show()
        if dialog.result and callback:
            callback(dialog.result)

    threading.Thread(target=_run, daemon=True).start()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="EchoNest Link Account")
    parser.add_argument("--server", required=True)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()

    LinkDialog(args.server, args.token).show()
