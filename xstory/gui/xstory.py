#!/usr/bin/env python3
"""
Xstory v1.2 - PySide6 Migration
A desktop app to explore story-tree databases.
Uses PySide6 (Qt for Python) under the LGPL v3 license.

PySide6 License: LGPL v3 (https://www.gnu.org/licenses/lgpl-3.0.html)
Qt for Python: https://www.qt.io/qt-for-python
"""

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTreeWidget, QTreeWidgetItem, QSplitter, QGroupBox, QCheckBox,
        QPushButton, QLabel, QTextEdit, QDialog, QDialogButtonBox,
        QFileDialog, QMessageBox, QScrollArea, QFrame, QStatusBar,
        QMenu, QLineEdit, QStyledItemDelegate, QStyleOptionViewItem, QStyle
    )
    from PySide6.QtCore import Qt, Signal, QSize, QRect, QPoint
    from PySide6.QtGui import (
        QBrush, QColor, QFont, QAction, QPixmap, QPainter, QPen, QIcon,
        QLinearGradient, QFontMetrics
    )
except ImportError:
    print("Error: PySide6 is required. Install with: pip install PySide6")
    sys.exit(1)

# Status colors (22-status rainbow system - optimized for visibility)
STATUS_COLORS = {
    # Dispositions (consistent red - terminal states, harshest to mildest)
    'infeasible': '#CC0000',   # Red (harshest - fundamentally impossible)
    'rejected': '#CC0000',     # Red (explicitly declined)
    'duplicative': '#CC0000',  # Red (redundant with another story)
    'deprecated': '#CC0000',   # Red (being phased out)
    'legacy': '#CC0000',       # Red (outdated/superseded)
    'archived': '#CC0000',     # Red (mildest - final cold storage)
    # Stages (greens/blues - workflow progression)
    'concept': '#66CC00',      # Lime green - RGB(102, 204, 0)
    'approved': '#00CC33',     # Spring Green
    'planned': '#00CC99',      # Teal (turquoise-green)
    'active': '#0099CC',       # Cerulean
    'reviewing': '#0066CC',    # Azure
    'verifying': '#0033CC',    # Royal Blue
    'implemented': '#0000CC',  # Pure Blue
    'ready': '#3300CC',        # Electric Indigo
    'released': '#6600CC',     # Violet
    # Hold reasons (gradient: reddish-orange to yellow for readability on gray)
    'broken': '#CC4400',       # RGB(204, 68, 0) - reddish orange (most urgent)
    'conflict': '#D25B00',     # RGB(210, 91, 0) - dark orange
    'blocked': '#DB7100',      # RGB(219, 113, 0) - orange
    'pending': '#E28B00',      # RGB(226, 139, 0) - golden orange
    'paused': '#E4A000',       # RGB(228, 160, 0) - gold
    'polish': '#E6B200',       # RGB(230, 178, 0) - dark gold
    'queued': '#E8C200',       # RGB(232, 194, 0) - dark yellow
    'wishlist': '#EAD000',     # RGB(234, 208, 0) - yellow (least urgent)
    'no hold': '#888888',      # Grey (no hold reason)
    # Live status (final stage in color wheel progression)
    'live': '#9900CC',         # Magenta - RGB(153, 0, 204) - 5.87:1 contrast
}

# All possible statuses (22-status rainbow system - canonical order)
ALL_STATUSES = [
    'infeasible', 'rejected', 'duplicative',
    'concept', 'broken', 'conflict', 'blocked', 'polish', 'wishlist',
    'pending', 'approved', 'planned', 'paused',
    'active', 'reviewing',
    'implemented',
    'ready', 'released',
    'legacy', 'deprecated', 'archived'
]

# Three-field system: classify each status into its field type
STAGE_VALUES = {'concept', 'approved', 'planned', 'active',
                'reviewing', 'verifying', 'implemented', 'ready', 'released'}
HOLD_REASON_VALUES = {'pending', 'paused', 'blocked', 'broken', 'polish', 'conflict', 'wishlist', 'queued'}
DISPOSITION_VALUES = {'rejected', 'infeasible', 'duplicative', 'legacy', 'deprecated', 'archived'}

# Ordered lists for UI display (urgency order for hold reasons)
STAGE_ORDER = ['concept', 'approved', 'planned', 'active',
               'reviewing', 'verifying', 'implemented', 'ready', 'released']
HOLD_REASON_ORDER = ['no hold', 'broken', 'conflict', 'blocked', 'pending', 'paused', 'polish', 'queued', 'wishlist']
DISPOSITION_ORDER = ['live', 'infeasible', 'rejected', 'duplicative', 'deprecated', 'legacy', 'archived']

# Hold reason icons for visual indication in tree view
HOLD_ICONS = {
    'queued': '📋',      # Queued - waiting in line
    'pending': '⏳',     # Pending - waiting for something
    'paused': '⏸',      # Paused - work temporarily stopped
    'blocked': '🚧',     # Blocked - missing dependency
    'broken': '🔥',      # Broken - needs fix
    'polish': '💎',      # Polish - needs refinement
    'conflict': '⚔',     # Conflict - inconsistent with another story
    'wishlist': '💭',    # Wishlist - indefinite hold, maybe someday
}

# Disposition icons for visual indication in tree view (override hold icons)
DISPOSITION_ICONS = {
    'rejected': '❌',      # Rejected - explicitly declined
    'infeasible': '🚫',    # Infeasible - cannot be done
    'duplicative': '👯‍♀️',   # Duplicative - duplicate of another
    'legacy': '🛑',        # Legacy - old/outdated
    'deprecated': '⚠️',    # Deprecated - no longer recommended
    'archived': '📦',      # Archived - stored away
}

# Default icon when no hold status
DEFAULT_STAGE_ICON = '▶️'


def calculate_stage_color(stage: str) -> QColor:
    """
    Calculate the gradient start color based on the node's stage.

    Uses HSL color space with:
    - Hue: Linear interpolation from 120° (green) to 240° (blue)
    - Saturation: Fixed at 100%
    - Lightness: Fixed at 40% for visibility on light backgrounds

    Args:
        stage: The stage value from STAGE_ORDER

    Returns:
        QColor representing the stage color
    """
    if stage not in STAGE_ORDER:
        # Default to first stage color for unknown stages
        stage = 'concept'

    stage_index = STAGE_ORDER.index(stage)
    total_stages = len(STAGE_ORDER)

    # Calculate hue: 120° (green) to 240° (blue)
    # Formula: Hue = 120 + (current_stage_index * (120 / (total_stages - 1)))
    if total_stages > 1:
        hue = 120 + (stage_index * (120 / (total_stages - 1)))
    else:
        hue = 120

    # HSL values: hue 0-360, saturation 0-1, lightness 0-1
    # Qt uses 0-359 for hue, 0-255 for saturation and lightness
    color = QColor()
    color.setHslF(hue / 360.0, 1.0, 0.40)
    return color


def calculate_gradient_colors(node: 'StoryNode') -> Tuple[QColor, QColor]:
    """
    Calculate the gradient start and end colors for a tree node.

    Color Logic:
    - Disposition active → Solid disposition color (no gradient)
    - Hold Status active (no disposition) → Gradient from stage color to black
    - Default → Solid stage color (no gradient)

    Args:
        node: StoryNode object with stage, hold_reason, and disposition

    Returns:
        Tuple of (start_color, end_color) as QColor objects
    """
    # Determine color based on priority: disposition > hold_reason > stage
    if node.disposition:
        # Disposition active → Use disposition color (solid, no gradient)
        color_hex = STATUS_COLORS.get(node.disposition, '#CC3300')  # Default to rejected color
        start_color = QColor(color_hex)
        end_color = start_color
        return start_color, end_color

    # Calculate start color based on stage
    start_color = calculate_stage_color(node.stage)

    # Determine end color based on hold status
    if node.hold_reason:
        # Hold Status active → Gradient to black
        end_color = QColor()
        end_color.setHslF(0 / 360.0, 0.0, 0.0)  # Black
    else:
        # Default → Solid stage color (no gradient)
        end_color = start_color

    return start_color, end_color


class GradientTextDelegate(QStyledItemDelegate):
    """
    Custom delegate for rendering tree node text with gradient colors.

    Renders node labels with colors based on:
    - Stage (determines base color: green → blue progression)
    - Hold Status (if active and no disposition, gradient ends in black)
    - Disposition (if active, solid stage color - disposition shown in Stage column)
    """

    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app  # Reference to XstoryExplorer for node lookup

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """Custom paint method for gradient text rendering."""
        # Get the node ID from column 0 of the same row
        tree_widget = option.widget
        item = tree_widget.itemFromIndex(index)
        if not item:
            super().paint(painter, option, index)
            return

        node_id = item.text(0)  # ID is always in column 0

        # Get the node data
        if not self.app or node_id not in self.app.nodes:
            super().paint(painter, option, index)
            return

        node = self.app.nodes[node_id]

        # Check if this node is a faded ancestor
        is_faded = item.data(0, Qt.UserRole) == 'faded'

        # Get text to display
        text = index.data(Qt.DisplayRole) or ''

        # Save painter state
        painter.save()

        # Draw selection/hover background if needed
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect, option.palette.light())

        # Calculate text rectangle with padding
        text_rect = option.rect.adjusted(4, 0, -4, 0)

        # Get font metrics
        font = option.font
        painter.setFont(font)
        fm = QFontMetrics(font)

        # For faded nodes, use gray solid color
        if is_faded:
            painter.setPen(QColor('#999999'))
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, text)
            painter.restore()
            return

        # Calculate gradient colors
        start_color, end_color = calculate_gradient_colors(node)

        # Check if this is a solid color (start == end)
        if start_color == end_color:
            painter.setPen(start_color)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, text)
            painter.restore()
            return

        # Create gradient for text
        # We need to render character by character with interpolated colors
        text_width = fm.horizontalAdvance(text)
        if text_width == 0:
            painter.restore()
            return

        # Draw text with gradient effect using character-by-character rendering
        x_pos = text_rect.left()
        y_pos = text_rect.top() + (text_rect.height() + fm.ascent() - fm.descent()) // 2

        total_width = min(text_width, text_rect.width())
        current_x = 0

        for char in text:
            char_width = fm.horizontalAdvance(char)
            if current_x + char_width > text_rect.width():
                break

            # Calculate interpolation factor (0.0 at start, 1.0 at end)
            t = current_x / total_width if total_width > 0 else 0

            # Interpolate color
            r = int(start_color.red() + t * (end_color.red() - start_color.red()))
            g = int(start_color.green() + t * (end_color.green() - start_color.green()))
            b = int(start_color.blue() + t * (end_color.blue() - start_color.blue()))

            painter.setPen(QColor(r, g, b))
            painter.drawText(x_pos + current_x, y_pos, char)

            current_x += char_width

        painter.restore()


