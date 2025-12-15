#!/usr/bin/env python3
"""
Xstory - A simple desktop app to explore story-tree databases.
Uses tkinter for GUI and SQLite for database access.
"""

import os
import sys
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Status colors (21-status rainbow system - ordered by production proximity)
STATUS_COLORS = {
    # Red Zone (Can't/Won't) - Furthest from production
    'infeasible': '#8B0000',   # Deep Red
    'rejected': '#FF4500',     # Red-Orange
    'wishlist': '#FF8C00',     # Orange
    # Orange-Yellow Zone (Concept)
    'concept': '#FFA500',      # Yellow-Orange
    'refine': '#FFD700',       # Gold
    'deferred': '#9ACD32',     # Yellow-Green
    'approved': '#FFDB58',     # Light Gold
    # Yellow Zone (Planning)
    'blocked': '#EEE8AA',      # Light Goldenrod
    'planned': '#B8860B',      # Dark Goldenrod
    'queued': '#DAA520',       # Goldenrod
    'broken': '#FFB347',       # Sandy (bug/issue indicator)
    'paused': '#BDB76B',       # Dark Khaki
    # Green Zone (Development)
    'active': '#32CD32',       # Lime Green
    # Cyan-Blue Zone (Testing)
    'reviewing': '#40E0D0',    # Turquoise
    'implemented': '#4169E1',  # Royal Blue
    # Blue Zone (Production)
    'ready': '#0000FF',        # Blue
    'polish': '#0047AB',       # Cobalt Blue
    'released': '#4169E1',     # Royal Blue
    # Violet Zone (Post-Production/End-of-Life)
    'legacy': '#4B0082',       # Indigo
    'deprecated': '#9400D3',   # Dark Violet
    'archived': '#800080',     # Purple
}

# All possible statuses (21-status system - canonical order)
ALL_STATUSES = [
    'infeasible', 'rejected', 'wishlist', 'concept', 'refine', 'deferred', 'approved',
    'blocked', 'planned', 'queued', 'broken', 'paused', 'active', 'reviewing',
    'implemented', 'ready', 'polish', 'released', 'legacy', 'deprecated', 'archived',
]

# Role-based status transitions
DESIGNER_TRANSITIONS = {
    'infeasible': ['concept', 'wishlist', 'archived'],
    'rejected': ['concept', 'wishlist', 'archived'],
    'wishlist': ['concept', 'rejected', 'archived'],
    'concept': ['approved', 'rejected', 'wishlist', 'refine'],
    'refine': ['concept', 'rejected', 'wishlist'],
    'deferred': ['approved', 'wishlist', 'rejected'],
    'approved': ['deferred', 'rejected'],
    'blocked': ['deferred'],
    'planned': ['deferred', 'approved'],
    'paused': ['deferred'],
    'reviewing': ['implemented'],
    'implemented': ['ready'],
    'ready': ['released', 'polish'],
    'polish': ['ready', 'released'],
    'released': ['polish', 'legacy'],
    'legacy': ['deprecated', 'released', 'archived'],
    'deprecated': ['archived', 'legacy'],
    'archived': ['deprecated', 'wishlist'],
}

ENGINEER_TRANSITIONS = {
    'approved': ['planned'],
    'blocked': ['planned', 'queued'],
    'planned': ['queued', 'blocked'],
    'queued': ['active', 'blocked', 'paused', 'planned'],
    'broken': ['active', 'paused', 'blocked', 'queued'],
    'paused': ['active', 'queued', 'blocked'],
    'active': ['reviewing', 'paused', 'broken', 'blocked'],
    'reviewing': ['active', 'broken'],
    'implemented': ['reviewing', 'broken'],
    'ready': ['reviewing'],
    'polish': ['reviewing'],
    'released': ['broken'],
}


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
        elif self.new_status == 'refine':
            prompt_text = "Please explain what needs to be refined (required):"
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

    def __init__(self, parent, app: 'XstoryExplorer'):
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

        status_color = STATUS_COLORS.get(child.status, '#000000')
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


