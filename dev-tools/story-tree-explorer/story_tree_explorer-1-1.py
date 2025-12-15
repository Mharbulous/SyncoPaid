#!/usr/bin/env python3
"""
Story Tree Explorer v1.1 - Using tksheet for per-cell coloring
A simple desktop app to explore story-tree databases.
Uses tkinter + tksheet for GUI and SQLite for database access.
"""

import os
import sys
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from tksheet import Sheet
except ImportError:
    print("Error: tksheet is required. Install with: pip install tksheet")
    sys.exit(1)

# Status colors (23-status rainbow system - optimized for visibility)
STATUS_COLORS = {
    'infeasible': '#CC0000',   # Deep Red
    'rejected': '#CC3300',     # Red-Orange
    'wishlist': '#CC6600',     # Pumpkin Orange
    'concept': '#CC9900',      # Goldenrod
    'refine': '#CCCC00',       # Dark Gold / Olive
    'approved': '#99CC00',     # Lime Green
    'epic': '#66CC00',         # Chartreuse
    'planned': '#33CC00',      # Kelly Green
    'blocked': '#00CC00',      # Pure Green
    'deferred': '#00CC33',     # Spring Green
    'queued': '#00CC66',       # Emerald
    'bugged': '#00CC99',       # Teal Green
    'paused': '#00CCCC',       # Dark Cyan
    'active': '#0099CC',       # Cerulean
    'in-progress': '#0066CC',  # Azure
    'reviewing': '#0033CC',    # Cobalt Blue
    'implemented': '#0000CC',  # Pure Blue
    'ready': '#3300CC',        # Electric Indigo
    'polish': '#6600CC',       # Violet
    'released': '#9900CC',     # Purple
    'legacy': '#CC00CC',       # Magenta
    'deprecated': '#CC0099',   # Fuchsia
    'archived': '#CC0066',     # Deep Pink
}

# All possible statuses (23-status rainbow system)
ALL_STATUSES = [
    'infeasible', 'rejected', 'wishlist',
    'concept', 'refine', 'approved', 'epic',
    'planned', 'blocked', 'deferred',
    'queued', 'bugged', 'paused',
    'active', 'in-progress',
    'reviewing', 'implemented',
    'ready', 'polish', 'released',
    'legacy', 'deprecated', 'archived'
]


class StoryNode:
    """Represents a story node from the database."""
    def __init__(self, id: str, title: str, status: str, capacity: Optional[int],
                 description: str = '', depth: int = 0, parent_id: Optional[str] = None,
                 notes: str = '', project_path: str = '', created_at: str = '',
                 updated_at: str = '', last_implemented: str = ''):
        self.id = id
        self.title = title
        self.status = status
        self.capacity = capacity
        self.description = description
        self.depth = depth
        self.parent_id = parent_id
        self.notes = notes
        self.project_path = project_path
        self.created_at = created_at
        self.updated_at = updated_at
        self.last_implemented = last_implemented
        self.children: List['StoryNode'] = []