# Designer mode transitions (approval, quality, priority, end-of-life decisions)
DESIGNER_TRANSITIONS = {
    'infeasible': ['concept', 'wishlist', 'archived'],
    'rejected': ['concept', 'wishlist', 'archived'],
    'wishlist': ['concept', 'rejected', 'archived'],
    'concept': ['approved', 'pending', 'rejected', 'wishlist', 'polish'],
    'polish': ['concept', 'ready', 'rejected', 'wishlist'],
    'pending': ['approved', 'wishlist', 'rejected'],
    'approved': ['pending', 'rejected'],
    'blocked': ['pending'],
    'planned': ['pending', 'approved'],
    'paused': ['pending'],
    'reviewing': ['implemented'],
    'implemented': ['ready'],
    'ready': ['released', 'polish'],
    'released': ['polish', 'legacy'],
    'legacy': ['deprecated', 'released', 'archived'],
    'deprecated': ['archived', 'legacy'],
    'archived': ['deprecated', 'wishlist'],
}

# Engineer mode transitions (workflow, blockers, bugs, progress)
ENGINEER_TRANSITIONS = {
    'approved': ['planned'],
    'blocked': ['planned', 'active'],
    'planned': ['active', 'blocked'],
    'broken': ['active', 'paused', 'blocked'],
    'paused': ['active', 'blocked'],
    'active': ['reviewing', 'paused', 'broken', 'blocked'],
    'reviewing': ['active', 'broken'],
    'implemented': ['reviewing', 'broken'],
    'ready': ['reviewing'],
    'polish': ['reviewing'],
    'released': ['broken'],
}