class XstoryExplorer:
    """Main application class."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Xstory")
        self.root.geometry("900x600")

        self.db_path: Optional[str] = None
        self.nodes: Dict[str, StoryNode] = {}
        self.status_vars: Dict[str, tk.BooleanVar] = {}
        self.tree_items: Dict[str, str] = {}  # node_id -> tree item id
        self.current_role: str = 'designer'  # 'designer' or 'engineer'

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

        # Role toggle (Designer/Engineer)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Label(toolbar, text="Role:").pack(side=tk.LEFT, padx=(0, 5))
        self.role_button = ttk.Button(toolbar, text="Designer", width=10, command=self._toggle_role)
        self.role_button.pack(side=tk.LEFT, padx=2)

        # Container for switchable views
        self.view_container = ttk.Frame(self.main_frame)
        self.view_container.pack(fill=tk.BOTH, expand=True)

        # Tree view frame
        self.tree_view_frame = ttk.Frame(self.view_container)

        # Paned window for tree and filters
        paned = ttk.PanedWindow(self.tree_view_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel: Tree view
        tree_frame = ttk.Frame(paned)
        paned.add(tree_frame, weight=3)

        # Tree with scrollbars
        tree_container = ttk.Frame(tree_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(tree_container, columns=('status', 'title'), show='tree headings')
        self.tree.heading('#0', text='ID', anchor=tk.W)
        self.tree.heading('status', text='Status', anchor=tk.W)
        self.tree.heading('title', text='Title', anchor=tk.W)

        self.tree.column('#0', width=120, minwidth=80)
        self.tree.column('status', width=100, minwidth=80)
        self.tree.column('title', width=400, minwidth=200)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Right panel: Filters
        filter_frame = ttk.LabelFrame(paned, text="Status Filters", padding="5")
        paned.add(filter_frame, weight=1)

        # Select All / None buttons
        btn_frame = ttk.Frame(filter_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(btn_frame, text="All", command=self._select_all_statuses, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="None", command=self._select_no_statuses, width=6).pack(side=tk.LEFT, padx=2)

        # Status checkboxes
        for status in ALL_STATUSES:
            var = tk.BooleanVar(value=True)
            self.status_vars[status] = var
            cb = ttk.Checkbutton(filter_frame, text=status, variable=var,
                                command=self._apply_filters)
            cb.pack(anchor=tk.W)

        # Description panel at bottom of tree view
        desc_frame = ttk.LabelFrame(self.tree_view_frame, text="Description (double-click node for details)", padding="5")
        desc_frame.pack(fill=tk.X, pady=(5, 0))

        self.desc_text = tk.Text(desc_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.desc_text.pack(fill=tk.X)

        # Bind tree events
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        self.tree.bind('<Double-Button-1>', self._on_tree_double_click)
        self.tree.bind('<Button-3>', self._on_tree_right_click)  # Right-click context menu

        # Create context menu (initially empty, populated on right-click)
        self.context_menu = tk.Menu(self.root, tearoff=0)

        # Detail view frame
        self.detail_view = DetailView(self.view_container, self)

        # Status bar
        self.status_bar = ttk.Label(self.main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))

        # Show tree view by default
        self.show_tree_view()

    def _toggle_role(self):
        """Toggle between Designer and Engineer roles."""
        if self.current_role == 'designer':
            self.current_role = 'engineer'
            self.role_button.config(text="Engineer")
        else:
            self.current_role = 'designer'
            self.role_button.config(text="Designer")
        self.status_bar.config(text=f"Switched to {self.current_role.capitalize()} mode")

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

    def _on_tree_double_click(self, event):
        """Handle double-click to open detail view."""
        item_id = self.tree.identify_row(event.y)
        if item_id:
            node_id = self.tree.item(item_id, 'text')
            if node_id in self.nodes:
                self.detail_view.reset_history()
                self.show_detail_view(node_id)

    def _on_tree_right_click(self, event):
        """Handle right-click to show context menu."""
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        # Select the item under cursor
        self.tree.selection_set(item_id)

        node_id = self.tree.item(item_id, 'text')
        node = self.nodes.get(node_id)
        if not node:
            return

        # Clear existing menu items
        self.context_menu.delete(0, tk.END)

        # Get transitions based on current role
        transitions = DESIGNER_TRANSITIONS if self.current_role == 'designer' else ENGINEER_TRANSITIONS
        available_transitions = transitions.get(node.status, [])

        # Show header with current status and role
        self.context_menu.add_command(
            label=f"[{node.status}] ({self.current_role.capitalize()})",
            state=tk.DISABLED
        )
        self.context_menu.add_separator()

        # Add transition options
        if available_transitions:
            for target_status in available_transitions:
                # Use closure properly to capture target_status value
                self.context_menu.add_command(
                    label=f"→ {target_status}",
                    command=lambda nid=node_id, ts=target_status: self._change_node_status(nid, ts)
                )
        else:
            self.context_menu.add_command(
                label="(no transitions available)",
                state=tk.DISABLED
            )

        # Show context menu at cursor position
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _change_node_status(self, node_id: str, new_status: str):
        """Change a node's status with a notes dialog."""
        node = self.nodes.get(node_id)
        if not node:
            return

        # Determine if notes are mandatory
        mandatory = (new_status == 'refine')

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
        """Build the tree view from loaded nodes."""
        # Clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree_items.clear()

        # Find root nodes (nodes with no parent or parent not in nodes)
        root_nodes = [n for n in self.nodes.values()
                     if not n.parent_id or n.parent_id not in self.nodes]
        root_nodes.sort(key=lambda n: self._sort_key(n.id))

        # Build tree recursively
        for node in root_nodes:
            self._add_node_to_tree(node, '')

    def _add_node_to_tree(self, node: StoryNode, parent_item: str):
        """Add a node and its children to the tree."""
        item_id = self.tree.insert(
            parent_item, 'end',
            text=node.id,
            values=(node.status, node.title),
            open=True
        )
        self.tree_items[node.id] = item_id

        # Add children
        for child in node.children:
            self._add_node_to_tree(child, item_id)

    def _apply_filters(self):
        """Apply status filters to show/hide nodes with ancestry display.

        When filtering:
        - Nodes matching filter: display normally
        - Ancestor nodes of matching nodes: display faded (even if they don't match)
        - Non-matching nodes with no matching descendants: hide completely
        """
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

        # Configure faded tag: gray italic for ancestor-only nodes
        # Note: tkinter Treeview doesn't support per-column styling,
        # so we apply gray+italic to the entire row for faded nodes
        self.tree.tag_configure('faded', foreground='#999999', font=('TkDefaultFont', 9, 'italic'))

        for node_id, item_id in self.tree_items.items():
            node = self.nodes.get(node_id)
            if not node:
                continue

            if node_id in visible_nodes:
                # Show node - reattach if detached
                try:
                    self.tree.reattach(item_id, self._get_parent_item(node), 'end')
                except tk.TclError:
                    pass  # Already attached

                # Apply appropriate tags
                if node_id in faded_nodes:
                    # Ancestor-only: gray italic
                    self.tree.item(item_id, tags=('faded',))
                else:
                    # Matching node: default styling (black text)
                    self.tree.item(item_id, tags=())
            else:
                # Hide node
                try:
                    self.tree.detach(item_id)
                except tk.TclError:
                    pass  # Already detached

    def _get_parent_item(self, node: StoryNode) -> str:
        """Get the tree item ID for a node's parent."""
        if node.parent_id and node.parent_id in self.tree_items:
            return self.tree_items[node.parent_id]
        return ''

    def _get_ancestors(self, node_id: str) -> set:
        """Get all ancestor node IDs for a given node."""
        ancestors = set()
        node = self.nodes.get(node_id)
        while node and node.parent_id:
            ancestors.add(node.parent_id)
            node = self.nodes.get(node.parent_id)
        return ancestors

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

    def _on_tree_select(self, event):
        """Handle tree selection to show description."""
        selection = self.tree.selection()
        if not selection:
            return

        item_id = selection[0]
        node_id = self.tree.item(item_id, 'text')
        node = self.nodes.get(node_id)

        self.desc_text.config(state=tk.NORMAL)
        self.desc_text.delete('1.0', tk.END)

        if node:
            desc = node.description if node.description else '(no description)'
            self.desc_text.insert('1.0', desc)

        self.desc_text.config(state=tk.DISABLED)


def main():
    """Main entry point."""
    root = tk.Tk()
    app = XstoryExplorer(root)
    root.mainloop()


if __name__ == '__main__':
    main()
