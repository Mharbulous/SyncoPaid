#!/usr/bin/env python3
"""
Story Tree Explorer - A simple desktop app to explore story-tree databases.
Uses tkinter for GUI and SQLite for database access.
"""

import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Status colors (muted, readable on both light and dark backgrounds)
STATUS_COLORS = {
    'implemented': '#228B22',  # Forest green
    'ready': '#2E8B57',        # Sea green
    'active': '#4169E1',       # Royal blue
    'in-progress': '#6495ED',  # Cornflower blue
    'queued': '#9370DB',       # Medium purple
    'planned': '#708090',      # Slate gray
    'approved': '#32CD32',     # Lime green
    'concept': '#808080',      # Gray
    'epic': '#FF8C00',         # Dark orange
    'wishlist': '#DDA0DD',     # Plum
    'rejected': '#DC143C',     # Crimson
    'bugged': '#FF4500',       # Orange red
    'deprecated': '#A9A9A9',   # Dark gray
    'infeasible': '#696969',   # Dim gray
}

# All possible statuses
ALL_STATUSES = [
    'active', 'in-progress', 'queued', 'planned', 'approved', 'concept',
    'epic', 'wishlist', 'implemented', 'ready', 'rejected', 'bugged',
    'deprecated', 'infeasible'
]


class StoryNode:
    """Represents a story node from the database."""
    def __init__(self, id: str, title: str, status: str, capacity: Optional[int],
                 description: str = '', depth: int = 0, parent_id: Optional[str] = None):
        self.id = id
        self.title = title
        self.status = status
        self.capacity = capacity
        self.description = description
        self.depth = depth
        self.parent_id = parent_id
        self.children: List['StoryNode'] = []


class StoryTreeExplorer:
    """Main application class."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Story Tree Explorer")
        self.root.geometry("900x600")

        self.db_path: Optional[str] = None
        self.nodes: Dict[str, StoryNode] = {}
        self.status_vars: Dict[str, tk.BooleanVar] = {}
        self.tree_items: Dict[str, str] = {}  # node_id -> tree item id

        self._setup_ui()
        self._try_auto_detect_db()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(toolbar, text="Open Database...", command=self._open_database).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self._refresh).pack(side=tk.LEFT, padx=2)

        self.db_label = ttk.Label(toolbar, text="No database loaded")
        self.db_label.pack(side=tk.LEFT, padx=10)

        # Paned window for tree and filters
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
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

        # Description panel at bottom
        desc_frame = ttk.LabelFrame(main_frame, text="Description", padding="5")
        desc_frame.pack(fill=tk.X, pady=(5, 0))

        self.desc_text = tk.Text(desc_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.desc_text.pack(fill=tk.X)

        # Bind tree selection
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))

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

        # Get all nodes with their depth and parent
        query = """
            SELECT
                s.id, s.title, s.status, s.capacity, s.description,
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
                parent_id=row['parent_id']
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
            open=True,
            tags=(node.status,)
        )
        self.tree_items[node.id] = item_id

        # Configure tag color
        color = STATUS_COLORS.get(node.status, '#000000')
        self.tree.tag_configure(node.status, foreground=color)

        # Add children
        for child in node.children:
            self._add_node_to_tree(child, item_id)

    def _apply_filters(self):
        """Apply status filters to show/hide nodes."""
        visible_statuses = {s for s, var in self.status_vars.items() if var.get()}

        for node_id, item_id in self.tree_items.items():
            node = self.nodes.get(node_id)
            if node:
                # Detach or reattach based on filter
                if node.status in visible_statuses:
                    # Need to show - check if it's detached
                    try:
                        self.tree.reattach(item_id, self._get_parent_item(node), 'end')
                    except tk.TclError:
                        pass  # Already attached
                else:
                    # Need to hide
                    try:
                        self.tree.detach(item_id)
                    except tk.TclError:
                        pass  # Already detached

    def _get_parent_item(self, node: StoryNode) -> str:
        """Get the tree item ID for a node's parent."""
        if node.parent_id and node.parent_id in self.tree_items:
            return self.tree_items[node.parent_id]
        return ''

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
    app = StoryTreeExplorer(root)
    root.mainloop()


if __name__ == '__main__':
    main()