def create_checkbox_pixmap(color_hex: str, checked: bool) -> QPixmap:
    """Create a custom checkbox pixmap with white checkmark on colored background."""
    size = 18
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    if checked:
        # Draw colored background with border
        painter.setBrush(QBrush(QColor(color_hex)))
        painter.setPen(QPen(QColor(color_hex), 1))
        painter.drawRoundedRect(0, 0, size-1, size-1, 3, 3)

        # Draw white checkmark
        painter.setPen(QPen(QColor(Qt.white), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        # Checkmark path
        painter.drawLine(4, 9, 7, 13)
        painter.drawLine(7, 13, 14, 4)
    else:
        # Draw white background with gray border
        painter.setBrush(QBrush(QColor(Qt.white)))
        painter.setPen(QPen(QColor('#999999'), 1))
        painter.drawRoundedRect(0, 0, size-1, size-1, 3, 3)

    painter.end()
    return pixmap


class ColoredCheckBox(QCheckBox):
    """Custom checkbox with colored background and white checkmark when checked."""

    def __init__(self, text: str, color: str, parent=None):
        super().__init__(text, parent)
        self.status_color = color
        self.checkbox_size = 18
        self.checkbox_margin = 4

    def paintEvent(self, event):
        """Custom paint to draw checkbox with colored background and white checkmark."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate positions
        indicator_y = (self.height() - self.checkbox_size) // 2
        text_x = self.checkbox_margin + self.checkbox_size + 8  # 8px spacing

        # Draw custom checkbox indicator
        if self.isChecked():
            # Draw colored background
            painter.setBrush(QBrush(QColor(self.status_color)))
            painter.setPen(QPen(QColor(self.status_color), 1))
            painter.drawRoundedRect(self.checkbox_margin, indicator_y, self.checkbox_size - 1, self.checkbox_size - 1, 3, 3)

            # Draw white checkmark
            painter.setPen(QPen(QColor(Qt.white), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(self.checkbox_margin + 4, indicator_y + 9,
                           self.checkbox_margin + 7, indicator_y + 13)
            painter.drawLine(self.checkbox_margin + 7, indicator_y + 13,
                           self.checkbox_margin + 14, indicator_y + 4)
        else:
            # Draw white background with gray border
            painter.setBrush(QBrush(QColor(Qt.white)))
            painter.setPen(QPen(QColor('#999999'), 1))
            painter.drawRoundedRect(self.checkbox_margin, indicator_y, self.checkbox_size - 1, self.checkbox_size - 1, 3, 3)

        # Draw text in status color
        painter.setPen(QColor(self.status_color))
        font = self.font()
        painter.setFont(font)
        text_rect = self.rect()
        text_rect.setLeft(text_x)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.text())

        painter.end()

    def hitButton(self, pos):
        """Override to make the entire widget clickable."""
        return self.rect().contains(pos)

    def sizeHint(self):
        """Calculate proper size for checkbox and text."""
        fm = self.fontMetrics()
        text_width = fm.horizontalAdvance(self.text())
        width = self.checkbox_margin + self.checkbox_size + 8 + text_width + 5
        height = max(self.checkbox_size + 4, fm.height())
        return QSize(width, height)


class StoryNode:
    """Represents a story node from the database."""
    def __init__(self, id: str, title: str, status: str, capacity: Optional[int],
                 description: str = '', depth: int = 0, parent_id: Optional[str] = None,
                 notes: str = '', project_path: str = '', created_at: str = '',
                 updated_at: str = '', last_implemented: str = '',
                 stage: str = '', hold_reason: Optional[str] = None,
                 disposition: Optional[str] = None, descendants_count: int = 0,
                 success_criteria: str = '', story: str = ''):
        self.id = id
        self.title = title
        self.status = status  # Effective status: COALESCE(disposition, hold_reason, stage)
        self.capacity = capacity
        self.description = description
        self.depth = depth
        self.parent_id = parent_id
        self.notes = notes
        self.project_path = project_path
        self.created_at = created_at
        self.updated_at = updated_at
        self.last_implemented = last_implemented
        # Three-field system components
        self.stage = stage
        self.hold_reason = hold_reason
        self.disposition = disposition
        self.descendants_count = descendants_count
        self.success_criteria = success_criteria
        self.story = story
        self.children: List['StoryNode'] = []


class StatusChangeDialog(QDialog):
    """Dialog for entering notes when changing story status."""

    def __init__(self, parent, node_id: str, new_status: str, mandatory: bool = False):
        super().__init__(parent)
        self.node_id = node_id
        self.new_status = new_status
        self.mandatory = mandatory
        self.result_notes: Optional[str] = None

        self.setWindowTitle(f"Change Status to '{new_status}'")
        self.setFixedSize(400, 250)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Header
        header_text = f"Changing '{self.node_id}' to status: {self.new_status}"
        header_label = QLabel(header_text)
        header_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        layout.addWidget(header_label)

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Prompt text based on status
        if self.new_status == 'approved':
            prompt_text = "Please note how high a priority this story is:"
        elif self.new_status == 'polish':
            prompt_text = "Please explain what needs refinement (required):"
        else:
            prompt_text = "Add a note about this decision (optional):"

        layout.addWidget(QLabel(prompt_text))

        # Text area for notes
        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText("Enter notes here...")
        layout.addWidget(self.notes_text)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_confirm)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_confirm(self):
        """Handle confirm button click."""
        notes = self.notes_text.toPlainText().strip()

        if self.mandatory and not notes:
            QMessageBox.warning(
                self,
                "Notes Required",
                f"Notes are required when changing status to '{self.new_status}'."
            )
            self.notes_text.setFocus()
            return

        self.result_notes = notes
        self.accept()

    def get_notes(self) -> Optional[str]:
        """Return the entered notes if dialog was accepted."""
        return self.result_notes


class ClickableLabel(QLabel):
    """A QLabel that emits a signal when double-clicked."""
    doubleClicked = Signal(str)

    def __init__(self, text: str, node_id: str, parent=None):
        super().__init__(text, parent)
        self.node_id = node_id
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("color: #0066CC;")

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(self.node_id)

    def enterEvent(self, event):
        font = self.font()
        font.setUnderline(True)
        self.setFont(font)

    def leaveEvent(self, event):
        font = self.font()
        font.setUnderline(False)
        self.setFont(font)


class DetailView(QWidget):
    """Detail view panel showing all information about a story node."""
    closeRequested = Signal()

    def __init__(self, app: 'XstoryExplorer', parent=None):
        super().__init__(parent)
        self.app = app
        self.history: List[str] = []
        self.history_index: int = -1
        self.current_node_id: Optional[str] = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the detail view UI with two-column layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Combined header bar with navigation, db label, and breadcrumbs
        header_widget = QWidget()
        header_widget.setFixedHeight(30)
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(8, 2, 8, 2)
        header_layout.setSpacing(4)

        # Back button
        self.back_btn = QPushButton("<")
        self.back_btn.clicked.connect(self._go_back)
        self.back_btn.setFixedSize(18, 18)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-weight: bold;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #e9ecef; }
            QPushButton:disabled { color: #adb5bd; border-color: #dee2e6; }
        """)
        header_layout.addWidget(self.back_btn)

        # Forward button
        self.forward_btn = QPushButton(">")
        self.forward_btn.clicked.connect(self._go_forward)
        self.forward_btn.setFixedSize(18, 18)
        self.forward_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-weight: bold;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #e9ecef; }
            QPushButton:disabled { color: #adb5bd; border-color: #dee2e6; }
        """)
        header_layout.addWidget(self.forward_btn)

        header_layout.addSpacing(8)

        # Breadcrumb area (inline with header)
        self.breadcrumb_widget = QWidget()
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_widget)
        self.breadcrumb_layout.setContentsMargins(0, 0, 0, 0)
        self.breadcrumb_layout.setSpacing(4)
        header_layout.addWidget(self.breadcrumb_widget)

        header_layout.addStretch()

        main_layout.addWidget(header_widget)

        # Two-column layout (main content + sidebar)
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setStyleSheet("QSplitter::handle { background-color: #dee2e6; }")

        # Left: Main content area
        main_content_widget = QWidget()
        main_content_widget.setStyleSheet("background-color: #ffffff;")
        main_content_layout = QVBoxLayout(main_content_widget)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(0)

        # Scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #ffffff; }")

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: #ffffff;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(24, 16, 24, 16)
        self.content_layout.setSpacing(16)
        self.content_layout.setAlignment(Qt.AlignTop)

        scroll_area.setWidget(self.content_widget)
        main_content_layout.addWidget(scroll_area)

        # Footer with status buttons
        footer_widget = QWidget()
        footer_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
            }
        """)
        self.footer_layout = QHBoxLayout(footer_widget)
        self.footer_layout.setContentsMargins(16, 12, 16, 12)
        self.footer_layout.setSpacing(8)

        # Container for status buttons (left-aligned)
        self.status_buttons_widget = QWidget()
        self.status_buttons_widget.setStyleSheet("background: transparent;")
        self.status_buttons_layout = QHBoxLayout(self.status_buttons_widget)
        self.status_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.status_buttons_layout.setSpacing(8)
        self.footer_layout.addWidget(self.status_buttons_widget)

        self.footer_layout.addStretch()

        # Close button (right-aligned)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self._close)
        close_btn.setFixedWidth(80)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #e9ecef; }
        """)
        self.footer_layout.addWidget(close_btn)

        main_content_layout.addWidget(footer_widget)
        content_splitter.addWidget(main_content_widget)

        # Right: Sidebar
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setMinimumWidth(280)
        self.sidebar_widget.setMaximumWidth(320)
        self.sidebar_widget.setStyleSheet("background-color: #f8f9fa;")

        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setFrameShape(QFrame.NoFrame)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sidebar_scroll.setStyleSheet("QScrollArea { border: none; background-color: #f8f9fa; }")

        sidebar_content = QWidget()
        sidebar_content.setStyleSheet("background-color: #f8f9fa;")
        self.sidebar_layout = QVBoxLayout(sidebar_content)
        self.sidebar_layout.setContentsMargins(16, 16, 16, 16)
        self.sidebar_layout.setSpacing(16)
        self.sidebar_layout.setAlignment(Qt.AlignTop)

        sidebar_scroll.setWidget(sidebar_content)
        sidebar_outer_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_outer_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_outer_layout.addWidget(sidebar_scroll)

        content_splitter.addWidget(self.sidebar_widget)
        content_splitter.setSizes([600, 300])

        main_layout.addWidget(content_splitter, 1)  # stretch factor ensures it takes remaining space

        self._update_nav_buttons()

    def _add_status_row(self, node: StoryNode):
        """Add the inline status row (Stage + Hold/Disposition)."""
        stage_color = STATUS_COLORS.get(node.stage, '#666666')

        row_layout = QHBoxLayout()
        row_layout.setSpacing(30)

        # Stage label
        stage_label = QLabel(f"Stage: <span style='color: {stage_color}; font-weight: bold;'>{node.stage}</span>")
        stage_label.setTextFormat(Qt.RichText)
        row_layout.addWidget(stage_label)

        # Disposition supersedes hold status
        if node.disposition:
            disp_color = '#CC0000'  # Always red for dispositions
            disp_label = QLabel(f"Disposition: <span style='color: {disp_color}; font-weight: bold;'>{node.disposition}</span>")
            disp_label.setTextFormat(Qt.RichText)
            row_layout.addWidget(disp_label)
        elif node.hold_reason:
            hold_color = STATUS_COLORS.get(node.hold_reason, '#888888')
            hold_label = QLabel(f"Hold: <span style='color: {hold_color}; font-weight: bold;'>{node.hold_reason}</span>")
            hold_label.setTextFormat(Qt.RichText)
            row_layout.addWidget(hold_label)

        row_layout.addStretch()
        self.content_layout.addLayout(row_layout)

    def _parse_user_story(self, description: str) -> Optional[dict]:
        """Parse user story format from description.

        Returns dict with 'as_a', 'i_want', 'so_that', and 'remaining' keys if found, None otherwise.
        The 'remaining' key contains any text after the user story (e.g., acceptance criteria).
        """
        import re

        if not description:
            return None

        # Pattern to match user story format (case insensitive)
        # Captures content up to a double newline or end of string for 'so_that'
        pattern = r'\*?\*?As a\*?\*?\s+(.+?)\s+\*?\*?I want\*?\*?\s+(.+?)\s+\*?\*?So that\*?\*?\s+(.+?)(?:\n\n|$)'
        match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)

        if match:
            # Get the remaining text after the user story
            remaining = description[match.end():].strip()
            return {
                'as_a': match.group(1).strip(),
                'i_want': match.group(2).strip(),
                'so_that': match.group(3).strip(),
                'remaining': remaining
            }
        return None

    def _update_breadcrumbs(self, node: StoryNode):
        """Update breadcrumb navigation showing node hierarchy."""
        # Clear existing breadcrumbs
        while self.breadcrumb_layout.count():
            item = self.breadcrumb_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Build ancestor chain
        ancestors = []
        current = node
        while current.parent_id and current.parent_id in self.app.nodes:
            parent = self.app.nodes[current.parent_id]
            ancestors.insert(0, parent)
            current = parent

        # Add ancestors (root node shows title only, others show "id - title")
        is_first = True
        for ancestor in ancestors:
            # Arrow separator (skip for first ancestor)
            if not is_first:
                arrow = QLabel(" > ")
                arrow.setStyleSheet("color: #6c757d; font-size: 9pt;")
                self.breadcrumb_layout.addWidget(arrow)
            is_first = False

            # Ancestor link - root node shows only title
            title = ancestor.title[:25] + '...' if len(ancestor.title) > 25 else ancestor.title
            if ancestor.id == 'root':
                btn = QPushButton(title)
            else:
                btn = QPushButton(f"{ancestor.id} - {title}")
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #0066CC;
                    padding: 4px 8px;
                    font-size: 9pt;
                    text-align: left;
                }
                QPushButton:hover { background-color: #e9ecef; border-radius: 4px; }
            """)
            btn.setCursor(Qt.PointingHandCursor)
            ancestor_id = ancestor.id
            btn.clicked.connect(lambda checked, aid=ancestor_id: self.show_node(aid))
            self.breadcrumb_layout.addWidget(btn)

        # Add current node (not clickable)
        if ancestors:
            arrow = QLabel(" > ")
            arrow.setStyleSheet("color: #6c757d; font-size: 9pt;")
            self.breadcrumb_layout.addWidget(arrow)

        # Current node - root shows title only, others show "id - title"
        title = node.title[:30] + '...' if len(node.title) > 30 else node.title
        if node.id == 'root':
            current_label = QLabel(title)
        else:
            current_label = QLabel(f"{node.id} - {title}")
        current_label.setStyleSheet("color: #212529; font-weight: 500; font-size: 9pt; padding: 4px 8px;")
        self.breadcrumb_layout.addWidget(current_label)

        self.breadcrumb_layout.addStretch()

    def _add_title_section(self, node: StoryNode):
        """Add the title section with ID badge and stage badge."""
        # Header row with ID badge, stage badge, and title
        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        # Top row: ID badge + Stage badge
        badges_row = QHBoxLayout()
        badges_row.setSpacing(12)

        # ID badge
        id_badge = QLabel(node.id)
        id_badge.setStyleSheet("""
            background-color: #e9ecef;
            color: #495057;
            padding: 4px 10px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 10pt;
        """)
        badges_row.addWidget(id_badge)

        # Stage badge with icon
        stage_color = STATUS_COLORS.get(node.stage, '#666666')
        stage_icon = self._get_stage_icon(node)
        stage_badge = QLabel(f"{stage_icon} {node.stage}")
        stage_badge.setStyleSheet(f"""
            background-color: {self._lighten_color(stage_color, 0.85)};
            color: {stage_color};
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 9pt;
            border: 1px solid {self._lighten_color(stage_color, 0.7)};
        """)
        badges_row.addWidget(stage_badge)

        # Hold/Disposition badge if applicable
        if node.disposition:
            disp_color = '#CC0000'
            disp_icon = DISPOSITION_ICONS.get(node.disposition, '')
            disp_badge = QLabel(f"{disp_icon} {node.disposition}")
            disp_badge.setStyleSheet(f"""
                background-color: #fce4e4;
                color: {disp_color};
                padding: 4px 12px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 9pt;
                border: 1px solid #f5c6c6;
            """)
            badges_row.addWidget(disp_badge)
        elif node.hold_reason:
            hold_color = STATUS_COLORS.get(node.hold_reason, '#888888')
            hold_icon = HOLD_ICONS.get(node.hold_reason, '')
            hold_badge = QLabel(f"{hold_icon} {node.hold_reason}")
            hold_badge.setStyleSheet(f"""
                background-color: {self._lighten_color(hold_color, 0.85)};
                color: {hold_color};
                padding: 4px 12px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 9pt;
                border: 1px solid {self._lighten_color(hold_color, 0.7)};
            """)
            badges_row.addWidget(hold_badge)

        badges_row.addStretch()
        header_layout.addLayout(badges_row)

        # Title
        title_label = QLabel(node.title)
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #212529;")
        title_label.setWordWrap(True)
        title_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        header_layout.addWidget(title_label)

        self.content_layout.addWidget(header_widget)

    def _get_stage_icon(self, node: StoryNode) -> str:
        """Get appropriate icon for node's stage."""
        stage_icons = {
            'concept': '*',
            'approved': 'v',
            'planned': '#',
            'active': '>',
            'reviewing': '?',
            'verifying': '!',
            'implemented': 'o',
            'ready': '+',
            'released': '^',
        }
        return stage_icons.get(node.stage, '>')

    def _lighten_color(self, hex_color: str, factor: float = 0.85) -> str:
        """Lighten a hex color by mixing with white."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _add_progress_bar(self, node: StoryNode):
        """Add workflow progress bar showing stage progression."""
        progress_widget = QWidget()
        progress_widget.setStyleSheet("background: transparent;")
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(4)

        # Calculate stage index for progress
        stage_index = STAGE_ORDER.index(node.stage) if node.stage in STAGE_ORDER else 0

        # Progress bar
        progress_percent = ((stage_index + 1) / len(STAGE_ORDER)) * 100
        stage_color = STATUS_COLORS.get(node.stage, '#666666')

        bar_widget = QWidget()
        bar_widget.setFixedHeight(8)
        bar_widget.setStyleSheet(f"""
            background-color: #e9ecef;
            border-radius: 4px;
        """)
        bar_layout = QHBoxLayout(bar_widget)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)

        # Filled portion
        filled = QWidget()
        filled.setStyleSheet(f"""
            background-color: {stage_color};
            border-radius: 4px;
        """)
        bar_layout.addWidget(filled, int(progress_percent))

        # Empty portion
        empty = QWidget()
        empty.setStyleSheet("background: transparent;")
        bar_layout.addWidget(empty, int(100 - progress_percent))

        progress_layout.addWidget(bar_widget)

        # Stage labels below bar
        stages_row = QHBoxLayout()
        stages_row.setSpacing(0)
        key_stages = ['concept', 'approved', 'planned', 'active', 'implemented', 'released']
        for i, stage in enumerate(key_stages):
            stage_lbl = QLabel(stage)
            is_current = stage == node.stage
            is_past = STAGE_ORDER.index(stage) < stage_index if stage in STAGE_ORDER else False
            color = '#212529' if is_current else ('#6c757d' if is_past else '#adb5bd')
            weight = 'bold' if is_current else 'normal'
            stage_lbl.setStyleSheet(f"color: {color}; font-size: 8pt; font-weight: {weight};")
            if i == 0:
                stage_lbl.setAlignment(Qt.AlignLeft)
            elif i == len(key_stages) - 1:
                stage_lbl.setAlignment(Qt.AlignRight)
            else:
                stage_lbl.setAlignment(Qt.AlignCenter)
            stages_row.addWidget(stage_lbl, 1)

        progress_layout.addLayout(stages_row)

        self.content_layout.addWidget(progress_widget)

    def _add_story_section(self, node: StoryNode, story: dict):
        """Add the Story section with user story format and icons.

        Args:
            node: The story node being displayed
            story: Parsed user story dict with 'as_a', 'i_want', 'so_that' keys
        """
        # Story content box with gradient background
        story_widget = QWidget()
        story_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fefefe, stop:1 #f8f9fa);
                border-radius: 8px;
            }
        """)
        story_layout = QVBoxLayout(story_widget)
        story_layout.setContentsMargins(16, 12, 16, 12)
        story_layout.setSpacing(12)

        # As a row
        as_a_row = QHBoxLayout()
        as_a_row.setSpacing(12)
        as_a_icon = QLabel("As a")
        as_a_icon.setStyleSheet("""
            color: #6c757d;
            font-size: 9pt;
            font-weight: bold;
            text-transform: uppercase;
        """)
        as_a_row.addWidget(as_a_icon)
        as_a_row.addStretch()
        story_layout.addLayout(as_a_row)

        as_a_text = QLabel(story['as_a'])
        as_a_text.setStyleSheet("color: #212529; font-size: 11pt; margin-left: 20px; background: transparent;")
        as_a_text.setWordWrap(True)
        as_a_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        story_layout.addWidget(as_a_text)

        # I want row
        i_want_row = QHBoxLayout()
        i_want_row.setSpacing(12)
        i_want_icon = QLabel("I want")
        i_want_icon.setStyleSheet("""
            color: #6c757d;
            font-size: 9pt;
            font-weight: bold;
            text-transform: uppercase;
        """)
        i_want_row.addWidget(i_want_icon)
        i_want_row.addStretch()
        story_layout.addLayout(i_want_row)

        i_want_text = QLabel(story['i_want'])
        i_want_text.setStyleSheet("color: #212529; font-size: 11pt; margin-left: 20px; background: transparent;")
        i_want_text.setWordWrap(True)
        i_want_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        story_layout.addWidget(i_want_text)

        # So that row
        so_that_row = QHBoxLayout()
        so_that_row.setSpacing(12)
        so_that_icon = QLabel("So that")
        so_that_icon.setStyleSheet("""
            color: #6c757d;
            font-size: 9pt;
            font-weight: bold;
            text-transform: uppercase;
        """)
        so_that_row.addWidget(so_that_icon)
        so_that_row.addStretch()
        story_layout.addLayout(so_that_row)

        so_that_text = QLabel(story['so_that'])
        so_that_text.setStyleSheet("color: #212529; font-size: 11pt; margin-left: 20px; background: transparent;")
        so_that_text.setWordWrap(True)
        so_that_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        story_layout.addWidget(so_that_text)

        self.content_layout.addWidget(story_widget)

    def _add_user_story_display(self, node: StoryNode):
        """Add the User Story section displaying the story field.

        Args:
            node: The story node being displayed
        """
        # Story content box with gradient background
        story_widget = QWidget()
        story_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fefefe, stop:1 #f8f9fa);
                border-radius: 8px;
            }
        """)
        story_layout = QVBoxLayout(story_widget)
        story_layout.setContentsMargins(16, 12, 16, 12)
        story_layout.setSpacing(8)

        # Header
        header = QLabel("User Story")
        header.setStyleSheet("""
            color: #6c757d;
            font-size: 9pt;
            font-weight: bold;
            text-transform: uppercase;
            background: transparent;
        """)
        story_layout.addWidget(header)

        # Story text
        story_text = QLabel(node.story)
        story_text.setStyleSheet("color: #212529; font-size: 11pt; background: transparent;")
        story_text.setWordWrap(True)
        story_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        story_layout.addWidget(story_text)

        self.content_layout.addWidget(story_widget)

    def _update_sidebar(self, node: StoryNode):
        """Update sidebar with metadata, tree context, and actions."""
        # Clear existing sidebar content
        while self.sidebar_layout.count():
            item = self.sidebar_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        # Metadata Card
        self._add_sidebar_metadata(node)

        # Acceptance Criteria Card
        self._add_acceptance_criteria_card(node)

        self.sidebar_layout.addStretch()

    def _add_sidebar_metadata(self, node: StoryNode):
        """Add metadata card to sidebar with plain text layout."""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 8px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(8)

        # Header
        header = QLabel("Metadata")
        header.setStyleSheet("""
            color: #6c757d;
            font-size: 9pt;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            background: transparent;
        """)
        card_layout.addWidget(header)

        # Parent row
        parent_row = QHBoxLayout()
        parent_row.setSpacing(6)
        parent_label = QLabel("Parent:")
        parent_label.setStyleSheet("color: #6c757d; font-size: 9pt; background: transparent;")
        parent_row.addWidget(parent_label)

        if node.parent_id and node.parent_id in self.app.nodes:
            parent_node = self.app.nodes[node.parent_id]
            parent_title = parent_node.title[:20] + '...' if len(parent_node.title) > 20 else parent_node.title
            parent_link = ClickableLabel(f"{node.parent_id} - {parent_title}", node.parent_id)
            parent_link.setStyleSheet("font-size: 9pt; background: transparent;")
            parent_link.doubleClicked.connect(self.show_node)
            parent_row.addWidget(parent_link)
        else:
            no_parent = QLabel("(root)")
            no_parent.setStyleSheet("color: #adb5bd; font-size: 9pt; background: transparent;")
            parent_row.addWidget(no_parent)

        parent_row.addStretch()
        card_layout.addLayout(parent_row)

        # Children row
        children_row = QHBoxLayout()
        children_row.setSpacing(6)
        children_label = QLabel("Children:")
        children_label.setStyleSheet("color: #6c757d; font-size: 9pt; background: transparent;")
        children_row.addWidget(children_label)
        children_value = QLabel(str(len(node.children)))
        children_value.setStyleSheet("color: #212529; font-size: 9pt; background: transparent;")
        children_row.addWidget(children_value)
        children_row.addStretch()
        card_layout.addLayout(children_row)

        # Capacity row
        capacity_row = QHBoxLayout()
        capacity_row.setSpacing(6)
        capacity_label = QLabel("Capacity:")
        capacity_label.setStyleSheet("color: #6c757d; font-size: 9pt; background: transparent;")
        capacity_row.addWidget(capacity_label)

        capacity_type = "dynamic" if node.capacity is None else str(node.capacity)
        max_capacity = node.capacity if node.capacity else 3
        used = len(node.children)
        capacity_value = QLabel(f"{capacity_type} ({used}/{max_capacity})")
        capacity_value.setStyleSheet("color: #212529; font-size: 9pt; background: transparent;")
        capacity_row.addWidget(capacity_value)
        capacity_row.addStretch()
        card_layout.addLayout(capacity_row)

        # Descendants row
        desc_row = QHBoxLayout()
        desc_row.setSpacing(6)
        desc_label = QLabel("Descendants:")
        desc_label.setStyleSheet("color: #6c757d; font-size: 9pt; background: transparent;")
        desc_row.addWidget(desc_label)
        desc_value = QLabel(str(node.descendants_count))
        desc_value.setStyleSheet("color: #212529; font-size: 9pt; background: transparent;")
        desc_row.addWidget(desc_value)
        desc_row.addStretch()
        card_layout.addLayout(desc_row)

        self.sidebar_layout.addWidget(card)

    def _add_acceptance_criteria_card(self, node: StoryNode):
        """Add acceptance criteria card to sidebar."""
        if not node.success_criteria:
            return

        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 8px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(8)

        # Header
        header = QLabel("Acceptance Criteria")
        header.setStyleSheet("""
            color: #6c757d;
            font-size: 9pt;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            background: transparent;
        """)
        card_layout.addWidget(header)

        # Parse and display criteria items
        criteria_lines = node.success_criteria.strip().split('\n')
        for line in criteria_lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is a checkbox item
            is_checked = False
            display_text = line

            if line.startswith('- [x]') or line.startswith('- [X]'):
                is_checked = True
                display_text = line[5:].strip()
            elif line.startswith('- [ ]'):
                is_checked = False
                display_text = line[5:].strip()
            elif line.startswith('- '):
                display_text = line[2:].strip()

            # Create row for criterion
            row = QHBoxLayout()
            row.setSpacing(6)

            # Checkbox indicator
            checkbox_label = QLabel("✓" if is_checked else "○")
            checkbox_label.setStyleSheet(f"""
                color: {'#28a745' if is_checked else '#adb5bd'};
                font-size: 10pt;
                background: transparent;
            """)
            checkbox_label.setFixedWidth(16)
            row.addWidget(checkbox_label)

            # Criterion text
            text_label = QLabel(display_text)
            text_label.setStyleSheet(f"""
                color: {'#6c757d' if is_checked else '#212529'};
                font-size: 9pt;
                background: transparent;
                {'text-decoration: line-through;' if is_checked else ''}
            """)
            text_label.setWordWrap(True)
            row.addWidget(text_label, 1)

            card_layout.addLayout(row)

        self.sidebar_layout.addWidget(card)

    def _add_metadata_card(self, node: StoryNode):
        """Add the metadata card with Parent, Children, Capacity, Descendants."""
        card_widget = QWidget()
        card_widget.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        card_layout = QVBoxLayout(card_widget)
        card_layout.setContentsMargins(12, 8, 12, 8)
        card_layout.setSpacing(8)

        # Row 1: Parent (clickable)
        parent_row = QHBoxLayout()
        parent_label = QLabel("Parent:")
        parent_label.setStyleSheet("font-weight: bold; background: transparent;")
        parent_row.addWidget(parent_label)

        if node.parent_id:
            parent_node = self.app.nodes.get(node.parent_id)
            if parent_node:
                parent_title = parent_node.title[:30] + '...' if len(parent_node.title) > 30 else parent_node.title
                link_text = f"{node.parent_id} - {parent_title}"
            else:
                link_text = node.parent_id
            parent_link = ClickableLabel(link_text, node.parent_id)
            parent_link.doubleClicked.connect(self.show_node)
            parent_row.addWidget(parent_link)
        else:
            parent_value = QLabel("(none)")
            parent_value.setStyleSheet("background: transparent;")
            parent_row.addWidget(parent_value)

        parent_row.addStretch()
        card_layout.addLayout(parent_row)

        # Row 2: Children, Capacity, Descendants
        stats_row = QHBoxLayout()
        stats_row.setSpacing(30)

        # Children
        children_label = QLabel(f"<b>Children:</b> {len(node.children)}")
        children_label.setTextFormat(Qt.RichText)
        children_label.setStyleSheet("background: transparent;")
        stats_row.addWidget(children_label)

        # Capacity
        capacity_text = str(node.capacity) if node.capacity is not None else "dynamic"
        capacity_label = QLabel(f"<b>Capacity:</b> {capacity_text}")
        capacity_label.setTextFormat(Qt.RichText)
        capacity_label.setStyleSheet("background: transparent;")
        stats_row.addWidget(capacity_label)

        # Descendants
        descendants_label = QLabel(f"<b>Descendants:</b> {node.descendants_count}")
        descendants_label.setTextFormat(Qt.RichText)
        descendants_label.setStyleSheet("background: transparent;")
        stats_row.addWidget(descendants_label)

        stats_row.addStretch()
        card_layout.addLayout(stats_row)

        self.content_layout.addWidget(card_widget)

    def show_node(self, node_id: str, add_to_history: bool = True):
        """Display details for a specific node with improved layout."""
        if node_id not in self.app.nodes:
            return

        self.current_node_id = node_id
        node = self.app.nodes[node_id]

        # Update history
        if add_to_history:
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]
            self.history.append(node_id)
            self.history_index = len(self.history) - 1

        self._update_nav_buttons()

        # Update breadcrumbs
        self._update_breadcrumbs(node)

        # Clear main content area (widgets AND layouts)
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        # Title section with badges
        self._add_title_section(node)

        # Display user story from story field, or parse from description as fallback
        if node.story:
            self._add_user_story_display(node)
        else:
            # Fallback: parse user story from description
            story = self._parse_user_story(node.description)
            if story:
                self._add_story_section(node, story)

        # Workflow progress bar
        self._add_progress_bar(node)

        # Success Criteria section
        if node.success_criteria:
            self._add_success_criteria_section(node)

        # Description section - always show if present
        if node.description:
            self._add_description_section(node, node.description)

        # Notes section
        if node.notes:
            self._add_notes_section(node)

        # Add stretch at the end
        self.content_layout.addStretch()

        # Update sidebar
        self._update_sidebar(node)

        # Add status action buttons to footer
        self._add_status_actions(node)

    def _add_description_section(self, node: StoryNode, description_text: str):
        """Add the description section.

        Args:
            node: The story node being displayed
            description_text: The text to display (may be full description or remaining after user story)
        """
        if not description_text:
            return

        desc_widget = QWidget()
        desc_widget.setStyleSheet("background: transparent;")
        desc_layout = QVBoxLayout(desc_widget)
        desc_layout.setContentsMargins(0, 0, 0, 0)
        desc_layout.setSpacing(8)

        header = QLabel("Description")
        header.setStyleSheet("font-size: 12pt; font-weight: bold; color: #212529;")
        desc_layout.addWidget(header)

        text = QLabel(description_text)
        text.setStyleSheet("""
            color: #495057;
            font-size: 10pt;
            line-height: 1.5;
            background-color: #f8f9fa;
            padding: 12px;
            border-radius: 6px;
        """)
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        desc_layout.addWidget(text)

        self.content_layout.addWidget(desc_widget)

    def _add_success_criteria_section(self, node: StoryNode):
        """Add the success criteria section.

        Args:
            node: The story node being displayed
        """
        if not node.success_criteria:
            return

        criteria_widget = QWidget()
        criteria_widget.setStyleSheet("background: transparent;")
        criteria_layout = QVBoxLayout(criteria_widget)
        criteria_layout.setContentsMargins(0, 0, 0, 0)
        criteria_layout.setSpacing(8)

        header = QLabel("Success Criteria")
        header.setStyleSheet("font-size: 12pt; font-weight: bold; color: #212529;")
        criteria_layout.addWidget(header)

        text = QLabel(node.success_criteria)
        text.setStyleSheet("""
            color: #495057;
            font-size: 10pt;
            line-height: 1.5;
            background-color: #f8f9fa;
            padding: 12px;
            border-radius: 6px;
        """)
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        criteria_layout.addWidget(text)

        self.content_layout.addWidget(criteria_widget)

    def _add_notes_section(self, node: StoryNode):
        """Add the notes section."""
        notes_widget = QWidget()
        notes_widget.setStyleSheet("background: transparent;")
        notes_layout = QVBoxLayout(notes_widget)
        notes_layout.setContentsMargins(0, 0, 0, 0)
        notes_layout.setSpacing(8)

        header = QLabel("Notes")
        header.setStyleSheet("font-size: 12pt; font-weight: bold; color: #212529;")
        notes_layout.addWidget(header)

        text = QLabel(node.notes)
        text.setStyleSheet("""
            color: #495057;
            font-size: 10pt;
            background-color: #fff3cd;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #ffc107;
        """)
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        notes_layout.addWidget(text)

        self.content_layout.addWidget(notes_widget)

    def _add_separator(self):
        """Add a horizontal line separator."""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.content_layout.addWidget(line)

    def _add_field(self, label: str, value: str, color: Optional[str] = None):
        """Add a simple label: value field."""
        row_layout = QHBoxLayout()
        label_widget = QLabel(f"{label}:")
        label_widget.setStyleSheet("font-weight: bold;")
        label_widget.setFixedWidth(120)
        row_layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setWordWrap(True)
        value_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if color:
            value_widget.setStyleSheet(f"color: {color};")
        row_layout.addWidget(value_widget)
        row_layout.addStretch()

        self.content_layout.addLayout(row_layout)

    def _add_link_field(self, label: str, node_id: str):
        """Add a clickable link field."""
        row_layout = QHBoxLayout()
        label_widget = QLabel(f"{label}:")
        label_widget.setStyleSheet("font-weight: bold;")
        label_widget.setFixedWidth(120)
        row_layout.addWidget(label_widget)

        node = self.app.nodes.get(node_id)
        link_text = node_id
        if node:
            title = node.title[:40] + '...' if len(node.title) > 40 else node.title
            link_text = f"{node_id} - {title}"

        link = ClickableLabel(link_text, node_id)
        link.doubleClicked.connect(self.show_node)
        row_layout.addWidget(link)
        row_layout.addStretch()

        self.content_layout.addLayout(row_layout)

    def _add_child_link(self, child: StoryNode):
        """Add a clickable child link."""
        title = child.title[:50] + '...' if len(child.title) > 50 else child.title
        link_text = f"  {child.id} [{child.status}] - {title}"

        link = ClickableLabel(link_text, child.id)
        link.doubleClicked.connect(self.show_node)
        self.content_layout.addWidget(link)

    def _add_text_field(self, label: str, text: str):
        """Add a multi-line text field that expands to fit content."""
        label_widget = QLabel(f"{label}:")
        label_widget.setStyleSheet("font-weight: bold;")
        self.content_layout.addWidget(label_widget)

        text_widget = QLabel(text)
        text_widget.setWordWrap(True)
        text_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_widget.setStyleSheet(
            "background-color: #f5f5f5; padding: 8px; border-radius: 4px;"
        )
        self.content_layout.addWidget(text_widget)

    def _add_status_actions(self, node: StoryNode):
        """Add context-aware status action buttons to footer based on current role."""
        # Clear existing status buttons from footer
        self._clear_status_buttons()

        # Get available transitions based on current role
        current_role = self.app.current_role
        if current_role == 'designer':
            transitions = DESIGNER_TRANSITIONS.get(node.status, [])
        else:
            transitions = ENGINEER_TRANSITIONS.get(node.status, [])

        if not transitions:
            return

        # Add status buttons to footer
        for target_status in transitions:
            status_color = STATUS_COLORS.get(target_status, '#666666')
            btn = QPushButton(f"→ {target_status}")
            btn.setFixedHeight(32)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {status_color};
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 12px;
                }}
                QPushButton:hover {{
                    background-color: {self._darken_color(status_color)};
                }}
                QPushButton:pressed {{
                    background-color: {self._darken_color(status_color, 0.7)};
                }}
            """)
            btn.clicked.connect(
                lambda checked, ns=target_status, nid=node.id: self._on_status_button_clicked(nid, ns)
            )
            self.status_buttons_layout.addWidget(btn)

    def _clear_status_buttons(self):
        """Clear all status buttons from the footer."""
        while self.status_buttons_layout.count():
            item = self.status_buttons_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _darken_color(self, hex_color: str, factor: float = 0.85) -> str:
        """Darken a hex color by the given factor."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_nodes_with_status(self, status: str) -> List[str]:
        """Get list of node IDs that have the given status."""
        return [node_id for node_id, node in self.app.nodes.items() if node.status == status]

    def _on_status_button_clicked(self, node_id: str, new_status: str):
        """Handle status button click - change status and navigate to next node with same original status."""
        # Get the original status before changing
        original_status = self.app.nodes[node_id].status if node_id in self.app.nodes else None

        # Get list of nodes with the original status (before the change)
        nodes_with_original_status = self._get_nodes_with_status(original_status) if original_status else []

        # Find the current node's position and the next node in the list
        next_node_id = None
        if node_id in nodes_with_original_status:
            current_index = nodes_with_original_status.index(node_id)
            # Look for the next node (after this one) with the original status
            if current_index < len(nodes_with_original_status) - 1:
                next_node_id = nodes_with_original_status[current_index + 1]
            elif current_index > 0:
                # If no next, fall back to previous node with original status
                next_node_id = nodes_with_original_status[current_index - 1]

        # Change the status
        self.app._change_node_status(node_id, new_status)

        # Navigate to the next node with the original status, or stay on current if none
        if next_node_id:
            self.show_node(next_node_id, add_to_history=True)
        elif self.current_node_id:
            # No other nodes with original status - stay on current node
            self.show_node(self.current_node_id, add_to_history=False)

    def _update_nav_buttons(self):
        """Update the state of navigation buttons."""
        self.back_btn.setEnabled(self.history_index > 0)
        self.forward_btn.setEnabled(self.history_index < len(self.history) - 1)

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
        self.closeRequested.emit()

    def reset_history(self):
        """Reset navigation history."""
        self.history.clear()
        self.history_index = -1
        self.current_node_id = None

    def _clear_layout(self, layout):
        """Recursively clear and delete a layout and its contents."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