class StatusChangeDialog(tk.Toplevel):
    """Dialog for entering notes when changing story status."""

    def __init__(self, parent, node_id: str, new_status: str, mandatory: bool = False):
        super().__init__(parent)
        self.result: Optional[str] = None
        self.mandatory = mandatory
        self.node_id = node_id
        self.new_status = new_status

        # Configure dialog
        self.title(f"Change Status to '{new_status}'")
        self.geometry("400x250")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._setup_ui()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        # Bind escape key
        self.bind('<Escape>', lambda e: self._on_cancel())

        # Wait for dialog to close
        self.wait_window()

    def _setup_ui(self):
        """Set up the dialog UI."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_text = f"Changing '{self.node_id}' to status: {self.new_status}"
        ttk.Label(main_frame, text=header_text, font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W)

        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Prompt text based on status
        if self.new_status == 'approved':
            prompt_text = "Please note how high a priority this story is:"
        elif self.new_status == 'revising':
            prompt_text = "Please explain what needs to be revised (required):"
        else:
            prompt_text = "Add a note about this decision (optional):"

        ttk.Label(main_frame, text=prompt_text).pack(anchor=tk.W, pady=(0, 5))

        # Text area for notes
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.notes_text = tk.Text(text_frame, height=6, wrap=tk.WORD)
        self.notes_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.notes_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.notes_text.configure(yscrollcommand=scrollbar.set)

        # Focus on text area
        self.notes_text.focus_set()

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Confirm", command=self._on_confirm).pack(side=tk.RIGHT)

        # Bind Enter key (Ctrl+Enter for confirm with text)
        self.bind('<Control-Return>', lambda e: self._on_confirm())

    def _on_confirm(self):
        """Handle confirm button click."""
        notes = self.notes_text.get('1.0', tk.END).strip()

        if self.mandatory and not notes:
            messagebox.showwarning(
                "Notes Required",
                f"Notes are required when changing status to '{self.new_status}'.",
                parent=self
            )
            self.notes_text.focus_set()
            return

        self.result = notes
        self.destroy()

    def _on_cancel(self):
        """Handle cancel button click."""
        self.result = None
        self.destroy()


class DetailView(ttk.Frame):
    """Detail view panel showing all information about a story node."""

    def __init__(self, parent, app: 'StoryTreeExplorer'):
        super().__init__(parent)
        self.app = app
        self.history: List[str] = []  # Navigation history
        self.history_index: int = -1  # Current position in history
        self.current_node_id: Optional[str] = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the detail view UI."""
        # Navigation toolbar
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=tk.X, pady=(0, 10))

        self.back_btn = ttk.Button(nav_frame, text="< Back", command=self._go_back, width=8)
        self.back_btn.pack(side=tk.LEFT, padx=2)

        self.forward_btn = ttk.Button(nav_frame, text="Forward >", command=self._go_forward, width=8)
        self.forward_btn.pack(side=tk.LEFT, padx=2)

        ttk.Button(nav_frame, text="Close", command=self._close, width=8).pack(side=tk.RIGHT, padx=2)

        # Scrollable content area
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        self.content_frame = ttk.Frame(canvas)

        self.content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mouse wheel
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._update_nav_buttons()

    def show_node(self, node_id: str, add_to_history: bool = True):
        """Display details for a specific node."""
        if node_id not in self.app.nodes:
            return

        self.current_node_id = node_id
        node = self.app.nodes[node_id]

        # Update history
        if add_to_history:
            # Remove any forward history
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]
            self.history.append(node_id)
            self.history_index = len(self.history) - 1

        self._update_nav_buttons()

        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Node ID and Title header
        header = ttk.Frame(self.content_frame)
        header.pack(fill=tk.X, pady=(0, 10))

        id_label = ttk.Label(header, text=node.id, font=('TkDefaultFont', 14, 'bold'))
        id_label.pack(anchor=tk.W)

        title_label = ttk.Label(header, text=node.title, font=('TkDefaultFont', 12))
        title_label.pack(anchor=tk.W)

        ttk.Separator(self.content_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Status with color
        self._add_field("Status", node.status, color=STATUS_COLORS.get(node.status))

        # Capacity
        capacity_text = str(node.capacity) if node.capacity is not None else "dynamic"
        self._add_field("Capacity", capacity_text)

        # Depth
        self._add_field("Depth", str(node.depth))

        ttk.Separator(self.content_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Parent (clickable)
        if node.parent_id:
            self._add_link_field("Parent", node.parent_id)
        else:
            self._add_field("Parent", "(none)")

        # Children (clickable list)
        if node.children:
            children_frame = ttk.Frame(self.content_frame)
            children_frame.pack(fill=tk.X, pady=2)
            ttk.Label(children_frame, text="Children:", font=('TkDefaultFont', 9, 'bold')).pack(anchor=tk.W)

            for child in node.children:
                self._add_child_link(children_frame, child)
        else:
            self._add_field("Children", "(none)")

        ttk.Separator(self.content_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Description
        self._add_text_field("Description", node.description or "(no description)")

        # Notes
        if node.notes:
            self._add_text_field("Notes", node.notes)

        # Project path
        if node.project_path:
            self._add_field("Project Path", node.project_path)

        ttk.Separator(self.content_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Timestamps
        if node.created_at:
            self._add_field("Created", node.created_at)
        if node.updated_at:
            self._add_field("Updated", node.updated_at)
        if node.last_implemented:
            self._add_field("Last Implemented", node.last_implemented)

    def _add_field(self, label: str, value: str, color: Optional[str] = None):
        """Add a simple label: value field."""
        frame = ttk.Frame(self.content_frame)
        frame.pack(fill=tk.X, pady=2)

        ttk.Label(frame, text=f"{label}:", font=('TkDefaultFont', 9, 'bold'), width=15).pack(side=tk.LEFT, anchor=tk.N)

        value_label = ttk.Label(frame, text=value, wraplength=400)
        if color:
            value_label.configure(foreground=color)
        value_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _add_link_field(self, label: str, node_id: str):
        """Add a clickable link field."""
        frame = ttk.Frame(self.content_frame)
        frame.pack(fill=tk.X, pady=2)

        ttk.Label(frame, text=f"{label}:", font=('TkDefaultFont', 9, 'bold'), width=15).pack(side=tk.LEFT, anchor=tk.N)

        node = self.app.nodes.get(node_id)
        link_text = f"{node_id}"
        if node:
            link_text += f" - {node.title[:40]}{'...' if len(node.title) > 40 else ''}"

        link = tk.Label(frame, text=link_text, fg='#0066CC', cursor='hand2')
        link.pack(side=tk.LEFT)
        link.bind('<Double-Button-1>', lambda e, nid=node_id: self.show_node(nid))
        link.bind('<Enter>', lambda e: e.widget.configure(font=('TkDefaultFont', 9, 'underline')))
        link.bind('<Leave>', lambda e: e.widget.configure(font=('TkDefaultFont', 9)))

    def _add_child_link(self, parent_frame: ttk.Frame, child: StoryNode):
        """Add a clickable child link."""
        child_frame = ttk.Frame(parent_frame)
        child_frame.pack(fill=tk.X, padx=(20, 0))

        link_text = f"{child.id} [{child.status}] - {child.title[:50]}{'...' if len(child.title) > 50 else ''}"

        link = tk.Label(child_frame, text=link_text, fg='#0066CC', cursor='hand2')
        link.pack(anchor=tk.W)
        link.bind('<Double-Button-1>', lambda e, nid=child.id: self.show_node(nid))
        link.bind('<Enter>', lambda e: e.widget.configure(font=('TkDefaultFont', 9, 'underline')))
        link.bind('<Leave>', lambda e: e.widget.configure(font=('TkDefaultFont', 9)))

    def _add_text_field(self, label: str, text: str):
        """Add a multi-line text field."""
        frame = ttk.Frame(self.content_frame)
        frame.pack(fill=tk.X, pady=2)

        ttk.Label(frame, text=f"{label}:", font=('TkDefaultFont', 9, 'bold')).pack(anchor=tk.W)

        text_widget = tk.Text(frame, height=4, wrap=tk.WORD, relief=tk.FLAT, bg='#f5f5f5')
        text_widget.insert('1.0', text)
        text_widget.configure(state=tk.DISABLED)
        text_widget.pack(fill=tk.X, pady=(2, 0))

    def _update_nav_buttons(self):
        """Update the state of navigation buttons."""
        # Back button
        if self.history_index > 0:
            self.back_btn.configure(state=tk.NORMAL)
        else:
            self.back_btn.configure(state=tk.DISABLED)

        # Forward button
        if self.history_index < len(self.history) - 1:
            self.forward_btn.configure(state=tk.NORMAL)
        else:
            self.forward_btn.configure(state=tk.DISABLED)

    def _go_back(self):
        """Navigate to previous node in history."""
        if self.history_index > 0:
            self.history_index -= 1
            self.show_node(self.history[self.history_index], add_to_history=False)

    def _go_forward(self):
        """Navigate to next node in history."""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.show_node(self.history[self.history_index], add_to_history=False)

    def _close(self):
        """Close detail view and return to tree view."""
        self.app.show_tree_view()

    def reset_history(self):
        """Reset navigation history."""
        self.history.clear()
        self.history_index = -1
        self.current_node_id = None


class StoryTreeExplorer:
    """Main application class."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Story Tree Explorer v1.1 (tksheet)")
        self.root.geometry("1000x700")

        self.db_path: Optional[str] = None
        self.nodes: Dict[str, StoryNode] = {}
        self.status_vars: Dict[str, tk.BooleanVar] = {}
        self.iid_to_row: Dict[str, int] = {}  # Maps node_id to sheet row

        self._setup_ui()
        self._try_auto_detect_db()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="5")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Top toolbar
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(toolbar, text="Open Database...", command=self._open_database).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self._refresh).pack(side=tk.LEFT, padx=2)

        self.db_label = ttk.Label(toolbar, text="No database loaded")
        self.db_label.pack(side=tk.LEFT, padx=10)

        # Container for switchable views
        self.view_container = ttk.Frame(self.main_frame)
        self.view_container.pack(fill=tk.BOTH, expand=True)

        # Tree view frame
        self.tree_view_frame = ttk.Frame(self.view_container)

        # Paned window for tree and filters
        paned = ttk.PanedWindow(self.tree_view_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel: tksheet Tree view
        tree_frame = ttk.Frame(paned)
        paned.add(tree_frame, weight=3)

        # Create tksheet with treeview mode
        # In treeview mode, the row index shows the tree hierarchy (via 'text' param)
        # The 'values' populate the data columns
        self.sheet = Sheet(
            tree_frame,
            treeview=True,
            headers=["Status", "Title"],
            show_row_index=True,  # Required for tree hierarchy display
            show_header=True,
            height=500,
            width=700
        )
        self.sheet.enable_bindings((
            "single_select",
            "row_select",
            "column_width_resize",
            "double_click_column_resize",
            "tree_expand_collapse",
            "right_click_popup_menu",
            "copy",
        ))
        self.sheet.pack(fill=tk.BOTH, expand=True)

        # Set column widths (Status=col 0, Title=col 1; ID is in row index)
        self.sheet.column_width(column=0, width=100)
        self.sheet.column_width(column=1, width=400)
        # Set row index width for tree display (shows node IDs with hierarchy)
        self.sheet.set_options(index_width=180)

        # Bind events
        self.sheet.bind("<<SheetSelect>>", self._on_sheet_select)
        self.sheet.bind("<Double-Button-1>", self._on_sheet_double_click)
        self.sheet.bind("<Button-3>", self._on_sheet_right_click)

        # Right panel: Filters
        filter_frame = ttk.LabelFrame(paned, text="Status Filters", padding="5")
        paned.add(filter_frame, weight=1)

        # Select All / None buttons
        btn_frame = ttk.Frame(filter_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(btn_frame, text="All", command=self._select_all_statuses, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="None", command=self._select_no_statuses, width=6).pack(side=tk.LEFT, padx=2)

        # Status checkboxes (with rainbow colors)
        for status in ALL_STATUSES:
            var = tk.BooleanVar(value=True)
            self.status_vars[status] = var
            color = STATUS_COLORS.get(status, '#000000')
            # Use tk.Checkbutton instead of ttk.Checkbutton to support foreground color
            cb = tk.Checkbutton(filter_frame, text=status, variable=var,
                               command=self._apply_filters, fg=color,
                               anchor=tk.W)
            cb.pack(anchor=tk.W)

        # Description panel at bottom of tree view
        desc_frame = ttk.LabelFrame(self.tree_view_frame, text="Description (double-click node for details)", padding="5")
        desc_frame.pack(fill=tk.X, pady=(5, 0))

        self.desc_text = tk.Text(desc_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.desc_text.pack(fill=tk.X)

        # Create context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)

        # Detail view frame
        self.detail_view = DetailView(self.view_container, self)

        # Status bar
        self.status_bar = ttk.Label(self.main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))

        # Show tree view by default
        self.show_tree_view()

    def show_tree_view(self):
        """Switch to tree view."""
        self.detail_view.pack_forget()
        self.tree_view_frame.pack(fill=tk.BOTH, expand=True)
        self.status_bar.config(text=f"Loaded {len(self.nodes)} nodes" if self.nodes else "Ready")

    def show_detail_view(self, node_id: str):
        """Switch to detail view for a specific node."""
        self.tree_view_frame.pack_forget()
        self.detail_view.pack(fill=tk.BOTH, expand=True)
        self.detail_view.show_node(node_id)
        node = self.nodes.get(node_id)
        if node:
            self.status_bar.config(text=f"Viewing: {node_id} - {node.title}")

    def _on_sheet_select(self, event):
        """Handle sheet selection to show description."""
        selected = self.sheet.get_currently_selected()
        if not selected:
            return

        # Get the selected row
        try:
            if hasattr(selected, 'row') and selected.row is not None:
                row = selected.row
            else:
                return
        except:
            return

        # Get node_id from the row (treeview mode)
        try:
            # In treeview mode, use rowitem() to get the iid (node ID) from row
            node_id = self.sheet.rowitem(row)
            node = self.nodes.get(node_id)

            self.desc_text.config(state=tk.NORMAL)
            self.desc_text.delete('1.0', tk.END)

            if node:
                desc = node.description if node.description else '(no description)'
                self.desc_text.insert('1.0', desc)

            self.desc_text.config(state=tk.DISABLED)
        except:
            pass

    def _on_sheet_double_click(self, event):
        """Handle double-click to open detail view."""
        selected = self.sheet.get_currently_selected()
        if not selected:
            return

        try:
            if hasattr(selected, 'row') and selected.row is not None:
                row = selected.row
                # Get node_id using rowitem() in treeview mode
                node_id = self.sheet.rowitem(row)
                if node_id in self.nodes:
                    self.detail_view.reset_history()
                    self.show_detail_view(node_id)
        except:
            pass

    def _on_sheet_right_click(self, event):
        """Handle right-click to show context menu."""
        # Identify the row under cursor
        try:
            row = self.sheet.identify_row(event)
            if row is None:
                return

            # Get node_id using rowitem() in treeview mode
            node_id = self.sheet.rowitem(row)
            node = self.nodes.get(node_id)
            if not node:
                return

            # Clear existing menu items
            self.context_menu.delete(0, tk.END)

            # Build context menu based on status
            if node.status == 'concept':
                self.context_menu.add_command(
                    label="Approve",
                    command=lambda: self._change_node_status(node_id, 'approved')
                )
                self.context_menu.add_command(
                    label="Reject",
                    command=lambda: self._change_node_status(node_id, 'rejected')
                )
                self.context_menu.add_command(
                    label="Wishlist",
                    command=lambda: self._change_node_status(node_id, 'wishlist')
                )
                self.context_menu.add_command(
                    label="Revise",
                    command=lambda: self._change_node_status(node_id, 'revising')
                )
            else:
                # For non-concept nodes, show current status (disabled)
                self.context_menu.add_command(
                    label=f"Status: {node.status}",
                    state=tk.DISABLED
                )

            # Show context menu at cursor position
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
        except Exception as e:
            print(f"Right-click error: {e}")

    def _change_node_status(self, node_id: str, new_status: str):
        """Change a node's status with a notes dialog."""
        node = self.nodes.get(node_id)
        if not node:
            return

        # Determine if notes are mandatory
        mandatory = (new_status == 'revising')

        # Show dialog
        dialog = StatusChangeDialog(self.root, node_id, new_status, mandatory=mandatory)

        # Check if user confirmed (result is not None)
        if dialog.result is not None:
            notes = dialog.result
            self._update_node_status_in_db(node_id, new_status, notes)

    def _update_node_status_in_db(self, node_id: str, new_status: str, notes: str):
        """Update node status and notes in the database."""
        if not self.db_path:
            messagebox.showerror("Error", "No database loaded.")
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get current notes to append to
            cursor.execute("SELECT notes FROM story_nodes WHERE id = ?", (node_id,))
            row = cursor.fetchone()
            current_notes = row[0] if row and row[0] else ""

            # Build new notes with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

            if notes:
                new_note_entry = f"[{timestamp}] Status changed to '{new_status}': {notes}"
            else:
                new_note_entry = f"[{timestamp}] Status changed to '{new_status}'"

            if current_notes:
                updated_notes = f"{current_notes}\n{new_note_entry}"
            else:
                updated_notes = new_note_entry

            # Update status and notes
            cursor.execute(
                "UPDATE story_nodes SET status = ?, notes = ?, updated_at = ? WHERE id = ?",
                (new_status, updated_notes, datetime.now().isoformat(), node_id)
            )

            conn.commit()
            conn.close()

            self.status_bar.config(text=f"Updated '{node_id}' status to '{new_status}'")

            # Refresh the tree to show updated status
            self._refresh()

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update status:\n{e}")

    def _try_auto_detect_db(self):
        """Try to auto-detect the database file."""
        # Look for database relative to script location
        possible_paths = [
            # Relative to script
            Path(__file__).parent.parent.parent / '.claude' / 'data' / 'story-tree.db',
            # Relative to CWD
            Path.cwd() / '.claude' / 'data' / 'story-tree.db',
            # Up from CWD
            Path.cwd().parent / '.claude' / 'data' / 'story-tree.db',
        ]

        for path in possible_paths:
            if path.exists():
                self._load_database(str(path.resolve()))
                return

        self.status_bar.config(text="No database auto-detected. Use 'Open Database...' to load one.")

    def _open_database(self):
        """Open a database file via file dialog."""
        path = filedialog.askopenfilename(
            title="Open Story Tree Database",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
            initialdir=Path.cwd()
        )
        if path:
            self._load_database(path)

    def _load_database(self, path: str):
        """Load a database file."""
        if not os.path.exists(path):
            messagebox.showerror("Error", f"Database file not found:\n{path}")
            return

        self.db_path = path
        self.db_label.config(text=os.path.basename(path))
        self._refresh()

    def _refresh(self):
        """Refresh the tree from the database."""
        if not self.db_path:
            return

        try:
            self._load_nodes_from_db()
            self._build_tree()
            self._apply_filters()
            self.status_bar.config(text=f"Loaded {len(self.nodes)} nodes from {os.path.basename(self.db_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load database:\n{e}")
            self.status_bar.config(text=f"Error: {e}")

    def _load_nodes_from_db(self):
        """Load all nodes from the database."""
        self.nodes.clear()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all nodes with their depth, parent, and all fields
        query = """
            SELECT
                s.id, s.title, s.status, s.capacity, s.description,
                s.notes, s.project_path, s.created_at, s.updated_at, s.last_implemented,
                COALESCE(
                    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id AND ancestor_id != s.id),
                    0
                ) as depth,
                (SELECT ancestor_id FROM story_paths WHERE descendant_id = s.id AND depth = 1) as parent_id
            FROM story_nodes s
            ORDER BY s.id
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            node = StoryNode(
                id=row['id'],
                title=row['title'] or '',
                status=row['status'] or 'concept',
                capacity=row['capacity'],
                description=row['description'] or '',
                depth=row['depth'] or 0,
                parent_id=row['parent_id'],
                notes=row['notes'] or '',
                project_path=row['project_path'] or '',
                created_at=row['created_at'] or '',
                updated_at=row['updated_at'] or '',
                last_implemented=row['last_implemented'] or ''
            )
            self.nodes[node.id] = node

        conn.close()

        # Build parent-child relationships
        for node in self.nodes.values():
            if node.parent_id and node.parent_id in self.nodes:
                self.nodes[node.parent_id].children.append(node)

        # Sort children by ID
        for node in self.nodes.values():
            node.children.sort(key=lambda n: self._sort_key(n.id))

    def _sort_key(self, node_id: str) -> Tuple:
        """Generate a sort key for node IDs (root first, then numeric order)."""
        if node_id == 'root':
            return (0,)
        try:
            parts = node_id.split('.')
            return (1,) + tuple(int(p) for p in parts)
        except ValueError:
            return (2, node_id)

    def _build_tree(self):
        """Build the tree view from loaded nodes using tksheet."""
        # Just call _apply_filters which handles the actual tree building
        # This ensures we don't insert nodes twice
        pass

    def _get_ancestors(self, node_id: str) -> set:
        """Get all ancestor node IDs for a given node."""
        ancestors = set()
        node = self.nodes.get(node_id)
        while node and node.parent_id:
            ancestors.add(node.parent_id)
            node = self.nodes.get(node.parent_id)
        return ancestors

    def _apply_filters(self):
        """Apply status filters and color the Status column."""
        visible_statuses = {s for s, var in self.status_vars.items() if var.get()}

        # Step 1: Find all nodes that directly match the filter
        matching_nodes = {node_id for node_id, node in self.nodes.items()
                         if node.status in visible_statuses}

        # Step 2: Collect ancestors of all matching nodes
        ancestor_nodes = set()
        for node_id in matching_nodes:
            ancestor_nodes.update(self._get_ancestors(node_id))

        # Nodes to show = matching nodes + their ancestors
        visible_nodes = matching_nodes | ancestor_nodes
        # Ancestor-only nodes (shown faded)
        faded_nodes = ancestor_nodes - matching_nodes

        # Clear the treeview completely before rebuilding
        try:
            self.sheet.tree_reset()
        except Exception as e:
            print(f"tree_reset error: {e}")

        # Find root nodes that are visible
        root_nodes = [n for n in self.nodes.values()
                     if (not n.parent_id or n.parent_id not in self.nodes)
                     and n.id in visible_nodes]
        root_nodes.sort(key=lambda n: self._sort_key(n.id))

        # Build filtered tree
        row_index = 0
        for node in root_nodes:
            row_index = self._add_filtered_node(node, "", visible_nodes, faded_nodes, row_index)

        # Expand all
        try:
            self.sheet.tree_set_open(self.sheet.get_children())
        except:
            pass

    def _add_filtered_node(self, node: StoryNode, parent: str, visible_nodes: set,
                           faded_nodes: set, row_index: int) -> int:
        """Add a node to the filtered tree with appropriate coloring."""
        if node.id not in visible_nodes:
            return row_index

        # Insert the node
        # text = row index display (tree hierarchy with node ID)
        # values = data columns (Status, Title)
        self.sheet.insert(
            parent=parent,
            iid=node.id,
            text=node.id,
            values=[node.status, node.title]
        )

        # Get the row index for this node
        try:
            # Get row index from iid for highlighting
            row_idx = self.sheet.itemrow(node.id)
            if row_idx is not None:
                # Column mapping: Status=0, Title=1 (ID is in row index)
                status_color = STATUS_COLORS.get(node.status, '#000000')

                if node.id in faded_nodes:
                    # Faded ancestor: gray text for Title, but keep status color
                    self.sheet.highlight((row_idx, 0), fg=status_color)
                    self.sheet.highlight((row_idx, 1), fg='#999999')
                else:
                    # Normal node: colored status, black title
                    self.sheet.highlight((row_idx, 0), fg=status_color)
                    self.sheet.highlight((row_idx, 1), fg='#000000')
        except Exception as e:
            print(f"Highlight error for {node.id}: {e}")

        row_index += 1

        # Add visible children
        visible_children = [c for c in node.children if c.id in visible_nodes]
        visible_children.sort(key=lambda n: self._sort_key(n.id))

        for child in visible_children:
            row_index = self._add_filtered_node(child, node.id, visible_nodes, faded_nodes, row_index)

        return row_index

    def _get_all_descendants(self) -> List[str]:
        """Get all descendant iids from the tree."""
        descendants = []
        def collect(parent):
            children = self.sheet.get_children(parent)
            for child in children:
                descendants.append(child)
                collect(child)
        try:
            collect("")
        except:
            pass
        return descendants

    def _select_all_statuses(self):
        """Select all status filters."""
        for var in self.status_vars.values():
            var.set(True)
        self._apply_filters()

    def _select_no_statuses(self):
        """Deselect all status filters."""
        for var in self.status_vars.values():
            var.set(False)
        self._apply_filters()


def main():
    """Main entry point."""
    root = tk.Tk()
    app = StoryTreeExplorer(root)
    root.mainloop()


if __name__ == '__main__':
    main()