class XstoryExplorer(QMainWindow):
    """Main application class."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xstory v1.2 (PySide6)")
        self.setGeometry(100, 100, 900, 700)

        self.db_path: Optional[str] = None
        self.nodes: Dict[str, StoryNode] = {}
        self.status_checkboxes: Dict[str, QCheckBox] = {}
        self.tree_items: Dict[str, QTreeWidgetItem] = {}  # Maps node_id to QTreeWidgetItem
        self.current_role: str = 'designer'  # 'designer' or 'engineer'

        self._setup_ui()
        self._try_auto_detect_db()

    def _setup_ui(self):
        """Set up the user interface."""
        # Central widget with stacked layout for switching views
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Top toolbar
        toolbar_layout = QHBoxLayout()

        self.open_btn = QPushButton("Open Database...")
        self.open_btn.clicked.connect(self._open_database)
        toolbar_layout.addWidget(self.open_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh)
        toolbar_layout.addWidget(self.refresh_btn)

        self.db_label = QLabel("No database loaded")
        toolbar_layout.addWidget(self.db_label)
        toolbar_layout.addStretch()

        # Role toggle button
        self.role_toggle_btn = QPushButton("Designer")
        self.role_toggle_btn.setCheckable(True)
        self.role_toggle_btn.setFixedWidth(100)
        self.role_toggle_btn.clicked.connect(self._toggle_role)
        self._update_role_button()
        toolbar_layout.addWidget(self.role_toggle_btn)

        self.main_layout.addLayout(toolbar_layout)

        # Container for switchable views
        self.view_container = QWidget()
        self.view_layout = QVBoxLayout(self.view_container)
        self.view_layout.setContentsMargins(0, 0, 0, 0)

        # Tree view frame
        self.tree_view_frame = QWidget()
        tree_view_layout = QVBoxLayout(self.tree_view_frame)
        tree_view_layout.setContentsMargins(0, 0, 0, 0)

        # Splitter for tree and filters
        splitter = QSplitter(Qt.Horizontal)

        # Left panel: Tree view
        tree_container = QWidget()
        tree_container_layout = QVBoxLayout(tree_container)
        tree_container_layout.setContentsMargins(0, 0, 0, 0)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ID", "Stage", "Title"])
        self.tree.setColumnCount(3)
        self.tree.setColumnWidth(0, 180)
        self.tree.setColumnWidth(1, 100)
        self.tree.setColumnWidth(2, 400)
        self.tree.setIndentation(10)  # Reduce indentation from default ~20px
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_tree_right_click)
        self.tree.itemSelectionChanged.connect(self._on_tree_select)
        self.tree.itemDoubleClicked.connect(self._on_tree_double_click)

        # Apply gradient text delegate only to Stage column (column 1)
        self.gradient_delegate = GradientTextDelegate(self.tree, app=self)
        self.tree.setItemDelegateForColumn(1, self.gradient_delegate)

        tree_container_layout.addWidget(self.tree)
        splitter.addWidget(tree_container)

        # Right panel: Filters (organized by three-field system)
        filter_scroll = QScrollArea()
        filter_scroll.setWidgetResizable(True)
        filter_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        filter_widget = QWidget()
        filter_main_layout = QVBoxLayout(filter_widget)

        # Master Select All / None buttons
        master_btn_layout = QHBoxLayout()
        all_btn = QPushButton("All")
        all_btn.clicked.connect(self._select_all_statuses)
        all_btn.setFixedWidth(60)
        master_btn_layout.addWidget(all_btn)

        none_btn = QPushButton("None")
        none_btn.clicked.connect(self._select_no_statuses)
        none_btn.setFixedWidth(60)
        master_btn_layout.addWidget(none_btn)
        master_btn_layout.addStretch()
        filter_main_layout.addLayout(master_btn_layout)

        # Three-column layout for filter categories (Stage | Hold Status | Disposition)
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(8)

        # Stage Filters section (left column)
        stage_group = QGroupBox("Stage")
        stage_layout = QVBoxLayout(stage_group)
        stage_btn_layout = QHBoxLayout()
        stage_all_btn = QPushButton("All")
        stage_all_btn.setFixedWidth(50)
        stage_all_btn.clicked.connect(lambda: self._select_category_statuses(STAGE_ORDER, True))
        stage_btn_layout.addWidget(stage_all_btn)
        stage_none_btn = QPushButton("None")
        stage_none_btn.setFixedWidth(50)
        stage_none_btn.clicked.connect(lambda: self._select_category_statuses(STAGE_ORDER, False))
        stage_btn_layout.addWidget(stage_none_btn)
        stage_btn_layout.addStretch()
        stage_layout.addLayout(stage_btn_layout)

        for status in STAGE_ORDER:
            color = STATUS_COLORS.get(status, '#000000')
            cb = ColoredCheckBox(status, color)
            cb.setChecked(True)
            cb.setStyleSheet("QCheckBox::indicator { width: 0px; height: 0px; }")
            cb.stateChanged.connect(lambda state, checkbox=cb: (checkbox.update(), self._apply_filters()))
            self.status_checkboxes[status] = cb
            stage_layout.addWidget(cb)

        stage_layout.addStretch()
        columns_layout.addWidget(stage_group)

        # Hold Status Filters section (middle column)
        hold_group = QGroupBox("Hold Status")
        hold_layout = QVBoxLayout(hold_group)
        hold_btn_layout = QHBoxLayout()
        hold_all_btn = QPushButton("All")
        hold_all_btn.setFixedWidth(50)
        hold_all_btn.clicked.connect(lambda: self._select_category_statuses(HOLD_REASON_ORDER, True))
        hold_btn_layout.addWidget(hold_all_btn)
        hold_none_btn = QPushButton("None")
        hold_none_btn.setFixedWidth(50)
        hold_none_btn.clicked.connect(lambda: self._select_category_statuses(HOLD_REASON_ORDER, False))
        hold_btn_layout.addWidget(hold_none_btn)
        hold_btn_layout.addStretch()
        hold_layout.addLayout(hold_btn_layout)

        for status in HOLD_REASON_ORDER:
            color = STATUS_COLORS.get(status, '#000000')
            cb = ColoredCheckBox(status, color)
            cb.setChecked(True)
            cb.setStyleSheet("QCheckBox::indicator { width: 0px; height: 0px; }")
            cb.stateChanged.connect(lambda state, checkbox=cb: (checkbox.update(), self._apply_filters()))
            self.status_checkboxes[status] = cb
            hold_layout.addWidget(cb)

        hold_layout.addStretch()
        columns_layout.addWidget(hold_group)

        # Disposition Filters section (right column)
        disp_group = QGroupBox("Disposition")
        disp_layout = QVBoxLayout(disp_group)
        disp_btn_layout = QHBoxLayout()
        disp_all_btn = QPushButton("All")
        disp_all_btn.setFixedWidth(50)
        disp_all_btn.clicked.connect(lambda: self._select_category_statuses(DISPOSITION_ORDER, True))
        disp_btn_layout.addWidget(disp_all_btn)
        disp_none_btn = QPushButton("None")
        disp_none_btn.setFixedWidth(50)
        disp_none_btn.clicked.connect(lambda: self._select_category_statuses(DISPOSITION_ORDER, False))
        disp_btn_layout.addWidget(disp_none_btn)
        disp_btn_layout.addStretch()
        disp_layout.addLayout(disp_btn_layout)

        for status in DISPOSITION_ORDER:
            color = STATUS_COLORS.get(status, '#000000')
            cb = ColoredCheckBox(status, color)
            cb.setChecked(True)
            cb.setStyleSheet("QCheckBox::indicator { width: 0px; height: 0px; }")
            cb.stateChanged.connect(lambda state, checkbox=cb: (checkbox.update(), self._apply_filters()))
            self.status_checkboxes[status] = cb
            disp_layout.addWidget(cb)

        disp_layout.addStretch()
        columns_layout.addWidget(disp_group)

        filter_main_layout.addLayout(columns_layout)

        filter_main_layout.addStretch()
        filter_scroll.setWidget(filter_widget)
        filter_scroll.setMinimumWidth(380)  # Prevent filter panel from shrinking too small
        splitter.addWidget(filter_scroll)
        splitter.setCollapsible(1, False)  # Prevent filter panel from collapsing

        # Set splitter proportions (tree view : filter panel)
        splitter.setSizes([500, 400])
        tree_view_layout.addWidget(splitter)

        # Description panel at bottom of tree view
        desc_group = QGroupBox("Description (double-click node for details)")
        desc_layout = QVBoxLayout(desc_group)
        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setMaximumHeight(100)
        desc_layout.addWidget(self.desc_text)
        tree_view_layout.addWidget(desc_group)

        self.view_layout.addWidget(self.tree_view_frame)

        # Detail view frame
        self.detail_view = DetailView(self)
        self.detail_view.closeRequested.connect(self.show_tree_view)
        self.view_layout.addWidget(self.detail_view)

        self.main_layout.addWidget(self.view_container)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Show tree view by default
        self.show_tree_view()

    def show_tree_view(self):
        """Switch to tree view."""
        self.detail_view.hide()
        self.tree_view_frame.show()
        # Show toolbar buttons
        self.open_btn.show()
        self.refresh_btn.show()
        self.setWindowTitle("Xstory v1.2 (PySide6)")
        msg = f"Loaded {len(self.nodes)} nodes" if self.nodes else "Ready"
        self.status_bar.showMessage(msg)

    def show_detail_view(self, node_id: str):
        """Switch to detail view for a specific node."""
        self.tree_view_frame.hide()
        # Hide toolbar buttons
        self.open_btn.hide()
        self.refresh_btn.hide()
        self.detail_view.show()
        self.detail_view.show_node(node_id)
        node = self.nodes.get(node_id)
        if node:
            # Window title shows hierarchy context
            self.setWindowTitle(f"Feature: {node.title}")
            self.status_bar.showMessage(f"Viewing: {node_id} - {node.title}")
        else:
            self.setWindowTitle("Feature Details")

    def _on_tree_select(self):
        """Handle tree selection to show description."""
        items = self.tree.selectedItems()
        if not items:
            return

        item = items[0]
        node_id = item.text(0)
        node = self.nodes.get(node_id)

        if node:
            desc = node.description if node.description else '(no description)'
            self.desc_text.setPlainText(desc)

    def _on_tree_double_click(self, item: QTreeWidgetItem, column: int):
        """Handle double-click to open detail view."""
        node_id = item.text(0)
        if node_id in self.nodes:
            self.detail_view.reset_history()
            self.show_detail_view(node_id)

    def _on_tree_right_click(self, position):
        """Handle right-click to show context menu."""
        item = self.tree.itemAt(position)
        if not item:
            return

        node_id = item.text(0)
        node = self.nodes.get(node_id)
        if not node:
            return

        menu = QMenu(self)

        # Header showing current status and role
        header_action = QAction(f"[{node.status}] — {self.current_role.title()} mode", self)
        header_action.setEnabled(False)
        menu.addAction(header_action)
        menu.addSeparator()

        # Get available transitions based on current role
        if self.current_role == 'designer':
            transitions = DESIGNER_TRANSITIONS.get(node.status, [])
        else:
            transitions = ENGINEER_TRANSITIONS.get(node.status, [])

        if transitions:
            for target_status in transitions:
                action = QAction(f"→ {target_status}", self)
                action.triggered.connect(
                    lambda checked, ns=target_status: self._change_node_status(node_id, ns)
                )
                menu.addAction(action)
        else:
            no_options = QAction("(no transitions available)", self)
            no_options.setEnabled(False)
            menu.addAction(no_options)

        menu.exec(self.tree.mapToGlobal(position))

    def _change_node_status(self, node_id: str, new_status: str):
        """Change a node's status with a notes dialog."""
        node = self.nodes.get(node_id)
        if not node:
            return

        # Determine if notes are mandatory
        mandatory = (new_status == 'polish')

        # Show dialog
        dialog = StatusChangeDialog(self, node_id, new_status, mandatory=mandatory)
        if dialog.exec() == QDialog.Accepted:
            notes = dialog.get_notes()
            self._update_node_status_in_db(node_id, new_status, notes or '')

    def _update_node_status_in_db(self, node_id: str, new_status: str, notes: str):
        """Update node status and notes in the database using three-field system."""
        if not self.db_path:
            QMessageBox.critical(self, "Error", "No database loaded.")
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

            # Three-field system: determine which field(s) to update
            # - disposition: terminal states (exits pipeline)
            # - hold_reason: work stopped (stays in pipeline)
            # - stage: workflow position (active progress)
            if new_status in DISPOSITION_VALUES:
                # Setting disposition clears hold_reason
                cursor.execute(
                    """UPDATE story_nodes
                       SET disposition = ?, hold_reason = NULL, notes = ?, updated_at = ?
                       WHERE id = ?""",
                    (new_status, updated_notes, datetime.now().isoformat(), node_id)
                )
            elif new_status in HOLD_REASON_VALUES:
                # Setting hold_reason clears disposition
                cursor.execute(
                    """UPDATE story_nodes
                       SET hold_reason = ?, disposition = NULL, notes = ?, updated_at = ?
                       WHERE id = ?""",
                    (new_status, updated_notes, datetime.now().isoformat(), node_id)
                )
            elif new_status in STAGE_VALUES:
                # Setting stage clears both hold_reason and disposition
                cursor.execute(
                    """UPDATE story_nodes
                       SET stage = ?, hold_reason = NULL, disposition = NULL, notes = ?, updated_at = ?
                       WHERE id = ?""",
                    (new_status, updated_notes, datetime.now().isoformat(), node_id)
                )
            else:
                raise ValueError(f"Unknown status value: {new_status}")

            conn.commit()
            conn.close()

            self.status_bar.showMessage(f"Updated '{node_id}' status to '{new_status}'")

            # Refresh the tree to show updated status
            self._refresh()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update status:\n{e}")

    def _toggle_role(self):
        """Toggle between Designer and Engineer modes."""
        if self.current_role == 'designer':
            self.current_role = 'engineer'
        else:
            self.current_role = 'designer'
        self._update_role_button()
        self.status_bar.showMessage(f"Switched to {self.current_role.title()} mode")

    def _update_role_button(self):
        """Update the role toggle button appearance."""
        if self.current_role == 'designer':
            self.role_toggle_btn.setText("Designer")
            self.role_toggle_btn.setChecked(False)
            self.role_toggle_btn.setStyleSheet(
                "QPushButton { background-color: #9900CC; color: white; font-weight: bold; }"
                "QPushButton:hover { background-color: #7700AA; }"
            )
        else:
            self.role_toggle_btn.setText("Engineer")
            self.role_toggle_btn.setChecked(True)
            self.role_toggle_btn.setStyleSheet(
                "QPushButton { background-color: #0099CC; color: white; font-weight: bold; }"
                "QPushButton:hover { background-color: #0077AA; }"
            )

    def _try_auto_detect_db(self):
        """Try to auto-detect the database file."""
        possible_paths = [
            Path(__file__).parent.parent.parent / '.claude' / 'data' / 'story-tree.db',
            Path.cwd() / '.claude' / 'data' / 'story-tree.db',
            Path.cwd().parent / '.claude' / 'data' / 'story-tree.db',
        ]

        for path in possible_paths:
            if path.exists():
                self._load_database(str(path.resolve()))
                return

        self.status_bar.showMessage("No database auto-detected. Use 'Open Database...' to load one.")

    def _open_database(self):
        """Open a database file via file dialog."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Story Tree Database",
            str(Path.cwd()),
            "SQLite Database (*.db);;All Files (*.*)"
        )
        if path:
            self._load_database(path)

    def _load_database(self, path: str):
        """Load a database file."""
        if not os.path.exists(path):
            QMessageBox.critical(self, "Error", f"Database file not found:\n{path}")
            return

        self.db_path = path
        self.db_label.setText(os.path.basename(path))
        self._refresh()

    def _refresh(self):
        """Refresh the tree from the database."""
        if not self.db_path:
            return

        try:
            self._load_nodes_from_db()
            self._apply_filters()
            self.status_bar.showMessage(f"Loaded {len(self.nodes)} nodes from {os.path.basename(self.db_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load database:\n{e}")
            self.status_bar.showMessage(f"Error: {e}")

    def _load_nodes_from_db(self):
        """Load all nodes from the database."""
        self.nodes.clear()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Three-field system: effective status = COALESCE(disposition, hold_reason, stage)
        query = """
            SELECT
                s.id, s.title,
                COALESCE(s.disposition, s.hold_reason, s.stage) as status,
                s.stage, s.hold_reason, s.disposition,
                s.capacity, s.description, s.success_criteria, s.story,
                s.notes, s.project_path, s.created_at, s.updated_at, s.last_implemented,
                COALESCE(
                    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id AND ancestor_id != s.id),
                    0
                ) as depth,
                (SELECT ancestor_id FROM story_paths WHERE descendant_id = s.id AND depth = 1) as parent_id,
                (SELECT COUNT(*) - 1 FROM story_paths WHERE ancestor_id = s.id) as descendants_count
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
                last_implemented=row['last_implemented'] or '',
                stage=row['stage'] or 'concept',
                hold_reason=row['hold_reason'],
                disposition=row['disposition'],
                descendants_count=row['descendants_count'] or 0,
                success_criteria=row['success_criteria'] or '',
                story=row['story'] or ''
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

    def _get_ancestors(self, node_id: str) -> set:
        """Get all ancestor node IDs for a given node."""
        ancestors = set()
        node = self.nodes.get(node_id)
        while node and node.parent_id:
            ancestors.add(node.parent_id)
            node = self.nodes.get(node.parent_id)
        return ancestors

    def _apply_filters(self):
        """Apply status filters and color the tree.

        Filter logic: A node is visible if it matches ALL THREE filter categories (AND logic).
        Within each category, the node matches if its field matches ANY checked option (OR logic).
        - Stage: node.stage must be in checked stages
        - Hold Status: node.hold_reason must be in checked holds, OR 'no hold' checked and no hold_reason
        - Disposition: node.disposition must be in checked dispositions, OR 'live' checked and no disposition
        """
        # Collect checked statuses by category
        checked_stages = {s for s in STAGE_ORDER
                          if s in self.status_checkboxes and self.status_checkboxes[s].isChecked()}
        checked_holds = {s for s in HOLD_REASON_ORDER
                         if s in self.status_checkboxes and self.status_checkboxes[s].isChecked()}
        checked_disps = {s for s in DISPOSITION_ORDER
                         if s in self.status_checkboxes and self.status_checkboxes[s].isChecked()}

        # Special filter flags
        show_no_hold = 'no hold' in checked_holds
        show_live = 'live' in checked_disps

        def node_matches_filter(node):
            """Check if node matches the current filters (AND logic across categories)."""
            # Stage check: node.stage must be in checked stages
            if node.stage not in checked_stages:
                return False

            # Hold Status check: node.hold_reason in checked holds, OR 'no hold' if no hold_reason
            hold_ok = False
            if node.hold_reason and node.hold_reason in checked_holds:
                hold_ok = True
            elif show_no_hold and not node.hold_reason:
                hold_ok = True
            if not hold_ok:
                return False

            # Disposition check: node.disposition in checked dispositions, OR 'live' if no disposition
            disp_ok = False
            if node.disposition and node.disposition in checked_disps:
                disp_ok = True
            elif show_live and not node.disposition:
                disp_ok = True
            if not disp_ok:
                return False

            return True

        # Step 1: Find all nodes that directly match the filter
        matching_nodes = {node_id for node_id, node in self.nodes.items()
                         if node_matches_filter(node)}

        # Step 2: Collect ancestors of all matching nodes
        ancestor_nodes = set()
        for node_id in matching_nodes:
            ancestor_nodes.update(self._get_ancestors(node_id))

        # Nodes to show = matching nodes + their ancestors
        visible_nodes = matching_nodes | ancestor_nodes
        # Ancestor-only nodes (shown faded)
        faded_nodes = ancestor_nodes - matching_nodes

        # Clear the tree
        self.tree.clear()
        self.tree_items.clear()

        # Find root nodes that are visible
        root_nodes = [n for n in self.nodes.values()
                     if (not n.parent_id or n.parent_id not in self.nodes)
                     and n.id in visible_nodes]
        root_nodes.sort(key=lambda n: self._sort_key(n.id))

        # Build filtered tree
        for node in root_nodes:
            self._add_filtered_node(node, None, visible_nodes, faded_nodes)

        # Expand all nodes
        self.tree.expandAll()

    def _add_filtered_node(self, node: StoryNode, parent_item: Optional[QTreeWidgetItem],
                           visible_nodes: set, faded_nodes: set):
        """Add a node to the filtered tree with gradient coloring.

        Gradient coloring is applied via the GradientTextDelegate:
        - StartColor: Based on stage (green→blue progression)
        - EndColor: Red if disposition active, black if on hold, else same as start
        - Faded ancestors: Gray text (not gradient)
        """
        if node.id not in visible_nodes:
            return

        # Determine status display text and tooltip
        # Priority: disposition > hold_reason > default play icon
        if node.disposition and node.disposition in DISPOSITION_ICONS:
            # Disposition overrides everything - show disposition icon + disposition reason
            icon = DISPOSITION_ICONS[node.disposition]
            status_text = f"{icon} {node.disposition}"
            tooltip = f"Stage: {node.stage}"
        elif node.hold_reason and node.hold_reason in HOLD_ICONS:
            # Show hold icon + underlying stage when on hold
            icon = HOLD_ICONS[node.hold_reason]
            status_text = f"{icon} {node.stage}"
            tooltip = f"{node.hold_reason.capitalize()} - Stage: {node.stage}"
        else:
            # No hold status - show play icon + stage
            status_text = f"{DEFAULT_STAGE_ICON} {node.stage}"
            tooltip = None

        # Create tree item
        item = QTreeWidgetItem([node.id, status_text, node.title])

        # Set tooltip if hold reason exists
        if tooltip:
            item.setToolTip(1, tooltip)

        # Mark faded nodes with UserRole data for the delegate
        if node.id in faded_nodes:
            item.setData(0, Qt.UserRole, 'faded')
            # Set italic font for faded items
            italic_font = QFont()
            italic_font.setItalic(True)
            item.setFont(0, italic_font)
            item.setFont(2, italic_font)
        else:
            item.setData(0, Qt.UserRole, 'normal')

        # Note: Actual text coloring is handled by GradientTextDelegate
        # which reads node data and applies gradient colors

        # Add to tree
        if parent_item:
            parent_item.addChild(item)
        else:
            self.tree.addTopLevelItem(item)

        # Store reference
        self.tree_items[node.id] = item

        # Add visible children
        visible_children = [c for c in node.children if c.id in visible_nodes]
        visible_children.sort(key=lambda n: self._sort_key(n.id))

        for child in visible_children:
            self._add_filtered_node(child, item, visible_nodes, faded_nodes)

    def _select_all_statuses(self):
        """Select all status filters."""
        for cb in self.status_checkboxes.values():
            cb.setChecked(True)

    def _select_no_statuses(self):
        """Deselect all status filters."""
        for cb in self.status_checkboxes.values():
            cb.setChecked(False)

    def _select_category_statuses(self, statuses: List[str], checked: bool):
        """Select or deselect a category of status filters."""
        for status in statuses:
            if status in self.status_checkboxes:
                self.status_checkboxes[status].setChecked(checked)

    def closeEvent(self, event):
        """Handle window close - return to tree view if in detail view."""
        if self.detail_view.isVisible():
            event.ignore()
            self.show_tree_view()
        else:
            event.accept()

    def keyPressEvent(self, event):
        """Handle key presses - Escape returns to tree view from detail view."""
        if event.key() == Qt.Key_Escape and self.detail_view.isVisible():
            self.show_tree_view()
        else:
            super().keyPressEvent(event)


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = XstoryExplorer()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
